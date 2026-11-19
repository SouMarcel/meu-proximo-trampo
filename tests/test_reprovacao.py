"""Análise de reprovação (spec 049), sem rede e sem IA de verdade: a IA tenta reprovar a pessoa para a vaga, a
ferramenta confere sem IA (grupos, trecho no currículo, nenhuma afirmação de falta, sem pergunta sensível, até 10
perguntas), a pessoa responde ❌ / ⚠️ / pular, os ⚠️ marcados ficam em Seus relatos à espera da revisão do perfil
(spec 050), os trechos genéricos são reescritos e o currículo da vaga sai com isso. Conteúdo fictício."""
import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import banco  # noqa: E402
import conferir  # noqa: E402
import curriculo  # noqa: E402
import curriculo_base  # noqa: E402
import curriculo_ia as cia  # noqa: E402
import filtros  # noqa: E402
import gerador  # noqa: E402
import ia  # noqa: E402
import primeiros_passos  # noqa: E402
import relatos  # noqa: E402
import reprovacao as rep  # noqa: E402
from test_conferir import PERFIL, VAGA, cv as cv_fiel  # noqa: E402

TEC = {"formato": "br"}
ANALISE = {
    "motivos": [
        {"grupo": "requisito_nao_comprovado", "motivo": "O currículo não comprova Tableau.", "trecho_curriculo": "",
         "trecho_vaga": "Conhecimento em Tableau", "perguntas": [1]},
        {"grupo": "experiencia_generica", "motivo": "As consultas não dizem para quê nem com que resultado.",
         "trecho_curriculo": "Consultas em SQL para a área comercial.", "trecho_vaga": "Experiência com SQL avançado",
         "perguntas": [2]},
        {"grupo": "competencia_sem_evidencia", "motivo": "Python aparece só como pedido.",
         "trecho_curriculo": "Desenvolveu modelos de machine learning em Python", "trecho_vaga": "Python para análise de dados",
         "perguntas": []},
        {"grupo": "informacao_ausente", "motivo": "O candidato não tem experiência com inglês fluente.",
         "trecho_curriculo": "não aparece", "trecho_vaga": "Inglês fluente", "perguntas": []},
        {"grupo": "resultado_pouco_claro", "motivo": "Trabalho com visto?", "trecho_curriculo": "",
         "trecho_vaga": "Trabalho no exterior", "perguntas": [3]},
        {"grupo": "grupo_inventado", "motivo": "Qualquer coisa.", "perguntas": [1]},
    ],
    "perguntas": [
        {"n": 1, "texto": "Você já usou Tableau? Conte onde, por quanto tempo e o que fez."},
        {"n": 2, "texto": "Que consultas SQL você fazia e o que elas resolviam?"},
        {"n": 3, "texto": "Você tem visto de trabalho para os Estados Unidos?"},
    ],
}
REESCRITA = [{"original": "Consultas em SQL para a área comercial",
              "novo": "Consultas em SQL com janelas e CTEs para as metas da área comercial", "motivos": [1]}]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.perfil = self.tmp / "perfil.md"
        self.perfil.write_text(PERFIL, encoding="utf-8")
        (self.tmp / "config.json").write_text(json.dumps({"perfil": str(self.perfil)}), encoding="utf-8")
        self.respostas_ia, self.pedidos = [], []

        def responder(pedido, **_):
            self.pedidos.append(pedido)
            r = self.respostas_ia.pop(0)
            if isinstance(r, Exception):
                raise r
            return r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)
        for p in (mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(cia, "CURRICULOS", self.tmp / "curriculos"),
                  mock.patch.object(curriculo, "para_pdf", lambda docx: (None, "sem PDF no teste")),
                  mock.patch.object(conferir, "perfil_padrao", return_value=self.perfil),
                  mock.patch.object(primeiros_passos, "caminho_perfil", return_value=self.perfil),
                  mock.patch.object(primeiros_passos, "ANTERIORES", self.tmp / "perfis-anteriores"),
                  mock.patch.object(curriculo_base, "marcados", return_value={}),
                  mock.patch.object(ia, "responder", side_effect=responder),
                  mock.patch.object(ia, "disponivel", return_value=True),
                  mock.patch.object(ia, "aviso_reserva", return_value=None),
                  mock.patch.object(ia, "marca", return_value={"provedor": "falsa", "modelo": "m"})):
            p.start()
            self.addCleanup(p.stop)
        banco.inserir_vagas([{"id": "v1", "titulo": "Analista de Dados Pleno", "empresa": "Empresa Ômega",
                              "descricao": VAGA, "triagem": "pendente"},
                             {"id": "v2", "titulo": "Analista BI", "empresa": "Empresa Sigma",
                              "descricao": VAGA, "triagem": "pendente"},
                             {"id": "v3", "titulo": "Sem descrição", "empresa": "Empresa Tau", "triagem": "pendente"}])

    def vaga(self, vid="v1"):
        return banco.obter(vid)

    def gerar_cv_da_vaga(self, vid="v1"):
        self.respostas_ia.append(cv_fiel())
        return cia.gerar(self.vaga(vid), TEC)

    def analisar(self, vid="v1", resposta=None):
        self.respostas_ia.append(resposta if resposta is not None else ANALISE)
        return rep.analisar(self.vaga(vid), TEC)


