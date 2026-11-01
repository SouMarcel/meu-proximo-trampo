"""Aba falsa da janela da ferramenta para os portais com login (spec 041): sem navegador e sem rede. Responde aos
três scripts de leitura de fontes/_sessao.py (data-page, captcha e fetch) e guarda tudo o que foi pedido."""
import json


class SessaoFalsa:
    def __init__(self):
        self.pedidos = []

    def pedir(self, metodo, **params):
        self.pedidos.append((metodo, params))
        return {}


class AbaFalsa:
    def __init__(self, url="https://my.greenhouse.io/jobs/search", respostas=None, data_page=None, captcha=False):
        self.historico = [url]
        self.respostas = list(respostas or [])  # {"status", "dados", "url"?} na ordem dos fetch
        self.data_page = data_page
        self.captcha = captcha
        self.scripts, self.pedidos, self.idas = [], [], []
        self.frentes = self.minimizacoes = 0
        self.fechada = False
        self.ao_ir = None  # url -> endereço depois da carga (ex.: o login caído leva a /users/sign_in)
        self.erro = None  # exceção levantada em endereco() (janela fechada)
        self.sessao = SessaoFalsa()

    def endereco(self):
        if self.erro:
            raise self.erro
        return self.historico[-1]

    url = endereco

    def avaliar(self, js):
        self.scripts.append(js)
        if "data-page" in js:
            return self.data_page
        if "recaptcha" in js:
            return self.captcha
        if "fetch(" in js:
            url = json.loads(js.split("fetch(", 1)[1].split(", {credentials", 1)[0])
            self.pedidos.append(url)
            r = self.respostas.pop(0) if self.respostas else {"status": 200, "dados": None}
            if isinstance(r, Exception):
                raise r
            return {"status": r.get("status", 200), "dados": r.get("dados"), "url": r.get("url", url)}
        raise AssertionError(f"script inesperado: {js[:80]}")

    def ir(self, url):
        self.idas.append(url)
        self.historico.append(self.ao_ir(url) if self.ao_ir else url)

    def frente(self):
        self.frentes += 1

    def minimizar(self):
        self.minimizacoes += 1

    def fechar(self):
        pass

    def fechar_aba(self):
        self.fechada = True
