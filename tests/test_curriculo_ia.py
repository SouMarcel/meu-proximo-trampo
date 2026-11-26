"""Testes do curriculo_ia.py e do registro do currículo na vaga, com a IA substituída. Conteúdo fictício."""
import json
import re
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
CONTATO = {"nome": "Pessoa", "sobrenome": "Fictícia", "email": "pessoa@exemplo.com", "telefone": "+5511900000000",
           "cidade": "São Paulo", "estado": "SP", "pais": "Brasil", "linkedin": "https://www.linkedin.com/in/pessoa-ficticia/"}


def salvar_contato(pasta: Path, dados: dict = CONTATO):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "contato.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


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

    def test_nome_completo(self):
        dia = datetime(2026, 10, 9)
        nome = cia.nome_arquivo(None, dia, self.tmp, completo=True)
        self.assertEqual(nome, "2026-10-09-base-completo")
        (self.tmp / f"{nome}.json").write_text("{}", encoding="utf-8")
        self.assertEqual(cia.nome_arquivo(None, dia, self.tmp, completo=True), nome + "-2")

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

    def test_pedido_orcamento_2_paginas(self):
        tec2 = cia.validar_tecnicas({"paginas": 2})
        pedido = cia.montar_pedido(PERFIL_CPF, VAGA_DOC, tec2)
        self.assertIn("800 palavras", pedido)
        self.assertIn("3 experiências mais recentes", pedido)
        self.assertIn("Limite: até 2 página(s)", pedido)

    def test_pedido_orcamento_1_pagina(self):
        tec1 = cia.validar_tecnicas({"paginas": 1})
        pedido = cia.montar_pedido(PERFIL_CPF, VAGA_DOC, tec1)
        self.assertIn("Limite: até 1 página(s). Para caber, siga este orçamento:\n" + cia.ORCAMENTO[1], pedido)
        self.assertNotIn(cia.ORCAMENTO[2], pedido)  # o guia cita os dois números; o bloco do limite é só o de 1

    def test_pedido_completo(self):
        tec0 = cia.validar_tecnicas({"paginas": 0})
        pedido = cia.montar_pedido(PERFIL_CPF, None, tec0)
        self.assertIn("Currículo completo", pedido)
        self.assertNotIn("Limite: até", pedido)

    def test_orcamento_1_a_5(self):
        palavras = []
        for n in range(1, 6):
            self.assertIn(n, cia.ORCAMENTO)
            tec = cia.validar_tecnicas({"paginas": n})
            pedido = cia.montar_pedido(PERFIL_CPF, VAGA_DOC, tec)
            self.assertIn(cia.ORCAMENTO[n], pedido)
            m = re.search(r"cerca de (\d+) palavras", cia.ORCAMENTO[n], re.IGNORECASE)
            self.assertIsNotNone(m)
            palavras.append(int(m.group(1)))
        for i in range(len(palavras) - 1):
            self.assertLess(palavras[i], palavras[i + 1])

    def test_validar_tecnicas(self):
        self.assertEqual(cia.validar_tecnicas({"paginas": "1", "formato": "us"})["paginas"], 1)
        self.assertEqual(cia.validar_tecnicas({"paginas": 4})["paginas"], 4)
        with self.assertRaises(cia.GeracaoErro):
            cia.validar_tecnicas({"paginas": 6})
        with self.assertRaises(cia.GeracaoErro):
            cia.validar_tecnicas({"formato": "jp"})
        with self.assertRaises(cia.GeracaoErro):
            cia.validar_tecnicas({"paginas": 0}, VAGA_DOC)
        self.assertEqual(cia.validar_tecnicas({"paginas": 0})["paginas"], 0)


