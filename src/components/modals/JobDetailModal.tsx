/**
 * Detalhe da vaga: descrição (como texto), análise como o servidor manda, o que a candidatura pede e as anotações.
 * Currículo, carta e respostas chegam na História 4 da spec 025.
 */
import React, { useState } from "react"
import {
  X,
  ExternalLink,
  MapPin,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  CheckSquare,
  Edit3,
  Trash2,
  Clock,
  Save,
  Mail,
  Info,
} from "lucide-react"
import type { CamposEditaveis, Etapa, Resultado, Vaga, Versao } from "../../types/api"
import {
  getPlataformaStyle,
  getAderenciaBadge,
  getEtapaInfo,
  formatarDataRelativa,
  formatarModelo,
  formatarSenioridade,
  situacaoNota,
  podeForcar,
  linkSeguro,
  temNota,
  noQuadro,
  hoje,
} from "../../utils/formatters"
import { AUTORIZACAO, CONTRATACAO, ESTADOS_KIT, ETAPAS, INGLES, PEDE, RESULTADOS, RISCOS, TIPOS_EMPREGO } from "../../utils/rotulos"
import { useFerramenta, AvisoSoLeitura } from "../../contexto/Ferramenta"
import TextoDaVaga from "../TextoDaVaga"
import { KitDaVaga, Lembrete } from "../kit/Kit"
import { GerarCurriculo, SecaoCurriculos } from "../curriculo/Curriculos"

interface JobDetailModalProps {
  vaga: Vaga
  versao: Versao | null
  onClose: () => void
  onUpdateVaga: (id: string, campos: CamposEditaveis, sucesso?: string) => Promise<boolean>
  onDeleteVaga: (id: string) => Promise<void>
  onForcarVerificar?: (id: string) => Promise<void> | void
  onAviso: (mensagem: string, tipo?: "info" | "erro") => void
  onAbrirPerfil: () => void
}

type DetailTab = "descricao" | "analise" | "kit" | "anotacoes"

const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"

function Frase({ frase }: { frase?: string }) {
  if (!frase) return null
  return <span className="block text-[11px] italic text-slate-500 dark:text-slate-400 mt-0.5">“{frase}”</span>
}

