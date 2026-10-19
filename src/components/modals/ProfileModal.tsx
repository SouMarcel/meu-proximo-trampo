import React, { useState } from "react"
import {
  X,
  User,
  Save,
  Plus,
  Download,
  Upload,
  RotateCcw,
  CheckCircle2,
  Briefcase,
  Globe,
  Linkedin,
  Github,
} from "lucide-react"
import { PerfilUsuario } from "../../types/job"
import { JobStorageService } from "../../services/storage"

interface ProfileModalProps {
  isOpen: boolean
  onClose: () => void
  perfil: PerfilUsuario
  onSavePerfil: (perfil: PerfilUsuario) => void
  onReloadAllData: () => void
}

export default function ProfileModal({
  isOpen,
  onClose,
  perfil,
  onSavePerfil,
  onReloadAllData,
}: ProfileModalProps) {
  if (!isOpen) return null

  const [data, setData] = useState<PerfilUsuario>({ ...perfil })
  const [novaSkill, setNovaSkill] = useState("")
  const [novoCargoAlvo, setNovoCargoAlvo] = useState("")
  const [salvoSucesso, setSalvoSucesso] = useState(false)
  const [jsonImportString, setJsonImportString] = useState("")
  const [showImportBox, setShowImportBox] = useState(false)

  const handleAddSkill = () => {
    if (!novaSkill.trim()) return
    if (!data.competencias_chave.includes(novaSkill.trim())) {
      setData({
        ...data,
        competencias_chave: [...data.competencias_chave, novaSkill.trim()],
      })
    }
    setNovaSkill("")
  }

  const handleRemoveSkill = (skill: string) => {
    setData({
      ...data,
      competencias_chave: data.competencias_chave.filter((s) => s !== skill),
    })
  }

  const handleAddCargoAlvo = () => {
    if (!novoCargoAlvo.trim()) return
    if (!data.cargos_alvo.includes(novoCargoAlvo.trim())) {
      setData({
        ...data,
        cargos_alvo: [...data.cargos_alvo, novoCargoAlvo.trim()],
      })
    }
    setNovoCargoAlvo("")
  }

  const handleRemoveCargoAlvo = (cargo: string) => {
    setData({
      ...data,
      cargos_alvo: data.cargos_alvo.filter((c) => c !== cargo),
    })
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    onSavePerfil(data)
    setSalvoSucesso(true)
    setTimeout(() => {
      setSalvoSucesso(false)
      onClose()
    }, 600)
  }

  const handleExportJson = () => {
    const exported = JobStorageService.exportData()
    const blob = new Blob([exported], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `meu-proximo-trampo-backup-${new Date().toISOString().split("T")[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleImportJson = () => {
    if (!jsonImportString.trim()) return
    const ok = JobStorageService.importData(jsonImportString)
    if (ok) {
      alert("Dados importados com sucesso!")
      onReloadAllData()
      onClose()
    } else {
      alert("Erro ao importar JSON. Verifique o formato do arquivo.")
    }
  }

  const handleResetDefaults = () => {
    if (
      confirm(
        "Deseja restaurar as vagas e configurações de demonstração iniciais?",
      )
    ) {
      JobStorageService.resetToDefaults()
      onReloadAllData()
      onClose()
    }
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
              <User className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Meu Perfil Profissional
              </h3>
              <p className="text-xs text-slate-500">
                Estas informações calibram as notas de aderência calculadas pela
                inteligência artificial
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form
          onSubmit={handleSave}
          className="p-6 overflow-y-auto flex-1 space-y-6"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Seu Nome Completo
              </label>
              <input
                type="text"
                value={data.nome}
                onChange={(e) => setData({ ...data, nome: e.target.value })}
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Cargo Atual ou Principal
              </label>
              <input
                type="text"
                value={data.cargo_atual}
                onChange={(e) =>
                  setData({ ...data, cargo_atual: e.target.value })
                }
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Anos de Experiência Relevante
              </label>
              <input
                type="number"
                min="0"
                max="40"
                value={data.anos_experiencia}
                onChange={(e) =>
                  setData({ ...data, anos_experiencia: Number(e.target.value) })
                }
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Nível de Proficiência em Inglês
              </label>
              <select
                value={data.nivel_ingles}
                onChange={(e) =>
                  setData({
                    ...data,
                    nivel_ingles: e.target
                      .value as PerfilUsuario["nivel_ingles"],
                  })
                }
                className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-medium"
              >
                <option value="basico">Básico (Leitura técnica simples)</option>
                <option value="intermediario">
                  Intermediário (Conversação básica)
                </option>
                <option value="avancado">
                  Avançado (Reuniões técnicas em inglês)
                </option>
                <option value="fluente">
                  Fluente (Comunicação plena e negociações)
                </option>
                <option value="nativo">Nativo ou Bilíngue</option>
              </select>
            </div>
          </div>

          {/* Cargos Alvo */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
              Cargos que você tem como alvo
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={novoCargoAlvo}
                onChange={(e) => setNovoCargoAlvo(e.target.value)}
                placeholder="Novo cargo alvo (ex.: Tech Lead Frontend)"
                className="flex-1 px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
              <button
                type="button"
                onClick={handleAddCargoAlvo}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500"
              >
                Adicionar
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {data.cargos_alvo.map((cargo, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-semibold bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
                >
                  <span>{cargo}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveCargoAlvo(cargo)}
                    className="hover:text-rose-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Competências Chave */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
              Competências e Tecnologias Chave
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={novaSkill}
                onChange={(e) => setNovaSkill(e.target.value)}
                placeholder="Ex.: GraphQL, Next.js, Docker, Design System"
                className="flex-1 px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
              <button
                type="button"
                onClick={handleAddSkill}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500"
              >
                Adicionar
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {data.competencias_chave.map((skill, idx) => (
                <span
                  key={idx}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700"
                >
                  <span>{skill}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(skill)}
                    className="hover:text-rose-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Pretensões Salariais */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Pretensão Salarial Nacional (BRL)
              </label>
              <input
                type="text"
                value={data.pretensao_salarial_brl || ""}
                onChange={(e) =>
                  setData({ ...data, pretensao_salarial_brl: e.target.value })
                }
                placeholder="Ex.: R$ 15.000 - R$ 18.000 CLT"
                className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Pretensão Internacional (USD)
              </label>
              <input
                type="text"
                value={data.pretensao_salarial_usd || ""}
                onChange={(e) =>
                  setData({ ...data, pretensao_salarial_usd: e.target.value })
                }
                placeholder="Ex.: $5,000 - $7,000 USD / mês"
                className="w-full px-3 py-2 rounded-xl text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          {/* Data Portability Section */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-3">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500">
              Backup, Exportação e Restauração de Dados
            </h4>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleExportJson}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Exportar Backup (JSON)</span>
              </button>

              <button
                type="button"
                onClick={() => setShowImportBox(!showImportBox)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition"
              >
                <Upload className="w-3.5 h-3.5" />
                <span>Restaurar de JSON</span>
              </button>

              <button
                type="button"
                onClick={handleResetDefaults}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition ml-auto"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Restaurar Demo</span>
              </button>
            </div>

            {showImportBox && (
              <div className="space-y-2 p-3 bg-slate-50 dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700">
                <textarea
                  rows={3}
                  value={jsonImportString}
                  onChange={(e) => setJsonImportString(e.target.value)}
                  placeholder="Cole aqui o conteúdo do seu arquivo JSON exportado..."
                  className="w-full p-2.5 rounded-xl text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 font-mono"
                />
                <button
                  type="button"
                  onClick={handleImportJson}
                  className="px-4 py-1.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500"
                >
                  Confirmar Importação
                </button>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-xs transition"
            >
              <Save className="w-4 h-4" />
              <span>
                {salvoSucesso ? "Perfil Atualizado!" : "Salvar Perfil"}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
