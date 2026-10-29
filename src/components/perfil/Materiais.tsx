/**
 * Meu perfil → Materiais (spec 037; dash/API.md §3.6): três áreas, cada uma com o seu envio e a sua lista — Perfil do
 * LinkedIn (PDF do perfil, ZIP da exportação, link), Currículos (PDF e Word, os da pasta anexos, texto colado) e
 * Outros documentos e certificações (PDF e Word; nunca viram currículo). O arquivo vale como a área em que foi enviado;
 * "Mover para" troca a área sem reenviar. O aviso de área trocada só sugere: quem move é a pessoa. PDF sem texto ganha
 * o botão OCR (OCR do Windows, no próprio computador).
 */
import React, { useState } from "react"
import { Loader2, Upload, Trash2, ScanText } from "lucide-react"
import * as perfilApi from "../../services/api/perfil"
import type { AreaMaterial, CurriculosDaPasta, EstadoPerfil, Material } from "../../services/api/perfil"
import { mensagemDeErro } from "../../services/api"

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"
const BTN = "px-4 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
const BTN_PRI = `${BTN} text-white bg-indigo-600 hover:bg-indigo-500`
const BTN_SEC = `${BTN} text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700`
const BTN_MINI =
  "px-2.5 py-1 rounded-lg text-[11px] font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"
const AVISO_AREA =
  "flex items-center gap-2 flex-wrap p-2 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-[11px] text-amber-900 dark:text-amber-200"

const TIPOS_MATERIAL: Record<string, string> = {
  curriculo_pdf: "Currículo (PDF)",
  curriculo_docx: "Currículo (Word)",
  linkedin_pdf: "LinkedIn (PDF do perfil)",
  linkedin_zip: "LinkedIn (exportação de dados)",
  documento_pdf: "Documento (PDF)",
  documento_docx: "Documento (Word)",
  texto: "Texto colado",
}

const AREAS: { area: AreaMaterial; titulo: string; nome: string; aceita: string; formatos: string[]; dica: string }[] = [
  {
    area: "linkedin",
    titulo: "Perfil do LinkedIn",
    nome: "Perfil do LinkedIn",
    aceita: ".pdf,.zip",
    formatos: [".pdf", ".zip"],
    dica: "O PDF do seu perfil ou o ZIP da exportação de dados. Até 10 MB cada.",
  },
  {
    area: "curriculo",
    titulo: "Currículos",
    nome: "Currículos",
    aceita: ".pdf,.docx",
    formatos: [".pdf", ".docx"],
    dica: "Currículo em PDF ou Word (.docx). Até 10 MB cada.",
  },
  {
    area: "documento",
    titulo: "Outros documentos e certificações",
    nome: "Outros documentos e certificações",
    aceita: ".pdf,.docx",
    formatos: [".pdf", ".docx"],
    dica: "Certificados, diplomas, cartas de recomendação, em PDF ou Word. A IA usa em Formação e Certificações; nunca viram currículo.",
  },
]

const extensao = (arquivo: string) => (/\.[^.]+$/.exec(arquivo || "")?.[0] || "").toLowerCase()

/** A área de cada material; páginas antigas do servidor não mandam `area`, então sai do tipo. */
const areaDe = (m: Material): AreaMaterial =>
  m.area || (m.tipo.startsWith("linkedin") ? "linkedin" : m.tipo.startsWith("documento") ? "documento" : "curriculo")

