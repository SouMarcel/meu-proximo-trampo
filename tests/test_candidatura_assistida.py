"""Candidatura assistida (spec 027), sem navegador, sem rede e sem IA de verdade: domínios (conhecidos, liberados,
bloqueados e parecidos), classificação da página e dos campos, preencher só o confirmado (nada de botão, sensível,
cadastro, arquivo ou senha), login preso ao host exato com a senha fora de todo retorno, propostas da IA e as rotas."""
import http.client
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
import banco  # noqa: E402
import candidatura  # noqa: E402
import candidatura_ia  # noqa: E402
import curriculo_ia  # noqa: E402
import filtros  # noqa: E402
import ia  # noqa: E402
import segredos  # noqa: E402
from candidatura import dominios, formulario, login  # noqa: E402

DADOS = Path(__file__).resolve().parent / "dados" / "kit"
PERFIL = (DADOS / "perfil-ficticio.md").read_text(encoding="utf-8")
VAGA = json.loads((DADOS / "vagas.json").read_text(encoding="utf-8"))["en"]
URL_GUPY = "https://empresaalfa.gupy.io/candidates/jobs/123/apply"
SENHA = "s3nh4-Secreta!#="


def campos_exemplo():
    return [
        {"chave": "#nome", "tipo": "texto", "tipo_html": "text", "rotulo": "Nome completo", "valor": "Pessoa Teste"},
        {"chave": "#exp", "tipo": "area", "tipo_html": "textarea", "rotulo": "Conte sua experiência com SQL", "valor": "",
         "limite": 120},
        {"chave": "#anos", "tipo": "texto", "tipo_html": "number", "rotulo": "Quantos anos de experiência com Power BI?",
         "valor": ""},
        {"chave": "n:ingles", "tipo": "selecao", "tipo_html": "select", "rotulo": "Nível de inglês", "valor": "",
         "opcoes": [{"valor": "0", "texto": "Selecione", "vazia": True}, {"valor": "1", "texto": "Básico"},
                    {"valor": "2", "texto": "Intermediário"}, {"valor": "3", "texto": "Avançado"}]},
        {"chave": "radio:remoto", "tipo": "unica", "tipo_html": "radio", "rotulo": "Já trabalhou remoto?", "valor": "",
         "opcoes": [{"valor": "0", "texto": "Sim"}, {"valor": "1", "texto": "Não"}]},
        {"chave": "check:ferr", "tipo": "multipla", "tipo_html": "checkbox", "rotulo": "Quais ferramentas você usa?",
         "valor": "", "opcoes": [{"valor": "0", "texto": "Excel"}, {"valor": "1", "texto": "Power BI"},
                                 {"valor": "2", "texto": "Tableau"}]},
        {"chave": "#salario", "tipo": "texto", "tipo_html": "text", "rotulo": "Qual sua pretensão salarial?", "valor": ""},
        {"chave": "#cv", "tipo": "arquivo", "tipo_html": "file", "rotulo": "Anexe seu currículo", "valor": ""},
        {"chave": "#termos", "tipo": "caixa", "tipo_html": "checkbox", "rotulo": "Li e aceito os termos de uso", "valor": "nao"},
        {"chave": "#lider", "tipo": "caixa", "tipo_html": "checkbox", "rotulo": "Possui experiência com liderança de equipe?",
         "valor": "nao"},
    ]


def _prefixo(modelo):
    return modelo.rsplit("})(", 1)[0]


def _args(js):
    return json.loads("[" + js.rsplit("})(", 1)[1].rstrip()[:-1] + "]")


