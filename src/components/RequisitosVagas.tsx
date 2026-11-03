import React, { useCallback, useEffect, useMemo, useState } from "react"
import {
  Award,
  BookOpen,
  Briefcase,
  Clock,
  GraduationCap,
  Languages,
  ListChecks,
  Loader2,
  MapPin,
  Square,
  UserCheck,
} from "lucide-react"
import type { Vaga } from "../types/api"
import { mensagemDeErro } from "../services/api"
import * as api from "../services/api/requisitos"
import type { ItemPedido, LinhaSua, MarcaPerfil, ResumoRequisitos } from "../services/api/requisitos"
import { ScreenPreferencesService, type SelecaoRequisitos } from "../services/storage"
import type { WidgetDef } from "./painel/layout"

/**
 * O que as vagas pedem (spec 045), em dez widgets do painel (spec 046): a barra com o seletor e a leitura, e os nove
 * blocos. O resumo vem pronto do servidor; o estado fica num hook só, para o seletor valer para os nove onde quer que
 * eles estejam, e para mover um widget não recarregar o resumo nem parar a leitura.
 */

const VISIVEIS = 15
const VISIVEIS_SUAS = { habilidades: 10, certificacoes: 6 }

const OPCOES_VAGAS: { valor: SelecaoRequisitos["vagas"]; rotulo: string }[] = [
  { valor: "aplicacoes", rotulo: "Em Aplicações" },
  { valor: "todas", rotulo: "Todas as vagas analisadas" },
]
const OPCOES_AREA: { valor: SelecaoRequisitos["area"]; rotulo: string }[] = [
  { valor: "todas", rotulo: "As duas" },
  { valor: "nacional", rotulo: "Nacionais" },
  { valor: "internacional", rotulo: "Internacionais" },
]

const MARCA: Record<MarcaPerfil, { texto: string; classe: string }> = {
  habilidade: {
    texto: "✓ nas suas habilidades",
    classe: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
  },
  certificacao: {
    texto: "✓ nas suas certificações",
    classe: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800",
  },
  citada: {
    texto: "• citada no seu perfil",
    classe: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800",
  },
  nao: {
    texto: "não está no seu perfil",
    classe: "bg-slate-50 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700",
  },
}

const BOTAO = "px-2.5 py-1 rounded-lg font-medium transition"
const BOTAO_LIGADO =
  "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
const BOTAO_DESLIGADO = "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 hover:bg-slate-200"
/** Listas longas: uma coluna, ou duas no widget largo (768 px ou mais), pela largura do widget (spec 046). */
const LISTA_PEDIDA = "grid grid-cols-1 @3xl:grid-cols-2 gap-x-6 gap-y-2 items-start"
const LISTA_SUAS = "grid grid-cols-1 @3xl:grid-cols-2 gap-x-3 gap-y-1.5 items-start"

const porcento = (vagas: number, base: number) => (base > 0 ? Math.round((vagas / base) * 100) : 0)

function Rodape({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] text-slate-400 pt-1">{children}</p>
}

/** Estado e chamadas da seção: a seleção, o resumo, a leitura e o item aberto. */
export function useRequisitos({ vagas, versao }: { vagas: Vaga[]; versao?: number }) {
  const [selecao, setSelecao] = useState<SelecaoRequisitos>(() => ScreenPreferencesService.getSelecaoRequisitos())
  const [dados, setDados] = useState<ResumoRequisitos | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [pedindo, setPedindo] = useState(false)
  const [aberto, setAberto] = useState<string | null>(null)
  const [abaHab, setAbaHab] = useState<"tecnicas" | "comportamentais">("tecnicas")
  const [todas, setTodas] = useState<Record<string, boolean>>({})

  const porId = useMemo(() => new Map(vagas.map((v) => [v.id, v])), [vagas])

  const carregar = useCallback(async () => {
    try {
      setDados(await api.resumo(selecao))
      setErro(null)
    } catch (e) {
      setErro(mensagemDeErro(e, "Não deu para montar o resumo do que as vagas pedem."))
    }
  }, [selecao])

  useEffect(() => {
    void carregar()
  }, [carregar, versao])

  const rodando = Boolean(dados?.leitura.rodando)
  useEffect(() => {
    if (!rodando) return
    const t = setInterval(() => void carregar(), 3000)
    return () => clearInterval(t)
  }, [rodando, carregar])

  const mudarSelecao = (s: SelecaoRequisitos) => {
    setSelecao(s)
    setAberto(null)
    ScreenPreferencesService.saveSelecaoRequisitos(s)
  }

  const ler = async () => {
    setPedindo(true)
    try {
      await api.ler(selecao)
      await carregar()
    } catch (e) {
      setErro(mensagemDeErro(e, "Não deu para começar a leitura."))
    } finally {
      setPedindo(false)
    }
  }

  const parar = async () => {
    try {
      await api.parar()
      await carregar()
    } catch (e) {
      setErro(mensagemDeErro(e, "Não deu para parar a leitura."))
    }
  }

  const alternar = (chave: string) => setAberto((a) => (a === chave ? null : chave))

  return {
    selecao,
    dados,
    erro,
    pedindo,
    aberto,
    abaHab,
    setAbaHab,
    todas,
    setTodas,
    porId,
    rodando,
    mudarSelecao,
    ler,
    parar,
    alternar,
  }
}

