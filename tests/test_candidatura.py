"""Carta de apresentação e respostas de formulário (candidatura_ia.py e conferir.py), com perfil e vaga fictícios
e uma IA falsa: perguntas obrigatórias, conferência de fatos (SC-003) e perguntas sensíveis só com a pessoa (SC-002)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import candidatura_ia  # noqa: E402
import conferir  # noqa: E402
import curriculo_ia  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "kit"
PERFIL = (DADOS / "perfil-ficticio.md").read_text(encoding="utf-8")
VAGA = json.loads((DADOS / "vagas.json").read_text(encoding="utf-8"))["en"]
TEXTO_VAGA = curriculo_ia.texto_da_vaga(VAGA)
RESPOSTAS = {"por_que": "Quero trabalhar com relatórios de vendas num time remoto.",
             "problema": "Relatórios que demoram a fechar.", "primeiro_movimento": "Mapear os relatórios de vendas.",
             "tom": "direto"}
FILLER = "This is the kind of work I want to keep doing with a focused team that cares about clear numbers."


def carta(extra: str = "", empresa: bool = True, palavras: int = 380) -> str:
    inicio = [("Dear hiring team at Acme Analytics," if empresa else "Dear hiring team,"),
              "I am applying for the Senior Data Analyst role because sales reporting is what I do every day.",
              "At Empresa Alfa I automated the monthly report, cutting the close from 10 to 6 days.",
              "My Power BI dashboards are used by 1,500 people, and satisfaction rose 30%.",
              "I write advanced SQL for the sales team and I would bring that to your reporting.", extra]
    texto = " ".join(x for x in inicio if x)
    while conferir.contar_palavras(texto) + conferir.contar_palavras(FILLER) <= palavras:
        texto += " " + FILLER
    return texto


class TestConferirCarta(unittest.TestCase):
    def conf(self, texto, **k):
        return conferir.conferir_carta(texto, PERFIL, TEXTO_VAGA, k.get("empresa", "Acme Analytics"), RESPOSTAS)

    def test_carta_correta_passa(self):
        r = self.conf(carta())
        self.assertEqual(r["veredito"], "ok", r["pontos"])
        self.assertTrue(350 <= r["palavras"] <= 420)

    def test_fato_inventado_bloqueia(self):
        for extra in ("I grew revenue by 45% in one quarter.", "I managed a budget of US$ 2 million.", "I led 12 analysts."):
            r = self.conf(carta(extra))
            self.assertEqual(r["veredito"], "bloquear", extra)
            self.assertTrue(any(p["tipo"] == "numero" for p in r["pontos"]))
        self.assertEqual(self.conf(carta("Since 2015 I have worked with data."))["veredito"], "bloquear")  # data fora do perfil

    def test_generica_curta_e_nomes(self):
        r = self.conf(carta("I am passionate about data and a true team player.", empresa=False))
        tipos = {p["tipo"] for p in r["pontos"]}
        self.assertEqual(r["veredito"], "conferir")
        self.assertTrue({"vazia", "empresa_da_vaga"} <= tipos)
        self.assertIn("tamanho", {p["tipo"] for p in self.conf(carta(palavras=120))["pontos"]})
        r = self.conf(carta("Before that I worked at Globex Corporation."))
        self.assertIn("Globex Corporation", [p["valor"] for p in r["pontos"] if p["tipo"] == "nome"])
        sem_requisito = "Dear hiring team at Acme Analytics, " + " ".join([FILLER] * 22)
        self.assertIn("requisito", {p["tipo"] for p in self.conf(sem_requisito)["pontos"]})

    def test_linha_de_comando(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "carta.txt").write_text(carta("I grew revenue by 45%."), encoding="utf-8")
        (tmp / "perfil.md").write_text(PERFIL, encoding="utf-8")
        (tmp / "vaga.txt").write_text(TEXTO_VAGA, encoding="utf-8")
        with mock.patch("sys.stdout"):
            codigo = conferir.main(["--carta", str(tmp / "carta.txt"), "--perfil", str(tmp / "perfil.md"),
                                    "--vaga", str(tmp / "vaga.txt"), "--empresa", "Acme Analytics"])
        self.assertEqual(codigo, 3)


class ComPasta(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pedidos = []
        for p in (mock.patch.object(curriculo_ia, "CURRICULOS", self.tmp),
                  mock.patch.object(candidatura_ia, "_marca_ia", return_value={"provedor": "teste", "modelo": "x"})):
            p.start()
            self.addCleanup(p.stop)

    def ia(self, resposta):
        def responder(pedido):
            self.pedidos.append(pedido)
            return resposta
        return mock.patch.object(candidatura_ia, "_ia_responder", side_effect=responder)


class TestCarta(ComPasta):
    def test_respostas_obrigatorias(self):
        for falta in ("por_que", "problema", "primeiro_movimento", "tom"):
            with self.assertRaisesRegex(candidatura_ia.GeracaoErro, candidatura_ia.PERGUNTAS_CARTA[falta].rstrip("?")):
                candidatura_ia.validar_respostas({**RESPOSTAS, falta: " "})
        with self.assertRaises(candidatura_ia.GeracaoErro):
            candidatura_ia.validar_respostas({**RESPOSTAS, "tom": "engraçado"})

    def test_mensagem_curta(self):
        r = candidatura_ia.validar_respostas({"formato": "mensagem", "por_que": "Quero relatórios de vendas.", "tom": "direto",
                                              "idioma": "pt"})
        self.assertEqual((r["formato"], r["limite"], r["idioma"]), ("mensagem", 400, "pt"))  # só por que e tom são obrigatórias
        for ruim in ({"limite": 10}, {"limite": "x"}, {"idioma": "jp"}, {"por_que": ""}):
            with self.assertRaises(candidatura_ia.GeracaoErro, msg=ruim):
                candidatura_ia.validar_respostas({"formato": "mensagem", "por_que": "Quero.", "tom": "direto", **ruim})
        curta = ("Acme Analytics: I write advanced SQL for the sales team and my Power BI dashboards are used by 1,500 "
                 "people. Sales reporting is what I do every day at Empresa Alfa.")
        with self.ia(json.dumps({"texto": curta})):
            meta = candidatura_ia.gerar_carta(VAGA, {"formato": "mensagem", "por_que": "Relatórios de vendas.", "tom": "direto",
                                                     "limite": 400, "idioma": "en"}, perfil=PERFIL)
        self.assertEqual((meta["formato"], meta["conferencia"]["veredito"], meta["arquivos"]["docx"]), ("mensagem", "ok", None))
        self.assertTrue(meta["nome"].endswith("-mensagem"))
        self.assertIn("No máximo 400 caracteres", self.pedidos[-1])
        self.assertNotIn("primeiro movimento no cargo:", self.pedidos[-1])
        longa = conferir.conferir_carta(curta * 3, PERFIL, TEXTO_VAGA, "Acme Analytics", {}, limite=400)
        self.assertEqual(longa["veredito"], "bloquear")  # passa do limite: o campo não aceita
        self.assertIn("limite é 400", longa["pontos"][-1]["mensagem"] if longa["pontos"][-1]["tipo"] == "tamanho"
                      else " ".join(p["mensagem"] for p in longa["pontos"]))

    def test_gera_e_grava(self):
        with self.ia(json.dumps({"texto": carta()})):
            meta = candidatura_ia.gerar_carta(VAGA, RESPOSTAS, perfil=PERFIL)
        self.assertEqual((meta["conferencia"]["veredito"], meta["pronto"], meta["idioma"]), ("ok", True, "en"))
        self.assertTrue((self.tmp / f"{meta['nome']}.txt").exists() and (self.tmp / f"{meta['nome']}.docx").exists())
        self.assertTrue(meta["nome"].endswith("-acme-analytics-senior-data-analyst-carta"))
        self.assertIn("Relatórios que demoram a fechar.", self.pedidos[0])  # as respostas vão no pedido
        self.assertIn("inglês", self.pedidos[0])
        with self.ia(json.dumps({"texto": carta("I grew revenue by 45%.")})):
            ruim = candidatura_ia.gerar_carta(VAGA, RESPOSTAS, perfil=PERFIL)
        self.assertEqual((ruim["conferencia"]["veredito"], ruim["pronto"]), ("bloquear", False))
        self.assertNotEqual(ruim["nome"], meta["nome"])  # a anterior continua salva
        self.assertEqual([m["nome"] for m in candidatura_ia.listar(VAGA["id"])], [ruim["nome"], meta["nome"]])
        with self.ia("não sei escrever"), self.assertRaises(candidatura_ia.GeracaoErro):
            candidatura_ia.gerar_carta(VAGA, RESPOSTAS, perfil=PERFIL)
        with self.assertRaisesRegex(candidatura_ia.GeracaoErro, "perfil"):
            candidatura_ia.gerar_carta(VAGA, RESPOSTAS, perfil="")


SENSIVEIS = [
    "Are you legally authorized to work in the United States?", "Will you now or in the future require visa sponsorship?",
    "What are your salary expectations?", "Expected compensation (USD)", "Qual a sua pretensão salarial?",
    "Você é pessoa com deficiência (PCD)?", "Do you have a disability?", "Are you willing to relocate to Austin?",
    "Você tem disponibilidade para mudança de cidade?", "What is your gender?", "Are you a protected veteran?",
    "Você possui autorização de trabalho na Europa?", "What is your citizenship?", "What is your hourly rate?",
]
COMUNS = ["Why do you want to work at Acme Analytics?", "Describe a report you automated.", "Qual a sua experiência com SQL?",
          "Link to your portfolio", "How many years of experience do you have with Power BI?"]


class TestRespostas(ComPasta):
    def test_sensiveis_reconhecidas(self):
        self.assertEqual([p for p in SENSIVEIS if not candidatura_ia.sensivel(p)], [])
        self.assertEqual([p for p in COMUNS if candidatura_ia.sensivel(p)], [])
        self.assertEqual(candidatura_ia.separar("1. Primeira?\n2) Segunda?\n\n- Terceira?"), ["Primeira?", "Segunda?", "Terceira?"])

    def test_sensiveis_ficam_com_a_pessoa(self):
        perguntas = "\n".join(["1. Why do you want to work at Acme Analytics?", "2. Are you authorized to work in the US?",
                               "3. Describe a report you automated.", "4. What are your salary expectations?",
                               "5. Tell us about a team you led."])
        ia = [{"indice": i, "resposta": r} for i, r in ((1, "Sales reporting is my daily work."), (2, "Yes, I am authorized."),
                                                         (3, "I cut the monthly close from 10 to 6 days."),
                                                         (4, "US$ 120,000 per year."), (5, "I led 12 analysts."))]
        with self.ia(json.dumps(ia)):
            meta = candidatura_ia.gerar_respostas(VAGA, perguntas, perfil=PERFIL)
        itens = meta["itens"]
        self.assertEqual([bool(i["sensivel"]) for i in itens], [False, True, False, True, False])
        self.assertEqual([itens[1]["resposta"], itens[3]["resposta"]], ["", ""])  # a IA tentou; foi descartado (SC-002)
        self.assertNotIn("Are you authorized", self.pedidos[0])  # as sensíveis nem vão à IA
        self.assertEqual(itens[2]["conferir"], [])
        self.assertTrue(itens[4]["conferir"])  # 12 não está no perfil
        texto = (self.tmp / f"{meta['nome']}.txt").read_text(encoding="utf-8")
        self.assertIn("(responda você: autorização de trabalho)", texto)
        dela = candidatura_ia.gravar_da_pessoa(meta["nome"], {"2": "Preciso de patrocínio de visto.", "4": "A combinar."})
        self.assertEqual([dela["itens"][1]["resposta"], dela["itens"][3]["resposta"]], ["Preciso de patrocínio de visto.", "A combinar."])
        self.assertTrue(dela["itens"][1]["da_pessoa"])
        with self.assertRaises(candidatura_ia.GeracaoErro):
            candidatura_ia.gravar_da_pessoa(meta["nome"], {"9": "x"})
        # só perguntas sensíveis: nenhuma chamada à IA
        self.pedidos.clear()
        with self.ia("[]"):
            candidatura_ia.gerar_respostas(VAGA, "What are your salary expectations?", perfil=PERFIL)
        self.assertEqual(self.pedidos, [])


if __name__ == "__main__":
    unittest.main()
