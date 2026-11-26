"""Regras da nota numa fonte só (spec 062): o pedido usa regras-da-nota.md, sem a seção Contato do perfil, com a parte
fixa idêntica até `## Vagas` e as regras de cada portal só para as vagas dele. Sem rede e sem IA."""
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import analise  # noqa: E402
import banco  # noqa: E402
import filtros  # noqa: E402
import relatos  # noqa: E402

PERFIL = """# Meu perfil de carreira

## Resumo
Analista de dados fictício, com Kanban e SQL.

## Contato
- E-mail: pessoa@exemplo.invalid
- Telefone: +55 00 00000-0000
- LinkedIn: exemplo.invalid/in/pessoa

## Idiomas
- Inglês — intermediário
"""


def vaga(vid, plataforma="Indeed", **campos):
    return {"id": vid, "plataforma": plataforma, "titulo": f"Analista {vid}", "empresa": "Empresa Alfa",
            "local": "Remoto", "url": f"https://exemplo.invalid/{vid}", "descricao": f"Texto da vaga {vid}.", **campos}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.perfil = self.tmp / "perfil.md"
        self.perfil.write_text(PERFIL, encoding="utf-8")
        cfg = {"fontes": ["indeed"], "termos": ["analista"], "localidade": {"pais": "Brasil"},
               "modelos": {"remoto": True}, "perfil": str(self.perfil)}
        (self.tmp / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(relatos, "bloco", return_value="")):
            p.start()
            self.addCleanup(p.stop)

    @staticmethod
    def fixo(pedido: str) -> str:
        return pedido[:pedido.index("## Vagas")]


class TestArquivo(unittest.TestCase):
    def test_secoes_e_tamanho(self):  # FR-001, SC-001
        texto = analise.REGRAS.read_text(encoding="utf-8")
        for titulo in ("## Resposta", "## Campos", "## Como dar a nota", "## Portais"):
            self.assertRegex(texto, rf"(?m)^{titulo}$")
        fixa, portais = analise.regras()
        self.assertLessEqual(len(fixa), 5500)
        self.assertNotIn("## Portais", fixa)
        self.assertIn("Gupy", portais)
        for proibido in ("no chat", "PY ", "vagas.py"):  # texto só para a IA
            self.assertNotIn(proibido, fixa)

    def test_portais_com_o_nome_das_fontes(self):  # contrato: ### <PLATAFORMA>
        import vagas
        nomes = {getattr(f, "PLATAFORMA", None) for f in vagas.FONTES.values()}
        for nome in analise.regras()[1]:
            self.assertIn(nome, nomes)

    def test_skill_aponta_para_o_arquivo(self):  # FR-002
        skill = analise.SKILL.read_text(encoding="utf-8")
        self.assertIn("regras-da-nota.md", skill)
        self.assertNotIn("`senioridade_origem`:", skill)  # o texto das regras não se repete na skill


class TestPedido(Base):
    def test_usa_as_regras_e_tira_o_contato(self):  # US1, FR-009
        pedido = analise.montar_pedido([vaga("a")])
        self.assertIn(analise.regras()[0], pedido)
        self.assertIn("Analista de dados fictício", pedido)
        self.assertIn("Inglês — intermediário", pedido)
        for dado in ("## Contato", "pessoa@exemplo.invalid", "+55 00 00000-0000", "exemplo.invalid/in/pessoa"):
            self.assertNotIn(dado, pedido)

    def test_perfil_sem_contato_vai_inteiro(self):
        self.perfil.write_text("# Perfil\n\n## Resumo\nAnalista fictício.\n", encoding="utf-8")
        self.assertIn("# Perfil\n\n## Resumo\nAnalista fictício.", analise.montar_pedido([vaga("a")]))

    def test_sem_contato_pela_funcao(self):
        self.assertEqual(analise._sem_contato("## A\nx\n## Contato\ne-mail\n## B\ny\n"), "## A\nx\n## B\ny\n")
        self.assertEqual(analise._sem_contato("## A\nx\n## Contato\ne-mail\n"), "## A\nx\n")
        self.assertEqual(analise._sem_contato("## A\nContato: x\n"), "## A\nContato: x\n")

    def test_comeco_identico(self):  # US4, FR-007
        a = analise.montar_pedido([vaga("a", "Indeed")])
        b = analise.montar_pedido([vaga("b", "Gupy"), vaga("c", "JobGether", descricao="")], frozenset({"c"}))
        self.assertEqual(self.fixo(a), self.fixo(b))

    def test_portal_so_na_vaga_dele(self):
        sem_gupy = analise.montar_pedido([vaga("a", "Indeed")])
        com_gupy = analise.montar_pedido([vaga("a", "Indeed"), vaga("b", "Gupy")])
        self.assertNotIn("Sobre o portal Gupy:", sem_gupy)
        self.assertIn("Sobre o portal Gupy:", com_gupy)
        self.assertGreater(com_gupy.index("### id: a"), com_gupy.index("Sobre o portal Gupy:"))

    def test_nota_sem_descricao_depois_das_vagas(self):
        pedido = analise.montar_pedido([vaga("c", "JobGether", descricao="")], frozenset({"c"}))
        self.assertGreater(pedido.index("dê sempre a nota"), pedido.index("## Vagas"))

    def test_tipo_do_portal_na_vaga(self):
        self.assertIn("Tipo (do portal): PJ • Senior", analise.montar_pedido([vaga("a", "Nerdin", tipo="PJ • Senior")]))

    def test_sem_arquivo_de_regras(self):
        with mock.patch.object(analise, "REGRAS", self.tmp / "nao-existe.md"):
            pedido = analise.montar_pedido([vaga("a")])
        self.assertIn(analise.REGRAS_MINIMAS, pedido)
        self.assertIn("### id: a", pedido)

    def test_menor_que_antes(self):  # SC-001, com perfil e vaga fictícios do mesmo tamanho da medição
        self.perfil.write_text(PERFIL + "\n## Experiência\n" + "- Fiz uma entrega fictícia.\n" * 260, encoding="utf-8")
        pedido = analise.montar_pedido([vaga("a", descricao="Texto fictício da vaga. " * 280)])
        self.assertEqual(len(re.findall(r"^### id: ", pedido, re.M)), 1)
        self.assertLessEqual(len(pedido), 20000)


if __name__ == "__main__":
    unittest.main()