class PaginaFalsa:
    """Imita a aba: responde aos JavaScripts do módulo pelo modelo, guarda o que foi digitado e as teclas."""

    def __init__(self, url=URL_GUPY, campos=None, titulos="Candidatura", texto="Perguntas da vaga", iframes=(),
                 senhas=0, foco_em_botao=(), login_campos=None):
        self._url, self.campos = url, campos if campos is not None else campos_exemplo()
        self.titulos, self.texto, self.iframes, self.senhas = titulos, texto, list(iframes), senhas
        self.foco_em_botao, self.login_campos = set(foco_em_botao), login_campos or {}
        self.ativo, self.digitado, self.teclas, self.js = None, [], 0, []

    def _c(self, chave):
        return next(c for c in self.campos if c["chave"] == chave)

    def _marcada(self, c, i):
        if c["tipo"] == "unica":
            return c["valor"] == str(i)
        if c["tipo"] == "multipla":
            return str(i) in c["valor"].split(",")
        return c["valor"] == "sim"

    def url(self):
        return self._url

    def fechar(self):
        pass

    def avaliar(self, js):
        self.js.append(js)
        if js == formulario.JS_LER:
            return {"url": self._url, "titulos": self.titulos, "texto": self.texto, "iframes": self.iframes,
                    "campos": [dict(c, opcoes=list(c.get("opcoes") or [])) for c in self.campos], "senhas": self.senhas,
                    "outros": 0}
        if js in (formulario.JS_SAIR, login.JS_SAIR):
            self.ativo = None
            return True
        if js == login.JS_CAMPOS_LOGIN:
            return self.login_campos
        a = _args(js)
        if js.startswith(_prefixo(formulario.JS_FOCAR)):
            chave, limpar = a
            if chave in self.foco_em_botao:
                self.ativo = None
                return {"ok": True, "tag": "BUTTON", "tipo": "submit", "vazio": True}
            c = self._c(chave)
            if limpar:
                c["valor"] = ""
            self.ativo = (chave, None)
            return {"ok": True, "tag": "TEXTAREA" if c["tipo"] == "area" else "INPUT", "tipo": c["tipo_html"],
                    "vazio": not c["valor"]}
        if js.startswith(_prefixo(formulario.JS_SELECIONAR)):
            chave, i = a
            self._c(chave)["valor"] = str(i)
            return True
        if js.startswith(_prefixo(formulario.JS_FOCAR_OPCAO)):
            chave, i = a
            c = self._c(chave)
            self.ativo = (chave, i)
            return {"ok": True, "marcada": self._marcada(c, i), "tipo": "radio" if c["tipo"] == "unica" else "checkbox"}
        if js.startswith(_prefixo(formulario.JS_MARCADA)):
            chave, i = a
            return self._marcada(self._c(chave), i)
        if js.startswith(_prefixo(login.JS_FOCAR_LOGIN)):
            self.ativo = ("login", a[1])
            return {"ok": True}
        raise AssertionError("JavaScript inesperado: " + js[:80])

    def digitar(self, texto):
        assert self.ativo, "digitou sem foco"
        self.digitado.append((self.ativo[0] if self.ativo[0] != "login" else "login:" + self.ativo[1], texto))
        if self.ativo[0] != "login":
            self._c(self.ativo[0])["valor"] += texto

    def espaco(self):
        assert self.ativo and self.ativo[1] is not None, "espaço sem opção focada"
        self.teclas += 1
        chave, i = self.ativo
        c = self._c(chave)
        if c["tipo"] == "unica":
            c["valor"] = str(i)
        elif c["tipo"] == "multipla":
            marcadas = [v for v in c["valor"].split(",") if v]
            c["valor"] = ",".join(sorted(set(marcadas) ^ {str(i)}))
        else:
            c["valor"] = "nao" if c["valor"] == "sim" else "sim"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for p in (mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                  mock.patch.object(segredos, "ENV", self.tmp / ".env"),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(curriculo_ia, "CURRICULOS", self.tmp / "curriculos"),
                  mock.patch.dict("os.environ", {}, clear=False)):
            p.start()
            self.addCleanup(p.stop)
        for nome in ("LOGIN_GUPY_USUARIO", "LOGIN_GUPY_SENHA"):
            import os
            os.environ.pop(nome, None)

    VAGA = {"id": "v1", "candidatura_assistida": {"ligada": True, "em": "2026-10-24"}}  # ligada nesta vaga
    DESLIGADA = {"id": "v2"}

    def ligar(self):
        pass  # a chave agora é por vaga: os testes passam self.VAGA (ligada)


