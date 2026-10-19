"""Candidaturas lidas nos portais (contas/) → proposta para o quadro → aplicar só o que a pessoa marcou (spec 018).

  proposta(lidas, vagas)   pura: casa cada candidatura com o banco e diz o que mudaria (nunca rebaixa a etapa;
                           encerrada é final)
  aplicar(itens)           grava só os itens recebidos (os marcados), com anotação e a data da etapa do portal
  LEITURA                  leitura em segundo plano (a Gupy pode esperar o clique de login da pessoa)

Nada é gravado na leitura: a proposta espera a pessoa (constituição V).
"""
from __future__ import annotations

import json
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path

import banco

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(1, str(RAIZ))
import contas  # noqa: E402
import navegador  # noqa: E402

ULTIMA = contas.PASTA / "ultima.json"
ESPERA_LOGIN = 180  # segundos esperando a pessoa logar na janela
PASSO_LOGIN = 3


def _item(tipo: str, lida: dict, vaga: dict | None, para: dict) -> dict:
    de = {"etapa": (vaga or {}).get("etapa"), "resultado": (vaga or {}).get("resultado")} if vaga else None
    marcado = tipo in ("mudar", "quadro") or (tipo == "nova" and lida.get("ativa"))
    return {"chave": f"{lida['portal']}:{lida['id'] or lida['titulo']}", "portal": lida["portal"],
            "plataforma": lida["plataforma"], "tipo": tipo, "vaga_id": (vaga or {}).get("id"),
            "titulo": (vaga or {}).get("titulo") or lida["titulo"], "empresa": (vaga or {}).get("empresa") or lida["empresa"],
            "de": de, "para": para, "status": lida["status"], "nota": lida["nota"], "avisos": lida["avisos"],
            "data": lida["data"], "url": lida["url"], "marcado": bool(marcado), "lida": lida}


def proposta(lidas: list[dict], vagas: list[dict]) -> dict:
    """{"itens": [...], "sem_mudanca": n}. Casamento: os ids que o banco conhece (banco.ids_da_vaga) e, na falta,
    cargo + empresa no banco inteiro."""
    por_id, por_chave = {}, {}
    id_gupy = banco._id_gupy()
    for v in vagas:
        for i in banco.ids_da_vaga(v, id_gupy):
            por_id.setdefault(i, v)
        k = banco.chave_vaga(v.get("titulo"), v.get("empresa"))
        if k:
            por_chave.setdefault(k, v)
    escolhidos: dict[str, dict] = {}
    sem_mudanca = 0
    for x in lidas:
        vaga = por_id.get(x["id"]) if x.get("id") else None
        vaga = vaga or por_chave.get(banco.chave_vaga(x["titulo"], x["empresa"]) or "")
        para = {"etapa": x["etapa"], "resultado": x["resultado"] if x["etapa"] == "encerrada" else None}
        if vaga is None:
            if not x["etapa"] or not x["id"]:
                continue
            item = _item("nova", x, None, para)
        elif not vaga.get("etapa"):
            item = _item("quadro", x, vaga, para) if x["etapa"] else _item("info", x, vaga, para)
        elif contas.avancou(vaga.get("etapa"), x["etapa"]):
            item = _item("mudar", x, vaga, para)
        else:
            if x["avisos"]:
                escolhidos.setdefault(f"info:{vaga['id']}:{x['portal']}", _item("info", x, vaga, para))
            sem_mudanca += 1
            continue
        alvo = vaga["id"] if vaga else item["chave"]
        atual = escolhidos.get(alvo)  # mesma vaga em dois portais: fica a etapa mais avançada
        if atual is None or contas.avancou((atual["para"] or {}).get("etapa"), para["etapa"]):
            escolhidos[alvo] = item
    ordem = {"mudar": 0, "quadro": 1, "nova": 2, "info": 3}
    itens = sorted(escolhidos.values(), key=lambda i: (i["plataforma"], ordem[i["tipo"]], not i["marcado"], i["titulo"]))
    return {"itens": itens, "sem_mudanca": sem_mudanca}


def _anotacao(item: dict) -> str:
    partes = [f"Etapa atualizada pela {item['plataforma']} em {banco.hoje()}: {item['status']}"]
    partes += [item["nota"]] if item["nota"] else []
    partes += item["avisos"]
    return " · ".join(partes)


def _descricao(lida: dict) -> dict:
    """Dados públicos da vaga nova (descrição), quando o leitor público do portal consegue; senão, {}."""
    try:
        if lida["portal"] == "gupy" and lida["id"].startswith("gupy-"):
            from fontes import gupy
            return gupy.ler(lida["id"])
        if lida["portal"] == "indeed" and lida["url"]:
            from fontes import link
            return link.ler(lida["url"])
    except Exception:  # sem descrição a vaga entra assim mesmo; a nota fica pendente
        pass
    return {}


