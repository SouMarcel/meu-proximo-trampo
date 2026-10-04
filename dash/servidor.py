#!/usr/bin/env python3
"""Servidor local do dashboard de candidaturas (só biblioteca padrão).

  python dash/servidor.py                 abre em http://127.0.0.1:8765
  python dash/servidor.py --rede          aceita acesso de outros aparelhos da sua rede (ex.: celular no mesmo Wi-Fi)
  python dash/servidor.py --sem-navegador não abre o navegador

Feche a janela (ou Ctrl+C) para parar. Os dados ficam em dash/dados/candidaturas.db.
"""
from __future__ import annotations

import argparse
import json
import socket
import sys
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(1, str(Path(__file__).resolve().parent.parent))
import analise  # noqa: E402  (análise automática pelo Claude Code)
import banco  # noqa: E402
import filtros  # noqa: E402  (filtros.py, na raiz: lê e grava os filtros da busca no config.json)
from fontes import link  # noqa: E402  (lê a vaga a partir do link)

PAGINA = banco.DASH / "dashboard.html"
PORTA_PADRAO = 8765
LIMITE_CORPO = 1_000_000


def ip_da_rede() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "Candidaturas/1.0"
    hosts_permitidos: set[str] = set()

    def log_message(self, fmt, *args):  # silencioso; erros vão para stderr em _erro
        pass

    # ---------- utilidades
    def _enviar(self, status: int, corpo: bytes, tipo: str):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(corpo)

    def _json(self, status: int, obj):
        self._enviar(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _erro(self, status: int, msg: str):
        self._json(status, {"erro": msg})

    def _host_ok(self) -> bool:
        """Bloqueia DNS rebinding: só atende pelos nomes esperados."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in self.hosts_permitidos

    def _escrita_ok(self) -> bool:
        """Bloqueia pedidos de outros sites (CSRF): exige JSON e origem igual à própria página."""
        if not (self.headers.get("Content-Type") or "").lower().startswith("application/json"):
            return False
        origem = self.headers.get("Origin")
        return origem is None or origem == f"http://{self.headers.get('Host')}"

    def _corpo(self) -> dict:
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > LIMITE_CORPO:
            raise ValueError("pedido grande demais")
        dados = json.loads(self.rfile.read(tamanho) or b"{}")
        if not isinstance(dados, dict):
            raise ValueError("esperava um objeto JSON")
        return dados

    def _id_da_rota(self, caminho: str) -> str | None:
        prefixo = "/api/vagas/"
        if not caminho.startswith(prefixo):
            return None
        vid = unquote(caminho[len(prefixo):])
        return vid if banco.ID_VALIDO.match(vid) else None

    def _tratar(self, metodo: str):
        if not self._host_ok():
            return self._erro(421, "host não permitido")
        caminho = urlsplit(self.path).path
        try:
            if metodo == "GET":
                return self._get(caminho)
            if not self._escrita_ok():
                return self._erro(403, "pedido recusado")
            if metodo == "POST" and caminho == "/api/vagas":
                vaga = banco.criar_manual(self._corpo())
                auto = analise.precisa(vaga) and analise.FILA.pedir()
                return self._json(201, {"vaga": vaga, "analise_automatica": auto})
            if metodo == "POST" and caminho == "/api/vagas/link":
                url = str(self._corpo().get("url") or "").strip()[:1000]
                try:
                    dados = link.ler(url)
                except link.LinkErro as e:  # o dashboard abre o formulário com o que deu para ler
                    return self._json(422, {"erro": str(e), "parcial": {**e.parcial, "url": url}})
                vaga, nova = banco.criar_de_link(dados)
                auto = nova and analise.precisa(vaga) and analise.FILA.pedir()
                return self._json(201 if nova else 200, {"vaga": vaga, "nova": nova, "analise_automatica": auto})
            if metodo == "PUT" and caminho == "/api/config":
                return self._json(200, self._config(filtros.salvar(self._corpo())))
            vid = self._id_da_rota(caminho)
            if vid is None:
                return self._erro(404, "rota não encontrada")
            if metodo == "PATCH":
                return self._json(200, {"vaga": banco.atualizar_usuario(vid, self._corpo())})
            if metodo == "DELETE":
                banco.remover(vid)
                return self._json(200, {"ok": True})
            return self._erro(405, "método não permitido")
        except KeyError:
            return self._erro(404, "vaga não encontrada")
        except (ValueError, json.JSONDecodeError) as e:
            return self._erro(400, str(e))
        except Exception as e:  # registra e devolve erro genérico
            print(f"[erro] {metodo} {caminho}: {e!r}", file=sys.stderr)
            return self._erro(500, "erro interno no servidor do dashboard")

    def _get(self, caminho: str):
        if caminho in ("/", "/index.html"):
            return self._enviar(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
        if caminho == "/api/versao":
            return self._json(200, {"versao": banco.versao(), "analisando": analise.FILA.rodando})
        if caminho == "/api/vagas":
            return self._json(200, {"versao": banco.versao(), "vagas": banco.listar_vagas()})
        if caminho == "/api/buscas/ultima":
            return self._json(200, {"busca": banco.ultima_busca()})
        if caminho == "/api/config":
            cfg = filtros.ler_config()
            return self._json(200, {**self._config(filtros.efetivos(cfg)), "existe": bool(cfg)})
        if caminho == "/favicon.ico":
            return self._enviar(204, b"", "image/x-icon")
        return self._erro(404, "rota não encontrada")

    def do_GET(self):
        self._tratar("GET")

    def do_POST(self):
        self._tratar("POST")

    def do_PATCH(self):
        self._tratar("PATCH")

    def do_PUT(self):
        self._tratar("PUT")

    def do_DELETE(self):
        self._tratar("DELETE")

    @staticmethod
    def _config(f: dict) -> dict:
        f = {k: v for k, v in f.items() if k != "local_legado"}
        return {"filtros": f, "consultas": len(filtros.consultas(f)), "opcoes": filtros.opcoes()}


def ja_rodando(porta: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/api/versao", timeout=2) as r:
            return r.status == 200 and "versao" in json.loads(r.read())
    except (OSError, ValueError):
        return False


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, default=PORTA_PADRAO)
    ap.add_argument("--rede", action="store_true", help="aceita conexões de outros aparelhos da rede local")
    ap.add_argument("--sem-navegador", action="store_true")
    args = ap.parse_args()

    endereco = f"http://127.0.0.1:{args.porta}/"
    if ja_rodando(args.porta):
        print(f"O dashboard já está rodando em {endereco}")
        if not args.sem_navegador:
            webbrowser.open(endereco)
        return 0

    banco.conectar().close()  # cria o banco na primeira vez
    copia = banco.backup_diario()

    Handler.hosts_permitidos = {"127.0.0.1", "localhost"}
    bind = "127.0.0.1"
    ip = None
    if args.rede:
        bind = "0.0.0.0"
        ip = ip_da_rede()
        if ip:
            Handler.hosts_permitidos.add(ip)
        Handler.hosts_permitidos.add(socket.gethostname().lower())

    try:
        servidor = ThreadingHTTPServer((bind, args.porta), Handler)
    except OSError as e:
        print(f"Não foi possível usar a porta {args.porta}: {e}. Tente --porta 8766.", file=sys.stderr)
        return 1

    print("Acompanhamento de Candidaturas")
    print(f"  Neste computador: {endereco}")
    if ip:
        print(f"  Na rede local:    http://{ip}:{args.porta}/")
    print(f"  Dados: {banco.ARQUIVO}")
    if copia:
        print(f"  Backup do dia: {copia.name}")
    if analise.comando():
        print("  Análise automática: ligada (Claude Code)")
        if any(analise.precisa(v) for v in banco.listar_vagas()):
            analise.FILA.pedir()  # vagas que ficaram esperando nota
    print("Feche esta janela (ou Ctrl+C) para parar.")
    if not args.sem_navegador:
        webbrowser.open(endereco)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
