"""Regiões e continentes (spec 047): o catálogo, a leitura do texto da vaga, a sobreposição, as regiões aceitas, a
autorização por região, a consulta por região (só no LinkedIn), o perfil e a revisão das vagas antigas, sem rede."""
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import banco  # noqa: E402
import filtros  # noqa: E402
import primeiros_passos as pp  # noqa: E402
import vagas  # noqa: E402
from fontes import FONTES, linkedin  # noqa: E402

G = [filtros.GLOBAL]
CONTINENTES = ("América do Norte", "América Central", "América do Sul", "Europa", "Ásia", "Oceania", "África")


def cfg(**inter):
    return {"termos": ["analista"], "localidade": {"pais": "Brasil"}, "modelos": {"remoto": True},
            "fontes": ["indeed", "linkedin"],
            "internacional": {"ativo": True, "termos": ["data engineer"], "fontes": ["remotive"], **inter}}


def efet(**inter):
    return filtros.efetivos(cfg(**inter))


def vaga(descricao="", restricao=None, **outros):
    return {"titulo": "Data Engineer", "empresa": "Acme", "descricao": descricao, "restricao_local": restricao,
            "remoto": True, "grupos": G, **outros}


class TestCatalogo(unittest.TestCase):
    def test_cada_pais_num_continente(self):
        for pais in filtros.PAISES:
            with self.subTest(pais):
                dentro = [c for c in CONTINENTES if pais in filtros.REGIOES_PAISES[c]]
                self.assertEqual(len(dentro), 1, dentro)
        todos = set().union(*filtros.REGIOES_PAISES.values())
        self.assertLessEqual(todos, set(filtros.PAISES))  # nenhum país fora da lista da ferramenta

    def test_regioes_dentro_de_regioes(self):
        r = filtros.REGIOES_PAISES
        self.assertEqual(len(r["União Europeia"]), 27)
        self.assertLess(r["União Europeia"], r["Europa"])
        self.assertLess(r["América Latina"], r["Américas"])
        self.assertLess(r["América do Sul"], r["América Latina"])
        self.assertNotIn("Reino Unido", r["União Europeia"])
        self.assertEqual(filtros.REGIOES_MARCAVEIS, list(filtros.REGIAO_EN))
        self.assertEqual(len(filtros.REGIOES_MARCAVEIS), 10)

    def test_leitura_do_texto(self):
        casos = {"Remote - Oceania": "Oceania", "APAC": "Ásia-Pacífico", "Asia-Pacific": "Ásia-Pacífico",
                 "EMEA": "EMEA", "EU only": "União Europeia", "European Union": "União Europeia",
                 "South America": "América do Sul", "Central America": "América Central", "Asia": "Ásia",
                 "Africa": "África", "South Africa": "África do Sul", "Malaysia": "Malásia", "Europe": "Europa",
                 "Latin America": "América Latina", "Middle East": "Oriente Médio", "Worldwide": "mundo todo"}
        for texto, esperado in casos.items():
            with self.subTest(texto):
                self.assertEqual(filtros.pais_do_local(texto), esperado)

    def test_lugar_pt(self):
        for nome in ("União Europeia", "uniao europeia", "European Union", "EUROPEAN UNION"):
            self.assertEqual(filtros.lugar_pt(nome), "União Europeia")
        self.assertEqual(filtros.lugar_pt("Oceania"), "Oceania")
        self.assertEqual(filtros.lugar_pt("asia"), "Ásia")
        self.assertEqual(filtros.lugar_pt("Portugal"), "Portugal")
        self.assertEqual(filtros.lugar_pt("Germany"), "Alemanha")
        self.assertIsNone(filtros.lugar_pt("Atlântida"))
        self.assertIsNone(filtros.lugar_pt("EMEA"))  # só no texto da vaga, não nos campos

    def test_sobreposicao(self):
        s = filtros.sobrepoe
        self.assertTrue(s("Europa", "União Europeia"))
        self.assertTrue(s("Alemanha", "União Europeia"))
        self.assertTrue(s("América Latina", "Américas"))
        self.assertTrue(s("mundo todo", "Oceania"))
        self.assertTrue(s("Brasil", "Brasil"))
        self.assertTrue(s("Ásia-Pacífico", "Oceania"))
        self.assertFalse(s("Ásia", "Europa"))
        self.assertFalse(s("Reino Unido", "União Europeia"))
        self.assertFalse(s("Estados Unidos", "Brasil"))