class TestDominios(Base):
    def test_conhecidos_e_parecidos(self):
        self.assertEqual(dominios.situacao(URL_GUPY)["portal"], "gupy")
        self.assertTrue(dominios.situacao("https://login.gupy.io/candidates/signin")["permitido"])
        self.assertTrue(dominios.situacao("https://boards.greenhouse.io/x/jobs/1")["permitido"])
        self.assertTrue(dominios.situacao("https://empresa.wd5.myworkdayjobs.com/pt-BR/x")["permitido"])
        for url in ("https://gupy.io.exemplo.com/jobs", "https://falsogupy.io/jobs", "https://exemplo.com/gupy.io"):
            s = dominios.situacao(url)
            self.assertFalse(s["permitido"], url)
            self.assertTrue(s["pode_liberar"], url)
        s = dominios.situacao("http://empresaalfa.gupy.io/jobs")  # sem https
        self.assertFalse(s["permitido"])
        self.assertFalse(s["pode_liberar"])

    def test_bloqueados_sem_liberar(self):  # research §1
        for url in ("https://br.indeed.com/viewjob?jk=1", "https://smartapply.indeed.com/x", "https://www.linkedin.com/jobs/1",
                    "https://nerdin.com.br/vaga/1", "https://uk.indeed.co.uk/x"):
            s = dominios.situacao(url)
            self.assertFalse(s["permitido"], url)
            self.assertFalse(s["pode_liberar"], url)
            self.assertTrue(s["bloqueado"], url)
        with self.assertRaises(candidatura.CandidaturaErro):
            dominios.liberar("br.indeed.com")

    def test_liberar_e_revogar(self):
        url = "https://carreiras.empresa.com.br/vaga/1"
        self.assertFalse(dominios.situacao(url)["permitido"])
        dominios.liberar("Carreiras.Empresa.com.br")
        s = dominios.situacao(url)
        self.assertEqual((s["permitido"], s["origem"]), (True, "liberado"))
        self.assertEqual(json.loads(filtros.CONFIG.read_text(encoding="utf-8"))["candidatura"]["dominios"][0]["dominio"],
                         "carreiras.empresa.com.br")
        dominios.revogar("carreiras.empresa.com.br")
        self.assertFalse(dominios.situacao(url)["permitido"])
        for ruim in ("", "https://x.com/a", "x", "a b.com"):
            with self.assertRaises(candidatura.CandidaturaErro):
                dominios.liberar(ruim)

    def test_config_preserva_outras_chaves(self):
        filtros.CONFIG.write_text(json.dumps({"termos": ["analista"], "ia": {"provedor": "nenhum"}}), encoding="utf-8")
        dominios.liberar("carreiras.empresa.com.br")
        cfg = json.loads(filtros.CONFIG.read_text(encoding="utf-8"))
        self.assertEqual((cfg["termos"], cfg["ia"]["provedor"], cfg["candidatura"]["dominios"][0]["dominio"]),
                         (["analista"], "nenhum", "carreiras.empresa.com.br"))


class TestLigar(Base):
    def test_desligada_por_padrao_e_aviso_por_vaga(self):  # US4, FR-006 (vaga a vaga, decisão de 2026-10-24)
        with banco.escrita() as con:
            banco._gravar(con, "v1", {"id": "v1", "titulo": "Analista", "empresa": "Acme"})
            banco._gravar(con, "v2", {"id": "v2", "titulo": "Analista", "empresa": "Beta"})
        self.assertFalse(candidatura.ligada(banco.obter("v1")))
        with self.assertRaises(candidatura.CandidaturaErro):
            candidatura.exigir_ligada(banco.obter("v1"))
        with self.assertRaises(candidatura.CandidaturaErro):
            candidatura.ligar_vaga("v1", True)  # sem o aviso
        self.assertTrue(candidatura.ligada(candidatura.ligar_vaga("v1", True, aceitar_aviso=True)))
        self.assertFalse(candidatura.ligada(banco.obter("v2")))  # só a vaga ligada
        candidatura.ligar_vaga("v1", False)
        self.assertFalse(candidatura.ligada(banco.obter("v1")))
        with self.assertRaises(candidatura.CandidaturaErro):
            candidatura.ligar_vaga("v1", True)  # religar pede o aviso de novo
        with self.assertRaises(KeyError):
            candidatura.ligar_vaga("nao-existe", True, aceitar_aviso=True)

    def test_desligada_recusa_preencher(self):
        for vaga in (self.DESLIGADA, None, {"id": "v3", "candidatura_assistida": {"ligada": False}}):
            aba = PaginaFalsa()
            with self.assertRaises(candidatura.CandidaturaErro):
                formulario.preencher(aba, formulario.ler(aba)["assinatura"], [{"chave": "#exp", "valor": "x"}], vaga)
            with self.assertRaises(candidatura.CandidaturaErro):
                login.preencher_login(PaginaFalsa(url="https://login.gupy.io/candidates/signin"), vaga)
            self.assertEqual(aba.digitado, [])


