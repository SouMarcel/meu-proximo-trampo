# Quickstart: verificar a vaga publicada em post

Pré-requisitos:
- Windows;
- `.venv` pronto e servidor do dashboard rodando a partir da worktree da 016, numa porta de teste (o servidor da
  branch pessoal continua na 8765);
- uma IA configurada (ex.: OpenRouter `:free`) para os cenários com IA.

## Testes automáticos

```text
.venv\Scripts\python.exe -m unittest discover -s tests
```

Esperado: todos passam, incluindo `tests/test_post.py` (formatos de link, leitura do HTML fictício, bloqueios sem
espera, extração com IA falsa, gravação e edição do e-mail).

## Cenários na página

1. **Link de post com IA** (US1, SC-001, SC-005): Adicionar Vaga → colar o link de um post público com vaga →
   Buscar dados.
   - Aparece "Em análise pela IA (provedor · modelo), aguarde…".
   - O formulário abre já preenchido: cargo, empresa, e-mail, assunto, descrição e link.
   - Adicionar: a vaga aparece no Relatório com a etiqueta Post e a análise de aderência começa.
2. **Mesmo post de novo** (US1-6): colar o mesmo link. Aparece "Essa vaga já estava no dashboard…", sem pedido ao
   LinkedIn.
3. **Erro da IA** (US4-2, SC-005): no painel IA, colocar um modelo que não existe e repetir o cenário 1 com outro
   post. Depois do "aguarde…", o formulário abre como sem IA, com o motivo do erro. Depois, voltar o modelo.
4. **Sem IA** (US4-1, SC-004): no painel IA, escolher "Sem IA" e repetir o cenário 1 com outro post. O formulário
   abre com a descrição, o link e a empresa (se for página), e o aviso. Depois, voltar a IA.
5. **Colar texto** (US3): "Colar texto de post ou mensagem" → colar um texto com e-mail e link → Continuar. O
   formulário tem o link no campo de link e o e-mail no campo de e-mail.
6. **E-mail no cartão** (US2, SC-006): abrir o cartão de uma vaga antiga, preencher e-mail e assunto e salvar.
   - Recarregar: os dois continuam lá, e "Enviar por e-mail" abre o programa de e-mail com destinatário e assunto.
   - Um e-mail inválido mostra o aviso e não salva.
   - O kit mostra "Candidatura por e-mail".
7. **Link de vaga comum** (SC-007): colar um link de vaga do LinkedIn (`/jobs/view/…`) e um da Gupy. O comportamento
   é igual ao de antes.
8. **Formato share/ugcPost** (research §2): com o OK da pessoa, um pedido com um link real nesse formato.

## Verificação sem rede

O bloqueio (429/999/login) e o post privado (404) são verificados só nos testes, com o abridor falso. Neles, nenhum
arquivo de espera é criado.
