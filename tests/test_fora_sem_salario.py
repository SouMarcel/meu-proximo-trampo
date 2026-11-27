"""O "fora dos critérios" escrito pela IA não tira a vaga por salário ou moeda: a moeda aceita e o salário mínimo são
conferidos pelos campos. Textos fictícios, no formato das respostas reais."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
import filtros  # noqa: E402


class TestSemSalario(unittest.TestCase):
    def test_so_salario_some(self):
        for texto in ("Salário não especificado (valor desconhecido)", "salario nao informado",
                      "Salary not disclosed", "Paga em EUR", "Remuneração abaixo da pretensão (R$ 4.000)",
                      "vaga internacional com salário em GBP (não USD/EUR)."):
            with self.subTest(texto=texto):
                self.assertEqual(filtros.sem_salario(texto), "")

    def test_mantem_o_que_nao_e_salario(self):
        self.assertEqual(
            filtros.sem_salario("Localização Cidade A, usuário em Cidade B; salario nao informado"),
            "Localização Cidade A, usuário em Cidade B")
        self.assertEqual(
            filtros.sem_salario("Vaga em Cidade A, não remota, e sem confirmação de salário em USD/EUR."),
            "Vaga em Cidade A, não remota")
        self.assertEqual(filtros.sem_salario("Exige residência no Reino Unido; salário em GBP"),
                         "Exige residência no Reino Unido")
        self.assertEqual(filtros.sem_salario("Exige autorização de trabalho nos EUA"),
                         "Exige autorização de trabalho nos EUA")

    def test_vazio_ou_estranho(self):
        for v in (None, "", True, 0):
            self.assertEqual(filtros.sem_salario(v if not isinstance(v, bool) else ""), "")

    def test_criterios_nao_tira_por_salario(self):
        f = filtros.efetivos({"termos": ["analista"]})
        vaga = {"titulo": "Analista", "empresa": "Empresa X", "local": "Brasil", "remoto": True,
                "fora_dos_criterios": "Salário não especificado (valor desconhecido)"}
        self.assertEqual(filtros.criterios(vaga, f), [])
        vaga["fora_dos_criterios"] = "Presencial em Cidade A; salário não informado"
        self.assertEqual(filtros.criterios(vaga, f), ["Presencial em Cidade A"])


if __name__ == "__main__":
    unittest.main()
