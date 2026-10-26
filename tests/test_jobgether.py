"""JobGether na busca (fontes/jobgether.py), com respostas fictícias da API e sem rede (spec 030): campos da vaga,
filtro pelo cargo, janela de tempo e páginas, local do país, "anywhere" e híbridas, consultas sem pedido (cidade e
mudança), local recusado, pausa, bloqueio com espera de 24 horas (SC-002), portal desligado por padrão (SC-001), vaga
republicada com o mesmo id (SC-003) e o link no Adicionar Vaga."""
import io
import json
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
import vagas  # noqa: E402
from candidatura import dominios  # noqa: E402
from fontes import FONTES, _comum, jobgether, link  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "jobgether"
LISTA = json.loads((DADOS / "lista.json").read_text(encoding="utf-8"))
LISTA_2 = json.loads((DADOS / "lista-2.json").read_text(encoding="utf-8"))
ERRO_LOCAL = (DADOS / "erro-local.json").read_bytes()
HOJE = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)
CFG = {"termos": ["project manager"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                     "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": False}, "tipos_emprego": [],
       "fontes": ["jobgether"], "janela_horas": 168, "internacional": {"ativo": False}}


def grupos(cfg):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def numeros(lista):
    return [v["id"].removeprefix("jobgether-") for v in lista]


class Resposta:
    def __init__(self, dados):
        self.corpo = json.dumps(dados).encode() if not isinstance(dados, bytes) else dados

    def read(self, n):
        return self.corpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        jobgether._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(jobgether.time, "sleep"),
                  mock.patch.object(jobgether, "_agora", return_value=HOJE),
                  mock.patch.object(_comum.segredos, "ler", return_value=None),
                  mock.patch.object(jobgether, "ARQ_ESPERA", self.tmp / ".cache" / "jobgether-espera.json")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)
        self.abridor([])

    def abridor(self, respostas):
        """urlopen falso: cada pedido devolve o próximo da lista (dict = JSON, int = erro HTTP, (código, corpo) = erro
        HTTP com corpo)."""
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            if isinstance(r, tuple):
                raise urllib.error.HTTPError(req.full_url, r[0], "x", {}, io.BytesIO(r[1]))
            return Resposta(r)
        p = mock.patch.object(_comum.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)

    def corpo(self, i=0):
        return json.loads(self.pedidos[i].data.decode("utf-8"))


