import React, { useState } from "react"
import {
  X,
  SlidersHorizontal,
  Plus,
  Trash2,
  Save,
  Globe2,
  Building,
  MapPin,
  Clock,
  DollarSign,
  CheckCircle2,
} from "lucide-react"
import { FiltrosBusca, Senioridade } from "../../types/job"
interface SearchFiltersModalProps {
  isOpen: boolean
  onClose: () => void
  filtros: FiltrosBusca
  onSaveFiltros: (filtros: FiltrosBusca) => void
}

export default function SearchFiltersModal({
  isOpen,
  onClose,
  filtros,
  onSaveFiltros,
}: SearchFiltersModalProps) {
  if (!isOpen) return null

  const [config, setConfig] = useState<FiltrosBusca>({ ...filtros })
  const [novoTermo, setNovoTermo] = useState("")
  const [novaEmpresaExcluir, setNovaEmpresaExcluir] = useState("")
  const [salvoSucesso, setSalvoSucesso] = useState(false)

  const handleAddTermo = () => {
    if (!novoTermo.trim()) return
    let t = novoTermo.trim()
    // Se não tiver aspas, sugere ou adiciona
    if (!t.startsWith('"') && !t.endsWith('"')) {
      t = `"${t}"`
    }
    setConfig({
      ...config,
      termos: [...config.termos, t],
    })
    setNovoTermo("")
  }

  const handleRemoveTermo = (index: number) => {
    const updated = config.termos.filter((_, i) => i !== index)
    setConfig({ ...config, termos: updated })
  }

  const handleAddEmpresaExcluir = () => {
    if (!novaEmpresaExcluir.trim()) return
    setConfig({
      ...config,
      empresas_excluir: [...config.empresas_excluir, novaEmpresaExcluir.trim()],
    })
    setNovaEmpresaExcluir("")
  }

  const handleRemoveEmpresaExcluir = (index: number) => {
    const updated = config.empresas_excluir.filter((_, i) => i !== index)
    setConfig({ ...config, empresas_excluir: updated })
  }

  const handleToggleFonte = (fonte: string) => {
    const existe = config.fontes.includes(fonte)
    const updated = existe
      ? config.fontes.filter((f) => f !== fonte)
      : [...config.fontes, fonte]
    setConfig({ ...config, fontes: updated })
  }

  const handleToggleSenioridade = (sen: Senioridade) => {
    const existe = config.senioridades.includes(sen)
    const updated = existe
      ? config.senioridades.filter((s) => s !== sen)
      : [...config.senioridades, sen]
    setConfig({ ...config, senioridades: updated })
  }

  const handleSave = () => {
    onSaveFiltros(config)
    setSalvoSucesso(true)
    setTimeout(() => {
      setSalvoSucesso(false)
      onClose()
    }, 600)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-3xl bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400">
              <SlidersHorizontal className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Filtros e Configurações de Busca
              </h3>
              <p className="text-xs text-slate-500">
                Defina quais cargos, portais e critérios alimentam o seu funil
                de vagas
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {/* 1. Cargos e Termos de Busca */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Cargos e Termos de Busca
              </h4>
              <span className="text-xs text-slate-400">
                Dica: termos entre aspas (ex.: "frontend engineer") trazem menos
                ruído
              </span>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={novoTermo}
                onChange={(e) => setNovoTermo(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && (e.preventDefault(), handleAddTermo())
                }
                placeholder="Novo cargo (ex.: &quot;fullstack typescript&quot;)"
                className="flex-1 px-3.5 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
              <button
                type="button"
                onClick={handleAddTermo}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 transition shadow-xs"
              >
                Adicionar
              </button>
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              {config.termos.map((termo, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                >
                  <span>{termo}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveTermo(idx)}
                    className="hover:text-rose-600 ml-1"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* 2. Portais Ativos */}
          <div className="space-y-3">
            <h4 className="font-bold text-sm text-slate-900 dark:text-white">
              Portais e Fontes Conectadas
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {[
                { id: "gupy", label: "Gupy (MCP/API)" },
                { id: "indeed", label: "Indeed Brasil" },
                { id: "linkedin", label: "LinkedIn Jobs" },
                { id: "greenhouse", label: "Greenhouse ATS" },
                { id: "lever", label: "Lever ATS" },
                { id: "ashby", label: "Ashby ATS" },
                { id: "remoteok", label: "RemoteOK (Global)" },
                { id: "nerdin", label: "Nerdin Tech" },
              ].map((fonte) => {
                const isChecked = config.fontes.includes(fonte.id)
                return (
                  <label
                    key={fonte.id}
                    className={`flex items-center gap-2 p-3 rounded-xl border text-xs font-semibold cursor-pointer transition ${
                      isChecked
                        ? "bg-indigo-50/70 border-indigo-300 text-indigo-900 dark:bg-indigo-950/40 dark:border-indigo-800 dark:text-indigo-200"
                        : "bg-slate-50 border-slate-200 text-slate-600 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleFonte(fonte.id)}
                      className="rounded accent-indigo-600"
                    />
                    <span>{fonte.label}</span>
                  </label>
                )
              })}
            </div>
          </div>

          {/* 3. Localidade & Modelos */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Localidade Principal
              </h4>
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <input
                    type="text"
                    value={config.localidade.cidade}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        localidade: {
                          ...config.localidade,
                          cidade: e.target.value,
                        },
                      })
                    }
                    placeholder="Cidade"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <input
                    type="text"
                    value={config.localidade.estado}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        localidade: {
                          ...config.localidade,
                          estado: e.target.value,
                        },
                      })
                    }
                    placeholder="UF (ex.: SP)"
                    className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-bold text-sm text-slate-900 dark:text-white">
                Modos de Trabalho Permitidos
              </h4>
              <div className="flex gap-2">
                <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={config.modelos.remoto}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        modelos: {
                          ...config.modelos,
                          remoto: e.target.checked,
                        },
                      })
                    }
                    className="rounded accent-indigo-600"
                  />
                  <span>Remoto</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={config.modelos.hibrido}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        modelos: {
                          ...config.modelos,
                          hibrido: e.target.checked,
                        },
                      })
                    }
                    className="rounded accent-indigo-600"
                  />
                  <span>Híbrido</span>
                </label>
                <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={config.modelos.presencial}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        modelos: {
                          ...config.modelos,
                          presencial: e.target.checked,
                        },
                      })
                    }
                    className="rounded accent-indigo-600"
                  />
                  <span>Presencial</span>
                </label>
              </div>
            </div>
          </div>

          {/* 4. Janela de Publicação & Senioridade */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <h4 className="font-bold text-sm text-slate-900 dark:text-white mb-2">
                Janela de Publicação
              </h4>
              <select
                value={config.janela_horas}
                onChange={(e) =>
                  setConfig({ ...config, janela_horas: Number(e.target.value) })
                }
                className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              >
                <option value={24}>Últimas 24 horas</option>
                <option value={72}>Últimos 3 dias (72h)</option>
                <option value={168}>Últimos 7 dias (1 semana)</option>
                <option value={336}>Últimos 14 dias (2 semanas)</option>
                <option value={720}>Últimos 30 dias</option>
              </select>
            </div>

            <div>
              <h4 className="font-bold text-sm text-slate-900 dark:text-white mb-2">
                Senioridade Aceita
              </h4>
              <div className="flex gap-1.5 flex-wrap">
                {([
                  "junior",
                  "pleno",
                  "senior",
                  "especialista",
                ] as Senioridade[]).map((sen) => (
                  <button
                    key={sen}
                    type="button"
                    onClick={() => handleToggleSenioridade(sen)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                      config.senioridades.includes(sen)
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {sen === "junior"
                      ? "Jr"
                      : sen === "pleno"
                        ? "Pl"
                        : sen === "senior"
                          ? "Sr"
                          : "Lead"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 5. Empresas a Excluir */}
          <div className="space-y-3">
            <h4 className="font-bold text-sm text-slate-900 dark:text-white">
              Empresas Desconsideradas (Blacklist)
            </h4>
            <div className="flex gap-2">
              <input
                type="text"
                value={novaEmpresaExcluir}
                onChange={(e) => setNovaEmpresaExcluir(e.target.value)}
                placeholder="Nome da empresa a desconsiderar..."
                className="flex-1 px-3.5 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
              <button
                type="button"
                onClick={handleAddEmpresaExcluir}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800"
              >
                Bloquear
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {config.empresas_excluir.map((emp, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-semibold bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900"
                >
                  <span>{emp}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveEmpresaExcluir(idx)}
                    className="hover:text-rose-900"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-3 bg-slate-50/50 dark:bg-slate-800/40">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
          >
            <Save className="w-4 h-4" />
            <span>{salvoSucesso ? "Filtros Salvos!" : "Salvar Filtros"}</span>
          </button>
        </div>
      </div>
    </div>
  )
}
