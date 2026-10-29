---
description: "Tarefas da feature 037: Materiais do Meu perfil em três áreas e OCR de PDF só de imagem (Windows)"
---

# Tasks: Materiais do Meu perfil em três áreas (e OCR)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md),
[contracts/](contracts/), [quickstart.md](quickstart.md).

**Testes**: pedidos pela constituição (função pura nova ganha `unittest`) e pelo SC-005. Os arquivos são:
- `tests/test_ocr.py`, novo, com o PowerShell simulado;
- `tests/test_primeiros_passos.py`;
- `tests/test_curriculo_base.py`.

O OCR real é conferido à mão com os certificados do usuário. O front não tem testes automáticos: `tsc`, `vite build`
e o teste na página.

**Caminhos**:
- **Backend**: na worktree `../mpt-037-materiais-por-area`.
- **Front**: na worktree `../mpt-front-027b`, branch `front-037-materiais-por-area` saída da `frontend-react`.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Na worktree `../mpt-front-027b`:
  1. `git status` limpo;
  2. `git pull` da `frontend-react` (d1858f5 ou depois);
  3. criar a branch `front-037-materiais-por-area`;
  4. `npx -y pnpm@10.34.3 install --frozen-lockfile`;
  5. conferir com `npx -y pnpm@10.34.3 exec tsc --noEmit`.

## Phase 2: Foundational (áreas no backend; bloqueia US1–US4)

- [X] T002 Testes em `tests/test_primeiros_passos.py` (classe `TestAreas`):
  - `area_de(tipo)` para os 7 tipos;
  - `extrair(pdf, area="documento")` → `documento_pdf`;
  - `extrair(docx, area="documento")` → `documento_docx`;
  - `extrair(pdf, area="linkedin")` → `linkedin_pdf`, mesmo sem cara de LinkedIn;
  - `extrair(zip, area="curriculo")` recusa com "O ZIP do LinkedIn vai na área do LinkedIn";
  - `extrair(docx, area="linkedin")` recusa com "Aqui vão o PDF do perfil do LinkedIn ou o ZIP da exportação";
  - `area="x"` → "área inválida: use linkedin, curriculo ou documento";
  - sem área, a adivinhação de hoje;
  - `adicionar_material(..., area="documento")` grava `documento_pdf`.
- [X] T003 Em `primeiros_passos.py`:
  - `AREAS = {"linkedin": (".pdf", ".zip"), "curriculo": (".pdf", ".docx"), "documento": (".pdf", ".docx")}`;
  - `area_de(tipo)`;
  - `conferir_formato(nome, area=None)`, com as mensagens de research.md R2;
  - `extrair(caminho, area=None)`, em que a área decide o tipo e sem área vale a regra de hoje;
  - extrair a regra de LinkedIn para `parece_linkedin(texto)`;
  - `adicionar_material(estado, nome, dados=None, texto=None, area=None)`.
- [X] T004 Em `dash/servidor.py`, `POST /api/perfil/material` passa `corpo.get("area")` (string ou None) para
  `pp.adicionar_material`.

**Checkpoint**: o envio com área funciona pela API, e a página antiga continua igual.

---

## Phase 3: User Story 1 - Cada coisa na sua área (Priority: P1) 🎯 MVP

**Goal**: três áreas no passo Materiais, cada uma com o seu envio e a sua lista; "Usar este currículo" só em Currículos.

**Independent Test**: enviar um certificado em Outros documentos. Ele aparece só lá, como "Documento (PDF)", sem o
botão de currículo.

- [X] T005 [US1] Em `primeiros_passos.estado_para_pagina`, cada material ganha `area: area_de(m["tipo"])` e
  `ocr: bool(m.get("ocr"))`. Teste em `TestAreas`.
- [X] T006 [P] [US1] Em `src/services/api/perfil.ts`:
  - `Material` ganha `area: "linkedin" | "curriculo" | "documento"`, `sugestao: {area, motivo} | null` e `ocr:
    boolean`;
  - `enviarMaterial` aceita `area?`.