export default function JobDetailModal({
  vaga,
  versao,
  onClose,
  onUpdateVaga,
  onDeleteVaga,
  onForcarVerificar,
  onAviso,
  onAbrirPerfil,
}: JobDetailModalProps) {
  const { podeGravar } = useFerramenta()
  const [activeTab, setActiveTab] = useState<DetailTab>("descricao")
  const [anotacao, setAnotacao] = useState(vaga.anotacao || "")
  const [email, setEmail] = useState(vaga.email_candidatura || "")
  const [assunto, setAssunto] = useState(vaga.assunto_candidatura || "")
  const [entrevistaEm, setEntrevistaEm] = useState(vaga.entrevista_em || "")
  const [salvando, setSalvando] = useState(false)
  const [confirmarRemocao, setConfirmarRemocao] = useState(false)
  const [gerarCv, setGerarCv] = useState(false)

  const platStyle = getPlataformaStyle(vaga.plataforma)
  const aderBadge = getAderenciaBadge(vaga.aderencia)
  const etapaInfo = getEtapaInfo(vaga.etapa)
  const nota = situacaoNota(vaga, versao)
  const linkVaga = linkSeguro(vaga.url)
  const linkCandidatura = linkSeguro(vaga.url_candidatura) || linkVaga
  const estaNoQuadro = noQuadro(vaga)

  const salvar = async () => {
    setSalvando(true)
    const campos: CamposEditaveis = {
      anotacao: anotacao.slice(0, 5000),
      email_candidatura: email.trim(),
      assunto_candidatura: assunto.trim(),
    }
    if ((entrevistaEm || null) !== (vaga.entrevista_em || null)) campos.entrevista_em = entrevistaEm || null
    await onUpdateVaga(vaga.id, campos, "Anotações salvas.")
    setSalvando(false)
  }

  const mudarEtapa = (etapa: Etapa) => {
    const campos: CamposEditaveis = { etapa, etapa_em: hoje() }
    if (etapa !== "encerrada") campos.resultado = null
    onUpdateVaga(vaga.id, campos)
  }

  const abaBotao = (id: DetailTab, rotulo: string, Icone?: typeof Sparkles) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`py-3 px-2 sm:px-3 text-xs sm:text-sm font-semibold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap ${
        activeTab === id
          ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
          : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
      }`}
    >
      {Icone && <Icone className="w-3.5 h-3.5" />}
      <span>{rotulo}</span>
    </button>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-detalhe"
        className="relative w-full max-w-4xl max-h-[92vh] bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabeçalho */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`px-2.5 py-0.5 rounded-lg text-xs font-semibold border ${platStyle.bg} ${platStyle.text} ${platStyle.border}`}>
                {vaga.plataforma}
              </span>
              {estaNoQuadro && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${etapaInfo.badgeBg} ${etapaInfo.badgeText}`}>
                  {etapaInfo.label}
                  {vaga.etapa === "encerrada" && vaga.resultado ? ` · ${RESULTADOS[vaga.resultado]}` : ""}
                </span>
              )}
              {temNota(vaga) && (
                <span className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border ${aderBadge.bg} ${aderBadge.text} ${aderBadge.ring}`}>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>
                    {vaga.aderencia} · {vaga.nota_sem_descricao ? "nota provisória" : aderBadge.label}
                  </span>
                </span>
              )}
            </div>
            <h2 id="titulo-detalhe" className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white leading-snug">
              {vaga.titulo}
            </h2>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-600 dark:text-slate-400 flex-wrap">
              <span className="font-semibold text-slate-800 dark:text-slate-200">{vaga.empresa}</span>
              {vaga.local && (
                <>
                  <span>·</span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    {vaga.local}
                  </span>
                </>
              )}
              {vaga.salario && (
                <>
                  <span>·</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">{vaga.salario}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {linkCandidatura && (
              <a
                href={linkCandidatura}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
                title="Só abre a página do portal: a candidatura é você quem faz"
              >
                <span className="hidden sm:inline">Abrir a vaga</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
            <button onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Abas */}
        <div className="flex items-center border-b border-slate-200 dark:border-slate-800 px-3 sm:px-6 gap-1 sm:gap-2 bg-white dark:bg-slate-900 overflow-x-auto">
          {abaBotao("descricao", "Descrição")}
          {abaBotao("analise", "Análise da IA", Sparkles)}
          {abaBotao("kit", "Candidatura", CheckSquare)}
          {abaBotao("anotacoes", "Andamento e anotações", Edit3)}
        </div>

        <div className="p-4 sm:p-6 overflow-y-auto flex-1 space-y-4">
          {/* Descrição */}
          {activeTab === "descricao" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                {[
                  ["Modelo", formatarModelo(vaga.modelo_trabalho, vaga.remoto)],
                  [
                    "Senioridade",
                    formatarSenioridade(vaga.senioridade) +
                      (vaga.senioridade_origem === "sugerida" && vaga.senioridade?.length ? " (sugerida)" : ""),
                  ],
                  [
                    "Contrato",
                    vaga.tipo_emprego?.length
                      ? vaga.tipo_emprego.map((t) => TIPOS_EMPREGO[t] || t).join(", ")
                      : vaga.tipo || "Não informado",
                  ],
                  ["Publicada", formatarDataRelativa(vaga.publicada_em)],
                ].map(([rotulo, valor]) => (
                  <div key={rotulo} className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block font-medium">{rotulo}</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">{valor}</span>
                  </div>
                ))}
              </div>

              {vaga.descricao_pendente && (
                <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-600 shrink-0" />
                  <p className="text-xs text-amber-800 dark:text-amber-200">
                    O portal limitou os pedidos e a descrição ainda não chegou. Ela é lida na próxima busca ou em
                    Completar descrições, no Relatório; só então a vaga ganha nota.
                  </p>
                </div>
              )}

              {(vaga.motivo_fora || []).length > 0 && (
                <p className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-800 dark:text-rose-200">
                  <b>Fora dos critérios:</b> {(vaga.motivo_fora || []).join("; ")}
                </p>
              )}

              <div className="space-y-2">
                <h4 className="font-bold text-sm text-slate-900 dark:text-white">Texto do anúncio</h4>
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
                  <TextoDaVaga texto={vaga.descricao} />
                </div>
              </div>
            </div>
          )}

          {/* Análise */}
          {activeTab === "analise" && (
            <div className="space-y-4">
              {!temNota(vaga) ? (
                <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 text-center space-y-3">
                  <Sparkles className="w-8 h-8 text-indigo-500 mx-auto" />
                  <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                    {nota.tipo === "verificando"
                      ? "Verificando: a nota chega em alguns minutos."
                      : nota.tipo === "pendente"
                        ? "Aguardando a nota da IA."
                        : nota.tipo === "descricao_pendente"
                          ? "Sem nota até a descrição chegar."
                          : "Esta vaga ainda não tem nota de aderência."}
                  </h4>
                  {nota.tipo === "falha" && (
                    <p className="text-xs text-rose-600 dark:text-rose-400">Não deu para verificar: {nota.motivo}</p>
                  )}
                  {onForcarVerificar && podeForcar(vaga) && nota.tipo !== "verificando" && (
                    <button
                      disabled={!podeGravar}
                      onClick={() => onForcarVerificar(vaga.id)}
                      className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 transition shadow-xs disabled:opacity-50"
                      title="Pede a nota desta vaga à IA agora"
                    >
                      Forçar verificar
                    </button>
                  )}
                </div>
              ) : (
                <>
                  {vaga.nota_sem_descricao && (
                    <p className="flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-xs text-amber-900 dark:text-amber-200">
                      <Info className="w-4 h-4 shrink-0" />
                      Nota provisória, dada sem o texto da vaga; ela é refeita quando a descrição chegar.
                    </p>
                  )}
                  {vaga.resumo && (
                    <div className="bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/60 rounded-2xl p-4 sm:p-5 space-y-2">
                      <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-bold text-sm">
                        <Sparkles className="w-4 h-4 text-indigo-600" />
                        <span>Resumo</span>
                      </div>
                      <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{vaga.resumo}</p>
                    </div>
                  )}
                  {(
                    [
                      ["Encaixe", vaga.encaixe, "text-emerald-700 dark:text-emerald-400", CheckCircle2],
                      ["Lacunas", vaga.lacunas, "text-amber-700 dark:text-amber-400", AlertTriangle],
                      ["Atenção", vaga.alertas, "text-rose-700 dark:text-rose-400", AlertTriangle],
                      ["Sinais", vaga.sinais, "text-teal-700 dark:text-teal-400", ShieldCheck],
                    ] as [string, string[] | undefined, string, typeof CheckCircle2][]
                  ).map(([titulo, itens, cor, Icone]) =>
                    itens && itens.length > 0 ? (
                      <div key={titulo} className="space-y-2">
                        <h4 className={`font-bold text-xs uppercase tracking-wider flex items-center gap-1.5 ${cor}`}>
                          <Icone className="w-4 h-4" />
                          <span>{titulo}</span>
                        </h4>
                        <ul className="space-y-1.5">
                          {itens.map((item, idx) => (
                            <li key={idx} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-slate-200">
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null,
                  )}
                  {(vaga.autorizacao || vaga.ingles || vaga.contratacao?.length || vaga.fuso || vaga.riscos?.length) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      {vaga.autorizacao && (
                        <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                          <b className="text-slate-500">Visto e autorização:</b> {AUTORIZACAO[vaga.autorizacao.valor] || vaga.autorizacao.valor}
                          <Frase frase={vaga.autorizacao.frase} />
                        </div>
                      )}
                      {vaga.ingles && (
                        <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                          <b className="text-slate-500">Inglês:</b> {INGLES[vaga.ingles.nivel] || vaga.ingles.nivel}
                          <Frase frase={vaga.ingles.frase} />
                        </div>
                      )}
                      {vaga.contratacao && vaga.contratacao.length > 0 && (
                        <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                          <b className="text-slate-500">Contratação:</b>
                          {vaga.contratacao.map((c, i) => (
                            <span key={i} className="block">
                              {CONTRATACAO[c.valor] || c.valor}
                              <Frase frase={c.frase} />
                            </span>
                          ))}
                        </div>
                      )}
                      {vaga.fuso && (
                        <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800">
                          <b className="text-slate-500">Fuso:</b> {vaga.fuso.texto}
                          <Frase frase={vaga.fuso.frase} />
                        </div>
                      )}
                      {vaga.riscos && vaga.riscos.length > 0 && (
                        <div className="p-3 rounded-xl border border-rose-200 dark:border-rose-900 bg-rose-50/50 dark:bg-rose-950/30">
                          <b className="text-rose-700 dark:text-rose-300">Riscos:</b>
                          {vaga.riscos.map((r, i) => (
                            <span key={i} className="block">
                              {RISCOS[r.tipo] || r.tipo}
                              <Frase frase={r.frase} />
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  {(vaga.analise_provedor || vaga.analise_modelo) && (
                    <p className="text-[11px] text-slate-400">
                      Nota dada por {[vaga.analise_provedor, vaga.analise_modelo].filter(Boolean).join(" · ")}
                      {vaga.analisada_em ? ` em ${formatarDataRelativa(vaga.analisada_em)}` : ""}.
                    </p>
                  )}
                </>
              )}
            </div>
          )}

          {/* O que a candidatura pede, currículos, cartas e respostas */}
          {activeTab === "kit" && (
            <div className="space-y-6">
              <KitDaVaga vaga={vaga} onUpdateVaga={onUpdateVaga} onGerarCurriculo={() => setGerarCv(true)} onAviso={onAviso} />
              <SecaoCurriculos vagaId={vaga.id} onGerar={() => setGerarCv(true)} />
            </div>
          )}

          {/* Andamento e anotações */}
          {activeTab === "anotacoes" && (
            <div className="space-y-4">
              <AvisoSoLeitura />
              <Lembrete vaga={vaga} onUpdateVaga={onUpdateVaga} />
              {estaNoQuadro && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label htmlFor="d-etapa" className={ROTULO}>Etapa</label>
                    <select
                      id="d-etapa"
                      value={vaga.etapa || ""}
                      disabled={!podeGravar}
                      onChange={(e) => mudarEtapa(e.target.value as Etapa)}
                      className={CAMPO}
                    >
                      {ETAPAS.map((e) => (
                        <option key={e.valor} value={e.valor}>{e.rotulo}</option>
                      ))}
                    </select>
                  </div>
                  {vaga.etapa === "encerrada" && (
                    <div>
                      <label htmlFor="d-resultado" className={ROTULO}>Resultado</label>
                      <select
                        id="d-resultado"
                        value={vaga.resultado || ""}
                        disabled={!podeGravar}
                        onChange={(e) => onUpdateVaga(vaga.id, { resultado: (e.target.value || null) as Resultado | null })}
                        className={CAMPO}
                      >
                        <option value="">Sem resultado</option>
                        {(Object.keys(RESULTADOS) as Resultado[]).map((r) => (
                          <option key={r} value={r}>{RESULTADOS[r]}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  <div>
                    <label htmlFor="d-entrevista" className={ROTULO}>Data da entrevista</label>
                    <input id="d-entrevista" type="date" value={entrevistaEm} onChange={(e) => setEntrevistaEm(e.target.value)} className={CAMPO} />
                  </div>
                </div>
              )}

              <div>
                <label htmlFor="d-anotacao" className={ROTULO}>Anotações</label>
                <textarea
                  id="d-anotacao"
                  rows={6}
                  maxLength={5000}
                  value={anotacao}
                  onChange={(e) => setAnotacao(e.target.value)}
                  placeholder="Contatos, retornos, perguntas feitas, impressões…"
                  className={CAMPO}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="d-email" className={ROTULO}>E-mail para candidatura (se a vaga pedir)</label>
                  <input id="d-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={CAMPO} />
                </div>
                <div>
                  <label htmlFor="d-assunto" className={ROTULO}>Assunto do e-mail</label>
                  <input id="d-assunto" value={assunto} onChange={(e) => setAssunto(e.target.value)} className={CAMPO} />
                </div>
              </div>
              {vaga.email_candidatura && (
                <a
                  href={`mailto:${encodeURIComponent(vaga.email_candidatura)}${
                    vaga.assunto_candidatura ? `?subject=${encodeURIComponent(vaga.assunto_candidatura)}` : ""
                  }`}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400"
                  title="Só abre o seu programa de e-mail: quem escreve e envia é você"
                >
                  <Mail className="w-3.5 h-3.5" /> Enviar por e-mail
                </a>
              )}

              <div className="flex items-center justify-between gap-3 pt-2 flex-wrap">
                {estaNoQuadro ? (
                  <div className="flex items-center gap-2">
                    <button
                      disabled={!podeGravar}
                      onClick={() => {
                        if (!confirmarRemocao) {
                          setConfirmarRemocao(true)
                          return
                        }
                        onDeleteVaga(vaga.id)
                      }}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition disabled:opacity-50 ${
                        confirmarRemocao
                          ? "bg-rose-600 text-white hover:bg-rose-500"
                          : "text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                      }`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>{confirmarRemocao ? "Confirmar remoção" : "Remover do quadro"}</span>
                    </button>
                    {confirmarRemocao && (
                      <button onClick={() => setConfirmarRemocao(false)} className="text-xs text-slate-500 hover:underline">
                        Cancelar
                      </button>
                    )}
                  </div>
                ) : (
                  <span />
                )}
                <button
                  onClick={salvar}
                  disabled={!podeGravar || salvando}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{salvando ? "Salvando…" : "Salvar"}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      {gerarCv && <GerarCurriculo vagaId={vaga.id} onClose={() => setGerarCv(false)} onAbrirPerfil={onAbrirPerfil} />}
    </div>
  )
}