def aplicar(itens: list[dict]) -> dict:
    """Grava os itens recebidos (os que a pessoa marcou). Devolve {"aplicados": n, "erros": [...]}."""
    aplicados, erros = 0, []
    for item in itens:
        lida, para = item["lida"], item["para"]
        try:
            campos = {"etapa": para["etapa"], "etapa_em": lida["data"],
                      "resultado": para["resultado"] if para["etapa"] == "encerrada" else None}
            if item["tipo"] == "nova":
                publico = _descricao(lida)
                dados = {**{k: v for k, v in publico.items() if v}, "id": lida["id"],
                         "plataforma": lida["plataforma"], "titulo": publico.get("titulo") or lida["titulo"],
                         "empresa": publico.get("empresa") or lida["empresa"], "local": publico.get("local") or lida["local"],
                         "url": lida["url"] or publico.get("url") or ""}
                vaga, _ = banco.criar_de_link(dados)
                vid = vaga["id"]
                campos.update(triagem="seguir", triada_em=banco.hoje())
            elif item["tipo"] in ("mudar", "quadro"):
                vid = item["vaga_id"]
                if item["tipo"] == "quadro":
                    campos.update(triagem="seguir", triada_em=banco.hoje())
            else:
                continue
            banco.atualizar_usuario(vid, campos)
            banco.anotar(vid, _anotacao(item))
            aplicados += 1
        except (ValueError, KeyError) as e:
            erros.append(f"{item['titulo']}: {e}")
    return {"aplicados": aplicados, "erros": erros}


class Leitura:
    """A leitura dos portais conectados, em segundo plano, com o estado para a página acompanhar."""

    def __init__(self):
        self._trava = threading.Lock()
        self.estado = {"situacao": "parada"}
        self.resultado: dict | None = None

    def rodando(self) -> bool:
        return self.estado.get("situacao") in ("lendo", "aguardando_login")

    def iniciar(self, portais: list[str]) -> dict:
        with self._trava:
            if self.rodando():
                return self.estado
            self.estado = {"situacao": "lendo", "portal": None, "inicio": datetime.now().isoformat(timespec="seconds")}
            self.resultado = None
        threading.Thread(target=self._rodar, args=(list(portais),), daemon=True).start()
        return self.estado

    def _esperar_login(self, aba, modulo) -> bool:
        """Traz a janela para a frente e espera a página voltar logada ao portal (o login pode passar por outro
        site, como o LinkedIn no "Entrar com LinkedIn"); a pessoa é quem faz o login."""
        aba.frente()
        limite = time.monotonic() + ESPERA_LOGIN
        while time.monotonic() < limite:
            time.sleep(PASSO_LOGIN)
            try:
                if modulo.logado(aba.url()):
                    time.sleep(PASSO_LOGIN)  # deixa o portal terminar de gravar a sessão antes de ler
                    return True
            except navegador.NavegadorErro:
                return False
        return False

    def _ler_portal(self, modulo, aba) -> list[dict]:
        try:
            return modulo.ler(aba)
        except contas.PortalErro as e:
            if not e.login:
                raise
        self.estado.update(situacao="aguardando_login", portal=modulo.PLATAFORMA)
        if not self._esperar_login(aba, modulo):
            raise contas.PortalErro(f"o login na {modulo.PLATAFORMA} não foi concluído na janela")
        self.estado.update(situacao="lendo")
        lidas = modulo.ler(aba)
        aba.minimizar()
        return lidas

    def _rodar(self, portais: list[str]) -> None:
        """A janela fica aberta e minimizada depois da leitura (decisão da pessoa): a Gupy esquece o login quando
        ela fecha. Ela fecha no Desconectar ou quando o dashboard para."""
        lidas, erros, aba, r = [], {}, None, None
        try:
            for nome in portais:
                modulo = contas.CONTAS.get(nome)
                if modulo is None:
                    continue
                self.estado.update(situacao="lendo", portal=modulo.PLATAFORMA)
                try:
                    aba = aba or navegador.abrir(modulo.URL_CANDIDATURAS, minimizado=True)
                    lidas += self._ler_portal(modulo, aba)
                except contas.PortalErro as e:
                    erros[modulo.PLATAFORMA] = str(e)
                except navegador.NavegadorErro as e:
                    erros[modulo.PLATAFORMA] = str(e)
                    aba = None  # a janela foi fechada ou não respondeu: o próximo portal abre de novo
                except Exception as e:  # nada pode deixar a leitura presa em "lendo"
                    erros[modulo.PLATAFORMA] = f"erro inesperado ({type(e).__name__})"
                    aba = None
            r = proposta(lidas, banco.listar_vagas())
        finally:
            if aba is not None:
                aba.minimizar()
                aba.fechar()  # só a conexão; a janela continua aberta
            r = r or {"itens": [], "sem_mudanca": 0}
            r.update(erros=erros, lidas_em=datetime.now().isoformat(timespec="seconds"))
            self.resultado = r
            self.estado = {"situacao": "pronta", "fim": r["lidas_em"]}
        try:
            contas.PASTA.mkdir(parents=True, exist_ok=True)
            ULTIMA.write_text(json.dumps({"lidas_em": r["lidas_em"], "itens": len(r["itens"])}), encoding="utf-8")
        except OSError:
            pass

    def ultima(self) -> str | None:
        try:
            return json.loads(ULTIMA.read_text(encoding="utf-8")).get("lidas_em")
        except (OSError, ValueError):
            return None

    def aplicar(self, chaves: list[str]) -> dict:
        """Aplica os itens da última proposta cujas chaves a pessoa marcou (o conteúdo vem do servidor, não da
        página)."""
        if self.rodando() or not self.resultado:
            raise ValueError("não há proposta para aplicar; atualize as candidaturas")
        marcados = [i for i in self.resultado["itens"] if i["chave"] in set(chaves) and i["tipo"] != "info"]
        r = aplicar(marcados)
        self.resultado["itens"] = [i for i in self.resultado["itens"] if i not in marcados]
        return r


LEITURA = Leitura()
