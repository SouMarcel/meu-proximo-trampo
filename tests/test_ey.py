"""EY na busca (fontes/ey.py), com HTML fictício e sem rede (spec 039): linhas da lista, microdados da página da vaga,
filtro por cargo, consultas remota, cidade e país com uma leitura, janela pela data da página, limite de páginas de
vaga, memória de datas, bloqueio sem espera, pausa, link no Adicionar Vaga e o portal ligado por padrão."""
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
from fontes import FONTES, _comum, ey, link  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "ey"
LISTA_1 = (DADOS / "lista-1.html").read_text(encoding="utf-8")
LISTA_2 = (DADOS / "lista-2.html").read_text(encoding="utf-8")
VAGA = (DADOS / "vaga.html").read_text(encoding="utf-8")
SEM_DATA = (DADOS / "vaga-sem-data.html").read_text(encoding="utf-8")
HOJE = datetime(2026, 10, 30, 15, tzinfo=timezone.utc)
DATAS = {"9000001": "Thu Oct 29", "9000003": "Tue Oct 27", "9000004": "Sun Oct 25", "9000005": "Sat Oct 10"}
CFG = {"termos": ["desenvolvedor"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                  "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "tipos_emprego": [],
       "fontes": ["ey"], "janela_horas": 168, "internacional": {"ativo": False}}
URL = "https://careers.ey.com/ey/job/Sao-Paulo-JK-Desenvolvedora-Java-Pleno-SP-04543-011/9000001/"


def grupos(cfg=CFG):
    return {c["grupo"]: c for c in filtros.consultas(filtros.efetivos(cfg))}


def pais(cfg=CFG):
    """A consulta do país inteiro (sem o filtro de remoto), como a busca monta sem cidade."""
    return {**grupos(cfg)["remoto"], "grupo": "pais", "remoto": False, "modelos": ["remoto", "hibrido", "presencial"]}


def numeros(lista):
    return [int(v["id"].removeprefix("ey-")) for v in lista]


LOCAIS = {"9000003": ("Curitiba", "PR"), "9000004": ("Fortaleza", "CE"), "9000005": ("Belo Horizonte", "MG")}
ENDERECO = re.compile(r'<span itemprop="address".*?</span>', re.S)


def vaga(n, datas=DATAS):
    """A página da vaga n: a data de DATAS e, fora a 9000001, um local só (o da lista)."""
    p = VAGA.replace("Thu Oct 29", datas[n])
    if n in LOCAIS:
        cidade, uf = LOCAIS[n]
        p = p.replace("".join(ENDERECO.findall(p)), (
            '<span itemprop="address" itemscope itemtype="http://schema.org/PostalAddress">'
            f'<meta itemprop="addressLocality" content="{cidade}"><meta itemprop="addressRegion" content="{uf}">'
            '<meta itemprop="addressCountry" content="BR"></span>'))
        p = p.replace('rtltextaligneligible">São Paulo JK', f'rtltextaligneligible">{cidade}')
    return p


class SemRede(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        ey._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(ey, "PAUSA", (0, 0)), mock.patch.object(ey.time, "sleep"),
                  mock.patch.object(ey, "_agora", return_value=HOJE),
                  mock.patch.object(ey, "POR_PAGINA", 4),
                  mock.patch.object(ey, "ARQ_DATAS", self.tmp / ".cache" / "ey-datas.json"),
                  mock.patch.object(segredos, "ler", return_value="")):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def respostas(self, paginas=None):
        """Troca ey._baixar: as listas pelo startrow e a página de cada vaga pelo número (paginas[n] pode ser um texto
        ou uma exceção)."""
        self.urls = []
        paginas = paginas or {}

        def baixar(url):
            self.urls.append(url)
            if "/search/" in url:
                return LISTA_2 if "startrow=4" in url else LISTA_1
            n = ey.numero(url)
            r = paginas.get(n, vaga(n) if n in DATAS else None)
            if isinstance(r, Exception):
                raise r
            return r
        p = mock.patch.object(ey, "_baixar", side_effect=baixar)
        p.start()
        self.addCleanup(p.stop)

    def paginas_de_vaga(self):
        return [u for u in self.urls if "/job/" in u]

    def abridor(self, respostas, final="https://careers.ey.com/ey/search/"):
        self.pedidos = []
        fila = list(respostas)

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            resp = mock.MagicMock()
            resp.__enter__.return_value = resp
            resp.read.return_value = r.encode()
            resp.headers.get_content_charset.return_value = "utf-8"
            resp.geturl.return_value = final
            return resp
        p = mock.patch.object(_comum.urllib.request, "urlopen", side_effect=abrir)
        p.start()
        self.addCleanup(p.stop)


class TestLeitura(SemRede):
    def test_linhas_da_lista(self):
        vs = ey.ler_lista(LISTA_1)
        self.assertEqual(numeros(vs), [9000001, 9000002, 9000003, 9000004])
        java, _, banco_talentos, python = vs
        self.assertEqual((java["titulo"], java["empresa"], java["local"], java["remoto"], java["tipo"]),
                         ("Desenvolvedor(a) Java Pleno", "EY", "São Paulo JK, SP", False, None))  # sem o "+2 more"
        self.assertEqual(java["url"], URL)
        self.assertIsNone(java["publicada_em"])
        self.assertEqual(banco_talentos["tipo"], "Banco de talentos • Exclusiva para PCD")
        self.assertEqual((python["remoto"], python["modelo_trabalho"]), (True, "remoto"))
        self.assertNotIn("modelo_trabalho", java)

    def test_microdados(self):
        v = ey.ler_pagina(VAGA)
        self.assertEqual((v["titulo"], v["empresa"], v["publicada_em"], v["local"]),
                         ("Desenvolvedor(a) Java Pleno", "EY", "2026-10-29", "São Paulo JK, SP"))
        self.assertEqual(v["locais"], [["São Paulo JK", "SP"], ["Goiania", "GO"], ["Recife", "PE"]])
        self.assertIn("projetos de Java e nuvem", v["descricao"])
        self.assertIn("- Spring Boot", v["descricao"])
        self.assertNotIn("Rodapé", v["descricao"])
        self.assertIsNone(ey.ler_pagina(SEM_DATA)["publicada_em"])
        with self.assertRaises(link.LinkErro):
            ey.ler_pagina("<html><body>sem vaga</body></html>")

    def test_local_principal_primeiro(self):
        pagina = VAGA.replace('data-careersite-propertyid="city" class="rtltextaligneligible">São Paulo JK',
                              'data-careersite-propertyid="city" class="rtltextaligneligible">Recife')
        self.assertEqual(ey.ler_pagina(pagina)["local"], "Recife, PE")

    def test_datas(self):
        self.assertEqual(ey._data_postada("Thu Oct 22 00:00:00 UTC 2026"), "2026-10-22")
        self.assertEqual(ey._data_postada("Mon Mar 2 00:00:00 UTC 2026"), "2026-03-02")
        self.assertEqual(ey._data_postada("2026-10-22T00:00:00Z"), "2026-10-22")
        self.assertIsNone(ey._data_postada(""))
        self.assertIsNone(ey._data_postada("ontem"))

    def test_url_e_id(self):
        url = ey.url_lista("desenvolvedor java", "Brazil", 25)
        self.assertTrue(url.startswith("https://careers.ey.com/ey/search/?q=desenvolvedor+java&locationsearch=Brazil"))
        self.assertIn("sortColumn=referencedate&sortDirection=desc&startrow=25", url)
        self.assertNotIn("startrow", ey.url_lista("x", "Brazil"))
        self.assertNotIn("/services/", url)  # o RSS fica numa área bloqueada pelo robots.txt (FR-009)
        self.assertEqual(ey.id_do_link(URL), "ey-9000001")
        self.assertEqual(ey.id_do_link(URL.rstrip("/") + "?locale=pt_BR"), "ey-9000001")
        self.assertIsNone(ey.id_do_link("https://careers.ey.com/ey/search/?q=x"))
        self.assertIsNone(ey.id_do_link("https://outro.com/ey/job/x/9000001/"))
        self.assertEqual((ey._pais("brazil"), ey._pais("usa"), ey._pais("portugal")),
                         ("Brazil", "United States", "Portugal"))


class TestBusca(SemRede):
    def test_tres_consultas_com_uma_leitura(self):
        self.respostas()
        c = grupos()
        remoto, erros = ey.buscar(c["remoto"], 168, 20)
        self.assertEqual((numeros(remoto), erros), ([9000004], []))
        local, _ = ey.buscar(c["local"], 168, 20)
        self.assertEqual(numeros(local), [9000001])  # SP; 9000003 é de Curitiba; 9000004 é remota
        todas, _ = ey.buscar(pais(), 168, 20)
        self.assertEqual(numeros(todas), [9000001, 9000003, 9000004])  # 9000002 não bate; 9000005 é antiga
        self.assertEqual(len([u for u in self.urls if "/search/" in u]), 2)  # as duas páginas, uma vez
        self.assertEqual(len(self.paginas_de_vaga()), 4)  # as que bateram, até a primeira fora da janela
        self.assertEqual([v["publicada_em"] for v in todas], ["2026-10-29", "2026-10-27", "2026-10-25"])

    def test_cidade_por_outro_local_da_vaga(self):
        self.respostas()
        cfg = {**CFG, "localidade": {**CFG["localidade"], "cidade": "Recife", "estado": "PE"}}
        local, _ = ey.buscar(grupos(cfg)["local"], 168, 20)
        self.assertEqual(numeros(local), [9000001])  # Recife é um dos locais da página da vaga

    def test_descricao_vem_da_busca(self):
        self.respostas()
        v = ey.buscar(pais(), 168, 20)[0][0]
        self.assertIn("Spring Boot", v["descricao"])
        antes = len(self.urls)
        self.assertEqual(ey.descrever(v), v["descricao"])
        self.assertEqual(len(self.urls), antes)  # sem pedido

    def test_descrever_sem_texto_abre_a_pagina(self):
        self.respostas()
        texto = ey.descrever({"url": URL, "descricao": ""})
        self.assertIn("Spring Boot", texto)
        self.assertEqual(self.urls, [URL])
        with self.assertRaises(_comum.FonteErro):
            ey.descrever({"url": "https://careers.ey.com/ey/search/", "descricao": ""})

    def test_memoria_evita_reabrir_a_pagina(self):
        self.respostas()
        primeira, _ = ey.buscar(pais(), 168, 20)
        memoria = json.loads(ey.ARQ_DATAS.read_text(encoding="utf-8"))
        self.assertEqual(sorted(memoria), ["9000001", "9000003", "9000004", "9000005"])
        self.assertEqual(memoria["9000001"], {"data": "2026-10-29", "locais": [["São Paulo JK", "SP"],
                                              ["Goiania", "GO"], ["Recife", "PE"]], "lida_em": "2026-10-30"})
        _comum.esquecer()
        self.urls.clear()
        segunda, _ = ey.buscar(pais(), 168, 20)
        self.assertEqual(numeros(segunda), numeros(primeira))
        self.assertEqual(self.paginas_de_vaga(), [])  # só as listas
        local, _ = ey.buscar(grupos()["local"], 168, 20)
        self.assertEqual(numeros(local), [9000001])  # os locais vêm da memória

    def test_memoria_esquece_o_que_e_velho(self):
        ey.ARQ_DATAS.parent.mkdir(parents=True)
        ey.ARQ_DATAS.write_text(json.dumps({"1": {"data": "2026-01-01", "locais": [], "lida_em": "2026-07-01"},
                                            "2": {"data": "2026-10-01", "locais": [], "lida_em": "2026-10-01"}}),
                                encoding="utf-8")
        self.respostas()
        ey.buscar(pais(), 168, 20)
        memoria = json.loads(ey.ARQ_DATAS.read_text(encoding="utf-8"))
        self.assertNotIn("1", memoria)
        self.assertIn("2", memoria)

    def test_memoria_ilegivel_vale_como_vazia(self):
        ey.ARQ_DATAS.parent.mkdir(parents=True)
        ey.ARQ_DATAS.write_text("{quebrado", encoding="utf-8")
        self.respostas()
        self.assertEqual(numeros(ey.buscar(pais(), 168, 20)[0]), [9000001, 9000003, 9000004])

    def test_limite_de_paginas_de_vaga(self):
        self.respostas()
        with mock.patch.object(ey, "MAX_VAGAS", 2):
            primeira, _ = ey.buscar(pais(), 168, 20)
            self.assertEqual(numeros(primeira), [9000001, 9000003])  # 9000004 fica para a próxima
            self.assertEqual(len(self.paginas_de_vaga()), 2)
            self.assertEqual(ey.descrever({"url": URL, "descricao": ""}), "")  # limite: sem pedido
            _comum.esquecer()
            segunda, _ = ey.buscar(pais(), 168, 20)
        self.assertEqual(numeros(segunda), [9000001, 9000003, 9000004])
        self.assertEqual(len(self.paginas_de_vaga()), 4)  # 9000004 e 9000005, não as duas já lidas

    def test_vaga_sem_data_entra(self):
        self.respostas({"9000003": SEM_DATA})
        todas, _ = ey.buscar(pais(), 168, 20)
        self.assertEqual(numeros(todas), [9000001, 9000003, 9000004])
        self.assertIsNone(todas[1]["publicada_em"])

    def test_ordem_por_data(self):
        antiga = {**DATAS, "9000003": "Sat Oct 10"}
        self.respostas({n: vaga(n, antiga) for n in antiga})
        self.assertEqual(numeros(ey.buscar(pais(), 168, 20)[0]), [9000001])  # para na primeira antiga
        _comum.esquecer()
        ey.ARQ_DATAS.unlink()
        with mock.patch.object(ey, "ORDEM_POR_DATA", False):
            self.assertEqual(numeros(ey.buscar(pais(), 168, 20)[0]), [9000001, 9000004])

    def test_vaga_encerrada_fica_de_fora(self):
        self.respostas({"9000003": _comum.FonteErro("a EY respondeu 404")})
        todas, erros = ey.buscar(pais(), 168, 20)
        self.assertEqual((numeros(todas), erros), ([9000001, 9000004], []))
        self.assertFalse(ey.parada())

    def test_titulo_com_aspas(self):
        self.respostas()
        todas, _ = ey.buscar({**pais(), "termo": '"desenvolvedor python"'}, 168, 20)
        self.assertEqual(numeros(todas), [9000004])
        self.assertIn("q=desenvolvedor+python&", self.urls[0])

    def test_pagina_ilegivel(self):
        self.respostas()
        with mock.patch.object(ey, "_baixar", return_value='<table><tr class="data-row"><td>?</td></tr></table>'):
            self.assertEqual(ey.buscar(pais(), 168, 20), ([], [ey.ILEGIVEL]))

    def test_sem_vagas(self):
        with mock.patch.object(ey, "_baixar", return_value="<html><body>Nenhuma vaga encontrada</body></html>"):
            self.assertEqual(ey.buscar(pais(), 168, 20), ([], []))


class TestBloqueio(SemRede):
    def test_429_na_lista(self):
        self.abridor([429])
        vs, erros = ey.buscar(pais(), 168, 20)
        self.assertEqual(vs, [])
        self.assertEqual(erros, [ey.BLOQUEIO + " (código 429); a busca seguiu sem ela"])
        self.assertTrue(ey.parada())
        self.assertEqual(ey.buscar({**pais(), "termo": "analista"}, 168, 20), ([], []))
        self.assertEqual(len(self.pedidos), 1)  # sem nova tentativa e sem pedido a mais
        _comum.esquecer()
        self.assertFalse(ey.parada())  # sem espera entre buscas

    def test_403_na_pagina_da_vaga(self):
        self.abridor([LISTA_1, LISTA_2, vaga("9000001"), 403])
        vs, erros = ey.buscar(pais(), 168, 20)
        self.assertEqual(numeros(vs), [9000001])  # a vaga já completa segue
        self.assertEqual(erros, [ey.BLOQUEIO + " (código 403); a busca seguiu sem ela"])
        self.assertEqual(len(self.pedidos), 4)
        self.assertEqual(ey.descrever({"url": URL, "descricao": ""}), "")  # parada: sem pedido
        self.assertEqual(len(self.pedidos), 4)

    def test_503_e_login(self):
        for resposta, final, motivo in ((503, None, "código 503"),
                                        (LISTA_1, "https://careers.ey.com/ey/login/", "pediu login")):
            _comum.esquecer()
            self.abridor([resposta], final or "https://careers.ey.com/ey/search/")
            vs, erros = ey.buscar(pais(), 168, 20)
            self.assertEqual((vs, erros), ([], [f"{ey.BLOQUEIO} ({motivo}); a busca seguiu sem ela"]))
            self.assertEqual(len(self.pedidos), 1)


class TestPausa(unittest.TestCase):
    def pausa(self, valor):
        with mock.patch.object(segredos, "ler", side_effect=lambda nome: valor if nome == "EY_PAUSA" else ""):
            return ey.pausa(), ey.aviso_pausa(3)

    def test_padrao_env_minimo_e_invalido(self):
        p, aviso = self.pausa("")
        self.assertEqual((p["faixa"], aviso), ((3.0, 7.0), None))
        p, aviso = self.pausa("10")
        self.assertEqual(p["faixa"], (10.0, 14.0))
        self.assertIn("EY: pausa de 10 a 14 s entre os pedidos (EY_PAUSA)", aviso)
        p, aviso = self.pausa("1")
        self.assertEqual(p["faixa"], (3.0, 7.0))
        self.assertIn("abaixo do mínimo", aviso)
        p, aviso = self.pausa("abc")
        self.assertEqual(p["faixa"], (3.0, 7.0))
        self.assertIn("não é um número", aviso)


class TestPadraoELink(SemRede):
    def test_ligada_por_padrao(self):
        self.assertIn("ey", FONTES)
        self.assertIn("ey", filtros.efetivos({})["fontes"])
        self.assertNotIn("ey", filtros.efetivos({"fontes": ["indeed"]})["fontes"])  # a escolha da pessoa vale
        nomes = {o["nome"]: o for o in filtros.opcoes()["fontes_nac"]}
        self.assertEqual(nomes["ey"]["rotulo"], "EY")
        self.assertIn("pausa", nomes["ey"]["termos"])
        self.assertIn("EY", banco.PLATAFORMAS)

    def test_adicionar_vaga_pelo_link(self):
        self.assertEqual(link.plataforma("careers.ey.com"), "EY")
        self.assertEqual(link.plataforma("www.ey.com"), "Outra")
        self.assertEqual(link.plataforma("careers.ey.com.exemplo.net"), "Outra")
        with mock.patch.object(link, "_baixar", return_value=VAGA):
            v = link.ler(URL)
        self.assertEqual((v["id"], v["plataforma"], v["empresa"], v["titulo"], v["local"], v["publicada_em"]),
                         ("ey-9000001", "EY", "EY", "Desenvolvedor(a) Java Pleno", "São Paulo JK, SP", "2026-10-29"))
        self.assertEqual(v["url"], URL)
        self.assertNotIn("locais", v)
        self.assertIn("Spring Boot", v["descricao"])


if __name__ == "__main__":
    unittest.main()
