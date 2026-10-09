"""Kit de candidatura (dash/kit.py e dash/banco.py): campos da análise sobre a candidatura, checklist "o que esta
candidatura pede" e lembretes de follow-up, com vagas fictícias e uma IA falsa."""
import json
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import analise  # noqa: E402
import banco  # noqa: E402
import filtros  # noqa: E402
import kit  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "kit"
VAGAS = json.loads((DADOS / "vagas.json").read_text(encoding="utf-8"))
HOJE = date(2026, 10, 9)
# o que uma IA responderia para a vaga em inglês (com campos fora das opções, que caem)
RESPOSTA = [{
    "id": "kit-en-1", "aderencia": 78, "resumo": "Analista sênior de relatórios de vendas.", "encaixe": ["SQL"],
    "lacunas": [], "alertas": [], "modelo_trabalho": "hibrido", "senioridade": ["senior"], "senioridade_origem": "declarada",
    "autorizacao": {"valor": "patrocina", "frase": "We sponsor visas for candidates who later relocate."},
    "contratacao": [{"valor": "contractor", "frase": "This is a B2B contractor engagement paid in USD."},
                    {"valor": "talvez", "frase": "x"}],
    "ingles": {"nivel": "fluente", "frase": "Fluent English"},
    "fuso": {"texto": "4 h em comum com o horário de Nova York", "frase": "At least 4 hours of overlap with US Eastern Time"},
    "sistema_candidatura": "Greenhouse",
    "pede": [{"item": "carta", "frase": "Please send a cover letter"}, {"item": "portfolio", "frase": "a link to your portfolio"},
             {"item": "teste", "frase": "complete a take-home exercise"}],
    "riscos": [{"tipo": "remoto_hibrido", "frase": "you will join the team in our Austin office 2 days a week"}],
}]


class TestValidar(unittest.TestCase):
    def test_campos_da_candidatura(self):
        a = banco.validar_analise(RESPOSTA[0])
        self.assertEqual(a["autorizacao"]["valor"], "patrocina")
        self.assertEqual([c["valor"] for c in a["contratacao"]], ["contractor"])  # "talvez" cai
        self.assertEqual(a["ingles"], {"nivel": "fluente", "frase": "Fluent English"})
        self.assertEqual([p["item"] for p in a["pede"]], ["carta", "portfolio", "teste"])
        self.assertEqual(a["riscos"][0]["tipo"], "remoto_hibrido")
        self.assertEqual(a["sistema_candidatura"], "Greenhouse")
        ruim = banco.validar_analise({"aderencia": 50, "autorizacao": {"valor": "quem sabe"}, "ingles": "fluente",
                                      "pede": "carta", "fuso": {"texto": " "}, "riscos": [{"tipo": "x"}]})
        for campo in ("autorizacao", "ingles", "pede", "fuso", "riscos", "contratacao"):
            self.assertNotIn(campo, ruim)  # fora das opções: o campo cai, a análise segue
        longa = banco.validar_analise({"aderencia": 50, "autorizacao": {"valor": "omisso", "frase": "x" * 500}})
        self.assertEqual(len(longa["autorizacao"]["frase"]), kit.TAMANHO_FRASE)

    def test_estado_da_pessoa(self):
        k = kit.validar_kit({"estados": {"carta": "pronto"}, "extras": ["Referências", "referências", " "], "removidos": ["video"]})
        self.assertEqual(k, {"estados": {"carta": "pronto"}, "extras": ["Referências"], "removidos": ["video"]})
        with self.assertRaises(ValueError):
            kit.validar_kit({"estados": {"carta": "talvez"}})
        with self.assertRaises(ValueError):
            kit.validar_kit({"extras": [f"item {i}" for i in range(11)]})
        lem = kit.validar_lembretes({"base": "aplicada:2026-10-01", "follow1": "feito", "parar": 0})
        self.assertEqual(lem, {"base": "aplicada:2026-10-01", "parar": False, "follow1": "feito"})
        for ruim in ({"base": "salva:2026-10-01"}, {"base": "aplicada:2026-10-01", "follow2": "talvez"}):
            with self.assertRaises(ValueError):
                kit.validar_lembretes(ruim)
        campos = banco._validar_usuario({"kit": {"estados": {}}, "entrevista_em": "2026-10-10"})
        self.assertEqual(campos["entrevista_em"], "2026-10-10")
        with self.assertRaises(ValueError):
            banco._validar_usuario({"aderencia": 99})


