# Quickstart: conferir "LinkedIn com menos pedidos"

Pré-requisitos: `.venv` pronto (`python iniciar.py`), rodar da raiz do projeto. `PY` = `.venv\Scripts\python.exe`.

## 1. Testes (sem rede)

```powershell
PY -m unittest tests.test_linkedin tests.test_busca
PY -m unittest discover -s tests
```

Cobrem:
- a expressão OR (aspas, parênteses, um cargo só, divisão por tamanho);
- uma consulta por grupo e até 3 páginas;
- os cargos da vaga pelo título;
- no máximo 20 descrições, com as pendentes primeiro;
- a marca de pendente, e a marca saindo quando o texto chega;
- a IA pulando as pendentes (`analise.precisa`, `banco.precisa_analise`);
- a espera gravada, respeitada e expirando depois de 6 horas;
- o motivo do bloqueio nos 4 tipos;
- a confirmação na página (`iniciar` com e sem `confirmar_espera`, e `so_espera`);
- o terminal com o código 5;
- o aviso de mais de 5 cargos;
- a saída idêntica com LinkedIn e Indeed desligados.

## 2. Pesquisa R1: o OR na busca pública (um pedido, com o OK da pessoa)

Só depois de 6 horas sem bloqueio. Um pedido com 2 a 3 cargos fictícios genéricos. O que conferir:
- a resposta é 200;
- vêm cards;
- há títulos de mais de um cargo.

Anotar o resultado em [research.md](research.md) (R1). Se falhar, aplicar o plano B (`AGRUPAR = False`).

## 3. Página (Windows)

1. Subir o servidor com `--sem-navegador` e abrir o dashboard (Live Server ou http://127.0.0.1:8765).
2. **Filtros da busca**:
   - com 6 cargos e o LinkedIn ligado, o aviso de cargos aparece e salvar funciona;
   - com 5 cargos, o aviso some.
3. **Espera simulada**: criar `.cache/linkedin-espera.json` com `desde` = agora. Em **Buscar vagas**:
   - o diálogo mostra "LinkedIn em espera até HH:MM" e o botão "Buscar sem o LinkedIn";
   - Cancelar não começa nada;
   - confirmar busca só nas outras fontes.
4. Com só o LinkedIn ligado e em espera, o botão fica desligado e a mensagem explica.
5. Apagar o arquivo: a busca volta ao normal.
6. **Descrição pendente**: com uma vaga do LinkedIn marcada `descricao_pendente`, o relatório mostra o chip
   "Descrição pendente", e a análise automática não a pega.

## 4. Terminal

```powershell
PY vagas.py buscar --fontes linkedin gupy        # com espera: pergunta [s/N]
PY vagas.py buscar --fontes linkedin gupy < NUL  # sem terminal: código 5
PY vagas.py buscar --fontes linkedin gupy --confirmar-espera
```

## 5. Busca real (com o OK da pessoa, fora da espera)

Uma busca pela página com o LinkedIn ligado. O que conferir no progresso e no resumo:
- até 3 páginas por grupo e até 20 descrições;
- as vagas que passaram do limite aparecem como "Descrição pendente";
- na busca seguinte (depois do intervalo), as pendentes são lidas primeiro.
