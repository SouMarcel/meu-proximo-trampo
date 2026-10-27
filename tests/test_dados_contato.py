"""Dados de contato na candidatura assistida (spec 033), sem rede, sem navegador e sem IA: proposta a partir do
currículo, das respostas guardadas e dos filtros; gravar com validação; reconhecer o campo pelo sentido; preencher
antes da memória e da IA, inclusive com a IA fora do ar."""
import json
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI.parent), str(AQUI.parent / "dash"), str(AQUI)]
import test_candidatura_assistida as tca  # noqa: E402  (a página falsa e a base com dados temporários)
from candidatura import auto, contato, memoria  # noqa: E402

CURRICULO = ("Ana Exemplo Silva\nAnalista de Dados\nana.exemplo@email.com | (11) 90000-0000 | "
             "linkedin.com/in/ana-exemplo\nSão Paulo, SP\n\nExperiência\n...")
DADOS = {"nome": "Ana", "sobrenome": "Exemplo Silva", "email": "ana.exemplo@email.com", "telefone": "(11) 90000-0000",
         "cidade": "São Paulo", "estado": "SP", "pais": "Brasil", "linkedin": "https://linkedin.com/in/ana-exemplo"}


def campo(rotulo="", tipo="texto", tipo_html="text", autocomplete="", nome="", opcoes=None, valor="", chave=None):
    return {"chave": chave or "#" + (nome or rotulo or autocomplete or tipo_html).replace(" ", "_")[:40], "tipo": tipo,
            "tipo_html": tipo_html, "rotulo": rotulo, "autocomplete": autocomplete, "nome": nome,
            "opcoes": opcoes or [], "valor": valor}


class Base(tca.Base):
    def setUp(self):
        super().setUp()
        tca.filtros.CONFIG.write_text(json.dumps({"termos": ["x"], "localidade": {"pais": "Brasil", "estado": "SP",
                                                                                 "cidade": "São Paulo"}}),
                                      encoding="utf-8")


class TestProposta(Base):  # US1
    def propor(self, texto=CURRICULO, marcados=None):
        marcados = {"pt": str(self.tmp / "cv.pdf"), "en": None} if marcados is None else marcados
        with mock.patch("curriculo_base.marcados", return_value=marcados), \
                mock.patch("primeiros_passos.extrair", return_value={"texto": texto, "contato": None}):
            return contato.propor()

    def test_do_curriculo_sem_gravar(self):  # SC-003, SC-004
        p = self.propor()
        d = p["dados"]
        self.assertEqual((d["nome"], d["sobrenome"]), ("Ana", "Exemplo Silva"))
        self.assertEqual(d["email"], "ana.exemplo@email.com")
        self.assertEqual(d["telefone"], "(11) 90000-0000")
        self.assertIn("linkedin.com/in/ana-exemplo", d["linkedin"])
        self.assertEqual((d["cidade"], d["estado"], d["pais"]), ("São Paulo", "SP", "Brasil"))
        self.assertEqual((p["fontes"]["email"], p["fontes"]["cidade"]), ("currículo", "filtros da busca"))
        self.assertFalse(contato.arquivo().exists())  # propor não grava

    def test_primeira_linha_que_nao_e_nome(self):
        d = self.propor(texto="Currículo 2026\nAna Exemplo\nana@email.com")["dados"]
        self.assertNotIn("nome", d)
        self.assertEqual(d["email"], "ana@email.com")

    def test_memoria_completa_o_que_falta(self):
        memoria.lembrar({"rotulo": "First Name*", "tipo": "texto"}, "Bia")
        memoria.lembrar({"rotulo": "Phone*", "tipo": "texto"}, "+55 21 98888-7777")
        p = self.propor(marcados={})  # sem currículo base
        self.assertEqual((p["dados"]["nome"], p["dados"]["telefone"]), ("Bia", "+55 21 98888-7777"))
        self.assertEqual(p["fontes"]["nome"], "respostas anteriores")
        self.assertTrue(any("sem currículo base" in a for a in p["avisos"]))

    def test_dois_emails_avisa(self):
        p = self.propor(texto="Ana Exemplo\nana@a.com\nana@b.com")
        self.assertEqual(p["dados"]["email"], "ana@a.com")
        self.assertTrue(any("2 e-mails" in a for a in p["avisos"]))


