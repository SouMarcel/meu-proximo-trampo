"""Post do LinkedIn com uma vaga (botão Adicionar Vaga do dashboard, spec 016).

Muitas vagas são publicadas como post comum, no feed, e não na área de vagas. O post é texto livre, sem os dados
estruturados que fontes/link.py lê. Aqui:

- id_do_post(url)  reconhece o link de um post (feed/update, posts, share, ugcPost) e o id da vaga (lip-…);
- ler(url)         um único pedido à versão pública de incorporação do post (a que o LinkedIn oferece para mostrar
                   um post em outros sites), sem login, sem cookies e sem seguir redirecionamento. Devolve o texto
                   inteiro, quem publicou (empresa ou pessoa) e o link canônico.

É um pedido pontual, feito pela pessoa, como o link de vaga do LinkedIn: não grava nem consulta a espera de 6
horas da busca (fontes/linkedin.py). No bloqueio, para sem nova tentativa e levanta PostErro com o motivo.
"""
from __future__ import annotations

import re
import urllib.error
import urllib.request
from urllib.parse import unquote

from . import link, linkedin

EMBED = "https://www.linkedin.com/embed/feed/update/"
CANONICO = "https://www.linkedin.com/feed/update/"
TEMPO = 20
LIMITE_BYTES = 3_000_000
LIMITE_TEXTO = 20000
TEXTO = "attributed-text-segment-list__content"
AUTOR = "public_post_embed_feed-actor-name"
PREFIXO = {"activity": "lip-", "share": "lip-s", "ugcPost": "lip-u"}


class PostErro(Exception):
    """Não deu para ler o post; a mensagem é o motivo, para a pessoa."""


def id_do_post(url: str) -> dict | None:
    """{"urn", "id"} do post do LinkedIn no link, ou None se o link não é de um post."""
    texto = unquote(unquote(str(url or "")))
    if "linkedin." not in texto.lower():
        return None
    m = re.search(r"urn:li:(activity|share|ugcPost):(\d{6,25})", texto)
    if not m:
        m = re.search(r"/posts/[^?#]*?-(activity)-(\d{6,25})-", texto)
    if not m:
        return None
    tipo, numero = m.group(1), m.group(2)
    return {"urn": f"urn:li:{tipo}:{numero}", "id": PREFIXO[tipo] + numero}


def _baixar(urn: str) -> str:
    req = urllib.request.Request(EMBED + urn, headers={"User-Agent": link.NAVEGADOR,
                                                        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
    try:
        with urllib.request.build_opener(linkedin._SemRedirecionar).open(req, timeout=TEMPO) as r:
            corpo = r.read(LIMITE_BYTES + 1)
            charset = r.headers.get_content_charset() or "utf-8"
        linkedin.registrar_pedido("post", 200, de="adicionar")  # o registro dos pedidos ao LinkedIn (spec 024)
    except urllib.error.HTTPError as e:
        linkedin.registrar_pedido("post", e.code, de="adicionar")
        if e.code in (404, 410):
            raise PostErro("o post não existe mais ou não é público (só para conexões)") from None
        if e.code in (429, 999, 401, 403) or 300 <= e.code < 400:
            raise PostErro(f"o LinkedIn não deixou ler o post ({linkedin._motivo(e.code)})") from None
        raise PostErro(f"o LinkedIn respondeu {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        linkedin.registrar_pedido("post", "rede", de="adicionar")
        raise PostErro(f"não consegui falar com o LinkedIn ({getattr(e, 'reason', e)})") from None
    if len(corpo) > LIMITE_BYTES:
        raise PostErro("página grande demais")
    return corpo.decode(charset, errors="replace")


def _autor(pagina: str) -> tuple[str, str]:
    """(nome, tipo) de quem publicou: tipo "empresa" (página de empresa), "pessoa" ou ""."""
    for m in re.finditer(r"<a\b[^>]*>(.*?)</a>", pagina, re.S):
        abre = m.group(0)[:m.group(0).find(">") + 1]
        if AUTOR not in abre:
            continue
        nome = " ".join(link.texto_de_html(m.group(1)).split())[:120]
        href = (re.search(r'href="([^"]*)"', abre) or [None, ""])[1]
        tipo = "empresa" if "/company/" in href else "pessoa" if "/in/" in href else ""
        return nome, tipo if nome else ""
    return "", ""


def ler(url: str) -> dict:
    """{"id", "url", "texto", "autor", "autor_tipo"} do post. Levanta PostErro."""
    achado = id_do_post(url)
    if not achado:
        raise PostErro("o link não é de um post do LinkedIn")
    pagina = _baixar(achado["urn"])
    classes = link._Classes((TEXTO,))
    classes.feed(pagina)
    classes.close()
    texto = link.texto_de_html(classes.achados[TEXTO][0]) if classes.achados[TEXTO] else ""
    if not texto:
        raise PostErro("não achei o texto do post")
    dados = link._Dados()
    dados.feed(pagina)
    dados.close()
    canonico = id_do_post(dados.meta.get("og:url", ""))
    if canonico and canonico["urn"].startswith("urn:li:activity:"):
        achado = canonico
    autor, tipo = _autor(pagina)
    return {"id": achado["id"], "url": CANONICO + achado["urn"], "texto": texto[:LIMITE_TEXTO],
            "autor": autor, "autor_tipo": tipo}
