/**
 * Filtros da busca (dash/API.md §3.4), nacional e internacional, com as opções que o servidor aceita. Grava o objeto
 * inteiro em PUT /api/config; erro 400 mostra a regra que falhou. Valem a partir da próxima busca.
 */
import React, { useEffect, useMemo, useState } from "react"
import { X, SlidersHorizontal, Globe, Loader2, AlertTriangle, Plus } from "lucide-react"
import * as configApi from "../../services/api/config"
import type { Config, Filtros, Opcoes } from "../../services/api/config"
import { mensagemDeErro } from "../../services/api"
import { useFerramenta, AvisoSoLeitura } from "../../contexto/Ferramenta"

export type ModoFiltros = "nacional" | "internacional"

interface Props {
  modo: ModoFiltros
  /** Filtros sugeridos (primeiros passos, cargos-alvo): o painel abre com eles, e nada é gravado sem Salvar. */
  proposta?: Filtros | null
  onClose: () => void
  onTrocarModo: (modo: ModoFiltros) => void
  onSalvo: (config: Config) => void
}

const SEC = "space-y-2 pb-4 border-b border-slate-100 dark:border-slate-800 last:border-0"
const H = "font-bold text-sm text-slate-900 dark:text-white"
const DICA = "text-[11px] text-slate-500 dark:text-slate-400"
const CAMPO =
  "w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-60"
const ROTULO = "text-xs font-semibold text-slate-600 dark:text-slate-300 block mb-1"

function semAcento(s: string) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
}

function alternar(lista: string[], k: string): string[] {
  return lista.includes(k) ? lista.filter((x) => x !== k) : [...lista, k]
}

function Pilulas({
  mapa,
  marcados,
  onTrocar,
}: {
  mapa: Record<string, string>
  marcados: string[]
  onTrocar: (k: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {Object.entries(mapa).map(([k, rotulo]) => {
        const ativo = marcados.includes(k)
        return (
          <button
            key={k}
            type="button"
            aria-pressed={ativo}
            onClick={() => onTrocar(k)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition ${
              ativo
                ? "bg-indigo-100 text-indigo-700 border-indigo-300 dark:bg-indigo-950 dark:text-indigo-300 dark:border-indigo-800"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-700"
            }`}
          >
            {rotulo}
          </button>
        )
      })}
    </div>
  )
}

/** Lista de textos com remover e uma linha para acrescentar (com "frase exata" opcional). */
function Etiquetas({
  lista,
  onMudar,
  exemplo,
  rotulo,
  comExata,
}: {
  lista: string[]
  onMudar: (l: string[]) => void
  exemplo: string
  rotulo: string
  comExata?: boolean
}) {
  const [texto, setTexto] = useState("")
  const [exata, setExata] = useState(true)
  const acrescentar = () => {
    let t = texto.trim()
    if (!t) return
    if (comExata && exata) t = `"${t.replace(/"/g, "")}"`
    if (!lista.some((x) => semAcento(x) === semAcento(t))) onMudar([...lista, t])
    setTexto("")
  }
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {lista.length ? (
          lista.map((x, i) => (
            <span
              key={x + i}
              className="inline-flex items-center gap-1 pl-2.5 pr-1 py-0.5 rounded-full text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
            >
              {x}
              <button
                type="button"
                onClick={() => onMudar(lista.filter((_, j) => j !== i))}
                className="p-0.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700"
                aria-label={`Remover ${x}`}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))
        ) : (
          <span className={DICA}>Nenhum.</span>
        )}
      </div>
      <div className="flex gap-2 items-center flex-wrap">
        <input
          value={texto}
          maxLength={80}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault()
              acrescentar()
            }
          }}
          placeholder={exemplo}
          aria-label={rotulo}
          className={`${CAMPO} flex-1 min-w-[160px]`}
        />
        {comExata && (
          <label className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
            <input type="checkbox" checked={exata} onChange={(e) => setExata(e.target.checked)} /> frase exata
          </label>
        )}
        <button
          type="button"
          onClick={acrescentar}
          className="flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700"
        >
          <Plus className="w-3.5 h-3.5" /> Adicionar
        </button>
      </div>
    </div>
  )
}

