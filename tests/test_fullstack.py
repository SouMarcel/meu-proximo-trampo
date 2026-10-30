"""FullStack na busca (fontes/fullstack.py), com JSON fictício e sem rede (spec 040): leitura e agrupamento das
publicações, nenhum e-mail de recrutador gravado, uma leitura por busca para todos os cargos, janela, modelos, cidade e
outro país sem pedido, descrição pelo detalhe, bloqueio com espera de 24 horas, pausa, link no Adicionar Vaga e o portal
desligado por padrão."""
import json
import re
import shutil
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import segredos  # noqa: E402
import vagas  # noqa: E402
from candidatura import dominios  # noqa: E402
from fontes import FONTES, _comum, fullstack, link  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "fullstack"
LISTA_1 = json.loads((DADOS / "lista-1.json").read_text(encoding="utf-8"))
LISTA_2 = json.loads((DADOS / "lista-2.json").read_text(encoding="utf-8"))
DETALHE = json.loads((DADOS / "detalhe.json").read_text(encoding="utf-8"))
HOJE = datetime(2026, 10, 30, 15, tzinfo=timezone.utc)
CFG = {"termos": ["engineer"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo", "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "tipos_emprego": [],
       "fontes": ["fullstack"], "janela_horas": 168, "internacional": {"ativo": False}}
PUB_1 = "00000001-aaaa-4aaa-8aaa-000000000001"
JOB_1 = "fullstack-11111111-bbbb-4bbb-8bbb-111111111111"
URL_1 = "https://talent.fullstack.com/jobs/" + PUB_1


def grupos(cfg=CFG):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def pais(modelos=("remoto", "hibrido", "presencial"), termo="engineer"):
    return {**grupos()["remoto"], "grupo": "pais", "remoto": False, "modelos": list(modelos), "termo": termo}


def jobs(lista):
    """O número da vaga fictícia (o dígito do jobId "1111111<n>-…")."""
    return [int(re.match(r"fullstack-1111111(\d)", v["id"]).group(1)) for v in lista]


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        fullstack._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(fullstack, "PAUSA", (0, 0)), mock.patch.object(fullstack.time, "sleep"),
                  mock.patch.object(fullstack, "_agora", return_value=HOJE),
                  mock.patch.object(fullstack, "ARQ_ESPERA", self.tmp / ".cache" / "fullstack-espera.json"),
                  mock.patch.object(segredos, "ler", return_value="")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def respostas(self, paginas=None):
        """Troca fullstack._baixar: a lista pela página pedida e o detalhe de qualquer publicação."""
        self.pedidos = []
        paginas = paginas or {1: LISTA_1, 2: LISTA_2}

        def baixar(caminho, params=None):
            self.pedidos.append((caminho, params))
            if caminho == "job-postings/public":
                r = paginas[params["page"]]
                if isinstance(r, Exception):
                    raise r
                return r
            return DETALHE
        p = mock.patch.object(fullstack, "_baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)

    def abridor(self, respostas):
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            resp = mock.MagicMock()
            resp.__enter__.return_value = resp
            resp.read.return_value = json.dumps(r).encode()
            return resp
        p = mock.patch.object(fullstack.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)


class TestLeitura(SemRede):
    def test_publicacoes_agrupadas_pela_vaga(self):
        vs = fullstack.ler_lista(LISTA_1["data"] + LISTA_2["data"])
        self.assertEqual(jobs(vs), [1, 2, 3, 4, 5])  # a 1 e a 2 estavam em duas cidades
        dados, ml, executivo, devops, _ = vs
        self.assertEqual(dados["id"], JOB_1)
        self.assertEqual({k: dados[k] for k in ("plataforma", "titulo", "empresa", "local", "remoto", "publicada_em",
                                                 "url", "tipo", "tipo_emprego", "idioma", "modelo_trabalho",
                                                 "restricao_local", "descricao")},
                         {"plataforma": "FullStack", "titulo": "Senior Data Engineer (Python + AWS) - Remote - Latin America",
                          "empresa": "FullStack", "local": "Remoto", "remoto": True, "publicada_em": "2026-10-28",
                          "url": URL_1, "tipo": "Senior • Tempo integral", "tipo_emprego": [], "idioma": "en",
                          "modelo_trabalho": "remoto", "restricao_local": "América Latina", "descricao": ""})
        self.assertEqual((ml["tipo"], ml["tipo_emprego"]), ("Mid-Level • Contrato", ["pj"]))
        self.assertEqual(devops["tipo_emprego"], ["temporario"])
        self.assertEqual((executivo["local"], executivo["remoto"], executivo["modelo_trabalho"]),
                         ("São Paulo, São Paulo, Brazil", False, "hibrido"))
        self.assertNotIn("restricao_local", executivo)

    def test_nenhum_email_nem_id_interno(self):
        texto = json.dumps(fullstack.ler_lista(LISTA_1["data"] + LISTA_2["data"]))
        for proibido in ("exemplo.invalid", "ownerEmail", "authorId", "formId", "55555555", "22222222"):
            self.assertNotIn(proibido, texto)

    def test_itens_fora_do_formato(self):
        self.assertEqual(fullstack.ler_lista([{}, "x", {"jobId": "a", "id": "b"}, None]), [])
        self.assertEqual(fullstack.ler_lista(None), [])

    def test_descricao_do_detalhe(self):
        texto = fullstack._descricao(DETALHE)
        self.assertTrue(texto.startswith("About FullStack\n\nConsultoria fictícia"))
        self.assertIn("The Role\n\nConstruir pipelines de dados com Python.", texto)
        self.assertIn("- AWS", texto)
        self.assertTrue(texto.endswith("Habilidades: Python, AWS, dbt"))
        self.assertEqual(fullstack._descricao({}), "")


class TestBusca(SemRede):
    def test_uma_leitura_para_todos_os_cargos(self):
        self.respostas()
        remoto, erros = fullstack.buscar(grupos()["remoto"], 168, 20)
        self.assertEqual((jobs(remoto), erros), ([1, 2, 4], []))  # 3 não bate; 5 é antiga
        dados, _ = fullstack.buscar({**grupos()["remoto"], "termo": '"data engineer"'}, 168, 20)
        self.assertEqual(jobs(dados), [1])
        self.assertEqual([p[0] for p in self.pedidos], ["job-postings/public"] * 2)  # as duas páginas, uma vez
        self.assertEqual(self.pedidos[0][1], {"page": 1, "take": 30,
                                              "filter": "countryId=1ae07c37-d911-413f-9160-8cd2a5d93257"})

    def test_cidade_e_outro_pais_sem_pedido(self):
        self.respostas()
        self.assertEqual(fullstack.buscar(grupos()["local"], 168, 20), ([], []))
        self.assertEqual(fullstack.buscar({**grupos()["remoto"], "pais": "usa"}, 168, 20), ([], []))
        self.assertEqual(self.pedidos, [])

    def test_modelos_na_consulta_do_pais(self):
        self.respostas()
        hibrida, _ = fullstack.buscar(pais(("hibrido", "presencial"), "account executive"), 168, 20)
        self.assertEqual(jobs(hibrida), [3])
        self.assertEqual(fullstack.buscar(pais(("hibrido", "presencial")), 168, 20), ([], []))  # as engineer são remotas
        self.assertEqual(jobs(fullstack.buscar(pais(), 168, 20)[0]), [1, 2, 4])

    def test_janela(self):
        self.respostas()
        self.assertEqual(jobs(fullstack.buscar(grupos()["remoto"], 24 * 60, 20)[0]), [1, 2, 4, 5])
        self.assertEqual(jobs(fullstack.buscar(grupos()["remoto"], 24 * 5, 20)[0]), [1, 2])  # desde 25/10

    def test_limite_de_paginas_e_por_termo(self):
        self.respostas()
        with mock.patch.object(fullstack, "MAX_PAGINAS", 1):
            self.assertEqual(jobs(fullstack.buscar(grupos()["remoto"], 168, 20)[0]), [1, 2])
        self.assertEqual(len(self.pedidos), 1)
        self.assertEqual(len(fullstack.buscar(grupos()["remoto"], 168, 1)[0]), 1)

    def test_resposta_fora_do_formato(self):
        self.respostas({1: {"message": "x"}})
        self.assertEqual(fullstack.buscar(grupos()["remoto"], 168, 20), ([], [fullstack.ILEGIVEL]))

    def test_erro_comum_vale_so_para_a_busca(self):
        self.respostas({1: LISTA_1, 2: _comum.FonteErro("a FullStack respondeu 500")})
        vs, erros = fullstack.buscar(grupos()["remoto"], 168, 20)
        self.assertEqual((jobs(vs), erros), ([1, 2], ["a FullStack respondeu 500"]))
        self.assertFalse(fullstack.parada())
        self.assertIsNone(fullstack.espera())

    def test_descrever(self):
        self.respostas()
        v = fullstack.buscar(grupos()["remoto"], 168, 20)[0][0]
        self.assertIn("Habilidades: Python, AWS, dbt", fullstack.descrever(v))
        self.assertEqual(self.pedidos[-1], (f"job-postings/{PUB_1}", None))
        with self.assertRaises(_comum.FonteErro):
            fullstack.descrever({"url": "https://talent.fullstack.com/dashboard"})


class TestBloqueio(SemRede):
    def test_codigos_de_bloqueio(self):
        for codigo in (401, 403, 429, 503):
            _comum.esquecer()
            fullstack.ARQ_ESPERA.unlink(missing_ok=True)
            self.abridor([codigo])
            vs, erros = fullstack.buscar(grupos()["remoto"], 168, 20)
            self.assertEqual(vs, [])
            self.assertTrue(erros[0].startswith(f"{fullstack.BLOQUEIO} (código {codigo}); em espera até "), erros)
            self.assertEqual(len(self.pedidos), 1)  # sem nova tentativa
            self.assertIsNotNone(fullstack.espera())

    def test_bloqueio_na_segunda_pagina(self):
        self.abridor([LISTA_1, 429])
        vs, erros = fullstack.buscar(grupos()["remoto"], 168, 20)
        self.assertEqual(jobs(vs), [1, 2])  # a página já lida vale
        self.assertEqual(len(erros), 1)
        self.assertEqual(fullstack.buscar({**grupos()["remoto"], "termo": "data"}, 168, 20)[1], [])
        self.assertEqual(len(self.pedidos), 2)

    def test_espera_sem_pedido(self):
        self.abridor([403])
        fullstack.buscar(grupos()["remoto"], 168, 20)
        _comum.esquecer()
        self.abridor([])
        vs, erros = fullstack.buscar(grupos()["remoto"], 168, 20)
        self.assertEqual(vs, [])
        self.assertTrue(erros[0].startswith("FullStack em espera até "), erros)
        self.assertEqual(fullstack.buscar({**grupos()["remoto"], "termo": "data"}, 168, 20), ([], []))  # aviso uma vez
        self.assertTrue(fullstack.parada())
        self.assertEqual(fullstack.descrever({"url": URL_1, "descricao": "texto antigo"}), "texto antigo")
        with self.assertRaises(link.LinkErro) as e:
            link.ler(URL_1)
        self.assertEqual(e.exception.parcial, {"plataforma": "FullStack", "url": URL_1})
        self.assertEqual([x["nome"] for x in vagas.fontes_em_espera(["fullstack"])], ["fullstack"])
        self.assertEqual(self.pedidos, [])

    def test_pedido_sem_cookies_com_json(self):
        self.abridor([LISTA_2])
        fullstack.buscar(grupos()["remoto"], 168, 20)
        req = self.pedidos[0]
        self.assertEqual(req.full_url, "https://api-v1.fullstack.com/api/job-postings/public?page=1&take=30"
                                       "&filter=countryId%3D1ae07c37-d911-413f-9160-8cd2a5d93257")
        self.assertEqual(req.get_header("Accept"), "application/json")
        self.assertIsNone(req.get_header("Cookie"))


class TestPausa(unittest.TestCase):
    def pausa(self, valor):
        with mock.patch.object(segredos, "ler", side_effect=lambda nome: valor if nome == "FULLSTACK_PAUSA" else ""):
            return fullstack.pausa(), fullstack.aviso_pausa(3)

    def test_padrao_env_minimo_e_invalido(self):
        p, aviso = self.pausa("")
        self.assertEqual((p["faixa"], aviso), ((3.0, 7.0), None))
        p, aviso = self.pausa("10")
        self.assertEqual(p["faixa"], (10.0, 14.0))
        self.assertIn("FullStack: pausa de 10 a 14 s entre os pedidos (FULLSTACK_PAUSA)", aviso)
        p, aviso = self.pausa("2")
        self.assertEqual(p["faixa"], (3.0, 7.0))
        self.assertIn("abaixo do mínimo", aviso)
        p, aviso = self.pausa("abc")
        self.assertEqual(p["faixa"], (3.0, 7.0))
        self.assertIn("não é um número", aviso)


class TestPadraoELink(SemRede):
    def test_desligada_por_padrao(self):
        self.assertIn("fullstack", FONTES)
        self.assertNotIn("fullstack", filtros.efetivos({})["fontes"])
        self.assertIn("fullstack", filtros.efetivos({"fontes": ["fullstack"]})["fontes"])
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertEqual(nomes["fullstack"]["rotulo"], "FullStack")
        self.assertIn("proíbem acesso automatizado", nomes["fullstack"]["termos"])
        self.assertIn("FullStack", banco.PLATAFORMAS)

    def test_adicionar_vaga_pelo_link(self):
        self.assertEqual(link.plataforma("talent.fullstack.com"), "FullStack")
        self.assertEqual(link.plataforma("www.fullstack.com"), "Outra")
        self.respostas()
        v = link.ler(URL_1 + "/apply")
        self.assertEqual((v["id"], v["plataforma"], v["empresa"], v["url"], v["publicada_em"]),
                         (JOB_1, "FullStack", "FullStack", URL_1, "2026-10-28"))  # o mesmo id da busca
        self.assertIn("Habilidades: Python, AWS, dbt", v["descricao"])
        self.assertTrue(banco.ID_VALIDO.match(v["id"]))
        self.assertEqual(self.pedidos, [(f"job-postings/{PUB_1}", None)])
        with self.assertRaises(link.LinkErro):
            link.ler("https://talent.fullstack.com/dashboard")
        self.assertIsNone(fullstack.id_do_link(URL_1))

    def test_candidatura_assistida_segue_liberada(self):  # FR-011
        self.assertIsNone(dominios.bloqueio("talent.fullstack.com"))


if __name__ == "__main__":
    unittest.main()