class TestResposta(unittest.TestCase):
    def test_le_e_forca_tecnicas(self):
        tec = cia.validar_tecnicas({"formato": "us"})
        texto = "Aqui está:\n" + json.dumps({**cv_fiel(), "tecnicas": {"formato": "br"}, "idioma": "pt", "outra": 1}) + "\nFim."
        cv = cia.ler_resposta(texto, tec)
        self.assertEqual(cv["tecnicas"], tec)
        self.assertEqual(cv["idioma"], "en")
        self.assertNotIn("outra", cv)

    def test_nome_dos_dados_de_contato(self):
        sem_nome = {k: v for k, v in cv_fiel().items() if k != "nome"}
        with self.assertRaises(cia.GeracaoErro):
            cia.ler_resposta(json.dumps(sem_nome), TEC)
        self.assertEqual(cia.ler_resposta(json.dumps(sem_nome), TEC, "Pessoa Fictícia")["nome"], "Pessoa Fictícia")
        self.assertEqual(cia.ler_resposta(json.dumps(cv_fiel()), TEC, "Pessoa Fictícia")["nome"], "Pessoa Fictícia")

    def test_nome_do_contato(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "contato.json").write_text(json.dumps({"nome": "Pessoa", "sobrenome": "Fictícia"}), encoding="utf-8")
            with mock.patch.object(banco, "ARQUIVO", tmp / "banco.db"):
                self.assertEqual(cia.nome_do_contato(), "Pessoa Fictícia")
            with mock.patch.object(banco, "ARQUIVO", tmp / "outro" / "banco.db"):
                self.assertEqual(cia.nome_do_contato(), "")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_contato_dos_dados_de_contato(self):
        salvos = ["São Paulo, SP, Brasil", "pessoa@exemplo.com", "+55 11 90000-0000"]
        self.assertEqual(cia.ler_resposta(json.dumps(cv_fiel()), TEC, "", salvos)["contato"], salvos)
        self.assertEqual(cia.ler_resposta(json.dumps(cv_fiel()), TEC, "", [])["contato"], ["ana@exemplo.com"])

    def test_linha_de_contato(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            salvar_contato(tmp)
            with mock.patch.object(banco, "ARQUIVO", tmp / "banco.db"):
                self.assertEqual(cia.linha_de_contato("pt"), ["São Paulo, SP, Brasil", "pessoa@exemplo.com",
                                                             "+55 11 90000-0000", "linkedin.com/in/pessoa-ficticia"])
                self.assertEqual(cia.linha_de_contato("en")[0], "São Paulo, SP, Brazil")
            with mock.patch.object(banco, "ARQUIVO", tmp / "outro" / "banco.db"):
                self.assertEqual(cia.linha_de_contato("pt"), [])
            self.assertEqual(cia.linha_de_contato("pt", {"email": "a@b.co", "telefone": "(11) 3333-4444"}),
                             ["a@b.co", "(11) 3333-4444"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

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

    def test_contato_salvo_no_cabecalho_sem_ir_a_ia(self):
        salvar_contato(self.tmp)
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())) as resp:
            meta = cia.gerar(VAGA_DOC, TEC, perfil=PERFIL)
        cv = json.loads((self.tmp / "curriculos" / f"{meta['nome']}.json").read_text(encoding="utf-8"))
        self.assertEqual(cv["nome"], "Pessoa Fictícia")
        self.assertIn("pessoa@exemplo.com", cv["contato"])
        self.assertIn("+55 11 90000-0000", cv["contato"])
        self.assertNotIn("pessoa@exemplo.com", resp.call_args[0][0])
        from docx import Document
        texto = "\n".join(par.text for par in Document(str(self.tmp / "curriculos" / f"{meta['nome']}.docx")).paragraphs)
        self.assertIn("pessoa@exemplo.com | +55 11 90000-0000", texto)

    def test_contato_salvo_no_curriculo_base(self):
        salvar_contato(self.tmp)
        for tec in (TEC, cia.validar_tecnicas({"paginas": 0})):  # base e base completo
            with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())):
                meta = cia.gerar(None, tec, perfil=PERFIL)
            self.assertIn("-base", meta["nome"])
            cv = json.loads((self.tmp / "curriculos" / f"{meta['nome']}.json").read_text(encoding="utf-8"))
            self.assertIn("pessoa@exemplo.com", cv["contato"])
            self.assertIn("+55 11 90000-0000", cv["contato"])

    def test_sem_dados_de_contato_fica_o_da_ia(self):
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())):
            meta = cia.gerar(VAGA_DOC, TEC, perfil=PERFIL)
        cv = json.loads((self.tmp / "curriculos" / f"{meta['nome']}.json").read_text(encoding="utf-8"))
        self.assertEqual(cv["contato"], ["ana@exemplo.com"])

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

    def test_base_completo(self):
        tec0 = cia.validar_tecnicas({"paginas": 0})
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())):
            meta = cia.gerar(None, tec0, perfil=PERFIL)
        self.assertTrue(meta["nome"].endswith("-base-completo"))
        self.assertFalse(meta["acima_do_limite"])
        self.assertEqual(meta["sugestoes_corte"], [])

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


