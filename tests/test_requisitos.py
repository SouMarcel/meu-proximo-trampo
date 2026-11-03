"""O que as vagas pedem (spec 045), sem rede e sem IA de verdade: a validação dos requisitos (experiência não é
habilidade), as chaves, a seleção, o resumo, a leitura do perfil e a comparação com ele, a gravação que não mexe na
nota, a leitura avulsa em segundo plano (lotes, parar, falha, retomar, vaga suspeita sozinha), as rotas e o terminal."""
import contextlib
import http.client
import io
import json
import re
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import analise  # noqa: E402
import banco  # noqa: E402
import filtros  # noqa: E402
import ia  # noqa: E402
import requisitos as R  # noqa: E402

CFG = {"fontes": ["indeed"], "termos": ["analista"], "localidade": {"pais": "Brasil"},
       "modelos": {"remoto": True, "hibrido": True, "presencial": True}, "janela_horas": 168}

PERFIL = """# Meu perfil de carreira

## Resumo
Analista de dados que organiza o trabalho com Kanban.

## Experiência
### Analista — Empresa Fictícia (01/2020–atual)
- Montei relatórios em Excel para a diretoria.

## Certificações
- PSM I (em preparação)
- Treinamento em Scrum (Escola Fictícia) — Gestão Ágil (40h, concluída)

## Habilidades e ferramentas (com nível)
- Ferramenta — nível (ex.: Jira — avançado; SQL — consultas básicas)
- Jira — avançado
- SQL — consultas básicas
- Python/Pandas — profissional
- Looker — profissional
- Stack geral: Confluence, Trello, Jira
- C — básico

## Idiomas
- Inglês — intermediário
"""


def vaga(vid, **campos):
    return {"id": vid, "origem": "busca", "plataforma": "Falsa", "titulo": f"Analista {vid}", "empresa": "Empresa Alfa",
            "local": "Remoto", "url": f"https://exemplo.invalid/{vid}", "triagem": "pendente",
            "descricao": f"Texto da vaga {vid}.", "analise_status": "feita", "aderencia": 70, "resumo": "Bate.",
            "encaixe": ["SQL"], "lacunas": ["Power BI"], "alertas": [], "encontrada_em": "2026-11-01", **campos}


def req(*habilidades, cert=(), anos=None, formacao=None, idiomas=()):
    r = {"habilidades": [h if isinstance(h, dict) else {"nome": h, "tipo": "tecnica", "exigida": False}
                         for h in habilidades],
         "certificacoes": [c if isinstance(c, dict) else {"nome": c, "tipo": "certificacao", "exigida": False}
                           for c in cert],
         "idiomas": list(idiomas), "lido_em": "2026-11-03"}
    if anos is not None:
        r["experiencia"] = {"anos": anos, "em": "a área", "frase": f"{anos} anos"}
    if formacao:
        r["formacao"] = formacao
    return r


def gravar(*docs):
    with banco.escrita() as con:
        for d in docs:
            banco._gravar(con, d["id"], d)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "config.json").write_text(json.dumps(CFG), encoding="utf-8")
        for p in (mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(R, "perfil_texto", return_value=PERFIL)):
            p.start()
            self.addCleanup(p.stop)

    def ia_falsa(self, responder=None, ligada=True):
        """IA ligada; por padrão devolve "SQL" e 3 anos para cada vaga do pedido. Guarda os pedidos."""
        self.pedidos_ia = []

        def padrao(pedido, **_):
            ids = re.findall(r"^### id: (\S+)$", pedido, re.M)
            return json.dumps([{"id": i, "requisitos": {"habilidades": [{"nome": "SQL", "tipo": "tecnica",
                                                                         "exigida": True}],
                                                        "experiencia": {"anos": 3, "em": "dados", "frase": "3 anos"}}}
                               for i in ids])

        def chamar(pedido, **kw):
            self.pedidos_ia.append(pedido)
            return (responder or padrao)(pedido, **kw)
        for p in (mock.patch.object(ia, "responder", side_effect=chamar),
                  mock.patch.object(ia, "disponivel", return_value=ligada),
                  mock.patch.object(ia, "escolha_efetiva", return_value={"provedor": "openrouter", "modelo": "m:free"}),
                  mock.patch.object(ia, "modelo_efetivo", return_value="m:free")):
            p.start()
            self.addCleanup(p.stop)


# ---------------------------------------------------------------- validação e chaves

