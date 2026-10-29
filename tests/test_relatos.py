"""Relatos (spec 035), sem navegador, sem rede e sem IA de verdade: o relato da pessoa vira a resposta da pergunta comum
(um pedido à IA, dentro do limite; sem IA, o próprio relato), fica guardado e entra no texto do perfil de todos os
pedidos; sensível e cadastral vão literais e nunca à IA; remuneração atual × pretensão; nome da mãe é cadastro e é
reaproveitado com outra redação; "Levar ao perfil" grava o perfil.md guardando a versão anterior."""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import analise  # noqa: E402
import candidatura_ia  # noqa: E402
import conferir  # noqa: E402
import curriculo_ia  # noqa: E402
import entrevista  # noqa: E402
import filtros  # noqa: E402
import ia  # noqa: E402
import primeiros_passos  # noqa: E402
import relatos  # noqa: E402
from candidatura import auto, formulario, memoria  # noqa: E402
from test_candidatura_assistida import Base, PaginaFalsa  # noqa: E402

PERGUNTA_PROJETO = "Conte um projeto em que você usou Power BI"
PERGUNTA_MAE = "Qual é o nome completo da sua mãe? Essa informação é necessária para fins cadastrais."
PERGUNTA_REMUNERACAO = "Poderia compartilhar conosco a sua remuneração atual?"
PERGUNTA_PRETENSAO = "Qual sua pretensão salarial?"
RELATO = ("Em 2023 montei no time de vendas um painel de Power BI com as metas por região, ligado ao SQL Server; "
          "o time passou a usar toda segunda-feira na reunião e deixamos de montar a planilha à mão. " * 3)


def pagina():
    return PaginaFalsa(campos=[
        {"chave": "#projeto", "tipo": "area", "tipo_html": "textarea", "rotulo": PERGUNTA_PROJETO, "valor": "", "limite": 300},
        {"chave": "#mae", "tipo": "area", "tipo_html": "textarea", "rotulo": PERGUNTA_MAE, "valor": "", "limite": 1000},
        {"chave": "#remun", "tipo": "area", "tipo_html": "textarea", "rotulo": PERGUNTA_REMUNERACAO, "valor": "", "limite": 1000},
        {"chave": "#pretensao", "tipo": "texto", "tipo_html": "text", "rotulo": PERGUNTA_PRETENSAO, "valor": ""},
    ])


class BaseRelatos(Base):
    def setUp(self):
        super().setUp()
        self.perfil = self.tmp / "perfil.md"
        self.perfil.write_text("# Perfil\n\n## Experiência\n\n- Analista de Dados na Empresa Alfa (2021–2024)\n",
                               encoding="utf-8")
        (self.tmp / "config.json").write_text(json.dumps({"perfil": str(self.perfil), "termos": ["analista"]}),
                                              encoding="utf-8")
        for p in (mock.patch.object(conferir, "perfil_padrao", return_value=self.perfil),
                  mock.patch.object(primeiros_passos, "caminho_perfil", return_value=self.perfil),
                  mock.patch.object(primeiros_passos, "ANTERIORES", self.tmp / "perfis-anteriores")):
            p.start()
            self.addCleanup(p.stop)

    def ia_falsa(self, resposta=None):
        self.pedidos = []

        def responder(pedido, **_):
            self.pedidos.append(pedido)
            return json.dumps(resposta if resposta is not None else
                              [{"indice": 1, "resposta": "Montei um painel de Power BI de metas por região, ligado ao SQL "
                                                         "Server, que o time de vendas usa toda semana. " * 4}])
        for p in (mock.patch.object(ia, "responder", side_effect=responder),
                  mock.patch.object(ia, "disponivel", return_value=True),
                  mock.patch.object(ia, "aviso_reserva", return_value=None),
                  mock.patch.object(ia, "marca", return_value={"provedor": "falsa", "modelo": "m"})):
            p.start()
            self.addCleanup(p.stop)


class TestClassificacao(unittest.TestCase):
    def test_remuneracao_atual_e_pretensao(self):
        for pergunta in (PERGUNTA_REMUNERACAO, "Qual sua última/atual remuneração?", "Qual o seu salário atual?",
                         "What is your current salary?", "Quanto você ganha hoje?"):
            self.assertEqual(candidatura_ia.sensivel(pergunta), "remuneração atual", pergunta)
        for pergunta in (PERGUNTA_PRETENSAO, "What are your salary expectations?", "Expected compensation (USD)",
                         "Salário"):
            self.assertEqual(candidatura_ia.sensivel(pergunta), "pretensão salarial", pergunta)

    def test_nome_da_mae_em_campo_longo_e_cadastro(self):
        def marca(rotulo, tipo="area"):
            return formulario.classificar_campo({"tipo": tipo, "rotulo": rotulo, "opcoes": []})[0]
        self.assertEqual(marca(PERGUNTA_MAE), "cadastro")
        self.assertEqual(marca("Nome do pai"), "cadastro")
        self.assertEqual(marca("Informe seu CPF"), "cadastro")
        self.assertEqual(marca(PERGUNTA_PROJETO), "comum")
        self.assertEqual(marca("Descreva um documento técnico que você escreveu"), "comum")