class TestClassificacao(Base):
    def test_campos(self):
        marcas = {c["chave"]: c["marca"] for c in formulario.ler(PaginaFalsa())["campos"]}
        self.assertEqual(marcas, {"#nome": "cadastro", "#exp": "comum", "#anos": "comum", "n:ingles": "comum",
                                  "radio:remoto": "comum", "check:ferr": "comum", "#salario": "sensivel", "#cv": "arquivo",
                                  "#termos": "consentimento", "#lider": "comum"})
        unico = lambda **c: formulario.classificar_campo({"tipo": "texto", "tipo_html": "text", "rotulo": "", **c})[0]
        self.assertEqual(unico(rotulo="Seu e-mail"), "cadastro")
        self.assertEqual(unico(rotulo="Contato", tipo_html="tel"), "cadastro")
        self.assertEqual(unico(rotulo="Você precisa de visto?"), "sensivel")
        self.assertEqual(unico(rotulo="Pergunta", tipo="senha"), "senha")
        self.assertEqual(unico(rotulo="Início", tipo="data"), "outro")
        self.assertEqual(unico(rotulo=""), "outro")

    def test_paginas(self):
        etapa = lambda **k: formulario.ler(PaginaFalsa(**k))["etapa"]
        self.assertEqual(etapa(), "perguntas")
        self.assertEqual(etapa(iframes=["https://www.google.com/recaptcha/api2/anchor"]), "bloqueio")
        self.assertEqual(etapa(texto="Digite o código de verificação enviado ao seu e-mail"), "bloqueio")
        self.assertEqual(etapa(senhas=1), "login")
        self.assertEqual(etapa(titulos="Teste de perfil comportamental"), "teste")
        self.assertEqual(etapa(campos=[]), "desconhecida")
        # "teste técnico" na descrição da vaga não bloqueia o formulário (só os títulos contam)
        self.assertEqual(etapa(texto="Etapas: triagem, teste técnico e entrevista"), "perguntas")

    def test_assinatura_muda_com_a_pagina(self):
        a = formulario.ler(PaginaFalsa())["assinatura"]
        outra = campos_exemplo()[:3]
        self.assertNotEqual(a, formulario.ler(PaginaFalsa(campos=outra))["assinatura"])
        self.assertEqual(a, formulario.ler(PaginaFalsa())["assinatura"])