class TestRespostaDaIA(unittest.TestCase):
    def test_lista_json_tolerante(self):
        L = analise.lista_json
        self.assertEqual(L('[{"id": "a"}]'), [{"id": "a"}])
        self.assertEqual(L('```json\n[{"id": "a"}, {"id": "b"},]\n```'), [{"id": "a"}, {"id": "b"}])
        self.assertEqual(L('Aqui está: [{"id": "a", "x": [1]}, {"id": "b", "x": [2'), [{"id": "a", "x": [1]}])
        self.assertEqual(L('{"id": "a"}'), [{"id": "a"}])
        self.assertIsNone(L("não sei"))
        self.assertIsNone(L(""))

    def test_analise_aceita_resposta_em_bloco_de_codigo(self):
        resposta = '```json\n[{"id": "a", "aderencia": 66, "resumo": "Ok.",}]\n```'
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(banco, "ARQUIVO", Path(tmp) / "banco.db"), \
                mock.patch.object(filtros, "CONFIG", Path(tmp) / "config.json"), \
                mock.patch.object(ia, "disponivel", return_value=True), \
                mock.patch.object(ia, "escolha_efetiva", return_value={"provedor": "openrouter", "modelo": "m:free"}), \
                mock.patch.object(ia, "modelo_efetivo", return_value="m:free"), \
                mock.patch.object(ia, "responder", return_value=resposta):
            (Path(tmp) / "config.json").write_text(json.dumps(CFG), encoding="utf-8")
            gravar(vaga("a", analise_status="pendente", aderencia=None))
            ok, _ = analise.analisar([banco.obter("a")])
            self.assertEqual((ok, banco.obter("a")["aderencia"]), (["a"], 66))


class TestValidar(unittest.TestCase):
    def test_experiencia_nao_e_habilidade(self):  # FR-002, SC-002
        r = R.validar({"habilidades": [{"nome": "5+ anos de experiência"}, {"nome": "Experiência com SQL"},
                                       {"nome": "Inglês avançado"}, {"nome": "Conhecimento em Excel"},
                                       {"nome": "Vivência com APIs"}, {"nome": "3 years of Python"},
                                       {"nome": "Gestão de projetos", "exigida": True}],
                       "certificacoes": [{"nome": "Experiência em auditoria"}, {"nome": "PMP"}]})
        self.assertEqual([h["nome"] for h in r["habilidades"]], ["Gestão de projetos"])
        self.assertTrue(r["habilidades"][0]["exigida"])
        self.assertEqual([c["nome"] for c in r["certificacoes"]], ["PMP"])

    def test_tipos_limites_e_repeticao(self):
        r = R.validar({"habilidades": [{"nome": "Power BI", "tipo": "outra"}, {"nome": "PowerBI", "exigida": True},
                                       {"nome": "Comunicação", "tipo": "comportamental"}, "Jira", {"nome": ""}, 7]
                       + [{"nome": f"Ferramenta {i}"} for i in range(40)],
                       "certificacoes": [{"nome": "Curso de SQL", "tipo": "x"}]})
        self.assertEqual(len(r["habilidades"]), R.MAX_HABILIDADES)
        self.assertEqual(r["habilidades"][0], {"nome": "Power BI", "tipo": "tecnica", "exigida": True})
        self.assertEqual(r["habilidades"][1]["tipo"], "comportamental")
        self.assertEqual(r["habilidades"][2]["nome"], "Jira")
        self.assertEqual(r["certificacoes"][0]["tipo"], "curso")

    def test_experiencia_formacao_e_idiomas(self):
        r = R.validar({"experiencia": {"anos": "5+", "em": "projetos", "frase": "5+ anos em projetos"},
                       "formacao": {"nivel": "graduacao", "areas": ["Administração", "administracao", "Engenharia"]},
                       "idiomas": [{"idioma": "English", "nivel": "avancado"}, {"idioma": "inglês", "nivel": "basico"},
                                   {"idioma": "Espanhol", "nivel": "nenhum"}]})
        self.assertEqual(r["experiencia"]["anos"], 5)
        self.assertEqual(r["formacao"]["areas"], ["Administração", "Engenharia"])
        self.assertEqual(r["idiomas"], [{"idioma": "Inglês", "nivel": "fluente", "frase": ""}])
        sem = R.validar({"experiencia": {"anos": 80}, "formacao": {"nivel": "phd"}})
        self.assertNotIn("experiencia", sem)  # sem anos válidos e sem frase
        self.assertNotIn("formacao", sem)
        nulo = R.validar({"experiencia": {"anos": None, "frase": "experiência sólida"}})
        self.assertIsNone(nulo["experiencia"]["anos"])

    def test_objeto_ausente_e_provedor(self):
        self.assertIsNone(R.validar(None))
        self.assertIsNone(R.validar([]))
        r = R.validar({}, "gemini", "g-2")
        self.assertEqual((r["habilidades"], r["provedor"], r["modelo"]), ([], "gemini", "g-2"))
        self.assertNotIn("provedor", R.validar({}, "Provedor Ruim!"))

    def test_chave(self):
        self.assertEqual(R.chave("Power BI"), R.chave("powerbi"))
        self.assertEqual(R.chave("Gestão de Projetos"), R.chave("gestao de projetos"))
        self.assertNotEqual(R.chave("C#"), R.chave("C++"))
        self.assertEqual(R.chave("Node.js"), R.chave("NodeJS"))