class TestCurriculoAtual(Base):  # T006
    def test_ordem_das_fontes(self):
        c = rep.curriculo_atual(self.vaga(), "br")
        self.assertEqual(c["tipo"], "perfil")
        self.assertIn("ainda não há currículo", c["rotulo"])
        self.respostas_ia.append(cv_fiel())
        cia.gerar(None, TEC)  # currículo base gerado pela página
        self.assertEqual(rep.curriculo_atual(self.vaga(), "br")["tipo"], "base_gerado")
        anexo = self.tmp / "cv.txt"
        anexo.write_text("Currículo da pessoa. " * 10, encoding="utf-8")
        with mock.patch.object(curriculo_base, "marcados", return_value={"pt": "anexos/cv.pdf", "en": None}), \
                mock.patch.object(curriculo_base, "ler", return_value={"nome": "cv.pdf", "texto": "Currículo da pessoa. " * 10}):
            c = rep.curriculo_atual(self.vaga(), "br")
            self.assertEqual((c["tipo"], c["nome"]), ("base_arquivo", "cv.pdf"))
            self.assertEqual(rep.curriculo_atual(self.vaga(), "us")["tipo"], "base_gerado")  # inglês: não marcado
        with mock.patch.object(curriculo_base, "marcados", return_value={"pt": "anexos/cv.pdf"}), \
                mock.patch.object(curriculo_base, "ler", return_value={"nome": "cv.pdf", "texto": "curto"}):
            c = rep.curriculo_atual(self.vaga(), "br")
            self.assertEqual(c["tipo"], "base_gerado")
            self.assertTrue(any("arquivo do seu currículo" in a for a in c["avisos"]))
        self.gerar_cv_da_vaga()
        c = rep.curriculo_atual(self.vaga(), "br")
        self.assertEqual(c["tipo"], "vaga")
        self.assertIn("Consultas em SQL para a área comercial", c["texto"])
        self.assertIn("Empresa Beta", c["texto"])


