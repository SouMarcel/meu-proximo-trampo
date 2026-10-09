"""Testes do primeiros_passos.py (python -m unittest discover -s tests). Materiais fictícios gerados aqui."""
import io
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import ia  # noqa: E402
import primeiros_passos as pp  # noqa: E402

CPF = "123.456.789-09"


def pdf_minimo(linhas):
    """PDF de uma página com texto (Helvetica, só ASCII); sem linhas, um PDF sem texto (como um digitalizado)."""
    conteudo = ("BT /F1 12 Tf 72 720 Td " + " ".join(f"({l}) Tj 0 -16 Td" for l in linhas) + " ET") if linhas else ""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> "
            "/Contents 4 0 R >>",
            f"<< /Length {len(conteudo)} >>\nstream\n{conteudo}\nendstream",
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    saida, posicoes = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        posicoes.append(len(saida))
        saida += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(saida)
    saida += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    saida += "".join(f"{p:010d} 00000 n \n" for p in posicoes).encode()
    saida += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return saida


def docx_bytes(paragrafos, tabela=None):
    import docx
    d = docx.Document()
    for p in paragrafos:
        d.add_paragraph(p)
    if tabela:
        t = d.add_table(rows=len(tabela), cols=len(tabela[0]))
        for i, linha in enumerate(tabela):
            for j, c in enumerate(linha):
                t.cell(i, j).text = c
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def zip_linkedin(completo=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Profile.csv", "﻿First Name,Last Name,Headline,Summary,Geo Location\n"
                                  "Ana,Exemplo,Analista de Dados,Trabalho com dados há 5 anos.,\"Curitiba, PR\"\n")
        z.writestr("Positions.csv", "Company Name,Title,Description,Location,Started On,Finished On\n"
                                    "Empresa Alfa,Analista de Dados,\"Painéis de vendas\nAutomação de relatórios\","
                                    "Curitiba,Mar 2021,\n"
                                    "Empresa Beta,Assistente de Dados,,Curitiba,Jan 2018,Jun 2020\n")
        z.writestr("Skills.csv", "Name\nSQL\nPower BI\n")
        if completo:
            z.writestr("Education.csv", "School Name,Start Date,End Date,Notes,Degree Name,Activities\n"
                                        "Universidade Exemplo,2014,2018,,Bacharelado em Estatística,\n")
            z.writestr("Certifications.csv", "Name,Url,Authority,Started On,Finished On,License Number\n"
                                             "Certificação Exemplo,,Instituto Exemplo,Mai 2022,,\n")
            z.writestr("Languages.csv", "Name,Proficiency\nInglês,Profissional\n")
    return buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(pp, "ANEXOS", self.tmp / "anexos" / "primeiros-passos"),
                        mock.patch.object(pp, "ANTERIORES", self.tmp / "anexos" / "perfis-anteriores"),
                        mock.patch.object(pp, "PROGRESSO", self.tmp / ".cache" / "primeiros-passos.json"),
                        mock.patch.object(pp, "RAIZ", self.tmp)]
        for p in self.patches:
            p.start()
        shutil.copy(Path(__file__).resolve().parent.parent / "perfil.exemplo.md", self.tmp / "perfil.exemplo.md")
        self.cfg = {"perfil": str(self.tmp / "perfil.md")}

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def arquivo(self, nome, dados):
        caminho = self.tmp / nome
        caminho.write_bytes(dados)
        return caminho


class TestPrivacidade(unittest.TestCase):
    def test_mascara_documentos(self):
        texto = f"CPF: {CPF}\nRG: 12.345.678-9\nData de nascimento: 01/02/1990\nCPF sem pontos 12345678909"
        limpo = pp.mascarar_documentos(texto)
        for proibido in (CPF, "12.345.678-9", "01/02/1990", "12345678909"):
            self.assertNotIn(proibido, limpo)
        self.assertIn("[removido]", limpo)

    def test_nao_mascara_telefone_nem_datas_de_cargo(self):
        texto = "Telefone (41) 99999-8888 — Analista (03/2021–atual)"
        self.assertEqual(pp.mascarar_documentos(texto), texto)

    def test_reconhece_contato(self):
        c = pp.reconhecer_contato("ana@exemplo.com.br | (41) 99999-8888 | linkedin.com/in/ana-exemplo")
        self.assertEqual(c["emails"], ["ana@exemplo.com.br"])
        self.assertEqual(c["telefones"], ["(41) 99999-8888"])
        self.assertEqual(c["linkedin"], "linkedin.com/in/ana-exemplo")


