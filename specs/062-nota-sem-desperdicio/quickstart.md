# Quickstart: validar a spec 062

Pré-requisitos: worktree `../mpt-062`, `.venv` do projeto, e para os passos com IA, a branch pessoal com
`config.json`, `perfil.md`, vagas no banco e uma IA ligada.

## 1. Testes

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```

Esperado: tudo passa, incluindo `test_nota_regras`, `TestAnaliseLimite` e `TestForcarGrupos`.

## 2. Tamanho do pedido (SC-001), sem IA

```powershell
.venv\Scripts\python.exe calibrar_nota.py --medir <ID>   # ou sem ID
```

Esperado: total ≤ 20.000 caracteres (a vaga medida em 26/11 tinha 25.729), "SC-001: PASSA", e o pedido sem a seção Contato.

## 3. Calibração (SC-002), com IA, na branch pessoal

```powershell
.venv\Scripts\python.exe calibrar_nota.py
```

Esperado: "SC-002: PASSA" (≥ 90% com diferença ≤ 10, nenhuma troca de fora/dentro sem motivo). Sem PASSA, ajustar
`regras-da-nota.md` e repetir com `--ids` do relatório anterior.

## 4. Começo idêntico (FR-007)

Coberto pelo teste; para conferir à mão, gerar dois pedidos de vagas de portais diferentes (`--medir` com IDs
diferentes grava o pedido em `.cache/pedido-<ID>.txt`) e comparar até `## Vagas`.

## 5. Forçar em grupos (SC-003), na página

Reiniciar o dashboard, forçar 6 vagas que já têm descrição e olhar o terminal do servidor: 2 linhas de pedido à IA
(3 + 3), com a pausa `FORCAR_PAUSA` entre elas.

## 6. Análise automática no limite (SC-004)

Coberto pelo `TestAnaliseLimite` (IA falsa com 429). Na vida real: depois de uma busca com muitas vagas novas no
provedor gratuito, o terminal mostra a pausa entre lotes e, se vier 429, "lote de 5 em 60 s"; no fim, nenhuma vaga com
descrição fica sem nota sem que a pessoa precise forçar.

## 7. Skill

```powershell
python sincronizar_skills.py --conferir
```

Esperado: sem diferença; a skill `buscar-vagas` aponta para `regras-da-nota.md` e não repete o texto.