class TestMemoria(BaseRelatos):
    def test_remuneracao_atual_guardada_com_outra_redacao(self):
        self.assertTrue(memoria.lembrar({"rotulo": PERGUNTA_REMUNERACAO, "tipo": "area"}, "R$ 9.000 CLT"))
        self.assertEqual(memoria.valor_para({"rotulo": "Qual o seu salário atual?", "tipo": "texto"}), "R$ 9.000 CLT")
        self.assertFalse(memoria.lembrar({"rotulo": PERGUNTA_PRETENSAO, "tipo": "texto"}, "R$ 12.000"))
        self.assertIsNone(memoria.valor_para({"rotulo": PERGUNTA_PRETENSAO, "tipo": "texto"}))

    def test_nome_da_mae_com_outra_redacao(self):
        self.assertTrue(memoria.lembrar({"rotulo": PERGUNTA_MAE, "tipo": "area"}, "Maria Exemplo"))
        self.assertEqual(memoria.valor_para({"rotulo": "Nome da mãe", "tipo": "texto"}), "Maria Exemplo")
        self.assertIsNone(memoria.valor_para({"rotulo": "Nome do pai", "tipo": "texto"}))
        self.assertIsNone(memoria.valor_para({"rotulo": "Nome completo", "tipo": "texto"}))


class TestBaseDeRelatos(BaseRelatos):
    def test_guardar_editar_apagar(self):
        r = relatos.adicionar(PERGUNTA_PROJETO, "Fiz um painel. CPF 123.456.789-09.", "Resposta.", {"id": "v1", "titulo": "Dev"})
        self.assertNotIn("123.456.789-09", r["relato"])  # documentos mascarados
        relatos.adicionar(PERGUNTA_PROJETO, "Fiz um painel. CPF 123.456.789-09.", "Outra resposta.")  # o mesmo: atualiza
        self.assertEqual(len(relatos.listar()), 1)
        relatos.editar(r["id"], "Fiz um painel de vendas.")
        self.assertEqual(relatos.listar()[0]["relato"], "Fiz um painel de vendas.")
        with self.assertRaises(relatos.RelatoErro):
            relatos.editar(r["id"], "  ")
        relatos.apagar(r["id"])
        self.assertEqual(relatos.listar(), [])
        with self.assertRaises(relatos.RelatoErro):
            relatos.apagar(r["id"])

    def test_relato_entra_no_perfil_de_todos_os_pedidos(self):  # SC-002
        r = relatos.adicionar(PERGUNTA_PROJETO, "Montei um painel de Power BI de metas por região em 2023.")
        for nome, texto in (("currículo", curriculo_ia.perfil_texto()), ("entrevista", entrevista.perfil_texto()),
                            ("nota", analise.montar_pedido([{"id": "x1", "titulo": "Analista", "empresa": "ACME",
                                                             "descricao": "Vaga."}]))):
            with self.subTest(pedido=nome):
                self.assertIn("Relatos da pessoa", texto)
                self.assertIn("painel de Power BI de metas por região em 2023", texto)
        relatos.apagar(r["id"])
        self.assertNotIn("Relatos da pessoa", curriculo_ia.perfil_texto())

    def test_numero_do_relato_conta_como_fato_na_conferencia(self):
        cv = {"destaques": ["Reduzi em 40% o tempo do fechamento"]}
        self.assertTrue(conferir.conferir_fatos(cv, curriculo_ia.perfil_texto()))  # sem o relato, o 40% é bloqueado
        relatos.adicionar(PERGUNTA_PROJETO, "O painel reduziu em 40% o tempo do fechamento.")
        self.assertEqual(conferir.conferir_fatos(cv, curriculo_ia.perfil_texto()), [])

    def test_levar_ao_perfil(self):
        r = relatos.adicionar(PERGUNTA_PROJETO, "Montei um painel de Power BI em 2023.")
        saida = relatos.levar_ao_perfil(r["id"])
        texto = self.perfil.read_text(encoding="utf-8")
        self.assertIn("## Relatos", texto)
        self.assertIn("Montei um painel de Power BI em 2023.", texto)
        self.assertTrue(saida["anterior"])  # a versão anterior ficou guardada
        self.assertTrue(relatos.listar()[0]["no_perfil"])
        self.assertNotIn("Relatos da pessoa", curriculo_ia.perfil_texto())  # já está no perfil: não repete
        r2 = relatos.adicionar("Outra pergunta", "Outro fato.")
        relatos.levar_ao_perfil(r2["id"])
        texto = self.perfil.read_text(encoding="utf-8")
        self.assertEqual(texto.count("## Relatos"), 1)
        self.assertLess(texto.index("Power BI em 2023"), texto.index("Outro fato."))