class TestExtracao(Base):
    def test_docx_com_tabela_e_cpf(self):
        dados = docx_bytes(["Ana Exemplo", f"CPF {CPF}", "ana@exemplo.com"], [["SQL", "Avançado"]])
        r = pp.extrair(self.arquivo("cv.docx", dados))
        self.assertEqual(r["tipo"], "curriculo_docx")
        self.assertIn("Ana Exemplo", r["texto"])
        self.assertIn("SQL | Avançado", r["texto"])
        self.assertNotIn(CPF, r["texto"])
        self.assertEqual(r["contato"]["emails"], ["ana@exemplo.com"])

    def test_pdf(self):
        r = pp.extrair(self.arquivo("cv.pdf", pdf_minimo(["Ana Exemplo", "Analista de Dados", f"CPF {CPF}"])))
        self.assertEqual(r["tipo"], "curriculo_pdf")
        self.assertIn("Analista de Dados", r["texto"])
        self.assertNotIn(CPF, r["texto"])

    def test_pdf_do_linkedin(self):
        r = pp.extrair(self.arquivo("Profile.pdf", pdf_minimo(["www.linkedin.com/in/ana-exemplo", "Experience"])))
        self.assertEqual(r["tipo"], "linkedin_pdf")

    def test_pdf_sem_texto_avisa(self):
        r = pp.extrair(self.arquivo("scan.pdf", pdf_minimo([])))
        self.assertEqual(r["texto"], "")
        self.assertTrue(any("imagem" in a for a in r["avisos"]))

    def test_zip_do_linkedin(self):
        r = pp.extrair(self.arquivo("linkedin.zip", zip_linkedin()))
        self.assertEqual(r["tipo"], "linkedin_zip")
        c = r["campos"]
        self.assertEqual(c["perfil"]["titulo"], "Analista de Dados")
        self.assertEqual([x["empresa"] for x in c["cargos"]], ["Empresa Alfa", "Empresa Beta"])
        self.assertEqual(c["competencias"], ["SQL", "Power BI"])
        self.assertTrue(any("Education.csv" in a for a in r["avisos"]))
        completo = pp.extrair(self.arquivo("linkedin2.zip", zip_linkedin(completo=True)))
        self.assertEqual(completo["avisos"], [])
        self.assertEqual(completo["campos"]["idiomas"], [{"idioma": "Inglês", "nivel": "Profissional"}])

    def test_formatos_recusados(self):
        with self.assertRaises(pp.PerfilErro):
            pp.extrair(self.arquivo("antigo.doc", b"x"))
        with self.assertRaises(pp.PerfilErro):
            pp.extrair(self.arquivo("foto.png", b"x"))
        z = io.BytesIO()
        with zipfile.ZipFile(z, "w") as arq:
            arq.writestr("outra.txt", "nada")
        with self.assertRaises(pp.PerfilErro):
            pp.extrair(self.arquivo("outro.zip", z.getvalue()))
        with self.assertRaises(pp.PerfilErro):
            pp.extrair(self.arquivo("quebrado.zip", b"PK nada"))