class TestPreencher(Base):
    def respostas(self, **extra):
        r = {"#exp": "Escrevo SQL avançado para o time de vendas.", "#anos": "4", "n:ingles": "3", "radio:remoto": "0",
             "check:ferr": "0,1", "#lider": "sim",
             # o que não é comum é ignorado, mesmo se vier
             "#salario": "R$ 10.000", "#nome": "Outro Nome", "#termos": "sim", "#cv": "C:/arquivo.pdf"}
        r.update(extra)
        return [{"chave": k, "valor": v} for k, v in r.items()]

    def test_preenche_so_os_comuns(self):  # US1, FR-001, FR-004
        self.ligar()
        aba = PaginaFalsa()
        r = formulario.preencher(aba, formulario.ler(aba)["assinatura"], self.respostas(), self.VAGA)
        valores = {c["chave"]: c["valor"] for c in aba.campos}
        self.assertEqual(valores["#exp"], "Escrevo SQL avançado para o time de vendas.")
        self.assertEqual((valores["#anos"], valores["n:ingles"], valores["radio:remoto"], valores["check:ferr"],
                          valores["#lider"]), ("4", "3", "0", "0,1", "sim"))
        self.assertEqual((valores["#salario"], valores["#nome"], valores["#termos"], valores["#cv"]),
                         ("", "Pessoa Teste", "nao", ""))
        self.assertEqual({p["chave"] for p in r["preenchidos"]}, {"#exp", "#anos", "n:ingles", "radio:remoto", "check:ferr", "#lider"})
        self.assertEqual({p["chave"]: p["texto"] for p in r["preenchidos"]}["check:ferr"], "Excel; Power BI")
        motivos = {f["chave"]: f["motivo"] for f in r["ficaram"]}
        self.assertIn("pretensão", motivos["#salario"].replace("salário ou pretensão", "pretensão"))
        self.assertIn("anexo", motivos["#cv"])
        self.assertIn("termos", motivos["#termos"])
        self.assertIn("Continuar ou Enviar", r["aviso"])
        self.assertEqual(aba.teclas, 4)  # radio, duas caixas da lista e a caixa de liderança

    def test_nao_pisa_em_valor_existente(self):  # FR-014
        self.ligar()
        campos = campos_exemplo()
        campos[1]["valor"] = "Texto que a pessoa já escreveu"
        aba = PaginaFalsa(campos=campos)
        a = formulario.ler(aba)["assinatura"]
        r = formulario.preencher(aba, a, [{"chave": "#exp", "valor": "Novo"}], self.VAGA)
        self.assertEqual(aba._c("#exp")["valor"], "Texto que a pessoa já escreveu")
        self.assertIn("mantido", r["ficaram"][0]["motivo"])
        r = formulario.preencher(aba, formulario.ler(aba)["assinatura"], [{"chave": "#exp", "valor": "Novo", "trocar": True}], self.VAGA)
        self.assertEqual(aba._c("#exp")["valor"], "Novo")

    def test_limite_e_numero(self):  # FR-010
        self.ligar()
        aba = PaginaFalsa()
        longo = "Escrevo SQL avançado " * 20
        r = formulario.preencher(aba, formulario.ler(aba)["assinatura"],
                                 [{"chave": "#exp", "valor": longo}, {"chave": "#anos", "valor": "quatro anos"}], self.VAGA)
        self.assertLessEqual(len(aba._c("#exp")["valor"]), 120)
        self.assertEqual(aba._c("#anos")["valor"], "")
        self.assertIn("#anos", {f["chave"] for f in r["ficaram"]})

    def test_foco_errado_nao_digita(self):  # nunca digita num botão
        self.ligar()
        aba = PaginaFalsa(foco_em_botao={"#exp"})
        r = formulario.preencher(aba, formulario.ler(aba)["assinatura"], [{"chave": "#exp", "valor": "texto"}], self.VAGA)
        self.assertEqual(aba.digitado, [])
        self.assertEqual(r["preenchidos"], [])

    def test_pagina_mudou_dominio_e_bloqueio(self):  # FR-003, FR-005, FR-015
        self.ligar()
        aba = PaginaFalsa()
        with self.assertRaisesRegex(candidatura.CandidaturaErro, "mudou"):
            formulario.preencher(aba, "assinatura-velha", self.respostas(), self.VAGA)
        for url in ("https://carreiras.empresa.com.br/x", "https://br.indeed.com/x", "https://gupy.io.exemplo.com/x"):
            aba = PaginaFalsa(url=url)
            with self.assertRaises(candidatura.CandidaturaErro):
                formulario.preencher(aba, formulario.ler(aba)["assinatura"], self.respostas(), self.VAGA)
            self.assertEqual(aba.digitado, [])
        aba = PaginaFalsa(iframes=["https://challenges.cloudflare.com/turnstile"])
        with self.assertRaises(candidatura.CandidaturaErro):
            formulario.preencher(aba, formulario.ler(aba)["assinatura"], self.respostas(), self.VAGA)
        self.assertEqual((aba.digitado, aba.teclas), ([], 0))

    def test_um_por_vez(self):
        self.ligar()
        aba = PaginaFalsa()
        with candidatura.TRAVA:
            with self.assertRaisesRegex(candidatura.CandidaturaErro, "andamento"):
                formulario.preencher(aba, formulario.ler(aba)["assinatura"], self.respostas(), self.VAGA)

    def test_javascript_nunca_clica_nem_envia(self):  # SC-002
        textos = [v for m in (formulario, login) for v in vars(m).values() if isinstance(v, str) and "=>" in v]
        self.assertGreaterEqual(len(textos), 7)
        for js in textos:
            self.assertNotRegex(js, r"\.click\(|submit\(|requestSubmit|\bEnter\b|fetch\(|XMLHttpRequest|sendBeacon|"
                                    r"\.href\s*=|location\.(assign|replace)|window\.open")
        for metodo in ("digitar", "espaco"):  # o navegador só ganhou digitação e espaço, não clique
            self.assertTrue(hasattr(__import__("navegador").Aba, metodo))
        fonte = (RAIZ / "navegador.py").read_text(encoding="utf-8")
        self.assertNotIn("dispatchMouseEvent", fonte)
        self.assertNotIn("Enter", re.sub(r'""".*?"""', "", fonte, flags=re.S))