class TestApagar(Base):
    def _gerar(self, vaga=None):
        with mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())):
            return cia.gerar(vaga, TEC, perfil=PERFIL)

    def _arquivos(self, nome):
        return [cia.CURRICULOS / f"{nome}{s}" for s in (".json", ".docx", ".pdf", ".meta.json")]

    def test_apaga_so_o_pedido(self):
        a = self._gerar()
        b = self._gerar()
        ret = cia.apagar(a["nome"])
        self.assertEqual(ret["nome"], a["nome"])
        self.assertFalse(any(p.exists() for p in self._arquivos(a["nome"])))
        self.assertTrue(all(p.exists() for p in self._arquivos(b["nome"]) if not p.name.endswith(".pdf")))
        self.assertEqual(len(cia.listar(base=True)), 1)
        self.assertEqual(list(cia.CURRICULOS.glob("*.apagando")), [])

    def test_retorna_alvo(self):
        meta = self._gerar(VAGA_DOC)
        alvo = cia.apagar(meta["nome"])["alvo"]
        self.assertEqual((alvo["tipo"], alvo["id"]), ("vaga", "v1"))

    def test_nomes_invalidos_e_inexistente(self):
        for ruim in ("../x", "A"):
            with self.assertRaises(cia.GeracaoErro):
                cia.apagar(ruim)
        with self.assertRaises(FileNotFoundError):
            cia.apagar("nao-existe")

    def test_carta_e_apagada(self):
        cia.CURRICULOS.mkdir(parents=True, exist_ok=True)
        meta = {
            "nome": "carta-x",
            "tipo": "carta",
            "alvo": {"tipo": "vaga", "id": "v1"},
            "arquivos": {"txt": "carta-x.txt", "docx": "carta-x.docx", "pdf": "carta-x.pdf"},
        }
        (cia.CURRICULOS / "carta-x.meta.json").write_text(json.dumps(meta), encoding="utf-8")
        for ext in (".txt", ".docx", ".pdf"):
            (cia.CURRICULOS / f"carta-x{ext}").write_text("conteudo", encoding="utf-8")
        ret = cia.apagar("carta-x")
        self.assertEqual(ret["nome"], "carta-x")
        self.assertEqual(ret["tipo"], "carta")
        for ext in (".txt", ".docx", ".pdf", ".meta.json"):
            self.assertFalse((cia.CURRICULOS / f"carta-x{ext}").exists())

    def test_apagar_lote_dois_documentos(self):
        a = self._gerar()
        b = self._gerar()
        ret = cia.apagar_lote([a["nome"], b["nome"]])
        self.assertEqual(len(ret), 2)
        self.assertEqual(ret[0]["nome"], a["nome"])
        self.assertEqual(ret[1]["nome"], b["nome"])
        self.assertFalse(any(p.exists() for p in self._arquivos(a["nome"])))
        self.assertFalse(any(p.exists() for p in self._arquivos(b["nome"])))
        self.assertEqual(len(cia.listar(base=True)), 0)

    def test_apagar_lote_nome_inexistente_nada_apagado(self):
        a = self._gerar()
        with self.assertRaises(FileNotFoundError):
            cia.apagar_lote([a["nome"], "doc-inexistente"])
        self.assertTrue(all(p.exists() for p in self._arquivos(a["nome"]) if not p.name.endswith(".pdf")))

    def test_apagar_lote_falha_segundo_documento_desfaz(self):
        a = self._gerar()
        b = self._gerar()
        original = Path.rename

        def rename(self_, destino):
            if destino.name.startswith(b["nome"]):
                raise PermissionError("arquivo aberto")
            return original(self_, destino)

        with mock.patch.object(Path, "rename", rename):
            with self.assertRaises(cia.GeracaoErro):
                cia.apagar_lote([a["nome"], b["nome"]])

        self.assertEqual(list(cia.CURRICULOS.glob("*.apagando")), [])
        self.assertTrue(all(p.exists() for p in self._arquivos(a["nome"]) if not p.name.endswith(".pdf")))
        self.assertTrue(all(p.exists() for p in self._arquivos(b["nome"]) if not p.name.endswith(".pdf")))

    def test_falha_no_meio_desfaz(self):
        nome = self._gerar()["nome"]
        antes = sorted(p.name for p in cia.CURRICULOS.iterdir())
        original = Path.rename
        chamadas = {"n": 0}

        def rename(self_, destino):
            chamadas["n"] += 1
            if chamadas["n"] == 2:
                raise PermissionError("aberto")
            return original(self_, destino)

        with mock.patch.object(Path, "rename", rename):
            with self.assertRaises(cia.GeracaoErro):
                cia.apagar(nome)
        self.assertEqual(sorted(p.name for p in cia.CURRICULOS.iterdir()), antes)