class TestMateriais(Base):
    def test_guarda_sem_sobrescrever_e_remove(self):
        e = pp.estado_vazio()
        a = pp.adicionar_material(e, "Currículo Ana.docx", docx_bytes(["Ana"]))
        b = pp.adicionar_material(e, "Currículo Ana.docx", docx_bytes(["Ana 2"]))
        self.assertNotEqual(a["arquivo"], b["arquivo"])
        self.assertTrue((self.tmp / a["arquivo"]).exists() and (self.tmp / b["arquivo"]).exists())
        self.assertEqual([m["id"] for m in e["materiais"]], ["m1", "m2"])
        pp.remover_material(e, "m1")
        self.assertEqual([m["id"] for m in e["materiais"]], ["m2"])
        with self.assertRaises(pp.PerfilErro):
            pp.remover_material(e, "m9")

    def test_texto_colado_e_limites(self):
        e = pp.estado_vazio()
        m = pp.adicionar_material(e, "", texto=f"Sou analista. CPF {CPF}")
        self.assertEqual(m["tipo"], "texto")
        self.assertNotIn(CPF, m["texto"])
        with self.assertRaises(pp.PerfilErro):
            pp.adicionar_material(e, "grande.pdf", b"x" * (pp.LIMITE_ARQUIVO + 1))
        with self.assertRaises(pp.PerfilErro):
            pp.adicionar_material(e, "antigo.doc", b"x")
        with self.assertRaises(pp.PerfilErro):
            pp.adicionar_material(e, "quebrado.zip", b"PK nada")
        self.assertEqual(len(e["materiais"]), 1)
        self.assertFalse(list(pp.ANEXOS.glob("*.zip")) if pp.ANEXOS.exists() else [])

    def test_progresso_e_recomecar(self):
        e = pp.carregar()
        pp.adicionar_material(e, "cv.docx", docx_bytes(["Ana"]))
        e["respostas"] = {"cidade": "Curitiba"}
        pp.salvar(e)
        self.assertEqual(pp.carregar()["respostas"], {"cidade": "Curitiba"})
        self.assertEqual(pp.recomecar(), pp.estado_vazio())
        self.assertEqual(pp.carregar()["materiais"], [])
        self.assertTrue(list(pp.ANEXOS.glob("*.docx")))  # os arquivos ficam


class TestRascunho(Base):
    def estado(self):
        e = pp.estado_vazio()
        pp.adicionar_material(e, "cv.docx", docx_bytes(["Analista de Dados — Empresa Alfa (03/2021–atual)",
                                                        f"CPF {CPF}"]))
        pp.adicionar_material(e, "linkedin.zip", zip_linkedin())
        return e

    def test_com_ia_fonte_conflito_e_sem_documentos(self):
        resposta = {
            "objetivo": [{"texto": "Analista de Dados", "fonte": "cv.docx"}],
            "resumo": [{"texto": "Inventado", "fonte": "chute"}, {"texto": "Sem fonte"}],
            "experiencias": [{"cargo": "Analista de Dados", "empresa": "Empresa Alfa", "inicio": "{{conflito:0}}",
                              "fim": "", "itens": [{"texto": "Painéis de vendas", "fonte": "linkedin.zip"}],
                              "fonte": "cv.docx"},
                             {"cargo": "Fantasma", "empresa": "X", "fonte": "inexistente"}],
            "conflitos": [{"campo": "Início na Empresa Alfa", "opcoes": [{"valor": "03/2021", "fonte": "cv.docx"},
                                                                          {"valor": "Mar 2021",
                                                                           "fonte": "linkedin.zip"}]}],
        }
        pedidos = []
        with mock.patch.object(ia, "responder", lambda p, **k: pedidos.append(p) or json.dumps(resposta)):
            r = pp.rascunho_com_ia(self.estado())
        self.assertNotIn(CPF, pedidos[0])
        self.assertIn("### Fonte: cv.docx", pedidos[0])
        self.assertEqual(r["resumo"], [])
        self.assertEqual([x["cargo"] for x in r["experiencias"]], ["Analista de Dados"])
        self.assertEqual(len(r["conflitos"][0]["opcoes"]), 2)
        self.assertIsNone(r["conflitos"][0]["escolha"])

    def test_com_ia_erros(self):
        with mock.patch.object(ia, "responder", side_effect=ia.IAErro("sem conexão")):
            with self.assertRaises(pp.PerfilErro):
                pp.rascunho_com_ia(self.estado())
        with mock.patch.object(ia, "responder", return_value="não sei"):
            with self.assertRaises(pp.PerfilErro):
                pp.rascunho_com_ia(self.estado())
        with self.assertRaises(pp.PerfilErro):
            pp.rascunho_com_ia(pp.estado_vazio())

    def test_sem_ia_pelo_zip(self):
        r = pp.rascunho_sem_ia(self.estado())
        self.assertEqual(r["objetivo"][0]["texto"], "Analista de Dados")
        self.assertEqual(r["experiencias"][0]["itens"][1]["texto"], "Automação de relatórios")
        self.assertEqual([x["texto"] for x in r["habilidades"]], ["SQL", "Power BI"])
        self.assertTrue(all(x["fonte"] == "linkedin.zip" for x in r["habilidades"]))


