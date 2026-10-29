"""Carta de apresentação e respostas de formulário (candidatura_ia.py e conferir.py), com perfil e vaga fictícios
e uma IA falsa: perguntas da carta opcionais e guardadas como relato (spec 035), pedido que vende a pessoa no
primeiro parágrafo, conferência de fatos (SC-003) e perguntas sensíveis só com a pessoa (SC-002)."""
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
import candidatura_ia  # noqa: E402
import conferir  # noqa: E402
import curriculo  # noqa: E402
import curriculo_ia  # noqa: E402
import relatos  # noqa: E402

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
        with mock.patch("sys.stdout"), mock.patch.object(banco, "ARQUIVO", tmp / "banco.db"):  # sem os relatos reais
            codigo = conferir.main(["--carta", str(tmp / "carta.txt"), "--perfil", str(tmp / "perfil.md"),
                                    "--vaga", str(tmp / "vaga.txt"), "--empresa", "Acme Analytics"])
        self.assertEqual(codigo, 3)


def pdf_falso(docx):
    """O PDF sem LibreOffice nem Word: o teste nunca abre programa nenhum."""
    pdf = docx.with_suffix(".pdf")
    pdf.write_bytes(b"%PDF-1.4 teste")
    return pdf, ""


class ComPasta(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pedidos = []
        for p in (mock.patch.object(curriculo_ia, "CURRICULOS", self.tmp),
                  mock.patch.object(curriculo, "para_pdf", side_effect=pdf_falso),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "dados" / "banco.db"),  # os relatos ficam aqui
                  mock.patch.object(candidatura_ia, "_marca_ia", return_value={"provedor": "teste", "modelo": "x"})):
            p.start()
            self.addCleanup(p.stop)

    def ia(self, resposta):
        def responder(pedido):
            self.pedidos.append(pedido)
            return resposta
        return mock.patch.object(candidatura_ia, "_ia_responder", side_effect=responder)


