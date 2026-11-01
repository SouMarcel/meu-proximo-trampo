#!/usr/bin/env python3
"""Servidor local do dashboard de candidaturas (só biblioteca padrão).

  python dash/servidor.py                 abre em http://127.0.0.1:8765
  python dash/servidor.py --rede          aceita acesso de outros aparelhos da sua rede (ex.: celular no mesmo Wi-Fi)
  python dash/servidor.py --sem-navegador não abre o navegador

Feche a janela (ou Ctrl+C) para parar. Os dados ficam em dash/dados/candidaturas.db.
No VS Code, a tarefa "Dashboard" (.vscode/tasks.json) sobe este servidor ao abrir a pasta, e a
página também pode ser aberta pelo Live Server (dash/front/index.html): ela fala com este servidor
na porta 8765, que aceita páginas abertas neste computador.
A página (dash/front/, montada pelo GitHub Actions a partir da branch frontend-react; specs 022 e 025) fica em /;
o endereço antigo /novo/ leva para lá.
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
import sincronia  # noqa: E402  (contas conectadas: candidaturas lidas nos portais, spec 018)
import gerador  # noqa: E402  (currículo pela página, em segundo plano)
import filtros  # noqa: E402  (filtros.py, na raiz: lê e grava os filtros da busca no config.json)
import ia  # noqa: E402  (ia.py, na raiz: provedores de IA)
import post_ia  # noqa: E402  (post_ia.py, na raiz: vaga a partir de texto livre, com a IA)
import primeiros_passos as pp  # noqa: E402  (primeiros_passos.py, na raiz: perfil a partir do currículo e do LinkedIn)
import segredos  # noqa: E402  (segredos.py, na raiz: chaves no .env)
from fontes import ats, link, post  # noqa: E402  (lê a vaga a partir do link; o post do LinkedIn com uma vaga)

FRONT = banco.DASH / "front"  # a página (specs 022 e 025), montada pelo GitHub Actions a partir da branch frontend-react
TIPOS_FRONT = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
               ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png", ".woff2": "font/woff2"}
SEM_FRONT = ("<!doctype html><meta charset='utf-8'><title>Meu Próximo Trampo</title><p>A página da ferramenta "
             "ainda não foi montada nesta cópia (falta a pasta dash/front/). Atualize a sua cópia da ferramenta "
             "(git pull): a página vem pronta, sem precisar instalar nada.</p>")
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
        self._descartar_corpo()  # resposta antes de ler o pedido (ex.: 403): sem isso, o Windows às vezes corta a conexão
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

    def _descartar_corpo(self) -> None:
        if getattr(self, "_corpo_lido", False):
            return
        self._corpo_lido = True
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return
        if 0 < tamanho <= LIMITE_MATERIAL:
            self.rfile.read(tamanho)

    def _corpo(self, limite: int = LIMITE_CORPO) -> dict:
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > limite:
            raise ValueError("pedido grande demais")
        self._corpo_lido = True
        dados = json.loads(self.rfile.read(tamanho) or b"{}")
        if not isinstance(dados, dict):
            raise ValueError("esperava um objeto JSON")
        return dados

    def _local(self) -> bool:
        """O pedido veio deste computador (não de outro aparelho da rede, com --rede)."""
        return self.client_address[0] in ("127.0.0.1", "::1")

    def _contas(self, metodo: str, caminho: str):
        """Contas conectadas (spec 018): só deste computador; a leitura só lê e propõe, aplicar grava o marcado."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        contas, nav = sincronia.contas, sincronia.navegador
        if metodo == "GET" and caminho == "/api/contas":
            ligados = contas.conectados()
            return self._json(200, {"navegador": bool(nav.achar()), "ultima": sincronia.LEITURA.ultima(),
                                    "portais": [{"nome": n, "plataforma": m.PLATAFORMA, "icone": m.ICONE,
                                                 "conectado": n in ligados, "aviso_login": m.AVISO_LOGIN}
                                                for n, m in contas.CONTAS.items()]})
        if metodo == "GET" and caminho == "/api/candidaturas/estado":
            r = sincronia.LEITURA.resultado
            limpar = lambda lista: [{k: v for k, v in i.items() if k != "lida"} for i in lista or []]
            res = {**r, "itens": limpar(r.get("itens")), "historico": limpar(r.get("historico"))} if r else None
            return self._json(200, {**sincronia.LEITURA.estado, "resultado": res})
        if metodo != "POST":
            return self._erro(405, "método não permitido")
        partes = caminho.strip("/").split("/")  # api / contas / <portal> / <acao>
        if len(partes) == 4 and partes[1] == "contas":
            modulo = contas.CONTAS.get(partes[2])
            if modulo is None:
                return self._erro(404, "portal desconhecido")
            try:
                if partes[3] == "conectar":
                    nav.abrir(modulo.URL_CANDIDATURAS).frente()
                    return self._json(200, {"ok": True})
                if partes[3] == "pronto":  # a janela fica aberta e minimizada: a Gupy esquece o login ao fechar
                    aba = nav.abrir(modulo.URL_CANDIDATURAS)
                    ok = modulo.logado(aba.url())
                    if ok:
                        contas.marcar(partes[2], True)
                        aba.minimizar()
                    aba.fechar()
                    return self._json(200, {"conectado": ok})
                if partes[3] == "desconectar":
                    contas.marcar(partes[2], False)
                    from fontes import _sessao
                    if not _sessao.algum_conectado():  # contas e portais com login (spec 041)
                        nav.desconectar()  # nenhum portal: fecha a janela e apaga o perfil inteiro
                    else:
                        aba = nav.abrir("about:blank", minimizado=True)
                        for origem in modulo.ORIGENS:
                            aba.sessao.pedir("Storage.clearDataForOrigin", origin=origem, storageTypes="all")
                        aba.minimizar()
                        aba.fechar()
                    return self._json(200, {"ok": True})
            except (nav.NavegadorErro, contas.PortalErro) as e:
                return self._erro(409, str(e))
            return self._erro(404, "rota não encontrada")
        if caminho == "/api/candidaturas/ler":
            ligados = contas.conectados()
            if not ligados:
                return self._erro(409, "conecte pelo menos um portal")
            return self._json(200, sincronia.LEITURA.iniciar(ligados))
        if caminho == "/api/candidaturas/aplicar":
            corpo = self._corpo()
            chaves = corpo.get("chaves") or []
            if not isinstance(chaves, list):
                raise ValueError("chaves inválidas")
            r = sincronia.LEITURA.aplicar([str(c) for c in chaves][:500], historico=corpo.get("historico") is True)
            if r["aplicados"]:
                analise.FILA.pedir()  # vagas novas com descrição ganham nota, como no Adicionar Vaga
            return self._json(200, r)
        return self._erro(404, "rota não encontrada")

    def _portais_login(self, metodo: str, caminho: str):
        """Portais com login (spec 041): só deste computador. Conectar abre a página de login na janela da ferramenta,
        Pronto confere o login só pelo endereço da aba, Desconectar apaga a sessão do portal. Ligar e desligar é pelo
        salvamento de sempre dos filtros (fontes)."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        from fontes import FONTES, _sessao
        nav = sincronia.navegador
        if metodo == "GET" and caminho == "/api/portais-login":
            try:
                ligadas = filtros.ler_config().get("fontes") or filtros.FONTES_PADRAO
            except (OSError, ValueError):
                ligadas = filtros.FONTES_PADRAO
            conectados = _sessao.conectados()
            portais = []
            for nome, rotulo in filtros.FONTES_LOGIN.items():
                m = FONTES.get(nome)
                if m is None:
                    continue
                esp = m.espera()
                ligado, conectado = nome in ligadas, nome in conectados
                situacao = ("desligado" if not ligado else "em_espera" if esp else
                            "desconectado" if not conectado else "conectado")
                portais.append({"nome": nome, "rotulo": rotulo, "termos": m.TERMOS, "aviso_risco": m.AVISO_RISCO,
                                "aviso_login": m.AVISO_LOGIN, "ligado": ligado, "conectado": conectado,
                                "situacao": situacao, "espera": esp})
            return self._json(200, {"navegador": bool(nav.achar()), "portais": portais})
        if metodo != "POST":
            return self._erro(405, "método não permitido")
        partes = caminho.strip("/").split("/")  # api / portais-login / <portal> / <acao>
        if len(partes) != 4:
            return self._erro(404, "rota não encontrada")
        modulo = FONTES.get(partes[2]) if partes[2] in filtros.FONTES_LOGIN else None
        if modulo is None:
            return self._erro(404, "portal desconhecido")
        try:
            if partes[3] == "conectar":  # aba nova na janela, na frente: não tira a pessoa de outra página
                aba = nav.abrir_para_leitura(modulo.URL_LOGIN)
                aba.frente()
                aba.fechar()
                return self._json(200, {"ok": True})
            if partes[3] == "pronto":
                aba = nav.abrir_para_leitura(modulo.URL_BUSCA)
                try:
                    ok = modulo.logado(aba.endereco())
                    if ok:
                        _sessao.marcar(modulo.NOME, True)
                        aba.minimizar()
                finally:
                    aba.fechar_aba()
                return self._json(200, {"conectado": ok})
            if partes[3] == "desconectar":
                _sessao.desconectar(modulo)
                return self._json(200, {"ok": True})
        except nav.NavegadorErro as e:
            return self._erro(409, str(e))
        return self._erro(404, "rota não encontrada")

    def _candidatura(self, metodo: str, caminho: str):
        """Candidatura assistida (spec 027): só deste computador, só no clique e só nas vagas em que a pessoa ligou.
        Preenche campos na janela da ferramenta; nunca clica em botão nem envia. A senha guardada nunca sai."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        import candidatura
        from candidatura import dominios, formulario, login
        nav = sincronia.navegador
        partes = [unquote(x) for x in caminho.strip("/").split("/")[2:]]  # api / candidatura / ...
        try:
            if not partes:
                if metodo != "GET":
                    return self._erro(405, "método não permitido")
                from candidatura import contato, memoria
                return self._json(200, {"aviso": candidatura.AVISO, "navegador": bool(nav.achar()),
                                        "dominios": dominios.para_pagina(), "credenciais": login.para_pagina(),
                                        "memoria": memoria.listar(), "contato": contato.ler(),
                                        "campos_contato": list(contato.CAMPOS)})
            if partes[:1] == ["contato"]:  # dados de contato (spec 033): só o que a pessoa salva; nunca vão à IA
                from candidatura import contato
                if partes == ["contato", "proposta"] and metodo == "POST":
                    return self._json(200, contato.propor())
                if partes == ["contato"] and metodo == "PUT":
                    return self._json(200, {"contato": contato.gravar(self._corpo().get("dados"))})
                if partes == ["contato"] and metodo == "DELETE":
                    return self._json(200, {"contato": contato.apagar()})
                return self._erro(405, "método não permitido")
            if len(partes) == 2 and partes[0] == "memoria" and metodo == "DELETE":
                from candidatura import memoria
                if not memoria.apagar(partes[1]):
                    return self._erro(404, "resposta não encontrada")
                return self._json(200, {"memoria": memoria.listar()})
            if partes == ["dominios"] and metodo == "POST":
                corpo = self._corpo()
                acao = dominios.liberar if corpo.get("acao") == "liberar" else dominios.revogar if corpo.get("acao") == "revogar" else None
                if acao is None:
                    raise ValueError("acao deve ser liberar ou revogar")
                acao(str(corpo.get("dominio") or ""))
                return self._json(200, {"dominios": dominios.para_pagina()})
            if len(partes) == 2 and partes[0] == "credenciais" and metodo in ("PUT", "DELETE"):
                if metodo == "PUT":
                    corpo = self._corpo()
                    login.gravar(partes[1], corpo.get("usuario"), corpo.get("senha"))
                else:
                    login.apagar(partes[1])
                return self._json(200, {"credenciais": login.para_pagina()})
            if len(partes) == 2 and partes[0] == "vaga" and metodo == "PUT" and banco.ID_VALIDO.match(partes[1]):
                corpo = self._corpo()  # a chave da vaga: ligar exige o aviso aceito, a cada vaga
                vaga = candidatura.ligar_vaga(partes[1], corpo.get("ligada") is True, aceitar_aviso=corpo.get("aceitar_aviso") is True)
                return self._json(200, {"vaga": banco.com_kit(vaga)})
            if len(partes) == 3 and partes[0] == "vaga" and metodo == "POST" and banco.ID_VALIDO.match(partes[1]):
                vaga = banco.obter(partes[1])
                if vaga is None:
                    return self._erro(404, "vaga não encontrada")
                candidatura.exigir_ligada(vaga)
                acao = partes[2]
                if acao == "login":
                    aba = nav.aba_atual()
                    try:
                        return self._json(200, login.preencher_login(aba, vaga))
                    finally:
                        aba.fechar()
                if acao == "abrir":
                    url = vaga.get("url_candidatura") or vaga.get("url") or ""
                    if not url.startswith("https://"):
                        return self._erro(409, "esta vaga não tem um link https para abrir")
                    aba = nav.abrir(url)
                    aba.frente()
                    aba.fechar()
                    return self._json(200, {"ok": True, "url": url, "dominio": dominios.situacao(url)})
                if acao in ("ler", "auto", "preencher"):
                    from candidatura import auto
                    import candidatura_ia
                    corpo = self._corpo()
                    aba = nav.aba_atual()
                    try:
                        if acao in ("auto", "preencher"):
                            if acao == "auto":  # preenche o que sabe (memória e perfil) e devolve as perguntas para a pessoa
                                r = auto.preencher_pagina(aba, vaga)
                            else:  # as respostas que a pessoa deu no painel
                                r = auto.responder(aba, vaga, str(corpo.get("assinatura") or ""), corpo.get("respostas"),
                                                   lembrar=corpo.get("lembrar") is not False,
                                                   guardar_relatos=corpo.get("guardar_relatos") is not False)
                            meta = candidatura_ia.gravar_preenchidas(vaga, r["preenchidos"]) if r["preenchidos"] else {}
                            return self._json(200, {**r, "documento": meta.get("nome")})
                        pagina = formulario.ler(aba)
                    finally:
                        aba.fechar()
                    resposta = {"pagina": {k: pagina[k] for k in ("url", "dominio", "etapa", "aviso", "assinatura")},
                                "itens": [], "aviso_ia": None, "ia": None}
                    if pagina["etapa"] == "perguntas" and pagina["dominio"]["permitido"]:
                        proposta = candidatura_ia.propor_respostas(vaga, pagina["campos"])
                        resposta.update(itens=proposta["itens"], aviso_ia=proposta["aviso"], ia=proposta["ia"])
                    return self._json(200, resposta)
            return self._erro(404, "rota não encontrada")
        except candidatura.CandidaturaErro as e:
            return self._erro(409, str(e))
        except nav.NavegadorErro as e:
            return self._erro(409, str(e))

    def _ler_post(self, url: str):
        """Link de post do LinkedIn (spec 016): um pedido à versão pública do post e os dados para o formulário do
        Adicionar Vaga, sem gravar nada. O mesmo post já no banco não gera pedido."""
        existente = banco.obter(post.id_do_post(url)["id"])
        if existente is not None:
            return self._json(200, {"vaga": banco.com_kit(existente), "nova": False})
        try:
            p = post.ler(url)
        except post.PostErro as e:
            return self._json(422, {"erro": str(e), "sugestao": "colar",
                                    "parcial": {"url": url, "plataforma": "LinkedIn", "formato": "post"}})
        existente = banco.obter(p["id"])
        if existente is not None:
            return self._json(200, {"vaga": banco.com_kit(existente), "nova": False})
        parcial = {"url": p["url"], "plataforma": "LinkedIn", "formato": "post", "post_id": p["id"], "descricao": p["texto"]}
        if p["autor_tipo"] == "empresa":
            parcial["empresa"] = p["autor"]
        elif p["autor_tipo"] == "pessoa":
            parcial["publicado_por"] = p["autor"]
        parcial["area"], parcial["pais_vaga"] = filtros.area_da_vaga({"local": ""}, filtros.efetivos(filtros.ler_config()))
        escolha = ia.escolha_efetiva()
        return self._json(200, {"post": p, "parcial": parcial, "ia": {
            "disponivel": ia.disponivel(), "local": self._local(),
            "provedor": ia.PROVEDORES.get(escolha["provedor"], {}).get("nome", ""), "modelo": ia.modelo_efetivo(escolha)}})

    def _extrair(self):
        """Cargo, empresa, local e contato de candidatura tirados de um texto livre pela IA escolhida, para o
        formulário do Adicionar Vaga. Só deste computador (usa a chave e a cota da pessoa); nada é gravado."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        corpo = self._corpo()
        texto = str(corpo.get("texto") or "").strip()
        if not texto:
            return self._erro(400, "cole o texto do post ou da mensagem")
        if not ia.disponivel():
            return self._erro(409, "nenhuma IA configurada")
        try:
            r = post_ia.extrair(texto, str(corpo.get("autor") or ""), str(corpo.get("autor_tipo") or ""))
        except post_ia.ExtracaoErro as e:
            return self._erro(502, str(e))
        campos = {k: r[k] for k in ("titulo", "empresa", "local", "url", "email_candidatura", "assunto_candidatura")}
        return self._json(200, {"campos": campos, "parece_vaga": r["parece_vaga"], "vagas": r["vagas"],
                                "provedor": r["provedor"], "modelo": r["modelo"]})

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
            for bruta in corpo.get("reservas") or [] if isinstance(corpo.get("reservas"), list) else []:
                chave_r = str(bruta.get("chave") or "").strip() if isinstance(bruta, dict) else ""
                variavel_r = ia.PROVEDORES.get(str(bruta.get("provedor") or ""), {}).get("variavel") if chave_r else ""
                if variavel_r:  # a chave da reserva vai para o .env, como a da principal; nunca para o config.json
                    segredos.gravar(variavel_r, chave_r)
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
        if metodo == "POST" and caminho == "/api/perfil/do-curriculo":  # a proposta: lê e propõe, não grava
            import curriculo_base
            corpo = self._corpo()
            arquivo = str(corpo.get("arquivo") or "")
            if not arquivo and corpo.get("material_id"):
                with TRAVA_PERFIL:
                    material = next((m for m in pp.carregar()["materiais"] if m["id"] == corpo["material_id"]), None)
                arquivo = (material or {}).get("arquivo") or ""
            if not arquivo:
                raise ValueError("escolha um currículo em PDF ou Word (.docx)")
            return self._json(200, curriculo_base.proposta(arquivo))
        if metodo == "POST" and caminho == "/api/perfil/do-curriculo/confirmar":
            import curriculo_base
            with TRAVA_PERFIL:
                return self._json(200, curriculo_base.confirmar(self._corpo()))
        if metodo == "PUT" and caminho == "/api/curriculo-base":
            import curriculo_base
            corpo = self._corpo()
            idioma = str(corpo.get("idioma") or "")
            marc = (curriculo_base.marcar(idioma, corpo["arquivo"]) if corpo.get("arquivo")
                    else curriculo_base.desmarcar(idioma))
            return self._json(200, {"curriculo_base": marc})
        if metodo == "POST" and caminho == "/api/perfil/filtros-propostos":
            sugerir = bool(self._corpo().get("sugerir_en")) and ia.disponivel()
            return self._json(200, pp.propor_filtros(pp.carregar()["respostas"], sugerir_en=sugerir))
        if caminho.startswith("/api/perfil/relatos/"):  # relatos da pessoa (spec 035): corrigir, apagar, levar ao perfil
            import relatos
            partes = caminho[len("/api/perfil/relatos/"):].split("/")
            rid = unquote(partes[0])
            if metodo == "PUT" and len(partes) == 1:
                relatos.editar(rid, str(self._corpo().get("relato") or ""))
            elif metodo == "DELETE" and len(partes) == 1:
                self._corpo()
                relatos.apagar(rid)
            elif metodo == "POST" and partes[1:] == ["perfil"]:
                self._corpo()
                with TRAVA_PERFIL:  # grava o perfil.md (a versão anterior fica guardada)
                    r = relatos.levar_ao_perfil(rid)
                return self._json(200, {"relatos": relatos.listar(), "anterior": r["anterior"]})
            else:
                return self._erro(405, "método não permitido")
            return self._json(200, {"relatos": relatos.listar()})
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
                    area = corpo.get("area")  # spec 037: linkedin, curriculo ou documento; sem ela, a ferramenta adivinha
                    material = pp.adicionar_material(estado, str(corpo.get("nome") or ""), dados,
                                                     area=str(area) if area is not None else None)
                if estado["etapa"] == "ia":
                    estado["etapa"] = "materiais"
                pp.salvar(estado)
                pagina = pp.estado_para_pagina(True)
                publico = next(m for m in pagina["materiais"] if m["id"] == material["id"])
                return self._json(201, {"material": publico, "estado": pagina})
            if metodo in ("PUT", "POST") and caminho.startswith("/api/perfil/material/"):
                partes = [unquote(x) for x in caminho[len("/api/perfil/material/"):].split("/")]
                if metodo == "PUT" and len(partes) == 1:  # Mover para (spec 037): só a área muda
                    area = self._corpo().get("area")
                    material = pp.mover_material(estado, partes[0], str(area) if area is not None else None)
                    pp.salvar(estado)
                    aviso = None
                    if pp.area_de(material["tipo"]) != "curriculo" and material.get("arquivo"):
                        import curriculo_base
                        idiomas = curriculo_base.desmarcar_arquivo(material["arquivo"])
                        if idiomas:
                            nomes = " e ".join("português" if i == "pt" else "inglês" for i in idiomas)
                            aviso = f"Este arquivo era o seu currículo em {nomes}; a marcação saiu."
                    return self._json(200, {"estado": pp.estado_para_pagina(True), "aviso": aviso})
                if metodo == "POST" and partes[1:] == ["ocr"]:  # botão OCR: lê de novo o PDF que ficou sem texto
                    self._corpo()
                    material = pp.reler_material(estado, partes[0])
                    pp.salvar(estado)
                    pagina = pp.estado_para_pagina(True)
                    publico = next(m for m in pagina["materiais"] if m["id"] == material["id"])
                    return self._json(200, {"material": publico, "estado": pagina})
                return self._erro(405, "método não permitido")
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
                                                confirmar_recente=bool(corpo.get("confirmar_recente")),
                                                confirmar_espera=bool(corpo.get("confirmar_espera")))
            except buscador.BuscaRecusada as e:
                return self._json(409, {"erro": str(e), "precisa_confirmar": e.precisa_confirmar,
                                        "estado": buscador.BUSCA.estado()})
            return self._json(202, {**estado, "pode_alterar": True})
        if metodo == "DELETE" and caminho == "/api/busca":
            return self._json(200, {**buscador.BUSCA.cancelar(), "pode_alterar": True})
        if metodo == "POST" and caminho == "/api/busca/pendentes":
            try:
                return self._json(202, buscador.COMPLETAR.iniciar())
            except buscador.BuscaRecusada as e:
                return self._erro(409, str(e))
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
            if metodo == "POST" and caminho in ("/api/kit/carta", "/api/kit/respostas", "/api/kit/verificar"):
                corpo = self._corpo()
                tipo = caminho.rsplit("/", 1)[1]
                dados = {"carta": corpo.get("respostas"), "respostas": corpo.get("perguntas"),
                         "verificar": {k: corpo.get(k) for k in ("nome", "texto", "guardar_relatos")}}[tipo]
                vaga_id = str(corpo.get("vaga_id") or "").strip()
                return self._json(202, {**gerador.GERACAO.iniciar_kit(tipo, vaga_id, dados), "pode_alterar": True})
            if metodo == "POST" and caminho.startswith("/api/kit/carta/") and caminho.endswith("/pdf") and caminho.count("/") == 5:
                import candidatura_ia  # o PDF de uma carta que ficou sem ele (spec 035)
                self._corpo()
                try:
                    meta = candidatura_ia.pdf_da_carta(caminho.split("/")[4])
                except candidatura_ia.GeracaoErro as e:
                    return self._erro(400, str(e))
                return self._json(200, {"documento": meta})
            if metodo == "PUT" and caminho.startswith("/api/kit/respostas/"):
                import candidatura_ia
                try:
                    meta = candidatura_ia.gravar_da_pessoa(unquote(caminho.rsplit("/", 1)[1]), self._corpo().get("pessoa") or {})
                except candidatura_ia.GeracaoErro as e:
                    return self._erro(400, str(e))
                return self._json(200, {"documento": meta})
        except gerador.GeracaoOcupada as e:
            return self._json(409, {"erro": str(e), "estado": gerador.GERACAO.estado()})
        return self._erro(404, "rota não encontrada")

    def _analises(self, metodo: str, caminho: str):
        """Análises do perfil: só deste computador e só no clique (as que usam IA rodam fora de qualquer trava)."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        import analise_perfil as ap
        if metodo == "POST" and caminho == "/api/analises-perfil/lacunas":
            visao = str(self._corpo().get("visao") or "todas")
            r = ap.lacunas(ap.vagas_do_banco(), ap.perfil_texto(), visao)
            return self._json(200, r if r.get("faltam") else ap.salvar("lacunas", r))
        if metodo == "POST" and caminho == "/api/analises-perfil/plano":
            ultima = (ap.carregar().get("lacunas") or {}).get("itens") or []
            return self._json(200, ap.salvar("plano", ap.plano_estudo(ap.perfil_texto(), ultima)))
        if metodo == "POST" and caminho == "/api/analises-perfil/cargos":
            return self._json(200, ap.salvar("cargos", ap.cargos_alvo(ap.perfil_texto())))
        if metodo == "POST" and caminho == "/api/analises-perfil/cargos/filtros":
            corpo = self._corpo()
            cargos = corpo.get("cargos") if isinstance(corpo.get("cargos"), list) else []
            return self._json(200, ap.filtros_com_cargos(cargos, confirmar=bool(corpo.get("confirmar"))))
        if metodo == "PUT" and caminho == "/api/analises-perfil/marcas":
            corpo = self._corpo()
            return self._json(200, {"marcas": ap.marcar("linkedin_en", bool(corpo.get("linkedin_en")))})
        return self._erro(404, "rota não encontrada")

    def _entrevista(self, metodo: str, caminho: str):
        """Preparação para entrevista: só deste computador (histórias e respostas são da pessoa) e só no clique."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        sys.path.insert(0, str(banco.DASH.parent))
        import entrevista
        partes = [unquote(p) for p in caminho[len("/api/entrevista/"):].split("/")]
        if partes[0] == "historias":
            if metodo == "POST" and len(partes) == 1:
                return self._json(200, {"historia": entrevista.salvar_historia(self._corpo().get("historia"))})
            if metodo == "DELETE" and len(partes) == 2:
                entrevista.remover_historia(partes[1])
                return self._json(200, {"ok": True})
            return self._erro(404, "rota não encontrada")
        vid, acao = partes[0], (partes[1] if len(partes) == 2 else None)
        if not banco.ID_VALIDO.match(vid) or len(partes) > 2:
            return self._erro(404, "rota não encontrada")
        if metodo == "GET" and acao is None:
            return self._json(200, {**entrevista.preparacao(vid), "ia": ia.disponivel()})
        if metodo == "PUT" and acao == "empresa":
            return self._json(200, {"texto_empresa": entrevista.guardar_texto_empresa(vid, self._corpo().get("texto"))["texto_empresa"]})
        if metodo == "POST" and acao == "resumo":
            return self._json(200, {"resumo": entrevista.resumo_ia(vid)})
        if metodo == "POST" and acao == "perguntas":
            entrevista.perguntas_ia(vid)
            return self._json(200, {"perguntas": entrevista.preparacao(vid)["perguntas"]})
        if metodo == "POST" and acao == "historias":
            return self._json(200, {"rascunhos": entrevista.historias_ia(vid)})
        if metodo == "POST" and acao == "simulacao":
            corpo = self._corpo()
            r = entrevista.registrar_resposta(vid, corpo.get("pergunta"), corpo.get("resposta"), str(corpo.get("idioma") or "pt"),
                                              com_retorno=corpo.get("retorno", True) is not False)
            return self._json(200, {**r, "treinar": entrevista.resumo_simulacao(r["simulacao"])})
        if metodo == "POST" and acao == "rodada":
            return self._json(200, {"rodada": entrevista.registrar_rodada(vid, self._corpo())})
        return self._erro(404, "rota não encontrada")

    def _arquivo_curriculo(self, nome: str):
        """Só .pdf, .docx e .txt de curriculos/, com o nome validado (nada de caminhos)."""
        sys.path.insert(0, str(banco.DASH.parent))
        import curriculo_ia
        caminho = curriculo_ia.arquivo_servivel(unquote(nome))
        if not caminho:
            return self._erro(404, "arquivo não encontrado")
        dados = caminho.read_bytes()
        pdf = caminho.suffix == ".pdf"
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf" if pdf else "text/plain; charset=utf-8" if caminho.suffix == ".txt" else
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Content-Disposition", ("inline" if pdf else "attachment") + f"; filename*=UTF-8''{quote(caminho.name)}")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self._cabecalhos_cors()
        self.end_headers()
        self.wfile.write(dados)

    def _arquivo_curriculo_base(self, idioma: str):
        """O currículo da própria pessoa marcado para o idioma, e nenhum outro arquivo; só deste computador."""
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        sys.path.insert(0, str(banco.DASH.parent))
        import curriculo_base
        rel = curriculo_base.marcados().get(idioma) if idioma in curriculo_base.IDIOMAS else None
        if not rel:
            return self._erro(404, "arquivo não encontrado")
        caminho = curriculo_base.RAIZ / rel
        dados = caminho.read_bytes()
        pdf = caminho.suffix.lower() == ".pdf"
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf" if pdf else
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Content-Disposition", ("inline" if pdf else "attachment") + f"; filename*=UTF-8''{quote(caminho.name)}")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self._cabecalhos_cors()
        self.end_headers()
        self.wfile.write(dados)

    def _forcar(self, vid: str):
        """Forçar verificar (spec 021): a nota desta vaga, na frente das automáticas. Só deste computador, como o
        "Tentar a nota de novo" (gasta a IA da pessoa)."""
        self._corpo()  # lê o corpo ({}) antes de responder: recusar sem ler derruba a conexão no Windows
        if not self._local():
            return self._erro(403, SO_LOCAL_PERFIL)
        if not banco.ID_VALIDO.match(vid):
            return self._erro(404, "rota não encontrada")
        v = banco.obter(vid)
        if v is None:
            return self._erro(404, "vaga não encontrada")
        if analise._tem_nota(v) and not v.get("nota_sem_descricao"):
            return self._erro(409, "a vaga já tem nota")
        if not analise.FILA.forcar(vid):
            return self._json(409, {"erro": "Para dar nota, ligue uma IA", "sem_ia": True})
        return self._json(202, {"verificando": analise.FILA.verificando()})

    def _salario(self, metodo: str, caminho: str):
        """Faixa salarial (spec 028): só números com fonte (vaga, vagas parecidas do banco, anotações da pessoa) e
        links de pesquisa para ela abrir; nada é buscado na internet nem estimado pela IA."""
        import salarios
        partes = [unquote(x) for x in caminho[len("/api/vagas/"):].split("/")]
        if len(partes) < 2 or partes[1] != "salario" or not banco.ID_VALIDO.match(partes[0]):
            return self._erro(404, "rota não encontrada")
        vid = partes[0]
        try:
            if metodo == "GET" and len(partes) == 2:
                return self._json(200, salarios.faixa(vid))
            if metodo == "POST" and len(partes) == 2:
                corpo = self._corpo()
                salarios.anotar(vid, corpo.get("texto"), corpo.get("fonte"))
                return self._json(200, salarios.faixa(vid))
            if metodo == "DELETE" and len(partes) == 3 and partes[2].isdigit():
                salarios.remover(vid, int(partes[2]))
                return self._json(200, salarios.faixa(vid))
        except salarios.SalarioErro as e:
            return self._erro(400, str(e))
        return self._erro(404, "rota não encontrada")

    def _redirecionar(self, destino: str):
        self.send_response(308)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _front(self, caminho: str):
        """A página (specs 022 e 025) em /: só os arquivos de dash/front/, com os tipos de TIPOS_FRONT. O endereço
        antigo /novo/ (o front novo enquanto o dashboard antigo existia) leva para o mesmo arquivo na raiz."""
        if caminho == "/novo" or caminho.startswith("/novo/"):
            return self._redirecionar("/" + caminho[len("/novo/"):])
        relativo = unquote(caminho.lstrip("/")) or "index.html"
        base = FRONT.resolve()
        alvo = (base / relativo).resolve()
        if alvo == base / "index.html" and not alvo.is_file():
            return self._enviar(404, SEM_FRONT.encode("utf-8"), "text/html; charset=utf-8")
        if not alvo.is_relative_to(base) or alvo.suffix.lower() not in TIPOS_FRONT or not alvo.is_file():
            return self._erro(404, "arquivo não encontrado")
        return self._enviar(200, alvo.read_bytes(), TIPOS_FRONT[alvo.suffix.lower()])

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
                vaga, nova = banco.criar_manual(self._corpo())
                if not nova:
                    return self._json(200, {"vaga": banco.com_kit(vaga), "nova": False})
                auto = analise.precisa(vaga) and analise.FILA.pedir()
                return self._json(201, {"vaga": banco.com_kit(vaga), "nova": True, "analise_automatica": auto})
            if metodo == "POST" and caminho == "/api/vagas/extrair":
                return self._extrair()
            if metodo == "POST" and caminho == "/api/vagas/link":
                url = str(self._corpo().get("url") or "").strip()[:1000]
                if post.id_do_post(url):
                    return self._ler_post(url)
                try:
                    dados = link.ler(url)
                except link.LinkErro as e:  # o dashboard abre o formulário com o que deu para ler
                    area, pais = filtros.area_da_vaga({"local": e.parcial.get("local")}, filtros.efetivos(filtros.ler_config()))
                    return self._json(422, {"erro": str(e), "parcial": {**e.parcial, "url": url, "area": area, "pais_vaga": pais}})
                vaga, nova = banco.criar_de_link(dados)
                auto = nova and analise.precisa(vaga) and analise.FILA.pedir()
                resposta = {"vaga": banco.com_kit(vaga), "nova": nova, "analise_automatica": auto}
                empresa = self._empresa_do_link(url)
                if empresa:  # vaga do Greenhouse, do Lever ou do Ashby: a página oferece "Acompanhar" (spec 031)
                    resposta["empresa"] = empresa
                return self._json(201 if nova else 200, resposta)
            if metodo == "POST" and caminho == "/api/empresas":
                empresa, nova, empresas = filtros.acompanhar(self._corpo().get("url"))
                return self._json(201 if nova else 200, {"empresa": empresa, "nova": nova, "empresas": empresas})
            if caminho == "/api/ia" or caminho.startswith("/api/ia/"):
                return self._ia(metodo, caminho)
            if caminho in ("/api/perfil", "/api/curriculo-base") or caminho.startswith("/api/perfil/"):
                return self._perfil(metodo, caminho)
            if caminho.startswith(("/api/contas", "/api/candidaturas")):
                return self._contas(metodo, caminho)
            if caminho == "/api/portais-login" or caminho.startswith("/api/portais-login/"):
                return self._portais_login(metodo, caminho)
            if caminho == "/api/candidatura" or caminho.startswith("/api/candidatura/"):
                return self._candidatura(metodo, caminho)
            if caminho == "/api/busca" or caminho.startswith("/api/busca/"):
                return self._busca(metodo, caminho)
            if caminho == "/api/curriculo" or caminho.startswith(("/api/curriculo/", "/api/kit/")):
                return self._curriculo(metodo, caminho)
            if caminho.startswith("/api/analises-perfil/"):
                return self._analises(metodo, caminho)
            if caminho.startswith("/api/entrevista/"):
                return self._entrevista(metodo, caminho)
            if metodo == "PUT" and caminho == "/api/config":
                return self._json(200, self._config(filtros.salvar(self._corpo())))
            if metodo == "POST" and caminho.startswith("/api/vagas/") and caminho.endswith("/analisar"):
                return self._forcar(unquote(caminho[len("/api/vagas/"):-len("/analisar")]))
            if caminho.startswith("/api/vagas/") and "/salario" in caminho:
                return self._salario(metodo, caminho)
            vid = self._id_da_rota(caminho)
            if vid is None:
                return self._erro(404, "rota não encontrada")
            if metodo == "PATCH":
                return self._json(200, {"vaga": banco.com_kit(banco.atualizar_usuario(vid, self._corpo()))})
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
        if caminho in ("/", "/index.html") or caminho == "/novo" or caminho.startswith("/novo/"):
            return self._front(caminho)
        if caminho == "/api/versao":
            return self._json(200, {"versao": banco.versao(), "analisando": analise.FILA.rodando,
                                    "ia_erro": analise.FILA.erro(), "ia_alerta": ia.alerta(),
                                    "busca": buscador.BUSCA.resumo(),
                                    "verificando": analise.FILA.verificando(), "falhas": analise.FILA.falhas_atuais()})
        if caminho == "/api/ia":
            return self._json(200, ia.estado_para_pagina(self._local(), analise.FILA.erro()))
        if caminho.startswith(("/api/contas", "/api/candidaturas")):
            return self._contas("GET", caminho)
        if caminho == "/api/portais-login":
            return self._portais_login("GET", caminho)
        if caminho == "/api/candidatura":
            return self._candidatura("GET", caminho)
        if caminho.startswith("/arquivos/curriculo-base/"):
            return self._arquivo_curriculo_base(caminho.rsplit("/", 1)[1])
        if caminho.startswith("/arquivos/curriculos/"):
            return self._arquivo_curriculo(caminho[len("/arquivos/curriculos/"):])
        if caminho == "/api/analises-perfil":  # as análises salvas e a prontidão calculada agora
            import analise_perfil as ap
            perfil = ap.perfil_texto()
            return self._json(200, {"salvas": ap.carregar(), "prontidao": ap.prontidao(perfil), "ia": ia.disponivel(),
                                    "existe_perfil": bool(perfil.strip()), "pode_alterar": self._local()})
        if caminho.startswith("/api/entrevista/"):
            return self._entrevista("GET", caminho)
        if caminho == "/api/kit/lista":  # cartas e respostas de uma vaga
            sys.path.insert(0, str(banco.DASH.parent))
            import candidatura_ia
            vaga_id = (parse_qs(urlsplit(self.path).query).get("vaga") or [""])[0].strip()
            return self._json(200, {"documentos": candidatura_ia.listar(vaga_id) if vaga_id else []})
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
        if caminho == "/api/busca/pendentes":  # descrições pendentes (spec 019): quantas, a espera e o andamento
            return self._json(200, {**buscador.COMPLETAR.estado(), "pode_alterar": self._local()})
        if caminho == "/api/perfil/curriculos":  # os currículos de anexos/ e o seu currículo de cada idioma
            if not self._local():
                return self._erro(403, SO_LOCAL_PERFIL)
            import curriculo_base
            return self._json(200, {"curriculos": curriculo_base.candidatos(), "curriculo_base": curriculo_base.marcados(),
                                    "existe_perfil": pp.caminho_perfil().exists()})
        if caminho == "/api/perfil/estado":
            return self._json(200, pp.estado_para_pagina(self._local()))
        if caminho == "/api/perfil/relatos":  # relatos da pessoa (spec 035): só deste computador
            if not self._local():
                return self._erro(403, SO_LOCAL_PERFIL)
            import relatos
            return self._json(200, {"relatos": relatos.listar()})
        if caminho == "/api/perfil/filtros-propostos":
            return self._json(200, pp.propor_filtros(pp.carregar()["respostas"]))
        if caminho.startswith("/api/vagas/") and caminho.endswith("/salario"):
            return self._salario("GET", caminho)
        if caminho == "/api/vagas":
            base = banco.curriculos_base()
            return self._json(200, {"versao": banco.versao(), "vagas": [banco.com_kit(v, base) for v in banco.listar_vagas()]})
        if caminho == "/api/buscas/ultima":
            return self._json(200, {"busca": banco.ultima_busca()})
        if caminho == "/api/config":
            cfg = filtros.ler_config()
            return self._json(200, {**self._config(filtros.efetivos(cfg)), "existe": bool(cfg.get("termos"))})
        if caminho == "/api/empresas":
            return self._json(200, {"empresas": filtros.efetivos(filtros.ler_config())["empresas"],
                                    "maximo": filtros.MAX_EMPRESAS})
        if caminho == "/favicon.ico":
            return self._enviar(204, b"", "image/x-icon")
        if not caminho.startswith(("/api/", "/arquivos/")):  # os arquivos da página (assets/, favicon.svg)
            return self._front(caminho)
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
    def _empresa_do_link(url: str) -> dict | None:
        """A empresa de um link de vaga do Greenhouse, do Lever ou do Ashby, com "acompanhada"; None para outro link."""
        achado = ats.vaga_do_link(url)
        if not achado:
            return None
        empresa = achado[0]
        lista = filtros.efetivos(filtros.ler_config())["empresas"]
        return {**empresa, "acompanhada": filtros.empresa_igual(lista, empresa) is not None}

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
    if (FRONT / "index.html").is_file():
        print(f"  Front novo:       {endereco}novo/")
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
        sincronia.navegador.fechar()  # a janela das contas conectadas fecha junto com o dashboard
    return 0


if __name__ == "__main__":
    sys.exit(main())
