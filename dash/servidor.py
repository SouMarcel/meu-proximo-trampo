#!/usr/bin/env python3
"""Servidor local do dashboard de candidaturas (só biblioteca padrão).

  python dash/servidor.py                 abre em http://127.0.0.1:8765
  python dash/servidor.py --rede          aceita acesso de outros aparelhos da sua rede (ex.: celular no mesmo Wi-Fi)
  python dash/servidor.py --sem-navegador não abre o navegador

Feche a janela (ou Ctrl+C) para parar. Os dados ficam em dash/dados/candidaturas.db.
No VS Code, a tarefa "Dashboard" (.vscode/tasks.json) sobe este servidor ao abrir a pasta, e a
página também pode ser aberta pelo Live Server (dash/dashboard.html): ela fala com este servidor
na porta 8765, que aceita páginas abertas neste computador.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import socket
import sys
import threading
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(1, str(Path(__file__).resolve().parent.parent))
import analise  # noqa: E402  (análise automática pela IA escolhida)
import banco  # noqa: E402
import buscador  # noqa: E402  (busca de vagas pela página, em segundo plano)
import gerador  # noqa: E402  (currículo pela página, em segundo plano)
import filtros  # noqa: E402  (filtros.py, na raiz: lê e grava os filtros da busca no config.json)
import ia  # noqa: E402  (ia.py, na raiz: provedores de IA)
import primeiros_passos as pp  # noqa: E402  (primeiros_passos.py, na raiz: perfil a partir do currículo e do LinkedIn)
import segredos  # noqa: E402  (segredos.py, na raiz: chaves no .env)
from fontes import link  # noqa: E402  (lê a vaga a partir do link)

PAGINA = banco.DASH / "dashboard.html"
PORTA_PADRAO = 8765
LIMITE_CORPO = 1_000_000
LIMITE_MATERIAL = 15_000_000  # arquivo de até 10 MB em base64
SO_LOCAL = "Só dá para mudar a IA no computador onde a ferramenta roda."
SO_LOCAL_PERFIL = "Só dá para fazer isso no computador onde a ferramenta roda."
TRAVA_PERFIL = threading.Lock()  # o progresso dos primeiros passos é um arquivo só


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
        self._cabecalhos_cors()
        self.end_headers()
        self.wfile.write(corpo)

    def _origem_local(self) -> str | None:
        """Origem de uma página aberta neste computador por outro servidor, como o Live Server do VS Code
        (http://127.0.0.1:5500). Sites da internet têm outra origem e continuam recusados."""
        origem = self.headers.get("Origin") or ""
        partes = urlsplit(origem)
        if partes.scheme == "http" and partes.hostname in ("127.0.0.1", "localhost") and origem == f"http://{partes.netloc}":
            return origem
        return None

    def _cabecalhos_cors(self):
        origem = self._origem_local()
        if origem:
            self.send_header("Access-Control-Allow-Origin", origem)
            self.send_header("Vary", "Origin")

    def _json(self, status: int, obj):
        self._enviar(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _erro(self, status: int, msg: str):
        self._json(status, {"erro": msg})

    def _host_ok(self) -> bool:
        """Bloqueia DNS rebinding: só atende pelos nomes esperados."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in self.hosts_permitidos

    def _escrita_ok(self) -> bool:
        """Bloqueia pedidos de outros sites (CSRF): exige JSON e origem igual à própria página ou uma página
        aberta neste computador (_origem_local)."""
        if not (self.headers.get("Content-Type") or "").lower().startswith("application/json"):
            return False
        origem = self.headers.get("Origin")
        return origem is None or origem == f"http://{self.headers.get('Host')}" or self._origem_local() is not None

    def _corpo(self, limite: int = LIMITE_CORPO) -> dict:
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > limite:
            raise ValueError("pedido grande demais")
        dados = json.loads(self.rfile.read(tamanho) or b"{}")
        if not isinstance(dados, dict):
            raise ValueError("esperava um objeto JSON")
        return dados

    def _local(self) -> bool:
        """O pedido veio deste computador (não de outro aparelho da rede, com --rede)."""
        return self.client_address[0] in ("127.0.0.1", "::1")

    def _ia(self, metodo: str, caminho: str):
        """Rotas de escrita do painel IA: só deste computador; mensagens sem chave."""
        if not self._local():
            return self._erro(403, SO_LOCAL)
        if metodo == "PUT" and caminho == "/api/ia":
            corpo = self._corpo()
            escolha = ia.validar_escolha(corpo)
            chave = str(corpo.get("chave") or "").strip()
            if chave:
                variavel = ia.PROVEDORES[escolha["provedor"]]["variavel"]
                if not variavel:
                    raise ValueError("este provedor não usa chave")
                segredos.gravar(variavel, chave)
            ia.salvar_escolha(escolha)
            if ia.disponivel():
                analise.FILA.pedir()
            return self._json(200, ia.estado_para_pagina(True, analise.FILA.erro()))
        if metodo == "POST" and caminho == "/api/ia/testar":
            corpo = self._corpo()
            ok, mensagem = ia.testar(corpo, chave=str(corpo.get("chave") or "").strip() or None)
            if ok and ia.disponivel():
                analise.FILA.pedir()
            return self._json(200, {"ok": ok, "mensagem": ia.mascarar(mensagem, str(corpo.get("chave") or ""))})
        if metodo == "DELETE" and caminho.startswith("/api/ia/chave/"):
            provedor = unquote(caminho[len("/api/ia/chave/"):])
            variavel = ia.PROVEDORES.get(provedor, {}).get("variavel")
            if not variavel:
                return self._erro(404, "provedor sem chave")
            segredos.remover(variavel)
            estado = ia.estado_para_pagina(True, analise.FILA.erro())
            if segredos.origem(variavel) == "ambiente":
                estado["aviso"] = "Esta chave está definida nas variáveis de ambiente do sistema; remova-a por lá."
            return self._json(200, estado)
        return self._erro(404, "rota não encontrada")

    def _perfil(self, metodo: str, caminho: str):
        """Primeiros passos: tudo que grava é só deste computador; o pedido à IA roda fora da trava."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        if metodo == "POST" and caminho == "/api/perfil/rascunho":
            sem_ia = bool(self._corpo().get("sem_ia")) or not ia.disponivel()
            with TRAVA_PERFIL:
                estado = pp.carregar()
            perfil = pp.caminho_perfil()
            atual = perfil.read_text(encoding="utf-8", errors="replace") if perfil.exists() else None
            rascunho = pp.rascunho_sem_ia(estado) if sem_ia else pp.rascunho_com_ia(estado, atual)
            with TRAVA_PERFIL:
                estado = pp.carregar()
                estado.update(rascunho=rascunho, etapa="rascunho")
                pp.salvar(estado)
            return self._json(200, pp.estado_para_pagina(True))
        if metodo == "POST" and caminho == "/api/perfil/filtros-propostos":
            sugerir = bool(self._corpo().get("sugerir_en")) and ia.disponivel()
            return self._json(200, pp.propor_filtros(pp.carregar()["respostas"], sugerir_en=sugerir))
        with TRAVA_PERFIL:
            estado = pp.carregar()
            if metodo == "POST" and caminho == "/api/perfil/material":
                corpo = self._corpo(LIMITE_MATERIAL)
                if "texto" in corpo:
                    material = pp.adicionar_material(estado, str(corpo.get("nome") or ""), texto=str(corpo["texto"]))
                else:
                    try:
                        dados = base64.b64decode(str(corpo.get("base64") or ""), validate=True)
                    except (binascii.Error, ValueError):
                        raise ValueError("arquivo inválido") from None
                    material = pp.adicionar_material(estado, str(corpo.get("nome") or ""), dados)
                if estado["etapa"] == "ia":
                    estado["etapa"] = "materiais"
                pp.salvar(estado)
                pagina = pp.estado_para_pagina(True)
                publico = next(m for m in pagina["materiais"] if m["id"] == material["id"])
                return self._json(201, {"material": publico, "estado": pagina})
            if metodo == "DELETE" and caminho.startswith("/api/perfil/material/"):
                pp.remover_material(estado, unquote(caminho[len("/api/perfil/material/"):]))
                pp.salvar(estado)
                return self._json(200, pp.estado_para_pagina(True))
            if metodo == "PUT" and caminho == "/api/perfil/progresso":
                pp.salvar(pp.atualizar_progresso(estado, self._corpo()))
                return self._json(200, pp.estado_para_pagina(True))
            if metodo == "DELETE" and caminho == "/api/perfil/progresso":
                pp.recomecar()
                return self._json(200, pp.estado_para_pagina(True))
            if metodo == "POST" and caminho == "/api/perfil/previa":
                markdown = self._corpo().get("markdown")
                return self._json(200, pp.previa(estado, None if markdown is None else str(markdown)))
            if metodo == "PUT" and caminho == "/api/perfil":
                destino, anterior = pp.gravar_perfil(str(self._corpo().get("markdown") or ""))
                estado["etapa"] = "filtros"
                pp.salvar(estado)
                rel = lambda c: c.relative_to(pp.RAIZ).as_posix() if c and c.is_relative_to(pp.RAIZ) else (str(c) if c else None)
                return self._json(200, {"gravado": rel(destino), "anterior": rel(anterior)})
        return self._erro(404, "rota não encontrada")

    def _busca(self, metodo: str, caminho: str):
        """Buscar vagas pela página: iniciar, cancelar e pedir a nota de novo, só deste computador."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        if metodo == "POST" and caminho == "/api/busca":
            corpo = self._corpo()
            try:
                estado = buscador.BUSCA.iniciar(sem_nota=bool(corpo.get("sem_nota")),
                                                confirmar_recente=bool(corpo.get("confirmar_recente")))
            except buscador.BuscaRecusada as e:
                return self._json(409, {"erro": str(e), "precisa_confirmar": e.precisa_confirmar,
                                        "estado": buscador.BUSCA.estado()})
            return self._json(202, {**estado, "pode_alterar": True})
        if metodo == "DELETE" and caminho == "/api/busca":
            return self._json(200, {**buscador.BUSCA.cancelar(), "pode_alterar": True})
        if metodo == "POST" and caminho == "/api/busca/analisar":
            analise.FILA.pedir()
            return self._json(200, {"analise": buscador.BUSCA.analise()})
        return self._erro(404, "rota não encontrada")

    def _curriculo(self, metodo: str, caminho: str):
        """Gerar o currículo pela página: só deste computador e só no clique."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        try:
            if metodo == "POST" and caminho == "/api/curriculo":
                corpo = self._corpo()
                vaga_id = str(corpo.get("vaga_id") or "").strip() or None
                return self._json(202, {**gerador.GERACAO.iniciar(vaga_id, corpo.get("tecnicas") or {}), "pode_alterar": True})
            if metodo == "POST" and caminho == "/api/curriculo/tentar":
                return self._json(202, {**gerador.GERACAO.tentar(), "pode_alterar": True})
        except gerador.GeracaoOcupada as e:
            return self._json(409, {"erro": str(e), "estado": gerador.GERACAO.estado()})
        return self._erro(404, "rota não encontrada")

    def _arquivo_curriculo(self, nome: str):
        """Só .pdf e .docx de curriculos/, com o nome validado (nada de caminhos)."""
        sys.path.insert(0, str(banco.DASH.parent))
        import curriculo_ia
        caminho = curriculo_ia.arquivo_servivel(unquote(nome))
        if not caminho:
            return self._erro(404, "arquivo não encontrado")
        dados = caminho.read_bytes()
        pdf = caminho.suffix == ".pdf"
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf" if pdf else
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Content-Disposition", ("inline" if pdf else "attachment") + f"; filename*=UTF-8''{quote(caminho.name)}")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self._cabecalhos_cors()
        self.end_headers()
        self.wfile.write(dados)

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
            if caminho == "/api/ia" or caminho.startswith("/api/ia/"):
                return self._ia(metodo, caminho)
            if caminho == "/api/perfil" or caminho.startswith("/api/perfil/"):
                return self._perfil(metodo, caminho)
            if caminho == "/api/busca" or caminho.startswith("/api/busca/"):
                return self._busca(metodo, caminho)
            if caminho == "/api/curriculo" or caminho.startswith("/api/curriculo/"):
                return self._curriculo(metodo, caminho)
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
            return self._json(200, {"versao": banco.versao(), "analisando": analise.FILA.rodando,
                                    "ia_erro": analise.FILA.erro(), "busca": buscador.BUSCA.resumo()})
        if caminho == "/api/ia":
            return self._json(200, ia.estado_para_pagina(self._local(), analise.FILA.erro()))
        if caminho.startswith("/arquivos/curriculos/"):
            return self._arquivo_curriculo(caminho[len("/arquivos/curriculos/"):])
        if caminho.startswith("/api/curriculo"):
            consulta = parse_qs(urlsplit(self.path).query)
            vaga_id = (consulta.get("vaga") or [""])[0].strip() or None
            if caminho == "/api/curriculo/estado":
                return self._json(200, {**gerador.GERACAO.estado(), "pode_alterar": self._local()})
            if caminho == "/api/curriculo/catalogo":
                return self._json(200, {**gerador.GERACAO.preparar(vaga_id), "pode_alterar": self._local()})
            if caminho == "/api/curriculo/lista":
                sys.path.insert(0, str(banco.DASH.parent))
                import curriculo_ia
                base = (consulta.get("base") or [""])[0] == "1"
                return self._json(200, {"curriculos": curriculo_ia.listar(vaga_id, base=base)})
        if caminho == "/api/busca":
            return self._json(200, {**buscador.BUSCA.estado(), "pode_alterar": self._local()})
        if caminho == "/api/busca/plano":
            return self._json(200, buscador.BUSCA.plano())
        if caminho == "/api/perfil/estado":
            return self._json(200, pp.estado_para_pagina(self._local()))
        if caminho == "/api/perfil/filtros-propostos":
            return self._json(200, pp.propor_filtros(pp.carregar()["respostas"]))
        if caminho == "/api/vagas":
            return self._json(200, {"versao": banco.versao(), "vagas": banco.listar_vagas()})
        if caminho == "/api/buscas/ultima":
            return self._json(200, {"busca": banco.ultima_busca()})
        if caminho == "/api/config":
            cfg = filtros.ler_config()
            return self._json(200, {**self._config(filtros.efetivos(cfg)), "existe": bool(cfg.get("termos"))})
        if caminho == "/favicon.ico":
            return self._enviar(204, b"", "image/x-icon")
        return self._erro(404, "rota não encontrada")

    def do_OPTIONS(self):
        """Pré-verificação de CORS da página aberta pelo Live Server (outra porta deste computador)."""
        if not self._host_ok() or not self._origem_local():
            return self._erro(403, "pedido recusado")
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self._cabecalhos_cors()
        self.end_headers()

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
    if analise.ligada():
        print(f"  Análise automática: ligada ({analise.descricao_ia()})")
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