- [X] T007 [US1] Criar `src/components/perfil/Materiais.tsx`, com o `Materiais` que hoje está em `MeuPerfil.tsx` e a
  mesma interface, mais `onEnviar(files, area)`:
  - **As três seções `SEC`**, cada uma com o próprio `<label>` de arrastar e soltar e o `<input accept>` da área:
    - Perfil do LinkedIn: `.pdf,.zip`, com "Como baixar do LinkedIn" e o campo do link;
    - Currículos: `.pdf,.docx`, com os currículos da pasta anexos e o "Cole o texto do currículo";
    - Outros documentos e certificações: `.pdf,.docx`, com a dica "Certificados, diplomas, cartas de recomendação. A IA
      usa em Formação e Certificações; nunca viram currículo.".
  - **Lista de cada seção**: os materiais com `m.area` da seção.
  - **Botão de currículo**: "Usar este currículo e ir para as vagas" só em Currículos.
  - **Rótulos de tipo**: `TIPOS_MATERIAL` ganha `documento_pdf: "Documento (PDF)"` e `documento_docx: "Documento
    (Word)"`.
  - **Rodapé**: o "Continuar" de hoje.
- [X] T008 [US1] Em `src/components/perfil/MeuPerfil.tsx`:
  - tirar `Materiais` e importar de `./Materiais`;
  - `enviarArquivos(files, area?)` passa `area` a `perfilApi.enviarMaterial`;
  - tirar os imports que ficarem sem uso.

**Checkpoint**: as três áreas funcionam, e o certificado novo fica em Documentos.

---

## Phase 4: User Story 2 - Mover um arquivo de área (Priority: P1)

**Goal**: Mover para em cada arquivo, sem reenviar.

**Independent Test**: um PDF em Currículos movido para Documento sai de Currículos, perde o botão de currículo e some
do seletor Seu currículo.

- [X] T009 [US2] Testes em `TestAreas`:
  - `mover_material(estado, id, "documento")` troca `curriculo_pdf` por `documento_pdf` e mantém `arquivo`, `texto`
    e `id`;
  - Word para LinkedIn é recusado;
  - texto colado: "o texto colado fica em Currículos";
  - id inexistente dá `PerfilErro`.
- [X] T010 [US2] Em `primeiros_passos.py`, `mover_material(estado, mid, area) -> dict`, com o tipo recalculado pela
  extensão de `arquivo` (research.md R1).
- [X] T011 [P] [US2] Testes em `tests/test_curriculo_base.py`:
  - `candidatos()` não traz arquivo que está nos materiais como `documento_*` ou `linkedin_*`, e traz os
    `curriculo_*`;
  - `desmarcar_arquivo(arquivo)` apaga a marcação pt/en desse arquivo e devolve os idiomas desmarcados.
- [X] T012 [US2] Em `curriculo_base.py`:
  - `candidatos()` filtra pelos materiais do progresso (`pp.carregar()`, área documento ou LinkedIn);
  - `desmarcar_arquivo(arquivo) -> list[str]`, que usa `marcar(idioma, None)`.
- [X] T013 [US2] Em `dash/servidor.py`, `PUT /api/perfil/material/{id}` `{area}`, dentro de `TRAVA_PERFIL`:
  - chama `pp.mover_material` e salva;
  - para área diferente de currículo, chama `curriculo_base.desmarcar_arquivo`;
  - responde `{estado, aviso?}`, com o aviso "Este arquivo era o seu currículo em <português|inglês>; a marcação
    saiu.".
- [X] T014 [US2] Front:
  - em `src/services/api/perfil.ts`, `moverMaterial(id, area)`;
  - em `Materiais.tsx`:
    - "Mover para" (`<select>` com as áreas que aceitam a extensão, sem a atual), que não aparece no texto colado;
    - depois de mover, `onEstado` e `onAviso` (mensagem "Movido para <área>.", mais o aviso do servidor).

---

## Phase 5: User Story 5 - OCR de PDF só de imagem (Priority: P1)

**Goal**: o PDF sem texto é lido pelo OCR do Windows, no envio e pelo botão OCR.

**Independent Test**: no Windows, o botão OCR num dos certificados só de imagem mostra o texto do curso e o aviso de
OCR.

- [X] T015 [P] [US5] Testes em `tests/test_ocr.py`:
  - `disponivel()` é `False` fora do Windows (com `sys.platform` simulado);
  - `ler_pdf` lê o JSON `{paginas, lidas, textos}` e junta as páginas;
  - `paginas > lidas` dá o aviso "OCR só nas 5 primeiras páginas";
  - `{"erro": …}`, `TimeoutExpired`, `OSError` e JSON inválido dão `("", [aviso com o motivo])`;
  - fora do Windows dá `("", [])`.

  O `subprocess.run` é simulado com `mock.patch`.
