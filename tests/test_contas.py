"""Contas conectadas (spec 018), com respostas fictícias e uma aba falsa (sem navegador e sem rede): tradução dos
status da Gupy, do Indeed e do LinkedIn, proposta para o quadro, aplicar só o marcado e a leitura em segundo plano."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import contas  # noqa: E402
import filtros  # noqa: E402
import sincronia  # noqa: E402
from contas import gupy, indeed, linkedin  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "contas"
LISTA = json.loads((DADOS / "gupy-lista.json").read_text(encoding="utf-8"))
ETAPAS = json.loads((DADOS / "gupy-etapas.json").read_text(encoding="utf-8"))
APLICADAS = json.loads((DADOS / "indeed-applied.json").read_text(encoding="utf-8"))
HOJE = date(2026, 10, 18)


def dia(ms):  # o dia de um timestamp no fuso deste computador, como o leitor faz
    return datetime.fromtimestamp(ms / 1000).date().isoformat()


class AbaFalsa:
    """Responde aos fetch da página pelo endereço; guarda as páginas visitadas e o JavaScript pedido."""

    def __init__(self, respostas, login=None):
        self.respostas, self.login, self.atual, self.visitas, self.js = respostas, login, "", [], []

    def ir(self, url):
        self.atual = url
        self.visitas.append(url)

    def url(self):
        return self.login or self.atual

    def frente(self):
        pass

    def minimizar(self):
        self.minimizada = True

    def fechar(self):
        self.conexao_fechada = True

    def avaliar(self, js):
        self.js.append(js)
        alvo = json.loads(re.search(r"fetch\((\".*?\")", js).group(1))
        status, dados = self.respostas.get(alvo, (404, None))
        return {"status": status, "dados": dados, "url": self.atual}


def respostas_gupy():
    r = {f"{gupy.API}/applications": (200, LISTA)}
    for app, d in ETAPAS.items():
        r[f"{gupy.API}/application/{app}/step"] = (200, d)
    return r


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(contas, "PASTA", self.tmp / "contas"),
                  mock.patch.object(contas, "ESTADO", self.tmp / "contas" / "estado.json"),
                  mock.patch.object(gupy, "MAPA", self.tmp / "contas" / "gupy.json"),
                  mock.patch.object(sincronia, "ULTIMA", self.tmp / "contas" / "ultima.json")):
            p.start()
            self.addCleanup(p.stop)


class TestGupy(Base):
    def test_leitura_e_traducao(self):  # research §3
        aba = AbaFalsa(respostas_gupy())
        lidas = {x["id"]: x for x in gupy.ler(aba)}
        a = lidas["gupy-9000001"]
        self.assertEqual((a["etapa"], a["resultado"], a["ativa"]), ("aplicada", None, True))
        self.assertEqual(a["nota"], "Gupy: etapa 2 de 5 (Triagem)")
        self.assertEqual(a["url"], "https://empresaalfa.gupy.io/jobs/9000001")
        self.assertEqual(lidas["gupy-9000002"]["etapa"], "entrevista")  # categoria interview
        self.assertEqual(lidas["gupya-1000003"]["etapa"], "encerrada")
        self.assertEqual(lidas["gupya-1000003"]["resultado"], "nao_aprovado")
        self.assertEqual(lidas["gupya-1000004"]["resultado"], "cancelada")
        self.assertEqual((lidas["gupya-1000005"]["etapa"], lidas["gupya-1000005"]["resultado"]), ("encerrada", None))
        self.assertIn("sem resultado", lidas["gupya-1000005"]["nota"])
        talentos = lidas["gupya-1000006"]
        self.assertEqual((talentos["etapa"], talentos["ativa"]), ("aplicada", False))
        self.assertIn("banco de talentos", talentos["nota"])
        # detalhe só das em andamento, na página de cada empresa; o id da vaga fica guardado
        detalhes = [u for u in aba.visitas if "/candidates/applications/" in u]
        self.assertEqual(detalhes, ["https://empresaalfa.gupy.io/candidates/applications/1000001",
                                    "https://empresabeta.gupy.io/candidates/applications/1000002"])
        self.assertEqual(json.loads(gupy.MAPA.read_text()), {"1000001": 9000001, "1000002": 9000002})

    def test_so_leitura_e_so_candidaturas(self):  # constituição VI
        aba = AbaFalsa(respostas_gupy())
        gupy.ler(aba)
        for js in aba.js:
            self.assertNotRegex(js, r"click\(|submit\(|method:\s*\"(POST|PUT|DELETE)")
            self.assertIn("/selection-process/candidate/", json.loads(re.search(r"fetch\((\".*?\")", js).group(1)))

    def test_login(self):
        with self.assertRaises(contas.PortalErro) as e:
            gupy.ler(AbaFalsa({}, login="https://login.gupy.io/candidates/signin"))
        self.assertTrue(e.exception.login)
        with self.assertRaises(contas.PortalErro) as e:
            gupy.ler(AbaFalsa({f"{gupy.API}/applications": (401, None)}))
        self.assertTrue(e.exception.login)

    def test_logado(self):  # o login pelo LinkedIn passa pelo linkedin.com antes de voltar
        self.assertTrue(gupy.logado("https://portal.gupy.io/my/applications"))
        self.assertTrue(gupy.logado("https://empresaalfa.gupy.io/candidates/applications/1"))
        self.assertFalse(gupy.logado("https://login.gupy.io/candidates/signin"))
        self.assertFalse(gupy.logado("https://www.linkedin.com/oauth/v2/authorization"))
        self.assertTrue(indeed.logado("https://myjobs.indeed.com/applied"))
        self.assertFalse(indeed.logado("https://secure.indeed.com/auth"))
        self.assertFalse(linkedin.logado("https://www.linkedin.com/checkpoint/challenge"))

    def test_resposta_estranha(self):
        with self.assertRaises(contas.PortalErro) as e:
            gupy.ler(AbaFalsa({f"{gupy.API}/applications": (200, {"outra": 1})}))
        self.assertFalse(e.exception.login)

    def test_subdominio_invalido_nao_vira_link(self):
        x = gupy.traduzir({**LISTA["results"][2], "careerPageSubdomain": "evil.com/x"})
        self.assertEqual(x["url"], "")


class TestIndeed(Base):
    def lidas(self, entrevistas=None):
        return {x["id"]: x for x in (indeed.traduzir(i, entrevistas, HOJE) for i in APLICADAS["body"]["appStatusJobs"])}

    def test_traducao(self):  # research §4
        lidas = self.lidas()
        a = lidas["aaaaaaaaaaaaaaa1"]
        self.assertEqual((a["etapa"], a["ativa"], a["avisos"]), ("aplicada", True, []))
        self.assertEqual(a["data"], dia(1791100800000))  # applyTime em ms
        b = lidas["aaaaaaaaaaaaaaa2"]  # a empresa recusou depois do "aplicada" da pessoa: vale o mais recente
        self.assertEqual((b["etapa"], b["resultado"]), ("encerrada", "nao_aprovado"))
        self.assertEqual(b["avisos"], ["vaga fechada ou expirada no Indeed"])
        c = lidas["aaaaaaaaaaaaaaa3"]
        self.assertEqual((c["etapa"], c["resultado"]), ("encerrada", "desisti"))
        d = lidas["aaaaaaaaaaaaaaa4"]  # vaga fechada não muda a etapa
        self.assertEqual((d["etapa"], d["ativa"]), ("aplicada", False))
        self.assertEqual(d["avisos"], ["vaga fechada ou expirada no Indeed"])

    def test_entrevista_e_desistencia(self):
        self.assertEqual(self.lidas({"aaaaaaaaaaaaaaa1"})["aaaaaaaaaaaaaaa1"]["etapa"], "entrevista")
        item = {**APLICADAS["body"]["appStatusJobs"][0], "withdrawn": True}
        self.assertEqual(indeed.traduzir(item)["resultado"], "desisti")
        for status, esperado in (("HIRED", ("encerrada", "contratado")), ("OFFER_RECEIVED", ("proposta", None)),
                                 ("INTERVIEWING", ("entrevista", None)), ("ALGO_NOVO", (None, None))):
            self.assertEqual(indeed._etapa(status), esperado)

    def test_ler_e_login(self):
        aba = AbaFalsa({f"/api/v1/appStatusJobs?type=POST_APPLY&co={indeed.PAIS}": (200, APLICADAS),
                        "/api/v1/interviews": (200, {"body": {"interviews": [{"jobKey": "aaaaaaaaaaaaaaa1"}]}})})
        lidas = {x["id"]: x for x in indeed.ler(aba)}
        self.assertEqual(lidas["aaaaaaaaaaaaaaa1"]["etapa"], "entrevista")
        with self.assertRaises(contas.PortalErro) as e:
            indeed.ler(AbaFalsa({}, login="https://secure.indeed.com/auth?continue=x"))
        self.assertTrue(e.exception.login)


class TestLinkedIn(unittest.TestCase):
    def test_desativado(self):  # US4
        self.assertFalse(linkedin.ATIVO)
        self.assertNotIn("linkedin", contas.CONTAS)
        self.assertIn("linkedin", contas.TODAS)

    def test_linha_do_rastreador(self):
        x = linkedin.traduzir("https://www.linkedin.com/jobs/view/123456/?x=1",
                              "Analista de Projetos\nEmpresa Alfa · Brasil (Remoto)\n"
                              "Candidatou-se há 1 sem (Não aceita mais candidaturas)\nRecebeu resposta?\nSim\nNão", hoje=HOJE)
        self.assertEqual((x["id"], x["empresa"], x["local"]), ("li-123456", "Empresa Alfa", "Brasil (Remoto)"))
        self.assertEqual((x["etapa"], x["data"], x["ativa"]), ("aplicada", "2026-10-11", False))
        self.assertIn("aproximada", x["nota"])
        self.assertEqual(x["avisos"], ["não aceita mais candidaturas"])
        self.assertEqual(linkedin.data_aproximada("Candidatou-se há 2 m", HOJE)[0], "2026-08-19")
        self.assertIsNone(linkedin.traduzir("https://www.linkedin.com/feed/", "x"))


class TestProposta(Base):
    def vaga(self, vid, plataforma, titulo, empresa, etapa=None, resultado=None, url=""):
        v, _ = banco.criar_de_link({"id": vid, "plataforma": plataforma, "titulo": titulo, "empresa": empresa, "url": url})
        if etapa:
            banco.atualizar_usuario(vid, {"etapa": etapa, "etapa_em": "2026-09-01", "triagem": "seguir",
                                          "resultado": resultado})
        return v

    def montar(self, criar=True):
        if criar:
            self.criar()
        lidas = gupy.ler(AbaFalsa(respostas_gupy())) + [indeed.traduzir(i, None, HOJE) for i in APLICADAS["body"]["appStatusJobs"]]
        return sincronia.proposta(lidas, banco.listar_vagas())

    def criar(self):
        self.vaga("aaaaaaaaaaaaaaa2", "Indeed", "Coordenador Ágil", "Empresa Beta", "aplicada")
        self.vaga("aaaaaaaaaaaaaaa1", "Indeed", "Analista de Projetos", "Empresa Alfa", "entrevista")
        self.vaga("gupy-9000001", "Gupy", "Analista de Projetos", "Empresa Alfa Gupy")
        self.vaga("m-1", "Gupy", "Analista de Dados", "Empresa Gama", "encerrada", "nao_aprovado")

    def test_proposta(self):  # US2
        r = self.montar()
        itens = {i["chave"]: i for i in r["itens"]}
        mudar = itens["indeed:aaaaaaaaaaaaaaa2"]
        self.assertEqual((mudar["tipo"], mudar["marcado"]), ("mudar", True))
        self.assertEqual((mudar["de"]["etapa"], mudar["para"]), ("aplicada", {"etapa": "encerrada", "resultado": "nao_aprovado"}))
        quadro = itens["gupy:gupy-9000001"]
        self.assertEqual((quadro["tipo"], quadro["para"]["etapa"], quadro["marcado"]), ("quadro", "aplicada", True))
        self.assertNotIn("indeed:aaaaaaaaaaaaaaa1", itens)  # entrevista no quadro, aplicada no portal: não rebaixa
        self.assertNotIn("gupy:gupya-1000003", itens)  # encerrada no quadro (casou por cargo + empresa): fica
        self.assertEqual((itens["gupy:gupy-9000002"]["tipo"], itens["gupy:gupy-9000002"]["marcado"]), ("nova", True))
        self.assertEqual((itens["gupy:gupya-1000005"]["tipo"], itens["gupy:gupya-1000005"]["marcado"]), ("nova", False))
        self.assertFalse(itens["indeed:aaaaaaaaaaaaaaa3"]["marcado"])  # nova já encerrada: desmarcada
        self.assertGreaterEqual(r["sem_mudanca"], 2)

    def test_aplicar_so_o_marcado(self):  # SC-003
        r = self.montar()
        itens = {i["chave"]: i for i in r["itens"]}
        escolhidos = [itens["indeed:aaaaaaaaaaaaaaa2"], itens["gupy:gupy-9000001"], itens["gupy:gupy-9000002"]]
        with mock.patch.object(sincronia, "_descricao", return_value={}):
            res = sincronia.aplicar(escolhidos)
        self.assertEqual(res, {"aplicados": 3, "erros": []})
        b = banco.obter("aaaaaaaaaaaaaaa2")
        self.assertEqual((b["etapa"], b["resultado"], b["etapa_em"]), ("encerrada", "nao_aprovado", dia(1790000000000)))
        self.assertIn("Etapa atualizada pela Indeed", b["anotacao"])
        self.assertIn("vaga fechada ou expirada no Indeed", b["anotacao"])
        g = banco.obter("gupy-9000001")
        self.assertEqual((g["etapa"], g["triagem"]), ("aplicada", "seguir"))
        self.assertIn("Gupy: etapa 2 de 5 (Triagem)", g["anotacao"])
        n = banco.obter("gupy-9000002")
        self.assertEqual((n["etapa"], n["triagem"], n["url"]), ("entrevista", "seguir", "https://empresabeta.gupy.io/jobs/9000002"))
        self.assertIsNone(banco.obter("gupya-1000005"))  # não marcada: não entrou
        self.assertEqual(banco.obter("aaaaaaaaaaaaaaa1")["etapa"], "entrevista")
        # nova leitura: o que foi aplicado vira "sem mudança"
        de_novo = {i["chave"] for i in self.montar(criar=False)["itens"] if i["tipo"] != "info"}
        self.assertFalse({"indeed:aaaaaaaaaaaaaaa2", "gupy:gupy-9000001", "gupy:gupy-9000002"} & de_novo)

    def test_mesma_vaga_em_dois_portais(self):
        self.vaga("aaaaaaaaaaaaaaa9", "Indeed", "Analista X", "Empresa X", "aplicada")
        a = contas.lida("indeed", "Indeed", id="aaaaaaaaaaaaaaa9", titulo="Analista X", empresa="Empresa X", etapa="entrevista")
        b = contas.lida("gupy", "Gupy", id="gupya-1", titulo="Analista X", empresa="Empresa X", etapa="proposta")
        itens = sincronia.proposta([a, b], banco.listar_vagas())["itens"]
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["para"]["etapa"], "proposta")


class TestLeitura(Base):
    def test_um_portal_com_erro_nao_para_o_outro(self):  # SC-006
        aba = AbaFalsa(respostas_gupy())
        with mock.patch.object(sincronia.navegador, "abrir", return_value=aba), \
                mock.patch.object(sincronia.navegador, "fechar") as fechar, \
                mock.patch.object(indeed, "ler", side_effect=contas.PortalErro("não consegui ler")):
            leitura = sincronia.Leitura()
            leitura._rodar(["gupy", "indeed"])
        self.assertEqual(leitura.estado["situacao"], "pronta")
        self.assertEqual(leitura.resultado["erros"], {"Indeed": "não consegui ler"})
        self.assertTrue(any(i["portal"] == "gupy" for i in leitura.resultado["itens"]))
        fechar.assert_not_called()  # a janela fica aberta (a Gupy esquece o login quando ela fecha)
        self.assertTrue(aba.minimizada and aba.conexao_fechada)
        self.assertTrue(sincronia.ULTIMA.exists())

    def test_espera_o_login_e_segue(self):
        aba = AbaFalsa(respostas_gupy(), login="https://login.gupy.io/candidates/signin")
        caminho = iter(["https://www.linkedin.com/oauth/v2/authorization?x=1", None])

        def logou(_):  # "Entrar com LinkedIn": passa pelo LinkedIn antes de voltar à Gupy
            aba.login = next(caminho, None)
        with mock.patch.object(sincronia.navegador, "abrir", return_value=aba), \
                mock.patch.object(sincronia.navegador, "fechar"), \
                mock.patch.object(sincronia.time, "sleep", side_effect=logou), \
                mock.patch.object(aba, "frente") as frente:
            leitura = sincronia.Leitura()
            leitura._rodar(["gupy"])
        frente.assert_called_once()
        self.assertEqual(leitura.resultado["erros"], {})
        self.assertTrue(leitura.resultado["itens"])

    def test_erro_inesperado_nao_prende_a_leitura(self):
        with mock.patch.object(sincronia.navegador, "abrir", side_effect=RuntimeError("x")):
            leitura = sincronia.Leitura()
            leitura._rodar(["gupy"])
        self.assertEqual(leitura.estado["situacao"], "pronta")
        self.assertIn("inesperado", leitura.resultado["erros"]["Gupy"])

    def test_janela_fechada_durante_o_login(self):
        aba = AbaFalsa(respostas_gupy(), login="https://login.gupy.io/candidates/signin")
        with mock.patch.object(sincronia.navegador, "abrir", return_value=aba),                 mock.patch.object(sincronia.time, "sleep"),                 mock.patch.object(aba, "url", side_effect=["https://login.gupy.io/x"] + [sincronia.navegador.NavegadorErro("fechada")] * 3):
            leitura = sincronia.Leitura()
            leitura._rodar(["gupy"])
        self.assertEqual(leitura.estado["situacao"], "pronta")
        self.assertIn("login", leitura.resultado["erros"]["Gupy"])

    def test_aplicar_usa_a_proposta_do_servidor(self):
        leitura = sincronia.Leitura()
        with self.assertRaisesRegex(ValueError, "não há proposta"):
            leitura.aplicar(["x"])

    def test_conectados(self):
        self.assertEqual(contas.conectados(), [])
        contas.marcar("gupy", True)
        contas.marcar("linkedin", True)  # desativado: não conta
        self.assertEqual(contas.conectados(), ["gupy"])
        contas.marcar("gupy", False)
        self.assertEqual(contas.conectados(), [])


if __name__ == "__main__":
    unittest.main()