class TestLogin(Base):
    URL_LOGIN = "https://login.gupy.io/candidates/signin"

    def guardar(self):
        login.gravar("gupy", "pessoa@exemplo.com", SENHA)

    def test_guarda_no_env_e_mostra_so_o_final(self):  # FR-021, FR-022
        self.guardar()
        self.assertEqual(login.credencial("gupy"), ("pessoa@exemplo.com", SENHA))
        self.assertIn("LOGIN_GUPY_SENHA=", segredos.ENV.read_text(encoding="utf-8"))
        pagina = login.para_pagina()
        self.assertNotIn(SENHA, json.dumps(pagina))
        gupy = next(p for p in pagina if p["portal"] == "gupy")
        self.assertEqual((gupy["usuario"], gupy["final"], gupy["guardada"]), ("pessoa@exemplo.com", SENHA[-4:], True))
        login.apagar("gupy")
        self.assertIsNone(login.credencial("gupy"))
        with self.assertRaises(candidatura.CandidaturaErro):
            login.gravar("lever", "a", "b")  # sem login central

    def test_aspas_e_espacos_sobrevivem(self):
        for senha in ('"entre aspas"', " espaço ", "b64:literal", "fim'"):
            login.gravar("gupy", "u@exemplo.com", senha)
            self.assertEqual(login.credencial("gupy")[1], senha)
        segredos.gravar("LOGIN_GUPY_SENHA", "escrita-a-mao")  # escrita direto no .env, sem prefixo
        self.assertEqual(login.credencial("gupy")[1], "escrita-a-mao")

    def test_preenche_so_no_host_exato(self):  # FR-023, FR-024
        self.ligar()
        self.guardar()
        campos = {"senhas": 1, "usuario": 0, "senha": 1}
        aba = PaginaFalsa(url=self.URL_LOGIN, login_campos=campos)
        r = login.preencher_login(aba, self.VAGA)
        self.assertEqual(aba.digitado, [("login:usuario", "pessoa@exemplo.com"), ("login:senha", SENHA)])
        self.assertNotIn(SENHA, json.dumps(r))
        self.assertEqual(aba.teclas, 0)
        for url in ("https://login.gupy.io.exemplo.com/signin", "https://empresaalfa.gupy.io/login",
                    "http://login.gupy.io/candidates/signin", "https://login-gupy.io/x"):
            aba = PaginaFalsa(url=url, login_campos=campos)
            with self.assertRaises(candidatura.CandidaturaErro) as e:
                login.preencher_login(aba, self.VAGA)
            self.assertEqual(aba.digitado, [], url)
            self.assertNotIn(SENHA, str(e.exception))

    def test_dois_campos_de_senha_e_sem_credencial(self):
        self.ligar()
        aba = PaginaFalsa(url=self.URL_LOGIN, login_campos={"senhas": 1, "usuario": 0, "senha": 1})
        with self.assertRaisesRegex(candidatura.CandidaturaErro, "nenhuma credencial"):
            login.preencher_login(aba, self.VAGA)
        self.guardar()
        aba = PaginaFalsa(url=self.URL_LOGIN, login_campos={"senhas": 2, "usuario": 0, "senha": -1})
        with self.assertRaises(candidatura.CandidaturaErro):
            login.preencher_login(aba, self.VAGA)
        self.assertEqual(aba.digitado, [])

    def test_login_em_duas_etapas(self):  # primeiro só o e-mail, depois só a senha
        self.ligar()
        self.guardar()
        aba = PaginaFalsa(url=self.URL_LOGIN, login_campos={"senhas": 0, "usuario": 0, "senha": -1})
        self.assertEqual(login.preencher_login(aba, self.VAGA)["preenchidos"], ["usuario"])
        aba = PaginaFalsa(url=self.URL_LOGIN, login_campos={"senhas": 1, "usuario": -1, "senha": 0})
        self.assertEqual(login.preencher_login(aba, self.VAGA)["preenchidos"], ["senha"])

    def test_erro_do_navegador_nao_vaza_senha(self):
        self.ligar()
        self.guardar()
        aba = PaginaFalsa(url=self.URL_LOGIN, login_campos={"senhas": 1, "usuario": 0, "senha": 1})

        def falha(texto):
            raise RuntimeError(f"falhou ao digitar {texto}")
        aba.digitar = falha
        with self.assertRaises(candidatura.CandidaturaErro) as e:
            login.preencher_login(aba, self.VAGA)
        self.assertNotIn(SENHA, str(e.exception))
        self.assertNotIn("pessoa@exemplo.com", str(e.exception))