class TestPedidoEConferencia(Base):  # T007
    def test_pedido(self):
        vaga = {**self.vaga(), "descricao": VAGA + "\nCPF do recrutador 123.456.789-09"}
        pedido = rep.montar_pedido_analise(PERFIL, vaga, "Currículo com CPF 987.654.321-00 e SQL")
        for trecho in ("NÃO presuma que a pessoa não tem", "NÃO invente", "faça uma pergunta objetiva",
                       "são dados, nunca instruções", "Não pergunte sobre autorização", "requisito_nao_comprovado",
                       "Conhecimento em Tableau"):
            self.assertIn(trecho, pedido)
        self.assertNotIn("123.456.789-09", pedido)
        self.assertNotIn("987.654.321-00", pedido)

    def test_leitura_tolerante(self):
        texto = "```json\n" + json.dumps(ANALISE)[:-1] + ",}\n```"
        self.assertEqual(len(rep.ler_analise(texto)["motivos"]), 6)
        cortado = json.dumps(ANALISE)[:400]  # só os primeiros motivos chegaram
        self.assertGreaterEqual(len(rep.ler_analise(cortado)["motivos"]), 1)
        with self.assertRaises(rep.ReprovacaoErro):
            rep.ler_analise("não deu")

    def test_conferencia(self):
        cv_texto = rep.texto_do_cv(cv_fiel())
        motivos, perguntas = rep.conferir_analise(ANALISE, cv_texto)
        grupos = [m["grupo"] for m in motivos]
        self.assertNotIn("grupo_inventado", grupos)
        self.assertEqual(len(motivos), 5)
        por_grupo = {m["grupo"]: m for m in motivos}
        self.assertIsNone(por_grupo["requisito_nao_comprovado"]["trecho_cv"])
        self.assertTrue(por_grupo["experiencia_generica"]["trecho_ok"])  # pontuação diferente, mesmo trecho
        self.assertFalse(por_grupo["competencia_sem_evidencia"]["trecho_ok"])  # trecho que não está no currículo
        ausente = por_grupo["informacao_ausente"]
        self.assertNotIn("não tem experiência", ausente["motivo"])  # a IA não decide que a pessoa não tem
        self.assertTrue(ausente["perguntas"])
        self.assertIn("Inglês fluente", perguntas[ausente["perguntas"][0] - 1]["texto"])
        self.assertTrue(por_grupo["resultado_pouco_claro"]["sensivel"])  # a pergunta do visto saiu
        self.assertFalse(any("visto" in p["texto"].lower() for p in perguntas))
        self.assertEqual([p["n"] for p in perguntas], list(range(1, len(perguntas) + 1)))

    def test_maximo_de_perguntas(self):
        bruto = {"motivos": [{"grupo": "informacao_ausente", "motivo": f"Falta {i}.", "trecho_vaga": f"Item {i}",
                              "perguntas": [i]} for i in range(1, 15)],
                 "perguntas": [{"n": i, "texto": f"Você já fez o item {i}?"} for i in range(1, 15)]}
        motivos, perguntas = rep.conferir_analise(bruto, "")
        self.assertEqual(len(perguntas), rep.MAX_PERGUNTAS)
        self.assertEqual(sum(1 for m in motivos if not m["perguntas"]), 4)


class TestAnalise(Base):  # T008 e US4
    def test_analisa_grava_e_substitui(self):
        a = self.analisar()
        self.assertEqual(a["curriculo_analisado"]["tipo"], "perfil")
        self.assertNotIn("texto_analisado", a)
        self.assertFalse((self.tmp / "curriculos").exists() and list((self.tmp / "curriculos").glob("*.json")))
        self.assertFalse(a["pronta_para_gerar"])
        self.assertEqual(a["resumo"], {"nao_tenho": 0, "tenho": 0, "sem_resposta": 3})  # 2 motivos sem pergunta
        self.assertEqual(set(a["grupos"]), set(rep.GRUPOS))
        primeira = a["criada_em"]
        self.analisar("v2")
        self.analisar("v1", {"motivos": [ANALISE["motivos"][0]], "perguntas": [ANALISE["perguntas"][0]]})
        self.assertEqual(len(rep.obter("v1")["motivos"]), 1)  # só a última da vaga
        self.assertEqual(len(rep.obter("v2")["motivos"]), 5)  # a da outra vaga não muda
        self.assertGreaterEqual(rep.anterior("v1"), primeira)

    def test_aviso_de_integridade_e_falhas(self):
        with mock.patch.object(banco, "obter", return_value={**self.vaga(), "integridade": {"tipo": "oculto"}}):
            a = self.analisar()
        self.assertIn("integridade", a["avisos"][0])
        with self.assertRaises(rep.ReprovacaoErro):
            rep.analisar(self.vaga("v3"), TEC)  # sem descrição
        self.respostas_ia.append(ia.IAErro("fora do ar"))
        with self.assertRaises(rep.ReprovacaoErro):
            rep.analisar(self.vaga(), TEC)
        self.assertEqual(len(rep.obter("v1")["motivos"]), 5)  # a anterior continua


