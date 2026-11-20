"""Testes do conferir.py (sem IA) com perfil, vaga e currículo fictícios."""
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import conferir  # noqa: E402

PERFIL = """# Meu perfil de carreira
## Experiência
### Analista de Dados — Empresa Alfa (03/2021–atual)
- Automatizei o relatório mensal, reduzindo o fechamento de 10 para 6 dias
- Painéis em Power BI usados por 1.500 pessoas; satisfação subiu 30%
### Assistente de Dados — Empresa Beta (01/2018–06/2020)
- Consultas em SQL para a área comercial
## Habilidades e ferramentas (com nível)
- SQL — avançado
- Power BI — avançado
- Jira — intermediário
"""
VAGA = """Analista de Dados Pleno
Responsabilidades:
- Criar painéis para a diretoria
Requisitos:
- Experiência com SQL avançado
- Conhecimento em Tableau
- Python para análise de dados
- Inglês fluente
Benefícios:
- Vale refeição
"""


def cv(**mudancas):
    base = {
        "nome": "Ana Exemplo", "contato": ["ana@exemplo.com"], "titulo": "Analista de Dados",
        "resumo": "Analista de dados com painéis usados por 1,5 mil pessoas.",
        "competencias": [{"grupo": "Dados", "itens": ["SQL", "Power BI"]}],
        "experiencia": [
            {"empresa": "Empresa Alfa", "periodo": "03/2021 – atual", "cargos": [
                {"cargo": "Analista de Dados", "itens": ["Reduziu o fechamento de 10 para 6 dias automatizando o relatório",
                                                         "Satisfação subiu 30 % com os novos painéis"]}]},
            {"empresa": "Empresa Beta", "periodo": "01/2018 – 06/2020", "cargos": [
                {"cargo": "Assistente de Dados", "itens": ["Consultas em SQL para a área comercial"]}]}],
    }
    base.update(mudancas)
    return base


class TestFatos(unittest.TestCase):
    def test_fiel_ao_perfil_nao_aponta(self):
        self.assertEqual(conferir.conferir_fatos(cv(), PERFIL), [])

    def test_numero_inventado_bloqueia(self):
        c = cv()
        c["experiencia"][0]["cargos"][0]["itens"].append("Aumentou a receita em 45%")
        r = conferir.conferir(c, PERFIL)
        self.assertEqual(r["veredito"], "bloquear")
        self.assertTrue(any(p["tipo"] == "numero" and "45%" in p["valor"] for p in r["fatos"]))

    def test_numeros_escritos_de_outro_jeito(self):
        for texto in ("painéis para 1500 pessoas", "painéis para 1.500 pessoas", "satisfação subiu trinta por cento"):
            self.assertEqual(conferir.conferir_fatos(cv(resumo=texto), PERFIL), [], texto)
        self.assertEqual(len(conferir.conferir_fatos(cv(resumo="painéis para 2 mil pessoas"), PERFIL)), 1)

    def test_empresa_cargo_e_data(self):
        c = cv()
        c["experiencia"].append({"empresa": "Empresa Gama", "periodo": "02/2015 – 12/2016",
                                 "cargos": [{"cargo": "Coordenador", "itens": []}]})
        tipos = {p["tipo"] for p in conferir.conferir_fatos(c, PERFIL)}
        self.assertEqual(tipos, {"empresa", "cargo", "data"})
        self.assertEqual(conferir.conferir(c, PERFIL)["veredito"], "conferir")


TAREFA = ["Responsável pelo backlog de 2 squads.", "Atua no suporte aos usuários do sistema.",
          "Participou das reuniões de planejamento.", "Facilitou as cerimônias do time.",
          "Auxiliou a equipe no atendimento.", "Apoiou a migração dos relatórios.",
          "Responsible for the release notes.", "Assisted users with the reports.",
          "Manutenção dos painéis da diretoria.", "Elaboração de relatórios semanais."]