# ---------------------------------------------------------------- gravação

class TestGravacao(Base):
    def test_analise_grava_os_requisitos(self):
        gravar(vaga("a", analise_status="pendente", aderencia=None))
        ok, _ = banco.aplicar_analises([{"id": "a", "aderencia": 80, "analise_provedor": "gemini",
                                         "analise_modelo": "g-2", "requisitos": req("SQL", anos=2)}])
        self.assertEqual(ok, ["a"])
        r = banco.obter("a")["requisitos"]
        self.assertEqual(([h["nome"] for h in r["habilidades"]], r["provedor"], r["experiencia"]["anos"]),
                         (["SQL"], "gemini", 2))

    def test_requisito_invalido_nao_derruba_a_nota(self):
        gravar(vaga("a", analise_status="pendente", aderencia=None))
        ok, _ = banco.aplicar_analises([{"id": "a", "aderencia": 80, "requisitos": {"habilidades": "texto solto"}}])
        self.assertEqual(ok, ["a"])
        self.assertEqual((banco.obter("a")["aderencia"], banco.obter("a")["requisitos"]["habilidades"]), (80, []))

    def test_aplicar_requisitos_so_muda_o_campo(self):  # FR-005, SC-003
        gravar(vaga("a", triagem="seguir", etapa="aplicada"))
        antes = banco.obter("a")
        ok, problemas = banco.aplicar_requisitos([{"id": "a", "requisitos": req("SQL")}, {"id": "x", "requisitos": {}},
                                                  {"id": "a", "requisitos": "não"}, "solto"])
        self.assertEqual(ok, ["a"])
        self.assertEqual(len(problemas), 3)
        depois = banco.obter("a")
        mudou = {k for k in set(antes) | set(depois) if antes.get(k) != depois.get(k)}
        self.assertEqual(mudou, {"requisitos", "atualizada_em"})


# ---------------------------------------------------------------- seleção e resumo (US1)

class TestSelecao(unittest.TestCase):
    def test_em_aplicacoes_e_todas(self):
        vs = [vaga("m", origem="manual", etapa="salva", analise_status="sem_analise"),
              vaga("s", triagem="seguir", etapa="encerrada"), vaga("x", triagem="seguir"),
              vaga("p"), vaga("f", triagem="fora"), vaga("b", triagem="pendente", etapa="aplicada"),
              vaga("q", analise_status="pendente")]
        self.assertEqual([v["id"] for v in R.selecionar(vs, "aplicacoes")], ["m", "s"])
        self.assertEqual([v["id"] for v in R.selecionar(vs, "todas")], ["s", "x", "p", "f", "b"])
        self.assertEqual(R.normalizar("outra", "lua"), ("aplicacoes", "todas"))

    def test_area_como_a_pagina(self):
        self.assertEqual(R.area_de(vaga("a", area="internacional")), "internacional")
        self.assertEqual(R.area_de(vaga("a", grupos=["internacional:EUA", "mudanca:Portugal"])), "internacional")
        self.assertEqual(R.area_de(vaga("a", grupos=["internacional:EUA", "remoto"])), "nacional")
        self.assertEqual(R.area_de(vaga("a", local="Lisboa, Portugal")), "nacional")  # o local não decide, como na página
        vs = [vaga("n"), vaga("i", area="internacional")]
        self.assertEqual([v["id"] for v in R.selecionar(vs, "todas", "internacional")], ["i"])