class TestAnamneseEPerfil(Base):
    def rascunho(self):
        return {"objetivo": [], "resumo": [{"texto": "Analista com 5 anos.", "fonte": "cv"}], "formacao": [],
                "certificacoes": [], "habilidades": [], "idiomas": [],
                "experiencias": [{"cargo": "Analista", "empresa": "Alfa", "inicio": "{{conflito:0}}", "fim": "",
                                  "itens": [{"texto": "Painéis", "fonte": "cv"}], "fonte": "cv"},
                                 {"cargo": "Assistente", "empresa": "Beta", "inicio": "2015", "fim": "06/2018",
                                  "itens": [], "fonte": "cv"}],
                "conflitos": [{"campo": "Início", "opcoes": [{"valor": "03/2021", "fonte": "cv"},
                                                             {"valor": "04/2021", "fonte": "zip"}], "escolha": None}]}

    def test_perguntas_por_cargo_e_condicionais(self):
        ids = [p["id"] for p in pp.perguntas_para({"rascunho": self.rascunho()})]
        self.assertIn("conquista:0", ids)
        self.assertIn("medida:1", ids)
        self.assertNotIn("conquista:2", ids)
        cond = {p["id"] for p in pp.PERGUNTAS if p.get("condicao") == pp.EXTERIOR}
        self.assertEqual(cond, {"exterior_remoto", "exterior_paises", "morar_fora", "passaporte", "autorizacao",
                                "sponsor", "fuso", "contratacao"})

    def test_diagnostico(self):
        resp = {"ferramentas": ["Jira — avançado", "Excel"], "conquista:0": "Reduzi o prazo", "medida:0": ""}
        achados = pp.diagnosticar(self.rascunho(), resp)
        textos = " ".join(a["mensagem"] for a in achados)
        self.assertIn("cargos que você busca", textos)
        self.assertIn("Datas sem mês em Assistente — Beta", textos)
        self.assertIn("Sem descrição do que você fazia em Assistente — Beta", textos)
        self.assertIn("Ferramenta sem nível: Excel", textos)
        self.assertNotIn("Jira", textos)
        self.assertIn("sem medida", textos)
        self.assertIn("Conflito sem escolha", textos)
        self.assertIn("Formação vazia", textos)
        self.assertNotIn("Habilidades e ferramentas vazias", textos)  # as ferramentas foram respondidas
        self.assertTrue(all(a["pergunta"] for a in achados))
        ir = {a["mensagem"]: a["ir"] for a in achados}
        self.assertEqual(ir["Ferramenta sem nível: Excel."], "pergunta:ferramentas")
        self.assertEqual(ir["Conflito sem escolha: Início."], "conflitos")
        self.assertEqual(ir["A conquista em Analista está sem medida."], "pergunta:medida:0")

    def test_intervalo(self):
        x = [{"texto": "x", "fonte": "cv"}]
        r = {"experiencias": [{"cargo": "A", "inicio": "01/2015", "fim": "12/2016", "itens": x},
                              {"cargo": "B", "inicio": "Mar 2018", "fim": "", "itens": x}],
             "resumo": x, "formacao": x, "habilidades": x, "idiomas": x}
        achados = pp.diagnosticar(r, {"cargos_alvo": ["X"]})
        self.assertEqual([a["mensagem"] for a in achados], ["Intervalo de 15 meses entre A e B."])

    def test_montar_gravar_e_versao_anterior(self):
        r = self.rascunho()
        resp = {"cargos_alvo": ["Analista de Dados"], "modelos": ["remoto", "hibrido"], "cidade": "Curitiba",
                "estado": "PR", "conquista:0": "Reduzi o prazo do fechamento", "medida:0": "de 10 para 6 dias",
                "interesse_exterior": True, "exterior_remoto": True, "passaporte": False, "nota": f"CPF {CPF}"}
        md = pp.montar_perfil(r, resp, {"email": "ana@exemplo.com"})
        self.assertIn("{{conflito:0}}", md)
        with self.assertRaises(pp.PerfilErro):
            pp.gravar_perfil(md, self.cfg)
        r["conflitos"][0]["escolha"] = 1
        md = pp.montar_perfil(r, resp, {"email": "ana@exemplo.com"})
        self.assertIn("### Analista — Alfa (04/2021–atual)", md)
        self.assertIn("- Maior conquista: Reduzi o prazo do fechamento (medida: de 10 para 6 dias)", md)
        self.assertIn("- E-mail: ana@exemplo.com", md)
        self.assertIn("## Trabalho no exterior", md)
        self.assertIn("- Passaporte válido: não", md)
        self.assertNotIn(CPF, md)
        destino, anterior = pp.gravar_perfil(md, self.cfg)
        self.assertIsNone(anterior)
        self.assertEqual(destino.read_text(encoding="utf-8"), md)
        novo = md.replace("Curitiba", "Londrina")
        destino, anterior = pp.gravar_perfil(novo + f"\nCPF {CPF}\n", self.cfg)
        self.assertEqual(anterior.read_text(encoding="utf-8"), md)
        self.assertNotIn(CPF, destino.read_text(encoding="utf-8"))
        dif = pp.diferencas(md, novo)
        self.assertIn({"tipo": "+", "texto": "- Cidade onde moro: Londrina, PR"}, dif)
        self.assertIn({"tipo": "-", "texto": "- Cidade onde moro: Curitiba, PR"}, dif)

    def test_objetivo_sem_repetir_cargo(self):
        r = {"objetivo": [{"texto": "Analista de Dados", "fonte": "zip"}, {"texto": "Foco em varejo", "fonte": "cv"}]}
        md = pp.montar_perfil(r, {"cargos_alvo": ["analista de dados"]})
        self.assertNotIn("- Analista de Dados", md)
        self.assertIn("- Foco em varejo", md)

    def test_sem_exterior_nao_ha_bloco(self):
        md = pp.montar_perfil({}, {"cargos_alvo": ["X"], "interesse_exterior": False})
        self.assertNotIn("Trabalho no exterior", md)
        self.assertNotIn("Contato", md)


