# Implementation Plan: Materiais do Meu perfil em três áreas (e OCR de PDF só de imagem)

**Branch**: `037-materiais-por-area` (worktree `../mpt-037-materiais-por-area`, saída da `master`; front na
`frontend-react`, worktree `../mpt-front-027b`) | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

## Summary

- **`ocr.py`** (raiz, novo) e **`ocr_windows.ps1`** (raiz, novo):
  - `disponivel()` e `ler_pdf(caminho) -> (texto, avisos)`;
  - o Python chama o script do PowerShell, que usa o que o Windows já traz (`Windows.Data.Pdf` para a página virar
    imagem e `Windows.Media.Ocr` em pt-BR);
  - até 5 páginas, 1.600 px primeiro, outros tamanhos se a leitura vier curta;
  - saída em JSON (UTF-8), tempo limite de 30 s;
  - fora do Windows, sem PowerShell ou sem o idioma: devolve vazio, sem erro.
- **`primeiros_passos.py`**:
  - `AREAS` (`linkedin`, `curriculo`, `documento`) e os formatos de cada uma;
  - `extrair(caminho, area=None)`: com área, vale a área (tipos novos `documento_pdf` e `documento_docx`); sem área,
    a adivinhação de hoje;
  - `ler_pdf` tenta `ocr.ler_pdf` quando o PDF não tem texto, e o material ganha `ocr: true` e o aviso;
  - `adicionar_material(..., area=None)`, `mover_material(estado, id, area)` e `reler_material(estado, id)` (OCR);
  - `area_de(tipo)` e `sugestao_de_area(material)`, o aviso de área trocada;
  - `pedido_rascunho`: cada fonte com a área e a marca de OCR, mais as regras de documento e de OCR;
  - `estado_para_pagina`: cada material com `area`, `sugestao` e `ocr`;
  - `extrair` na linha de comando aceita `--area`.
- **`curriculo_base.py`**:
  - `candidatos()` tira os arquivos que estão nos materiais como documento ou LinkedIn;
  - quem move para documento ou LinkedIn um arquivo marcado como Seu currículo perde a marcação (`desmarcar_arquivo`).
- **`dash/servidor.py`**:
  - `POST /api/perfil/material` aceita `area`;
  - rotas novas `PUT /api/perfil/material/{id}` `{area}` (Mover para) e `POST /api/perfil/material/{id}/ocr`.
- **Front** (`frontend-react`):
  - `perfil/Materiais.tsx` (novo, sai do `MeuPerfil.tsx`): as três áreas, cada uma com o seu envio e a sua lista;
  - em cada arquivo: Mover para, o aviso com o botão da área sugerida e o botão **OCR**;
  - `services/api/perfil.ts`: `area` no envio, `moverMaterial`, `ocrMaterial`, campos novos do material;
  - `MeuPerfil.enviarArquivos` passa a área.
- **Documentação**: README, `dash/API.md` §3.6, skill `analisar-perfil` (com `sincronizar_skills.py`) e
  `specs/lista-de-desejos.md` (OCR no macOS e no Linux).
- **Testes**:
  - `tests/test_primeiros_passos.py`: áreas, formatos, mover, sugestão, pedido à IA e OCR com `ocr.ler_pdf` simulado;
  - `tests/test_ocr.py` (novo): `disponivel` fora do Windows, leitura do JSON, tempo limite e erro do PowerShell, com
    `subprocess.run` simulado;
  - `tests/test_curriculo_base.py`: candidatos sem documentos.

## Technical Context

- **Language/Version**: Python 3.10+ (biblioteca padrão); PowerShell 5.1 do Windows (já vem no sistema); React 19 e
  TypeScript 5 na `frontend-react`.
- **Primary Dependencies**: nenhuma nova. O OCR é o do Windows 10/11 (`Windows.Media.Ocr`), chamado pelo PowerShell.
- **Storage**: sem arquivo novo. A área fica no próprio material, pelo `tipo` no progresso do perfil
  (`.cache/primeiros-passos.json`, fora do Git). Os arquivos continuam em `anexos/primeiros-passos/`.
- **Testing**: `python -m unittest discover -s tests`; `tsc --noEmit` e `vite build`; OCR real conferido à mão com
  os certificados do usuário (o teste automático simula o PowerShell).
- **Target Platform**: Windows primeiro. No macOS e no Linux, tudo menos o OCR.
- **Constraints**:
  - página antiga compatível: o envio sem área e o tipo novo aparecem pelo nome;
  - OCR sem rede, com tempo limite;
  - CPF e RG mascarados depois do OCR.
- **Scale/Scope**: 3 módulos Python e 1 script; 1 componente novo no front; 2 rotas novas.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ O OCR roda no computador, sem rede. O texto passa pela máscara de documentos antes de ser guardado e antes de qualquer envio à IA, que já recebia o texto dos materiais. |
| II. Pública | ✅ Áreas e palavras de certificado genéricas; testes fictícios. |
| III. Simples | ⚠ Sem dependência nova, mas com um script PowerShell que só funciona no Windows. **Justificativa**: o OCR é um recurso do sistema; fora do Windows a ferramenta segue igual a hoje, com o aviso de PDF digitalizado. O macOS e o Linux vão para a lista de desejos. Não é serviço externo nem dependência instalada. |
| IV. Só fatos | ✅ O texto do OCR é do documento da pessoa, marcado como "lido da imagem: confira". A IA recebe a regra de não usar número ou data duvidosa, e tudo passa pela Revisão. |
| V. A pessoa decide | ✅ Mover e o OCR dos materiais antigos só no clique; o aviso não muda a área sozinho. A leitura no envio é a mesma de hoje (ler o arquivo que a pessoa mandou). Desmarcar Seu currículo só acontece quando a própria pessoa move o arquivo, com aviso. |
| VI. Portais | ✅ Não toca em portal. |

Resultado: passa, com a justificativa do item III. A conferência foi refeita depois do desenho, e não há outro
desvio.

## Project Structure

### Documentation (this feature)

```text
specs/037-materiais-por-area/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md
├── contracts/api-materiais.md       # rotas de material: envio com área, mover, OCR
├── contracts/ocr.md                 # entrada e saída do script de OCR
└── checklists/requirements.md
```

### Source Code

```text
ocr.py, ocr_windows.ps1                 # novos
primeiros_passos.py                     # áreas, extrair/adicionar com área, mover, reler, sugestão, pedido, OCR no PDF
curriculo_base.py                       # candidatos sem documentos/LinkedIn; desmarcar ao mover
dash/servidor.py                        # área no envio; PUT material/{id}; POST material/{id}/ocr
README.md, dash/API.md, .agents/skills/analisar-perfil/SKILL.md (+ cópia), specs/lista-de-desejos.md
tests/test_ocr.py (novo), tests/test_primeiros_passos.py, tests/test_curriculo_base.py

frontend-react (../mpt-front-027b):
src/components/perfil/Materiais.tsx   (novo; sai do MeuPerfil.tsx)
src/components/perfil/MeuPerfil.tsx
src/services/api/perfil.ts
```

**Structure Decision**: o backend fica na `037-materiais-por-area`, saída da `master`. O front fica na
`frontend-react`. A entrega segue a ordem das specs anteriores:
1. teste na branch pessoal;
2. com o OK, merge na `master`;
3. Action do front e PR.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Recurso só no Windows (OCR pelo PowerShell) | Ler os certificados que são só imagem, sem instalar nada | Tesseract: exige instalar um programa. IA com visão: mandaria a imagem do documento (com CPF e nome) para fora, sem máscara. |