- [X] T016 [US5] Criar `ocr_windows.ps1` na raiz, a partir do script testado (research.md R4):
  - parâmetros `-Caminho` e `-MaxPaginas` (padrão 5);
  - tipos WinRT e o `AsTask` para esperar as operações;
  - motor pt-BR ou o primeiro disponível; sem nenhum, `{"erro": "sem OCR neste Windows"}`;
  - por página: 1.600 px; se a leitura tiver menos de 40 letras, tenta 1.200 e 2.400 px e fica com a mais longa;
  - escreve na saída `ConvertTo-Json -Compress` em UTF-8;
  - erros em `try/catch` viram `{"erro": mensagem}`.
- [X] T017 [US5] Criar `ocr.py` na raiz:
  - `SCRIPT`, `TEMPO_LIMITE = 30`, `MAX_PAGINAS = 5`;
  - `disponivel()`: Windows e `shutil.which("powershell")`;
  - `ler_pdf(caminho) -> (texto, avisos)`, conforme [contracts/ocr.md](contracts/ocr.md): `subprocess.run` com lista
    de argumentos, `capture_output`, `timeout` e `creationflags=CREATE_NO_WINDOW` no Windows;
  - docstring no topo, como nos outros módulos.
- [X] T018 [US5] Testes em `tests/test_primeiros_passos.py` (`TestOcrNoPdf`), com `ocr.ler_pdf` e
  `ocr.disponivel` simulados:
  - PDF sem texto + OCR com "Certificado … CPF 123.456.789-09" → `texto` com o CPF mascarado, `ocr: True` e o aviso
    "Texto lido da imagem (OCR): confira nomes, datas e números";
  - OCR vazio → o aviso de PDF digitalizado de hoje;
  - PDF com texto → o OCR não é chamado;
  - `reler_material` só aceita PDF sem texto ("o OCR é só para PDF sem texto") e mantém a área.
- [X] T019 [US5] Em `primeiros_passos.py`:
  - `ler_pdf`: sem texto e com `ocr.disponivel()`, chama `ocr.ler_pdf` e devolve `(texto, avisos, lido_por_ocr)`.
    Quem já chama `ler_pdf` deve ser ajustado, ou sai uma função nova `ler_pdf_com_ocr` usada por `extrair`;
  - `extrair` grava `ocr`;
  - `reler_material(estado, mid)`.
- [X] T020 [US5] Em `dash/servidor.py`, `POST /api/perfil/material/{id}/ocr`, dentro de `TRAVA_PERFIL`: chama
  `pp.reler_material` e salva. Responde `{material, estado}`.
- [X] T021 [US5] Front:
  - em `perfil.ts`, `ocrMaterial(id)`;
  - em `Materiais.tsx`, o botão **OCR** (`BTN_MINI`) no material PDF com `!tem_texto`:
    - mostra o spinner enquanto lê;
    - com texto lido, `onAviso("Texto lido da imagem.")`; sem texto, o aviso do material;
    - `title` "Ler o texto da imagem do PDF com o OCR do Windows".
- [X] T022 [US5] Conferir o OCR real na máquina do usuário: rodar `ocr.ler_pdf` nos 7 PDFs sem texto de
  `anexos/primeiros-passos/`, só leitura e sem gravar o progresso. Os 7 devem trazer o nome do curso.

---

## Phase 6: User Story 3 - Aviso de área trocada (Priority: P2)

**Goal**: aviso amarelo com o botão da área sugerida.

**Independent Test**: um certificado curto em Currículos mostra "Parece um certificado…" com o botão para Documentos.

- [X] T023 [US3] Testes em `TestAreas`, para `sugestao_de_area(material)` em todos os casos da tabela do
  data-model:
  - certificado curto em currículo → documento;
  - currículo de 4.000 caracteres que cita "certificado" → nada;
  - texto de LinkedIn em currículo ou documento → linkedin;
  - PDF em linkedin sem cara de LinkedIn → curriculo, ou documento quando tem marca de certificado;
  - sem texto ou ZIP → nada;
  - acentos e maiúsculas ("CERTIFICAMOS", "Carga Horária") também contam.
- [X] T024 [US3] Em `primeiros_passos.py`:
  - `MARCAS_CERTIFICADO`, `LIMITE_CERTIFICADO = 3000` e `sugestao_de_area(m) -> dict | None`, com os motivos:
    - "Parece um certificado.";
    - "Parece o PDF do seu perfil do LinkedIn.";
    - "Não parece o PDF do perfil do LinkedIn.";
  - em `estado_para_pagina`, `sugestao`.
- [X] T025 [US3] Em `Materiais.tsx`, com `m.sugestao`, a linha amarela `{motivo}` e o botão "Mover para {nome da
  área}", que chama `moverMaterial`.

---