class TestFiltros(unittest.TestCase):
    def test_propoe_a_partir_das_respostas(self):
        resp = {"cargos_alvo": ["Analista de Dados", "BI"], "cargos_alvo_en": ["Data Analyst"],
                "modelos": ["remoto", "hibrido"], "cidade": "Curitiba", "estado": "PR", "senioridade": ["pleno"],
                "interesse_exterior": True, "exterior_remoto": True, "exterior_paises": ["Portugal", "Marte"]}
        r = pp.propor_filtros(resp, {})
        f = r["filtros"]
        self.assertEqual(f["termos"], ['"Analista de Dados"', "BI", '"Data Analyst"'])
        self.assertEqual(f["localidade"]["cidade"], "Curitiba")
        self.assertEqual(f["modelos"], {"remoto": True, "hibrido": True, "presencial": False})
        self.assertEqual({k: f["internacional"][k] for k in ("ativo", "paises", "termos")},
                         {"ativo": True, "paises": ["Portugal"], "termos": ['"Data Analyst"']})
        self.assertEqual(f["senioridades"], ["pleno"])
        self.assertIn("Cargos", [m["campo"] for m in r["mudancas"]])

    def test_sem_cidade_fica_remoto_e_sem_exterior_desligado(self):
        r = pp.propor_filtros({"cargos_alvo": ["Analista"], "modelos": ["hibrido"], "interesse_exterior": True}, {})
        self.assertEqual(r["filtros"]["modelos"], {"remoto": True, "hibrido": False, "presencial": False})
        self.assertFalse(r["filtros"]["internacional"]["ativo"])
        self.assertEqual(len(r["avisos"]), 2)

    def test_sem_cargos(self):
        with self.assertRaises(pp.PerfilErro):
            pp.propor_filtros({}, {})