class TestRespostas(Base):  # T020
    def test_respostas_e_estados(self):
        self.analisar()
        n_ingles = str(len(rep.obter("v1")["perguntas"]))
        a = rep.gravar_respostas("v1", {"1": {"resposta": "nao"}})
        self.assertEqual(a["resumo"]["nao_tenho"], 1)
        a = rep.gravar_respostas("v1", {"2": {"resposta": "tenho", "relato": "", "destino": "perfil"}})
        self.assertFalse(a["pronta_para_gerar"])  # tenho vazio não conta
        a = rep.gravar_respostas("v1", {"2": {"resposta": "tenho", "relato": "Fazia CTEs. CPF 123.456.789-09",
                                              "destino": "perfil"}, n_ingles: {"resposta": "pular"}})
        self.assertTrue(a["pronta_para_gerar"])
        self.assertNotIn("123.456.789-09", a["respostas"]["2"]["relato"])
        estados = {m["grupo"]: m["estado"] for m in a["motivos"]}
        self.assertEqual(estados, {"requisito_nao_comprovado": "nao_tenho", "experiencia_generica": "tenho",
                                   "competencia_sem_evidencia": "sem_pergunta", "informacao_ausente": "sem_resposta",
                                   "resultado_pouco_claro": "sem_pergunta"})
        self.assertEqual(a["resumo"], {"nao_tenho": 1, "tenho": 1, "sem_resposta": 1})
        self.assertEqual(rep.obter("v1")["respostas"]["1"], {"resposta": "nao"})  # guardadas
        for ruim in ({"9": {"resposta": "nao"}}, {"1": {"resposta": "talvez"}},
                     {"1": {"resposta": "tenho", "relato": "x", "destino": "lixo"}}, ["1"]):
            with self.assertRaises(rep.ReprovacaoErro):
                rep.gravar_respostas("v1", ruim)
        with self.assertRaises(rep.ReprovacaoErro):
            rep.gravar_respostas("v2", {"1": {"resposta": "nao"}})  # sem análise

    def test_tenho_vence_nao_no_mesmo_motivo(self):
        self.analisar(resposta={"motivos": [{"grupo": "informacao_ausente", "motivo": "Falta X.", "trecho_vaga": "X",
                                             "perguntas": [1, 2]}],
                                "perguntas": [{"n": 1, "texto": "Já fez X?"}, {"n": 2, "texto": "Já fez X de outro jeito?"}]})
        a = rep.gravar_respostas("v1", {"1": {"resposta": "nao"}, "2": {"resposta": "tenho", "relato": "Fiz X."}})
        self.assertEqual(a["motivos"][0]["estado"], "tenho")