function Marcar({
  checked,
  onChange,
  children,
}: {
  checked: boolean
  onChange: (v: boolean) => void
  children: React.ReactNode
}) {
  return (
    <label className="flex items-start gap-2 text-xs sm:text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
      <input type="checkbox" className="mt-0.5" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span>{children}</span>
    </label>
  )
}

function listaDeTexto(v: string, sep: RegExp) {
  return v
    .split(sep)
    .map((x) => x.trim())
    .filter(Boolean)
}

export default function SearchFiltersModal({ modo, proposta, onClose, onTrocarModo, onSalvo }: Props) {
  // PUT /api/config não é só do computador da ferramenta (dash/API.md §1): basta o servidor no ar
  const { servidor, tratarErro } = useFerramenta()
  const podeSalvar = servidor === "no_ar"
  const [op, setOp] = useState<Opcoes | null>(null)
  const [d, setD] = useState<Filtros | null>(null)
  const [existe, setExiste] = useState(true)
  const [erro, setErro] = useState("")
  const [salvando, setSalvando] = useState(false)
  const [buscaPais, setBuscaPais] = useState("")
  const [linkEmpresa, setLinkEmpresa] = useState("")
  const [erroEmpresa, setErroEmpresa] = useState("")
  // textos livres (listas separadas por vírgula ou linha) ficam como o usuário digita até salvar
  const [txtMudanca, setTxtMudanca] = useState("")
  const [txtAutorizacao, setTxtAutorizacao] = useState("")
  const [txtRestricao, setTxtRestricao] = useState("")
  const [txtPositivas, setTxtPositivas] = useState("")

  useEffect(() => {
    let ativo = true
    configApi
      .ler()
      .then((c) => {
        if (!ativo) return
        const f: Filtros = JSON.parse(JSON.stringify(proposta || c.filtros))
        f.empresas = f.empresas || (f.internacional as any).empresas || [] // servidor antigo: a lista vinha em internacional
        f.internacional.fontes = f.internacional.fontes || []
        setOp(c.opcoes)
        setD(f)
        setExiste(c.existe !== false)
        setTxtMudanca((f.internacional.paises_mudanca || []).join(", "))
        setTxtAutorizacao((f.internacional.autorizacao_trabalho || []).join(", "))
        setTxtRestricao((f.internacional.frases_restricao || []).join("\n"))
        setTxtPositivas((f.internacional.frases_positivas || []).join("\n"))
      })
      .catch((e) => setErro("Não foi possível ler os filtros: " + mensagemDeErro(e)))
    return () => {
      ativo = false
    }
  }, [proposta])

  const mudar = (fn: (f: Filtros) => void) =>
    setD((atual) => {
      if (!atual) return atual
      const novo: Filtros = JSON.parse(JSON.stringify(atual))
      fn(novo)
      return novo
    })
  const mudarInt = (fn: (it: Filtros["internacional"]) => void) => mudar((f) => fn(f.internacional))

  // a conta de consultas do dashboard antigo, com o aviso de risco de bloqueio
  const conta = useMemo(() => {
    if (!d) return null
    const n = configApi.contarConsultas(d)
    const nl = d.fontes.includes("linkedin") ? configApi.contarLinkedin(d) : 0
    const maior = Math.max(n, nl)
    const limitado = d.fontes.some((x) => x === "linkedin" || x === "indeed")
    const it = d.internacional
    const cargos = limitado && (d.termos.length > 5 || (it.ativo && it.termos.length > 5))
    const texto =
      `Esta busca fará ${n} ${n === 1 ? "consulta" : "consultas"} por portal` +
      (nl ? ` (no LinkedIn, ${nl})` : "") +
      (maior > 20 ? ": muitas consultas aumentam o risco de bloqueio" : "") +
      (cargos ? ". Mais de 5 cargos com LinkedIn ou Indeed ligados aumentam o risco de bloqueio desses portais." : "")
    return { texto, alerta: maior > 20 || cargos }
  }, [d])

  const salvar = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (!d) return
    const f: Filtros = JSON.parse(JSON.stringify(d))
    f.internacional.paises_mudanca = listaDeTexto(txtMudanca, /,/)
    f.internacional.autorizacao_trabalho = listaDeTexto(txtAutorizacao, /,/)
    f.internacional.frases_restricao = listaDeTexto(txtRestricao, /\n/)
    f.internacional.frases_positivas = listaDeTexto(txtPositivas, /\n/)
    setSalvando(true)
    setErro("")
    try {
      const c = await configApi.gravar(f)
      onSalvo(c)
    } catch (e) {
      tratarErro(e)
      setErro(mensagemDeErro(e, "Não deu para salvar os filtros."))
    } finally {
      setSalvando(false)
    }
  }

  const internacional = modo === "internacional"
  const loc = d?.localidade
  const ondeCidade = loc ? [loc.cidade, loc.estado].filter(Boolean).join(", ") : ""

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs" onClick={onClose}>
      <form
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-filtros"
        onSubmit={salvar}
        onKeyDown={(e) => {
          // Enter num campo não salva o painel (nas listas, ele acrescenta o item)
          if (e.key === "Enter" && (e.target as HTMLElement).tagName === "INPUT") e.preventDefault()
        }}
        className="relative w-full max-w-2xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              {internacional ? <Globe className="w-5 h-5" /> : <SlidersHorizontal className="w-5 h-5" />}
            </div>
            <div>
              <h3 id="titulo-filtros" className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                {internacional ? "Filtros da busca internacional" : "Filtros da busca"}
              </h3>
              <p className="text-xs text-slate-500">
                {internacional
                  ? "Vagas de empresas do exterior: opcional e desligado até você ligar. As vagas de fora aparecem na aba Internacional, com a etiqueta do país."
                  : "O que procurar nos portais. Vale a partir da próxima busca; vaga que furar estes filtros vai para Fora dos critérios, de onde você ainda pode seguir com ela."}
              </p>
            </div>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" aria-label="Fechar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 sm:p-6 overflow-y-auto flex-1 space-y-4 text-xs sm:text-sm">
          {!d && !erro && (
            <p className="flex items-center gap-2 text-slate-500">
              <Loader2 className="w-4 h-4 animate-spin" /> Carregando…
            </p>
          )}
          {proposta && d && (
            <p className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900 text-indigo-900 dark:text-indigo-200 text-xs">
              Estes são os filtros sugeridos. Confira e ajuste: nada é gravado até você clicar em Salvar filtros.
            </p>
          )}
          {!existe && d && !internacional && (
            <p className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-xs">
              Primeira vez: escolha os cargos e onde buscar. Os filtros ficam no arquivo config.json deste computador.
            </p>
          )}

          {d && op && !internacional && loc && (
            <>
              <section className={SEC}>
                <h4 className={H}>Cargos</h4>
                <p className={DICA}>
                  Cada cargo vira uma busca. Frase exata (entre aspas) traz só anúncios com aquela expressão, o que corta
                  muito ruído.
                </p>
                <Etiquetas
                  lista={d.termos}
                  onMudar={(l) => mudar((f) => (f.termos = l))}
                  exemplo="Ex.: analista de dados"
                  rotulo="Novo cargo"
                  comExata
                />
              </section>

              <section className={SEC}>
                <h4 className={H}>Portais</h4>
                <p className={DICA}>
                  Onde buscar. Marque pelo menos um. O LinkedIn também busca as vagas de fora quando a busca internacional
                  está ligada.
                </p>
                <div className="space-y-2">
                  {op.fontes_nac.map((x) => (
                    <Marcar
                      key={x.nome}
                      checked={d.fontes.includes(x.nome)}
                      onChange={() => mudar((f) => (f.fontes = alternar(f.fontes, x.nome)))}
                    >
                      <b>{x.rotulo}</b>
                      <span className={`block ${DICA}`}>
                        {[x.termos, x.precisa ? `Precisa ${x.precisa}.` : ""].filter(Boolean).join(" ")}
                      </span>
                    </Marcar>
                  ))}
                </div>
              </section>

              <section className={SEC}>
                <h4 className={H}>Localidade</h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <div>
                    <label htmlFor="fb-pais" className={ROTULO}>País</label>
                    <select
                      id="fb-pais"
                      value={loc.pais}
                      onChange={(e) =>
                        mudar((f) => {
                          f.localidade.pais = e.target.value
                          f.internacional.paises = f.internacional.paises.filter((p) => p !== e.target.value)
                        })
                      }
                      className={CAMPO}
                    >
                      {op.paises.map((p) => (
                        <option key={p}>{p}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor="fb-estado" className={ROTULO}>Estado</label>
                    <input id="fb-estado" maxLength={40} placeholder="SP" value={loc.estado} onChange={(e) => mudar((f) => (f.localidade.estado = e.target.value))} className={CAMPO} />
                  </div>
                  <div>
                    <label htmlFor="fb-cidade" className={ROTULO}>Cidade</label>
                    <input id="fb-cidade" maxLength={80} placeholder="Campinas" value={loc.cidade} onChange={(e) => mudar((f) => (f.localidade.cidade = e.target.value))} className={CAMPO} />
                  </div>
                  <div>
                    <label htmlFor="fb-raio" className={ROTULO}>Raio</label>
                    <select id="fb-raio" value={loc.raio_km} onChange={(e) => mudar((f) => (f.localidade.raio_km = Number(e.target.value)))} className={CAMPO}>
                      {op.raios_km.map((r) => (
                        <option key={r} value={r}>{r} km</option>
                      ))}
                    </select>
                  </div>
                </div>
                <p className={DICA}>
                  Cidade e raio valem para vagas híbridas e presenciais. O Indeed não busca por estado inteiro; o estado só
                  completa o nome da cidade. A Gupy busca só na cidade, sem raio.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Modo de trabalho</h4>
                <Marcar checked={d.modelos.remoto} onChange={(v) => mudar((f) => (f.modelos.remoto = v))}>
                  Remoto <span className={DICA}>(no {loc.pais})</span>
                </Marcar>
                <p className={DICA}>
                  Vagas de empresas do exterior ficam em{" "}
                  <button type="button" onClick={() => onTrocarModo("internacional")} className="underline font-semibold text-indigo-600 dark:text-indigo-400">
                    Filtros da busca internacional
                  </button>
                  .
                </p>
                {(["hibrido", "presencial"] as const).map((m) => (
                  <Marcar key={m} checked={d.modelos[m]} onChange={(v) => mudar((f) => (f.modelos[m] = v))}>
                    {m === "hibrido" ? "Híbrido" : "Presencial"}{" "}
                    <span className={DICA}>
                      {ondeCidade ? `em ${ondeCidade} (${loc.raio_km} km)` : "informe a cidade acima"}
                    </span>
                  </Marcar>
                ))}
              </section>

              <section className={SEC}>
                <h4 className={H}>Data de publicação</h4>
                <Pilulas
                  mapa={op.janelas}
                  marcados={[String(d.janela_horas)]}
                  onTrocar={(k) => mudar((f) => (f.janela_horas = Number(k)))}
                />
              </section>

              <section className={SEC}>
                <h4 className={H}>Tipo de emprego</h4>
                <Pilulas mapa={op.tipos_emprego} marcados={d.tipos_emprego} onTrocar={(k) => mudar((f) => (f.tipos_emprego = alternar(f.tipos_emprego, k)))} />
                <p className={DICA}>Nenhum marcado = todos. A IA confere o tipo lendo a descrição da vaga.</p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Senioridade</h4>
                <Pilulas mapa={op.senioridades} marcados={d.senioridades} onTrocar={(k) => mudar((f) => (f.senioridades = alternar(f.senioridades, k)))} />
                <p className={DICA}>
                  Nenhuma marcada = todas. Vale o nível do título ou o que a IA ler na descrição; vaga que não diz o nível
                  não é cortada.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Moedas aceitas (vagas fora do seu país)</h4>
                <Pilulas mapa={op.moedas} marcados={d.moedas_aceitas} onTrocar={(k) => mudar((f) => (f.moedas_aceitas = alternar(f.moedas_aceitas, k)))} />
                <p className={DICA}>
                  Nenhuma marcada = qualquer moeda. A moeda do seu país ({op.moeda_do_pais[loc.pais] || "—"}) sempre vale.
                  Vaga que não diz a moeda não é cortada.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Idiomas aceitos</h4>
                <Pilulas mapa={op.idiomas} marcados={d.idiomas_aceitos} onTrocar={(k) => mudar((f) => (f.idiomas_aceitos = alternar(f.idiomas_aceitos, k)))} />
                <p className={DICA}>
                  Nenhum marcado = todos. Vaga em outro idioma vai para Fora dos critérios; na dúvida (texto curto ou
                  misturado), a vaga não é cortada.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Empresas a excluir</h4>
                <Etiquetas
                  lista={d.empresas_excluir}
                  onMudar={(l) => mudar((f) => (f.empresas_excluir = l))}
                  exemplo="Nome da empresa"
                  rotulo="Empresa a excluir"
                />
              </section>

              <section className={SEC}>
                <h4 className={H}>Empresas que você acompanha</h4>
                <p className={DICA}>
                  Cole o link da página de vagas de empresas no Greenhouse, Lever ou Ashby (ex.: jobs.lever.co/empresa), ou
                  use "Acompanhar empresa" no detalhe de uma vaga. A busca traz as vagas delas abertas a quem mora no seu
                  país e, com a busca internacional ligada, as do exterior. Os títulos costumam vir em inglês: inclua o cargo
                  em inglês nos seus cargos.
                </p>
                <div className="flex gap-2">
                  <input
                    value={linkEmpresa}
                    maxLength={300}
                    onChange={(e) => setLinkEmpresa(e.target.value)}
                    placeholder="https://jobs.lever.co/empresa"
                    aria-label="Link da página de vagas da empresa"
                    className={`${CAMPO} flex-1`}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const e = configApi.empresaDoLink(linkEmpresa.trim())
                      if (!linkEmpresa.trim()) return
                      if (!e) {
                        setErroEmpresa("Esse link não é de uma página de vagas do Greenhouse, do Lever nem do Ashby.")
                        return
                      }
                      setErroEmpresa("")
                      mudar((f) => {
                        if (!f.empresas.some((x) => x.sistema === e.sistema && String(x.id).toLowerCase() === e.id.toLowerCase())) {
                          f.empresas.push(e)
                        }
                      })
                      setLinkEmpresa("")
                    }}
                    className="flex items-center gap-1 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
                  >
                    <Plus className="w-3.5 h-3.5" /> Adicionar
                  </button>
                </div>
                {erroEmpresa && <p className="text-[11px] text-rose-600 dark:text-rose-400">{erroEmpresa}</p>}
                <ul className="space-y-1">
                  {d.empresas.length ? (
                    d.empresas.map((e, i) => (
                      <li key={e.sistema + e.id} className="flex items-center justify-between gap-2 text-xs p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                        <span className="min-w-0 truncate">
                          {e.nome || e.id} <span className={DICA}>{e.sistema} · {e.url}</span>
                        </span>
                        <button
                          type="button"
                          onClick={() => mudar((f) => f.empresas.splice(i, 1))}
                          className="text-rose-600 hover:underline shrink-0"
                        >
                          Remover
                        </button>
                      </li>
                    ))
                  ) : (
                    <li className={DICA}>Nenhuma empresa.</li>
                  )}
                </ul>
              </section>
            </>
          )}

          {d && op && internacional && loc && (
            <>
              <section className={SEC}>
                <Marcar checked={d.internacional.ativo} onChange={(v) => mudarInt((it) => (it.ativo = v))}>
                  <b>Buscar também vagas no exterior</b>
                </Marcar>
                <p className={DICA}>
                  Remoto em cada país de interesse, mesmo que você não busque remoto no seu país. Cada país × cargo é uma
                  consulta a mais. Com fontes do exterior ou empresas, os países de interesse são opcionais.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Países de interesse</h4>
                <input value={buscaPais} onChange={(e) => setBuscaPais(e.target.value)} placeholder="Buscar país…" aria-label="Buscar país" className={CAMPO} />
                <div className="max-h-40 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 gap-1 p-2 rounded-xl border border-slate-200 dark:border-slate-800">
                  {op.paises
                    .filter((p) => p !== loc.pais && semAcento(p).includes(semAcento(buscaPais.trim())))
                    .map((p) => (
                      <Marcar key={p} checked={d.internacional.paises.includes(p)} onChange={() => mudarInt((it) => (it.paises = alternar(it.paises, p)))}>
                        {p}
                      </Marcar>
                    ))}
                </div>
                <p className={DICA}>
                  Marcados: {d.internacional.paises.length ? d.internacional.paises.join(", ") : "nenhum"}.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Cargos em inglês</h4>
                <p className={DICA}>Poucos e no idioma das vagas de lá (ex.: data analyst).</p>
                <Etiquetas
                  lista={d.internacional.termos}
                  onMudar={(l) => mudarInt((it) => (it.termos = l))}
                  exemplo="Ex.: data analyst"
                  rotulo="Novo cargo em inglês"
                  comExata
                />
              </section>

              <section className={SEC}>
                <h4 className={H}>Regiões aceitas</h4>
                <Pilulas mapa={op.regioes} marcados={d.internacional.regioes} onTrocar={(k) => mudarInt((it) => (it.regioes = alternar(it.regioes, k)))} />
                <p className={DICA}>Para vagas "remoto em tal região". Nenhuma marcada = sem restrição.</p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Moedas aceitas</h4>
                <Pilulas mapa={op.moedas} marcados={d.moedas_aceitas} onTrocar={(k) => mudar((f) => (f.moedas_aceitas = alternar(f.moedas_aceitas, k)))} />
                <p className={DICA}>Nenhuma marcada = qualquer moeda. Vaga que não diz a moeda não é cortada.</p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Salário e fuso</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div>
                    <label htmlFor="fbi-salario" className={ROTULO}>Salário mínimo por ano (US$)</label>
                    <input
                      id="fbi-salario"
                      type="number"
                      min={0}
                      step={1000}
                      placeholder="sem mínimo"
                      value={d.internacional.salario_min_anual_usd || ""}
                      onChange={(e) => mudarInt((it) => (it.salario_min_anual_usd = Math.max(0, Number(e.target.value) || 0)))}
                      className={CAMPO}
                    />
                  </div>
                  <div>
                    <label htmlFor="fbi-fuso" className={ROTULO}>Sobreposição de fuso com o Brasil</label>
                    <select id="fbi-fuso" value={d.internacional.fuso_horas} onChange={(e) => mudarInt((it) => (it.fuso_horas = Number(e.target.value)))} className={CAMPO}>
                      {Array.from({ length: 13 }, (_, i) => (
                        <option key={i} value={i}>{i ? `Pelo menos ${i} h` : "Não considerar"}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <p className={DICA}>O salário só corta vagas que informam o valor em dólar; não há conversão de câmbio.</p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Contratação aceita</h4>
                <Pilulas mapa={op.contratacao} marcados={d.internacional.contratacao} onTrocar={(k) => mudarInt((it) => (it.contratacao = alternar(it.contratacao, k)))} />
              </section>

              <section className={SEC}>
                <h4 className={H}>A sua situação</h4>
                <Marcar checked={d.internacional.aceita_mudar} onChange={(v) => mudarInt((it) => (it.aceita_mudar = v))}>
                  Aceito morar fora
                </Marcar>
                <input
                  value={txtMudanca}
                  onChange={(e) => setTxtMudanca(e.target.value)}
                  placeholder="Para quais países (separados por vírgula); vazio = os de interesse"
                  aria-label="Países para onde aceita se mudar"
                  className={CAMPO}
                />
                <Marcar checked={d.internacional.passaporte} onChange={(v) => mudarInt((it) => (it.passaporte = v))}>
                  Tenho passaporte válido
                </Marcar>
                <div>
                  <label htmlFor="fbi-autorizacao" className={ROTULO}>
                    Tenho visto ou autorização de trabalho em (países, separados por vírgula)
                  </label>
                  <input id="fbi-autorizacao" value={txtAutorizacao} onChange={(e) => setTxtAutorizacao(e.target.value)} placeholder="nenhum" className={CAMPO} />
                </div>
                <Marcar checked={d.internacional.precisa_sponsor} onChange={(v) => mudarInt((it) => (it.precisa_sponsor = v))}>
                  Preciso de patrocínio de visto (sponsor)
                </Marcar>
                <p className={DICA}>
                  Valem só para vagas internacionais: com "aceito morar fora", a busca inclui vagas presenciais e híbridas
                  nesses países. Vaga que exige autorização de trabalho num país onde você não tem (e não patrocina visto),
                  restrita a uma região fora das suas ou presencial sem você aceitar morar fora vai para Fora dos critérios,
                  com o motivo. Na dúvida, a vaga passa.
                </p>
              </section>

              <section className={SEC}>
                <h4 className={H}>Fontes do exterior</h4>
                <p className={DICA}>
                  Portais de vagas remotas, públicos e sem login. Desligados até você marcar; a busca consulta cada um uma vez
                  e filtra pelos cargos em inglês. A vaga sempre mostra a fonte e o link original.
                </p>
                <div className="space-y-2">
                  {op.fontes_int.map((x) => (
                    <Marcar key={x.nome} checked={d.internacional.fontes.includes(x.nome)} onChange={() => mudarInt((it) => (it.fontes = alternar(it.fontes, x.nome)))}>
                      <b>{x.rotulo}</b>
                      <span className={`block ${DICA}`}>{x.termos}</span>
                    </Marcar>
                  ))}
                </div>
              </section>

              <section className={SEC}>
                <h4 className={H}>Frases</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div>
                    <label htmlFor="fbi-restricao" className={ROTULO}>Frases que cortam a vaga (uma por linha)</label>
                    <textarea id="fbi-restricao" rows={3} value={txtRestricao} onChange={(e) => setTxtRestricao(e.target.value)} placeholder="Ex.: must be located in the US" className={CAMPO} />
                  </div>
                  <div>
                    <label htmlFor="fbi-positivas" className={ROTULO}>Frases que viram sinal positivo (uma por linha)</label>
                    <textarea id="fbi-positivas" rows={3} value={txtPositivas} onChange={(e) => setTxtPositivas(e.target.value)} placeholder="Ex.: open to Brazil" className={CAMPO} />
                  </div>
                </div>
                <p className={DICA}>
                  Além das frases que a ferramenta já reconhece ("US only", "we do not sponsor visas", "relocation
                  package"…). Sem diferença de maiúsculas e acentos.
                </p>
              </section>

              <p className={DICA}>
                Cargos, portais e localidade ficam em{" "}
                <button type="button" onClick={() => onTrocarModo("nacional")} className="underline font-semibold text-indigo-600 dark:text-indigo-400">
                  Filtros da busca
                </button>
                .
              </p>
            </>
          )}

          {erro && (
            <p role="alert" className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{erro}</span>
            </p>
          )}
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-800 space-y-2">
          {conta && (
            <p className={`text-[11px] ${conta.alerta ? "text-amber-700 dark:text-amber-300 font-semibold" : "text-slate-500"}`}>
              {conta.texto}
            </p>
          )}
          <div className="flex items-center justify-end gap-3 flex-wrap">
            {!podeSalvar && <AvisoSoLeitura />}
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!d || !podeSalvar || salvando}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition disabled:opacity-50"
            >
              {salvando && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>Salvar filtros</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