RESULTADO = ["Reduziu o tempo de fechamento de 10 para 6 dias.",
             "Negociou um prazo novo com a área, o que permitiu entregar a versão.",
             "Atendimento de 15 a 20 solicitações por dia.", "Automatizou a carga, reduzindo erros manuais.",
             "Treinou 30 pessoas no novo sistema.", "Evitando retrabalho, organizou a fila de pedidos.",
             "Migrou 5 painéis para a nuvem.", "Aumentou a adesão ao novo processo.",
             "Liderou 3 projetos entregues no prazo.", "Garantiu a entrega da versão sem falhas."]


def cv_com_itens(itens):
    return cv(experiencia=[{"empresa": "Empresa Alfa", "periodo": "03/2021 – atual",
                            "cargos": [{"cargo": "Analista", "itens": itens}]}])


class TestItensDeTarefa(unittest.TestCase):
    def test_classifica_20_itens(self):
        acertos = sum(conferir.item_de_tarefa(i) for i in TAREFA) + sum(not conferir.item_de_tarefa(i) for i in RESULTADO)
        self.assertGreaterEqual(acertos, 18)

    def test_quatro_de_dez(self):
        pontos = conferir.itens_de_tarefa(cv_com_itens(TAREFA[:4] + RESULTADO[:6]))
        self.assertEqual(pontos[0]["tipo"], "tarefa")
        self.assertEqual(pontos[0]["valor"], "4 de 10")
        self.assertEqual(sum(p["tipo"] == "tarefa_item" for p in pontos), 4)

    def test_no_maximo_oito_itens(self):
        pontos = conferir.itens_de_tarefa(cv_com_itens(TAREFA + TAREFA[:2]))
        self.assertEqual(len(pontos), 9)
        self.assertEqual(sum(p["tipo"] == "tarefa_item" for p in pontos), 8)

    def test_cv_padrao_um_de_tres(self):
        pontos = conferir.itens_de_tarefa(cv())
        self.assertEqual(pontos[0]["valor"], "1 de 3")

    def test_todos_com_resultado(self):
        self.assertEqual(conferir.itens_de_tarefa(cv_com_itens(RESULTADO)), [])

    def test_veredito_conferir_nunca_bloquear(self):
        self.assertEqual(conferir.conferir(cv(), PERFIL)["veredito"], "conferir")


class TestRequisitos(unittest.TestCase):
    def test_tem_sustentado_lacuna_e_cobertura(self):
        reqs, cob, lacunas = conferir.conferir_requisitos(cv(), PERFIL, VAGA)
        sit = {r["texto"]: r["situacao"] for r in reqs}
        self.assertEqual(sit["Experiência com SQL avançado"], "tem")
        self.assertEqual(sit["Conhecimento em Tableau"], "sustentado")  # Power BI é da mesma família
        self.assertEqual(sit["Python para análise de dados"], "sustentado")  # "dados" está no perfil
        self.assertEqual(sit["Inglês fluente"], "lacuna")
        self.assertNotIn("Vale refeição", sit)
        self.assertNotIn("Criar painéis para a diretoria", sit)
        self.assertEqual(lacunas, [])
        self.assertGreater(cob["total"], 0)
        self.assertIn("python", cob["faltando"])

    def test_lacuna_como_competencia_bloqueia(self):
        c = cv(competencias=[{"grupo": "Idiomas", "itens": ["Inglês fluente"]}])
        r = conferir.conferir(c, PERFIL, VAGA)
        self.assertEqual(r["veredito"], "bloquear")
        self.assertTrue(any(p["tipo"] == "lacuna" for p in r["fatos"]))

    def test_vaga_sem_cabecalho_usa_marcadores(self):
        reqs = conferir.requisitos_da_vaga("Venha trabalhar conosco.\n- SQL\n- Excel avançado\n")
        self.assertEqual(reqs, ["SQL", "Excel avançado"])


