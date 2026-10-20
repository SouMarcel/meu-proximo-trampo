# Quickstart: conferir cada entrega do front único

## Preparação (uma vez)

- Worktree do front: `git worktree add --track -b frontend-react <pasta> origin/frontend-react`.
- Na pasta do front: `npx -y pnpm@10.34.3 install --frozen-lockfile`.
- Servidor da ferramenta rodando na `marcel`: `python iniciar.py` (ou `dash/servidor.py --sem-navegador`).

## Portões de cada entrega (antes de mostrar à pessoa)

Na pasta do front:

1. `npx -y pnpm@10.34.3 exec tsc --noEmit` → sem erros.
2. `npx -y pnpm@10.34.3 exec vite build --base ./` → `dist/` montado.
3. `grep -rn "dangerouslySetInnerHTML\|innerHTML" src` → nada.
4. `grep -rn "localStorage" src` → só em `services/storage.ts`, com as chaves `mpt_pref_*`.
5. `grep -rln "mockData" src` → só no modo demonstração (`App.tsx` e `services/mockData.ts`).

Na `master` (worktree da spec): `python -m unittest discover -s tests` → tudo passa.

## Teste da pessoa na `marcel`

1. Copiar o `dist/` do front para `dash/front/` da `marcel`. É só cópia local, sem commit.
2. Reiniciar o servidor e abrir `http://127.0.0.1:8765/novo/`.
3. Seguir o roteiro da história (abaixo) e marcar as linhas dela na [lista de paridade](contracts/paridade.md).
4. Com o OK:
   - `git checkout -- dash/front` na `marcel`;
   - push da `frontend-react`;
   - `gh workflow run front.yml`;
   - revisar o PR `front/atualizacao`, fazer o merge e rodar `git merge master` na `marcel`.

## Roteiros por história

| H | Roteiro | Resultado esperado |
|---|---|---|
| 1 | Buscar vagas → ver o plano → confirmar → acompanhar → Cancelar uma segunda busca; Completar descrições; Adicionar vaga por link, por post e por texto colado | Vagas e busca aparecem também em `/`; aviso de busca recente; IA só preenche o formulário |
| 1 | Parar o servidor com a página aberta; voltar com ele | Faixa "servidor fora do ar" e reconexão sozinha; na abertura sem servidor, modo demonstração com aviso fixo e botões de gravar desligados |
| 2 | Mudar cargo, cidade e um filtro internacional; salvar; recarregar | Mantido; "híbrido sem cidade" mostra o erro do servidor |
| 2 | IA: trocar o modelo, testar, salvar, recarregar | Só os 4 últimos caracteres da chave; nada da chave no `localStorage` (DevTools → Application) |
| 3 | Meu perfil → Atualizar o perfil com o próprio currículo → rascunho → anamnese → revisão → Ver o que muda → gravar (ou parar antes de gravar, se a pessoa preferir) | `perfil.md` atualizado; a versão anterior guardada |
| 3 | Análises: lacunas e cargos-alvo → levar aos filtros | Proposta antes de gravar; aviso de custo da IA |
| 4 | Vaga seguida → Gerar currículo → abrir PDF e DOCX; carta; respostas com uma pergunta de salário | Arquivos abrem; a pergunta de salário volta sem resposta da IA |
| 4 | Lembrete numa vaga em Aplicação Enviada há 7 dias → Feito | Lembrete some, também em `/` |
| 5 | Vaga em Entrevista → Preparar entrevista → salvar texto da empresa, história e anotação | Também em `/`; rascunhos da IA não aparecem salvos |
| 6 | Conectar o Indeed → login na janela → Pronto → Atualizar agora → desmarcar um item → Aplicar | Só os marcados mudam no quadro |
| — | Abrir `/novo/` de outro aparelho (servidor com `--rede`) | Botões que gravam desligados com o motivo |
| 7 | Depois da troca: `python iniciar.py`, atalho `abrir-dashboard`, `/`, `/novo/`, `/novo/assets/...` | Todos levam à página nova; `python -m unittest` passa |