class TestProgressoEPrevia(Base):
    def estado(self):
        e = pp.estado_vazio()
        pp.adicionar_material(e, "cv.docx", docx_bytes(["Analista de Dados na Alfa", f"CPF {CPF}"]))
        e["rascunho"] = {"origem": "sem_ia", "objetivo": [], "resumo": [], "formacao": [], "certificacoes": [],
                         "habilidades": [], "idiomas": [],
                         "experiencias": [{"cargo": "Analista", "empresa": "Alfa", "inicio": "{{conflito:0}}", "fim": "",
                                           "itens": [], "fonte": "cv.docx"}],
                         "conflitos": [{"campo": "Início", "opcoes": [{"valor": "03/2021", "fonte": "cv.docx"}],
                                        "escolha": None}]}
        return e

    def test_atualizar_progresso(self):
        e = self.estado()
        pp.atualizar_progresso(e, {"etapa": "anamnese", "respostas": {"cidade": f"Curitiba CPF {CPF}", "passaporte": True},
                                   "escolhas": {"0": 0}, "contato": {"email": "ana@exemplo.com", "linkedin": ""}})
        self.assertEqual(e["etapa"], "anamnese")
        self.assertNotIn(CPF, e["respostas"]["cidade"])
        self.assertIs(e["respostas"]["passaporte"], True)
        self.assertEqual(e["rascunho"]["conflitos"][0]["escolha"], 0)
        self.assertEqual(e["contato"], {"email": "ana@exemplo.com"})
        pp.atualizar_progresso(e, {"respostas": {"cidade": None}})
        self.assertIsNone(e["respostas"]["cidade"])
        self.assertIs(e["respostas"]["passaporte"], True)
        for ruim in ({"etapa": "outra"}, {"respostas": {"inventada": "x"}}, {"escolhas": {"0": 5}}, {"escolhas": {"3": 0}},
                     {"escolhas": {"0": True}}, {"contato": {"email": "nao-e-email"}},
                     {"contato": {"linkedin": "https://exemplo.com/ana"}}, {"contato": {"telefone": "abc"}}):
            with self.assertRaises(pp.PerfilErro, msg=ruim):
                pp.atualizar_progresso(e, ruim)

    def test_previa_novo_e_existente(self):
        e = self.estado()
        p = pp.previa(e, cfg=self.cfg)
        self.assertIsNone(p["diferencas"])
        self.assertEqual(p["conflitos_pendentes"], 1)
        self.assertEqual(p["textos"][0]["nome"], "cv.docx")
        self.assertNotIn(CPF, json.dumps(p, ensure_ascii=False))
        (self.tmp / "perfil.md").write_text("# Meu perfil de carreira\n\n## Objetivo\n- Cargos que procuro: Antigo\n",
                                            encoding="utf-8")
        p = pp.previa(e, cfg=self.cfg)  # sem IA e com perfil: a revisão começa do perfil atual
        self.assertIn("Cargos que procuro: Antigo", p["markdown"])
        self.assertEqual(p["textos"][0]["nome"], "Montado a partir das suas respostas")
        self.assertEqual(p["diferencas"], [])
        p = pp.previa(e, markdown="# Meu perfil de carreira\n\n## Objetivo\n- Cargos que procuro: Novo\n", cfg=self.cfg)
        self.assertIn({"tipo": "+", "texto": "- Cargos que procuro: Novo"}, p["diferencas"])
        e["rascunho"]["origem"] = "ia"
        self.assertNotIn("Antigo", pp.previa(e, cfg=self.cfg)["markdown"])  # com IA, o rascunho já partiu do perfil atual

    def test_sugestao_em_ingles(self):
        resp = {"cargos_alvo": ["Analista de Dados"], "interesse_exterior": True, "exterior_remoto": True,
                "exterior_paises": ["Portugal"]}
        with mock.patch.object(ia, "responder", return_value='["Data Analyst"]'):
            r = pp.propor_filtros(resp, {}, sugerir_en=True)
        self.assertTrue(r["sugestao_en"])
        self.assertEqual(r["filtros"]["internacional"]["termos"], ['"Data Analyst"'])
        self.assertTrue(any("sugestão da IA" in a for a in r["avisos"]))
        with mock.patch.object(ia, "responder", side_effect=ia.IAErro("fora do ar")):
            with self.assertRaises(pp.PerfilErro):
                pp.propor_filtros(resp, {}, sugerir_en=True)