class TestRequisitosConservadores(unittest.TestCase):
    def test_certificacao_em_preparacao_vira_sustentado(self):
        perfil = (
            "## Experiência\n"
            "- Atuação com metodologia ágil no time\n"
            "- Facilitação de cerimônias ágil e promoção de práticas de desenvolvimento ágil\n"
            "## Certificações\n"
            "- Certificação Ágil Avançada (em preparação)\n"
        )
        vaga = "Requisitos:\n- Certificação Ágil Avançada\n"
        reqs = conferir.avaliar_requisitos(perfil, vaga)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["situacao"], "sustentado")
        self.assertTrue(reqs[0]["evidencia"].startswith("em preparação:"))

    def test_andamento_fora_dos_parenteses_nao_conta(self):
        perfil = ("## Experiência\n- Usa o quadro do time para ver o que está em andamento e o que falta\n"
                  "## Formação\n- Pós em Gestão de Projetos (2025–2026, em andamento)\n")
        vaga = "Requisitos:\n- Quadro do time\n- Pós em Gestão de Projetos\n"
        sit = {r["texto"]: r["situacao"] for r in conferir.avaliar_requisitos(perfil, vaga)}
        self.assertEqual(sit["Quadro do time"], "tem")
        self.assertEqual(sit["Pós em Gestão de Projetos"], "sustentado")

    def test_certificacao_sem_em_preparacao_sai_tem(self):
        perfil = (
            "## Experiência\n"
            "- Atuação com metodologia ágil no time\n"
            "- Facilitação de cerimônias ágil e promoção de práticas de desenvolvimento ágil\n"
            "## Certificações\n"
            "- Certificação Ágil Avançada\n"
        )
        vaga = "Requisitos:\n- Certificação Ágil Avançada\n"
        reqs = conferir.avaliar_requisitos(perfil, vaga)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["situacao"], "tem")

    def test_dois_idiomas_com_um_faltando_sai_lacuna(self):
        perfil = (
            "## Idiomas\n"
            "- Inglês — avançado\n"
        )
        vaga = "Requisitos:\n- Inglês e Espanhol\n"
        reqs = conferir.avaliar_requisitos(perfil, vaga)
        self.assertEqual(len(reqs), 1)
        self.assertEqual(reqs[0]["situacao"], "lacuna")
        self.assertEqual(reqs[0]["evidencia"], "falta: Espanhol")

    def test_dois_idiomas_com_ambos_presentes_nao_sai_lacuna(self):
        perfil = (
            "## Idiomas\n"
            "- Inglês — avançado\n"
            "- Espanhol — intermediário\n"
        )
        vaga = "Requisitos:\n- Inglês e Espanhol\n"
        reqs = conferir.avaliar_requisitos(perfil, vaga)
        self.assertEqual(len(reqs), 1)
        self.assertNotEqual(reqs[0]["situacao"], "lacuna")
        self.assertEqual(reqs[0]["situacao"], "tem")


