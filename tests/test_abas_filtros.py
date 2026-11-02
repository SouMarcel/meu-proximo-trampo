"""Testes da lista "Próximos a mapear" do painel Filtros da busca (spec 043): a forma de cada item e a guarda de que
um portal que já está na busca saiu da lista."""
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import filtros  # noqa: E402


class TestPortaisAMapear(unittest.TestCase):
    def test_forma_dos_itens(self):
        lista = filtros.opcoes()["portais_a_mapear"]
        self.assertIsInstance(lista, list)
        for p in lista:
            self.assertTrue(p["nome"].strip(), p)
            self.assertIn(p["situacao"], ("em_estudo", "nao_deu"), p)
            if p["situacao"] == "nao_deu":
                self.assertTrue(p["motivo"].strip(), f"{p['nome']}: o portal que não deu precisa do motivo")

    def test_portal_da_busca_sai_da_lista(self):
        # o portal que entra na busca sai da lista (docs/novo-portal.md)
        na_busca = {filtros.sem_acento(r) for d in (filtros.FONTES_NAC, filtros.FONTES_LOGIN, filtros.FONTES_INT)
                    for r in d.values()}
        for p in filtros.opcoes()["portais_a_mapear"]:
            self.assertNotIn(filtros.sem_acento(p["nome"]), na_busca, f"{p['nome']} já está na busca")

    def test_opcoes_devolve_copia(self):
        filtros.opcoes()["portais_a_mapear"][0]["nome"] = "mudado"
        self.assertNotEqual(filtros.opcoes()["portais_a_mapear"][0]["nome"], "mudado")


if __name__ == "__main__":
    unittest.main()
