"""Elegibilidade das vagas do exterior sem IA (filtros.elegibilidade): um conjunto de anúncios com restrições
conhecidas e o resultado esperado (SC-002: 100% das impossíveis cortadas e nenhuma possível; SC-003: sinal de
patrocínio e de relocation em 100% das que oferecem)."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402

G = [filtros.GLOBAL]


def efet(**inter):
    return filtros.efetivos({"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True},
                             "internacional": {"ativo": True, "termos": ["data engineer"], "fontes": ["remotive"],
                                               **inter}})


def vaga(descricao="", restricao=None, remoto=True, **outros):
    return {"titulo": "Data Engineer", "empresa": "Acme", "descricao": descricao, "restricao_local": restricao,
            "remoto": remoto, "grupos": G, **outros}


# (nome, vaga, caixas da pessoa, corta?, trecho do motivo, sinais)
CASOS = [
    ("US only sem sponsor", vaga("We do not sponsor visas for this role.", "USA"), {"precisa_sponsor": True},
     True, "Exige autorização de trabalho em: Estados Unidos; não patrocina visto", []),
    ("US only com autorização", vaga("We do not sponsor visas.", "USA"), {"autorizacao_trabalho": ["Estados Unidos"]},
     False, "", []),
    ("frase de autorização", vaga("Applicants must be authorized to work in the United States."), {},
     True, "Só aceita quem está em: Estados Unidos", []),
    ("LATAM aceita", vaga("This role is open to candidates in LATAM."), {}, False, "", []),
    ("LATAM pelo campo", vaga("", "LATAM"), {}, False, "", []),
    ("Europa only", vaga("", "Europe"), {}, True, "Só aceita quem está em: Europa", []),
    ("Europa com cidadania", vaga("EU only.", None), {"autorizacao_trabalho": ["Portugal"]}, False, "", []),
    ("vários países, nenhum serve", vaga("", "Canada, USA"), {}, True, "Canadá ou Estados Unidos", []),
    ("vários países, um serve", vaga("", "USA, Brazil, Mexico"), {}, False, "", []),
    ("mundo todo", vaga("", "Anywhere in the World"), {}, False, "", []),
    ("presencial em Lisboa sem morar fora", vaga("Office in Lisbon.", None, remoto=False, local="Lisbon"), {},
     True, "não marcou que aceita morar fora", []),
    ("presencial em Lisboa aceitando Portugal", vaga("Office in Lisbon.", None, remoto=False, local="Lisbon"),
     {"aceita_mudar": True, "paises_mudanca": ["Portugal"]}, False, "", []),
    ("presencial em Londres aceitando só Portugal", vaga("", None, remoto=False, local="London"),
     {"aceita_mudar": True, "paises_mudanca": ["Portugal"]}, True, "você aceita morar em Portugal", []),
    ("híbrido lido pela IA", vaga("", None, modelo_trabalho="hibrido", local="Berlin"), {}, True, "Híbrido em Berlin", []),
    ("sponsor disponível", vaga("Visa sponsorship is available for the right candidate.", "USA"), {"precisa_sponsor": True},
     False, "", [filtros.SINAL_PATROCINIO]),
    ("relocation", vaga("We offer a relocation package to Lisbon.", None, remoto=False, local="Lisbon"),
     {"aceita_mudar": True}, False, "", [filtros.SINAL_RELOCATION]),
    ("ambíguo", vaga("Remote role. We do not offer health insurance. Great team."), {"precisa_sponsor": True},
     False, "", []),
    ("US only + we sponsor", vaga("This role is US only, but we sponsor visas for the right person.", None),
     {"precisa_sponsor": True}, False, "", [filtros.SINAL_PATROCINIO]),
    ("frase própria de restrição", vaga("Candidates must attend the quarterly onsite in Austin."),
     {"frases_restricao": ["quarterly onsite"]}, True, "“quarterly onsite” (frase da sua lista)", []),
    ("frase própria positiva", vaga("Brazilian candidates are welcome!"), {"frases_positivas": ["Brazilian candidates"]},
     False, "", ["Brazilian candidates"]),
    ("região aceita: só LATAM, vaga do mundo todo", vaga("", "Worldwide"), {"regioes": ["latam"]},
     True, "Vaga aberta a: Mundo todo", []),
    ("região aceita: mundo, vaga LATAM", vaga("", "LATAM"), {"regioes": ["mundo", "latam"]}, False, "", []),
    ("UK right to work", vaga("You must have the right to work in the UK."), {}, True, "Reino Unido", []),
    ("residência exigida", vaga("You must reside in Canada to be considered."), {}, True, "Canadá", []),
]


class TestElegibilidade(unittest.TestCase):
    def test_conjunto_de_anuncios(self):
        for nome, v, caixas, corta, trecho, sinais in CASOS:
            with self.subTest(nome):
                r = filtros.elegibilidade(v, efet(**caixas))
                self.assertEqual(bool(r["motivos"]), corta, r["motivos"])
                if trecho:
                    self.assertIn(trecho, " ".join(r["motivos"]))
                self.assertEqual(r["sinais"], sinais)

    def test_criterios_e_vaga_nacional(self):
        f = efet(precisa_sponsor=True)
        v = vaga("We do not sponsor visas.", "USA")
        self.assertIn("Exige autorização de trabalho em: Estados Unidos; não patrocina visto", filtros.criterios(v, f))
        # vaga nacional: nada da elegibilidade, mas os sinais valem
        nacional = {"titulo": "Analista", "descricao": "We do not sponsor visas. US only. Relocation package offered.",
                    "grupos": ["remoto"], "local": "São Paulo"}
        self.assertEqual(filtros.criterios(nacional, f), [])
        self.assertEqual(filtros.sinais(nacional, f), [filtros.SINAL_RELOCATION])
        # no exterior, o modelo de trabalho segue "aceito morar fora", não os modelos do Brasil
        hibrida = vaga("", None, modelo_trabalho="hibrido", local="Lisbon")
        self.assertEqual(filtros.criterios(hibrida, efet(aceita_mudar=True)), [])


if __name__ == "__main__":
    unittest.main()
