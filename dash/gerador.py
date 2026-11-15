"""Currículo, carta e respostas de formulário pela página, em segundo plano (uma geração por vez).

O servidor chama GERACAO.iniciar(vaga_id, tecnicas) (currículo), GERACAO.iniciar_kit(tipo, vaga_id, dados)
(carta ou respostas), GERACAO.iniciar_reprovacao / iniciar_reescrita (análise de reprovação, spec 049) ou
GERACAO.iniciar_revisao (revisão do perfil ao levar relatos, spec 050) no clique da pessoa (nunca antes),
GERACAO.estado() para o andamento e GERACAO.tentar() para repetir o último pedido que falhou. A escrita é da IA
escolhida no painel IA; os arquivos, a conferência e o meta saem de curriculo_ia.gerar e de candidatura_ia.
"""
from __future__ import annotations

import sys
import threading
from datetime import datetime

import banco

RAIZ = banco.DASH.parent
ETAPAS = {"escrevendo": "Escrevendo com a IA…", "gerando": "Gerando os arquivos…", "conferindo": "Conferindo…",
          "analisando": "Analisando como um recrutador…", "reescrevendo": "Reescrevendo os trechos genéricos…",
          "revisando": "Revisando o seu perfil…"}


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


def _reprovacao():
    _raiz()
    import reprovacao
    return reprovacao


def _revisao():
    _raiz()
    import revisao_perfil
    return revisao_perfil