class TestPropostas(Base):
    def setUp(self):
        super().setUp()
        self.pedidos = []
        self.resposta = "[]"
        for p in (mock.patch.object(candidatura_ia, "_ia_responder", side_effect=self._ia),
                  mock.patch.object(ia, "disponivel", return_value=True),
                  mock.patch.object(candidatura_ia, "_marca_ia", return_value={"provedor": "falso", "modelo": "x"})):
            p.start()
            self.addCleanup(p.stop)

    def _ia(self, pedido):
        self.pedidos.append(pedido)
        return self.resposta

    def propor(self):
        campos = formulario.ler(PaginaFalsa())["campos"]
        return {x["chave"]: x for x in candidatura_ia.propor_respostas(VAGA, campos, perfil=PERFIL)["itens"]}

    def test_formatos(self):  # FR-008 a FR-011, SC-006
        self.resposta = json.dumps([
            {"indice": 2, "resposta": "Escrevo SQL avançado para o time de vendas. " * 6},
            {"indice": 3, "resposta": "4"},
            {"indice": 4, "resposta": "avancado"},
            {"indice": 5, "resposta": "Talvez"},  # não é opção
            {"indice": 6, "resposta": ["Excel", "power bi", "Looker"]},
            {"indice": 10, "resposta": "sem base"},
            {"indice": 7, "resposta": "R$ 99.000"},  # sensível: descartada
            {"indice": 1, "resposta": "Nome Inventado"},  # cadastro: descartada
        ])
        itens = self.propor()
        self.assertLessEqual(len(itens["#exp"]["proposta"]), 120)
        self.assertTrue(itens["#exp"]["proposta"].startswith("Escrevo SQL"))
        self.assertEqual((itens["#anos"]["proposta"], itens["n:ingles"]["proposta"], itens["radio:remoto"]["proposta"],
                          itens["check:ferr"]["proposta"], itens["#lider"]["proposta"]), ("4", "3", "", "0,1", ""))
        self.assertEqual((itens["#salario"]["proposta"], itens["#nome"]["proposta"]), ("", ""))

    def test_pedido_sem_sensiveis_nem_credencial(self):  # FR-011, FR-012, SC-003
        login.gravar("gupy", "pessoa@exemplo.com", SENHA)
        self.propor()
        pedido = self.pedidos[0]
        self.assertNotIn("pretensão", pedido)
        self.assertNotIn("Nome completo", pedido)
        self.assertNotIn("termos de uso", pedido)
        self.assertNotIn(SENHA, pedido)
        self.assertNotIn("pessoa@exemplo.com", pedido)
        self.assertNotIn("Pessoa Teste", pedido)  # valor que já estava na página não vai à IA
        self.assertIn("Avançado", pedido)  # as opções vão, para a IA escolher entre elas

    def test_sem_ia_e_com_falha(self):  # caso de borda: a pessoa escreve e preenche igual
        with mock.patch.object(ia, "disponivel", return_value=False):
            campos = formulario.ler(PaginaFalsa())["campos"]
            r = candidatura_ia.propor_respostas(VAGA, campos, perfil=PERFIL)
        self.assertIn("Sem IA", r["aviso"])
        self.assertTrue(all(x["proposta"] == "" for x in r["itens"]))
        self.resposta = "não é JSON"
        r = candidatura_ia.propor_respostas(VAGA, formulario.ler(PaginaFalsa())["campos"], perfil=PERFIL)
        self.assertIn("preencha igual", r["aviso"])

    def test_grava_no_kit(self):  # FR-016
        meta = candidatura_ia.gravar_preenchidas(dict(VAGA, id="v1"), [{"rotulo": "Nível de inglês", "texto": "Avançado"}])
        self.assertEqual((meta["tipo"], meta["origem"], meta["itens"][0]["resposta"]), ("respostas", "candidatura_assistida", "Avançado"))
        self.assertEqual(candidatura_ia.listar("v1")[0]["nome"], meta["nome"])


