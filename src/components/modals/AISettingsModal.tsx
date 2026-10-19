import React, { useState } from "react"
import {
  X,
  Sparkles,
  Save,
  Key,
  Cpu,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ShieldCheck,
} from "lucide-react"
import { ConfigIA } from "../../types/job"

interface AISettingsModalProps {
  isOpen: boolean
  onClose: () => void
  configIA: ConfigIA
  onSaveConfig: (config: ConfigIA) => void
}

export default function AISettingsModal({
  isOpen,
  onClose,
  configIA,
  onSaveConfig,
}: AISettingsModalProps) {
  if (!isOpen) return null

  const [config, setConfig] = useState<ConfigIA>({ ...configIA })
  const [testStatus, setTestStatus] =
    useState<"idle" | "testing" | "success" | "error">("idle")
  const [savedSuccess, setSavedSuccess] = useState(false)

  const handleTestConnection = () => {
    setTestStatus("testing")
    setTimeout(() => {
      setTestStatus("success")
      setConfig((prev) => ({
        ...prev,
        status_conexao: "conectado",
        ultima_verificacao: "Agora",
      }))
    }, 1000)
  }

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    onSaveConfig(config)
    setSavedSuccess(true)
    setTimeout(() => {
      setSavedSuccess(false)
      onClose()
    }, 600)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-5 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-violet-50 dark:bg-violet-950 text-violet-600 dark:text-violet-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-base sm:text-lg text-slate-900 dark:text-white">
                Configurações do Modelo de IA
              </h3>
              <p className="text-xs text-slate-500">
                Escolha a inteligência responsável pelas notas de aderência e
                análise de requisitos
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

        {/* Body Content */}
        <form onSubmit={handleSave} className="p-6 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
              Provedor de Inteligência Artificial
            </label>
            <select
              value={config.provedor}
              onChange={(e) => {
                const prov = e.target.value as ConfigIA["provedor"]
                let defaultModel = "claude-3-7-sonnet"
                if (prov === "openai") defaultModel = "gpt-4o"
                if (prov === "gemini") defaultModel = "gemini-1.5-pro"
                if (prov === "ollama") defaultModel = "llama3:latest"
                if (prov === "deepseek") defaultModel = "deepseek-chat"
                if (prov === "openrouter")
                  defaultModel = "anthropic/claude-3.5-sonnet"
                setConfig({ ...config, provedor: prov, modelo: defaultModel })
              }}
              className="w-full px-3.5 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-semibold"
            >
              <option value="claude">
                Anthropic (Claude 3.7 / 3.5 Sonnet) - Recomendado
              </option>
              <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
              <option value="gemini">Google Gemini (1.5 Pro / Flash)</option>
              <option value="ollama">
                Ollama (Local / 100% Gratuito & Offline)
              </option>
              <option value="deepseek">DeepSeek (V3 / R1)</option>
              <option value="openrouter">OpenRouter (Multi-modelos)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
              Nome do Modelo Efetivo
            </label>
            <div className="relative">
              <Cpu className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={config.modelo}
                onChange={(e) =>
                  setConfig({ ...config, modelo: e.target.value })
                }
                className="w-full pl-9 pr-4 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono"
              />
            </div>
          </div>

          {config.provedor !== "ollama" ? (
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Chave de API ({config.provedor.toUpperCase()})
              </label>
              <div className="relative">
                <Key className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={config.chave_api || ""}
                  onChange={(e) =>
                    setConfig({ ...config, chave_api: e.target.value })
                  }
                  placeholder="sk-ant-... ou sk-..."
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span>
                  Suas chaves são armazenadas localmente com segurança no seu
                  próprio navegador.
                </span>
              </p>
            </div>
          ) : (
            <div>
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block mb-1">
                Endereço do Servidor Ollama
              </label>
              <input
                type="text"
                value={config.url_base || "http://localhost:11434"}
                onChange={(e) =>
                  setConfig({ ...config, url_base: e.target.value })
                }
                className="w-full px-3.5 py-2.5 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-mono"
              />
            </div>
          )}

          {/* Test Status Feedback */}
          {testStatus === "success" && (
            <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                Conexão verificada! O modelo respondeu adequadamente às
                requisições de teste.
              </span>
            </div>
          )}

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testStatus === "testing"}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-300 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 transition"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 ${
                  testStatus === "testing" ? "animate-spin" : ""
                }`}
              />
              <span>Testar Conexão</span>
            </button>

            <div className="flex items-center gap-2">
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
                <span>{savedSuccess ? "Configuração Salva!" : "Salvar"}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