class TestCarta(ComPasta):
    def test_respostas_opcionais(self):  # spec 035: a que ficar em branco a IA responde pelo perfil
        r = candidatura_ia.validar_respostas({})
        self.assertEqual((r["formato"], r["tom"], r["por_que"], r["guardar_relatos"]), ("carta", "direto", "", True))
        self.assertFalse(candidatura_ia.validar_respostas({"guardar_relatos": False})["guardar_relatos"])
        with self.assertRaises(candidatura_ia.GeracaoErro):
            candidatura_ia.validar_respostas({**RESPOSTAS, "tom": "engraçado"})

    def test_pedido_vende_no_primeiro_paragrafo(self):
        sem = candidatura_ia.montar_pedido_carta(PERFIL, VAGA, candidatura_ia.validar_respostas({}))
        self.assertIn("Primeiro parágrafo, até 60 palavras", sem)
        self.assertIn("problema", sem)
        self.assertIn("ATS", sem)
        self.assertIn("Ela não respondeu a: Por que esta vaga?", sem)
        self.assertIn("(nenhuma: responda você, pelo perfil e pela vaga)", sem)
        com = candidatura_ia.montar_pedido_carta(PERFIL, VAGA, candidatura_ia.validar_respostas(RESPOSTAS))
        self.assertNotIn("Ela não respondeu", com)
        self.assertIn("Relatórios que demoram a fechar.", com)

    def test_respostas_viram_relatos(self):
        with self.ia(json.dumps({"texto": carta()})):
            meta = candidatura_ia.gerar_carta(VAGA, {**RESPOSTAS, "primeiro_movimento": ""}, perfil=PERFIL)
        self.assertEqual(meta["relatos"], 2)
        guardados = {x["relato"] for x in relatos.listar()}
        self.assertEqual(guardados, {RESPOSTAS["por_que"], RESPOSTAS["problema"]})
        self.assertTrue(all("Acme Analytics" in x["pergunta"] for x in relatos.listar()))
        with self.ia(json.dumps({"texto": carta()})):
            meta = candidatura_ia.gerar_carta(VAGA, {"tom": "direto", "problema": "Outro fato.", "guardar_relatos": False},
                                              perfil=PERFIL)
        self.assertEqual((meta["relatos"], len(relatos.listar())), (0, 2))

    def test_mensagem_curta(self):
        r = candidatura_ia.validar_respostas({"formato": "mensagem", "por_que": "Quero relatórios de vendas.", "tom": "direto",
                                              "idioma": "pt"})
        self.assertEqual((r["formato"], r["limite"], r["idioma"]), ("mensagem", 400, "pt"))  # só por que e tom são obrigatórias
        for ruim in ({"limite": 10}, {"limite": "x"}, {"idioma": "jp"}, {"tom": "engraçado"}):
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
        self.assertEqual(meta["arquivos"]["pdf"], f"{meta['nome']}.pdf")  # a carta também sai em PDF (spec 035)
        self.assertTrue((self.tmp / f"{meta['nome']}.pdf").exists())
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

    def test_pedido_traz_palavras_chave_que_o_perfil_sustenta(self):  # ATS (spec 035)
        pedido = candidatura_ia.montar_pedido_carta(PERFIL, VAGA, candidatura_ia.validar_respostas({}))
        chave = pedido[pedido.index("## Palavras-chave"):pedido.index("## Requisitos que a ferramenta")]
        self.assertIn("Advanced SQL", chave)
        self.assertIn("Fluent English", chave)  # "Inglês" no perfil: a mesma coisa em outro idioma
        self.assertNotIn("Eastern Time", chave)  # "time" (inglês) não é "time" (equipe) do perfil
        self.assertIn("o termo exato do anúncio", pedido)
        conf = conferir.conferir_carta("Dear Acme Analytics team, I write reports.", PERFIL, TEXTO_VAGA, "Acme Analytics", {})
        self.assertEqual(conf["palavras_chave"]["citadas"], 0)
        self.assertIn("palavras_chave", {p["tipo"] for p in conf["pontos"]})

    def test_verificar_incorpora_a_edicao(self):  # o botão Verificar (spec 035)
        with self.ia(json.dumps({"texto": carta()})):
            meta = candidatura_ia.gerar_carta(VAGA, RESPOSTAS, perfil=PERFIL)
        acrescimo = "In 2024 I led the migration of 40 reports to the cloud."
        editado = meta["texto"] + "\n\n" + acrescimo
        revisado = carta(acrescimo)
        with self.ia(json.dumps({"texto": revisado, "mudancas": ["corrigi a concordância no segundo parágrafo"]})):
            nova = candidatura_ia.verificar_carta(meta["nome"], editado, perfil=PERFIL)
        pedido = self.pedidos[-1]
        self.assertIn("## O que a pessoa escreveu ou mudou (manter)", pedido)
        self.assertIn(acrescimo, pedido)
        self.assertIn("Corrija gramática", pedido)
        self.assertEqual((nova["origem"], nova["base"], nova["mudancas"]),
                         ("verificada", meta["nome"], ["corrigi a concordância no segundo parágrafo"]))
        self.assertNotEqual(nova["nome"], meta["nome"])  # versão nova; a anterior continua
        self.assertEqual({m["nome"] for m in candidatura_ia.listar(VAGA["id"])}, {meta["nome"], nova["nome"]})
        self.assertNotEqual(nova["conferencia"]["veredito"], "bloquear")  # o 2024 e o 40 são da pessoa
        self.assertEqual(nova["relatos"], 1)
        self.assertTrue(any("led the migration of 40 reports" in x["relato"] for x in relatos.listar()))
        with self.ia(json.dumps({"texto": revisado})):
            sem = candidatura_ia.verificar_carta(meta["nome"], editado + " More.", guardar_relatos=False, perfil=PERFIL)
        self.assertEqual(sem["relatos"], 0)
        with self.assertRaisesRegex(candidatura_ia.GeracaoErro, "vazio"):
            candidatura_ia.verificar_carta(meta["nome"], "  ", perfil=PERFIL)

    def test_pdf_que_falha_e_gerar_depois(self):
        with self.ia(json.dumps({"texto": carta()})), \
                mock.patch.object(curriculo, "para_pdf", return_value=(None, "instale o LibreOffice para gerar o PDF")):
            meta = candidatura_ia.gerar_carta(VAGA, RESPOSTAS, perfil=PERFIL)
        self.assertEqual((meta["arquivos"]["pdf"], meta["aviso_pdf"]), (None, "instale o LibreOffice para gerar o PDF"))
        with mock.patch.object(curriculo, "para_pdf", return_value=(None, "instale o LibreOffice para gerar o PDF")), \
                self.assertRaisesRegex(candidatura_ia.GeracaoErro, "LibreOffice"):
            candidatura_ia.pdf_da_carta(meta["nome"])
        (self.tmp / f"{meta['nome']}.docx").unlink()  # o .docx some: refeito a partir do texto
        nova = candidatura_ia.pdf_da_carta(meta["nome"])
        self.assertEqual((nova["arquivos"]["pdf"], nova["disponivel"]["pdf"], "aviso_pdf" in nova),
                         (f"{meta['nome']}.pdf", True, False))
        self.assertEqual(candidatura_ia.listar(VAGA["id"])[0]["arquivos"]["pdf"], f"{meta['nome']}.pdf")
        with self.ia(json.dumps({"texto": "Acme Analytics: SQL and Power BI for your sales reports."})):
            msg = candidatura_ia.gerar_carta(VAGA, {"formato": "mensagem", "limite": 400}, perfil=PERFIL)
        self.assertIsNone(msg["arquivos"]["pdf"])  # a mensagem curta é para copiar e colar
        with self.assertRaisesRegex(candidatura_ia.GeracaoErro, "mensagem"):
            candidatura_ia.pdf_da_carta(msg["nome"])

    def test_acrescimos(self):
        self.assertEqual(candidatura_ia.acrescimos("Eu fiz A. Eu fiz B.", "Eu fiz A. Eu fiz C. Eu fiz B."), ["Eu fiz C."])


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