class TestConfig(unittest.TestCase):
    def test_efetivos(self):
        f = efet(regioes=["brasil", "mundo", "europa", "lua", "europa"], paises=["European Union", "Brasil", "Japão"],
                 paises_mudanca=["Oceania", "Atlântida"], autorizacao_trabalho=["Portugal", "uniao europeia"])
        it = f["internacional"]
        self.assertEqual(it["regioes"], ["pais", "europa"])
        self.assertEqual(it["paises"], ["União Europeia", "Japão"])  # o país da pessoa sai
        self.assertEqual(it["paises_mudanca"], ["Oceania"])
        self.assertEqual(it["autorizacao_trabalho"], ["Portugal", "União Europeia"])
        self.assertEqual(filtros.regioes_aceitas(f), ["Brasil", "Europa"])

    def test_validar(self):
        base = {**cfg(), "internacional": {**cfg()["internacional"], "paises": ["Japão"]}}
        ok = filtros.validar({**base, "internacional": {**base["internacional"], "regioes": ["brasil", "mundo", "oceania"],
                                                        "paises": ["Europa", "América do Sul"],
                                                        "autorizacao_trabalho": ["União Europeia"]}})
        self.assertEqual(ok["internacional"]["regioes"], ["pais", "oceania"])
        self.assertEqual(ok["internacional"]["paises"], ["Europa", "América do Sul"])  # a região com o Brasil fica
        self.assertEqual(ok["internacional"]["autorizacao_trabalho"], ["União Europeia"])
        for campo, valor, msg in (("regioes", ["lua"], "região"),
                                  ("autorizacao_trabalho", ["Atlântida"], "país ou região desconhecido")):
            with self.subTest(campo), self.assertRaisesRegex(ValueError, msg):
                filtros.validar({**base, "internacional": {**base["internacional"], campo: valor}})

    def test_opcoes(self):
        op = filtros.opcoes()
        self.assertEqual(list(op["regioes"])[0], "pais")
        self.assertNotIn("mundo", op["regioes"])
        self.assertIn("União Europeia", op["regioes_lugar"])
        self.assertEqual(op["fontes_regiao"], ["linkedin"])

    def test_criterios_para_a_ia(self):
        texto = " ".join(filtros.criterios_extra(efet(regioes=["pais", "oceania"],
                                                      autorizacao_trabalho=["União Europeia"])))
        self.assertIn("regiões aceitas: Brasil, Oceania", texto)
        self.assertIn("autorização de trabalho em: União Europeia", texto)


class TestAutorizacao(unittest.TestCase):
    def corta(self, v, **inter):
        return filtros.elegibilidade(v, efet(**inter))["motivos"]

    def test_uniao_europeia(self):
        ue = {"autorizacao_trabalho": ["União Europeia"]}
        self.assertEqual(self.corta(vaga("Candidates must be based in Germany."), **ue), [])
        self.assertEqual(self.corta(vaga("You must be authorized to work in the EU."), **ue), [])
        self.assertTrue(self.corta(vaga("You must have the right to work in the UK. We do not sponsor visas."), **ue))
        self.assertEqual(self.corta(vaga("", "EU only"), autorizacao_trabalho=["Portugal"]), [])
        # sem autorização, "só Alemanha" continua cortada
        self.assertIn("Alemanha", " ".join(self.corta(vaga("Candidates must be based in Germany."))))

    def test_mudanca_por_regiao(self):
        hibrida = vaga("", None, modelo_trabalho="hibrido", local="Lisbon")
        self.assertEqual(self.corta(hibrida, aceita_mudar=True, paises_mudanca=["Europa"]), [])
        self.assertTrue(self.corta(hibrida, aceita_mudar=True, paises_mudanca=["Oceania"]))


