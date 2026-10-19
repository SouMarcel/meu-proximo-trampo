"""Navegador da ferramenta: uma janela do Edge (ou do Chrome) com um perfil só da ferramenta, para as contas
conectadas (spec 018; constituição, princípio VI, "Conta conectada").

A pessoa faz o login nos portais nessa janela; a ferramenta nunca vê nem guarda senha e não copia cookies para fora
do navegador. A conversa com a janela é pelo protocolo de depuração do navegador (DevTools Protocol), por WebSocket,
só com a biblioteca padrão: abrir uma página, esperar carregar e ler o que ela mostra (Runtime.evaluate). Nada de
clicar em botões do portal.

  achar()                   caminho do Edge ou do Chrome, ou None
  aberto()                  a janela da ferramenta está aberta (porta de depuração respondendo)
  abrir(url, minimizado)    abre a janela (ou uma aba nela) na URL; devolve a Aba
  Aba.ir(url) / .avaliar(js) / .url() / .fechar()
  fechar()                  fecha a janela da ferramenta
  desconectar()             fecha a janela e apaga o perfil (as sessões dos portais)

O perfil fica em .cache/navegador (fora do Git). A porta de depuração só existe enquanto a janela está aberta e só
aceita conexões deste computador.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

RAIZ = Path(__file__).resolve().parent
PERFIL = RAIZ / ".cache" / "navegador"
CANDIDATOS = (
    r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
    r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
    r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
    r"%LocalAppData%\Google\Chrome\Application\chrome.exe",
    "/usr/bin/microsoft-edge", "/usr/bin/google-chrome", "/usr/bin/chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)
TEMPO_ABRIR = 20
TEMPO_PEDIDO = 30
LIMITE_QUADRO = 50_000_000


class NavegadorErro(Exception):
    """Mensagem legível para a pessoa (sem caminhos internos nem dados da página)."""


def achar(candidatos=CANDIDATOS) -> str | None:
    for c in candidatos:
        p = Path(os.path.expandvars(c))
        if "%" not in str(p) and p.is_file():
            return str(p)
    return None


# ---------------------------------------------------------------- porta de depuração

def _porta() -> int | None:
    """A porta que o navegador escreveu no perfil (DevToolsActivePort), se a janela está aberta."""
    try:
        linha = (PERFIL / "DevToolsActivePort").read_text(encoding="utf-8").splitlines()[0].strip()
        return int(linha)
    except (OSError, ValueError, IndexError):
        return None


def _http(caminho: str, metodo: str = "GET", porta: int | None = None):
    porta = porta or _porta()
    if not porta:
        raise NavegadorErro("a janela da ferramenta não está aberta")
    req = urllib.request.Request(f"http://127.0.0.1:{porta}{caminho}", method=metodo)
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read() or b"null")


def aberto() -> bool:
    try:
        _http("/json/version")
        return True
    except (NavegadorErro, OSError, ValueError):
        return False


# ---------------------------------------------------------------- WebSocket mínimo (RFC 6455, cliente)

def quadro(texto: str, mascara: bytes | None = None) -> bytes:
    """Um quadro de texto do cliente (com máscara, como a RFC pede)."""
    dados = texto.encode("utf-8")
    mascara = mascara if mascara is not None else os.urandom(4)
    n = len(dados)
    if n < 126:
        cab = struct.pack("!BB", 0x81, 0x80 | n)
    elif n < 1 << 16:
        cab = struct.pack("!BBH", 0x81, 0x80 | 126, n)
    else:
        cab = struct.pack("!BBQ", 0x81, 0x80 | 127, n)
    return cab + mascara + bytes(b ^ mascara[i % 4] for i, b in enumerate(dados))


def ler_quadro(ler) -> tuple[int, bool, bytes]:
    """(opcode, final, dados) do próximo quadro; ler(n) devolve exatamente n bytes."""
    b1, b2 = ler(2)
    final, opcode, mascarado, n = bool(b1 & 0x80), b1 & 0x0F, bool(b2 & 0x80), b2 & 0x7F
    if n == 126:
        n = struct.unpack("!H", ler(2))[0]
    elif n == 127:
        n = struct.unpack("!Q", ler(8))[0]
    if n > LIMITE_QUADRO:
        raise NavegadorErro("resposta grande demais do navegador")
    mascara = ler(4) if mascarado else b""
    dados = ler(n)
    if mascarado:
        dados = bytes(b ^ mascara[i % 4] for i, b in enumerate(dados))
    return opcode, final, dados


class _WS:
    def __init__(self, url: str):
        p = urlsplit(url)
        if p.hostname not in ("127.0.0.1", "localhost"):
            raise NavegadorErro("endereço de depuração inesperado")
        try:
            self.sock = socket.create_connection((p.hostname, p.port), timeout=TEMPO_PEDIDO)
            chave = base64.b64encode(os.urandom(16)).decode()
            self.sock.sendall((f"GET {p.path} HTTP/1.1\r\nHost: {p.hostname}:{p.port}\r\nUpgrade: websocket\r\n"
                               f"Connection: Upgrade\r\nSec-WebSocket-Key: {chave}\r\nSec-WebSocket-Version: 13\r\n\r\n")
                              .encode())
            resposta = b""
            while b"\r\n\r\n" not in resposta:
                parte = self.sock.recv(4096)
                if not parte:
                    raise NavegadorErro("o navegador fechou a conexão")
                resposta += parte
        except OSError:
            raise NavegadorErro("a janela da ferramenta não respondeu (foi fechada?)") from None
        cabecalho, self._sobra = resposta.split(b"\r\n\r\n", 1)
        if b" 101 " not in cabecalho.split(b"\r\n", 1)[0]:
            raise NavegadorErro("o navegador recusou a conexão de depuração")

    def _ler(self, n: int) -> bytes:
        buf = self._sobra[:n]
        self._sobra = self._sobra[n:]
        while len(buf) < n:
            parte = self.sock.recv(min(65536, n - len(buf)))
            if not parte:
                raise NavegadorErro("o navegador fechou a conexão")
            buf += parte
        return buf

    def enviar(self, texto: str) -> None:
        self.sock.sendall(quadro(texto))

    def receber(self) -> str:
        partes = []
        while True:
            opcode, final, dados = ler_quadro(self._ler)
            if opcode == 0x8:
                raise NavegadorErro("o navegador fechou a conexão")
            if opcode == 0x9:  # ping: responde pong
                self.sock.sendall(struct.pack("!BB", 0x8A, 0x80 | len(dados)) + b"\0\0\0\0" + dados)
                continue
            if opcode in (0x1, 0x0, 0x2):
                partes.append(dados)
                if final:
                    return b"".join(partes).decode("utf-8", errors="replace")

    def fechar(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class _Sessao:
    """Uma conexão do protocolo de depuração: pedidos com id e respostas casadas pelo id."""

    def __init__(self, url_ws: str):
        self.ws = _WS(url_ws)
        self._id = 0

    def pedir(self, metodo: str, **params):
        self._id += 1
        meu = self._id
        try:
            self.ws.enviar(json.dumps({"id": meu, "method": metodo, "params": params}))
            limite = time.monotonic() + TEMPO_PEDIDO
            while time.monotonic() < limite:
                msg = json.loads(self.ws.receber())
                if msg.get("id") == meu:
                    if "error" in msg:
                        raise NavegadorErro(f"o navegador não fez {metodo}: {msg['error'].get('message', '')}")
                    return msg.get("result") or {}
        except (OSError, ValueError):  # janela fechada no meio, resposta cortada
            raise NavegadorErro("a janela da ferramenta não respondeu (foi fechada?)") from None
        raise NavegadorErro("o navegador demorou demais para responder")

    def fechar(self) -> None:
        self.ws.fechar()


# ---------------------------------------------------------------- janela e abas

class Aba:
    def __init__(self, info: dict):
        self.id = info["id"]
        self.sessao = _Sessao(info["webSocketDebuggerUrl"])

    def avaliar(self, js: str):
        """Valor (JSON) de uma expressão JavaScript na página; promessas são esperadas. Só leitura: o código passado
        aqui nunca clica em botões nem envia formulários do portal."""
        r = self.sessao.pedir("Runtime.evaluate", expression=js, returnByValue=True, awaitPromise=True)
        if r.get("exceptionDetails"):
            raise NavegadorErro("a página não deixou ler o conteúdo")
        return (r.get("result") or {}).get("value")

    def url(self) -> str:
        return self.avaliar("location.href") or ""

    def esperar_carregar(self, tempo: float = TEMPO_PEDIDO, calma: float = 1.5) -> None:
        """Espera o documento carregar e mais um pouco para a página montar a lista (páginas feitas em JavaScript)."""
        limite = time.monotonic() + tempo
        while time.monotonic() < limite:
            try:
                if self.avaliar("document.readyState") == "complete":
                    time.sleep(calma)
                    return
            except NavegadorErro:
                pass
            time.sleep(0.3)

    def ir(self, url: str) -> None:
        self.sessao.pedir("Page.navigate", url=url)
        self.esperar_carregar()

    def _estado_janela(self, estado: str) -> None:
        try:
            janela = self.sessao.pedir("Browser.getWindowForTarget").get("windowId")
            if janela:
                self.sessao.pedir("Browser.setWindowBounds", windowId=janela, bounds={"windowState": estado})
        except NavegadorErro:
            pass

    def frente(self) -> None:
        """Traz a janela para a frente (login, captcha ou verificação que a pessoa precisa resolver)."""
        self._estado_janela("normal")
        try:
            self.sessao.pedir("Page.bringToFront")
        except NavegadorErro:
            pass

    def minimizar(self) -> None:
        self._estado_janela("minimized")

    def fechar(self) -> None:
        self.sessao.fechar()


def abrir(url: str, minimizado: bool = False) -> Aba:
    """Abre a janela da ferramenta na URL e devolve a Aba. Se a janela já está aberta, usa a aba que ela tem (sem
    acumular abas) e só navega até a URL."""
    if aberto():
        paginas = [a for a in _http("/json/list") if a.get("type") == "page" and a.get("webSocketDebuggerUrl")]
        if paginas:
            aba = Aba(paginas[0])
            aba.ir(url)
            if not minimizado:
                aba.frente()
            return aba
    if not aberto():
        exe = achar()
        if not exe:
            raise NavegadorErro("não achei o Edge nem o Chrome neste computador")
        PERFIL.mkdir(parents=True, exist_ok=True)
        (PERFIL / "DevToolsActivePort").unlink(missing_ok=True)
        args = [exe, f"--user-data-dir={PERFIL}", "--remote-debugging-port=0", "--no-first-run",
                "--no-default-browser-check", "--disable-sync"]
        if minimizado:
            args.append("--start-minimized")
        subprocess.Popen(args + [url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        limite = time.monotonic() + TEMPO_ABRIR
        while not aberto():
            if time.monotonic() > limite:
                raise NavegadorErro("o navegador não abriu a tempo")
            time.sleep(0.3)
        alvo = None
        while alvo is None and time.monotonic() < limite + 5:  # a aba começa em about:blank e só depois vai à URL
            paginas = [a for a in _http("/json/list") if a.get("type") == "page"]
            alvo = next((a for a in paginas if not a.get("url", "").startswith("about:")), None)
            if alvo is None:
                time.sleep(0.3)
        alvo = alvo or _http(f"/json/new?{url}", "PUT")
    else:
        alvo = _http(f"/json/new?{url}", "PUT")
    aba = Aba(alvo)
    aba.esperar_carregar()
    return aba


def fechar() -> None:
    if not aberto():
        return
    try:
        s = _Sessao(_http("/json/version")["webSocketDebuggerUrl"])
        try:
            s.pedir("Browser.close")
        finally:
            s.fechar()
    except (NavegadorErro, OSError, ValueError, KeyError):
        pass
    limite = time.monotonic() + 10
    while aberto() and time.monotonic() < limite:
        time.sleep(0.3)


def desconectar() -> None:
    """Fecha a janela e apaga o perfil da ferramenta: as sessões de todos os portais somem."""
    fechar()
    for _ in range(10):  # o navegador pode demorar a soltar os arquivos
        try:
            shutil.rmtree(PERFIL)
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(0.5)
    shutil.rmtree(PERFIL, ignore_errors=True)