class TestReescritaEGeracao(Base):  # T025
    def preparar(self):
        self.gerar_cv_da_vaga()
        self.analisar()
        n = len(rep.obter("v1")["perguntas"])
        rep.gravar_respostas("v1", {
            "1": {"resposta": "tenho", "relato": "Usei Tableau por 2 anos na Empresa Alfa para os painéis da diretoria.",
                  "destino": "so_aqui"},
            "2": {"resposta": "tenho", "relato": "Fazia consultas com CTEs para as metas comerciais.", "destino": "perfil"},
            str(n): {"resposta": "nao"}})

    def cv_com_tableau(self):
        c = cv_fiel()
        c["experiencia"][0]["cargos"][0]["itens"].append("Painéis em Tableau por 2 anos para a diretoria")
        return c

    def test_fluxo_completo(self):
        self.preparar()
        self.respostas_ia += [REESCRITA, self.cv_com_tableau()]
        meta = rep.reescrever_e_gerar("v1")
        pedido_reescrita, pedido_cv = self.pedidos[-2], self.pedidos[-1]
        self.assertIn("Com base somente nas informações que eu confirmei", pedido_reescrita)
        self.assertIn("Consultas em SQL para a área comercial", pedido_reescrita)
        self.assertNotIn("Conhecimento em Tableau\n  Trecho", pedido_reescrita)  # requisito_nao_comprovado não é reescrito
        self.assertIn("Usei Tableau por 2 anos", pedido_cv)  # ⚠️ só neste currículo, como fato
        self.assertIn("Consultas em SQL com janelas e CTEs", pedido_cv)  # trecho reescrito
        self.assertIn("NÃO tem (nunca apresente como competência", pedido_cv)
        self.assertTrue(meta["reprovacao"])
        self.assertFalse([p for p in meta["conferencia"]["fatos"] if p.get("tipo") == "numero"])  # o "2" é confirmado
        a = rep.obter("v1")
        self.assertEqual(a["curriculo_gerado"], meta["nome"])
        self.assertEqual(a["reescritos"][0]["motivos"], [1])
        self.assertFalse(a["respostas_mudaram"])
        perfil = self.perfil.read_text(encoding="utf-8")
        self.assertNotIn("Fazia consultas com CTEs", perfil)  # destino perfil: espera a revisão do perfil (spec 050)
        self.assertNotIn("Usei Tableau", perfil)  # só neste currículo
        lista = relatos.listar()
        self.assertEqual([r["relato"] for r in lista], ["Fazia consultas com CTEs para as metas comerciais."])
        self.assertFalse(lista[0]["no_perfil"])
        self.assertEqual((a["para_revisar"], a["levadas_em"]), ([lista[0]["id"]], None))
        self.assertFalse((self.tmp / "perfis-anteriores").exists())  # o perfil não mudou
        with self.assertRaises(rep.ReprovacaoErro):  # o guardado não muda de destino
            rep.gravar_respostas("v1", {"2": {"resposta": "tenho", "relato": "Outra coisa.", "destino": "so_aqui"}})
        rep.gravar_respostas("v1", {"1": {"resposta": "pular"}})
        self.assertTrue(rep.obter("v1")["respostas_mudaram"])

    def test_numero_inventado_na_reescrita_vira_aviso(self):
        self.preparar()
        self.respostas_ia += [[{"original": "Consultas em SQL para a área comercial",
                                "novo": "Consultas em SQL que cortaram 45% do tempo", "motivos": [1, 99]}],
                              cv_fiel()]
        rep.reescrever_e_gerar("v1")
        r = rep.obter("v1")["reescritos"][0]
        self.assertEqual(r["motivos"], [1])
        self.assertTrue(any("45%" in a for a in r["avisos"]))

    def test_tentar_de_novo_nao_duplica_o_relato(self):
        self.preparar()
        self.respostas_ia.append(ia.IAErro("fora do ar"))
        with self.assertRaises(rep.ReprovacaoErro):
            rep.reescrever_e_gerar("v1")
        self.respostas_ia += [REESCRITA, cv_fiel()]
        rep.reescrever_e_gerar("v1")
        self.assertNotIn("Fazia consultas com CTEs", self.perfil.read_text(encoding="utf-8"))
        self.assertEqual(len(relatos.listar()), 1)
        self.assertEqual(len(rep.obter("v1")["para_revisar"]), 1)

    def test_sem_perguntas_e_pendentes(self):
        self.analisar(resposta={"motivos": [{"grupo": "requisito_nao_comprovado", "motivo": "Sem Tableau no currículo.",
                                             "trecho_vaga": "Conhecimento em Tableau", "perguntas": []}], "perguntas": []})
        self.assertTrue(rep.obter("v1")["pronta_para_gerar"])
        self.respostas_ia.append(cv_fiel())  # nada a reescrever: vai direto ao currículo
        self.assertTrue(rep.reescrever_e_gerar("v1")["reprovacao"])
        self.analisar()
        with self.assertRaises(rep.ReprovacaoErro):
            rep.reescrever_e_gerar("v1")

    def test_sem_marca_o_curriculo_segue_igual(self):  # SC-001
        self.assertEqual(cia.montar_pedido(PERFIL, self.vaga(), cia.validar_tecnicas(TEC)),
                         cia.montar_pedido(PERFIL, self.vaga(), cia.validar_tecnicas(TEC), ""))
        self.assertNotIn("reprovacao", self.gerar_cv_da_vaga())


