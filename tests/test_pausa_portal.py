"""Pausa por portal no .env (<NOME>_PAUSA, spec 026): padrão sem a variável, valor, mínimo, máximo e valor
inválido; o aviso do começo da busca por portal e junto na busca; o fim da espera com a data quando passa de hoje."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402
import segredos  # noqa: E402
import vagas  # noqa: E402
from fontes import _comum, infojobs, linkedin, nerdin, vagascom  # noqa: E402

CFG = {"termos": ["analista de dados"], "localidade": {"pais": "Brasil", "estado": "SP", "cidade": "São Paulo",
                                                      "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "janela_horas": 168,
       "internacional": {"ativo": False}}


class Base(unittest.TestCase):
    def env(self, **valores):
        p = mock.patch.object(segredos, "ler", side_effect=lambda nome: valores.get(nome, ""))
        p.start()
        self.addCleanup(p.stop)
        _comum.esquecer()
        self.addCleanup(_comum.esquecer)


class TestPausaDoEnv(Base):
    def test_padrao_sem_a_variavel(self):  # FR-016: sem variável, nada muda
        self.env()
        self.assertEqual(infojobs.pausa(), {"faixa": (3.0, 7.0), "definida": False, "ajuste": ""})
        self.assertEqual(vagascom.pausa()["faixa"], (3.0, 7.0))
        self.assertEqual(nerdin.pausa()["faixa"], (3.0, 3.0))
        self.assertEqual(linkedin.pausa()["faixa"], (3.0, 7.0))
        self.assertIsNone(infojobs.aviso_pausa(4))

    def test_valores(self):  # FR-013
        casos = {"10": (10, 14), "4,5": (4.5, 8.5), '"4,5"': (4.5, 8.5), "1": (3, 7), "500": (60, 64), "abc": (3, 7)}
        for valor, faixa in casos.items():
            self.env(INFOJOBS_PAUSA=valor.strip('"'))
            self.assertEqual(infojobs.pausa()["faixa"], faixa, valor)
        self.env(INFOJOBS_PAUSA="1")
        self.assertIn("INFOJOBS_PAUSA abaixo do mínimo de 3 segundos", infojobs.pausa()["ajuste"])
        self.env(INFOJOBS_PAUSA="abc")
        self.assertIn("não é um número", infojobs.pausa()["ajuste"])

    def test_cada_portal_com_a_sua(self):  # US4: a variável de um portal não mexe nos outros
        self.env(INFOJOBS_PAUSA="10", NERDIN_PAUSA="5")
        self.assertEqual(infojobs.pausa()["faixa"], (10, 14))
        self.assertEqual(nerdin.pausa()["faixa"], (5, 5))  # a Nerdin não sorteia
        self.assertEqual(vagascom.pausa()["faixa"], (3.0, 7.0))
        self.assertFalse(linkedin.pausa()["definida"])

    def test_pausa_usada_entre_os_pedidos(self):
        self.env(INFOJOBS_PAUSA="10")
        infojobs._estado["ultimo"] = None
        with mock.patch.object(_comum.random, "uniform", return_value=12.0) as sorteio, \
                mock.patch.object(_comum.time, "sleep"):
            infojobs._pausar()
            infojobs._pausar()
        sorteio.assert_called_with(10.0, 14.0)


class TestAvisos(Base):
    def test_aviso_por_portal(self):
        self.env(INFOJOBS_PAUSA="10", NERDIN_PAUSA="5")
        self.assertEqual(infojobs.aviso_pausa(2), "InfoJobs: pausa de 10 a 14 s entre os pedidos (INFOJOBS_PAUSA), "
                                                  "até cerca de 6 min só de pausa no InfoJobs.")  # (2 + 30) × 12 s
        self.assertEqual(nerdin.aviso_pausa(1), "Nerdin: pausa de 5 s entre os pedidos (NERDIN_PAUSA), "
                                                "até cerca de 3 min só de pausa na Nerdin.")  # (5 + 30) × 5 s
        self.assertIsNone(infojobs.aviso_pausa(0))

    def test_aviso_na_busca_junta_os_portais(self):
        self.env(INFOJOBS_PAUSA="10", NERDIN_PAUSA="5")
        f = filtros.efetivos(CFG)
        aviso = vagas.aviso_pausa(f, ["indeed", "nerdin", "infojobs", "vagascom"])
        self.assertIn("Nerdin: pausa de 5 s", aviso)
        self.assertIn("InfoJobs: pausa de 10 a 14 s", aviso)
        self.assertNotIn("Vagas.com", aviso)  # sem VAGASCOM_PAUSA, sem aviso
        self.assertIsNone(vagas.aviso_pausa(f, ["indeed", "vagascom"]))
        with mock.patch.object(infojobs, "espera", return_value={"ate": "2026-10-24T10:00", "motivo": "x"}):
            self.assertNotIn("InfoJobs", vagas.aviso_pausa(f, ["nerdin", "infojobs"]))  # em espera: sem pedidos


class TestAteQuando(unittest.TestCase):
    def test_data_so_quando_passa_de_hoje(self):
        hoje = date(2026, 10, 23)
        self.assertEqual(_comum.ate_quando("2026-10-23T17:00", hoje), "17:00")
        self.assertEqual(_comum.ate_quando("2026-10-15T17:00", hoje), "17:00")
        self.assertEqual(_comum.ate_quando("2026-10-24T09:30", hoje), "24/10 09:30")
        self.assertEqual(_comum.ate_quando("quebrado", hoje), "")


if __name__ == "__main__":
    unittest.main()