class TestBuscaNacional(SemRede):  # US1
    def test_campos_da_vaga(self):
        self.abridor([LISTA, LISTA_2])
        achadas, erros = jobgether.buscar(grupos(CFG)["remoto"], 168, 20)
        self.assertEqual(erros, [])
        # NetSuite Consultant não bate com o cargo; a híbrida fica fora da consulta remota; a de 10/10 sai da janela
        self.assertEqual(numeros(achadas), ["6b0000000000000000000001", "6b0000000000000000000003",
                                            "6a0000000000000000000099", "6b0000000000000000000006"])
        v = achadas[0]
        self.assertEqual(v["plataforma"], "JobGether")
        self.assertEqual(v["titulo"], "Senior Project Manager")
        self.assertEqual(v["empresa"], "Acme Remota")
        self.assertEqual(v["local"], "Remoto (South America, Latin America, Brazil)")
        self.assertEqual(v["restricao_local"], "South America, Latin America, Brazil")
        self.assertTrue(v["remoto"])
        self.assertEqual(v["modelo_trabalho"], "remoto")
        self.assertEqual(v["publicada_em"], "2026-10-24")
        self.assertEqual(v["salario"], "US$ 65.000–70.000")  # sem período: a API não informa
        self.assertEqual(v["moeda"], "USD")
        self.assertEqual(v["tipo"], "Tempo integral")
        self.assertNotIn("tipo_emprego", v)  # tempo integral no exterior não é CLT
        self.assertEqual(v["url"], "https://jobgether.com/offer/6b0000000000000000000001-senior-project-manager")
        self.assertIsNone(v["url_candidatura"])
        self.assertEqual(v["descricao"], "")
        self.assertIsNone(achadas[1]["salario"])
        self.assertEqual((achadas[1]["tipo"], achadas[1]["tipo_emprego"]), ("Meio período", ["meio_periodo"]))
        self.assertEqual((achadas[2]["tipo"], achadas[2]["tipo_emprego"]), ("Temporário", ["temporario"]))
        self.assertEqual(achadas[3]["tipo_emprego"], ["pj"])

    def test_pedido_pela_api(self):
        self.abridor([LISTA, LISTA_2])
        jobgether.buscar({**grupos(CFG)["remoto"], "termo": '"project manager"'}, 168, 20)
        req = self.pedidos[0]
        self.assertEqual((req.full_url, req.get_method()), (jobgether.URL, "POST"))
        self.assertEqual(req.get_header("User-agent"), _comum.AGENTE)
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertIsNone(req.get_header("Cookie"))
        self.assertNotIn("?", req.full_url)  # o robots.txt bloqueia query string
        self.assertEqual(self.corpo(0), {"keyword": "project manager", "locations": ["brazil"], "sort": "date",
                                         "limit": 25, "page": 1})
        self.assertEqual(self.corpo(1)["page"], 2)

    def test_janela_corta_a_segunda_pagina(self):
        self.abridor([LISTA])
        achadas, _ = jobgether.buscar(grupos(CFG)["remoto"], 72, 20)  # janela de 3 dias: desde 22/10
        self.assertEqual(numeros(achadas), ["6b0000000000000000000001", "6b0000000000000000000003"])
        self.assertEqual(len(self.pedidos), 1)

    def test_sem_mais_paginas_para(self):
        self.abridor([LISTA, LISTA_2])
        achadas, _ = jobgether.buscar(grupos(CFG)["remoto"], 720, 20)
        self.assertIn("6b0000000000000000000007", numeros(achadas))
        self.assertEqual(len(self.pedidos), 2)  # hasMore falso na página 2: nada de página 3

    def test_no_maximo_tres_paginas(self):
        mais = {**LISTA, "jobs": LISTA_2["jobs"][:1], "pagination": {"hasMore": True}}
        self.abridor([LISTA, mais, mais, mais])
        jobgether.buscar(grupos(CFG)["remoto"], 720, 20)
        self.assertEqual(len(self.pedidos), jobgether.MAX_PAGINAS)

    def test_pais_com_hibridas(self):
        cfg = {**CFG, "localidade": {"pais": "Brasil", "estado": "", "cidade": "", "raio_km": None}}
        self.abridor([LISTA, LISTA_2])
        achadas, _ = jobgether.buscar(grupos(cfg)["pais"], 168, 20)
        self.assertTrue(self.corpo(0)["includeHybrid"])
        hibrida = next(v for v in achadas if v["titulo"] == "Technical Project Manager")
        self.assertEqual((hibrida["local"], hibrida["remoto"], hibrida["modelo_trabalho"]),
                         ("Híbrido (Brazil)", False, "hibrido"))

    def test_cidade_sem_pedido(self):
        self.assertEqual(jobgether.buscar(grupos(CFG)["local"], 168, 20), ([], []))
        self.assertEqual(self.pedidos, [])

    def test_mesma_consulta_lida_uma_vez(self):
        self.abridor([LISTA, LISTA_2])
        c = grupos(CFG)["remoto"]
        primeira = jobgether.buscar(c, 168, 20)
        self.assertEqual(jobgether.buscar({**c, "termo": '"Project Manager"'}, 168, 20)[0], primeira[0])
        self.assertEqual(len(self.pedidos), 2)

    def test_vaga_republicada_com_o_mesmo_id(self):  # SC-003
        original = LISTA["jobs"][4]
        republicada = {**original, "id": "6c0000000000000000000123", "postedAt": "2026-10-25T08:00:00.000Z"}
        self.assertEqual(jobgether.normalizar(original)["id"], jobgether.normalizar(republicada)["id"])
        self.assertEqual(jobgether.normalizar({**original, "url": ""})["id"], "jobgether-6b0000000000000000000005")
        self.assertIsNone(jobgether.normalizar({**original, "title": " "}))

    def test_id_do_link(self):
        self.assertEqual(jobgether.id_do_link("https://www.jobgether.com/offer/6A0000000000000000000099-pm?x=1"),
                         "jobgether-6a0000000000000000000099")
        self.assertIsNone(jobgether.id_do_link("https://jobgether.com/search-offers?keyword=pm"))
        self.assertIsNone(jobgether.id_do_link("https://exemplo.com/offer/6a0000000000000000000099-pm"))


INTER = {**CFG, "internacional": {"ativo": True, "paises": ["Portugal", "Estados Unidos", "República Tcheca"],
                                  "termos": ["project manager"], "aceita_mudar": True}}


