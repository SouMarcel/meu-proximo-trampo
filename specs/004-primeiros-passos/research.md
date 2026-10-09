# Research: Primeiros passos e anamnese

Sem agentes de pesquisa: as decisões saem do código atual (`ia.py`, `segredos.py`,
`dash/servidor.py`, `filtros.py`, `perfil.exemplo.md`) e de formatos conhecidos.

## 1. Ler os arquivos

- **PDF**: `pypdf` (puro Python, licença BSD), **única dependência nova**, no `requirements.txt` —
  o `iniciar.py` já detecta e instala dependência nova com confirmação. Texto por página; página sem
  texto em todas → "PDF digitalizado: envie outro formato ou cole o texto". Senha → aviso.
- **Word (.docx)**: `python-docx` (já é dependência): parágrafos e tabelas, na ordem. `.doc` antigo
  → aviso para salvar como .docx ou PDF.
- **Exportação do LinkedIn (ZIP)**: `zipfile` + `csv` (biblioteca padrão, `utf-8-sig`). Planilhas
  lidas quando existirem (nomes em inglês, como o LinkedIn exporta): `Profile.csv` (Headline,
  Summary, Geo Location), `Positions.csv` (Company Name, Title, Description, Location, Started On,
  Finished On), `Education.csv` (School Name, Degree Name, Start Date, End Date, Notes),
  `Skills.csv` (Name), `Certifications.csv` (Name, Authority, Started On, Finished On),
  `Languages.csv` (Name, Proficiency). Colunas faltando são ignoradas; o resultado diz quais
  planilhas vieram.
- **Texto colado**: aceito como material do tipo "texto".
- **Alternatives considered**: `pdfminer.six` (mais pesado), PyMuPDF (licença AGPL), mandar o PDF
  direto à IA (cada provedor aceita de um jeito; o Claude Code sem ferramentas não lê arquivos).

## 2. Privacidade antes da IA

- **Decision**: `mascarar_documentos(texto)` troca por `[removido]` CPF (com ou sem pontuação), RG
  (padrões comuns com dígito/X), datas precedidas de "nascimento"/"nasc."/"nascido(a) em" e
  "data de nascimento"; aplicado ao texto de todo material antes de qualquer pedido à IA e antes de
  gravar o perfil. E-mail, telefone e URL do LinkedIn são reconhecidos por expressão regular e
  propostos à parte (campo "Contato"), só gravados se confirmados.

## 3. Rascunho com IA

- **Decision**: `ia.responder` com um pedido que leva o modelo de perfil, os textos mascarados (cada
  um com o nome da fonte) e as regras (só o que está nos materiais; fonte de cada item; conflitos
  em vez de escolher). Resposta: um objeto JSON (extraído do primeiro `{` ao último `}`):
  `{"objetivo": [...], "resumo": [...], "experiencias": [{"cargo", "empresa", "inicio", "fim",
  "itens": [], "fonte"}], "formacao": [...], "certificacoes": [...], "habilidades": [...],
  "idiomas": [...], "conflitos": [{"campo", "opcoes": [{"valor", "fonte"}]}]}`, onde cada item de
  lista é `{"texto", "fonte"}`. Validado e normalizado em Python (campos desconhecidos fora, textos
  com limite).
- **Sem IA**: o rascunho nasce dos campos do ZIP do LinkedIn (se houver) e o resto fica vazio, com o
  texto extraído ao lado.
- **Atualização (perfil existente)**: com IA, o pedido inclui o perfil atual e pede o rascunho
  atualizado; sem IA, a revisão começa do perfil atual.

## 4. Anamnese

- **Decision**: catálogo fixo de perguntas em `primeiros_passos.PERGUNTAS` (id, texto, tipo
  `opcoes`/`multi`/`texto`/`lista`/`sim_nao`, opções, condição, destino), servido à página. Perguntas
  por cargo (maior conquista e como foi medida) geradas para os 3 cargos mais recentes do rascunho.
  Condição `interesse_exterior == sim` libera o bloco do exterior. Número só entra na resposta
  "como foi medida" quando a pessoa digita; sem número, a conquista entra qualitativa.

## 5. Diagnóstico sem IA

- **Decision**: regras determinísticas sobre o rascunho + respostas: experiência sem mês nas datas,
  experiência sem itens, nenhum resultado medido nos últimos cargos, ferramenta sem nível, intervalo
  maior que 6 meses entre empregos, conflito pendente, seção obrigatória vazia (objetivo, cargos-alvo,
  experiência). Cada achado traz a pergunta para completar. Funciona com e sem IA.

## 6. Revisão, gravação e comparação

- **Decision**: o perfil final é Markdown gerado por `montar_perfil(rascunho, respostas)` no formato
  do `perfil.exemplo.md` (com as seções novas opcionais: Contato, Trabalho no exterior, Regras de
  verbo e atribuição) e mostrado num editor de texto para a pessoa ajustar. Gravar: se já existe
  perfil, `difflib` mostra antes o que entra e sai, e a versão anterior vai para
  `anexos/perfis-anteriores/perfil-AAAA-MM-DD-HHMM.md`; gravação atômica.

## 7. Progresso e arquivos

- **Decision**: arquivos em `anexos/primeiros-passos/` (nome saneado, sem sobrescrever); progresso em
  `.cache/primeiros-passos.json` (materiais, rascunho, escolhas de conflito, respostas, etapa),
  ambos fora do Git. Limite de 10 MB por arquivo; pedido de envio em JSON com o conteúdo em base64
  (rota com limite próprio de 15 MB; as outras rotas seguem com 1 MB).

## 8. Filtros propostos

- **Decision**: a partir das respostas: `termos` (cargos-alvo em português; em inglês, os que a
  pessoa informar ou, com IA, sugeridos e marcados como sugestão), `localidade` (cidade/estado),
  `modelos`, `senioridades`, `internacional` (ativo só com interesse; países e cargos em inglês).
  Comparação com `filtros.efetivos(config atual)`; gravação por `filtros.salvar` (que valida).

## 9. Rotas e segurança

- **Decision**: rotas de escrita só do próprio computador (mesmo `_local()` da spec 002) e com as
  proteções atuais; leitura pode ser de qualquer origem permitida. Texto dos materiais é dado, nunca
  instrução (repetido no pedido à IA).

## 10. Skill de chat

- **Decision**: `.agents/skills/analisar-perfil/SKILL.md` (fonte, portátil), sincronizada para
  `.claude/skills/` (entra em `sincronizar_skills.SKILLS`); usa os mesmos comandos:
  `PY primeiros_passos.py extrair <arquivo>` (texto mascarado e campos do ZIP) e
  `PY primeiros_passos.py diagnostico [perfil.md]`; segue o mesmo catálogo de perguntas e as mesmas
  regras; grava `perfil.md` só com confirmação, guardando a versão anterior.