class TestAnaliseComIA(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json")):
            p.start()
            self.addCleanup(p.stop)
        banco.inserir_vagas([{**VAGAS["en"], "analise_status": "pendente", "origem": "link"}])

    def test_idioma_no_adicionar_vaga(self):
        doc = banco.criar_manual({"titulo": "Data Analyst", "empresa": "Beta", "etapa": "salva", "descricao": VAGAS["en"]["descricao"]})
        self.assertEqual(doc["idioma"], "en")
        self.assertEqual(banco.com_kit(doc)["checklist"][0]["rotulo"], "Currículo em inglês")

    def test_pedido_e_gravacao(self):
        pedidos = []
        falsa = SimpleNamespace(disponivel=lambda: True, escolha_efetiva=lambda: {"provedor": "openai_compat"},
                                modelo_efetivo=lambda e: "teste", IAErro=RuntimeError,
                                responder=lambda texto, **k: pedidos.append(texto) or json.dumps(RESPOSTA))
        with mock.patch.object(analise, "_ia", return_value=falsa):
            ok, problemas = analise.analisar([banco.obter("kit-en-1")])
        self.assertEqual((ok, problemas), (["kit-en-1"], []))
        self.assertIn('"autorizacao" {"valor", "frase"}', pedidos[0])
        self.assertIn("`nao_precisa` (o anúncio aceita quem está num país", pedidos[0])  # a regra vem da skill
        v = banco.com_kit(banco.obter("kit-en-1"))
        self.assertEqual(v["autorizacao"]["frase"], "We sponsor visas for candidates who later relocate.")
        self.assertEqual([i["item"] for i in v["checklist"]], ["curriculo", "carta", "portfolio", "teste", "candidatura"])


class TestChecklist(unittest.TestCase):
    def test_sem_analise_pelas_palavras(self):
        itens = {i["item"]: i for i in kit.checklist(VAGAS["en"])}
        self.assertEqual(list(itens), ["curriculo", "carta", "portfolio", "teste", "candidatura"])
        self.assertEqual(itens["curriculo"]["rotulo"], "Currículo em inglês")  # vaga em inglês
        self.assertEqual(itens["carta"]["origem"], "anuncio")
        self.assertIn("cover letter", itens["carta"]["frase"])
        self.assertEqual((itens["carta"]["acao"], itens["candidatura"]["acao"]), ("carta", "candidatar"))
        pt = [i["item"] for i in kit.checklist(VAGAS["pt"])]
        self.assertEqual(pt, ["curriculo", "teste", "candidatura"])
        self.assertEqual(kit.checklist({"descricao": ""})[0]["rotulo"], "Currículo")

    def test_item_conhecido_pelo_nome(self):
        v = {**VAGAS["pt"], "kit": {"estados": {}, "extras": ["Cover letter", "Referências"], "removidos": []}}
        itens = {i["item"]: i for i in kit.checklist(v)}
        self.assertEqual((itens["carta"]["acao"], itens["carta"]["origem"], itens["carta"]["extra"]), ("carta", "pessoa", "Cover letter"))
        self.assertEqual(itens["carta"]["rotulo"], "Carta de apresentação")
        self.assertNotIn("acao", {k: x for k, x in itens["x:referencias"].items() if x})  # item só da pessoa, sem botão
        en = {i["item"]: i for i in kit.checklist({**VAGAS["en"], "kit": {"extras": ["carta"]}})}
        self.assertEqual(en["carta"]["origem"], "anuncio")  # já pedido pelo anúncio: fica o do anúncio
        self.assertNotIn("extra", en["carta"])

    def test_estado_preservado_com_analise_refeita(self):
        v = {**VAGAS["pt"], "kit": {"estados": {"teste": "pronto", "curriculo": "nao_se_aplica"},
                                    "extras": ["Carta de referência"], "removidos": ["candidatura"]}}
        antes = {i["item"]: i["estado"] for i in kit.checklist(v)}
        v.update(banco.validar_analise({"aderencia": 70, "pede": [{"item": "video", "frase": "grave um vídeo"}]}))
        depois = {i["item"]: i["estado"] for i in kit.checklist(v)}
        self.assertEqual({k: depois[k] for k in antes}, antes)  # SC-006
        self.assertEqual(depois["video"], "a_fazer")  # o item novo entra
        self.assertIn("x:carta-de-referencia", depois)
        self.assertNotIn("candidatura", depois)


class TestLembretes(unittest.TestCase):
    def vaga(self, dias, etapa="aplicada", **mais):
        return {"etapa": etapa, "etapa_em": (HOJE - timedelta(days=dias)).isoformat(), **mais}

    def tipos(self, v):
        return [x["tipo"] for x in kit.lembretes(v, HOJE)]

    def test_follow_up(self):
        self.assertEqual(self.tipos(self.vaga(6)), [])
        self.assertEqual(self.tipos(self.vaga(7)), ["follow1"])
        self.assertEqual(self.tipos(self.vaga(15)), ["follow2"])  # o 2º substitui o 1º
        base = f"aplicada:{(HOJE - timedelta(days=8)).isoformat()}"
        self.assertEqual(self.tipos(self.vaga(8, lembretes={"base": base, "follow1": "feito"})), [])
        base22 = f"aplicada:{(HOJE - timedelta(days=22)).isoformat()}"
        self.assertEqual(self.tipos(self.vaga(22, lembretes={"base": base22, "follow2": "dispensado"})), [])  # nunca um 3º
        self.assertEqual(self.tipos(self.vaga(22, lembretes={"base": base22, "parar": True})), [])
        # a vaga voltou para Aplicação Enviada em outra data: o que foi marcado antes não vale
        self.assertEqual(self.tipos(self.vaga(8, lembretes={"base": "aplicada:2026-01-01", "follow1": "feito"})), ["follow1"])
        self.assertEqual(self.tipos(self.vaga(30, etapa="salva")), [])

    def test_agradecimento(self):
        ontem = (HOJE - timedelta(days=1)).isoformat()
        self.assertEqual(self.tipos(self.vaga(5, "entrevista", entrevista_em=ontem)), ["agradecimento"])
        self.assertEqual(self.tipos(self.vaga(5, "entrevista", entrevista_em=HOJE.isoformat())), [])
        self.assertEqual(self.tipos(self.vaga(1, "entrevista")), ["agradecimento"])  # sem data: o dia em que entrou na etapa
        self.assertEqual(kit.lembretes(self.vaga(1, "entrevista"), HOJE)[0]["base"],
                         f"entrevista:{(HOJE - timedelta(days=1)).isoformat()}")


if __name__ == "__main__":
    unittest.main()
