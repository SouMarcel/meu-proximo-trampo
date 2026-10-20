import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import { ScreenPreferencesService, aplicarTema } from "./services/storage"
import "./index.css"

// Tema antes de pintar a página; no "sistema", acompanha a troca de tema do computador.
aplicarTema(ScreenPreferencesService.getTema())
window.matchMedia?.("(prefers-color-scheme: dark)").addEventListener?.("change", () => {
  aplicarTema(ScreenPreferencesService.getTema())
})

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