class TestRotas(Base):
    def setUp(self):
        super().setUp()
        import servidor
        import sincronia
        self.servidor, self.nav = servidor, sincronia.navegador
        p = mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})
        p.start()
        self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        with banco.escrita() as con:
            banco._gravar(con, "v1", {**VAGA, "id": "v1", "url": URL_GUPY, "triagem": "seguir", "etapa": "salva"})

    def pedir(self, metodo, caminho, corpo=None):
        con = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        bruto = r.read().decode("utf-8")
        return r.status, json.loads(bruto), bruto

    def test_fluxo(self):
        st, j, _ = self.pedir("GET", "/api/candidatura")
        self.assertEqual((st, "ligado" in j, bool(j["aviso"])), (200, False, True))  # sem chave geral
        self.assertEqual(self.pedir("POST", "/api/candidatura/vaga/v1/ler", {})[0], 409)  # desligada na vaga
        self.assertEqual(self.pedir("PUT", "/api/candidatura/vaga/v1", {"ligada": True})[0], 409)  # sem o aviso
        self.assertEqual(self.pedir("PUT", "/api/candidatura/vaga/zz", {"ligada": True, "aceitar_aviso": True})[0], 404)
        st, j, _ = self.pedir("PUT", "/api/candidatura/vaga/v1", {"ligada": True, "aceitar_aviso": True})
        self.assertEqual((st, j["vaga"]["candidatura_assistida"]["ligada"]), (200, True))
        st, j, bruto = self.pedir("PUT", "/api/candidatura/credenciais/gupy", {"usuario": "pessoa@exemplo.com", "senha": SENHA})
        self.assertEqual(st, 200)
        self.assertNotIn(SENHA, bruto)
        self.assertNotIn(SENHA, self.pedir("GET", "/api/candidatura")[2])

        aba = PaginaFalsa(url="https://login.gupy.io/candidates/signin", login_campos={"senhas": 1, "usuario": 0, "senha": 1})
        with mock.patch.object(self.nav, "aba_atual", return_value=aba):
            st, j, bruto = self.pedir("POST", "/api/candidatura/vaga/v1/login", {})
        self.assertEqual(st, 200, bruto)
        self.assertNotIn(SENHA, bruto)
        self.assertIn(("login:senha", SENHA), aba.digitado)

        aba = PaginaFalsa()
        resposta_ia = json.dumps([{"indice": 4, "resposta": "Avançado"}])
        with mock.patch.object(self.nav, "aba_atual", return_value=aba), \
                mock.patch.object(ia, "disponivel", return_value=True), \
                mock.patch.object(candidatura_ia, "_ia_responder", return_value=resposta_ia), \
                mock.patch.object(candidatura_ia, "_marca_ia", return_value={}), \
                mock.patch.object(curriculo_ia, "perfil_texto", return_value=PERFIL):
            st, j, bruto = self.pedir("POST", "/api/candidatura/vaga/v1/ler", {})
            self.assertEqual((st, j["pagina"]["etapa"]), (200, "perguntas"), bruto)
            propostas = {x["chave"]: x["proposta"] for x in j["itens"]}
            self.assertEqual(propostas["n:ingles"], "3")
            respostas = [{"chave": "n:ingles", "valor": "3"}, {"chave": "#exp", "valor": "SQL para vendas."}]
            st, j, bruto = self.pedir("POST", "/api/candidatura/vaga/v1/preencher",
                                      {"assinatura": j["pagina"]["assinatura"], "respostas": respostas})
        self.assertEqual(st, 200, bruto)
        self.assertEqual(len(j["preenchidos"]), 2)
        self.assertTrue(j["documento"])
        self.assertEqual(aba._c("n:ingles")["valor"], "3")

    def test_dominio_nao_liberado_e_rede(self):
        self.pedir("PUT", "/api/candidatura/vaga/v1", {"ligada": True, "aceitar_aviso": True})
        aba = PaginaFalsa(url="https://carreiras.empresa.com.br/vaga")
        with mock.patch.object(self.nav, "aba_atual", return_value=aba), \
                mock.patch.object(candidatura_ia, "_ia_responder") as chamada:
            st, j, _ = self.pedir("POST", "/api/candidatura/vaga/v1/ler", {})
            self.assertEqual((st, j["pagina"]["dominio"]["pode_liberar"], j["itens"]), (200, True, []))
            chamada.assert_not_called()  # nada vai à IA antes de liberar
        st, j, _ = self.pedir("POST", "/api/candidatura/dominios", {"dominio": "carreiras.empresa.com.br", "acao": "liberar"})
        self.assertEqual(j["dominios"]["liberados"][0]["dominio"], "carreiras.empresa.com.br")
        self.assertEqual(self.pedir("POST", "/api/candidatura/dominios", {"dominio": "br.indeed.com", "acao": "liberar"})[0], 409)
        with mock.patch.object(self.servidor.Handler, "_local", return_value=False):
            self.assertEqual(self.pedir("GET", "/api/candidatura")[0], 403)
            self.assertEqual(self.pedir("POST", "/api/candidatura/vaga/v1/login", {})[0], 403)
            self.assertEqual(self.pedir("PUT", "/api/candidatura/vaga/v1", {"ligada": False})[0], 403)


if __name__ == "__main__":
    unittest.main()
