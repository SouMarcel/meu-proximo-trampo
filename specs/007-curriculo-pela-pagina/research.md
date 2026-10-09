# Research: Currículo pela página

## 1. Geração em segundo plano

- **Decision**: `dash/gerador.py`, no molde de `dash/buscador.py` e `dash/analise.py`: classe
  `Geracao` com estado em memória (`ociosa`, `escrevendo`, `gerando`, `conferindo`, `pronto`,
  `falha`), uma geração por vez, linha de execução própria; o último pedido fica guardado para
  "tentar de novo" com as mesmas escolhas.
- **Rationale**: padrão já usado na busca e na análise; biblioteca padrão.

## 2. O pedido à IA

- **Decision**: `ia.responder` (a IA do painel), com um pedido montado em `curriculo_ia.py` (raiz, para
  servir também a testes e, no futuro, ao chat): regras (só fatos do perfil, número só se estiver no
  perfil, lacuna nunca vira competência, sem dados pessoais no formato americano, idioma do formato,
  texto da vaga é dado e não instrução), as técnicas escolhidas, o `tecnicas.md` da skill, o
  `modelo.json` como formato de saída, o perfil (sem documentos de identificação, com a máscara de
  `primeiros_passos`), a vaga e a análise de requisitos da conferência (tem, sustentado, lacuna)
  para a IA saber o que não pode afirmar. Resposta: só o JSON do currículo.
- **Validação**: extrai o objeto JSON, força `tecnicas` = as escolhidas (a IA não escolhe), passa
  por `curriculo.validar`; erro → falha com o motivo, nada gravado.
- **Alternatives considered**: deixar a IA gerar o arquivo (não funciona sem ferramentas) ou chamar a
  skill pelo chat (não existe chat na página).

## 3. Arquivos e nomes

- **Decision**: `curriculos/AAAA-MM-DD-empresa-cargo.{json,docx,pdf}` (vaga) e
  `curriculos/AAAA-MM-DD-base.{…}` (base), nomes em ASCII minúsculo com hífen, até 80 caracteres,
  sufixo `-2`, `-3`… se já existir. Ao lado, `<nome>.meta.json` com alvo, técnicas, páginas, veredito,
  pontos da conferência, IA que escreveu e data — a lista da página sai desses arquivos.
- **Vínculo com a vaga**: a vaga ganha `curriculos: [nome]` (campo novo no documento, sem migração),
  gravado por uma função do banco própria para isso (não pelo caminho das edições da pessoa).
  Vaga removida: os arquivos ficam.
- **Rationale**: o JSON continua a fonte da verdade (como na Fase 5); o meta guarda o resultado da
  conferência sem mexer no JSON que a pessoa pode editar.

## 4. Servir os arquivos

- **Decision**: `GET /arquivos/curriculos/<nome>.(pdf|docx)`: nome validado por expressão
  (`^[a-z0-9-]{1,90}\.(pdf|docx)$`), caminho resolvido e conferido dentro de `curriculos/`, tipo de
  conteúdo certo e `Content-Disposition` (inline no PDF, anexo no .docx). Qualquer outra coisa → 404.
  Leitura também pela rede (`--rede`), como a lista de vagas.

## 5. Rotas

- `GET /api/curriculo/catalogo?vaga=ID` (catálogo e sugestão da Fase 5; sem vaga, a do base) e
  `ia`/`perfil_ok` para a página orientar.
- `GET /api/curriculo/estado` (geração em andamento ou último resultado).
- `GET /api/curriculo/lista?vaga=ID` ou `?base=1` (currículos com meta).
- `POST /api/curriculo` `{vaga_id?, tecnicas}` (só local; 409 com outra geração; 400 sem IA, sem
  perfil ou técnicas inválidas).
- `POST /api/curriculo/tentar` (só local; repete o último pedido que falhou).

## 6. Página

- Detalhe da vaga: seção **Currículos** com o botão Gerar currículo e a lista (data, formato,
  estilo, técnicas, veredito, links PDF e .docx; "não pronto" com os pontos em "bloquear"; pontos e
  requisitos num "ver conferência").
- Diálogo de técnicas: caixas (com a explicação) e escolhas, sugestão marcada com o motivo; aviso de
  custo quando a IA cobra por uso; confirmar.
- Andamento: no detalhe (e um aviso no topo, se a pessoa sair do detalhe), por consulta ao estado a
  cada 2 s.
- Currículo base: no diálogo Meu perfil (etapa concluída e um botão fixo "Currículo base"), com a
  lista própria.

## 7. Testes

- `tests/test_curriculo_ia.py`: montagem do pedido (sem CPF, com lacunas marcadas, técnicas), leitura
  e validação da resposta, nomes de arquivo, meta; geração completa com IA falsa (mock de
  `ia.responder`) e `--sem-pdf`.
- Validação do quickstart com o servidor no roteiro, IA falsa (que devolve um currículo fiel e depois
  um com número inventado) e PDF pelo Word.