class TestDocumentosDaVaga(Base):
    def test_documentos_da_vaga(self):
        cia.CURRICULOS.mkdir(parents=True, exist_ok=True)
        # 1. pelo alvo.id
        (cia.CURRICULOS / "cv-v1.meta.json").write_text(json.dumps({
            "nome": "cv-v1", "tipo": "curriculo", "alvo": {"tipo": "vaga", "id": "v1"},
            "criado_em": "2026-11-20T10:00:00"
        }), encoding="utf-8")
        # 2. por ids_relacionados
        (cia.CURRICULOS / "carta-antiga.meta.json").write_text(json.dumps({
            "nome": "carta-antiga", "tipo": "carta", "alvo": {"tipo": "vaga", "id": "v_antiga"},
            "criado_em": "2026-11-21T10:00:00"
        }), encoding="utf-8")
        # 3. por nome em documentos
        (cia.CURRICULOS / "respostas-outra.meta.json").write_text(json.dumps({
            "nome": "respostas-outra", "tipo": "respostas", "alvo": {"tipo": "vaga", "id": "v_outra"},
            "criado_em": "2026-11-22T10:00:00"
        }), encoding="utf-8")
        # 4. por nome em curriculos
        (cia.CURRICULOS / "cv-antigo.meta.json").write_text(json.dumps({
            "nome": "cv-antigo", "alvo": {"tipo": "vaga", "id": "v_outra2"},
            "criado_em": "2026-11-19T10:00:00"
        }), encoding="utf-8")
        # 5. base (deve ser ignorado mesmo se em curriculos)
        (cia.CURRICULOS / "cv-base.meta.json").write_text(json.dumps({
            "nome": "cv-base", "tipo": "curriculo", "alvo": {"tipo": "base"},
            "criado_em": "2026-11-25T10:00:00"
        }), encoding="utf-8")
        # 6. documento de outra vaga
        (cia.CURRICULOS / "carta-estranha.meta.json").write_text(json.dumps({
            "nome": "carta-estranha", "tipo": "carta", "alvo": {"tipo": "vaga", "id": "v999"},
            "criado_em": "2026-11-24T10:00:00"
        }), encoding="utf-8")

        vaga = {
            "id": "v1",
            "ids_relacionados": ["v_antiga"],
            "curriculos": ["cv-antigo", "cv-base"],
            "documentos": [{"tipo": "respostas", "nome": "respostas-outra"}],
        }

        docs = cia.documentos_da_vaga(vaga)
        nomes = [d["nome"] for d in docs]
        self.assertEqual(nomes, ["respostas-outra", "carta-antiga", "cv-v1", "cv-antigo"])
        self.assertNotIn("cv-base", nomes)
        self.assertNotIn("carta-estranha", nomes)
        self.assertEqual(docs[3]["tipo"], "curriculo")  # padrão preenchido