class TestGravar(Base):  # US1
    def test_gravar_ler_apagar(self):
        salvo = contato.gravar({**DADOS, "cep": "", "endereco": "  "})
        self.assertEqual(contato.ler(), salvo)
        self.assertNotIn("cep", salvo)
        self.assertEqual(contato.apagar(), {})
        self.assertEqual(contato.ler(), {})

    def test_validacao(self):
        with self.assertRaisesRegex(ValueError, "e-mail inválido"):
            contato.gravar({"email": "ana.email.com"})
        with self.assertRaisesRegex(ValueError, "linkedin.com"):
            contato.gravar({"linkedin": "https://exemplo.com/ana"})
        with self.assertRaisesRegex(ValueError, "parece um documento"):
            contato.gravar({"endereco": "CPF 123.456.789-09"})
        with self.assertRaisesRegex(ValueError, "parece um documento"):
            contato.gravar({"telefone": "123.456.789-09"})
        self.assertEqual(contato.gravar({"telefone": "11999998888"})["telefone"], "11999998888")  # celular, não CPF
        with self.assertRaisesRegex(ValueError, "portfólio"):
            contato.gravar({"portfolio": "meu site"})


class TestReconhecer(unittest.TestCase):  # US2
    def test_sinonimos_autocomplete_e_tipo(self):
        casos = {
            "Full name": "nome_completo", "Nome completo *": "nome_completo", "Name": "nome_completo",
            "Nome": "nome", "First Name (required)": "nome", "Sobrenome": "sobrenome", "Last name": "sobrenome",
            "E-mail": "email", "Email Address*": "email", "Celular": "telefone", "Phone number": "telefone",
            "WhatsApp": "telefone", "LinkedIn profile": "linkedin", "Cidade": "cidade", "País": "pais",
            "CEP": "cep", "Website": "portfolio",
        }
        for rotulo, esperado in casos.items():
            self.assertEqual(contato.reconhecer(campo(rotulo)), esperado, rotulo)
        self.assertEqual(contato.reconhecer(campo(autocomplete="given-name")), "nome")
        self.assertEqual(contato.reconhecer(campo(autocomplete="family-name")), "sobrenome")
        self.assertEqual(contato.reconhecer(campo("Contato", tipo_html="email")), "email")
        self.assertEqual(contato.reconhecer(campo("LinkedIn URL", tipo_html="url")), "linkedin")
        self.assertEqual(contato.reconhecer(campo("Link", tipo_html="url")), "portfolio")
        self.assertEqual(contato.reconhecer(campo(nome="job_application[first_name]")), "nome")

    def test_nao_reconhece_o_que_nao_e_contato(self):
        for rotulo in ("Nome da empresa anterior", "Qual o nome do seu gestor?", "Telefone de uma referência",
                       "Por que você quer trabalhar aqui?", "Cidade onde fica a empresa atual"):
            self.assertIsNone(contato.reconhecer(campo(rotulo)), rotulo)
        self.assertIsNone(contato.reconhecer({**campo("País"), "marca": "sensivel"}))

    def test_valor_no_formato_do_campo(self):
        paises = [{"valor": "0", "texto": "Selecione", "vazia": True}, {"valor": "1", "texto": "Argentina"},
                  {"valor": "2", "texto": "Brazil"}]
        self.assertEqual(contato.valor_para(campo("Country", tipo="selecao", tipo_html="select", opcoes=paises), DADOS), "2")
        estados = [{"valor": "0", "texto": "Rio de Janeiro"}, {"valor": "1", "texto": "São Paulo"}]
        self.assertEqual(contato.valor_para(campo("Estado", tipo="selecao", tipo_html="select", opcoes=estados), DADOS), "1")
        self.assertIsNone(contato.valor_para(campo("Country", tipo="selecao", tipo_html="select",
                                                    opcoes=paises[:2]), DADOS))  # sem opção que bata
        self.assertEqual(contato.valor_para(campo("Full name"), DADOS), "Ana Exemplo Silva")
        self.assertIsNone(contato.valor_para({**campo("Full name"), "limite": 5}, DADOS))  # não cabe
        self.assertIsNone(contato.valor_para(campo("CEP"), DADOS))  # não cadastrado


