import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from contas import PortalErro, nerdin

LISTA = "https://www.nerdin.com.br/vagas_candidato.php"
PAGINA = LISTA + "?id=777"
JS_HTML = "document.documentElement.outerHTML"


def passo(rotulo, feito=True):
    return (f'<li class="passo{" success" if feito else ""}"><i class="fa fa-{"check" if feito else "circle"}"></i>'
            f'<span>{rotulo}</span></li>')


def cartao(titulo, empresa, local, selo, trilha, link="", inscrito="05/03/2026"):
    ancora = f'<a href="{link}">Ver Detalhes</a>' if link else "<a>Ver Detalhes</a>"
    titulo_html = f"<h3>{titulo}</h3>" if titulo else ""
    return (f'<div class="card"><div class="topo">{titulo_html}<span class="selo">{selo}</span></div>'
            f'<p><i class="fa fa-building"></i> {empresa}</p><p><i class="fa fa-map-marker"></i> {local}</p>'
            f'<span class="etiqueta">Remoto</span><small>Inscrito em: {inscrito}</small>'
            f'<h5>Acompanhe sua candidatura</h5><ul>{trilha}</ul>{ancora}<button>Cancelar candidatura</button></div>')


BASE = passo("Inscrito") + passo("Currículo recebido") + passo("Perfil visualizado")
ANDAMENTO = BASE + passo("Em análise") + passo("Processo aberto", False)
RECUSADA = BASE + passo("Não selecionado") + passo("Processo encerrado")
ENCERRADO = BASE + passo("Processo encerrado")
DESCONHECIDO = BASE + passo("Teste técnico", False)

HTML = ("<html><head><script>var x = 'Acompanhe sua candidatura Inscrito em: 01/01/2020';</script></head><body>"
        + cartao("Scrum Master", "Alfa Sistemas", "São Paulo, SP", "Aberta", ANDAMENTO,
                 "/vaga_emprego/vaga-scrum-master-12345.php")
        + cartao("Analista de Dados", "Beta Dados", "Recife, PE", "Expirada", RECUSADA, "vaga.php?id=678")
        + cartao("Dev Backend", "Gama Soluções", "Remoto", "Expirada", ANDAMENTO)
        + cartao("QA", "Delta Tech", "Curitiba, PR", "Aberta", ENCERRADO)
        + cartao("Dev Mobile", "Épsilon Apps", "Belo Horizonte, MG", "Aberta", DESCONHECIDO)
        + cartao("", "Zeta Labs", "Salvador, BA", "Aberta", ANDAMENTO)
        + "</body></html>")


class AbaFalsa:
    def __init__(self, paginas, login=None):
        self.paginas, self.login, self.atual, self.visitas, self.js = paginas, login, "", [], []

    def ir(self, url):
        self.atual = url
        self.visitas.append(url)

    def url(self):
        return self.login or self.atual

    def avaliar(self, js):
        self.js.append(js)
        return self.paginas.get(self.atual, "")


class CartoesTest(unittest.TestCase):
    def setUp(self):
        self.lidos = nerdin.cartoes(HTML)

    def test_ignora_script_e_cartao_sem_titulo(self):
        self.assertEqual([c["titulo"] for c in self.lidos],
                         ["Scrum Master", "Analista de Dados", "Dev Backend", "QA", "Dev Mobile"])

    def test_campos_do_cartao(self):
        c = self.lidos[0]
        self.assertEqual((c["empresa"], c["local"], c["selo"], c["inscrito"]),
                         ("Alfa Sistemas", "São Paulo, SP", "Aberta", "2026-03-05"))
        self.assertEqual([p["rotulo"] for p in c["passos"]][-2:], ["Em análise", "Processo aberto"])
        self.assertTrue(c["passos"][3]["feito"])
        self.assertFalse(c["passos"][4]["feito"])

    def test_ids_e_links(self):
        self.assertEqual(self.lidos[0]["id"], "nerdin-12345")
        self.assertEqual(self.lidos[1]["id"], "nerdin-678")
        self.assertEqual(self.lidos[1]["url"], "https://www.nerdin.com.br/vaga.php?id=678")
        self.assertEqual(self.lidos[2]["id"], "")

    def test_sem_icones_usa_as_duas_linhas_depois_do_titulo(self):
        html = ('<div><h3>Dev</h3><span>Aberta</span><div>Eta Ltda</div><div>Natal, RN</div>'
                '<p>Inscrito em: 02/02/2026</p><h5>Acompanhe sua candidatura</h5><b>Inscrito</b></div>')
        c = nerdin.cartoes(html)[0]
        self.assertEqual((c["empresa"], c["local"]), ("Eta Ltda", "Natal, RN"))