class TestResponder(BaseRelatos):
    def responder(self, respostas, **kw):
        aba = pagina()
        r = auto.responder(aba, self.VAGA, formulario.ler(aba)["assinatura"], respostas, **kw)
        return aba, r

    RESPOSTAS = [{"chave": "#projeto", "valor": RELATO}, {"chave": "#mae", "valor": "Maria Exemplo"},
                 {"chave": "#remun", "valor": "R$ 9.000 CLT"}, {"chave": "#pretensao", "valor": "R$ 12.000"}]

    def test_relato_vira_resposta_e_conhecimento(self):  # SC-001, SC-004
        self.ia_falsa()
        aba, r = self.responder(self.RESPOSTAS)
        self.assertEqual(len(self.pedidos), 1)  # um pedido à IA por clique
        pedido = self.pedidos[0]
        self.assertIn(PERGUNTA_PROJETO, pedido)
        self.assertIn("até 300 caracteres", pedido)
        for fora in ("Maria Exemplo", "R$ 9.000", "R$ 12.000", "mãe", "remuneração atual", "pretensão"):
            self.assertNotIn(fora, pedido)  # sensível e cadastral nunca vão à IA
        projeto = aba._c("#projeto")["valor"]
        self.assertTrue(projeto.startswith("Montei um painel"))
        self.assertLessEqual(len(projeto), 300)
        self.assertEqual((aba._c("#mae")["valor"], aba._c("#remun")["valor"], aba._c("#pretensao")["valor"]),
                         ("Maria Exemplo", "R$ 9.000 CLT", "R$ 12.000"))
        fontes = {p["chave"]: p["fonte"] for p in r["preenchidos"]}
        self.assertEqual(fontes, {"#projeto": auto.FONTE_RELATO, "#mae": auto.FONTE_PESSOA, "#remun": auto.FONTE_PESSOA,
                                  "#pretensao": auto.FONTE_PESSOA})
        guardados = relatos.listar()
        self.assertEqual([(x["pergunta"], x["resposta"]) for x in guardados], [(PERGUNTA_PROJETO, projeto)])
        self.assertTrue(guardados[0]["relato"].startswith("Em 2023 montei"))
        perguntas = {x["pergunta"] for x in memoria.listar()}
        self.assertIn(PERGUNTA_MAE, perguntas)
        self.assertIn(PERGUNTA_REMUNERACAO, perguntas)
        self.assertNotIn(PERGUNTA_PRETENSAO, perguntas)

    def test_sem_ia_vai_o_relato_cortado(self):
        p = mock.patch.object(ia, "disponivel", return_value=False)  # nunca a IA de verdade deste computador
        p.start()
        self.addCleanup(p.stop)
        aba, r = self.responder(self.RESPOSTAS[:1])
        self.assertEqual(r["preenchidos"][0]["fonte"], auto.FONTE_RELATO_LITERAL)
        self.assertTrue(aba._c("#projeto")["valor"].startswith("Em 2023 montei"))
        self.assertLessEqual(len(aba._c("#projeto")["valor"]), 300)
        self.assertIn("Sem IA", r["aviso_ia"])

    def test_sem_guardar_relatos(self):
        self.ia_falsa()
        self.responder(self.RESPOSTAS[:1], guardar_relatos=False)
        self.assertEqual(relatos.listar(), [])

    def test_segunda_vaga_preenche_sozinha(self):  # SC-005
        self.ia_falsa()
        self.responder(self.RESPOSTAS)
        aba = pagina()
        r = auto.preencher_pagina(aba, self.VAGA, propor=lambda vaga, campos: {"itens": [], "aviso": None, "ia": None})
        fontes = {p["chave"]: p["fonte"] for p in r["preenchidos"]}
        self.assertEqual(fontes.get("#mae"), "sua resposta anterior")
        self.assertEqual(fontes.get("#remun"), "sua resposta anterior")
        perguntas = {q["chave"]: q for q in r["perguntas"]}
        self.assertIn("#pretensao", perguntas)  # a pretensão é a cada vaga
        self.assertFalse(perguntas["#pretensao"]["relato"])

    def test_painel_marca_quem_aceita_relato(self):
        aba = pagina()
        r = auto.preencher_pagina(aba, self.VAGA, propor=lambda vaga, campos: {"itens": [], "aviso": None, "ia": None})
        perguntas = {q["chave"]: q for q in r["perguntas"]}
        self.assertTrue(perguntas["#projeto"]["relato"])
        self.assertIn("conte com suas palavras", perguntas["#projeto"]["motivo"])
        for chave in ("#mae", "#remun", "#pretensao"):
            self.assertFalse(perguntas[chave]["relato"], chave)
            self.assertIn("como você escrever", perguntas[chave]["motivo"])
        self.assertTrue(perguntas["#remun"]["lembrar"])
        self.assertFalse(perguntas["#pretensao"]["lembrar"])


if __name__ == "__main__":
    unittest.main()