class TestPreencher(Base):  # US2
    def pagina(self):
        return tca.PaginaFalsa(url=tca.URL_GUPY, campos=[
            campo("Full name", chave="#nome"), campo("E-mail", tipo_html="email", chave="#email"),
            campo("Celular", tipo_html="tel", chave="#cel"), campo("LinkedIn profile", tipo_html="url", chave="#li"),
            campo("Nome da empresa anterior", chave="#empresa"),
            campo("Cidade", chave="#cidade", valor="Campinas"),  # já preenchido na página
            {**campo("Conte sua experiência com SQL", tipo="area", tipo_html="textarea", chave="#exp"), "limite": 0},
        ])

    def test_preenche_os_dados_de_contato_sem_ia(self):  # SC-001
        contato.gravar(DADOS)
        chamadas = []

        def propor(vaga, campos):
            chamadas.append([c["rotulo"] for c in campos])
            return {"itens": [{**c, "proposta": "", "conferir": []} for c in campos], "aviso": None, "ia": None}
        aba = self.pagina()
        r = auto.preencher_pagina(aba, self.VAGA, propor=propor)
        fontes = {p["rotulo"]: p["fonte"] for p in r["preenchidos"]}
        for rotulo in ("Full name", "E-mail", "Celular", "LinkedIn profile"):
            self.assertEqual(fontes.get(rotulo), "seus dados de contato", rotulo)
        valores = {c["chave"]: c["valor"] for c in aba.campos}
        self.assertEqual(valores["#nome"], "Ana Exemplo Silva")
        self.assertEqual(valores["#email"], "ana.exemplo@email.com")
        self.assertEqual(valores["#cidade"], "Campinas")  # não pisa no que já estava
        enviados = [r for lista in chamadas for r in lista]
        self.assertNotIn("Full name", enviados)  # dado de contato não vai à IA (SC-003)
        self.assertNotIn("E-mail", enviados)
        self.assertNotIn("Nome da empresa anterior", fontes)

    def test_com_a_ia_fora_do_ar(self):  # SC-002
        contato.gravar(DADOS)

        def ia_fora(vaga, campos):
            return {"itens": [{**c, "proposta": "", "conferir": []} for c in campos],
                    "aviso": "a IA não conseguiu escrever: o provedor está com problema agora (erro 503)", "ia": None}
        r = auto.preencher_pagina(self.pagina(), self.VAGA, propor=ia_fora)
        self.assertEqual(len([p for p in r["preenchidos"] if p["fonte"] == "seus dados de contato"]), 4)
        self.assertIn("erro 503", r["aviso_ia"])

    def test_sem_dados_salvos_vira_pergunta(self):
        r = auto.preencher_pagina(self.pagina(), self.VAGA,
                                  propor=lambda v, cs: {"itens": [{**c, "proposta": ""} for c in cs], "aviso": None, "ia": None})
        self.assertIn("E-mail", [p["rotulo"] for p in r["perguntas"]])
        self.assertFalse([p for p in r["preenchidos"] if p["fonte"] == "seus dados de contato"])


class TestRotas(Base):  # US1
    def setUp(self):
        super().setUp()
        import http.client

        import servidor
        self.http, self.servidor = http.client, servidor
        for p in (mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"}),):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)

    def pedir(self, metodo, caminho, corpo=None):
        con = self.http.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_rotas(self):
        status, j = self.pedir("GET", "/api/candidatura")
        self.assertEqual((status, j["contato"]), (200, {}))
        self.assertIn("linkedin", j["campos_contato"])
        self.assertEqual(self.pedir("PUT", "/api/candidatura/contato", {"dados": {"email": "x"}})[0], 400)
        status, j = self.pedir("PUT", "/api/candidatura/contato", {"dados": DADOS})
        self.assertEqual((status, j["contato"]["email"]), (200, "ana.exemplo@email.com"))
        self.assertEqual(self.pedir("GET", "/api/candidatura")[1]["contato"]["nome"], "Ana")
        with mock.patch("curriculo_base.marcados", return_value={}):
            status, j = self.pedir("POST", "/api/candidatura/contato/proposta", {})
        self.assertEqual(status, 200)
        self.assertEqual(j["dados"]["cidade"], "São Paulo")
        self.assertEqual(self.pedir("DELETE", "/api/candidatura/contato", {})[1], {"contato": {}})


if __name__ == "__main__":
    unittest.main()