class TestBuscaPorRegiao(unittest.TestCase):
    def plano(self, **inter):
        return filtros.consultas(efet(**inter))

    def test_consultas(self):
        plano = self.plano(paises=["União Europeia", "Japão"], fontes=[])
        ue = [c for c in plano if c["grupo"] == "internacional:União Europeia"]
        self.assertEqual(len(ue), 1)
        self.assertEqual((ue[0]["pais"], ue[0]["regiao"], ue[0]["pais_nome"]),
                         (None, "European Union", "União Europeia"))
        jp = [c for c in plano if c["grupo"] == "internacional:Japão"]
        self.assertEqual((jp[0]["pais"], jp[0].get("regiao")), ("japan", None))

    def test_quem_atende(self):
        c = self.plano(paises=["Oceania"])
        regiao = next(x for x in c if x.get("regiao"))
        self.assertTrue(vagas.atende(FONTES["linkedin"], regiao))
        for nome in ("indeed", "jobgether", "remotive", "gupy", "ats"):
            with self.subTest(nome):
                self.assertFalse(vagas.atende(FONTES[nome], regiao))

    def test_contagem(self):
        sem = self.plano(fontes=[], termos=["data engineer", "data analyst"])
        com = self.plano(fontes=[], termos=["data engineer", "data analyst"], paises=["União Europeia"])
        self.assertEqual(vagas.contar_consultas(com, ["indeed"]) - vagas.contar_consultas(sem, ["indeed"]), 0)
        self.assertEqual(vagas.contar_consultas(com, ["linkedin"]) - vagas.contar_consultas(sem, ["linkedin"]), 1)

    def test_parametros_do_linkedin(self):
        regiao = next(x for x in self.plano(paises=["União Europeia"]) if x.get("regiao"))
        self.assertEqual(linkedin.parametros(regiao, 24)["location"], "European Union")

    def test_area_da_vaga_da_regiao(self):
        f = efet(paises=["União Europeia"])
        g = ["internacional:União Europeia"]
        self.assertEqual(filtros.area_da_vaga({"grupos": g, "local": "Berlin, Germany"}, f),
                         ("internacional", "Alemanha"))
        self.assertEqual(filtros.area_da_vaga({"grupos": g, "local": "São Paulo, Brazil"}, f), ("nacional", None))
        self.assertEqual(filtros.area_da_vaga({"grupos": g, "local": "Remote"}, f),
                         ("internacional", "União Europeia"))
        # consulta de país continua como antes
        self.assertEqual(filtros.area_da_vaga({"grupos": ["internacional:Japão"], "local": "Remote"}, f),
                         ("internacional", "Japão"))


class TestPerfil(unittest.TestCase):
    def test_linha_e_proposta(self):
        resp = {pp.EXTERIOR: True, "exterior_remoto": True, "exterior_paises": ["Europa", "Estados Unidos", "Atlântida"],
                "cargos_alvo": ["Analista"], "cargos_alvo_en": ["Data Analyst"]}
        r = pp.propor_filtros(resp, cfg())
        self.assertEqual(r["filtros"]["internacional"]["paises"], ["Europa", "Estados Unidos"])
        self.assertTrue(any("Atlântida" in a for a in r["avisos"]), r["avisos"])
        pergunta = next(p for p in pp.PERGUNTAS if p["id"] == "exterior_paises")
        self.assertIn("países ou regiões", pergunta["texto"])


class TestRevisao(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "config.json").write_text(json.dumps(cfg(regioes=["brasil", "americas"])), encoding="utf-8")
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json")):
            p.start()
            self.addCleanup(p.stop)
        base = {"titulo": "Data Engineer", "empresa": "Acme", "plataforma": "Remotive", "url": "https://x.invalid/1",
                "triagem": "fora", "triada_em": "2026-11-01", "area": "internacional", "pais_vaga": "América Latina",
                "grupos": G, "restricao_local": "LATAM", "descricao": "", "encontrada_em": "2026-11-01"}
        antigo = "Vaga aberta a: América Latina; você aceita Brasil e Américas"
        banco.inserir_vagas([
            {**base, "id": "so-regiao", "motivo_fora": [antigo]},
            {**base, "id": "com-moeda", "motivo_fora": [antigo, "Paga em ARS; fora do seu país você aceita USD"]},
            {**base, "id": "outro", "motivo_fora": ["Vaga em espanhol; você aceita português e inglês"]},
        ])

    def rodar(self, gravar):
        with redirect_stdout(io.StringIO()) as saida:
            r = banco.rever_regioes(gravar)
        return r, saida.getvalue()

    def test_sem_gravar_nao_muda(self):
        r, _ = self.rodar(False)
        self.assertEqual(sorted(x["id"] for x in r["mudam"]), ["com-moeda", "so-regiao"])
        self.assertEqual(r["voltam"], 1)
        self.assertEqual(banco.obter("so-regiao")["triagem"], "fora")

    def test_gravar(self):
        banco.rever_regioes(True)
        volta = banco.obter("so-regiao")
        self.assertEqual(volta["triagem"], "pendente")
        self.assertNotIn("motivo_fora", volta)
        self.assertNotIn("triada_em", volta)
        moeda = banco.obter("com-moeda")
        self.assertEqual(moeda["triagem"], "fora")
        self.assertEqual(moeda["motivo_fora"], ["Paga em ARS; fora do seu país você aceita USD"])
        self.assertEqual(banco.obter("outro")["motivo_fora"], ["Vaga em espanhol; você aceita português e inglês"])

    def test_comando(self):
        with redirect_stdout(io.StringIO()) as saida, mock.patch.object(sys, "argv", ["banco.py", "regioes"]):
            self.assertEqual(banco.main(), 0)
        texto = saida.getvalue()
        self.assertIn("2 vaga(s) perderiam", texto)
        self.assertIn("1 voltariam", texto)
        self.assertIn("Nada foi gravado", texto)
        self.assertEqual(banco.obter("so-regiao")["triagem"], "fora")


if __name__ == "__main__":
    unittest.main()