class TestResumo(unittest.TestCase):
    def setUp(self):
        self.vagas = [
            vaga("a", requisitos=req({"nome": "SQL", "tipo": "tecnica", "exigida": True},
                                     {"nome": "Comunicação", "tipo": "comportamental"}, anos=3, cert=["PMP"])),
            vaga("b", requisitos=req("sql", "Power BI", anos=5)),
            vaga("c", requisitos=req("SQL", {"nome": "Comunicação", "tipo": "comportamental", "exigida": False},
                                     anos=None)),
            vaga("d", requisitos=req("Power BI", anos=12)),
            vaga("e", requisitos=req("Jira Software", anos=0)),
            vaga("f", descricao="", analise_status="feita"),
            vaga("g"),
            vaga("h", descricao="Texto.", descricao_pendente=True),
        ]

    def resumo(self, perfil=PERFIL):
        return R.resumo(self.vagas, perfil, "todas", "todas")

    def test_contagem(self):
        c = self.resumo()["contagem"]
        self.assertEqual(c, {"selecao": 8, "com_requisitos": 5, "a_ler": 1, "sem_texto": 2, "sem_analise": 0})
        self.assertFalse(self.resumo()["poucas"])
        self.assertTrue(R.resumo(self.vagas[:2], PERFIL, "todas")["poucas"])

    def test_habilidades_uma_vez_por_vaga_e_na_ordem(self):
        h = self.resumo()["habilidades"]
        self.assertEqual(h["base"], 5)
        sql = h["tecnicas"][0]
        self.assertEqual((sql["nome"], sql["vagas"], sql["exigida"], sql["parte"], sql["ids"]),
                         ("SQL", 3, 1, 0.6, ["a", "b", "c"]))
        self.assertEqual([i["nome"] for i in h["tecnicas"]], ["SQL", "Power BI", "Jira Software"])
        self.assertEqual([(i["nome"], i["vagas"]) for i in h["comportamentais"]], [("Comunicação", 2)])

    def test_faixas_de_experiencia(self):
        e = self.resumo()["experiencia"]
        por = {f["faixa"]: f["vagas"] for f in e["faixas"]}
        self.assertEqual(por, {"ate1": 1, "2a3": 1, "4a5": 1, "6a9": 0, "10mais": 1, "nao_diz": 1})
        self.assertEqual(e["destaque"], "ate1")  # empate: a menor faixa
        self.assertEqual([f["faixa"] for f in e["faixas"]], ["ate1", "2a3", "4a5", "6a9", "10mais", "nao_diz"])
        self.assertIsNone(R.resumo([], PERFIL, "todas")["experiencia"]["destaque"])

    def test_certificacoes(self):
        c = self.resumo()["certificacoes"]
        self.assertEqual([(i["nome"], i["vagas"], i["tipo"]) for i in c["itens"]], [("PMP", 1, "certificacao")])


# ---------------------------------------------------------------- perfil (US2)

class TestPerfil(unittest.TestCase):
    def test_le_as_secoes(self):
        p = R.ler_perfil(PERFIL)
        linhas = [(i["linha"], i["nivel"]) for i in p["habilidades"]]
        self.assertEqual(linhas, [("Jira", "avançado"), ("SQL", "consultas básicas"), ("Python/Pandas", "profissional"),
                                  ("Looker", "profissional"), ("Confluence", ""), ("Trello", ""), ("C", "básico")])
        self.assertEqual(p["habilidades"][2]["nomes"], ["Python", "Pandas"])
        self.assertEqual([(i["linha"], i["nivel"]) for i in p["certificacoes"]],
                         [("PSM I", "em preparação"), ("Treinamento em Scrum", "Gestão Ágil (40h, concluída)")])
        self.assertIn("Kanban", p["fora"])
        self.assertNotIn("Jira — avançado", p["fora"])

    def test_outros_titulos(self):
        p = R.ler_perfil("## Competências\n- Excel: avançado\n## Skills\n- Figma\n## Cursos\n- Curso de SQL\n")
        self.assertEqual([(i["linha"], i["nivel"]) for i in p["habilidades"]], [("Excel", "avançado"), ("Figma", "")])
        self.assertEqual([i["linha"] for i in p["certificacoes"]], ["Curso de SQL"])
        self.assertEqual(R.ler_perfil("## Resumo\nNada aqui.")["habilidades"], [])

    def test_combina_por_nome_e_nao_por_parecida(self):
        jira = {"linha": "Jira", "nivel": "", "nomes": ["Jira"]}
        looker = {"linha": "Looker", "nivel": "", "nomes": ["Looker"]}
        c = {"linha": "C", "nivel": "", "nomes": ["C"]}
        pandas = {"linha": "Python/Pandas", "nivel": "", "nomes": ["Python", "Pandas"]}
        self.assertTrue(R.combina("Jira Software", jira))
        self.assertTrue(R.combina("jira", jira))
        self.assertFalse(R.combina("Power BI", looker))  # parecida não é a mesma
        self.assertFalse(R.combina("C#", c))
        self.assertTrue(R.combina("C", c))
        self.assertTrue(R.combina("Python", pandas))
        self.assertFalse(R.combina("Trello", jira))

    def test_marcas_nas_listas(self):
        vs = [vaga("a", requisitos=req("Jira", "Kanban", "Power BI", "Excel", cert=["PSM I", "Scrum"]))]
        r = R.resumo(vs, PERFIL, "todas")
        marcas = {i["nome"]: i["perfil"] for i in r["habilidades"]["tecnicas"] + r["certificacoes"]["itens"]}
        self.assertEqual(marcas, {"Jira": "habilidade", "Kanban": "citada", "Power BI": "nao", "Excel": "citada",
                                  "PSM I": "certificacao", "Scrum": "certificacao"})

    def test_relato_conta_como_citada(self):
        vs = [vaga("a", requisitos=req("Tableau"))]
        com_relato = PERFIL + "\n## Relatos\n- Usei Tableau num projeto da faculdade.\n"
        self.assertEqual(R.resumo(vs, com_relato, "todas")["habilidades"]["tecnicas"][0]["perfil"], "citada")

    def test_suas_habilidades(self):
        vs = [vaga("a", requisitos=req("SQL", "Jira")), vaga("b", requisitos=req("Jira Software")),
              vaga("c", requisitos=req("Python", cert=["PSM I"]))]
        s = R.resumo(vs, PERFIL, "todas")["suas"]
        self.assertEqual([(i["linha"], i["vagas"]) for i in s["habilidades"][:3]],
                         [("Jira", 2), ("SQL", 1), ("Python/Pandas", 1)])
        self.assertTrue(all(i["destaque"] for i in s["habilidades"][:3]))
        self.assertFalse(any(i["destaque"] for i in s["habilidades"][3:]))
        self.assertEqual([i["linha"] for i in s["habilidades"][3:]], ["Looker", "Confluence", "Trello", "C"])
        self.assertEqual((s["aparecem"], s["total"], s["tem_secao"], s["existe_perfil"]), (3, 7, True, True))
        self.assertEqual(s["certificacoes"][0]["vagas"], 1)
        self.assertEqual(s["habilidades"][0]["ids"], ["a", "b"])

    def test_perfil_sem_secao(self):
        s = R.resumo([], "## Resumo\nSó isto.", "todas")["suas"]
        self.assertEqual((s["tem_secao"], s["existe_perfil"], s["total"]), (False, True, 0))
        self.assertFalse(R.resumo([], "", "todas")["suas"]["existe_perfil"])

    def test_linha_repetida_sai(self):
        p = R.ler_perfil("## Habilidades\n- Power BI — básico\n- SQL/MySQL\n- Stack: Power BI, MySQL, Jira\n")
        self.assertEqual([i["linha"] for i in p["habilidades"]], ["Power BI", "SQL/MySQL", "Jira"])


