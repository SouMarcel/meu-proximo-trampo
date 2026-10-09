"""Currículo pela página, em segundo plano (uma geração por vez).

O servidor chama GERACAO.iniciar(vaga_id, tecnicas) no clique da pessoa (nunca antes), GERACAO.estado()
para o andamento e GERACAO.tentar() para repetir o último pedido que falhou. A escrita é da IA escolhida
no painel IA; os arquivos, a conferência e o meta saem de curriculo_ia.gerar.
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime

import banco

RAIZ = banco.DASH.parent
ETAPAS = {"escrevendo": "Escrevendo com a IA…", "gerando": "Gerando os arquivos…", "conferindo": "Conferindo…"}


def _raiz():
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))


def _curriculo_ia():
    _raiz()
    import curriculo_ia
    return curriculo_ia


def _ia():
    _raiz()
    import ia
    return ia


class GeracaoOcupada(Exception):
    """Já há uma geração rodando."""


class Geracao:
    def __init__(self):
        self._trava = threading.Lock()
        self._thread: threading.Thread | None = None
        self._e: dict = {"situacao": "ociosa"}
        self._ultimo_pedido: tuple | None = None

    def rodando(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _set(self, **campos):
        with self._trava:
            self._e.update(campos)

    def estado(self) -> dict:
        with self._trava:
            e = dict(self._e)
        e["pode_tentar"] = e.get("situacao") == "falha" and self._ultimo_pedido is not None and not self.rodando()
        e["etapa_texto"] = ETAPAS.get(e.get("situacao"), "")
        return e

    def preparar(self, vaga_id: str | None) -> dict:
        """O que o diálogo mostra: catálogo com a sugestão, IA e perfil."""
        cia, ia = _curriculo_ia(), _ia()
        vaga = banco.obter(vaga_id) if vaga_id else None
        if vaga_id and not vaga:
            raise KeyError(vaga_id)
        cfg = ia._ler_config()
        escolha = ia.escolha_efetiva(cfg)
        prov = ia.PROVEDORES[escolha["provedor"]]
        return {**cia.curriculo.catalogo(vaga),
                "ia": {"ligada": ia.disponivel(cfg), "nome": prov["nome"], "modelo": ia.modelo_efetivo(escolha),
                       "cobranca": prov["cobranca"]},
                "perfil_ok": bool(cia.perfil_texto())}

    def iniciar(self, vaga_id: str | None, tecnicas) -> dict:
        cia, ia = _curriculo_ia(), _ia()
        with self._trava:
            if self.rodando():
                raise GeracaoOcupada("Já há um currículo sendo gerado; espere ele terminar.")
        if not ia.disponivel():
            raise ValueError("Escrever o currículo pela página precisa de uma IA: escolha uma no botão IA "
                             "(ou peça o currículo no chat do seu assistente).")
        if not cia.perfil_texto():
            raise ValueError("Monte o seu perfil antes (botão Meu perfil): o currículo sai só dos fatos dele.")
        vaga = banco.obter(vaga_id) if vaga_id else None
        if vaga_id and not vaga:
            raise ValueError("vaga não encontrada")
        try:
            tec = cia.validar_tecnicas(tecnicas)
        except cia.GeracaoErro as e:
            raise ValueError(str(e)) from None
        self._ultimo_pedido = (vaga_id, tec)
        with self._trava:
            self._e = {"situacao": "escrevendo", "alvo": {"vaga_id": vaga_id, "titulo": (vaga or {}).get("titulo"),
                                                          "empresa": (vaga or {}).get("empresa")} if vaga else {"base": True},
                       "tecnicas": tec, "inicio": datetime.now().isoformat(timespec="seconds"), "nome": None, "mensagem": ""}
            self._thread = threading.Thread(target=self._rodar, args=(vaga, tec), daemon=True, name="gerar-curriculo")
            self._thread.start()
        return self.estado()

    def tentar(self) -> dict:
        if not self._ultimo_pedido or self._e.get("situacao") != "falha":
            raise GeracaoOcupada("Não há geração com falha para tentar de novo.")
        vaga_id, tec = self._ultimo_pedido
        return self.iniciar(vaga_id, tec)

    def _rodar(self, vaga: dict | None, tec: dict):
        cia = _curriculo_ia()
        try:
            meta = cia.gerar(vaga, tec, progresso=lambda etapa: self._set(situacao=etapa))
            if vaga:
                banco.registrar_curriculo(vaga["id"], meta["nome"])
            self._set(situacao="pronto", nome=meta["nome"], veredito=meta["conferencia"]["veredito"], pronto=meta["pronto"],
                      fim=datetime.now().isoformat(timespec="seconds"))
        except cia.GeracaoErro as e:
            self._set(situacao="falha", mensagem=str(e), fim=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:  # nunca derruba o servidor
            print(f"[currículo pela página] erro: {e!r}", file=sys.stderr)
            self._set(situacao="falha", mensagem="A geração parou por um erro inesperado; os detalhes estão na janela do servidor.",
                      fim=datetime.now().isoformat(timespec="seconds"))


GERACAO = Geracao()
