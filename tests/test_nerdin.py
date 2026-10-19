"""Nerdin na busca (fontes/nerdin.py), com HTML fictício e sem rede (spec 020): leitura dos cards, filtro por cargo,
janela e grupo, uma leitura por cargo, bloqueio sem nova tentativa (SC-005), descrição pela página da vaga, link no
Adicionar Vaga e o portal ligado por padrão (SC-001)."""
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
from fontes import FONTES, _comum, link, nerdin  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "nerdin"
LISTA = (DADOS / "lista.html").read_text(encoding="utf-8")
LISTA_2 = (DADOS / "lista-2.html").read_text(encoding="utf-8")
VAGA = (DADOS / "vaga.html").read_text(encoding="utf-8")
HOJE = datetime(2026, 10, 19, 12, tzinfo=timezone.utc)
CFG = {"termos": ["analista de dados"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                      "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "tipos_emprego": [],
       "fontes": ["nerdin"], "janela_horas": 168, "internacional": {"ativo": False}}


def grupos(cfg):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def numeros(lista):
    return [int(v["id"].removeprefix("nerdin-")) for v in lista]


def paginas(url):
    """A página de resultados que o site devolveria para a url."""
    return LISTA_2 if "pagina=2" in url else LISTA


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        nerdin._estado["ultimo"] = None
        for p in (mock.patch.object(nerdin, "PAUSA", 0), mock.patch.object(nerdin.time, "sleep"),
                  mock.patch.object(nerdin, "_agora", return_value=HOJE)):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def respostas(self, fn=paginas):
        """Substitui o pedido de rede: fn(url) devolve o HTML."""
        self.urls = []

        def baixar(url):
            self.urls.append(url)
            return fn(url)
        p = mock.patch.object(nerdin, "_baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)


class TestLeitura(SemRede):
    def test_cards(self):
        vs = {v["id"]: v for v in nerdin.ler_lista(LISTA)}
        self.assertEqual(len(vs), 20)
        a = vs["nerdin-90020"]
        self.assertEqual((a["titulo"], a["empresa"], a["local"], a["publicada_em"]),
                         ("Analista de Dados Pleno", "Empresa Alfa", "São Paulo, SP", "2026-10-18"))
        self.assertEqual((a["modelo_trabalho"], a["remoto"], a["tipo_emprego"], a["salario"]),
                         ("hibrido", False, ["tempo_integral"], None))  # "Salário a combinar" fica vazio
        self.assertEqual(a["url"], "https://www.nerdin.com.br/vaga_emprego/vaga-analista-de-dados-pleno-90020.php")
        self.assertEqual((a["plataforma"], a["descricao"], a["tipo"]), ("Nerdin", "", "CLT • Pleno • Híbrido"))
        b = vs["nerdin-90019"]  # selo "Nova" e ícone de urgente fora do título
        self.assertEqual((b["titulo"], b["local"], b["remoto"], b["modelo_trabalho"], b["tipo_emprego"]),
                         ("Analista de Dados Senior - Remoto", "Remoto", True, "remoto", ["pj"]))
        self.assertEqual(b["salario"], "R$ 12.000,00 a R$ 15.000,00")
        self.assertIsNone(vs["nerdin-90017"]["salario"])
        sem = vs["nerdin-90013"]  # card sem empresa, sem local e sem modelo
        self.assertEqual((sem["empresa"], sem["local"], sem["remoto"]), ("Empresa não informada", "", False))
        self.assertNotIn("modelo_trabalho", sem)
        self.assertNotIn("tipo_emprego", sem)
        self.assertEqual(vs["nerdin-90015"]["tipo_emprego"], ["pj"])  # Freelancer
        self.assertEqual(vs["nerdin-90010"]["tipo_emprego"], ["estagio"])
        self.assertEqual(vs["nerdin-90011"]["titulo"], "Analista de Dados Sênior")
        self.assertEqual(vs["nerdin-90016"]["modelo_trabalho"], "presencial")

    def test_pagina_sem_cards(self):
        self.assertEqual(nerdin.ler_lista("<html><body>Nenhuma vaga encontrada</body></html>"), [])


class TestBusca(SemRede):
    def test_remoto_e_cidade_com_uma_leitura(self):
        self.respostas()
        c = grupos(CFG)
        remoto, erros = nerdin.buscar(c["remoto"], 168, 20)
        self.assertEqual(erros, [])
        self.assertEqual(numeros(remoto), [90019, 90015, 90008, 90005, 90002])  # 89999 é de antes da janela
        local, _ = nerdin.buscar(c["local"], 168, 20)
        self.assertEqual(numeros(local), [90020, 90016, 90010, 90007, 90001])  # SP; 90001 da página 2 uma vez só
        self.assertEqual(len(self.urls), 2)  # as duas consultas usam a mesma lista
        self.assertEqual(self.urls[0], "https://www.nerdin.com.br/vagas.php?busca=analista+de+dados")
        self.assertTrue(self.urls[1].endswith("&pagina=2"))

    def test_janela_para_a_paginacao(self):
        self.respostas()
        remoto, _ = nerdin.buscar(grupos(CFG)["remoto"], 72, 20)
        self.assertEqual(numeros(remoto), [90019, 90015])  # 3 dias: de 16/10 em diante
        self.assertEqual(len(self.urls), 1)  # a página 1 já chega a vagas mais antigas que a janela

    def test_janela_de_15_dias(self):  # FR-016: a janela do painel, com a opção de 15 dias
        self.respostas()
        remoto, _ = nerdin.buscar(grupos({**CFG, "janela_horas": 360})["remoto"], 360, 20)
        self.assertEqual(numeros(remoto), [90019, 90015, 90008, 90005, 90002, 89999])  # 89997 (30/09) fica fora
        self.assertEqual(filtros.opcoes()["janelas"][360], "Últimos 15 dias")
        base = {"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}}
        self.assertEqual(filtros.validar({**base, "janela_horas": 360})["janela_horas"], 360)
        with self.assertRaises(ValueError):
            filtros.validar({**base, "janela_horas": 721})  # máximo de 30 dias

    def test_estado_por_nome_e_modelos(self):
        self.respostas()
        cfg = {**CFG, "localidade": {"pais": "Brasil", "estado": "São Paulo", "cidade": "Osasco", "raio_km": 25},
               "modelos": {"remoto": False, "hibrido": True, "presencial": False}}
        local, _ = nerdin.buscar(grupos(cfg)["local"], 168, 20)
        self.assertEqual(numeros(local), [90020, 90010, 90007, 90001])  # sem a presencial de Campinas
        cfg = {**CFG, "localidade": {"pais": "Brasil", "estado": "", "cidade": "Belo Horizonte", "raio_km": 25}}
        _comum.esquecer()
        local, _ = nerdin.buscar(grupos(cfg)["local"], 168, 20)
        self.assertEqual(numeros(local), [90014])

    def test_pais_inteiro_nos_modelos_marcados(self):
        self.respostas()
        cfg = {**CFG, "localidade": {"pais": "Brasil"}, "modelos": {"remoto": False, "hibrido": False,
                                                                     "presencial": True}}
        pais, _ = nerdin.buscar(grupos(cfg)["pais"], 168, 20)
        self.assertEqual(numeros(pais), [90016, 90014, 90013, 90004])  # 90013 não diz o modelo

    def test_cargo_entre_aspas_e_limite(self):
        self.respostas()
        consulta = {**grupos(CFG)["remoto"], "termo": '"analista de dados"'}
        achadas, _ = nerdin.buscar(consulta, 168, 2)
        self.assertEqual(numeros(achadas), [90019, 90015])
        self.assertEqual(self.urls[0], "https://www.nerdin.com.br/vagas.php?busca=analista+de+dados")

    def test_fora_do_brasil_sem_pedido(self):
        self.respostas()
        consulta = {**grupos(CFG)["remoto"], "pais": "portugal"}
        self.assertEqual(nerdin.buscar(consulta, 168, 20), ([], []))
        self.assertEqual(self.urls, [])
        self.assertFalse(vagas.atende(nerdin, {"area": "internacional", "pais": "portugal"}))

    def test_pagina_ilegivel_avisa_uma_vez(self):
        self.respostas(lambda url: '<div class="vaga-card" data-href="outra-coisa.php"><h3>?</h3></div>')
        c = grupos(CFG)
        self.assertEqual(nerdin.buscar(c["remoto"], 168, 20), ([], [nerdin.ILEGIVEL]))
        self.assertEqual(nerdin.buscar(c["local"], 168, 20), ([], []))

    def test_sem_vagas(self):
        self.respostas(lambda url: "<html><body>Nenhuma vaga</body></html>")
        self.assertEqual(nerdin.buscar(grupos(CFG)["remoto"], 168, 20), ([], []))


class TestDescricaoELink(SemRede):
    def test_descrever_pela_pagina_da_vaga(self):
        self.respostas(lambda url: VAGA)
        url = "https://www.nerdin.com.br/vaga_emprego/vaga-analista-de-dados-senior---remoto-90019.php"
        d = nerdin.descrever({"id": "nerdin-90019", "url": url, "descricao": ""})
        self.assertIn("SQL avançado", d)
        self.assertEqual(self.urls, [url])
        with self.assertRaises(_comum.FonteErro):
            nerdin.descrever({"id": "nerdin-1", "url": "https://exemplo.com/vaga-1.php"})

    def test_id_do_link(self):
        for url in ("https://www.nerdin.com.br/vaga_emprego/vaga-qa-senior-90019.php",
                    "https://nerdin.com.br/vaga_emprego/vaga-qa-senior-90019.php?utm_source=x",
                    "http://www.nerdin.com.br/vaga_emprego/vaga-qa-90019.php#topo"):
            self.assertEqual(nerdin.id_do_link(url), "nerdin-90019", url)
        for url in ("https://www.nerdin.com.br/vagas.php", "https://exemplo.com/vaga_emprego/vaga-qa-1.php",
                    "vaga_emprego/vaga-qa-1.php", ""):
            self.assertIsNone(nerdin.id_do_link(url), url)

    def test_adicionar_pelo_link(self):  # mesmo id da busca: a vaga não volta como nova
        url = "https://www.nerdin.com.br/vaga_emprego/vaga-analista-de-dados-senior---remoto-90019.php"
        self.assertEqual(link.plataforma("www.nerdin.com.br"), "Nerdin")
        with mock.patch.object(link, "_baixar", return_value=VAGA):
            v = link.ler(url)
        self.assertEqual((v["id"], v["plataforma"], v["empresa"], v["url"], v["remoto"]),
                         ("nerdin-90019", "Nerdin", "Empresa Beta", url, True))
        self.assertIn("SQL avançado", v["descricao"])
        self.assertIn("Nerdin", banco.PLATAFORMAS)


class Resposta:
    def __init__(self, corpo, final="https://www.nerdin.com.br/vagas.php"):
        self.corpo, self.final = corpo.encode(), final
        self.headers = mock.Mock(get_content_charset=lambda: "utf-8")

    def read(self, n):
        return self.corpo

    def geturl(self):
        return self.final

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestBloqueio(SemRede):
    def abridor(self, respostas):
        """urlopen falso: cada pedido devolve o próximo da lista (Resposta, texto ou código de erro HTTP)."""
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            return r if isinstance(r, Resposta) else Resposta(r)
        p = mock.patch.object(nerdin.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)

    def test_429_para_o_resto_da_busca(self):  # SC-005
        self.abridor([LISTA, 429])
        c = grupos(CFG)
        remoto, erros = nerdin.buscar(c["remoto"], 168, 20)
        self.assertEqual(numeros(remoto), [90019, 90015, 90008, 90005, 90002])  # a página 1 já lida vale
        self.assertEqual(erros, [nerdin.BLOQUEIO + " (código 429); a busca seguiu sem ela"])
        self.assertTrue(nerdin.parada())
        local, erros = nerdin.buscar(c["local"], 168, 20)  # mesma lista, sem pedido e sem repetir o aviso
        self.assertEqual((len(local), erros), (5, []))
        outro = {**c["remoto"], "termo": "cientista de dados"}
        self.assertEqual(nerdin.buscar(outro, 168, 20), ([], []))  # outro cargo: nenhum pedido a mais
        self.assertEqual(nerdin.descrever({"id": "nerdin-1", "descricao": "da lista"}), "da lista")
        self.assertEqual(len(self.pedidos), 2)
        for req in self.pedidos:  # sem cookies e com o nome da ferramenta
            self.assertIsNone(req.get_header("Cookie"))
            self.assertEqual(req.get_header("User-agent"), _comum.AGENTE)
        _comum.esquecer()  # a busca seguinte tenta de novo
        self.abridor([LISTA, LISTA_2])
        self.assertEqual(len(nerdin.buscar(c["remoto"], 168, 20)[0]), 5)

    def test_403_503_e_login_contam_como_bloqueio(self):
        for resposta, motivo in ((403, "código 403"), (503, "código 503"),
                                 (Resposta(LISTA, "https://www.nerdin.com.br/login.php?x=1"), "pediu login")):
            _comum.esquecer()
            self.abridor([resposta])
            self.assertEqual(nerdin.buscar(grupos(CFG)["remoto"], 168, 20),
                             ([], [f"{nerdin.BLOQUEIO} ({motivo}); a busca seguiu sem ela"]))
            self.assertTrue(nerdin.parada())

    def test_outro_erro_nao_para_a_fonte(self):
        self.abridor([500, LISTA, LISTA_2])
        c = grupos(CFG)
        self.assertEqual(nerdin.buscar(c["remoto"], 168, 20), ([], ["a Nerdin respondeu 500"]))
        self.assertFalse(nerdin.parada())
        outro = {**c["remoto"], "termo": "analista"}
        self.assertTrue(nerdin.buscar(outro, 168, 20)[0])

    def test_pausa_entre_pedidos(self):
        relogio = iter([100.0, 101.0, 103.0])  # o segundo pedido 1 s depois do primeiro: espera mais 2 s
        with mock.patch.object(nerdin, "PAUSA", 3.0), \
                mock.patch.object(nerdin.time, "monotonic", side_effect=lambda: next(relogio)):
            nerdin._pausar()
            nerdin._pausar()
        nerdin.time.sleep.assert_called_once()
        self.assertAlmostEqual(nerdin.time.sleep.call_args[0][0], 2.0)


class TestNaBusca(SemRede):
    def setUp(self):
        super().setUp()
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(vagas, "CACHE", self.tmp / ".cache"),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db")):
            p.start()
            self.addCleanup(p.stop)

    def test_descricoes_no_limite(self):
        self.respostas(lambda url: VAGA if "vaga_emprego" in url else paginas(url))
        cfg = {**CFG, "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True}}
        with mock.patch.object(nerdin, "MAX_DESCRICOES", 2):
            r = vagas.executar(cfg, filtros.efetivos(cfg), ["nerdin"], 20, pausa=0)
        achadas = r["candidatas"] + r["fora"]
        self.assertEqual(sorted(numeros(achadas)), [90002, 90005, 90008, 90015, 90019])
        self.assertEqual(len([u for u in self.urls if "vaga_emprego" in u]), 2)
        self.assertTrue(all(v["plataforma"] == "Nerdin" for v in achadas))

    def test_desligada_nenhum_pedido(self):
        self.respostas()
        cfg = {**CFG, "fontes": ["indeed"]}
        self.assertNotIn("nerdin", vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)))
        self.assertEqual(self.urls, [])


class TestPadrao(unittest.TestCase):
    def test_ligada_por_padrao(self):  # SC-001
        self.assertIn("nerdin", FONTES)
        self.assertEqual(filtros.efetivos({})["fontes"], ["indeed", "gupy", "nerdin"])
        cfg = {"termos": ["analista"]}
        self.assertEqual(vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)), ["indeed", "gupy", "nerdin"])
        cfg = {"termos": ["analista"], "fontes": ["indeed", "gupy"]}  # a lista escolhida pela pessoa não muda
        self.assertEqual(vagas.fontes_da_busca(cfg, filtros.efetivos(cfg)), ["indeed", "gupy"])
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertIn("tecnologia", nomes["nerdin"]["termos"])
        self.assertEqual(nomes["nerdin"]["precisa"], "")


if __name__ == "__main__":
    unittest.main()
