#!/usr/bin/env python3
"""Consulta a Gupy pela linha de comando, com as ferramentas do MCP público de candidatos.

Para assistentes sem a integração MCP (Codex, OpenCode…); o Claude Code e o Gemini CLI podem usar
o MCP direto (.mcp.json e .gemini/settings.json). Mesmas ferramentas e argumentos do MCP:

  python consultar_gupy.py search_jobs term=analista pwd=true limit=10
  python consultar_gupy.py list_companies term=nubank
  python consultar_gupy.py get_job_by_id id=12345

chave=valor (true/false viram booleano e inteiros viram número) ou um único JSON. Saída em JSON.
"""
import sys

from fontes import gupy

if __name__ == "__main__":
    sys.exit(gupy.main())