class TestGeradorERotas(Base):  # T008, T020, T025, T035
    def setUp(self):
        super().setUp()
        import http.client

        import servidor
        self.http, self.servidor = http.client, servidor
        self.geracao = gerador.Geracao()
        for p in (mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"}),
                  mock.patch.object(gerador, "GERACAO", self.geracao)):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = self.http.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else (b"{}" if metodo != "GET" else None)
        headers = {"Content-Type": "application/json"} if (dados is not None or metodo != "GET") else {}
        con.request(metodo, caminho, dados, headers)
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def esperar(self):
        for _ in range(200):
            if not self.geracao.rodando():
                return self.geracao.estado()
            time.sleep(0.02)
        self.fail("a geração não terminou")

    def test_fluxo_pelas_rotas(self):
        status, j = self.pedir("GET", "/api/curriculo/catalogo?vaga=v1")
        self.assertEqual(j["reprovacao"], {"disponivel": True, "motivo": "", "anterior": None})
        self.assertFalse(self.pedir("GET", "/api/curriculo/catalogo?vaga=v3")[1]["reprovacao"]["disponivel"])
        self.assertNotIn("reprovacao", self.pedir("GET", "/api/curriculo/catalogo")[1])
        self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao", {"vaga_id": "v3", "tecnicas": TEC})[0], 400)
        self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao", {"vaga_id": "nada", "tecnicas": TEC})[0], 404)
        self.assertEqual(self.pedir("GET", "/api/curriculo/reprovacao?vaga=v1")[1]["analise"], None)

        self.respostas_ia.append(ia.IAErro("fora do ar"))
        status, j = self.pedir("POST", "/api/curriculo/reprovacao", {"vaga_id": "v1", "tecnicas": TEC})
        self.assertEqual((status, j["tipo"], j["situacao"]), (202, "reprovacao", "analisando"))
        e = self.esperar()
        self.assertEqual((e["situacao"], e["pode_tentar"]), ("falha", True))
        self.respostas_ia.append(ANALISE)
        self.assertEqual(self.pedir("POST", "/api/curriculo/tentar", {})[0], 202)
        self.assertEqual(self.esperar()["situacao"], "pronto")
        self.assertFalse((self.tmp / "curriculos").exists())  # nenhum currículo na análise

        status, j = self.pedir("GET", "/api/curriculo/reprovacao?vaga=v1")
        self.assertEqual((status, len(j["analise"]["motivos"]), j["pode_alterar"]), (200, 5, True))
        self.assertIsNotNone(self.pedir("GET", "/api/curriculo/catalogo?vaga=v1")[1]["reprovacao"]["anterior"])
        self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao/v1/gerar", {})[0], 400)  # perguntas pendentes
        self.assertEqual(self.pedir("PUT", "/api/curriculo/reprovacao/v1/respostas",
                                    {"respostas": {"1": {"resposta": "x"}}})[0], 400)
        self.assertEqual(self.pedir("PUT", "/api/curriculo/reprovacao/v2/respostas",
                                    {"respostas": {"1": {"resposta": "nao"}}})[0], 404)
        n = len(j["analise"]["perguntas"])
        status, j = self.pedir("PUT", "/api/curriculo/reprovacao/v1/respostas", {"respostas": {
            str(i): {"resposta": "pular"} for i in range(1, n + 1)}})
        self.assertTrue(j["analise"]["pronta_para_gerar"])

        self.respostas_ia += [REESCRITA, cv_fiel()]
        status, j = self.pedir("POST", "/api/curriculo/reprovacao/v1/gerar", {})
        self.assertEqual((status, j["tipo"], j["situacao"]), (202, "curriculo", "reescrevendo"))
        e = self.esperar()
        self.assertEqual(e["situacao"], "pronto", e.get("mensagem"))
        lista = self.pedir("GET", "/api/curriculo/lista?vaga=v1")[1]["curriculos"]
        self.assertEqual([m.get("reprovacao") for m in lista], [True])
        self.assertEqual(banco.obter("v1")["curriculos"], [lista[0]["nome"]])

    def test_ocupado_e_fora_deste_computador(self):
        trava = threading.Event()
        self.respostas_ia.append(ANALISE)
        original = ia.responder.side_effect

        def lento(pedido, **kw):
            trava.wait(5)
            return original(pedido, **kw)
        ia.responder.side_effect = lento
        self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao", {"vaga_id": "v1", "tecnicas": TEC})[0], 202)
        self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao", {"vaga_id": "v2", "tecnicas": TEC})[0], 409)
        trava.set()
        self.esperar()
        with mock.patch.object(self.servidor.Handler, "_local", return_value=False):
            self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao", {"vaga_id": "v1", "tecnicas": TEC})[0], 403)
            self.assertEqual(self.pedir("PUT", "/api/curriculo/reprovacao/v1/respostas", {"respostas": {}})[0], 403)
            self.assertEqual(self.pedir("POST", "/api/curriculo/reprovacao/v1/gerar", {})[0], 403)
            self.assertFalse(self.pedir("GET", "/api/curriculo/reprovacao?vaga=v1")[1]["pode_alterar"])

    def test_apagar_curriculo_pela_rota(self):
        meta = self.gerar_cv_da_vaga("v1")
        nome = meta["nome"]
        banco.registrar_curriculo("v1", nome)
        self.analisar("v1")
        rep._atualizar("v1", curriculo_gerado=nome, gerado_em="2026-11-19T10:00:00")

        self.assertIn(nome, banco.obter("v1")["curriculos"])
        self.assertEqual(rep.obter("v1")["curriculo_gerado"], nome)
        self.assertTrue((self.tmp / "curriculos" / f"{nome}.json").exists())

        status, j = self.pedir("DELETE", f"/api/curriculo/{nome}")
        self.assertEqual((status, j), (200, {"apagado": nome}))
        self.assertFalse((self.tmp / "curriculos" / f"{nome}.json").exists())
        self.assertFalse((self.tmp / "curriculos" / f"{nome}.meta.json").exists())
        self.assertNotIn(nome, banco.obter("v1")["curriculos"])
        self.assertIsNone(rep.obter("v1")["curriculo_gerado"])
        self.assertIsNone(rep.obter("v1")["gerado_em"])

        self.assertEqual(self.pedir("DELETE", "/api/curriculo/nao-existe")[0], 404)
        self.assertEqual(self.pedir("DELETE", "/api/curriculo/Nome%20Ruim")[0], 400)

        with mock.patch("curriculo_ia.apagar", side_effect=cia.GeracaoErro("um arquivo do currículo está aberto em outro programa; feche e tente de novo")):
            st, err = self.pedir("DELETE", "/api/curriculo/cv-bloqueado")
            self.assertEqual(st, 409)
            self.assertIn("aberto em outro programa", err.get("erro", ""))

        # currículo base (sem vaga ligada)
        self.respostas_ia.append(cv_fiel())
        meta_base = cia.gerar(None, TEC)
        nome_base = meta_base["nome"]
        self.assertTrue((self.tmp / "curriculos" / f"{nome_base}.json").exists())
        st, j_base = self.pedir("DELETE", f"/api/curriculo/{nome_base}")
        self.assertEqual((st, j_base), (200, {"apagado": nome_base}))
        self.assertFalse((self.tmp / "curriculos" / f"{nome_base}.json").exists())

    def test_desligar_curriculo_direto(self):
        banco.desligar_curriculo("vaga_inexistente", "cv-teste")
        banco.registrar_curriculo("v1", "cv-teste")
        self.assertIn("cv-teste", banco.obter("v1")["curriculos"])
        banco.desligar_curriculo("v1", "outro-cv")
        self.assertIn("cv-teste", banco.obter("v1")["curriculos"])
        banco.desligar_curriculo("v1", "cv-teste")
        self.assertNotIn("cv-teste", banco.obter("v1")["curriculos"])

    def test_esquecer_curriculo_direto(self):
        rep.esquecer_curriculo("v1", "cv-teste")
        self.analisar("v1")
        rep._atualizar("v1", curriculo_gerado="cv-original", gerado_em="2026-11-19T10:00:00")
        rep.esquecer_curriculo("v1", "cv-diferente")
        self.assertEqual(rep.obter("v1")["curriculo_gerado"], "cv-original")
        rep.esquecer_curriculo("v1", "cv-original")
        self.assertIsNone(rep.obter("v1")["curriculo_gerado"])
        self.assertIsNone(rep.obter("v1")["gerado_em"])


if __name__ == "__main__":
    unittest.main()