class TestBuscaInternacional(SemRede):  # US2
    def test_local_de_cada_consulta(self):
        g = grupos(INTER)
        self.abridor([LISTA, LISTA_2, LISTA, LISTA_2, LISTA, LISTA_2])
        jobgether.buscar(g["internacional:Portugal"], 168, 20)
        jobgether.buscar(g["internacional:Estados Unidos"], 168, 20)
        jobgether.buscar(g[filtros.GLOBAL], 168, 20)
        self.assertEqual([self.corpo(i)["locations"] for i in (0, 2, 4)], [["portugal"], ["united-states"],
                                                                           ["anywhere"]])
        self.assertNotIn("includeHybrid", self.corpo(4))  # "mundo todo" é só remoto

    def test_mudanca_sem_pedido(self):
        self.assertEqual(jobgether.buscar(grupos(INTER)["mudanca:Portugal"], 168, 20), ([], []))
        self.assertEqual(self.pedidos, [])

    def test_local_recusado_avisa_uma_vez(self):
        g = grupos(INTER)
        self.abridor([(400, ERRO_LOCAL), LISTA, LISTA_2])
        achadas, erros = jobgether.buscar(g["internacional:República Tcheca"], 168, 20)
        self.assertEqual(self.corpo(0)["locations"], ["czech-republic"])
        self.assertEqual(achadas, [])
        self.assertEqual(erros, ["o JobGether não reconhece o local czech-republic; a busca seguiu sem ele"])
        outro = {**g["internacional:República Tcheca"], "termo": "data analyst"}
        self.assertEqual(jobgether.buscar(outro, 168, 20), ([], []))  # o mesmo local, sem pedido nem novo aviso
        self.assertTrue(jobgether.buscar(g["internacional:Portugal"], 168, 20)[0])  # os outros locais seguem
        self.assertEqual(len(self.pedidos), 3)
        self.assertFalse(jobgether.parada())  # local recusado não é bloqueio

    def test_consulta_global_com_o_jobgether(self):
        cfg = {**INTER, "internacional": {"ativo": True, "paises": [], "termos": ["project manager"]}}
        self.assertIn(filtros.GLOBAL, grupos(cfg))  # sem fontes do exterior nem empresas, só pelo JobGether
        self.assertNotIn(filtros.GLOBAL, grupos({**cfg, "fontes": ["indeed"]}))
        plano = filtros.consultas(filtros.efetivos(INTER))
        atendidas = {c["grupo"] for c in plano if vagas.atende(jobgether, c)}
        self.assertTrue({"remoto", "local", "internacional:Portugal", "mudanca:Portugal", filtros.GLOBAL} <= atendidas)


class TestDesligadoPorPadrao(SemRede):  # US3, SC-001
    def test_fora_da_configuracao_nova(self):
        self.assertIn("jobgether", FONTES)
        self.assertNotIn("jobgether", filtros.FONTES_PADRAO)
        self.assertNotIn("jobgether", vagas.fontes_da_busca({}, filtros.efetivos({})))
        cfg = {"termos": ["project manager"], "fontes": ["indeed", "gupy"]}
        self.assertEqual(vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)), ["indeed", "gupy"])
        exemplo = json.loads((RAIZ / "config.exemplo.json").read_text(encoding="utf-8"))
        self.assertNotIn("jobgether", exemplo.get("fontes") or filtros.FONTES_PADRAO)

    def test_termos_no_painel(self):
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertEqual(nomes["jobgether"]["rotulo"], "JobGether")
        self.assertIn("proíbem acesso automatizado", nomes["jobgether"]["termos"])
        self.assertIn("spec 030", nomes["jobgether"]["termos"])
        self.assertEqual(nomes["jobgether"]["precisa"], "")

    def test_ligado_pela_pessoa(self):
        cfg = {**CFG, "fontes": ["indeed", "jobgether"]}
        self.assertEqual(vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)), ["indeed", "jobgether"])
        self.assertEqual(filtros.validar({**cfg, "fontes": ["jobgether"]})["fontes"], ["jobgether"])