## Phase 7: User Story 4 - Documentos no perfil, nunca como currículo (Priority: P2)

**Goal**: a IA sabe a área de cada fonte; documentos e LinkedIn fora das listas de currículo.

**Independent Test**: o pedido do rascunho traz "(área: certificado ou documento)" e as regras novas.

- [X] T026 [US4] Teste em `TestRascunho`: `pedido_rascunho` traz:
  - `### Fonte: <nome> (área: certificado ou documento)`;
  - `(área: currículo; texto lido por OCR, pode ter erros de leitura)`;
  - as duas regras novas (research.md R5).
- [X] T027 [US4] Em `primeiros_passos.pedido_rascunho`:
  - cabeçalho com área e OCR;
  - as regras "Fontes da área certificado ou documento entram só em formação e certificações, nunca como
    experiência." e "Em texto lido por OCR, não use número, data ou nome que pareça mal lido; deixe de fora.";
  - "(currículos, LinkedIn)" passa a "(currículos, LinkedIn, certificados e documentos)".

---

## Phase 8: Polish e entrega

- [X] T028 [P] Documentação:
  - `README.md`: Primeiros passos, Materiais em três áreas e OCR no Windows;
  - `dash/API.md` §3.6: rotas e campos, conforme [contracts/api-materiais.md](contracts/api-materiais.md);
  - `.agents/skills/analisar-perfil/SKILL.md`: perguntar o que é cada arquivo; certificados como documento;
    `extrair --area`; depois, `python sincronizar_skills.py` (e desfazer as cópias que só mudarem o fim de linha);
  - `specs/lista-de-desejos.md`: OCR no macOS (Vision) e no Linux (Tesseract opcional).
- [X] T029 Em `primeiros_passos.main`, `extrair <arquivo> [--area linkedin|curriculo|documento]`, com teste em
  `TestLinhaDeComando`.
- [X] T030 Rodar `python -m unittest discover -s tests`: tudo passa.
- [X] T031 Rodar `tsc --noEmit` e `vite build --base ./` no front e commitar na `front-037-materiais-por-area`.
- [X] T032 Procurar dados pessoais nos diffs (nomes, cursos ou arquivos do usuário nos testes e na spec) e commitar
  na `037-materiais-por-area`.
- [ ] T033 Na pasta principal (branch pessoal):
  - `git merge 037-materiais-por-area`;
  - copiar o `dist/` para `dash/front/`, sem commit;
  - rodar os testes;
  - reiniciar o dashboard;
  - pedir o teste do usuário pelo [quickstart.md](quickstart.md).
- [ ] T034 Com o OK do usuário:
  1. `git checkout -- dash/front` e apagar os assets novos;
  2. merge `--no-ff` na `master` e push (com os testes passando);
  3. merge da branch do front na `frontend-react` e push;
  4. `gh workflow run front.yml` e merge do PR com squash;
  5. `git merge origin/master` na branch pessoal;
  6. apagar a worktree e as branches;
  7. `graphify update .`.

---

## Dependencies & Execution Order

- **T001** vem antes do front. **T002–T004** vêm antes de todas as histórias.
- **US1 (T005–T008)** é o MVP. **US2 (T009–T014)** depende de US1 no front (`Materiais.tsx`).
- **US5 (T015–T022)**:
  - o backend é independente de US1 e US2;
  - o botão OCR (T021) depende de `Materiais.tsx` (T007).
- **US3 (T023–T025)** depende de `mover_material` (T010) e de `moverMaterial` no front (T014).
- **US4 (T026–T027)** depende só de T003, mais do campo `ocr` (T019) para a marca de OCR.
- **Polish** vem no fim.
- `primeiros_passos.py` é tocado por T003, T005, T010, T019, T024, T027 e T029, que rodam em sequência.

## Parallel Opportunities

- Backend e front em worktrees diferentes.
- T006, T011 e T015 em paralelo, porque estão em arquivos diferentes.
- `ocr.py`, `ocr_windows.ps1` e `test_ocr.py` (T015–T017) em paralelo com as tarefas de áreas em `primeiros_passos.py`.

## Implementation Strategy

1. **MVP**: Setup, Foundational e US1. O certificado novo vai para Documentos e não vira currículo.
2. US2 move os antigos. US5 lê os PDFs só de imagem. Com isso, o caso do usuário fica resolvido.
3. US3 avisa da área trocada. US4 manda a área de cada fonte à IA e tira documentos e LinkedIn das listas de currículo.
4. Polish e entrega: a master e o PR só depois do OK do usuário.
