"""Revisão do perfil ao levar relatos (spec 050), sem rede e sem IA de verdade: a IA propõe onde cada relato entra no
perfil, a ferramenta confere sem IA (linha e lugar que existem, número, data ou nome fora das fontes, afirmação de
falta, assunto sensível), a pessoa decide item a item e nas discordâncias, e só então o perfil.md muda. Conteúdo
fictício."""
import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import banco  # noqa: E402
import gerador  # noqa: E402
import ia  # noqa: E402
import relatos  # noqa: E402
import reprovacao as rep  # noqa: E402
import revisao_perfil as rv  # noqa: E402
from test_reprovacao import ANALISE, Base  # noqa: E402

CARGO_ALFA = "Analista de Dados — Empresa Alfa (01/2024–atual)"
CARGO_BETA = "Assistente de BI — Empresa Beta (03/2021–12/2023)"
RELATO_CTE = "Fazia consultas com CTEs para as metas comerciais da Empresa Alfa."
RELATO_TAB = "Usei Tableau por dois anos na Empresa Alfa para os painéis da diretoria."
PERFIL_REV = f"""# Meu perfil de carreira

## Objetivo
- Cargos que procuro: Analista de Dados

## Resumo
Analista de dados com foco em vendas.

## Experiência

### {CARGO_ALFA}
- Consultas em SQL para a área comercial.
- Painéis mensais para a diretoria.

### {CARGO_BETA}
- Relatórios em Excel.

## Formação
- Tecnologia em Análise de Dados — Faculdade Gama (2020)

## Habilidades e ferramentas (com nível)
- SQL — avançado

## Idiomas
- Inglês — B2 (Intermediário superior)

## Relatos

Fatos que você contou na candidatura assistida.

- Você já usou Tableau? — {RELATO_TAB} (2026-11-01)
"""


def proposta(id_cte, id_tab):
    return {
        "itens": [
            {"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA,
             "novo": "Consultas em SQL com CTEs para as metas comerciais.", "relatos": [id_cte]},
            {"tipo": "muda", "secao": "Habilidades", "cargo": None, "atual": "- SQL — avançado",
             "novo": "- SQL — avançado (CTEs e janelas)", "relatos": [id_cte]},
            {"tipo": "entra", "secao": "Experiência", "cargo": "Analista de Dados — Empresa Alfa",
             "novo": "Painéis em Tableau por dois anos para a diretoria.", "relatos": [id_tab]},
            {"tipo": "entra", "secao": "Certificações", "novo": "Tableau Desktop Specialist (2022)", "relatos": [id_tab]},
            {"tipo": "muda", "secao": "Experiência", "cargo": CARGO_ALFA, "atual": "- Linha que não existe no perfil.",
             "novo": "- Outra linha.", "relatos": []},
            {"tipo": "entra", "secao": "Experiência", "cargo": "Gerente — Empresa Zeta", "novo": "Liderou o time de dados.",
             "relatos": [id_cte]},
            {"tipo": "entra", "secao": "Trabalho no exterior", "novo": "Aceita morar fora.", "relatos": []},
            {"tipo": "entra", "secao": "Resumo", "novo": "A pessoa não tem experiência com Python.", "relatos": []},
            {"tipo": "entra", "secao": "Habilidades", "novo": "Pretensão salarial de 10 mil.", "relatos": []},
        ],
        "discordancias": [
            {"assunto": "Tempo com Tableau", "trecho_relato": "Usei Tableau por dois anos",
             "trecho_perfil": "Painéis mensais para a diretoria.", "relatos": [id_tab],
             "opcao_relato": {"tipo": "muda", "secao": "Experiência", "cargo": CARGO_ALFA,
                              "atual": "- Painéis mensais para a diretoria.",
                              "novo": "- Painéis mensais em Tableau para a diretoria, por dois anos.", "relatos": [id_tab]}},
        ],
        "sem_fato": [],
    }


class BaseRevisao(Base):
    def setUp(self):
        super().setUp()
        self.perfil.write_text(PERFIL_REV, encoding="utf-8")
        self.cte = relatos.adicionar("Que consultas SQL você fazia?", RELATO_CTE)
        self.tab = relatos.adicionar("Você já usou Tableau?", RELATO_TAB)
        relatos.marcar_no_perfil([self.tab["id"]])  # já colado cru na seção Relatos (spec 035)

    def revisar(self, resposta=None, ids=None):
        self.respostas_ia.append(resposta if resposta is not None else proposta(self.cte["id"], self.tab["id"]))
        return rv.revisar("relatos", ids or [self.cte["id"], self.tab["id"]])

    @staticmethod
    def item(r, tipo, trecho):
        return next(i for i in r["itens"] if i["tipo"] == tipo and (trecho in (i.get("novo") or "") or trecho in (i.get("atual") or "")))

    def texto(self):
        return self.perfil.read_text(encoding="utf-8")