# ---------------------------------------------------------------- indicadores (US3)

class TestIndicadores(unittest.TestCase):
    def test_formacao(self):
        vs = [vaga("a", requisitos=req(formacao={"nivel": "graduacao", "areas": ["Administração"]})),
              vaga("b", requisitos=req(formacao={"nivel": "graduacao", "areas": ["administracao", "Engenharia"]})),
              vaga("c", requisitos=req())]
        f = R.resumo(vs, PERFIL, "todas")["formacao"]
        por = {n["nivel"]: n["vagas"] for n in f["niveis"]}
        self.assertEqual((por["graduacao"], por["nao_diz"], por["mestrado"]), (2, 1, 0))
        self.assertEqual([(a["nome"], a["vagas"]) for a in f["areas"]], [("Administração", 2), ("Engenharia", 1)])

    def test_idiomas_com_o_ingles_da_analise(self):
        vs = [vaga("a", ingles={"nivel": "fluente", "frase": "fluent"}),  # sem requisitos lidos
              vaga("b", ingles={"nivel": "nao_pede"}),
              vaga("c", requisitos=req(idiomas=[{"idioma": "Espanhol", "nivel": "intermediario"}]),
                   ingles={"nivel": "basico"}),
              vaga("d", requisitos=req(idiomas=[{"idioma": "Inglês", "nivel": "nativo"}]), ingles={"nivel": "basico"})]
        i = R.resumo(vs, PERFIL, "todas")["idiomas"]
        self.assertEqual(i["base"], 3)
        ingles = next(x for x in i["itens"] if x["idioma"] == "Inglês")
        self.assertEqual((ingles["vagas"], [(n["nivel"], n["vagas"]) for n in ingles["niveis"]]),
                         (3, [("basico", 1), ("fluente", 1), ("nativo", 1)]))
        self.assertEqual([x["idioma"] for x in i["itens"]], ["Inglês", "Espanhol"])

    def test_senioridade_modelo_e_contratacao(self):
        vs = [vaga("a", senioridade=["pleno", "senior"], modelo_trabalho="remoto", tipo_emprego=["tempo_integral", "pj"],
                   contratacao=[{"valor": "clt", "frase": "CLT"}]),
              vaga("b", senioridade=["senior"], modelo_trabalho="nao_informado",
                   contratacao=[{"valor": "contractor", "frase": "contractor"}]),
              vaga("c", analise_status="pendente", senioridade=["junior"])]
        r = R.resumo(vs, PERFIL, "todas")
        self.assertEqual([(i["valor"], i["vagas"]) for i in r["senioridade"]["itens"]], [("pleno", 1), ("senior", 2)])
        self.assertEqual(r["senioridade"]["base"], 2)
        self.assertEqual([(i["valor"], i["vagas"]) for i in r["modelo"]["itens"]], [("remoto", 1)])
        self.assertEqual({i["valor"]: i["vagas"] for i in r["contratacao"]["itens"]}, {"clt": 1, "pj": 1, "contractor": 1})