class TestDocumentosOrfaos(Base):
    def test_documentos_orfaos(self):
        cia.CURRICULOS.mkdir(parents=True, exist_ok=True)
        # Arquivada
        (cia.CURRICULOS / "doc-arq.meta.json").write_text(json.dumps({
            "nome": "doc-arq", "tipo": "curriculo",
            "alvo": {"tipo": "vaga", "id": "v_arq", "titulo": "Dev Python", "empresa": "Empresa A"},
            "criado_em": "2026-11-20T10:00:00"
        }), encoding="utf-8")
        # Removida (visitada sem etapa)
        (cia.CURRICULOS / "doc-rem.meta.json").write_text(json.dumps({
            "nome": "doc-rem", "tipo": "carta",
            "alvo": {"tipo": "vaga", "id": "v_rem", "titulo": "Analista", "empresa": "Empresa B"},
            "criado_em": "2026-11-21T10:00:00"
        }), encoding="utf-8")
        # Id inexistente (vaga não encontrada)
        (cia.CURRICULOS / "doc-sumiu.meta.json").write_text(json.dumps({
            "nome": "doc-sumiu", "tipo": "respostas",
            "alvo": {"tipo": "vaga", "id": "v_sumiu", "titulo": "Engenheiro", "empresa": "Empresa C"},
            "criado_em": "2026-11-22T10:00:00"
        }), encoding="utf-8")
        # Vaga viva (não deve aparecer)
        (cia.CURRICULOS / "doc-viva.meta.json").write_text(json.dumps({
            "nome": "doc-viva", "tipo": "curriculo",
            "alvo": {"tipo": "vaga", "id": "v_viva", "titulo": "Arquiteto", "empresa": "Empresa D"},
            "criado_em": "2026-11-23T10:00:00"
        }), encoding="utf-8")
        # Documento de vaga que saiu, mas cujo nome está em documentos de outra vaga viva (junção de repetidas)
        (cia.CURRICULOS / "doc-repetida.meta.json").write_text(json.dumps({
            "nome": "doc-repetida", "tipo": "curriculo",
            "alvo": {"tipo": "vaga", "id": "v_saiu", "titulo": "Cientista", "empresa": "Empresa E"},
            "criado_em": "2026-11-24T10:00:00"
        }), encoding="utf-8")
        # Documento base (não é alvo.tipo == vaga, não deve aparecer)
        (cia.CURRICULOS / "doc-base.meta.json").write_text(json.dumps({
            "nome": "doc-base", "tipo": "curriculo",
            "alvo": {"tipo": "base"},
            "criado_em": "2026-11-25T10:00:00"
        }), encoding="utf-8")

        vagas = [
            {"id": "v_arq", "titulo": "Dev Python", "empresa": "Empresa A", "arquivada_em": "2026-11-01"},
            {"id": "v_rem", "titulo": "Analista", "empresa": "Empresa B", "triagem": "visitada", "etapa": None},
            {"id": "v_saiu", "titulo": "Cientista", "empresa": "Empresa E", "triagem": "visitada", "etapa": None},
            {"id": "v_viva", "titulo": "Arquiteto", "empresa": "Empresa D", "triagem": "seguir", "etapa": "salva"},
            {"id": "v_outra_viva", "titulo": "Cientista Sênior", "empresa": "Empresa E", "triagem": "seguir", "etapa": "salva",
             "documentos": [{"nome": "doc-repetida", "tipo": "curriculo"}]},
        ]

        orfaos = cia.documentos_orfaos(vagas)
        nomes = [d["nome"] for d in orfaos]

        self.assertNotIn("doc-viva", nomes)
        self.assertNotIn("doc-repetida", nomes)
        self.assertNotIn("doc-base", nomes)

        self.assertEqual(len(orfaos), 3)
        self.assertEqual(orfaos[0]["nome"], "doc-sumiu")
        self.assertEqual(orfaos[0]["motivo"], "vaga não encontrada")
        self.assertEqual(orfaos[0]["titulo"], "Engenheiro")
        self.assertEqual(orfaos[0]["empresa"], "Empresa C")
        self.assertEqual(orfaos[0]["vaga_id"], "v_sumiu")

        self.assertEqual(orfaos[1]["nome"], "doc-rem")
        self.assertEqual(orfaos[1]["motivo"], "removida")
        self.assertEqual(orfaos[1]["titulo"], "Analista")
        self.assertEqual(orfaos[1]["empresa"], "Empresa B")
        self.assertEqual(orfaos[1]["vaga_id"], "v_rem")

        self.assertEqual(orfaos[2]["nome"], "doc-arq")
        self.assertEqual(orfaos[2]["motivo"], "arquivada")
        self.assertEqual(orfaos[2]["titulo"], "Dev Python")
        self.assertEqual(orfaos[2]["empresa"], "Empresa A")
        self.assertEqual(orfaos[2]["vaga_id"], "v_arq")


