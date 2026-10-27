# Implementation Plan: Dados de contato na candidatura assistida, sem IA

**Branch**: `033-dados-de-contato` (worktree `../meu-proximo-trampo-033`, saída da `master`) | **Date**: 2026-10-28 |
**Spec**: [spec.md](spec.md)

## Summary

**Módulo novo `candidatura/contato.py`**:
- `ler()`, `gravar(dados)` e `apagar()` cuidam de `dash/dados/contato.json`, ao lado da memória de respostas;
- `propor()` monta a proposta a partir do currículo base (`curriculo_base.marcados()` e
  `primeiros_passos.extrair`/`reconhecer_contato`; o nome sai da primeira linha), da memória e dos filtros da busca. A
  proposta não é gravada;
- `reconhecer(campo)` diz qual dado de contato o campo pede, pelo `autocomplete`, pelo tipo e por sinônimos. A pergunta
  inteira precisa bater com o sinônimo, não só um pedaço dela;
- `valor_para(campo, dados)` devolve o valor no formato do campo: texto, ou o índice da opção numa lista de país ou
  estado.

**`candidatura/auto.preencher_pagina`**:
- antes da memória, preenche os campos de contato reconhecidos (marca `cadastro` ou `comum`, nunca `sensivel`) com
  `da_pessoa=True`, a fonte "seus dados de contato" e sem pisar em valor existente;
- o resto segue igual: memória, depois a IA.

**Servidor**:
- `GET /api/candidatura` passa a trazer `contato`;
- rotas novas: `PUT` e `DELETE /api/candidatura/contato` e `POST /api/candidatura/contato/proposta`.

**Front** (`frontend-react`): seção "Seus dados de contato" no painel da candidatura assistida (`ConfigCandidatura.tsx`).

**Documentação**: `dash/API.md`, README e spec 027.

## Technical Context

**Language/Version**: Python 3.10+, só biblioteca padrão. O PDF é lido pelo pypdf, que já é usado nos primeiros
passos. Front em TypeScript, na `frontend-react`.

**Primary Dependencies**: nenhuma nova.

**Storage**: `dash/dados/contato.json`, fora do Git, com `{nome, sobrenome, email, telefone, cidade, estado, pais,
linkedin, portfolio, endereco, cep}`, gravado só quando a pessoa salva.

**Testing**: `unittest` sem rede e sem navegador, com `PaginaFalsa` (como `test_candidatura_assistida.py`), um texto de
currículo fictício, memória e `config.json` temporários. Os testes atuais da candidatura assistida servem de não
regressão.

**Constraints**:
- dado de contato nunca vai à IA;
- nada é gravado sem a pessoa salvar;
- CPF, RG e data de nascimento são recusados;
- campo `sensivel` nunca é preenchido com dado de contato;
- não pisa em valor já preenchido.

**Scale/Scope**: 11 campos; o reconhecimento roda por campo da página, sem custo de rede.

## Constitution Check

| Princípio | Avaliação |
|---|---|
| I. Local e privado | ✅ Os dados ficam em `dash/dados/`, fora do Git, e nunca vão à IA nem a outro serviço. |
| II. Pública, sem dados pessoais | ✅ Testes com dados fictícios; nenhum dado da pessoa no código. |
| III. Simples | ✅ Biblioteca padrão; funciona sem IA. |
| IV. Só fatos | ✅ Só o que a pessoa confirmou ao salvar. A proposta vem do currículo dela e das respostas que ela mesma deu. Documentos de identificação ficam de fora. |
| V. A pessoa decide | ✅ Propor não grava. A pessoa confere na janela antes de avançar, e o envio é sempre dela. |
| VI. Candidatura assistida | ✅ Só preenche campos, nunca clica. Pergunta sensível continua só com a resposta da pessoa. |
| Fluxo | ✅ Spec aprovada em 28/10 → plano → tarefas. |

Resultado: passa, sem desvio.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Verificação só no Windows | Decisão da pessoa | Mesmo motivo das specs anteriores |

## Project Structure

### Documentation (this feature)

```text
specs/033-dados-de-contato/
├── spec.md, plan.md, research.md (R1–R4 + decisões D1–D6)
├── data-model.md, quickstart.md
├── contracts/contato.md
└── checklists/requirements.md
```

### Source Code (repository root)

```text
candidatura/contato.py      # novo: ler, gravar, apagar, propor, reconhecer, valor_para
candidatura/auto.py         # dados de contato antes da memória e da IA
dash/servidor.py            # GET /api/candidatura com contato; PUT/DELETE /contato; POST /contato/proposta
dash/API.md, README.md, specs/027-candidatura-assistida/spec.md (referência)
tests/test_dados_contato.py
frontend-react: src/services/api/candidatura.ts, src/components/modals/ConfigCandidatura.tsx (ou um componente
  DadosContato.tsx dentro dele)
```

**Structure Decision**: um módulo próprio ao lado de `memoria.py`. A memória continua sendo "o que a pessoa respondeu
numa pergunta"; os dados de contato são "quem a pessoa é", reconhecidos pelo sentido. `auto.py` só ganha um passo
antes da memória.
