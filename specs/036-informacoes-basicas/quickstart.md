# Quickstart: validar a spec 036

## Pré-requisitos

- Backend: a branch `036-informacoes-basicas` mesclada na branch pessoal.
- Front: o build da `frontend-react` copiado para `dash/front/`, sem commit.
- O dashboard reiniciado: `python iniciar.py --sem-navegador`, aberto em http://127.0.0.1:8765.

## Automático

```text
python -m unittest discover -s tests          # todos passam, com os testes novos de idiomas
(frontend-react) pnpm exec tsc --noEmit       # sem erro de tipo
(frontend-react) pnpm exec vite build --base ./
```

## Na página

1. **Atualizar candidaturas**:
   - aparecem só Portais, Login guardado e a leitura, mais a linha que aponta Informações básicas;
   - **Abrir** leva ao Meu perfil, já na aba.
2. **Meu perfil → Informações básicas**:
   - mudar o telefone e salvar;
   - gerar uma carta: o telefone novo aparece no cabeçalho;
   - apagar uma resposta guardada: ela some da lista;
   - revogar um site liberado, se houver.
3. **Primeiros passos** (sem perfil, num ambiente de teste): a aba aparece e salva os dados de contato.
4. **Meu perfil → Perguntas → idiomas**:
   - com as respostas antigas em texto livre: cada uma vira uma linha. A sigla do CEFR e "nativo" vêm com o nível
     escolhido; "Professional Working" e parecidos vêm com o nível em branco e "você tinha escrito: …";
   - Próxima com nível em branco: aparece o aviso e a pergunta não avança;
   - repetir um idioma: aparece o aviso de repetição;
   - Outro sem nome: aparece o aviso;
   - escolher Inglês B2, Português (BR) Nativo e Outro "Italiano" A2, depois Próxima: a pergunta seguinte não é mais
     "Qual o seu nível de inglês?";
   - na Revisão, o perfil traz "Inglês — B2 (Intermediário superior)", "Português (BR) — Nativo" e
     "Italiano — A2 (Básico)", e não traz "Inglês (nível declarado)".
5. **Análises → Prontidão para vagas de fora**: o inglês aparece pronto, com a linha nova.
6. **Carta sem dados de contato** (num ambiente de teste): o aviso aponta Meu perfil → Informações básicas.
7. **Tema escuro e celular**: a aba e as linhas de idioma ficam legíveis e as linhas quebram sem rolagem lateral.

## Antes da entrega

- `git checkout -- dash/front` na branch pessoal e apagar os assets novos.
- Procurar dados pessoais no diff que vai para a `master`.