# ---------------------------------------------------------------- leitura avulsa

class TestLeitura(Base):
    def ler(self, leitura, *args):
        situacao = leitura.iniciar(*args)
        t = leitura._thread
        if t is not None:
            t.join(20)
        return situacao

    def test_le_em_lotes_e_nao_mexe_na_nota(self):  # FR-005, SC-003
        self.ia_falsa()
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada") for i in range(3)], vaga("fora-da-selecao"))
        antes = {v["id"]: v for v in banco.listar_vagas()}
        leitura = R.Leitura()
        with mock.patch.object(R, "LOTE_LEITURA", 2):
            self.assertEqual(self.ler(leitura, "aplicacoes", "todas"), "comecou")
        e = leitura.estado()
        self.assertEqual((e["rodando"], e["lidas"], e["total"], e["parada"], e["erro"]), (False, 3, 3, False, None))
        self.assertEqual(len(self.pedidos_ia), 2)
        for v in banco.listar_vagas():
            mudou = {k for k in set(v) | set(antes[v["id"]]) if v.get(k) != antes[v["id"]].get(k)}
            self.assertEqual(mudou, set() if v["id"] == "fora-da-selecao" else {"requisitos", "atualizada_em"})
        r = banco.obter("v0")["requisitos"]
        self.assertEqual((r["habilidades"][0]["nome"], r["provedor"]), ("SQL", "openrouter"))

    def test_pedido_so_com_o_anuncio_e_os_nomes(self):  # FR-006
        self.ia_falsa()
        gravar(vaga("a", triagem="seguir", etapa="aplicada", descricao="Pedimos SQL." + "​"))
        self.ler(R.Leitura(), "aplicacoes")
        pedido = self.pedidos_ia[0]
        self.assertIn("Pedimos SQL.", pedido)
        self.assertNotIn("​", pedido)  # o texto passa pelo filtro de integridade
        self.assertIn("Jira; SQL; Python; Pandas", pedido)
        self.assertNotIn("Empresa Fictícia", pedido)  # o resto do perfil não vai
        self.assertNotIn("consultas básicas", pedido)  # nem o nível
        self.assertIn("**Os requisitos**", pedido)  # as regras vêm da skill
        self.assertIn("Experiência não é habilidade", pedido)

    def test_parar_e_continuar(self):  # SC-004
        leitura = R.Leitura()

        def responder(pedido, **_):
            leitura.parar()
            ids = re.findall(r"^### id: (\S+)$", pedido, re.M)
            return json.dumps([{"id": i, "requisitos": {"habilidades": ["SQL"]}} for i in ids])
        self.ia_falsa(responder)
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada") for i in range(3)])
        with mock.patch.object(R, "LOTE_LEITURA", 1):
            self.ler(leitura, "aplicacoes")
            e = leitura.estado()
            self.assertEqual((e["lidas"], e["total"], e["parada"], e["rodando"]), (1, 3, True, False))
            self.ler(leitura, "aplicacoes")
            self.assertEqual((leitura.estado()["total"], leitura.estado()["lidas"]), (2, 1))
        lidas = [p for p in self.pedidos_ia]
        ids = [re.findall(r"^### id: (\S+)$", p, re.M)[0] for p in lidas]
        self.assertEqual(len(ids), len(set(ids)))  # nenhuma lida duas vezes

    def test_falha_para_e_guarda_o_motivo(self):
        chamadas = []

        def responder(pedido, **_):
            chamadas.append(1)
            if len(chamadas) == 2:
                raise ia.IAErro("limite de pedidos do provedor")
            ids = re.findall(r"^### id: (\S+)$", pedido, re.M)
            return json.dumps([{"id": i, "requisitos": {"habilidades": ["SQL"]}} for i in ids])
        self.ia_falsa(responder)
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada") for i in range(3)])
        leitura = R.Leitura()
        with mock.patch.object(R, "LOTE_LEITURA", 1):
            self.ler(leitura, "aplicacoes")
            e = leitura.estado()
            self.assertEqual((e["lidas"], e["parada"]), (1, False))
            self.assertIn("limite", e["erro"]["motivo"])
            self.ler(leitura, "aplicacoes")
            self.assertEqual((leitura.estado()["total"], leitura.estado()["erro"]), (2, None))

    def test_vaga_suspeita_vai_sozinha(self):
        self.ia_falsa()
        gravar(vaga("a", triagem="seguir", etapa="aplicada"), vaga("b", triagem="seguir", etapa="aplicada"),
               vaga("s", triagem="seguir", etapa="aplicada", integridade={"veredito": "atencao"}))
        self.ler(R.Leitura(), "aplicacoes")
        lotes = [re.findall(r"^### id: (\S+)$", p, re.M) for p in self.pedidos_ia]
        self.assertIn(["s"], lotes)
        self.assertEqual(sorted(sum(lotes, [])), ["a", "b", "s"])

    def test_sem_ia_e_sem_vagas(self):
        self.ia_falsa(ligada=False)
        gravar(vaga("a", triagem="seguir", etapa="aplicada"))
        self.assertIsNone(R.Leitura().iniciar())
        ia.disponivel.return_value = True
        gravar(vaga("a", triagem="seguir", etapa="aplicada", requisitos=req("SQL")))
        self.assertEqual(R.Leitura().iniciar(), "nada")

    def test_resposta_sem_json(self):
        self.ia_falsa(lambda pedido, **_: "não sei")
        gravar(vaga("a", triagem="seguir", etapa="aplicada"))
        leitura = R.Leitura()
        self.ler(leitura, "aplicacoes")
        self.assertIn("fora do formato", leitura.estado()["erro"]["motivo"])
        self.assertNotIn("requisitos", banco.obter("a"))

    def test_lote_ilegivel_e_dividido(self):  # resposta longa demais, comum nas IAs gratuitas
        def responder(pedido, **_):
            ids = re.findall(r"^### id: (\S+)$", pedido, re.M)
            if len(ids) > 2:
                return '[{"id": "' + ids[0] + '", "requisitos": {"habilidades": ["SQ'  # cortada no meio
            return "```json\n" + json.dumps([{"id": i, "requisitos": {"habilidades": ["SQL"]}} for i in ids]) + "\n```"
        self.ia_falsa(responder)
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada") for i in range(4)])
        with mock.patch.object(R, "LOTE_LEITURA", 4), mock.patch.object(R, "RAIZ", self.tmp):
            leitura = R.Leitura()
            self.ler(leitura, "aplicacoes")
        self.assertEqual((leitura.estado()["lidas"], leitura.estado()["erro"]), (4, None))
        self.assertEqual(len(self.pedidos_ia), 3)  # o lote de 4 e as duas metades
        self.assertTrue((self.tmp / ".cache" / "requisitos-resposta-invalida.txt").exists())

    def test_vaga_esquecida_e_pedida_sozinha(self):
        def responder(pedido, **_):
            ids = re.findall(r"^### id: (\S+)$", pedido, re.M)
            return json.dumps([{"id": i, "requisitos": {"habilidades": ["SQL"]}} for i in ids[:-1] or ids])
        self.ia_falsa(responder)
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada") for i in range(3)])
        with mock.patch.object(R, "LOTE_LEITURA", 3):
            self.ler(R.Leitura(), "aplicacoes")
        self.assertTrue(all(R.lidos(v) for v in banco.listar_vagas()))

    def test_ilegivel_seguido_para(self):
        self.ia_falsa(lambda pedido, **_: "desculpe, não consigo")
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada") for i in range(8)])
        leitura = R.Leitura()
        with mock.patch.object(R, "RAIZ", self.tmp):
            self.ler(leitura, "aplicacoes")
        self.assertIn("fora do formato", leitura.estado()["erro"]["motivo"])
        self.assertEqual(len(self.pedidos_ia), R.ILEGIVEIS_SEGUIDAS)  # não insiste numa IA que não está dando conta

    def test_analise_leva_o_item_da_skill(self):
        self.assertIn("**Os requisitos**", analise.montar_pedido([vaga("a")]))
        self.assertIn('"requisitos"', analise.montar_pedido([vaga("a")]))