def cv_menor():
    c = cv_fiel()
    c["resumo"] = "Analista de dados."
    return c


def cv_maior():
    c = cv_fiel()
    c["experiencia"].append({
        "empresa": "Empresa Gama", "periodo": "01/2015 – 12/2017",
        "cargos": [{"cargo": "Estagiário de Dados", "itens": ["Auxílio em relatórios"]}]
    })
    return c


class TestEncurtar(Base):
    def setUp(self):
        super().setUp()
        self.patch_pdf = mock.patch.object(curriculo, "para_pdf", lambda docx: (docx.with_suffix(".pdf"), ""))
        self.patch_pdf.start()

    def tearDown(self):
        self.patch_pdf.stop()
        super().tearDown()

    def test_encurtou(self):
        tec = cia.validar_tecnicas({"paginas": 2, "paginas_obrigatorio": True})
        respostas = [json.dumps(cv_fiel()), json.dumps(cv_menor())]
        with mock.patch.object(curriculo, "paginas", side_effect=[3, 2]), \
                mock.patch.object(ia, "responder", side_effect=respostas) as resp:
            meta = cia.gerar(VAGA_DOC, tec, perfil=PERFIL)
        self.assertEqual(meta["encurtado"], {"de": 3, "para": 2, "tentativas": 1})
        self.assertFalse(meta["acima_do_limite"])
        self.assertEqual(meta["paginas"], 2)
        self.assertEqual(resp.call_count, 2)
        mensagens = [p["mensagem"] for p in meta["conferencia"]["ats"]]
        self.assertFalse(any("página" in m for m in mensagens))

    def test_encurtar_mantem_contato_sem_ir_a_ia(self):
        salvar_contato(self.tmp)
        tec = cia.validar_tecnicas({"paginas": 2, "paginas_obrigatorio": True})
        respostas = [json.dumps(cv_fiel()), json.dumps(cv_menor())]
        with mock.patch.object(curriculo, "paginas", side_effect=[3, 2]),                 mock.patch.object(ia, "responder", side_effect=respostas) as resp:
            meta = cia.gerar(VAGA_DOC, tec, perfil=PERFIL)
        self.assertEqual(meta["paginas"], 2)
        for chamada in resp.call_args_list:
            self.assertNotIn("pessoa@exemplo.com", chamada[0][0])
        cv = json.loads((self.tmp / "curriculos" / f"{meta['nome']}.json").read_text(encoding="utf-8"))
        self.assertIn("pessoa@exemplo.com", cv["contato"])

    def test_maior_descartada(self):
        tec = cia.validar_tecnicas({"paginas": 2, "paginas_obrigatorio": True})
        respostas = [json.dumps(cv_fiel()), json.dumps(cv_maior()), json.dumps(cv_maior())]
        with mock.patch.object(curriculo, "paginas", side_effect=[3]), \
                mock.patch.object(ia, "responder", side_effect=respostas) as resp:
            meta = cia.gerar(VAGA_DOC, tec, perfil=PERFIL)
        self.assertEqual(meta["encurtado"]["tentativas"], 2)
        self.assertTrue(meta["acima_do_limite"])
        self.assertEqual(resp.call_count, 3)
        gravado = json.loads((self.tmp / "curriculos" / f"{meta['nome']}.json").read_text(encoding="utf-8"))
        self.assertEqual(len(gravado["experiencia"]), len(cv_fiel()["experiencia"]))
        pontos = [p for p in meta["conferencia"]["ats"] if "não conseguiu" in p["mensagem"]]
        self.assertTrue(bool(pontos))
        self.assertEqual(pontos[0]["nivel"], "conferir")
        self.assertEqual(pontos[0]["trecho"], "3 páginas")
        self.assertEqual(meta["conferencia"]["veredito"], "conferir")

    def test_ia_falha_ao_encurtar(self):
        tec = cia.validar_tecnicas({"paginas": 2, "paginas_obrigatorio": True})
        respostas = [json.dumps(cv_fiel()), ia.IAErro("fora")]
        with mock.patch.object(curriculo, "paginas", side_effect=[3]), \
                mock.patch.object(ia, "responder", side_effect=respostas) as resp:
            meta = cia.gerar(VAGA_DOC, tec, perfil=PERFIL)
        self.assertTrue(meta["acima_do_limite"])
        self.assertEqual(resp.call_count, 2)
        pasta = self.tmp / "curriculos"
        self.assertTrue((pasta / f"{meta['nome']}.json").exists())
        self.assertTrue((pasta / f"{meta['nome']}.docx").exists())
        mensagens = [p["mensagem"] for p in meta["conferencia"]["ats"]]
        self.assertTrue(any("não conseguiu" in m for m in mensagens))
        self.assertEqual(meta["conferencia"]["veredito"], "conferir")

    def test_sem_a_tecnica(self):
        tec = cia.validar_tecnicas({"paginas": 2, "paginas_obrigatorio": False})
        with mock.patch.object(curriculo, "paginas", side_effect=[3]), \
                mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())) as resp:
            meta = cia.gerar(VAGA_DOC, tec, perfil=PERFIL)
        self.assertEqual(resp.call_count, 1)
        self.assertNotIn("encurtado", meta)
        self.assertTrue(meta["acima_do_limite"])
        pontos = [p for p in meta["conferencia"]["ats"] if "Limite de páginas obrigatório" in p["mensagem"]]
        self.assertTrue(bool(pontos))
        self.assertEqual(pontos[0]["nivel"], "conferir")
        self.assertEqual(pontos[0]["trecho"], "3 páginas")
        self.assertEqual(meta["conferencia"]["veredito"], "conferir")

    def test_completo_zero(self):
        tec = cia.validar_tecnicas({"paginas": 0, "paginas_obrigatorio": True})
        with mock.patch.object(curriculo, "paginas", side_effect=[5]), \
                mock.patch.object(ia, "responder", return_value=json.dumps(cv_fiel())) as resp:
            meta = cia.gerar(None, tec, perfil=PERFIL)
        self.assertEqual(resp.call_count, 1)
        self.assertNotIn("encurtado", meta)
        self.assertFalse(meta["acima_do_limite"])
        mensagens = [p["mensagem"] for p in meta["conferencia"]["ats"]]
        self.assertFalse(any("página" in m or "limite" in m for m in mensagens))


