# Contrato: começar pelo currículo e currículo base

## Rotas (só deste computador)

| Rota | O que faz |
|---|---|
| `GET /api/perfil/curriculos` | arquivos PDF/DOCX de `anexos/` (nome, caminho, idioma, data), o currículo base de cada idioma e se há perfil |
| `POST /api/perfil/do-curriculo` | `{arquivo}` ou `{material_id}` → a proposta (texto, idioma, perfil, dados, filtros, existe_perfil); não grava |
| `POST /api/perfil/do-curriculo/confirmar` | `{arquivo, perfil_markdown, filtros, manter_perfil, marcar_base, idioma}` → grava perfil (se não manter), filtros e currículo base; `400` com a explicação |
| `PUT /api/curriculo-base` | `{idioma, arquivo}` marca; `{idioma, arquivo: null}` desmarca |
| `GET /arquivos/curriculo-base/<idioma>` | o arquivo marcado daquele idioma (e nenhum outro) |
| `GET /api/vagas` | o item `curriculo` do checklist com `base` ou `falta_base` |

## Módulo `curriculo_base.py`

```text
candidatos() -> list            marcados(cfg) -> {pt, en}          marcar(idioma, arquivo) / desmarcar(idioma)
ler(arquivo) -> {texto, idioma, avisos}                            perfil_do_curriculo(texto, arquivo) -> str
dados_do_curriculo(texto, com_ia) -> dict                          proposta(arquivo | material) -> dict
confirmar(dados) -> dict                                           origem_do_perfil(texto) -> {arquivo, data} | None
```

## Linha de comando

```text
PY curriculo_base.py lista
PY curriculo_base.py proposta anexos/meu-cv.pdf          # mostra perfil e filtros; não grava
PY curriculo_base.py usar anexos/meu-cv.pdf [--manter-perfil]   # grava (só com o OK da pessoa)
PY curriculo_base.py marcar anexos/resume.pdf [--idioma en]
```