# ---------------------------------------------------------------- rotas e terminal (US4)

class TestServidor(Base):
    def setUp(self):
        super().setUp()
        import servidor
        self.servidor = servidor
        for p in (mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"}),
                  mock.patch.object(R, "LEITURA", R.Leitura())):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_resumo_pela_rota(self):
        self.ia_falsa(ligada=False)
        gravar(vaga("a", triagem="seguir", etapa="aplicada", requisitos=req("SQL")), vaga("b"))
        status, r = self.pedir("GET", "/api/requisitos?vagas=xx&area=yy")
        self.assertEqual(status, 200)
        self.assertEqual(r["selecao"], {"vagas": "aplicacoes", "area": "todas"})
        self.assertEqual((r["contagem"]["com_requisitos"], r["ia"]["ligada"], r["leitura"]["rodando"]), (1, False, False))
        _, todas = self.pedir("GET", "/api/requisitos?vagas=todas&area=nacional")
        self.assertEqual(todas["contagem"]["selecao"], 2)

    def test_ler_e_parar(self):
        self.ia_falsa()
        gravar(vaga("a", triagem="seguir", etapa="aplicada"))
        status, r = self.pedir("POST", "/api/requisitos/ler", {"vagas": "aplicacoes", "area": "todas"})
        self.assertIn(status, (200, 202))
        t = R.LEITURA._thread
        if t is not None:
            t.join(20)
        self.assertIn("requisitos", banco.obter("a"))
        status, r = self.pedir("POST", "/api/requisitos/parar", {})
        self.assertEqual((status, r["leitura"]["rodando"]), (200, False))
        status, r = self.pedir("POST", "/api/requisitos/ler", {})
        self.assertEqual((status, r["leitura"]["total"]), (200, 0))  # nada a ler

    def test_sem_ia_e_de_fora_do_computador(self):
        self.ia_falsa(ligada=False)
        status, r = self.pedir("POST", "/api/requisitos/ler", {})
        self.assertEqual(status, 409)
        self.assertIn("botão IA", r["erro"])
        with mock.patch.object(self.servidor.Handler, "_local", return_value=False):
            status, _ = self.pedir("POST", "/api/requisitos/ler", {})
        self.assertEqual(status, 403)

    def test_terminal_igual_a_pagina(self):  # SC-005
        self.ia_falsa(ligada=False)
        gravar(vaga("a", triagem="seguir", etapa="aplicada", requisitos=req("SQL", "Jira", anos=3)),
               vaga("b", triagem="seguir", etapa="aplicada", requisitos=req("SQL")))
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            self.assertEqual(R.main(["resumo", "--json"]), 0)
        _, pagina = self.pedir("GET", "/api/requisitos")
        terminal = json.loads(saida.getvalue())
        self.assertEqual(terminal, {k: v for k, v in pagina.items() if k not in ("leitura", "ia")})


