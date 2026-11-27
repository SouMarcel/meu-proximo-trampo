"""A espera de cada portal depois de um bloqueio, ajustável por <PORTAL>_ESPERA no .env (spec 064, FR-012)."""
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from fontes import _comum, fullstack, infojobs, jobgether, linkedin, mygreenhouse, vagascom  # noqa: E402

PORTAIS = ((linkedin, "LINKEDIN_ESPERA"), (infojobs, "INFOJOBS_ESPERA"), (vagascom, "VAGASCOM_ESPERA"),
           (jobgether, "JOBGETHER_ESPERA"), (fullstack, "FULLSTACK_ESPERA"), (mygreenhouse, "MYGREENHOUSE_ESPERA"))


def _env(valor: str):
    return mock.patch.object(_comum.segredos, "ler", return_value=valor)


class EsperaDoEnv(unittest.TestCase):
    def test_ausente_vale_o_padrao(self):
        with _env(""):
            r = _comum.espera_do_env("X_ESPERA")
        self.assertEqual(r, {"duracao": timedelta(minutes=360), "definida": False, "ajuste": ""})

    def test_valor_valido(self):
        with _env("90"):
            r = _comum.espera_do_env("X_ESPERA")
        self.assertEqual((r["duracao"], r["definida"], r["ajuste"]), (timedelta(minutes=90), True, ""))

    def test_abaixo_do_minimo(self):
        with _env("30"):
            r = _comum.espera_do_env("X_ESPERA")
        self.assertEqual(r["duracao"], timedelta(minutes=60))
        self.assertIn("abaixo do mínimo de 60 minutos", r["ajuste"])

    def test_acima_do_maximo(self):
        with _env("5000"):
            r = _comum.espera_do_env("X_ESPERA")
        self.assertEqual(r["duracao"], timedelta(minutes=2880))
        self.assertIn("acima do máximo de 2880 minutos", r["ajuste"])

    def test_nao_numerico_ou_infinito(self):
        for bruto in ("abc", "inf"):
            with self.subTest(bruto), _env(bruto):
                r = _comum.espera_do_env("X_ESPERA")
            self.assertEqual(r["duracao"], timedelta(minutes=360))
            self.assertTrue(r["definida"])
            self.assertIn("não é um número", r["ajuste"])

    def test_virgula_decimal_arredonda(self):
        with _env("120,4"):
            self.assertEqual(_comum.espera_do_env("X_ESPERA")["duracao"], timedelta(minutes=120))


class EsperaDosPortais(unittest.TestCase):
    def test_duracao_segue_a_variavel_de_cada_portal(self):
        for modulo, var in PORTAIS:
            with self.subTest(var):
                self.assertEqual(modulo.VAR_ESPERA, var)
                with mock.patch.object(_comum.segredos, "ler", side_effect=lambda n: "90" if n == var else ""):
                    self.assertEqual(modulo.duracao_espera(), timedelta(minutes=90))
                with _env(""):
                    self.assertEqual(modulo.duracao_espera(), timedelta(minutes=360))

    def test_espera_usa_a_duracao_atual(self):
        agora = datetime.now()
        for modulo, var in PORTAIS:
            with self.subTest(var), tempfile.TemporaryDirectory() as pasta:
                arq = Path(pasta) / "espera.json"
                with mock.patch.object(modulo, "ARQ_ESPERA", arq):
                    _comum.gravar_espera(arq, "código 429", agora - timedelta(hours=2))
                    with _env("60"):
                        self.assertIsNone(modulo.espera(agora))
                    with _env("360"):
                        self.assertIsNotNone(modulo.espera(agora))


if __name__ == "__main__":
    unittest.main()