class TestATS(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_tabela_e_cabecalho(self):
        from docx import Document
        doc = Document()
        doc.add_paragraph("Ana Exemplo")
        doc.add_table(rows=1, cols=2)
        doc.sections[0].header.paragraphs[0].text = "ana@exemplo.com"
        caminho = self.tmp / "cv.docx"
        doc.save(caminho)
        msgs = " ".join(p["mensagem"] for p in conferir.conferir_ats(cv(), caminho))
        self.assertIn("tabela", msgs)
        self.assertIn("cabeçalho", msgs)

    def test_docx_do_motor_passa_e_dados_pessoais_no_us(self):
        import curriculo
        c = cv(tecnicas={"formato": "us"}, contato=["ana@exemplo.com", "Married, 35 years old"])
        caminho = self.tmp / "cv.docx"
        curriculo.Montador(c).montar().save(caminho)
        pontos = conferir.conferir_ats(c, caminho)
        self.assertEqual([p["nivel"] for p in pontos], ["bloquear"])
        self.assertEqual(conferir.conferir_ats(cv(), caminho), [])

    def test_contato_sem_email(self):
        c = cv(contato=["São Paulo, SP", "linkedin.com/in/exemplo"])
        pontos = [p for p in conferir.conferir_ats(c, None) if p.get("tipo") == "contato"]
        self.assertEqual(len(pontos), 1)
        self.assertEqual(pontos[0]["nivel"], "conferir")
        self.assertEqual(pontos[0]["mensagem"], "o contato não tem e-mail: recrutadores respondem por e-mail")

    def test_contato_br_sem_telefone(self):
        c = cv(contato=["ana@exemplo.com"], tecnicas={"formato": "br"})
        pontos = [p for p in conferir.conferir_ats(c, None) if p.get("tipo") == "contato"]
        self.assertEqual(len(pontos), 1)
        self.assertEqual(pontos[0]["nivel"], "conferir")
        self.assertEqual(pontos[0]["mensagem"], "o contato não tem telefone: no Brasil, recrutadores costumam ligar ou chamar no WhatsApp")

    def test_contato_br_completo(self):
        c = cv(contato=["ana@exemplo.com", "+55 11 90000-0000"], tecnicas={"formato": "br"})
        pontos = [p for p in conferir.conferir_ats(c, None) if p.get("tipo") == "contato"]
        self.assertEqual(pontos, [])

    def test_contato_us_sem_telefone(self):
        c = cv(contato=["ana@exemplo.com"], tecnicas={"formato": "us"})
        pontos = [p for p in conferir.conferir_ats(c, None) if p.get("tipo") == "contato"]
        self.assertEqual(pontos, [])

    def test_contato_vazio(self):
        c = cv(contato=[])
        pontos = [p for p in conferir.conferir_ats(c, None) if p.get("tipo") == "contato"]
        self.assertEqual(pontos, [])

    def test_rapido(self):
        inicio = time.time()
        conferir.conferir(cv(), PERFIL * 20, VAGA * 10)
        self.assertLess(time.time() - inicio, 5)


class TestConfissoes(unittest.TestCase):
    def test_acha_so_a_frase_que_confessa(self):
        r = conferir.confissoes("Tenho 5 anos com Scrum. Sendo transparente: não tenho a certificação X.")
        self.assertEqual(r, ["Sendo transparente: não tenho a certificação X"])

    def test_ingles_com_apostrofo_reto_e_curvo(self):
        self.assertEqual(len(conferir.confissoes("I don't have the certification yet.")), 1)
        self.assertEqual(len(conferir.confissoes("I don’t have the certification yet.")), 1)

    def test_frase_longa_tambem_conta(self):
        frase = ("Sendo transparente com vocês sobre a minha trajetória até aqui e sobre o que a vaga descreve, "
                 "não tenho a certificação X nem a ferramenta Y, mas trabalho com as equivalentes há anos")
        r = conferir.confissoes(frase + ".")
        self.assertEqual(r, [frase[:160]])

    def test_sem_confissao(self):
        self.assertEqual(conferir.confissoes("Trabalho com Scrum há anos."), [])

    def test_carta_ganha_ponto_de_confissao(self):
        r = conferir.conferir_carta("Trabalho com Scrum. Não tenho a certificação X.", "Scrum")
        pts = [p for p in r["pontos"] if p["tipo"] == "confissao"]
        self.assertEqual(len(pts), 1)
        self.assertEqual(pts[0]["nivel"], "conferir")

    def test_so_resposta_da_ia_ganha_mensagem(self):
        itens = [{"resposta": "Não tenho a certificação X."},
                 {"resposta": "Não tenho a certificação X.", "da_pessoa": True}]
        r = conferir.conferir_respostas(itens, "perfil")
        self.assertTrue(any("confessa uma falta" in m for m in r[0]["conferir"]))
        self.assertEqual(r[1]["conferir"], [])


if __name__ == "__main__":
    unittest.main()
