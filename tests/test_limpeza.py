"""Limpeza de vagas antigas (spec 054): critérios no config, grupos e datas, destaques, ficha curta, prévia sem
gravar, gravação com backup e compactação, dedupe depois de arquivar, "sem resposta", desarquivar, o comando e as
rotas. Vagas fictícias, banco e config numa pasta temporária."""
import argparse
import http.client
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import analise_perfil  # noqa: E402
import banco  # noqa: E402
import curriculo_ia  # noqa: E402
import filtros  # noqa: E402
import requisitos  # noqa: E402

DIA = "2026-06-30"


def antes(dias: int, base: str = DIA) -> str:
    return (date.fromisoformat(base) - timedelta(days=dias)).isoformat()


def vaga(vid, **campos):
    return {"id": vid, "origem": "busca", "plataforma": "Gupy", "titulo": f"Analista {vid}", "empresa": "Empresa Alfa",
            "url": f"https://exemplo.invalid/vaga/{vid}", "triagem": "pendente", "descricao": "Texto longo. " * 200,
            "resumo": "Resumo.", "encaixe": ["a"], "lacunas": ["b"], "requisitos": {"itens": []},
            "analise_status": "feita", "aderencia": 50, "encontrada_em": antes(40), **campos}


def crit(**mudar):
    c = filtros.limpeza_padrao()
    for g, m in mudar.items():
        c[g].update(m)
    return c


def gravar(*docs):
    with banco.escrita() as con:
        for d in docs:
            banco._gravar(con, d["id"], d)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pasta_curriculos = self.tmp / "curriculos"
        self.pasta_curriculos.mkdir(parents=True, exist_ok=True)
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(banco, "BACKUPS", self.tmp / "backup"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(curriculo_ia, "CURRICULOS", self.pasta_curriculos)):
            p.start()
            self.addCleanup(p.stop)