export type EstadoRequisitos = ReturnType<typeof useRequisitos>

interface Acoes {
  onSelectVaga?: (v: Vaga) => void
  onAbrirIA?: () => void
  onAbrirPerfil?: () => void
}

/** Os dez widgets da seção, na ordem do layout padrão (data-model §1 da spec 046). */
export function widgetsRequisitos(r: EstadoRequisitos, { onSelectVaga, onAbrirIA, onAbrirPerfil }: Acoes): WidgetDef[] {
  const { selecao, dados, erro, pedindo, aberto, abaHab, setAbaHab, todas, setTodas, porId, rodando, alternar } = r

  /** As vagas que formam um número (FR-019): os ids do resumo casados com as vagas carregadas. */
  const listaDeVagas = (chave: string, rotulo: string, ids: string[]) => {
    if (aberto !== chave) return null
    const lista = ids.map((id) => porId.get(id)).filter((v): v is Vaga => Boolean(v))
    return (
      <div className="mt-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-2">
        <p className="text-[11px] font-semibold text-slate-500 px-1 pb-1">
          Vagas que pedem {rotulo} ({ids.length})
        </p>
        <ul className="space-y-0.5">
          {lista.map((v) => (
            <li key={v.id}>
              <button
                type="button"
                onClick={() => onSelectVaga?.(v)}
                className="w-full text-left text-xs px-2 py-1 rounded-lg hover:bg-white dark:hover:bg-slate-900 text-slate-700 dark:text-slate-300 break-words"
              >
                <span className="font-semibold">{v.titulo}</span>
                {v.empresa ? <span className="text-slate-500"> · {v.empresa}</span> : null}
              </button>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  /** Uma linha com barra: nome (botão que abre as vagas), contagem e, nas listas do que é pedido, a marca do perfil. */
  const linha = (
    chave: string,
    nome: string,
    vagasItem: number,
    base: number,
    ids: string[],
    extra?: { exigida?: number; perfil?: MarcaPerfil; tipo?: string; destaque?: boolean; filhos?: React.ReactNode },
  ) => {
    const pct = porcento(vagasItem, base)
    return (
      <li key={chave} className="space-y-1 min-w-0">
        <button
          type="button"
          aria-expanded={aberto === chave}
          onClick={() => alternar(chave)}
          title={`${vagasItem} de ${base} vagas (${pct}%)`}
          className="w-full text-left space-y-1 rounded-lg -mx-1 px-1 py-0.5 hover:bg-slate-50 dark:hover:bg-slate-800/60"
        >
          <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1 text-xs">
            <span className="flex flex-wrap items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-200 break-words min-w-0">
              <span className="break-words">{nome}</span>
              {extra?.tipo ? (
                <span className="px-1.5 py-0.5 rounded-md text-[10px] font-semibold bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                  {extra.tipo}
                </span>
              ) : null}
              {extra?.destaque ? (
                <span className="px-1.5 py-0.5 rounded-md text-[10px] font-semibold bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                  a mais pedida
                </span>
              ) : null}
              {extra?.perfil ? (
                <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-semibold border ${MARCA[extra.perfil].classe}`}>
                  {MARCA[extra.perfil].texto}
                </span>
              ) : null}
            </span>
            <span className="text-slate-500 dark:text-slate-400 whitespace-nowrap">
              {vagasItem} de {base} vagas ({pct}%)
              {extra?.exigida ? ` · exigida em ${extra.exigida}` : ""}
            </span>
          </div>
          <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
            <div className="h-full bg-indigo-600 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
        </button>
        {extra?.filhos}
        {listaDeVagas(chave, nome, ids)}
      </li>
    )
  }

  const listaPedida = (grupo: string, itens: ItemPedido[], base: number, comTipo = false) => {
    const tudo = todas[grupo]
    const mostrar = tudo ? itens : itens.slice(0, VISIVEIS)
    if (itens.length === 0) return <p className="text-xs text-slate-400">Nenhum item nestas vagas.</p>
    return (
      <>
        <ul className={LISTA_PEDIDA}>
          {mostrar.map((i) =>
            linha(`${grupo}:${i.chave}`, i.nome, i.vagas, base, i.ids, {
              exigida: i.exigida,
              perfil: i.perfil,
              tipo: comTipo ? (i.tipo === "certificacao" ? "Certificação" : "Curso") : undefined,
            }),
          )}
        </ul>
        {itens.length > VISIVEIS ? (
          <button
            type="button"
            onClick={() => setTodas((t) => ({ ...t, [grupo]: !tudo }))}
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            {tudo ? "Ver menos" : `Ver todas (${itens.length})`}
          </button>
        ) : null}
      </>
    )
  }

  const suasLinhas = (grupo: string, linhas: LinhaSua[], limite: number) => (
    <>
      <ul className={LISTA_SUAS}>
        {(todas[grupo] ? linhas : linhas.slice(0, limite)).map((i, n) => {
          const chave = `${grupo}:${n}:${i.linha}`
          return (
            <li key={chave} className="min-w-0">
              <button
                type="button"
                aria-expanded={aberto === chave}
                onClick={() => (i.vagas ? alternar(chave) : undefined)}
                disabled={!i.vagas}
                className={`w-full text-left flex flex-wrap items-center justify-between gap-x-2 gap-y-0.5 rounded-xl border px-3 py-2 text-xs ${
                  i.destaque
                    ? "border-indigo-300 bg-indigo-50 dark:border-indigo-700 dark:bg-indigo-950/40"
                    : "border-slate-200 dark:border-slate-700"
                } ${i.vagas ? "hover:bg-slate-50 dark:hover:bg-slate-800/60" : "opacity-60"}`}
              >
                <span className="min-w-0 break-words">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{i.linha}</span>
                  {i.nivel ? <span className="text-slate-500 dark:text-slate-400"> · {i.nivel}</span> : null}
                </span>
                <span
                  className={
                    i.vagas
                      ? "font-semibold text-indigo-700 dark:text-indigo-300 whitespace-nowrap"
                      : "text-slate-400 whitespace-nowrap"
                  }
                >
                  {i.vagas ? `${i.vagas} ${i.vagas === 1 ? "vaga" : "vagas"}` : "nenhuma vaga desta seleção"}
                </span>
              </button>
              {listaDeVagas(chave, i.linha, i.ids)}
            </li>
          )
        })}
      </ul>
      {linhas.length > limite ? (
        <button
          type="button"
          onClick={() => setTodas((x) => ({ ...x, [grupo]: !x[grupo] }))}
          className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
        >
          {todas[grupo] ? "Ver menos" : `Ver todas (${linhas.length})`}
        </button>
      ) : null}
    </>
  )

  const c = dados?.contagem
  const leitura = dados?.leitura
  const extras = c
    ? [
        c.a_ler ? `${c.a_ler} a ler` : "",
        c.sem_texto ? `${c.sem_texto} sem o texto do anúncio` : "",
        c.sem_analise ? `${c.sem_analise} esperando análise` : "",
      ].filter(Boolean)
    : []
  const temRequisitos = Boolean(c && c.com_requisitos > 0)

  const botaoLer =
    c && c.a_ler > 0 && !rodando ? (
      <div className="space-y-1">
        <button
          type="button"
          onClick={() => void r.ler()}
          disabled={!dados?.ia.ligada || pedindo}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {pedindo ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ListChecks className="w-3.5 h-3.5" />}
          Ler os requisitos {c.a_ler === 1 ? "da vaga" : `das ${c.a_ler} vagas`} desta seleção
        </button>
        {dados?.ia.ligada ? (
          <p className="text-[11px] text-slate-400">com {dados.ia.nome}; a nota das vagas não muda</p>
        ) : (
          <p className="text-[11px] text-slate-500">
            Escolha uma IA no{" "}
            <button type="button" onClick={onAbrirIA} className="font-semibold text-indigo-600 dark:text-indigo-400 hover:underline">
              botão IA
            </button>{" "}
            ou peça no chat: ler os requisitos das vagas.
          </p>
        )}
      </div>
    ) : null

  const barra = (
    <>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Vagas">
          <span className="font-semibold text-slate-500">Vagas:</span>
          {OPCOES_VAGAS.map((o) => (
            <button
              key={o.valor}
              type="button"
              aria-pressed={selecao.vagas === o.valor}
              onClick={() => r.mudarSelecao({ ...selecao, vagas: o.valor })}
              className={`${BOTAO} ${selecao.vagas === o.valor ? BOTAO_LIGADO : BOTAO_DESLIGADO}`}
            >
              {o.rotulo}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Área">
          <span className="font-semibold text-slate-500">Área:</span>
          {OPCOES_AREA.map((o) => (
            <button
              key={o.valor}
              type="button"
              aria-pressed={selecao.area === o.valor}
              onClick={() => r.mudarSelecao({ ...selecao, area: o.valor })}
              className={`${BOTAO} ${selecao.area === o.valor ? BOTAO_LIGADO : BOTAO_DESLIGADO}`}
            >
              {o.rotulo}
            </button>
          ))}
        </div>
      </div>

      {c ? (
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Contando {c.com_requisitos} {c.com_requisitos === 1 ? "vaga" : "vagas"} com requisitos lidos, de {c.selecao}{" "}
          nesta seleção
          {extras.length ? ` · ${extras.join(" · ")}` : ""}
        </p>
      ) : null}

      {rodando && leitura ? (
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[12rem] space-y-1">
            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Lendo {leitura.lidas} de {leitura.total} vagas…
            </p>
            <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                style={{ width: `${porcento(leitura.lidas, leitura.total)}%` }}
              />
            </div>
          </div>
          <button
            type="button"
            onClick={() => void r.parar()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            <Square className="w-3 h-3" />
            Parar
          </button>
        </div>
      ) : null}

      {!rodando && leitura?.erro ? (
        <p className="text-xs text-rose-700 dark:text-rose-300">
          A leitura parou: {leitura.erro.motivo}. O que foi lido ficou gravado; clique de novo para continuar.
        </p>
      ) : null}
      {!rodando && leitura?.parada && !leitura.erro && c && c.a_ler > 0 ? (
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Leitura parada: {leitura.lidas} de {leitura.total} vagas lidas. Clique de novo para continuar.
        </p>
      ) : null}

      {botaoLer}

      {dados?.poucas && c ? (
        <p className="text-xs text-amber-700 dark:text-amber-300">Poucas vagas para tirar conclusão ({c.com_requisitos}).</p>
      ) : null}
      {erro ? <p className="text-xs text-rose-700 dark:text-rose-300">{erro}</p> : null}
    </>
  )

  // Os nove blocos aparecem sempre, para o layout da pessoa não pular (spec 046).
  const semResumo = erro ? (
    <p className="text-xs text-slate-400">O resumo não carregou; veja o aviso em O que as vagas pedem.</p>
  ) : (
    <p className="text-xs text-slate-400 flex items-center gap-1.5">
      <Loader2 className="w-3.5 h-3.5 animate-spin" />
      Montando o resumo…
    </p>
  )
  const semRequisitos = <p className="text-xs text-slate-500">Ainda não há requisitos lidos nestas vagas.</p>
  /** Corpo dos blocos que dependem de requisitos lidos. */
  const comRequisitos = (corpo: (d: ResumoRequisitos) => React.ReactNode) =>
    !dados ? semResumo : !temRequisitos ? semRequisitos : corpo(dados)
  /** Corpo dos blocos que aparecem com o resumo, com ou sem requisitos lidos. */
  const comResumo = (corpo: (d: ResumoRequisitos) => React.ReactNode) => (!dados ? semResumo : corpo(dados))

  const icone = (I: typeof ListChecks, cor = "text-indigo-500") => <I className={`w-4 h-4 shrink-0 ${cor}`} />

  return [
    {
      id: "requisitos",
      titulo: "O que as vagas pedem",
      tipo: "secao",
      subtitulo: "Habilidades, certificações, experiência e outros requisitos das vagas escolhidas neste seletor.",
      corpo: barra,
    },
    {
      id: "habilidades",
      titulo: "Habilidades mais pedidas",
      tipo: "bloco",
      icone: icone(ListChecks),
      corpo: comRequisitos((d) => (
        <>
          <div className="flex flex-wrap gap-1.5 text-xs" role="group" aria-label="Tipo de habilidade">
            {(
              [
                ["tecnicas", "Técnicas e ferramentas"],
                ["comportamentais", "Comportamentais"],
              ] as const
            ).map(([k, rotulo]) => (
              <button
                key={k}
                type="button"
                aria-pressed={abaHab === k}
                onClick={() => setAbaHab(k)}
                className={`${BOTAO} ${abaHab === k ? BOTAO_LIGADO : BOTAO_DESLIGADO}`}
              >
                {rotulo} ({d.habilidades[k].length})
              </button>
            ))}
          </div>
          {listaPedida(`hab-${abaHab}`, d.habilidades[abaHab], d.habilidades.base)}
          <Rodape>em {d.habilidades.base} vagas com requisitos lidos</Rodape>
        </>
      )),
    },
    {
      id: "suas-habilidades",
      titulo: "Suas habilidades",
      tipo: "bloco",
      icone: icone(UserCheck, "text-emerald-500"),
      corpo: comResumo((d) =>
        !d.suas.tem_secao ? (
          <div className="space-y-2">
            <p className="text-xs text-slate-500">
              {d.suas.existe_perfil
                ? "Seu perfil não tem a seção Habilidades e ferramentas. Abra Meu perfil para montar."
                : "Você ainda não tem um perfil. Abra Meu perfil para montar."}
            </p>
            <button
              type="button"
              onClick={onAbrirPerfil}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Meu perfil
            </button>
          </div>
        ) : (
          <>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              {temRequisitos
                ? `${d.suas.aparecem} das suas ${d.suas.total} habilidades aparecem nestas vagas`
                : "Leia os requisitos para ver quantas vagas pedem cada uma."}
            </p>
            {suasLinhas("sua-hab", d.suas.habilidades, VISIVEIS_SUAS.habilidades)}
            {d.suas.certificacoes.length ? (
              <>
                <p className="text-xs font-semibold text-slate-500 pt-2">Suas certificações</p>
                {suasLinhas("sua-cert", d.suas.certificacoes, VISIVEIS_SUAS.certificacoes)}
              </>
            ) : null}
          </>
        ),
      ),
    },
    {
      id: "certificacoes",
      titulo: "Certificações e cursos",
      tipo: "bloco",
      icone: icone(Award),
      corpo: comRequisitos((d) => (
        <>
          {listaPedida("cert", d.certificacoes.itens, d.certificacoes.base, true)}
          <Rodape>em {d.certificacoes.base} vagas com requisitos lidos</Rodape>
        </>
      )),
    },
    {
      id: "experiencia",
      titulo: "Tempo de experiência",
      tipo: "bloco",
      icone: icone(Clock),
      corpo: comRequisitos((d) => (
        <>
          <ul className="space-y-2">
            {d.experiencia.faixas.map((f) =>
              linha(`exp:${f.faixa}`, f.rotulo, f.vagas, d.experiencia.base, f.ids, {
                destaque: f.faixa === d.experiencia.destaque,
              }),
            )}
          </ul>
          <Rodape>em {d.experiencia.base} vagas com requisitos lidos · o mínimo de anos que cada uma pede</Rodape>
        </>
      )),
    },
    {
      id: "formacao",
      titulo: "Formação",
      tipo: "bloco",
      icone: icone(GraduationCap),
      corpo: comRequisitos((d) => (
        <>
          <ul className="space-y-2">
            {d.formacao.niveis.map((n) => linha(`form:${n.nivel}`, n.rotulo, n.vagas, d.formacao.base, n.ids))}
          </ul>
          {d.formacao.areas.length ? (
            <div className="space-y-1.5 pt-1">
              <p className="text-xs font-semibold text-slate-500">Áreas mais citadas</p>
              <div className="flex flex-wrap gap-1.5">
                {d.formacao.areas.slice(0, 12).map((a) => (
                  <button
                    key={a.nome}
                    type="button"
                    aria-expanded={aberto === `area:${a.nome}`}
                    onClick={() => alternar(`area:${a.nome}`)}
                    className="px-2 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 break-words"
                  >
                    {a.nome} · {a.vagas}
                  </button>
                ))}
              </div>
              {d.formacao.areas.map((a) => (
                <React.Fragment key={a.nome}>{listaDeVagas(`area:${a.nome}`, a.nome, a.ids)}</React.Fragment>
              ))}
            </div>
          ) : null}
          <Rodape>em {d.formacao.base} vagas com requisitos lidos · o mínimo que cada uma pede</Rodape>
        </>
      )),
    },
    {
      id: "idiomas",
      titulo: "Idiomas",
      tipo: "bloco",
      icone: icone(Languages),
      corpo: comResumo((d) => (
        <>
          {d.idiomas.itens.length ? (
            <ul className="space-y-2">
              {d.idiomas.itens.map((i) =>
                linha(`idi:${i.idioma}`, i.idioma, i.vagas, d.idiomas.base, i.ids, {
                  filhos: (
                    <>
                      <div className="flex flex-wrap gap-1.5 pl-1">
                        {i.niveis.map((n) => (
                          <button
                            key={n.nivel}
                            type="button"
                            aria-expanded={aberto === `idi:${i.idioma}:${n.nivel}`}
                            onClick={() => alternar(`idi:${i.idioma}:${n.nivel}`)}
                            className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                          >
                            {n.rotulo} {n.vagas}
                          </button>
                        ))}
                      </div>
                      {i.niveis.map((n) => (
                        <React.Fragment key={n.nivel}>
                          {listaDeVagas(`idi:${i.idioma}:${n.nivel}`, `${i.idioma} ${n.rotulo.toLowerCase()}`, n.ids)}
                        </React.Fragment>
                      ))}
                    </>
                  ),
                }),
              )}
            </ul>
          ) : (
            <p className="text-xs text-slate-400">Nenhum idioma pedido nestas vagas.</p>
          )}
          <Rodape>em {d.idiomas.base} vagas</Rodape>
        </>
      )),
    },
    // Senioridade e modelo em blocos separados: "Remoto" não é senioridade (pedido no teste da spec 045)
    {
      id: "senioridade",
      titulo: "Senioridade",
      tipo: "bloco",
      icone: icone(Briefcase),
      corpo: comResumo((d) => (
        <>
          {d.senioridade.itens.length ? (
            <ul className="space-y-2">
              {d.senioridade.itens.map((i) => linha(`sen:${i.valor}`, i.rotulo, i.vagas, d.senioridade.base, i.ids))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400">Nenhuma vaga desta seleção diz a senioridade.</p>
          )}
          <Rodape>em {d.senioridade.base} vagas analisadas</Rodape>
        </>
      )),
    },
    {
      id: "modelo",
      titulo: "Modelo de trabalho",
      tipo: "bloco",
      icone: icone(MapPin),
      corpo: comResumo((d) => (
        <>
          {d.modelo.itens.length ? (
            <ul className="space-y-2">
              {d.modelo.itens.map((i) => linha(`mod:${i.valor}`, i.rotulo, i.vagas, d.modelo.base, i.ids))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400">Nenhuma vaga desta seleção diz o modelo de trabalho.</p>
          )}
          <Rodape>em {d.modelo.base} vagas analisadas</Rodape>
        </>
      )),
    },
    {
      id: "contratacao",
      titulo: "Tipo de contratação",
      tipo: "bloco",
      icone: icone(BookOpen),
      corpo: comResumo((d) => (
        <>
          {d.contratacao.itens.length ? (
            <ul className="space-y-2">
              {d.contratacao.itens.map((i) => linha(`con:${i.valor}`, i.rotulo, i.vagas, d.contratacao.base, i.ids))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400">Nenhuma vaga desta seleção diz o tipo de contratação.</p>
          )}
          <Rodape>em {d.contratacao.base} vagas analisadas</Rodape>
        </>
      )),
    },
  ]
}