class TestTerminal(Base):
    def rodar(self, *args):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            codigo = R.main(list(args))
        return codigo, saida.getvalue()

    def test_resumo_em_texto(self):
        gravar(vaga("a", triagem="seguir", etapa="aplicada", requisitos=req("SQL", "Power BI", anos=3)))
        codigo, texto = self.rodar("resumo")
        self.assertEqual(codigo, 0)
        for trecho in ("Em Aplicações", "Habilidades mais pedidas", "SQL — 1 de 1 vagas (100%) · nas suas habilidades",
                       "Power BI — 1 de 1 vagas (100%) · não está no seu perfil", "Tempo de experiência",
                       "a mais pedida: 2 a 3 anos", "Suas habilidades: 1 das suas 7 habilidades", "Poucas vagas"):
            self.assertIn(trecho, texto)

    def test_pendentes(self):
        gravar(*[vaga(f"v{i}", triagem="seguir", etapa="aplicada", descricao=f"Texto {i}​") for i in range(3)],
               vaga("s", triagem="seguir", etapa="aplicada", integridade={"veredito": "atencao"}))
        codigo, texto = self.rodar("pendentes", "--limite", "2")
        dados = json.loads(texto)
        self.assertEqual((codigo, len(dados["vagas"]), dados["restam"]), (0, 2, 2))
        self.assertNotIn("​", dados["vagas"][0]["descricao"])
        _, tudo = self.rodar("pendentes", "--limite", "10")
        self.assertEqual({v["id"]: v["atencao"] for v in json.loads(tudo)["vagas"]}["s"], True)

    def test_gravar(self):
        gravar(vaga("a", triagem="seguir", etapa="aplicada"))
        arq = self.tmp / "req.json"
        arq.write_text(json.dumps({"requisitos": [{"id": "a", "requisitos": req("SQL")}]}), encoding="utf-8")
        codigo, texto = self.rodar("gravar", str(arq))
        self.assertEqual((codigo, banco.obter("a")["aderencia"]), (0, 70))
        self.assertIn("1 vaga(s) com os requisitos gravados", texto)
        self.assertNotIn("provedor", banco.obter("a")["requisitos"])  # quem leu foi o assistente do chat
        arq.write_text(json.dumps([{"id": "x", "requisitos": {}}]), encoding="utf-8")
        codigo, texto = self.rodar("gravar", str(arq))
        self.assertEqual(codigo, 1)
        self.assertIn("não encontrada", texto)


if __name__ == "__main__":
    unittest.main()