class TestCriterios(Base):
    def test_padrao_sem_a_chave(self):
        c = filtros.efetivos({})["limpeza"]
        self.assertEqual(c, filtros.limpeza_padrao())
        self.assertTrue(all(g["ligado"] and g["dias"] == 30 for g in c.values()))
        self.assertIsNone(c["pendente"]["nota_abaixo_de"])
        self.assertNotIn("contratado", c["dispensadas"]["resultados"])

    def test_config_fora_do_formato_fica_no_padrao(self):
        c = filtros.efetivos({"limpeza": {"fora": {"dias": 0, "ligado": "sim"}, "pendente": "x",
                                          "dispensadas": {"resultados": ["desisti", "contratado"]}}})["limpeza"]
        self.assertEqual((c["fora"]["dias"], c["fora"]["ligado"]), (30, True))
        self.assertEqual(c["dispensadas"]["resultados"], ["desisti"])

    def test_validar(self):
        v = filtros.validar_limpeza({"fora": {"ligado": False, "dias": 15}, "pendente": {"dias": 45, "nota_abaixo_de": 60},
                                     "dispensadas": {"dias": 20, "resultados": ["desisti", "cancelada"]}})
        self.assertEqual(v["fora"], {"ligado": False, "dias": 15})
        self.assertEqual(v["pendente"]["nota_abaixo_de"], 60)
        self.assertEqual(v["dispensadas"]["resultados"], ["desisti", "cancelada"])
        self.assertEqual(v["sem_resposta"], {"ligado": True, "dias": 30})  # ausente: padrão
        for ruim in ({"fora": {"dias": 0}}, {"fora": {"dias": 366}}, {"pendente": {"nota_abaixo_de": 101}},
                     {"dispensadas": {"resultados": ["contratado"]}}, {"fora": "x"}, "x"):
            with self.subTest(ruim=ruim), self.assertRaises(ValueError):
                filtros.validar_limpeza(ruim)

    def test_salvar_limpeza_sem_termos_e_salvar_filtros_nao_mexe(self):
        filtros.salvar_limpeza({"fora": {"ligado": True, "dias": 12}})
        self.assertEqual(filtros.efetivos(filtros.ler_config())["limpeza"]["fora"]["dias"], 12)
        filtros.salvar({"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}})
        self.assertEqual(filtros.ler_config()["limpeza"]["fora"]["dias"], 12)
        # o painel devolve o objeto lido ao abrir (critérios velhos): o Salvar filtros não desfaz a aba Limpeza
        filtros.salvar({"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True},
                        "limpeza": {"fora": {"ligado": True, "dias": 7}}})
        self.assertEqual(filtros.ler_config()["limpeza"]["fora"]["dias"], 12)

    def test_exemplo_tem_os_padroes(self):
        exemplo = json.loads(filtros.EXEMPLO.read_text(encoding="utf-8"))
        self.assertEqual(exemplo["limpeza"], filtros.limpeza_padrao())


class TestGrupos(unittest.TestCase):
    def g(self, v, **mudar):
        return banco.grupo_limpeza(v, crit(**mudar), DIA)

    def test_cada_grupo_pelo_prazo(self):
        casos = [
            ({"triagem": "fora", "triada_em": antes(40)}, ("fora", 40)),
            ({"triagem": "fora", "triada_em": antes(10)}, None),
            ({"triagem": "pendente", "encontrada_em": antes(31)}, ("pendente", 31)),
            ({"triagem": "visitada", "triada_em": antes(30)}, ("dispensadas", 30)),
            ({"triagem": "seguir", "etapa": "encerrada", "resultado": "nao_aprovado", "etapa_em": antes(35)},
             ("dispensadas", 35)),
            ({"triagem": "seguir", "etapa": "encerrada", "resultado": None, "etapa_em": antes(35)}, ("dispensadas", 35)),
            ({"triagem": "seguir", "etapa": "aplicada", "etapa_em": antes(45)}, ("sem_resposta", 45)),
            ({"triagem": "seguir", "etapa": "aplicada", "etapa_em": antes(5)}, None),
        ]
        for campos, esperado in casos:
            with self.subTest(campos=campos):
                self.assertEqual(self.g(vaga("v", **campos)), esperado)

    def test_atualizada_em_nao_conta_e_fallback_de_data(self):
        v = vaga("v", triagem="fora", atualizada_em=f"{DIA}T10:00:00")  # sem triada_em: conta encontrada_em (40)
        self.assertEqual(self.g(v), ("fora", 40))
        v = vaga("v", triagem="seguir", etapa="aplicada", triada_em=antes(50))  # sem etapa_em
        self.assertEqual(self.g(v), ("sem_resposta", 50))
        sem_data = vaga("v", triagem="fora")
        sem_data.pop("encontrada_em")
        self.assertIsNone(self.g(sem_data))

    def test_grupo_desligado_e_prazo_proprio(self):
        v = vaga("v", triagem="fora", triada_em=antes(20))
        self.assertIsNone(self.g(v))
        self.assertEqual(self.g(v, fora={"dias": 15}), ("fora", 20))
        self.assertIsNone(self.g(v, fora={"dias": 15, "ligado": False}))

    def test_nota_abaixo_de(self):
        teto = {"nota_abaixo_de": 60}
        self.assertEqual(self.g(vaga("v", aderencia=59), pendente=teto)[0], "pendente")
        self.assertIsNone(self.g(vaga("v", aderencia=60), pendente=teto))
        self.assertIsNone(self.g(vaga("v", aderencia=None), pendente=teto))  # sem nota fica de fora
        self.assertEqual(self.g(vaga("v", aderencia=None))[0], "pendente")  # sem teto: todas

    def test_resultados_escolhidos(self):
        v = vaga("v", triagem="seguir", etapa="encerrada", resultado="nao_aprovado", etapa_em=antes(40))
        self.assertIsNone(self.g(v, dispensadas={"resultados": ["desisti"]}))
        sem = vaga("v", triagem="seguir", etapa="encerrada", etapa_em=antes(40))
        self.assertIsNone(self.g(sem, dispensadas={"resultados": ["desisti"]}))
        self.assertEqual(self.g(sem, dispensadas={"resultados": ["sem_resultado"]})[0], "dispensadas")

    def test_nunca_entram(self):
        for campos in ({"origem": "manual", "triagem": "fora"},
                       {"triagem": "seguir", "etapa": "entrevista", "etapa_em": antes(90)},
                       {"triagem": "seguir", "etapa": "proposta", "etapa_em": antes(90)},
                       {"triagem": "seguir", "etapa": "salva", "etapa_em": antes(90)},
                       {"triagem": "seguir", "etapa": "encerrada", "resultado": "contratado", "etapa_em": antes(90)},
                       {"triagem": "fora", "arquivada_em": "2026-06-01T10:00:00"},
                       {"triagem": "seguir"}):
            with self.subTest(campos=campos):
                self.assertIsNone(self.g(vaga("v", **campos)))

    def test_vaga_por_link_entra(self):
        self.assertEqual(self.g(vaga("v", origem="link", triagem="fora"))[0], "fora")

    def test_destaques(self):
        self.assertEqual(banco.destaques(vaga("v")), [])
        self.assertEqual(banco.destaques(vaga("v", curriculos=["cv-x"], documentos=[{"nome": "c"}], anotacao="liguei")),
                         ["tem currículo", "tem carta ou respostas", "tem anotação"])
        self.assertEqual(banco.destaques(vaga("v", anotacao="  ")), [])

    def test_ficha_curta(self):
        v = vaga("v", jk="0123456789abcdef", ids_relacionados=["x"], anotacao="nota", descricao_pendente=True)
        f = banco._ficha_curta(v)
        self.assertTrue(f["arquivada_em"])
        self.assertLessEqual(set(f) - {"id", "arquivada_em"}, banco.FICHA_CURTA)
        for saiu in ("descricao", "resumo", "encaixe", "lacunas", "requisitos", "analise_status", "descricao_pendente"):
            self.assertNotIn(saiu, f)
        for ficou in ("jk", "ids_relacionados", "url", "titulo", "empresa", "aderencia", "anotacao", "triagem"):
            self.assertIn(ficou, f)


class TestLimpar(Base):
    def setUp(self):
        super().setUp()
        gravar(vaga("f40", triagem="fora", triada_em=antes(40), jk="0123456789abcdef"),
               vaga("f10", triagem="fora", triada_em=antes(10)),
               vaga("anot", triagem="fora", triada_em=antes(40), anotacao="falei com o recrutador"),
               vaga("apl", triagem="seguir", etapa="aplicada", etapa_em=antes(40)),
               vaga("ent", triagem="seguir", etapa="entrevista", etapa_em=antes(90)))

    def test_previa_nao_grava(self):
        v0 = banco.versao()
        p = banco.prever_limpeza(crit(), DIA)
        self.assertEqual(banco.versao(), v0)
        self.assertEqual([x["id"] for x in p["grupos"]["fora"]["vagas"]], ["anot", "f40"])
        self.assertEqual(p["grupos"]["fora"]["vagas"][0]["destaques"], ["tem anotação"])
        self.assertEqual(p["grupos"]["sem_resposta"]["acao"], "encerrar")
        self.assertEqual((p["total"], p["destacadas"], p["arquivadas"]), (3, 1, 0))
        self.assertIn("descricao", banco.obter("f40"))

    def test_terminal_deixa_as_destacadas(self):
        r = banco.limpar(crit=crit(), dia=DIA)
        self.assertEqual((r["arquivadas"], r["encerradas"]), (1, 1))
        self.assertTrue(banco.arquivada(banco.obter("f40")))
        self.assertNotIn("descricao", banco.obter("f40"))
        self.assertIn("descricao", banco.obter("anot"))  # destacada: inteira
        self.assertFalse(banco.arquivada(banco.obter("f10")))
        apl = banco.obter("apl")
        self.assertEqual((apl["etapa"], apl["resultado"], apl["etapa_em"]), ("encerrada", "sem_resposta", DIA))
        self.assertIn("descricao", apl)  # sem resposta: não arquiva
        self.assertFalse(banco.arquivada(apl))
        self.assertEqual(banco.obter("ent")["etapa"], "entrevista")
        self.assertTrue((self.tmp / "backup" / f"candidaturas-{banco.hoje()}-limpeza.db").exists())
        self.assertEqual(r["backup"], f"candidaturas-{banco.hoje()}-limpeza.db")

    def test_incluir_destacadas(self):
        banco.limpar(crit=crit(), incluir_destacadas=True, dia=DIA)
        anot = banco.obter("anot")
        self.assertTrue(banco.arquivada(anot))
        self.assertEqual(anot["anotacao"], "falei com o recrutador")  # a anotação fica na ficha

    def test_ids_da_pagina(self):
        r = banco.limpar(["anot", "f10", "ent", "nao-existe"], crit=crit(), dia=DIA)
        self.assertEqual(r["arquivadas"], 1)  # a destacada marcada entra
        self.assertTrue(banco.arquivada(banco.obter("anot")))
        self.assertFalse(banco.arquivada(banco.obter("f40")))  # não pedida
        self.assertEqual(r["ignoradas"], ["ent", "f10", "nao-existe"])

    def test_dedupe_depois_de_arquivar(self):
        banco.limpar(crit=crit(), dia=DIA)
        indice = banco.IndiceVistas()
        self.assertEqual(indice.achar({"id": "f40"}), "f40")
        self.assertEqual(indice.achar({"id": "outro", "url": "https://br.indeed.com/viewjob?jk=0123456789abcdef"}), "f40")

    def test_banco_diminui(self):
        gravar(*[vaga(f"x{i}", triagem="fora", triada_em=antes(60)) for i in range(60)])
        r = banco.limpar(crit=crit(), dia=DIA)
        self.assertGreater(r["arquivadas"], 60)
        self.assertLess(r["depois_kb"], r["antes_kb"] * 0.6)

    def test_arquivadas_saem_das_analises(self):
        banco.limpar(crit=crit(), dia=DIA)
        f40 = banco.obter("f40")
        self.assertFalse(banco.precisa_analise(f40))
        self.assertNotIn("f40", [v["id"] for v in requisitos.selecionar(banco.listar_vagas(), "todas")])
        enc = vaga("enc", triagem="seguir", etapa="encerrada", etapa_em=antes(40), resultado="desisti")
        gravar(enc)
        banco.limpar(crit=crit(), dia=DIA)
        self.assertNotIn("enc", [v["id"] for v in requisitos.selecionar(banco.listar_vagas(), "aplicacoes")])
        escolhidas = analise_perfil.lacunas([banco.obter("f40")], "perfil", "todas")
        self.assertEqual(escolhidas["vagas"], 0)

    def test_desarquivar_quando_a_etapa_muda(self):
        banco.limpar(crit=crit(), dia=DIA)
        banco.atualizar_usuario("f40", {"anotacao": "x"})
        self.assertTrue(banco.arquivada(banco.obter("f40")))
        banco.atualizar_usuario("f40", {"etapa": "entrevista"})
        self.assertFalse(banco.arquivada(banco.obter("f40")))

    def test_sem_resposta_a_mao(self):
        self.assertEqual(banco.atualizar_usuario("ent", {"etapa": "encerrada", "resultado": "sem_resposta"})["resultado"],
                         "sem_resposta")

    def test_criterios_gravados_mudam_a_previa(self):
        filtros.salvar_limpeza({"fora": {"ligado": False}, "sem_resposta": {"dias": 50}})
        p = banco.prever_limpeza(dia=DIA)
        self.assertEqual((p["grupos"]["fora"]["vagas"], p["grupos"]["sem_resposta"]["vagas"]), ([], []))
        self.assertFalse(p["grupos"]["fora"]["ligado"])

    def test_arquivar_vaga_com_carta_apaga_documentos(self):
        v = vaga("com_carta", triagem="fora", triada_em=antes(40), documentos=[{"tipo": "carta", "nome": "carta-v1"}])
        gravar(v)
        meta = {"nome": "carta-v1", "tipo": "carta", "alvo": {"tipo": "vaga", "id": "com_carta"},
                "arquivos": {"txt": "carta-v1.txt"}}
        (self.pasta_curriculos / "carta-v1.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        (self.pasta_curriculos / "carta-v1.txt").write_text("Texto da carta", encoding="utf-8")
        r = banco.limpar(["com_carta"], crit=crit(), dia=DIA)
        self.assertEqual(r["arquivadas"], 1)
        self.assertFalse((self.pasta_curriculos / "carta-v1.meta.json").exists())
        self.assertFalse((self.pasta_curriculos / "carta-v1.txt").exists())
        doc = banco.obter("com_carta")
        self.assertTrue(banco.arquivada(doc))
        self.assertEqual(doc.get("documentos_apagados"), {"carta": 1, "em": DIA})
        self.assertNotIn("documentos", doc)
        self.assertNotIn("curriculos", doc)

    def test_falha_apagar_lote_nao_arquiva(self):
        v1 = vaga("v_erro", triagem="fora", triada_em=antes(40), documentos=[{"tipo": "carta", "nome": "carta-erro"}])
        v2 = vaga("v_ok", triagem="fora", triada_em=antes(40))
        gravar(v1, v2)
        meta = {"nome": "carta-erro", "tipo": "carta", "alvo": {"tipo": "vaga", "id": "v_erro"}}
        (self.pasta_curriculos / "carta-erro.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        with mock.patch.object(curriculo_ia, "apagar_lote", side_effect=curriculo_ia.GeracaoErro("arquivo aberto")):
            r = banco.limpar(["v_erro", "v_ok"], crit=crit(), dia=DIA)
        self.assertEqual(r["arquivadas"], 1)
        self.assertEqual(r["nao_arquivadas"], [{"id": "v_erro", "motivo": "arquivo aberto"}])
        self.assertFalse(banco.arquivada(banco.obter("v_erro")))
        self.assertTrue(banco.arquivada(banco.obter("v_ok")))

    def test_sem_resposta_encerrada_nao_perde_documentos(self):
        v = vaga("sem_resp", triagem="seguir", etapa="aplicada", etapa_em=antes(40),
                 documentos=[{"tipo": "respostas", "nome": "resp-1"}])
        gravar(v)
        meta = {"nome": "resp-1", "tipo": "respostas", "alvo": {"tipo": "vaga", "id": "sem_resp"}}
        (self.pasta_curriculos / "resp-1.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        (self.pasta_curriculos / "resp-1.txt").write_text("respostas", encoding="utf-8")
        r = banco.limpar(["sem_resp"], crit=crit(), dia=DIA)
        self.assertEqual(r["encerradas"], 1)
        self.assertEqual(r["arquivadas"], 0)
        self.assertTrue((self.pasta_curriculos / "resp-1.meta.json").exists())
        self.assertTrue((self.pasta_curriculos / "resp-1.txt").exists())
        doc = banco.obter("sem_resp")
        self.assertEqual(doc["etapa"], "encerrada")
        self.assertEqual(doc["resultado"], "sem_resposta")
        self.assertEqual(len(doc.get("documentos") or []), 1)
        self.assertNotIn("documentos_apagados", doc)

    def test_desligar_documento(self):
        v = vaga("v_doc", documentos=[{"tipo": "carta", "nome": "c1"}, {"tipo": "respostas", "nome": "r1"}])
        gravar(v)
        banco.desligar_documento("v_doc", "c1")
        doc = banco.obter("v_doc")
        self.assertEqual(doc["documentos"], [{"tipo": "respostas", "nome": "r1"}])
        # desligar documento que não existe na vaga não mexe em nada
        banco.desligar_documento("v_doc", "c_inexistente")
        self.assertEqual(banco.obter("v_doc")["documentos"], [{"tipo": "respostas", "nome": "r1"}])
        # vaga inexistente não levanta erro
        banco.desligar_documento("vaga_fantasma", "c1")


class TestComando(Base):
    def rodar(self, *args):
        env = {**os.environ, "TRAMPO_BANCO": str(self.tmp / "banco.db"),
               "TRAMPO_CURRICULOS": str(self.pasta_curriculos),
               "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, str(RAIZ / "dash" / "banco.py"), "limpar", *args], env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=60, cwd=self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def rodar_orfaos(self, *args):
        env = {**os.environ, "TRAMPO_BANCO": str(self.tmp / "banco.db"),
               "TRAMPO_CURRICULOS": str(self.pasta_curriculos),
               "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, str(RAIZ / "dash" / "banco.py"), "documentos-orfaos", *args], env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=60, cwd=self.tmp)
        return r.returncode, r.stdout, r.stderr

    def test_previa_e_gravar(self):
        hoje = date.today().isoformat()
        gravar(vaga("velha", triagem="fora", triada_em=antes(40, hoje)),
               vaga("anot", triagem="fora", triada_em=antes(40, hoje), anotacao="nota"))
        saida = self.rodar()
        self.assertIn("Nada foi gravado", saida)
        self.assertIn("tem anotação", saida)
        self.assertFalse(banco.arquivada(banco.obter("velha")))
        saida = self.rodar("--gravar")
        self.assertIn("Arquivadas: 1", saida)
        self.assertTrue(banco.arquivada(banco.obter("velha")))
        self.assertFalse(banco.arquivada(banco.obter("anot")))

    def test_documentos_orfaos_comando(self):
        code, out, _ = self.rodar_orfaos()
        self.assertEqual(code, 0)
        self.assertIn("Nenhum documento órfão.", out)

        meta = {"nome": "carta-antiga", "tipo": "carta", "criado_em": "2026-06-01T10:00:00",
                "alvo": {"tipo": "vaga", "id": "v_sumiu", "titulo": "Dev", "empresa": "Tech"}}
        (self.pasta_curriculos / "carta-antiga.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        (self.pasta_curriculos / "carta-antiga.txt").write_text("conteudo", encoding="utf-8")

        code, out, _ = self.rodar_orfaos()
        self.assertEqual(code, 0)
        self.assertIn("- carta | 2026-06-01 | Dev | Tech | vaga não encontrada | carta-antiga", out)
        self.assertIn("Nada foi apagado. Para apagar: python dash/banco.py documentos-orfaos --gravar", out)
        self.assertTrue((self.pasta_curriculos / "carta-antiga.meta.json").exists())

        code, out, _ = self.rodar_orfaos("--gravar")
        self.assertEqual(code, 0)
        self.assertIn("Apagados: 1 documento(s).", out)
        self.assertFalse((self.pasta_curriculos / "carta-antiga.meta.json").exists())
        self.assertFalse((self.pasta_curriculos / "carta-antiga.txt").exists())

    def test_documentos_orfaos_erro_arquivo_aberto(self):
        meta = {"nome": "carta-aberta", "tipo": "carta", "criado_em": "2026-06-01T10:00:00",
                "alvo": {"tipo": "vaga", "id": "v_sumiu"}}
        (self.pasta_curriculos / "carta-aberta.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        with mock.patch.object(curriculo_ia, "apagar_lote", side_effect=curriculo_ia.GeracaoErro("arquivo aberto")):
            saida = io.StringIO()
            with mock.patch("sys.stdout", saida):
                code = banco._cmd_documentos_orfaos(argparse.Namespace(gravar=True))
            self.assertEqual(code, 1)
            self.assertIn("arquivo aberto", saida.getvalue())


class TestRotas(Base):
    def setUp(self):
        super().setUp()
        import servidor
        p = mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})
        p.start()
        self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_fluxo(self):
        hoje = date.today().isoformat()
        gravar(vaga("velha", triagem="fora", triada_em=antes(40, hoje)), vaga("nova", triagem="fora", triada_em=hoje))
        st, r = self.pedir("GET", "/api/limpeza")
        self.assertEqual((st, r["criterios"], r["arquivadas"]), (200, filtros.limpeza_padrao(), 0))
        st, r = self.pedir("PUT", "/api/limpeza", {"criterios": {"fora": {"ligado": True, "dias": 20}}})
        self.assertEqual((st, r["criterios"]["fora"]["dias"]), (200, 20))
        st, r = self.pedir("PUT", "/api/limpeza", {"criterios": {"fora": {"dias": 0}}})
        self.assertEqual(st, 400)
        st, p = self.pedir("GET", "/api/limpeza/previa")
        self.assertEqual((st, [x["id"] for x in p["grupos"]["fora"]["vagas"]]), (200, ["velha"]))
        st, r = self.pedir("POST", "/api/limpeza/aplicar", {"ids": ["velha", "nova"]})
        self.assertEqual((st, r["arquivadas"], r["ignoradas"]), (200, 1, ["nova"]))
        st, r = self.pedir("GET", "/api/limpeza")
        self.assertEqual(r["arquivadas"], 1)
        for ruim in ({"ids": []}, {"ids": "velha"}, {"ids": ["../x"]}, {}):
            with self.subTest(ruim=ruim):
                self.assertEqual(self.pedir("POST", "/api/limpeza/aplicar", ruim)[0], 400)


if __name__ == "__main__":
    unittest.main()