class TestEstruturaEAplicar(unittest.TestCase):  # T003, T006
    def test_estrutura(self):
        est = rv.estrutura(PERFIL_REV)
        secoes = [(l["secao"], l["permitida"]) for l in est if l["nivel"] == 2]
        self.assertEqual(secoes, [("Objetivo", False), ("Resumo", True), ("Experiência", True), ("Formação", True),
                                  ("Habilidades", True), ("Idiomas", True), ("Relatos", False)])
        cargos = [l for l in est if l["cargo"]]
        self.assertEqual([c["cargo"] for c in cargos], [CARGO_ALFA, CARGO_BETA])
        self.assertEqual(cargos[0]["fim"], cargos[1]["inicio"])
        self.assertEqual(rv.lugar_existe(est, "Habilidades")["titulo"], "Habilidades e ferramentas (com nível)")
        self.assertEqual(rv.lugar_existe(est, "Experiência", "Analista de Dados — Empresa Alfa")["cargo"], CARGO_ALFA)
        self.assertIsNone(rv.lugar_existe(est, "Experiência", "Gerente — Empresa Zeta"))
        self.assertIsNone(rv.lugar_existe(est, "Certificações"))

    def test_linha_no_perfil(self):
        est = rv.estrutura(PERFIL_REV)
        linhas = PERFIL_REV.split("\n")
        i = rv.linha_no_perfil(PERFIL_REV, "SQL — avançado")
        self.assertEqual(linhas[i], "- SQL — avançado")
        alfa = rv.lugar_existe(est, "Experiência", CARGO_ALFA)
        self.assertEqual(linhas[rv.linha_no_perfil(PERFIL_REV, "- Painéis mensais para a diretoria.", alfa)],
                         "- Painéis mensais para a diretoria.")
        beta = rv.lugar_existe(est, "Experiência", CARGO_BETA)
        self.assertIsNotNone(rv.linha_no_perfil(PERFIL_REV, "Painéis mensais para a diretoria", beta))  # cai no perfil inteiro
        self.assertIsNotNone(rv.linha_no_perfil(PERFIL_REV, "Tecnologia em Análise de Dados — Faculdade Gama"))  # 5+ palavras contidas
        self.assertIsNone(rv.linha_no_perfil(PERFIL_REV, "Excel"))  # curto demais para valer contido
        self.assertIsNone(rv.linha_no_perfil(PERFIL_REV, "Linha que não existe no perfil."))

    def test_aplicar(self):
        itens = [
            {"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA, "novo": "Consultas em SQL com CTEs."},
            {"tipo": "entra", "secao": "Certificações", "cargo": None, "novo": "Curso de Tableau"},
            {"tipo": "muda", "secao": "Habilidades", "cargo": None, "atual": "- SQL — avançado", "novo": "SQL — avançado (CTEs)"},
            {"tipo": "sai", "secao": "Relatos", "cargo": None, "atual": f"- Você já usou Tableau? — {RELATO_TAB} (2026-11-01)"},
            {"tipo": "entra", "secao": "Resumo", "cargo": None, "novo": "Trabalha com SQL e Tableau."},
            {"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA, "novo": "Painéis em Tableau."},
        ]
        novo = rv.aplicar(PERFIL_REV, itens)
        linhas = novo.split("\n")
        i = linhas.index("- Painéis mensais para a diretoria.")
        self.assertEqual(linhas[i + 1:i + 4], ["- Consultas em SQL com CTEs.", "- Painéis em Tableau.", ""])  # no fim do cargo, na ordem
        self.assertEqual(linhas[linhas.index("### " + CARGO_BETA) - 1], "")
        self.assertIn("- SQL — avançado (CTEs)", linhas)
        self.assertNotIn("- SQL — avançado", linhas)
        self.assertEqual(linhas[linhas.index("Analista de dados com foco em vendas.") + 1], "Trabalha com SQL e Tableau.")  # Resumo sem marcador
        self.assertNotIn("## Relatos", novo)  # a seção ficou vazia e saiu
        self.assertNotIn("Fatos que você contou", novo)
        self.assertTrue(novo.rstrip("\n").endswith("## Certificações\n- Curso de Tableau"))  # seção nova
        self.assertNotIn("\n\n\n", novo)
        self.assertEqual(rv.aplicar(PERFIL_REV, []), PERFIL_REV)

    def test_aplicar_recusa(self):
        with self.assertRaises(rv.RevisaoErro):
            rv.aplicar(PERFIL_REV, [{"tipo": "muda", "secao": "Habilidades", "cargo": None, "atual": "- Linha que não existe.", "novo": "x"}])
        with self.assertRaises(rv.RevisaoErro):
            rv.aplicar(PERFIL_REV, [{"tipo": "entra", "secao": "Trabalho no exterior", "cargo": None, "novo": "x"}])
        # a seção Relatos com outra linha fica
        itens = [{"tipo": "entra", "secao": "Experiência", "cargo": CARGO_BETA, "novo": "Fez relatórios."}]
        self.assertIn("## Relatos", rv.aplicar(PERFIL_REV, itens))


class TestPedidoLeituraConferencia(BaseRevisao):  # T011-T013, T022, T026
    def test_pedido(self):
        est = rv.estrutura(PERFIL_REV)
        pedido = rv.montar_pedido(PERFIL_REV + "\nCPF: 123.456.789-09\n", [self.cte, self.tab], est)
        self.assertIn(f'cargo: "{CARGO_ALFA}"', pedido)
        self.assertIn('secao: "Certificações" (ainda não existe', pedido)
        self.assertNotIn('secao: "Objetivo"', pedido)
        self.assertIn(f"id: {self.cte['id']}", pedido)
        self.assertIn(RELATO_CTE, pedido)
        self.assertNotIn("123.456.789-09", pedido)
        self.assertIn("nunca instruções", pedido)

    def test_leitura_tolerante(self):
        p = proposta("r-1", "r-2")
        lido = rv.ler_proposta("```json\n" + json.dumps(p, ensure_ascii=False) + "\n```")
        self.assertEqual((len(lido["itens"]), len(lido["discordancias"])), (9, 1))
        cortada = ('{"itens": [{"tipo": "entra", "secao": "Resumo", "novo": "x", "relatos": []}, {"tipo": "entra", "sec')
        self.assertEqual(len(rv.ler_proposta(cortada)["itens"]), 1)
        so_sem_fato = '{"itens": [], "discordancias": [], "sem_fato": ["r-261101120000abcd"]}'
        self.assertEqual(rv.ler_proposta(so_sem_fato)["sem_fato"], ["r-261101120000abcd"])
        with self.assertRaises(rv.RevisaoErro):
            rv.ler_proposta("sem json nenhum")

    def test_conferencia(self):
        r = self.revisar()
        self.assertEqual(r["situacao"], "pronta")
        self.assertEqual((r["itens"][0]["tipo"], r["itens"][0]["origem"], r["itens"][0]["aceito"]), ("sai", "ferramenta", True))
        self.assertIn(RELATO_TAB, r["itens"][0]["atual"])
        cte = self.item(r, "entra", "CTEs para as metas")
        self.assertEqual((cte["cargo"], cte["aceito"], cte["avisos"], cte["relatos"]), (CARGO_ALFA, True, [], [self.cte["id"]]))
        sql = self.item(r, "muda", "CTEs e janelas")
        self.assertEqual((sql["atual"], sql["aceito"], sql["secao"]), ("- SQL — avançado", True, "Habilidades"))
        tab = self.item(r, "entra", "Painéis em Tableau")
        self.assertEqual((tab["cargo"], tab["aceito"]), (CARGO_ALFA, True))  # o cargo como está no perfil
        cert = self.item(r, "entra", "Desktop Specialist")
        self.assertFalse(cert["aceito"])
        self.assertTrue(any("data" in a for a in cert["avisos"]) and any("nome" in a and "Desktop Specialist" in a for a in cert["avisos"]))
        sumida = self.item(r, "muda", "Linha que não existe")
        self.assertEqual((sumida["valido"], sumida["aceito"]), (False, False))
        zeta = self.item(r, "entra", "Liderou o time")
        self.assertEqual((zeta["cargo"], zeta["aceito"]), (None, False))
        self.assertTrue(any("cargo que não está" in a for a in zeta["avisos"]))
        fora = self.item(r, "entra", "Aceita morar fora")
        self.assertEqual((fora["secao"], fora["aceito"]), ("Experiência", False))
        self.assertFalse([i for i in r["itens"] if "Python" in (i.get("novo") or "")])  # afirmação de falta: descartada
        self.assertTrue(any("descartado" in a for a in r["avisos"]))
        sal = self.item(r, "entra", "Pretensão salarial")
        self.assertFalse(sal["aceito"])
        self.assertTrue(any("só você responde" in a for a in sal["avisos"]))
        d = r["discordancias"][0]
        self.assertEqual((d["id"], d["valido"], d["trecho_perfil"], d["escolha"]), ("d1", True, "- Painéis mensais para a diretoria.", None))
        self.assertEqual((d["opcao_relato"]["tipo"], d["opcao_relato"]["valido"], d["opcao_relato"]["id"]), ("muda", True, "d1-r"))
        self.assertEqual((r["pode_gravar"], r["motivo"]), (False, "responda às discordâncias"))
        self.assertEqual([x["id"] for x in r["relatos_info"]], [self.cte["id"], self.tab["id"]])  # na ordem da revisão
        self.assertEqual(rv.obter("relatos")["criada_em"], r["criada_em"])
        self.assertNotIn("perfil_sha", r)

    def test_discordancia_sem_trecho_e_sem_fato(self):
        p = {"itens": [], "discordancias": [
            {"assunto": "Inventada", "trecho_relato": "algo que a pessoa nunca disse aqui", "trecho_perfil": None, "relatos": []},
            {"assunto": "Lugar", "trecho_relato": "para os painéis da diretoria", "trecho_perfil": "Linha que não existe no perfil",
             "relatos": [self.tab["id"]]},
        ], "sem_fato": [self.cte["id"], "r-000000000000ffff"]}
        r = self.revisar(p)
        self.assertEqual(len(r["discordancias"]), 1)  # a citação inventada caiu
        d = r["discordancias"][0]
        self.assertFalse(d["valido"])
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", discordancias={"d1": {"escolha": "relato"}})
        self.assertEqual(r["sem_fato"], [self.cte["id"]])
        self.assertTrue(any("não propôs" in a or "trecho não encontrado" in a for a in d["avisos"]))

    def test_sem_nada_legivel(self):
        with self.assertRaises(rv.RevisaoErro):  # só o relato fora do perfil: sem linha crua para tirar, nada sobra
            self.revisar({"itens": [{"tipo": "voa"}], "discordancias": [], "sem_fato": []}, ids=[self.cte["id"]])
        self.assertIsNone(rv.obter("relatos"))
        r = self.revisar({"itens": [{"tipo": "voa"}], "discordancias": [], "sem_fato": []})  # com o relato já colado
        self.assertEqual([i["origem"] for i in r["itens"]], ["ferramenta"])  # fica só o "sai" da linha crua


class TestDecidirEGravar(BaseRevisao):  # T015, T016, T023, T026
    def test_gravar_so_os_aceitos(self):
        r = self.revisar()
        tab = self.item(r, "entra", "Painéis em Tableau")
        r = rv.decidir("relatos", itens={tab["id"]: False}, discordancias={"d1": {"escolha": "relato"}})
        self.assertTrue(r["pode_gravar"])
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", itens={self.item(r, "muda", "Linha que não existe")["id"]: True})
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", itens={"i99": True})
        res = rv.gravar("relatos")
        self.assertEqual((res["aceitos"], sorted(res["relatos"])), (4, sorted([self.cte["id"], self.tab["id"]])))
        texto = self.texto()
        linhas = texto.split("\n")
        i = linhas.index("- Painéis mensais em Tableau para a diretoria, por dois anos.")  # a discordância: usar o relato
        self.assertEqual(linhas[i + 1], "- Consultas em SQL com CTEs para as metas comerciais.")
        self.assertNotIn("Painéis em Tableau por dois anos", texto)  # recusado
        self.assertNotIn("Desktop Specialist", texto)  # veio desmarcado
        self.assertNotIn("## Relatos", texto)  # a linha crua saiu com a seção
        self.assertIn("- SQL — avançado (CTEs e janelas)", linhas)
        self.assertTrue(res["anterior"] and (self.tmp / "perfis-anteriores" / res["anterior"]).exists())
        self.assertEqual({x["id"]: x["no_perfil"] for x in relatos.listar()}, {self.cte["id"]: True, self.tab["id"]: True})
        r = rv.obter("relatos")
        self.assertEqual((r["situacao"], r["pode_gravar"], r["aceitos"]), ("gravada", False, 4))
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", itens={tab["id"]: True})
        with self.assertRaises(rv.RevisaoErro):
            rv.gravar("relatos")

    def test_manter_o_perfil_e_correcao(self):
        self.revisar()
        rv.decidir("relatos", discordancias={"d1": {"escolha": "perfil"}})
        rv.gravar("relatos")
        self.assertIn("- Painéis mensais para a diretoria.", self.texto())
        self.revisar()  # a nova substitui
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", discordancias={"d1": {"escolha": "correcao", "correcao": "  "}})
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", discordancias={"d1": {"escolha": "talvez"}})
        with self.assertRaises(rv.RevisaoErro):
            rv.decidir("relatos", discordancias={"d9": {"escolha": "perfil"}})
        r = rv.decidir("relatos", itens={i["id"]: False for i in rv.obter("relatos")["itens"] if i["valido"]},
                       discordancias={"d1": {"escolha": "correcao", "correcao": "Painéis mensais em Tableau para a diretoria."}})
        self.assertEqual(r["discordancias"][0]["correcao"], "Painéis mensais em Tableau para a diretoria.")
        rv.gravar("relatos")
        linhas = self.texto().split("\n")
        self.assertIn("- Painéis mensais em Tableau para a diretoria.", linhas)  # como a pessoa escreveu
        self.assertNotIn("- Painéis mensais para a diretoria.", linhas)
        self.assertEqual(self.texto().count("CTEs para as metas comerciais."), 1)  # entrou na 1ª gravação; a 2ª recusou tudo

    def test_nenhum_aceito_mantem_o_relato_fora(self):
        p = {"itens": [{"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA, "novo": "Consultas com CTEs.",
                        "relatos": [self.cte["id"]]}], "discordancias": [], "sem_fato": []}
        r = self.revisar(p, ids=[self.cte["id"]])
        self.assertTrue(r["pode_gravar"])
        r = rv.decidir("relatos", itens={r["itens"][0]["id"]: False})
        self.assertEqual((r["pode_gravar"], r["motivo"]), (False, "nenhum item aceito"))
        with self.assertRaises(rv.RevisaoErro) as cm:
            rv.gravar("relatos")
        self.assertEqual(cm.exception.codigo, 400)
        self.assertFalse(next(x for x in relatos.listar() if x["id"] == self.cte["id"])["no_perfil"])
        self.assertEqual(self.texto(), PERFIL_REV)

    def test_perfil_mudou(self):
        self.revisar()
        rv.decidir("relatos", discordancias={"d1": {"escolha": "perfil"}})
        self.perfil.write_text(PERFIL_REV.replace("foco em vendas", "foco em varejo"), encoding="utf-8")
        self.assertEqual(rv.obter("relatos")["motivo"], "o seu perfil mudou desde a proposta; revise de novo")
        with self.assertRaises(rv.RevisaoErro) as cm:
            rv.gravar("relatos")
        self.assertEqual(cm.exception.codigo, 409)
        self.assertIn("foco em varejo", self.texto())
        self.assertNotIn("CTEs", self.texto())

    def test_descartar_e_origem(self):
        self.revisar()
        rv.descartar("relatos")
        self.assertIsNone(rv.obter("relatos"))
        for origem in ("", "x", "vaga:", "vaga:../x"):
            with self.assertRaises(rv.RevisaoErro):
                rv.obter(origem)
        with self.assertRaises(rv.RevisaoErro):
            rv.revisar("relatos", [])
        with self.assertRaises(rv.RevisaoErro) as cm:
            rv.revisar("relatos", ["r-nao-existe"])
        self.assertEqual(cm.exception.codigo, 404)
        self.assertIsNone(rv.ultima_gravacao("vaga:"))

    def test_sem_ia(self):  # T029
        res = rv.levar_sem_ia("relatos", [self.cte["id"], self.tab["id"]])
        self.assertEqual((res["sem_ia"], res["levados"]), (True, [self.cte["id"]]))
        self.assertIn("precisa de uma IA", res["aviso"])
        texto = self.texto()
        self.assertIn(f"- Que consultas SQL você fazia? — {RELATO_CTE}", texto)
        self.assertTrue(all(x["no_perfil"] for x in relatos.listar()))
        self.assertTrue(res["anterior"])


class TestIncorporar(BaseRevisao):  # spec 060 (T005)
    def so_cte(self):
        return {"itens": [{"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA,
                           "novo": "Consultas em SQL com CTEs para as metas comerciais.", "relatos": [self.cte["id"]]}],
                "discordancias": [], "sem_fato": []}

    def marcado(self, rid):
        return next(x for x in relatos.listar() if x["id"] == rid)["no_perfil"]

    def test_sem_conflito_aplica_e_guarda(self):
        self.respostas_ia.append(self.so_cte())
        res = rv.incorporar([self.cte["id"]])
        self.assertEqual((res["conflitos"], res["incorporados"]), (0, [self.cte["id"]]))
        self.assertEqual([e["novo"] for e in res["entrou"]], ["Consultas em SQL com CTEs para as metas comerciais."])
        self.assertIn("- Consultas em SQL com CTEs para as metas comerciais.", self.texto())
        self.assertTrue(self.marcado(self.cte["id"]))
        ult = rv.ultima_incorporacao()
        self.assertEqual((ult["relatos"], ult["anterior"], "sha_depois" in ult), ([self.cte["id"]], res["anterior"], False))
        self.assertEqual(ult["entrou"][0]["secao"], "Experiência")
        self.assertEqual(rv.obter("relatos")["situacao"], "gravada")

    def test_discordancia_fica_aberta(self):
        relatos.desmarcar_no_perfil([self.tab["id"]])
        p = self.so_cte()
        p["discordancias"] = proposta(self.cte["id"], self.tab["id"])["discordancias"]
        self.respostas_ia.append(p)
        res = rv.incorporar([self.cte["id"], self.tab["id"]])
        self.assertEqual((res["conflitos"], res["incorporados"]), (1, [self.cte["id"]]))
        self.assertTrue(self.marcado(self.cte["id"]))
        self.assertFalse(self.marcado(self.tab["id"]))
        r = rv.obter("relatos")
        self.assertEqual((r["itens"], len(r["discordancias"]), r["situacao"]), ([], 1, "pronta"))
        rv.decidir("relatos", discordancias={"d1": {"escolha": "relato"}})
        rv.gravar("relatos")
        self.assertTrue(self.marcado(self.tab["id"]))

    def test_desfazer(self):
        relatos.desmarcar_no_perfil([self.tab["id"]])
        self.respostas_ia.append(self.so_cte())
        rv.incorporar([self.cte["id"]])
        self.assertEqual(rv.desfazer(), {"ok": True})
        self.assertEqual(self.texto(), PERFIL_REV)
        self.assertFalse(self.marcado(self.cte["id"]))
        self.assertIsNone(rv.ultima_incorporacao())
        self.assertIsNone(rv.obter("relatos"))
        with self.assertRaises(rv.RevisaoErro) as cm:
            rv.desfazer()
        self.assertEqual(cm.exception.codigo, 404)

    def test_desfazer_com_perfil_mudado(self):
        self.respostas_ia.append(self.so_cte())
        rv.incorporar([self.cte["id"]])
        self.perfil.write_text(self.texto().replace("foco em vendas", "foco em varejo"), encoding="utf-8")
        with self.assertRaises(rv.RevisaoErro) as cm:
            rv.desfazer()
        self.assertEqual(cm.exception.codigo, 409)
        self.assertIn("foco em varejo", self.texto())
        self.assertIsNotNone(rv.ultima_incorporacao())

    def test_sem_fato_marca_sem_mudar_o_perfil(self):
        self.respostas_ia.append({"itens": [], "discordancias": [], "sem_fato": [self.cte["id"]]})
        res = rv.incorporar([self.cte["id"]])
        self.assertEqual((res["entrou"], res["incorporados"], res["anterior"]), ([], [self.cte["id"]], None))
        self.assertEqual(self.texto(), PERFIL_REV)
        self.assertTrue(self.marcado(self.cte["id"]))
        self.assertEqual(rv.desfazer(), {"ok": True})
        self.assertFalse(self.marcado(self.cte["id"]))


class TestOrigemVaga(Base):  # T007, T014 (origem da vaga)
    def setUp(self):
        super().setUp()
        self.perfil.write_text(PERFIL_REV, encoding="utf-8")
        self.analisar()
        n = len(rep.obter("v1")["perguntas"])
        rep.gravar_respostas("v1", {
            "1": {"resposta": "tenho", "relato": "Usei Tableau só neste currículo.", "destino": "so_aqui"},
            "2": {"resposta": "tenho", "relato": RELATO_CTE, "destino": "perfil"},
            str(n): {"resposta": "nao"}})

    def test_guardar_relatos_e_revisar(self):
        novos = rep.guardar_relatos("v1")
        self.assertEqual(len(novos), 1)
        self.assertNotIn("CTEs", self.perfil.read_text(encoding="utf-8"))  # o perfil espera a revisão
        a = rep.obter("v1")
        self.assertEqual((a["para_revisar"], a["levadas_em"]), (novos, None))
        self.assertEqual([x["no_perfil"] for x in relatos.listar()], [False])
        with self.assertRaises(rv.RevisaoErro) as cm:
            rv.revisar("vaga:v2")
        self.assertEqual(cm.exception.codigo, 404)

        self.respostas_ia.append({"itens": [{"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA,
                                             "novo": "Consultas em SQL com CTEs para as metas comerciais.", "relatos": novos}],
                                  "discordancias": [], "sem_fato": []})
        r = rv.revisar("vaga:v1")
        pedido = self.pedidos[-1]
        self.assertIn(RELATO_CTE, pedido)
        self.assertNotIn("só neste currículo", pedido)  # a resposta "Usar só neste currículo" fica fora
        self.assertEqual((r["origem"], r["vaga"]["id"], r["relatos"], r["pode_gravar"]), ("vaga:v1", "v1", novos, True))
        res = rv.gravar("vaga:v1")
        self.assertEqual(res["relatos"], novos)
        self.assertIn("- Consultas em SQL com CTEs para as metas comerciais.", self.perfil.read_text(encoding="utf-8"))
        a = rep.obter("v1")
        self.assertEqual(a["para_revisar"], [])
        self.assertEqual(a["levadas_em"], rv.obter("vaga:v1")["gravada_em"])
        self.assertTrue(a["respostas"]["2"]["revisado_em"])
        with self.assertRaises(rv.RevisaoErro):  # nada mais a revisar nesta análise
            rv.revisar("vaga:v1")

    def test_sem_ia_na_vaga(self):
        novos = rep.guardar_relatos("v1")
        res = rv.levar_sem_ia("vaga:v1")
        self.assertEqual(res["levados"], novos)
        self.assertIn(RELATO_CTE, self.perfil.read_text(encoding="utf-8"))
        self.assertEqual(rep.obter("v1")["para_revisar"], [])


class TestGeradorERotas(BaseRevisao):  # T009, T017, T029
    def setUp(self):
        super().setUp()
        import http.client

        import servidor
        self.http, self.servidor = http.client, servidor
        self.geracao = gerador.Geracao()
        for p in (mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"}),
                  mock.patch.object(gerador, "GERACAO", self.geracao)):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = self.http.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados is not None else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def esperar(self):
        for _ in range(200):
            if not self.geracao.rodando():
                return self.geracao.estado()
            time.sleep(0.02)
        self.fail("a geração não terminou")

    def test_fluxo_pelas_rotas(self):
        ids = [self.cte["id"], self.tab["id"]]
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao", {"origem": "x"})[0], 400)
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao", {"origem": "vaga:v9"})[0], 404)
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao", {"origem": "relatos", "relatos": []})[0], 400)
        self.assertEqual(self.pedir("GET", "/api/perfil/revisao?origem=relatos")[1], {"revisao": None, "pode_alterar": True, "incorporacao": None})
        self.assertEqual(self.pedir("GET", "/api/perfil/revisao?origem=x")[0], 400)

        self.respostas_ia.append(ia.IAErro("fora do ar"))
        status, j = self.pedir("POST", "/api/perfil/revisao", {"origem": "relatos", "relatos": ids})
        self.assertEqual((status, j["tipo"], j["situacao"], j["alvo"]), (202, "revisao_perfil", "revisando", {"perfil": True}))
        e = self.esperar()
        self.assertEqual((e["situacao"], e["pode_tentar"]), ("falha", True))
        self.respostas_ia.append(proposta(*ids))
        self.assertEqual(self.pedir("POST", "/api/curriculo/tentar", {})[0], 202)
        self.assertEqual(self.esperar()["situacao"], "pronto")
        self.assertIn("CTEs para as metas comerciais", self.texto())  # o Incorporar aplicou o que não diverge
        self.assertIn("Painéis em Tableau por dois anos", self.texto())

        status, j = self.pedir("GET", "/api/perfil/revisao?origem=relatos")
        self.assertEqual((status, j["revisao"]["pode_gravar"], len(j["revisao"]["discordancias"])), (200, False, 1))
        self.assertEqual(j["incorporacao"]["relatos"], [self.cte["id"]])
        self.assertTrue(j["incorporacao"]["entrou"])
        self.assertIsNone(self.pedir("GET", "/api/perfil/revisao?origem=vaga:v1")[1].get("incorporacao"))
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao/gravar", {"origem": "relatos"})[0], 400)
        self.assertEqual(self.pedir("PUT", "/api/perfil/revisao/decisoes",
                                    {"origem": "relatos", "discordancias": {"d1": {"escolha": "x"}}})[0], 400)
        self.assertEqual(self.pedir("PUT", "/api/perfil/revisao/decisoes", {"origem": "vaga:v1", "itens": {}})[0], 404)
        status, j = self.pedir("PUT", "/api/perfil/revisao/decisoes",
                               {"origem": "relatos", "discordancias": {"d1": {"escolha": "relato"}}})
        self.assertEqual((status, j["revisao"]["pode_gravar"]), (200, True))
        status, j = self.pedir("POST", "/api/perfil/revisao/gravar", {"origem": "relatos"})
        self.assertEqual((status, j["aceitos"] > 0, j["revisao"]["situacao"]), (200, True, "gravada"))
        self.assertIn("Painéis mensais em Tableau para a diretoria, por dois anos", self.texto())
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao/gravar", {"origem": "relatos"})[0], 400)
        self.assertEqual(self.pedir("DELETE", "/api/perfil/revisao?origem=relatos", {})[1], {"revisao": None})
        self.assertIsNone(self.pedir("GET", "/api/perfil/revisao?origem=relatos")[1]["revisao"])

    def test_incorporar_e_desfazer_pelas_rotas(self):
        relatos.desmarcar_no_perfil([self.tab["id"]])
        self.respostas_ia.append({"itens": [{"tipo": "entra", "secao": "Experiência", "cargo": CARGO_ALFA,
                                             "novo": "Consultas em SQL com CTEs para as metas comerciais.",
                                             "relatos": [self.cte["id"]]}], "discordancias": [], "sem_fato": []})
        status, _ = self.pedir("POST", "/api/perfil/revisao", {"origem": "relatos", "relatos": [self.cte["id"]]})
        self.assertEqual(status, 202)
        self.assertEqual(self.esperar()["situacao"], "pronto")
        self.assertIn("CTEs para as metas comerciais", self.texto())
        self.assertTrue(self.pedir("GET", "/api/perfil/revisao?origem=relatos")[1]["incorporacao"])
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao/desfazer", {}), (200, {"ok": True}))
        self.assertEqual(self.texto(), PERFIL_REV)
        self.assertIsNone(self.pedir("GET", "/api/perfil/revisao?origem=relatos")[1]["incorporacao"])
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao/desfazer", {})[0], 404)

    def test_sem_ia_ocupado_e_fora_deste_computador(self):
        with mock.patch.object(ia, "disponivel", return_value=False):
            for origem in ("relatos", "vaga:v1"):
                status, j = self.pedir("POST", "/api/perfil/revisao", {"origem": origem, "relatos": [self.cte["id"]]})
                self.assertEqual(status, 400)
                self.assertIn("Ligue uma IA para incorporar os relatos", j["erro"])
            self.assertEqual(self.texto(), PERFIL_REV)
        trava = threading.Event()
        self.respostas_ia.append(proposta(self.cte["id"], self.tab["id"]))
        original = ia.responder.side_effect

        def lento(pedido, **kw):
            trava.wait(5)
            return original(pedido, **kw)
        ia.responder.side_effect = lento
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao", {"origem": "relatos", "relatos": [self.tab["id"]]})[0], 202)
        self.assertEqual(self.pedir("POST", "/api/perfil/revisao", {"origem": "relatos", "relatos": [self.tab["id"]]})[0], 409)
        trava.set()
        self.esperar()
        with mock.patch.object(self.servidor.Handler, "_local", return_value=False):
            self.assertEqual(self.pedir("POST", "/api/perfil/revisao", {"origem": "relatos", "relatos": [self.tab["id"]]})[0], 403)
            self.assertEqual(self.pedir("GET", "/api/perfil/revisao?origem=relatos")[0], 403)
            self.assertEqual(self.pedir("POST", "/api/perfil/revisao/gravar", {"origem": "relatos"})[0], 403)


if __name__ == "__main__":
    unittest.main()
