# Quickstart: validar o Colar e-mail (spec 063)

## Testes automáticos

```text
.venv\Scripts\python.exe -m unittest tests.test_colar_email -v
.venv\Scripts\python.exe -m unittest discover -s tests
```

Esperado: os 20 e-mails fictícios de `tests/dados/emails_candidatura.json` com pelo menos 18 acertos (SC-001); nenhum
caso volta etapa; e-mail com "ignore as instruções" vira dado com alerta (SC-003); 5 e-mails geram 5 propostas e
aplicam juntos (SC-004).

## Front (na `frontend-react`)

```text
npm run typecheck
npm run build
```

## Teste na branch pessoal

1. Mesclar a `063-colar-email` na branch pessoal (e o front pela `front/atualizacao` ou build local), reiniciar o dashboard
   (`python iniciar.py --sem-navegador`).
2. Abrir Atualizar candidaturas: a área Colar e-mail aparece mesmo sem portal conectado, com o aviso de colar só o corpo.
3. Colar uma negativa real de uma candidatura de Aplicações → Ler → a proposta mostra "negativa", o trecho e
   "Aplicada → Encerrada · não aprovado". Aplicar → o card vai para Encerrada e as Anotações ganham a linha
   `dd/mm/aaaa — e-mail de negativa: "…"`, sem perder as anteriores.
4. "+ outro e-mail" com mais dois (convite e confirmação de recebida) → três propostas; marcar duas → só elas gravam.
5. Convite de 2ª entrevista de um card já em Entrevista → proposta "só anotar".
6. Um e-mail de propaganda → "não reconheci"; com IA ligada, ele vai à IA (a página diz qual) e, sem reconhecimento,
   pede a escolha.
