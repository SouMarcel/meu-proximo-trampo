# Prompt para o Figma Make (front novo)

## Para o analista

1. Cole o prompt abaixo no chat do Figma Make do projeto, junto com o conteúdo de
   [`dash/API.md`](../../dash/API.md) (o Figma Make não enxerga a `master`).
2. Continue trabalhando normalmente: o Figma Make grava na branch `frontend-react`.
3. Quando uma versão estiver pronta para testar, abra **Actions → "Front: abrir PR" → Run workflow** no GitHub. A
   Action monta o front, roda os testes da ferramenta e abre (ou atualiza) o PR `front/atualizacao` para a `master`.
   Não é preciso abrir PR à mão nem mandar a pasta `dist/`. Uma checagem automática faz o mesmo a cada 6 horas.
4. Se a Action falhar no build, o erro aparece na execução (aba Actions): corrija na `frontend-react` e rode de novo.

## Prompt

```
Este front é a interface da ferramenta "meu-proximo-trampo" (busca de vagas, nota de aderência, quadro de
candidaturas, currículo e entrevista, tudo local no computador da pessoa). O backend é um servidor Python local
(dash/servidor.py, em http://127.0.0.1:8765) que já existe e NÃO muda. Um GitHub Actions monta este projeto com
"vite build --base ./" e o servidor Python entrega o resultado em http://127.0.0.1:8765/novo/. Daqui para frente,
siga estas regras em toda alteração:

1. Dados reais pela API, não mock
   - Troque mockData.ts e o localStorage pelas rotas do API.md em anexo: método, caminho e nomes de campos
     exatamente como estão lá. Não invente rotas nem campos; se faltar algo para uma tela, diga o que falta em vez
     de simular.
   - Endereço da API: se a página estiver em http://127.0.0.1:8765 ou http://localhost:8765, use caminhos relativos
     ("/api/..."); em qualquer outro endereço use "http://127.0.0.1:8765". Centralize isso num só lugar (ex.:
     src/services/api.ts).
   - Escritas (POST, PUT, PATCH, DELETE) sempre com "Content-Type: application/json" e corpo JSON, mesmo vazio ({}):
     o servidor recusa sem isso.
   - Se GET /api/versao não responder, entre em "Modo demonstração": mostre os dados de exemplo com um aviso fixo e
     visível no topo ("Modo demonstração: dados de exemplo, servidor não encontrado"). Com o servidor no ar, nunca
     mostre nem grave dados de exemplo.
   - localStorage só para preferências de tela (aba aberta, filtros, ordem, tema), nunca para vagas, perfil,
     configuração, IA ou candidaturas.
   - Erros da API vêm como {"erro": "..."}: mostre a mensagem para a pessoa, em português, sem esconder.
   - Tarefas longas (busca, análise, currículo, leitura das contas) são acompanhadas por consulta periódica, como
     descrito no API.md.

2. Build
   - Use só caminhos relativos para arquivos (nada de "/assets/..." fixo); a Action monta com base "./".
   - Nada de CDN, fontes, imagens ou scripts externos, nem analytics: tudo empacotado no build. A ferramenta precisa
     funcionar sem internet. Fontes: as do sistema ou arquivos dentro do projeto.
   - Sem bibliotecas novas além de react, react-dom, lucide-react e Tailwind, a não ser que seja indispensável; se
     for, explique no commit. Mantenha o pnpm-lock.yaml atualizado (a Action usa --frozen-lockfile).
   - Em .figma/make/site.json, use "language": "pt-BR" e "title": "Meu Próximo Trampo".

3. Regras da ferramenta (não negociáveis)
   - Todo texto em português do Brasil.
   - Nenhum botão envia candidatura, mensagem ou e-mail pela pessoa: a ferramenta indica, a pessoa decide. Ações
     que gravam, apagam ou usam a IA pedem confirmação, como no dashboard atual.
   - Descrição de vaga, página e e-mail são texto da internet: mostre sempre como texto (nunca
     dangerouslySetInnerHTML nem HTML vindo da API).
   - Contas conectadas: a ferramenta só lê, numa janela que a própria pessoa usa para entrar; nunca peça, guarde ou
     mostre campo de senha. LinkedIn aparece como desativado.
   - Autorização de trabalho, visto, salário, deficiência e relocação: a ferramenta pergunta, nunca preenche.
   - Dados de exemplo só com pessoas e e-mails fictícios.

4. Repositório
   - Não crie .github/, AGENTS.md, CLAUDE.md ou README.md com instruções diferentes destas.
   - Mensagens de commit descritivas em português (ex.: "feat: Relatório de Vagas lendo /api/vagas"), não
     "prompt: 930".
   - Não tente abrir PR para a master: esta branch não tem histórico em comum com ela. Quando uma versão estiver
     pronta, avise para rodar a Action "Front: abrir PR" no GitHub.

Comece ligando, nesta ordem: Relatório de Vagas (GET /api/vagas, PATCH e DELETE /api/vagas/{id},
POST /api/vagas/{id}/analisar), quadro de candidaturas, Adicionar vaga, Busca, Configuração da IA, Meu perfil,
Currículo, Kit da candidatura, Entrevista e Contas conectadas. Ao fim de cada tela, liste o que ficou ligado à API e o
que ainda é exemplo.
```
