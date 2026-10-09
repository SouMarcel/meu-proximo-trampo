"""Currículo, carta e respostas de formulário pela página, em segundo plano (uma geração por vez).

O servidor chama GERACAO.iniciar(vaga_id, tecnicas) (currículo) ou GERACAO.iniciar_kit(tipo, vaga_id, dados)
(carta ou respostas) no clique da pessoa (nunca antes), GERACAO.estado() para o andamento e GERACAO.tentar()
para repetir o último pedido que falhou. A escrita é da IA escolhida no painel IA; os arquivos, a
conferência e o meta saem de curriculo_ia.gerar e de candidatura_ia.
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


def _candidatura_ia():
    _raiz()
    import candidatura_ia
    return candidatura_ia


NOMES = {"curriculo": "o currículo", "carta": "a carta", "respostas": "as respostas"}


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
        self._ultimo_pedido = ("curriculo", vaga_id, tec)
        with self._trava:
            self._e = {"situacao": "escrevendo", "tipo": "curriculo", "alvo": {"vaga_id": vaga_id, "titulo": (vaga or {}).get("titulo"),
                                                          "empresa": (vaga or {}).get("empresa")} if vaga else {"base": True},
                       "tecnicas": tec, "inicio": datetime.now().isoformat(timespec="seconds"), "nome": None, "mensagem": ""}
            self._thread = threading.Thread(target=self._rodar, args=(vaga, tec), daemon=True, name="gerar-curriculo")
            self._thread.start()
        return self.estado()

    def iniciar_kit(self, tipo: str, vaga_id: str, dados) -> dict:
        """Carta (dados = as quatro respostas) ou respostas de formulário (dados = as perguntas coladas)."""
        cand, ia = _candidatura_ia(), _ia()
        if tipo not in ("carta", "respostas"):
            raise ValueError("tipo de documento inválido")
        with self._trava:
            if self.rodando():
                raise GeracaoOcupada("Já há um documento sendo gerado; espere ele terminar.")
        vaga = banco.obter(vaga_id) if vaga_id else None
        if not vaga:
            raise ValueError("vaga não encontrada")
        try:  # o que falta a pessoa responder vem antes da IA e do perfil
            dados = cand.validar_respostas(dados) if tipo == "carta" else str(dados or "")
            if tipo == "respostas" and not cand.separar(dados):
                raise cand.GeracaoErro("cole as perguntas do formulário, uma por linha")
        except cand.GeracaoErro as e:
            raise ValueError(str(e)) from None
        if not ia.disponivel():
            raise ValueError(f"Escrever {NOMES[tipo]} pela página precisa de uma IA: escolha uma no botão IA "
                             f"(ou peça no chat do seu assistente, com a skill gerar-curriculo).")
        if not _curriculo_ia().perfil_texto():
            raise ValueError(f"Monte o seu perfil antes (botão Meu perfil): {NOMES[tipo]} sai só dos fatos dele.")
        self._ultimo_pedido = (tipo, vaga_id, dados)
        with self._trava:
            self._e = {"situacao": "escrevendo", "tipo": tipo,
                       "alvo": {"vaga_id": vaga_id, "titulo": vaga.get("titulo"), "empresa": vaga.get("empresa")},
                       "inicio": datetime.now().isoformat(timespec="seconds"), "nome": None, "mensagem": ""}
            self._thread = threading.Thread(target=self._rodar_kit, args=(tipo, vaga, dados), daemon=True,
                                            name=f"gerar-{tipo}")
            self._thread.start()
        return self.estado()

    def tentar(self) -> dict:
        if not self._ultimo_pedido or self._e.get("situacao") != "falha":
            raise GeracaoOcupada("Não há geração com falha para tentar de novo.")
        tipo, vaga_id, dados = self._ultimo_pedido
        return self.iniciar(vaga_id, dados) if tipo == "curriculo" else self.iniciar_kit(tipo, vaga_id, dados)

    def _rodar_kit(self, tipo: str, vaga: dict, dados):
        cand = _candidatura_ia()
        try:
            gerar = cand.gerar_carta if tipo == "carta" else cand.gerar_respostas
            meta = gerar(vaga, dados, progresso=lambda etapa: self._set(situacao=etapa))
            banco.registrar_documento(vaga["id"], tipo, meta["nome"])
            veredito = (meta.get("conferencia") or {}).get("veredito")
            self._set(situacao="pronto", nome=meta["nome"], veredito=veredito, pronto=meta.get("pronto", True),
                      fim=datetime.now().isoformat(timespec="seconds"))
        except cand.GeracaoErro as e:
            self._set(situacao="falha", mensagem=str(e), fim=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:  # nunca derruba o servidor
            print(f"[{tipo} pela página] erro: {e!r}", file=sys.stderr)
            self._set(situacao="falha", mensagem="A geração parou por um erro inesperado; os detalhes estão na janela do servidor.",
                      fim=datetime.now().isoformat(timespec="seconds"))

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