export default function Materiais({
  e,
  cvs,
  so,
  onEnviar,
  onUsar,
  onEstado,
  onErro,
  onAviso,
  onLinkedin,
}: {
  e: EstadoPerfil
  cvs: CurriculosDaPasta | null
  so: boolean
  onEnviar: (files: FileList | File[] | null, area: AreaMaterial) => Promise<void>
  onUsar: (arquivo: string) => void
  onEstado: (e: EstadoPerfil) => void
  onErro: (err: unknown) => void
  onAviso: (m: string, t?: "info" | "erro") => void
  onLinkedin: (li: string) => void
}) {
  const [colado, setColado] = useState("")
  const [linkedin, setLinkedin] = useState(e.contato?.linkedin || "")
  const [sobre, setSobre] = useState<AreaMaterial | null>(null)
  const [enviando, setEnviando] = useState<AreaMaterial | null>(null)
  const [ocupado, setOcupado] = useState("")
  const ms = e.materiais
  const usados = ms.map((m) => m.arquivo)
  const noAnexos = (cvs?.curriculos || []).filter((c) => !usados.includes(c.arquivo))

  const enviar = async (files: FileList | File[] | null, area: AreaMaterial) => {
    setEnviando(area)
    await onEnviar(files, area)
    setEnviando(null)
  }

  const mover = async (m: Material, area: AreaMaterial) => {
    setOcupado(m.id)
    try {
      const j = await perfilApi.moverMaterial(m.id, area)
      onEstado(j.estado)
      onAviso(`${m.nome}: movido para ${AREAS.find((a) => a.area === area)?.nome}.${j.aviso ? " " + j.aviso : ""}`)
    } catch (err) {
      onErro(err)
    } finally {
      setOcupado("")
    }
  }

  const lerComOcr = async (m: Material) => {
    setOcupado(m.id)
    try {
      const j = await perfilApi.ocrMaterial(m.id)
      onEstado(j.estado)
      onAviso(j.material.tem_texto ? `${m.nome}: texto lido da imagem. Confira em "Texto lido".` : `${m.nome}: ${j.material.avisos.join(" ") || "o OCR não achou texto."}`, j.material.tem_texto ? "info" : "erro")
    } catch (err) {
      onAviso(`${m.nome}: ${mensagemDeErro(err)}`, "erro")
    } finally {
      setOcupado("")
    }
  }

  const item = (m: Material) => {
    const area = areaDe(m)
    const ext = extensao(m.arquivo)
    const destinos = m.tipo === "texto" || !m.arquivo ? [] : AREAS.filter((a) => a.area !== area && a.formatos.includes(ext))
    const sugerida = m.sugestao && AREAS.find((a) => a.area === m.sugestao?.area)
    const lendo = ocupado === m.id
    return (
      <li key={m.id} className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <p className="min-w-0 break-words">
            <b>{m.nome}</b> <span className={DICA}>{TIPOS_MATERIAL[m.tipo] || m.tipo}</span>
          </p>
          <span className="flex gap-1.5 flex-wrap items-center">
            {area === "curriculo" && /\.(pdf|docx)$/i.test(m.arquivo || "") && m.tem_texto && (
              <button type="button" disabled={so || lendo} onClick={() => onUsar(m.arquivo)} className={BTN_MINI}>
                Usar este currículo e ir para as vagas
              </button>
            )}
            {ext === ".pdf" && !m.tem_texto && e.ocr_disponivel && (
              <button
                type="button"
                disabled={so || Boolean(ocupado)}
                onClick={() => lerComOcr(m)}
                className={`${BTN_MINI} flex items-center gap-1`}
                title="Ler o texto da imagem do PDF com o OCR do Windows"
              >
                {lendo ? <Loader2 className="w-3 h-3 animate-spin" /> : <ScanText className="w-3 h-3" />} OCR
              </button>
            )}
            {destinos.length > 0 && (
              <>
                <label htmlFor={`mover-${m.id}`} className="sr-only">
                  Mover {m.nome} para
                </label>
                <select
                  id={`mover-${m.id}`}
                  value=""
                  disabled={so || Boolean(ocupado)}
                  onChange={(ev) => ev.target.value && mover(m, ev.target.value as AreaMaterial)}
                  className="px-2 py-1 rounded-lg text-[11px] font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-50"
                >
                  <option value="">Mover para…</option>
                  {destinos.map((d) => (
                    <option key={d.area} value={d.area}>
                      {d.nome}
                    </option>
                  ))}
                </select>
              </>
            )}
            <button
              type="button"
              disabled={so || lendo}
              onClick={() => perfilApi.removerMaterial(m.id).then(onEstado).catch(onErro)}
              className={`${BTN_MINI} flex items-center gap-1`}
            >
              <Trash2 className="w-3 h-3" /> Remover
            </button>
          </span>
        </div>
        {m.sugestao && sugerida && (
          <p className={AVISO_AREA}>
            <span>{m.sugestao.motivo}</span>
            <button type="button" disabled={so || Boolean(ocupado)} onClick={() => mover(m, sugerida.area)} className={BTN_MINI}>
              Mover para {sugerida.nome}
            </button>
          </p>
        )}
        {m.avisos.length > 0 && <p className="text-[11px] text-amber-700 dark:text-amber-300">{m.avisos.join(" · ")}</p>}
        {m.trecho && (
          <details>
            <summary className={`cursor-pointer ${DICA}`}>Texto lido{m.ocr ? " (OCR)" : ""}</summary>
            <pre className="whitespace-pre-wrap text-[11px] p-2 rounded-lg bg-slate-50 dark:bg-slate-800 max-h-48 overflow-y-auto">
              {m.trecho}
              {m.trecho.length >= 600 ? "…" : ""}
            </pre>
          </details>
        )}
      </li>
    )
  }

  const envio = (a: (typeof AREAS)[number]) => (
    <label
      className={`flex flex-col items-center gap-1 p-4 rounded-2xl border-2 border-dashed text-center cursor-pointer transition ${
        sobre === a.area ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40" : "border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/40"
      } ${so || enviando ? "opacity-60 pointer-events-none" : ""}`}
      onDragOver={(ev) => {
        ev.preventDefault()
        setSobre(a.area)
      }}
      onDragLeave={() => setSobre(null)}
      onDrop={(ev) => {
        ev.preventDefault()
        setSobre(null)
        enviar(ev.dataTransfer.files, a.area)
      }}
    >
      <input
        type="file"
        accept={a.aceita}
        multiple
        hidden
        disabled={so}
        onChange={(ev) => {
          enviar(ev.target.files, a.area)
          ev.target.value = ""
        }}
      />
      {enviando === a.area ? <Loader2 className="w-5 h-5 animate-spin text-indigo-500" /> : <Upload className="w-5 h-5 text-indigo-500" />}
      <b className="text-slate-800 dark:text-slate-200 text-xs sm:text-sm">Escolher ou arrastar arquivos</b>
      <span className={DICA}>{a.dica}</span>
    </label>
  )

  const lista = (area: AreaMaterial) => {
    const doTipo = ms.filter((m) => areaDe(m) === area)
    return doTipo.length ? <ul className="space-y-2">{doTipo.map(item)}</ul> : null
  }

  const [li, cv, doc] = AREAS
  return (
    <>
      <p className="text-slate-700 dark:text-slate-300">
        Envie cada arquivo na área dele. Os arquivos ficam na pasta anexos, neste computador; CPF, RG e data de
        nascimento são retirados do texto antes de qualquer envio à IA.
      </p>

      <section className={SEC}>
        <h4 className={H}>{li.titulo}</h4>
        {envio(li)}
        <details className="text-xs">
          <summary className={`cursor-pointer ${DICA}`}>Como baixar do LinkedIn</summary>
          <ul className="list-disc pl-5 space-y-1 mt-1">
            <li><b>PDF do perfil</b>: abra o seu perfil, clique em <i>Mais</i> e depois em <i>Salvar como PDF</i>.</li>
            <li>
              <b>Exportação de dados</b> (mais completa): <i>Eu → Configurações e privacidade → Privacidade de dados → Obter uma cópia dos seus dados</i>. O LinkedIn manda o ZIP por e-mail.
            </li>
            <li>A ferramenta não abre o LinkedIn: lê só os arquivos que você enviar.</li>
          </ul>
        </details>
        {lista("linkedin")}
        <label htmlFor="pf-linkedin" className={ROTULO}>Link do seu perfil (opcional)</label>
        <input
          id="pf-linkedin"
          maxLength={200}
          autoComplete="off"
          spellCheck={false}
          placeholder="linkedin.com/in/seu-nome"
          value={linkedin}
          disabled={so}
          onChange={(ev) => setLinkedin(ev.target.value)}
          className={CAMPO}
        />
        <p className={DICA}>Entra só como contato no perfil. A ferramenta não abre a página.</p>
      </section>

      <section className={SEC}>
        <h4 className={H}>{cv.titulo}</h4>
        {envio(cv)}
        {lista("curriculo")}
        {noAnexos.length > 0 && (
          <div className="space-y-1.5">
            <p className={ROTULO}>Currículos que já estão na pasta anexos</p>
            <ul className="space-y-1.5">
              {noAnexos.map((c) => (
                <li key={c.arquivo} className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="min-w-0 break-words">
                    <b>{c.nome}</b>{" "}
                    <span className={DICA}>
                      {c.arquivo} · {c.idioma === "en" ? "inglês" : "português"}
                    </span>
                  </span>
                  <button type="button" disabled={so} onClick={() => onUsar(c.arquivo)} className={BTN_MINI}>
                    Usar este currículo e ir para as vagas
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        <label htmlFor="pf-colar" className={ROTULO}>Ou cole o texto do currículo</label>
        <textarea id="pf-colar" rows={4} maxLength={60000} value={colado} disabled={so} onChange={(ev) => setColado(ev.target.value)} className={CAMPO} />
        <button
          type="button"
          disabled={so || !colado.trim()}
          onClick={async () => {
            try {
              const j = await perfilApi.enviarMaterial({ texto: colado.trim(), nome: "texto colado" })
              onEstado(j.estado)
              setColado("")
              onAviso("Texto adicionado.")
            } catch (err) {
              onErro(err)
            }
          }}
          className={BTN_SEC}
        >
          Adicionar texto
        </button>
      </section>

      <section className={SEC}>
        <h4 className={H}>{doc.titulo}</h4>
        {envio(doc)}
        {lista("documento")}
      </section>

      <div className="flex justify-end gap-2 pt-2">
        <button type="button" onClick={() => onLinkedin(linkedin.trim())} className={BTN_PRI}>
          {ms.length ? "Continuar" : "Continuar sem materiais"}
        </button>
      </div>
    </>
  )
}