class TestEncurtarFuncoesPuras(unittest.TestCase):
    def test_cresceu(self):
        base = cv_fiel()
        maior = cv_maior()
        menor = cv_menor()
        self.assertTrue(cia._cresceu(maior, base))
        self.assertFalse(cia._cresceu(menor, base))
        self.assertFalse(cia._cresceu(base, base))
        com_mais_texto = cv_fiel()
        com_mais_texto["resumo"] = com_mais_texto["resumo"] + " Texto adicional muito longo para teste."
        self.assertTrue(cia._cresceu(com_mais_texto, base))

    def test_montar_pedido_encurtar(self):
        tec = cia.validar_tecnicas({"paginas": 2, "paginas_obrigatorio": True})
        pedido = cia.montar_pedido_encurtar(cv_fiel(), tec, 3)
        self.assertIn("deu 3 páginas; o limite é 2", pedido)
        self.assertIn("só tire ou condense", pedido)
        self.assertIn("mantenha completas as 3 experiências mais recentes", pedido)
        self.assertIn("800 palavras", pedido)
        self.assertIn("Responda SOMENTE com o JSON no mesmo formato, sem texto antes ou depois e sem a chave tecnicas", pedido)
        self.assertNotIn('"tecnicas":', pedido)
        self.assertNotIn("ana@exemplo.com", pedido)  # o contato nunca vai à IA


if __name__ == "__main__":
    unittest.main()
