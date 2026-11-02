# Quickstart: conferir a aba Internacional

## Pré-requisitos

- Dashboard aberto em http://127.0.0.1:8765 com o build de teste da página.
- Vagas de fora em pelo menos duas abas internas. A busca internacional ligada traz vagas, e as fora dos critérios
  aparecem com o motivo.

## Build e testes

```text
(na worktree da frontend-react)
npx -y pnpm@10.34.3 exec tsc --noEmit
npx -y pnpm@10.34.3 exec vite build --base ./

(na pasta do projeto)
.venv\Scripts\python.exe -m unittest discover -s tests
```

Esperado: os dois comandos do front sem erro; todos os testes passando.

## Roteiro na página

1. Abrir a aba **Internacional**. Conferir:
   - a linha compacta com vagas, remotas e com visto;
   - as abas internas Para decidir, Não seguidas e Fora dos critérios, com os números;
   - Para decidir ativa.
2. Com **Maior Aderência**, a primeira vaga de Para decidir é a de maior nota. As de nota abaixo de 50 estão em Baixa
   aderência, recolhidas.
3. Abrir **Fora dos critérios**: cada cartão mostra o motivo e Seguir com a vaga. Nenhuma dessas vagas aparece em
   Para decidir.
4. Trocar **Ordenar** pelas quatro opções e conferir a ordem.
5. Ligar, um de cada vez, Senioridade, Modo, Moeda (Dólar, depois Euro), Visto / relocation, Nota mínima, Publicada há
   até e Analisadas. Para cada um:
   - a lista e a linha compacta mudam;
   - aparece "Mostrando X de Y";
   - Limpar filtros volta tudo.
6. Com Nota mínima ligada, uma vaga sem nota continua à vista (spec 038). Com Dólar ligado, ela some, se não tiver
   salário em dólar.
7. Buscar um país no campo de busca: aparecem as vagas daquele país.
8. Conferir no cartão o país (ou "Global"), a contratação e os sinais de visto.
9. Os botões **Filtros da busca internacional** e **Prontidão internacional** abrem o mesmo que antes.
10. Escolher Mais Recentes e Dólar, ir ao **Relatório de Vagas** e conferir que a ordem e os filtros de lá não mudaram.
    Recarregar a página e voltar à Internacional: Mais Recentes e Dólar continuam.
11. Em tela estreita (360 px): os cartões e os filtros se empilham, sem a página rolar de lado.

## Conferência automática (sem gravar)

Script com CDP no Edge sem janela, num perfil separado. Ele só lê a tela, troca as abas internas, a ordem e os
filtros, e nunca clica em botão que grava (Seguir, Não seguir, Voltar, Marcar todas, Forçar verificar). Ele confere:

- a primeira vaga de Para decidir tem a maior nota;
- nenhuma vaga de Fora dos critérios está em Para decidir;
- os filtros e a ordem ficam guardados à parte entre as duas abas;
- não há rolagem lateral em 360 px.