class TestLinhaDeComando(Base):
    def test_extrair_e_diagnostico(self):
        cv = self.arquivo("cv.docx", docx_bytes(["Ana", f"CPF {CPF}"]))
        saida = io.StringIO()
        with mock.patch("sys.stdout", saida):
            self.assertEqual(pp.main(["extrair", str(cv)]), 0)
        self.assertNotIn(CPF, saida.getvalue())
        self.assertEqual(json.loads(saida.getvalue())["tipo"], "curriculo_docx")
        perfil = self.tmp / "perfil.md"
        perfil.write_text("# Meu perfil\n\n## Objetivo\n- Cargos que procuro: Analista\n\n## Experiência\n\n"
                          "### Analista — Alfa (2019–atual)\n", encoding="utf-8")
        saida = io.StringIO()
        with mock.patch("sys.stdout", saida):
            self.assertEqual(pp.main(["diagnostico", str(perfil)]), 0)
        self.assertIn("Datas sem mês em Analista — Alfa", saida.getvalue())
        self.assertNotIn("cargos que você busca", saida.getvalue())
        self.assertIn("Formação vazia", saida.getvalue())
        completo = self.tmp / "completo.md"
        completo.write_text("# Meu perfil\n\n## Objetivo\n- Cargos que procuro: Analista\n\n## Resumo\nAnalista.\n\n"
                            "## Experiência\n\n### Analista — Alfa (03/2019–atual)\n- Painéis\n\n## Formação\n- Estatística\n\n"
                            "## Habilidades e ferramentas (com nível)\n- SQL — avançado\n\n## Idiomas\n- Inglês — leitura\n",
                            encoding="utf-8")
        saida = io.StringIO()
        with mock.patch("sys.stdout", saida):
            self.assertEqual(pp.main(["diagnostico", str(completo)]), 0)
        self.assertIn("Nada a apontar.", saida.getvalue())
        with mock.patch("sys.stdout", io.StringIO()), mock.patch.object(pp, "_config", lambda: self.cfg):
            self.assertEqual(pp.main(["gravar", str(completo)]), 0)
            self.assertEqual(pp.main(["gravar", str(completo)]), 0)
        self.assertEqual((self.tmp / "perfil.md").read_text(encoding="utf-8"), completo.read_text(encoding="utf-8"))
        self.assertEqual(len(list(pp.ANTERIORES.glob("perfil-*.md"))), 2)  # o perfil.md do teste acima e o primeiro gravado
        with mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(pp.main(["extrair", str(self.tmp / "nao-existe.pdf")]), 1)
            pendente = self.arquivo("pendente.md", "### A — B ({{conflito:0}}–atual)\n".encode())
            self.assertEqual(pp.main(["gravar", str(pendente)]), 1)


if __name__ == "__main__":
    unittest.main()