NOMES = {"curriculo": "o currículo", "carta": "a carta", "respostas": "as respostas", "verificar": "a carta revisada",
         "reprovacao": "a análise de reprovação", "revisao_perfil": "a revisão do perfil"}


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
        saida = {**cia.curriculo.catalogo(vaga),
                 "ia": {"ligada": ia.disponivel(cfg), "nome": prov["nome"], "modelo": ia.modelo_efetivo(escolha),
                        "cobranca": ia.cobranca_efetiva(escolha)},
                 "perfil_ok": bool(cia.perfil_texto())}
        if vaga:  # o checkbox Análise de reprovação (spec 049)
            rep = _reprovacao()
            ok, motivo = rep.disponivel(vaga)
            saida["reprovacao"] = {"disponivel": ok, "motivo": motivo, "anterior": rep.anterior(vaga_id)}
        return saida

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
        if tipo not in ("carta", "respostas", "verificar"):
            raise ValueError("tipo de documento inválido")
        with self._trava:
            if self.rodando():
                raise GeracaoOcupada("Já há um documento sendo gerado; espere ele terminar.")
        vaga = banco.obter(vaga_id) if vaga_id else None
        if not vaga:
            raise ValueError("vaga não encontrada")
        try:  # o que falta a pessoa responder vem antes da IA e do perfil
            if tipo == "verificar":  # a carta editada pela pessoa (spec 035): {nome, texto, guardar_relatos}
                dados = dados if isinstance(dados, dict) else {}
                if not str(dados.get("texto") or "").strip():
                    raise cand.GeracaoErro("o texto da carta está vazio")
                if (cand._ler_meta(str(dados.get("nome") or "")).get("alvo") or {}).get("id") != vaga_id:
                    raise cand.GeracaoErro("esta carta não é desta vaga")
            else:
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

    def _pode_comecar(self, nome: str, sem_perfil: str = "a análise compara a vaga com os fatos dele"):
        """Confere a fila, a IA e o perfil antes de uma geração da análise de reprovação ou da revisão do perfil."""
        with self._trava:
            if self.rodando():
                raise GeracaoOcupada("Já há um documento sendo gerado; espere ele terminar.")
        if not _ia().disponivel():
            raise ValueError(f"{nome} pela página precisa de uma IA: escolha uma no botão IA.")
        if not _curriculo_ia().perfil_texto():
            raise ValueError(f"Monte o seu perfil antes (botão Meu perfil): {sem_perfil}.")

    def _comecar(self, tipo: str, situacao: str, vaga: dict | None, alvo_rodar, args, extra: dict | None = None,
                 alvo: dict | None = None):
        if alvo is None:
            alvo = {"vaga_id": vaga.get("id"), "titulo": vaga.get("titulo"), "empresa": vaga.get("empresa")}
        with self._trava:
            self._e = {"situacao": situacao, "tipo": tipo, "alvo": alvo,
                       "inicio": datetime.now().isoformat(timespec="seconds"), "nome": None, "mensagem": "", **(extra or {})}
            self._thread = threading.Thread(target=alvo_rodar, args=args, daemon=True, name=f"gerar-{tipo}")
            self._thread.start()
        return self.estado()

    def iniciar_reprovacao(self, vaga_id: str, tecnicas) -> dict:
        """Etapa 1 da análise de reprovação (spec 049): só a análise; o currículo espera as respostas."""
        rep, cia = _reprovacao(), _curriculo_ia()
        self._pode_comecar("A análise de reprovação")
        vaga = banco.obter(vaga_id) if vaga_id else None
        if not vaga:
            raise KeyError(vaga_id)
        ok, motivo = rep.disponivel(vaga)
        if not ok:
            raise ValueError(motivo)
        try:
            tec = cia.validar_tecnicas(tecnicas)
        except cia.GeracaoErro as e:
            raise ValueError(str(e)) from None
        self._ultimo_pedido = ("reprovacao", vaga_id, tec)
        return self._comecar("reprovacao", "analisando", vaga, self._rodar_reprovacao, (vaga, tec), {"tecnicas": tec})

    def iniciar_reescrita(self, vaga_id: str) -> dict:
        """Etapa 3: Reescrever e gerar o currículo, com as respostas da análise de reprovação."""
        rep = _reprovacao()
        self._pode_comecar("Reescrever e gerar o currículo")
        vaga = banco.obter(vaga_id) if vaga_id else None
        if not vaga:
            raise KeyError(vaga_id)
        analise = rep.obter(vaga_id)
        if not analise:
            raise ValueError("esta vaga não tem análise de reprovação")
        if not analise["pronta_para_gerar"]:
            raise ValueError("responda ou pule as perguntas")
        self._ultimo_pedido = ("reescrita", vaga_id, None)
        return self._comecar("curriculo", "reescrevendo", vaga, self._rodar_reescrita, (vaga,),
                             {"tecnicas": analise.get("tecnicas"), "reprovacao": True})

    def iniciar_revisao(self, origem: str, ids=None) -> dict:
        """Revisar e levar ao perfil (spec 050): a IA propõe onde cada relato entra; a pessoa decide e grava depois.
        origem: "vaga:<id>" (as respostas da análise de reprovação) ou "relatos" (ids marcados em Seus relatos)."""
        rv = _revisao()
        self._pode_comecar("A revisão do perfil", "a revisão põe os fatos nele")
        origem = rv._chave(origem)  # RevisaoErro (400) com origem inválida
        vaga, _ = rv._resolver(origem, ids)  # RevisaoErro: 404 sem análise, 400 sem relato
        alvo = ({"vaga_id": vaga.get("id"), "titulo": vaga.get("titulo"), "empresa": vaga.get("empresa")} if vaga
                else {"perfil": True})
        self._ultimo_pedido = ("revisao", origem, ids)
        return self._comecar("revisao_perfil", "revisando", None, self._rodar_revisao, (origem, ids), alvo=alvo)

    def tentar(self) -> dict:
        if not self._ultimo_pedido or self._e.get("situacao") != "falha":
            raise GeracaoOcupada("Não há geração com falha para tentar de novo.")
        tipo, vaga_id, dados = self._ultimo_pedido
        if tipo == "reprovacao":
            return self.iniciar_reprovacao(vaga_id, dados)
        if tipo == "reescrita":
            return self.iniciar_reescrita(vaga_id)
        if tipo == "revisao":
            return self.iniciar_revisao(vaga_id, dados)
        return self.iniciar(vaga_id, dados) if tipo == "curriculo" else self.iniciar_kit(tipo, vaga_id, dados)

    def _rodar_revisao(self, origem: str, ids):
        rv = _revisao()
        try:
            rv.revisar(origem, ids, progresso=lambda etapa: self._set(situacao=etapa))
            self._set(situacao="pronto", pronto=True, fim=datetime.now().isoformat(timespec="seconds"))
        except rv.RevisaoErro as e:
            self._set(situacao="falha", mensagem=str(e), fim=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:  # nunca derruba o servidor
            print(f"[revisão do perfil] erro: {e!r}", file=sys.stderr)
            self._set(situacao="falha", mensagem="A revisão parou por um erro inesperado; os detalhes estão na janela do servidor.",
                      fim=datetime.now().isoformat(timespec="seconds"))

    def _rodar_reprovacao(self, vaga: dict, tec: dict):
        rep = _reprovacao()
        try:
            rep.analisar(vaga, tec, progresso=lambda etapa: self._set(situacao=etapa))
            self._set(situacao="pronto", pronto=True, fim=datetime.now().isoformat(timespec="seconds"))
        except rep.ReprovacaoErro as e:
            self._set(situacao="falha", mensagem=str(e), fim=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:  # nunca derruba o servidor
            print(f"[análise de reprovação] erro: {e!r}", file=sys.stderr)
            self._set(situacao="falha", mensagem="A análise parou por um erro inesperado; os detalhes estão na janela do servidor.",
                      fim=datetime.now().isoformat(timespec="seconds"))

    def _rodar_reescrita(self, vaga: dict):
        rep, cia = _reprovacao(), _curriculo_ia()
        try:
            meta = rep.reescrever_e_gerar(vaga["id"], progresso=lambda etapa: self._set(situacao=etapa))
            banco.registrar_curriculo(vaga["id"], meta["nome"])
            self._set(situacao="pronto", nome=meta["nome"], veredito=meta["conferencia"]["veredito"], pronto=meta["pronto"],
                      fim=datetime.now().isoformat(timespec="seconds"))
        except (rep.ReprovacaoErro, cia.GeracaoErro) as e:
            self._set(situacao="falha", mensagem=str(e), fim=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:  # nunca derruba o servidor
            print(f"[reescrever e gerar] erro: {e!r}", file=sys.stderr)
            self._set(situacao="falha", mensagem="A geração parou por um erro inesperado; os detalhes estão na janela do servidor.",
                      fim=datetime.now().isoformat(timespec="seconds"))

    def _rodar_kit(self, tipo: str, vaga: dict, dados):
        cand = _candidatura_ia()
        try:
            if tipo == "verificar":
                meta = cand.verificar_carta(str(dados["nome"]), str(dados["texto"]), dados.get("guardar_relatos") is not False,
                                            progresso=lambda etapa: self._set(situacao=etapa))
            else:
                gerar = cand.gerar_carta if tipo == "carta" else cand.gerar_respostas
                meta = gerar(vaga, dados, progresso=lambda etapa: self._set(situacao=etapa))
            banco.registrar_documento(vaga["id"], "carta" if tipo == "verificar" else tipo, meta["nome"])
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