class TestPausaEBloqueio(SemRede):  # US4, SC-002
    def pausa_com(self, valor):
        with mock.patch.object(_comum.segredos, "ler", return_value=valor):
            return jobgether.pausa()

    def test_pausa(self):
        self.assertEqual(self.pausa_com(None), {"faixa": (2.0, 2.0), "definida": False, "ajuste": ""})
        self.assertEqual(self.pausa_com("5")["faixa"], (5.0, 5.0))
        baixa = self.pausa_com("1")
        self.assertEqual(baixa["faixa"], (2.0, 2.0))
        self.assertIn("mínimo de 2 segundos", baixa["ajuste"])
        self.assertEqual(self.pausa_com("abc")["faixa"], (2.0, 2.0))
        self.assertIn("não é um número", self.pausa_com("abc")["ajuste"])
        with mock.patch.object(_comum.segredos, "ler", return_value="4"):
            aviso = jobgether.aviso_pausa(2)
        self.assertTrue(aviso.startswith("JobGether: pausa de 4 s entre os pedidos (JOBGETHER_PAUSA)"), aviso)
        self.assertIsNone(jobgether.aviso_pausa(2))  # sem a variável, sem aviso

    def test_bloqueio_poe_em_espera_de_24_horas(self):
        for codigo in (403, 429):
            with self.subTest(codigo=codigo):
                _comum.esquecer()
                if jobgether.ARQ_ESPERA.exists():
                    jobgether.ARQ_ESPERA.unlink()
                self.abridor([codigo])
                c = grupos(CFG)["remoto"]
                achadas, erros = jobgether.buscar(c, 168, 20)
                self.assertEqual(achadas, [])
                self.assertTrue(erros[0].startswith(f"{jobgether.BLOQUEIO} (código {codigo}); em espera até "), erros)
                self.assertTrue(jobgether.parada())
                self.assertEqual(jobgether.buscar({**c, "termo": "data analyst"}, 168, 20), ([], []))
                self.assertEqual(len(self.pedidos), 1)  # sem nova tentativa e sem pedido a mais
                e = jobgether.espera()
                self.assertEqual(e["motivo"], f"código {codigo}")
                horas = (datetime.fromisoformat(e["ate"]) - datetime.now()).total_seconds() / 3600
                self.assertAlmostEqual(horas, 24, delta=0.1)
                self.assertEqual([x["nome"] for x in vagas.fontes_em_espera(["indeed", "jobgether"])], ["jobgether"])

    def test_vagas_lidas_antes_do_bloqueio_seguem(self):
        self.abridor([LISTA, 429])
        achadas, erros = jobgether.buscar(grupos(CFG)["remoto"], 168, 20)
        self.assertEqual(len(achadas), 3)  # as da página 1 que batem com o cargo e são remotas
        self.assertIn("código 429", erros[0])

    def test_na_espera_nenhum_pedido(self):
        jobgether._bloquear("código 429")
        _comum.esquecer()  # a busca seguinte, ainda na espera
        c = grupos(CFG)
        vagas_, erros = jobgether.buscar(c["remoto"], 168, 20)
        self.assertEqual(vagas_, [])
        self.assertTrue(erros[0].startswith("JobGether em espera até "), erros)
        self.assertEqual(jobgether.buscar({**c["remoto"], "termo": "data analyst"}, 168, 20), ([], []))
        self.assertEqual(self.pedidos, [])
        self.assertIsNone(vagas.aviso_pausa(filtros.efetivos(CFG), ["jobgether"]))  # em espera, sem aviso de pausa

    def test_outro_erro_vale_so_para_a_consulta(self):
        self.abridor([504, LISTA, LISTA_2])
        c = grupos(CFG)["remoto"]
        self.assertEqual(jobgether.buscar(c, 168, 20), ([], ["o JobGether respondeu 504"]))
        self.assertFalse(jobgether.parada())
        self.assertTrue(jobgether.buscar({**c, "termo": "senior project manager"}, 168, 20)[0])
        self.assertEqual(len(self.pedidos), 3)

    def test_resposta_fora_do_formato(self):
        self.abridor([{"vagas": []}])
        self.assertEqual(jobgether.buscar(grupos(CFG)["remoto"], 168, 20), ([], [jobgether.ILEGIVEL]))


class TestAdicionarVaga(SemRede):  # US5
    URL = "https://jobgether.com/offer/6b0000000000000000000001-senior-project-manager"

    def setUp(self):
        super().setUp()
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json")):
            p.start()
            self.addCleanup(p.stop)

    def test_link_sem_pedido(self):
        self.assertEqual(link.plataforma("jobgether.com"), "JobGether")
        with mock.patch.object(link, "_baixar", side_effect=AssertionError("não pode pedir a página")):
            with self.assertRaises(link.LinkErro) as ctx:
                link.ler(self.URL)
        self.assertIn("complete cargo, empresa e descrição", str(ctx.exception))
        self.assertEqual(ctx.exception.parcial, {"plataforma": "JobGether", "url": self.URL})
        self.assertIn("JobGether", banco.PLATAFORMAS)

    def test_vaga_manual_com_o_id_da_busca(self):
        campos = {"titulo": "Senior Project Manager", "empresa": "Acme Remota", "url": self.URL,
                  "plataforma": "JobGether", "etapa": "relatorio"}
        vaga, nova = banco.criar_manual(campos)
        self.assertTrue(nova)
        self.assertEqual((vaga["id"], vaga["plataforma"]), ("jobgether-6b0000000000000000000001", "JobGether"))
        de_novo, nova = banco.criar_manual({**campos, "titulo": "Outro título"})
        self.assertFalse(nova)  # a busca (ou outra aba) já trouxe: devolve a que existe
        self.assertEqual(de_novo["titulo"], "Senior Project Manager")
        outra, _ = banco.criar_manual({**campos, "url": "https://exemplo.com/vaga/1", "plataforma": "Outra"})
        self.assertTrue(outra["id"].startswith("m-"))

    def test_candidatura_assistida_bloqueada(self):
        s = dominios.situacao(self.URL)
        self.assertFalse(s["permitido"])
        self.assertIn("JobGether", s["bloqueado"])


if __name__ == "__main__":
    unittest.main()