class TraduzirTest(unittest.TestCase):
    def setUp(self):
        self.t = [nerdin.traduzir(c, date(2026, 6, 1)) for c in nerdin.cartoes(HTML)]

    def test_em_andamento_e_aberta(self):
        t = self.t[0]
        self.assertEqual((t["etapa"], t["ativa"], t["data"], t["avisos"], t["status"]),
                         ("aplicada", True, "2026-03-05", [], "Em análise"))
        self.assertEqual((t["portal"], t["plataforma"]), ("nerdin", "Nerdin"))

    def test_nao_selecionado_mesmo_expirada(self):
        t = self.t[1]
        self.assertEqual((t["etapa"], t["resultado"], t["ativa"], t["avisos"]), ("encerrada", "nao_aprovado", False, []))

    def test_em_andamento_e_expirada(self):
        t = self.t[2]
        self.assertEqual((t["etapa"], t["ativa"], t["avisos"]), ("aplicada", False, ["vaga expirada na Nerdin"]))

    def test_processo_encerrado_sozinho(self):
        t = self.t[3]
        self.assertEqual((t["etapa"], t["ativa"], t["avisos"]), (None, False, ["processo encerrado na Nerdin"]))

    def test_passo_desconhecido(self):
        t = self.t[4]
        self.assertIsNone(t["etapa"])
        self.assertTrue(t["avisos"][0].startswith("status na Nerdin:"))

    def test_sem_data_usa_hoje(self):
        t = nerdin.traduzir({"titulo": "X", "passos": []}, date(2026, 6, 1))
        self.assertEqual(t["data"], "2026-06-01")


class EnderecoTest(unittest.TestCase):
    def test_endereco_valido(self):
        self.assertTrue(nerdin.endereco_valido(PAGINA))
        self.assertTrue(nerdin.endereco_valido("https://nerdin.com.br/vagas_candidato.php?id=1"))
        self.assertFalse(nerdin.endereco_valido("https://outro.com/vagas_candidato.php?id=1"))
        self.assertFalse(nerdin.endereco_valido(LISTA))
        self.assertFalse(nerdin.endereco_valido("http://www.nerdin.com.br/vagas_candidato.php?id=1"))

    def test_logado(self):
        self.assertTrue(nerdin.logado(PAGINA))
        self.assertFalse(nerdin.logado("https://www.nerdin.com.br/login.php"))
        self.assertFalse(nerdin.logado("https://outro.com/x"))

    def test_link_do_menu(self):
        self.assertEqual(nerdin.link_do_menu('<a href="/vagas_candidato.php?id=777">Candidato</a>'), PAGINA)
        self.assertIsNone(nerdin.link_do_menu('<a href="/vagas.php">Vagas</a>'))


class LerTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.guardado = Path(tmp.name) / "contas" / "nerdin.json"
        self.env = {"valor": ""}
        for p in (mock.patch.object(nerdin, "GUARDADO", self.guardado),
                  mock.patch.object(nerdin.segredos, "ler", side_effect=lambda n: self.env["valor"]),
                  mock.patch.object(nerdin.time, "sleep")):
            p.start()
            self.addCleanup(p.stop)

    def test_login(self):
        aba = AbaFalsa({}, login="https://www.nerdin.com.br/login.php")
        with self.assertRaises(PortalErro) as e:
            nerdin.ler(aba)
        self.assertTrue(e.exception.login)

    def test_le_direto_e_so_pede_o_html(self):
        self.env["valor"] = PAGINA
        aba = AbaFalsa({PAGINA: HTML})
        lidas = nerdin.ler(aba)
        self.assertEqual(len(lidas), 5)
        self.assertEqual(aba.visitas, [PAGINA])
        self.assertEqual(set(aba.js), {JS_HTML})

    def test_descobre_link_do_menu_e_guarda(self):
        menu = '<html><body><a href="/vagas_candidato.php?id=777">Candidato</a></body></html>'
        aba = AbaFalsa({URL_BASE: menu, PAGINA: HTML})
        lidas = nerdin.ler(aba)
        self.assertEqual(aba.visitas, [URL_BASE, PAGINA])
        self.assertEqual(len(lidas), 5)
        self.assertEqual(json.loads(self.guardado.read_text(encoding="utf-8")), {"url": PAGINA})

    def test_usa_o_endereco_guardado(self):
        self.guardado.parent.mkdir(parents=True)
        self.guardado.write_text(json.dumps({"url": PAGINA}), encoding="utf-8")
        aba = AbaFalsa({PAGINA: HTML})
        nerdin.ler(aba)
        self.assertEqual(aba.visitas, [PAGINA])

    def test_endereco_do_env_de_outro_dominio_e_ignorado(self):
        self.env["valor"] = "https://outro.com/vagas_candidato.php?id=1"
        aba = AbaFalsa({URL_BASE: HTML})
        nerdin.ler(aba)
        self.assertEqual(aba.visitas, [URL_BASE])

    def test_pagina_logada_sem_cartoes_e_erro(self):
        aba = AbaFalsa({URL_BASE: "<html><body><p>Olá</p></body></html>"})
        with self.assertRaises(PortalErro) as e:
            nerdin.ler(aba)
        self.assertFalse(e.exception.login)
        self.assertIn("NERDIN_CANDIDATURAS", str(e.exception))

    def test_lista_vazia_devolve_nada(self):
        aba = AbaFalsa({URL_BASE: "<body><p>Você ainda não se inscreveu em nenhuma vaga.</p></body>"})
        self.assertEqual(nerdin.ler(aba), [])

    def test_bloqueio(self):
        aba = AbaFalsa({URL_BASE: "<body><p>Acesso negado</p></body>"})
        with self.assertRaises(PortalErro) as e:
            nerdin.ler(aba)
        self.assertIn("bloqueou", str(e.exception))

    def test_paginas_seguintes(self):
        self.env["valor"] = PAGINA
        p1 = HTML + f'<a href="{PAGINA}&pagina=2">2</a>'
        p2 = cartao("Dev Extra", "Iota Ltda", "Remoto", "Aberta", ANDAMENTO)
        aba = AbaFalsa({PAGINA: p1, PAGINA + "&pagina=2": p2})
        lidas = nerdin.ler(aba)
        self.assertEqual(aba.visitas, [PAGINA, PAGINA + "&pagina=2"])
        self.assertEqual(len(lidas), 6)

    def test_nunca_abre_link_que_age(self):  # FR-004: o link de cancelar pode agir só por ser aberto
        self.env["valor"] = PAGINA
        p1 = HTML + (f'<a href="{PAGINA}&cancelar=99">Cancelar candidatura</a>'
                     f'<a href="{PAGINA}&pagina=2&acao=sair">2</a><a href="{PAGINA}&pagina=x">x</a>')
        aba = AbaFalsa({PAGINA: p1})
        nerdin.ler(aba)
        self.assertEqual(aba.visitas, [PAGINA])


URL_BASE = nerdin.URL_CANDIDATURAS

if __name__ == "__main__":
    unittest.main()
