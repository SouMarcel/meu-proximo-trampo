"""Preparação para entrevista (entrevista.py) com perfil e vaga fictícios e uma IA falsa: dossiê e perguntas sem IA
(SC-001), histórias conferidas (SC-002) e salvas só na confirmação (SC-003), salário sem valor de fora (SC-004) e
retorno da simulação conferido (SC-005)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import entrevista as en  # noqa: E402
import ia  # noqa: E402

PERFIL = (Path(__file__).resolve().parent / "dados" / "kit" / "perfil-ficticio.md").read_text(encoding="utf-8")
PERFIL_SALARIO = PERFIL + "\n## Pretensão\n- Pretensão salarial: R$ 9.000 por mês (CLT)\n"
VAGAS = {
    "v1": {"titulo": "Analista de Dados", "empresa": "Empresa Delta", "etapa": "entrevista", "salario": "R$ 8.000 - R$ 10.000",
           "moeda": "BRL", "resumo": "Boa aderência em SQL e Power BI.", "lacunas": ["Tableau", "Certificação AWS"],
           "anotacao": "Recrutadora pediu para falar de painéis.",
           "descricao": "Somos uma empresa de varejo.\n\nRequisitos:\n- SQL avançado\n- Power BI\n- Python para automação\n\n"
                        "Benefícios:\n- Vale-refeição"},
    "v2": {"titulo": "Analista de BI", "empresa": "Empresa Épsilon", "etapa": "entrevista", "descricao": "Vaga de BI."},
}


class ComDados(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(en, "PASTA", self.tmp / "entrevistas"),
                  mock.patch.object(banco, "obter", side_effect=lambda vid: dict(VAGAS[vid]) if vid in VAGAS else None),
                  mock.patch.object(en, "perfil_texto", return_value=PERFIL)):
            p.start()
            self.addCleanup(p.stop)

    def com_ia(self, resposta):
        """IA falsa: `resposta` é texto ou função do pedido."""
        for p in (mock.patch.object(ia, "disponivel", return_value=True),
                  mock.patch.object(ia, "responder", side_effect=lambda pedido, **_: resposta(pedido) if callable(resposta) else resposta)):
            p.start()
            self.addCleanup(p.stop)

    def sem_ia(self):
        p = mock.patch.object(ia, "disponivel", return_value=False)
        p.start()
        self.addCleanup(p.stop)


class TestBase(ComDados):
    def test_preparacao_vazia_e_gravada(self):
        self.assertEqual(en.carregar_preparacao("v1"), {"vaga_id": "v1", "texto_empresa": "", "rodadas": []})
        en.guardar_texto_empresa("v1", "  A Delta tem 40 lojas.  ")
        self.assertEqual(en.carregar_preparacao("v1")["texto_empresa"], "A Delta tem 40 lojas.")
        self.assertTrue((self.tmp / "entrevistas" / "vaga-v1.json").exists())
        en.guardar_texto_empresa("v1", "x" * 30000)
        self.assertEqual(len(en.carregar_preparacao("v1")["texto_empresa"]), en.TAM_TEXTO_EMPRESA)
        with self.assertRaises(en.EntrevistaErro):
            en.guardar_texto_empresa("nao-existe", "x")

    def test_id_saneado(self):
        self.assertEqual(en._arquivo_vaga("../x y").name, "vaga-.._x_y.json")
        self.assertEqual(en._arquivo_vaga("../x").parent, en.PASTA)

    def test_historias_salvar_atualizar_remover(self):
        h = en.salvar_historia({"titulo": "Relatório mais rápido", "situacao": "Fechamento lento", "acao": "Automatizei",
                                "resultado": "De 10 para 6 dias", "perguntas": ["Desafio difícil"]})
        self.assertTrue(h["id"].startswith("h"))
        self.assertEqual(len(en.listar_historias()), 1)
        en.salvar_historia({**h, "reflexao": "Medir antes de mudar"})
        hs = en.listar_historias()
        self.assertEqual((len(hs), hs[0]["reflexao"]), (1, "Medir antes de mudar"))
        en.remover_historia(h["id"])
        self.assertEqual(en.listar_historias(), [])
        with self.assertRaises(en.EntrevistaErro):
            en.remover_historia(h["id"])

    def test_historia_limites(self):
        with self.assertRaises(en.EntrevistaErro):
            en.salvar_historia({"titulo": "", "situacao": "x"})
        with self.assertRaises(en.EntrevistaErro):
            en.salvar_historia({"titulo": "Só título"})
        h = en.salvar_historia({"titulo": "t" * 500, "situacao": "s" * 5000})
        self.assertEqual((len(h["titulo"]), len(h["situacao"])), (en.TAM_TITULO, en.TAM_CAMPO))
        with mock.patch.object(en, "MAX_HISTORIAS", 1):
            with self.assertRaises(en.EntrevistaErro):
                en.salvar_historia({"titulo": "Outra", "acao": "x"})


class TestSemIA(ComDados):
    def test_dossie_e_perguntas(self):  # SC-001
        self.sem_ia()
        r = en.preparacao("v1")
        self.assertEqual(r["dossie"]["empresa"], "Empresa Delta")
        self.assertEqual(r["dossie"]["lacunas"], ["Tableau", "Certificação AWS"])
        self.assertIn("painéis", r["dossie"]["anotacao"])
        origens = {q["origem"] for q in r["perguntas"]}
        self.assertTrue({"requisito", "lacuna", "padrao"} <= origens)
        self.assertTrue(all(q["porque"] and q["texto_en"] for q in r["perguntas"]))
        textos = " ".join(q["texto"] for q in r["perguntas"])
        self.assertIn("SQL avançado", textos)
        self.assertNotIn("Vale-refeição", textos)  # benefício não é requisito
        self.assertEqual(len({en._chave(q["texto"]) for q in r["perguntas"]}), len(r["perguntas"]))

    def test_sem_ia_avisa(self):
        self.sem_ia()
        for fn in (lambda: en.resumo_ia("v1"), lambda: en.perguntas_ia("v1"), lambda: en.historias_ia("v1")):
            with self.assertRaises(en.EntrevistaErro):
                fn()


class TestDossieIA(ComDados):
    def test_origem_do_resumo(self):
        en.guardar_texto_empresa("v1", "A Delta abriu 40 lojas no Sul em 2025 e quer crescer no digital.")
        self.com_ia(json.dumps([
            {"ponto": "Empresa de varejo", "origem": "vaga", "trecho": "Somos uma empresa de varejo"},
            {"ponto": "Expansão no Sul", "origem": "texto", "trecho": "abriu 40 lojas no Sul"},
            {"ponto": "Vai pedir painéis", "origem": "vaga", "trecho": "fundada por astronautas em Marte"},
            {"ponto": "Time pequeno", "origem": "deducao", "trecho": ""}]))
        itens = en.resumo_ia("v1")["itens"]
        self.assertEqual([i["origem"] for i in itens], ["vaga", "texto", "deducao", "deducao"])
        self.assertEqual(itens[2]["trecho"], "")
        self.assertEqual(en.preparacao("v1")["dossie"]["resumo_ia"]["itens"][1]["ponto"], "Expansão no Sul")

    def test_perguntas_da_ia_somadas(self):
        self.com_ia(json.dumps([{"texto": "Por que esta vaga e esta empresa?", "tipo": "comportamental", "porque": "x"},
                                {"texto": "Como você modela dados de vendas?", "tipo": "tecnica", "porque": "SQL na vaga"}]))
        en.perguntas_ia("v1")
        qs = en.preparacao("v1")["perguntas"]
        ia_q = [q for q in qs if q["origem"] == "ia"]
        self.assertEqual(len(ia_q), 2)
        self.assertEqual(sum(1 for q in qs if q["texto"] == "Por que esta vaga e esta empresa?"), 1)

    def test_resposta_fora_do_formato(self):
        self.com_ia("não sei")
        with self.assertRaises(en.EntrevistaErro):
            en.resumo_ia("v1")


class TestHistorias(ComDados):
    RASCUNHOS = [
        {"titulo": "Fechamento mais rápido", "situacao": "O relatório mensal demorava", "tarefa": "Reduzir o prazo",
         "acao": "Automatizei o relatório mensal", "resultado": "O fechamento caiu de 10 para 6 dias",
         "reflexao": "Automatizar o repetitivo libera o time", "conquista": "Automatizei o relatório mensal",
         "perguntas": ["Conte sobre um desafio difícil"]},
        {"titulo": "Painéis", "situacao": "Vendas sem visão", "tarefa": "Dar visão", "acao": "Criei painéis em Power BI",
         "resultado": "As vendas subiram 45% na Empresa Ômega", "reflexao": "Ouvir o usuário", "conquista": "Painéis"}]

    def test_rascunhos_conferidos_e_nao_gravados(self):  # SC-002, SC-003
        self.com_ia("Aqui: " + json.dumps(self.RASCUNHOS))
        rs = en.historias_ia("v1")
        self.assertEqual(len(rs), 2)
        self.assertEqual(rs[0]["conferir"], [])
        self.assertTrue(any("45%" in p for p in rs[1]["conferir"]))
        self.assertTrue(any("Ômega" in p for p in rs[1]["conferir"]))
        self.assertEqual(en.listar_historias(), [])  # nada salvo sem confirmação
        en.salvar_historia(rs[0])
        self.assertEqual([h["titulo"] for h in en.preparacao("v2")["historias"]], ["Fechamento mais rápido"])

    def test_sem_perfil(self):
        self.com_ia("[]")
        with mock.patch.object(en, "perfil_texto", return_value=""):
            with self.assertRaises(en.EntrevistaErro):
                en.historias_ia("v1")


class TestSimulacao(ComDados):
    def test_retorno_conferido(self):  # SC-005
        pedidos = []

        def resposta(pedido):
            pedidos.append(pedido)
            return json.dumps({"funcionou": "Você citou a automação.", "faltou": "Faltou o resultado.",
                               "mais_forte": "Automatizei o relatório mensal e o fechamento caiu de 10 para 6 dias, "
                                             "economizando R$ 200 mil."})
        self.com_ia(resposta)
        r = en.registrar_resposta("v1", "Tell me about a challenge", "I automated a report.", "en")
        self.assertIn("inglês", pedidos[0])
        self.assertTrue(any("200" in p for p in r["retorno"]["conferir"]))
        self.assertFalse(any("10" in p.split(":")[-1] for p in r["retorno"]["conferir"]))
        sim = en.carregar_preparacao("v1")["simulacao"]
        self.assertEqual((sim["idioma"], len(sim["respostas"])), ("en", 1))
        self.assertEqual(en.resumo_simulacao(sim), ["Faltou o resultado."])

    def test_sem_ia_grava_so_a_resposta(self):
        self.sem_ia()
        r = en.registrar_resposta("v1", "Pergunta", "Minha resposta")
        self.assertIsNone(r["retorno"])
        self.assertEqual(en.carregar_preparacao("v1")["simulacao"]["respostas"][0]["resposta"], "Minha resposta")
        self.assertEqual(en.resumo_simulacao(r["simulacao"]), [])
        with self.assertRaises(en.EntrevistaErro):
            en.registrar_resposta("v1", "Pergunta", "  ")


class TestSalarioERodadas(ComDados):
    def test_salario_so_da_vaga_e_do_perfil(self):  # SC-004
        s = en.salario(VAGAS["v1"], PERFIL_SALARIO)
        self.assertEqual((s["faixa"], s["moeda"]), ("R$ 8.000 - R$ 10.000", "BRL"))
        self.assertIn("9.000", s["pretensao"])
        self.assertTrue(s["pontos"])
        vazio = en.salario(VAGAS["v2"], PERFIL)
        self.assertEqual((vazio["faixa"], vazio["pretensao"]), ("", ""))
        self.assertFalse(any(ch.isdigit() for ch in " ".join(vazio["pontos"])))

    def test_rodada_alimenta_as_perguntas(self):
        self.sem_ia()
        with self.assertRaises(en.EntrevistaErro):
            en.registrar_rodada("v1", {"etapa": "RH"})
        en.registrar_rodada("v1", {"data": "2026-10-10", "etapa": "RH", "perguntas": "- Qual a sua maior fraqueza?\n2) Onde se vê em 5 anos?",
                                   "bem": "Falei dos painéis", "mal": "Travei no inglês"})
        r = en.preparacao("v1")
        self.assertEqual(r["rodadas"][0]["perguntas"], ["Qual a sua maior fraqueza?", "Onde se vê em 5 anos?"])
        primeira = r["perguntas"][0]
        self.assertEqual((primeira["texto"], primeira["origem"]), ("Qual a sua maior fraqueza?", "rodada"))
        self.assertIn("10/10/2026", primeira["porque"])


class TestLinhaDeComando(ComDados):
    def test_preparar_e_historias(self):
        self.sem_ia()
        with mock.patch.object(banco, "procurar", return_value=[{"id": "v1"}]), mock.patch("sys.stdout") as saida:
            self.assertEqual(en.main(["preparar", "Delta"]), 0)
        texto = "".join(c.args[0] for c in saida.write.call_args_list)
        self.assertIn("Perguntas prováveis", texto)
        self.assertIn("R$ 8.000", texto)
        with mock.patch("sys.stdout"):
            self.assertEqual(en.main(["historias"]), 0)
        with mock.patch.object(banco, "procurar", return_value=[]), mock.patch("sys.stderr"):
            self.assertEqual(en.main(["preparar", "nada"]), 2)


if __name__ == "__main__":
    unittest.main()
