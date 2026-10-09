"""Testes do curriculo_ia.py e do registro do currículo na vaga, com a IA substituída. Conteúdo fictício."""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import banco  # noqa: E402
import curriculo  # noqa: E402
import curriculo_ia as cia  # noqa: E402
import ia  # noqa: E402
from test_conferir import PERFIL, VAGA, cv as cv_fiel  # noqa: E402

PERFIL_CPF = PERFIL + "\nCPF: 123.456.789-09\n- Cargos que procuro: Analista de Dados, Cientista de Dados\n"
VAGA_DOC = {"id": "v1", "titulo": "Analista de Dados Pleno", "empresa": "Empresa Ômega S.A.", "local": "Remoto",
            "descricao": VAGA}
TEC = cia.validar_tecnicas({"foco": True, "formato": "br"})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(cia, "CURRICULOS", self.tmp / "curriculos"),
                        mock.patch.object(curriculo, "para_pdf", lambda docx: (None, "sem PDF no teste")),
                        mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db")]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestNomesEPedido(Base):
    def test_nome_sem_colidir(self):
        dia = datetime(2026, 10, 9)
        nome = cia.nome_arquivo(VAGA_DOC, dia, self.tmp)
        self.assertEqual(nome, "2026-10-09-empresa-omega-s-a-analista-de-dados-pleno")
        (self.tmp / f"{nome}.json").write_text("{}", encoding="utf-8")
        self.assertEqual(cia.nome_arquivo(VAGA_DOC, dia, self.tmp), nome + "-2")
        self.assertEqual(cia.nome_arquivo(None, dia, self.tmp), "2026-10-09-base")
        self.assertTrue(cia.NOME_VALIDO.match(nome))

    def test_pedido(self):
        pedido = cia.montar_pedido(PERFIL_CPF, VAGA_DOC, TEC)
        self.assertNotIn("123.456.789-09", pedido)
        self.assertIn("[lacuna] Inglês fluente", pedido)
        self.assertIn("[tem] Experiência com SQL avançado", pedido)
        self.assertIn("Foco:", pedido)
        self.assertNotIn("XYZ (estilo Google):", pedido)
        self.assertIn('"experiencia"', pedido)  # o modelo
        base = cia.montar_pedido(PERFIL_CPF, None, TEC)
        self.assertIn("Analista de Dados, Cientista de Dados", base)
        self.assertNotIn("## Vaga", base)

    def test_validar_tecnicas(self):
        self.assertEqual(cia.validar_tecnicas({"paginas": "1", "formato": "us"})["paginas"], 1)
        with self.assertRaises(cia.GeracaoErro):
            cia.validar_tecnicas({"formato": "jp"})


class TestResposta(unittest.TestCase):
    def test_le_e_forca_tecnicas(self):
        tec = cia.validar_tecnicas({"formato": "us"})
        texto = "Aqui está:\n" + json.dumps({**cv_fiel(), "tecnicas": {"formato": "br"}, "idioma": "pt", "outra": 1}) + "\nFim."
        cv = cia.ler_resposta(texto, tec)
        self.assertEqual(cv["tecnicas"], tec)
        self.assertEqual(cv["idioma"], "en")
        self.assertNotIn("outra", cv)

    def test_invalida(self):
        for texto in ("sem json", "{quebrado", json.dumps({"experiencia": []})):
            with self.assertRaises(cia.GeracaoErro):
                cia.ler_resposta(texto, TEC)


class TestGerar(Base):
    def test_gera_arquivos_e_meta(self):
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())) as resp:
            meta = cia.gerar(VAGA_DOC, TEC, perfil=PERFIL)
        self.assertEqual(resp.call_count, 1)
        pasta = self.tmp / "curriculos"
        for ext in (".json", ".docx", ".meta.json"):
            self.assertTrue((pasta / f"{meta['nome']}{ext}").exists(), ext)
        self.assertIsNone(meta["arquivos"]["pdf"])
        self.assertTrue(meta["pronto"])
        self.assertEqual(meta["alvo"]["id"], "v1")
        self.assertTrue(meta["conferencia"]["requisitos"])
        lista = cia.listar("v1")
        self.assertEqual([m["nome"] for m in lista], [meta["nome"]])
        self.assertEqual(lista[0]["disponivel"], {"json": True, "docx": True, "pdf": False})
        self.assertEqual(cia.listar(base=True), [])

    def test_numero_inventado_nao_pronto(self):
        c = cv_fiel()
        c["experiencia"][0]["cargos"][0]["itens"].append("Aumentou a receita em 45%")
        with mock.patch.object(ia, "responder", return_value=json.dumps(c)):
            meta = cia.gerar(VAGA_DOC, TEC, perfil=PERFIL)
        self.assertFalse(meta["pronto"])
        self.assertEqual(meta["conferencia"]["veredito"], "bloquear")

    def test_falha_nao_deixa_arquivo(self):
        with mock.patch.object(ia, "responder", side_effect=ia.IAErro("fora do ar")):
            with self.assertRaises(cia.GeracaoErro):
                cia.gerar(VAGA_DOC, TEC, perfil=PERFIL)
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())), \
                mock.patch.object(cia.conferir, "conferir", side_effect=RuntimeError("x")):
            with self.assertRaises(RuntimeError):
                cia.gerar(VAGA_DOC, TEC, perfil=PERFIL)
        self.assertEqual(list((self.tmp / "curriculos").glob("*")), [])
        with self.assertRaises(cia.GeracaoErro):
            cia.gerar(VAGA_DOC, TEC, perfil="")

    def test_base_duas_versoes(self):
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())):
            a = cia.gerar(None, TEC, perfil=PERFIL)
            b = cia.gerar(None, TEC, perfil=PERFIL)
        self.assertNotEqual(a["nome"], b["nome"])
        self.assertEqual(len(cia.listar(base=True)), 2)

    def test_arquivo_servivel(self):
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())):
            meta = cia.gerar(None, TEC, perfil=PERFIL)
        self.assertTrue(cia.arquivo_servivel(meta["arquivos"]["docx"]))
        for ruim in ("../banco.db", "..\\x.docx", meta["arquivos"]["json"], "nao-existe.pdf", "A.pdf", "x.docx/../y.pdf"):
            self.assertIsNone(cia.arquivo_servivel(ruim), ruim)

    def test_registrar_na_vaga(self):
        banco.inserir_vagas([{"id": "v1", "titulo": "Analista", "empresa": "Ômega", "triagem": "pendente"}])
        banco.registrar_curriculo("v1", "2026-10-09-omega-analista")
        banco.registrar_curriculo("v1", "2026-10-09-omega-analista-2")
        self.assertEqual(banco.obter("v1")["curriculos"], ["2026-10-09-omega-analista", "2026-10-09-omega-analista-2"])
        with self.assertRaises(KeyError):
            banco.registrar_curriculo("nao", "x")
        with self.assertRaises(ValueError):
            banco.registrar_curriculo("v1", "../x")


if __name__ == "__main__":
    unittest.main()
