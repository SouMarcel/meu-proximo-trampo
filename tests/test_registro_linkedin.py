"""Registro dos pedidos ao LinkedIn (spec 024), sem rede: cada pedido entra com a origem, o tipo, a resposta e o
intervalo desde o anterior, sem cargos nem endereços; o resumo mostra as rodadas e o que veio antes de um bloqueio."""
import json
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
from fontes import _comum, link, post  # noqa: E402
from fontes import linkedin as li  # noqa: E402
import vagas  # noqa: E402

LISTA = (RAIZ / "tests" / "dados" / "linkedin" / "lista.html").read_text(encoding="utf-8")


class Resposta:
    def __init__(self, texto):
        self.texto, self.headers, self.status = texto, mock.Mock(get_content_charset=lambda: "utf-8"), 200

    def read(self, _n=None):
        return self.texto.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Base(unittest.TestCase):
    def setUp(self):
        _comum.esquecer()
        li._estado["ultimo"] = None
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(li, "PAUSA", (0, 0)), mock.patch.object(li.time, "sleep"),
                  mock.patch.object(li, "ARQ_ESPERA", self.tmp / "linkedin-espera.json"),
                  mock.patch.object(li, "ARQ_PEDIDOS", self.tmp / "linkedin-pedidos.json"),
                  mock.patch.object(li.segredos, "ler", return_value=None)):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(_comum.esquecer)

    def rede(self, modulo, fila):
        """build_opener falso no módulo: cada pedido leva o próximo item (HTML, código HTTP ou OSError)."""
        def abrir(req, timeout=None):
            r = fila.pop(0)
            if isinstance(r, int):
                raise urllib.error.HTTPError(req.full_url, r, "x", {}, None)
            if isinstance(r, Exception):
                raise r
            return Resposta(r)
        p = mock.patch.object(modulo.urllib.request, "build_opener", return_value=mock.Mock(open=abrir))
        p.start()
        self.addCleanup(p.stop)

    def registro(self):
        return json.loads(li.ARQ_PEDIDOS.read_text(encoding="utf-8"))


class TestRegistro(Base):
    def test_pagina_descricao_e_bloqueio(self):
        self.rede(li, [LISTA, "<html></html>", 429])
        with li.origem("busca"):
            li._baixar(li.BUSCA + "?keywords=x")
            li._baixar(li.VAGA.format("1"))
            with self.assertRaises(_comum.FonteErro):
                li._baixar(li.VAGA.format("2"))
        r = self.registro()
        self.assertEqual([(p["origem"], p["tipo"], p["resposta"]) for p in r],
                         [("busca", "pagina", 200), ("busca", "descricao", 200), ("busca", "descricao", 429)])
        self.assertIsNone(r[0]["desde_anterior_s"])
        self.assertIsInstance(r[1]["desde_anterior_s"], float)
        self.assertNotIn("keywords", li.ARQ_PEDIDOS.read_text(encoding="utf-8"))  # sem cargos nem endereços
        self.assertEqual(set(r[0]), {"em", "origem", "tipo", "resposta", "desde_anterior_s"})

    def test_erro_de_rede_e_origem_padrao(self):
        self.rede(li, [OSError("sem rede")])
        with self.assertRaises(_comum.FonteErro):
            li._baixar(li.BUSCA)
        self.assertEqual([(p["origem"], p["resposta"]) for p in self.registro()], [("outro", "rede")])

    def test_origem_por_thread(self):
        vistos = {}

        def outra():
            vistos["outra"] = getattr(li._origem, "nome", None)
        with li.origem("busca"):
            t = threading.Thread(target=outra)
            t.start()
            t.join()
            vistos["esta"] = li._origem.nome
        self.assertEqual(vistos, {"outra": None, "esta": "busca"})
        self.assertIsNone(getattr(li._origem, "nome", None))

    def test_guarda_so_os_ultimos(self):
        with mock.patch.object(li, "MAX_PEDIDOS", 3):
            for i in range(5):
                li.registrar_pedido("pagina", 200 + i)
        self.assertEqual([p["resposta"] for p in self.registro()], [202, 203, 204])

    def test_sem_gravar_segue(self):
        with mock.patch.object(li, "ARQ_PEDIDOS", self.tmp / "arquivo" / "x.json"), \
                mock.patch.object(Path, "write_text", side_effect=OSError("disco")):
            li.registrar_pedido("pagina", 200)  # não levanta

    def test_link_e_post_colados(self):
        self.rede(link, [LISTA, 429])
        with mock.patch.object(link, "_host_publico", return_value=True):
            link._ler_linkedin(link.urlsplit("https://www.linkedin.com/jobs/view/4000000001/"))
            with self.assertRaises(link.LinkErro):
                link._ler_linkedin(link.urlsplit("https://www.linkedin.com/jobs/view/4000000002/"))
        self.rede(post, ["<html></html>"])
        post._baixar("urn:li:activity:1")
        self.assertEqual([(p["origem"], p["tipo"], p["resposta"]) for p in self.registro()],
                         [("adicionar", "link", 200), ("adicionar", "link", 429), ("adicionar", "post", 200)])

    def test_origem_nas_funcoes_do_vagas(self):
        visto = []
        falsa = mock.Mock(origem=li.origem)
        with mock.patch.dict(vagas.FONTES, {"linkedin": falsa}):
            @vagas._origem_linkedin("completar")
            def f():
                visto.append(li._origem.nome)
            f()
        self.assertEqual(visto, ["completar"])
        for fn, nome in ((vagas.executar, "busca"), (vagas.completar_pendentes, "completar"),
                         (vagas.descrever_uma, "forcar")):
            self.assertTrue(hasattr(fn, "__wrapped__"), nome)


class TestResumo(Base):
    def gravar(self, itens):
        li.ARQ_PEDIDOS.write_text(json.dumps(itens), encoding="utf-8")

    def test_sem_registro(self):
        self.assertIn("Nenhum pedido", li.resumo_pedidos())

    def test_rodadas_e_bloqueio(self):
        agora = datetime(2026, 10, 20, 13, 0)
        em = lambda m: (agora - timedelta(minutes=m)).isoformat(timespec="seconds")
        self.gravar([
            {"em": em(300), "origem": "forcar", "tipo": "descricao", "resposta": 200, "desde_anterior_s": None},
            {"em": em(40), "origem": "busca", "tipo": "pagina", "resposta": 200, "desde_anterior_s": 15600.0},
            {"em": em(39.8), "origem": "busca", "tipo": "pagina", "resposta": 429, "desde_anterior_s": 12.0},
        ])
        texto = li.resumo_pedidos(24, agora)
        self.assertIn("3, em 2 rodada(s)", texto)
        self.assertIn("bloqueio 429 (excesso de pedidos) no 2º pedido da rodada (pagina, busca), 12 s depois do "
                      "anterior; 2 pedido(s) ao LinkedIn nas 24 h antes", texto)
        self.assertNotIn("forcar", li.resumo_pedidos(1, agora))  # fora da janela pedida

    def test_comando(self):
        self.gravar([{"em": datetime.now().isoformat(timespec="seconds"), "origem": "busca", "tipo": "pagina",
                      "resposta": 200, "desde_anterior_s": None}])
        with mock.patch("builtins.print") as imprimir:
            self.assertEqual(vagas.cmd_pedidos_linkedin(mock.Mock(horas=48)), 0)
        self.assertIn("1 pagina", imprimir.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
