# Research: Currículo com técnicas

## 1. Catálogo único das técnicas

- **Decision**: `TECNICAS` e `ESCOLHAS` em `curriculo.py` (nome, explicação, padrão), expostos por
  `python curriculo.py --tecnicas [--vaga-id ID]` em JSON, com a sugestão para o alvo. A skill lê
  esse catálogo para montar as caixas de marcar; a página da Fase 6 vai usar a mesma função.
- **Rationale**: FR-014 (uma fonte só); o `curriculo.py` já é a porta de geração.

## 2. Onde ficam as escolhas

- **Decision**: no JSON do currículo, chave `tecnicas`:
  `{"ats", "foco", "xyz", "resultado_primeiro", "competencias_primeiro": bool, "paginas": 1|2,
  "formato": "br"|"us"|"eu", "estilo": "padrao"|"compacto"|"executivo"}`, mais a seção opcional
  `destaques` (até 3 itens, para foco). O JSON continua a fonte da verdade (FR-006); o `.docx` leva
  as técnicas nas propriedades do documento (comentários).
- **Compatibilidade**: sem `tecnicas`, o motor gera como hoje (FR-013, SC-006): A4, `idioma` do
  JSON, estilo atual, aviso acima de 2 páginas.

## 3. Formato e estilo no motor

- **Decision**: `formato` define papel e idioma dos títulos (`br`: A4 + pt; `us`: Letter
  21,59 × 27,94 cm + en; `eu`: A4 + en), e `LARGURA_TEXTO` passa a vir do papel e das margens. No
  `us`, `validar` recusa campos de dados pessoais (`foto`, `nascimento`, `estado_civil`,
  `nacionalidade`, `documentos`) e a conferência aponta esses dados no contato. `estilo` é um
  conjunto de valores (margens, fonte do corpo, espaçamentos, tamanho do nome): `padrao` = os de
  hoje; `compacto` = margens e espaços menores, corpo 10 pt; `executivo` = corpo 10,5 pt, mais
  respiro. Nunca abaixo de 10 pt no corpo (FR-004).
- **Ordem**: `competencias_primeiro` coloca Competências antes de Experiência quando o JSON não traz
  `ordem` própria; `destaques` entra logo depois do resumo.

## 4. Limite de páginas

- **Decision**: com `paginas`, depois do PDF o motor compara as páginas com o limite; acima dele,
  sai com código 3 e a mensagem "deu N páginas; o limite é M", com sugestões de corte (as
  experiências mais antigas, os itens além de 5 por cargo, cursos antigos). Sem PDF, "páginas não
  medidas" (aviso, código 0).

## 5. Conferência sem IA (`conferir.py`, novo)

- **ATS** (no `.docx` gerado e no JSON): seções com títulos do catálogo; contato no corpo (não em
  cabeçalho ou rodapé); sem tabelas, imagens, caixas de texto ou mais de uma coluna; fonte comum
  (Calibri, Arial, Helvetica, Times New Roman, Georgia, Garamond, Cambria, Verdana); no `us`, sem
  dados pessoais. Com vaga, cobertura das palavras-chave (termos dos requisitos que aparecem no
  currículo, em %).
- **Requisitos × perfil**: o texto da vaga é dividido em linhas de requisito pelos cabeçalhos
  comuns em PT e EN (Requisitos, Qualificações, O que buscamos, Desejável, Requirements,
  Qualifications, Must have, Nice to have…); sem cabeçalho, as linhas com marcador. Cada requisito
  vira termos significativos (sem palavras vazias); **tem** = todos os termos principais no perfil;
  **sustentado** = parte deles, ou um equivalente de uma tabela pequena de famílias (ex.: Jira ~
  Azure Boards; Power BI ~ Tableau ~ Looker; Scrum ~ ágil); **lacuna** = nenhum. Lacuna cujo termo
  aparece em Competências do currículo → ponto de "bloquear".
- **Fatos**: números do currículo (percentuais, valores com R$/US$/€/mil/k/M/bi, "N vezes"/"Nx",
  número + substantivo) normalizados ("1,5 mil" = "1.500" = "1500"; "30%" = "30 %") e procurados no
  perfil → ausente = **bloquear**; empresas e cargos da experiência que não aparecem no perfil →
  **conferir**; datas (mês/ano) que não batem com o perfil → **conferir**.
- **Veredito**: bloquear > conferir > ok.
- **Rationale**: sem IA (constituição III); regras explicáveis, cada ponto com trecho e motivo
  (FR-007).
- **Uso**: `python conferir.py curriculos/x.json [--vaga arquivo.txt | --vaga-id ID] [--perfil
  caminho]` (texto ou `--json`); `curriculo.py` roda a conferência no fim quando há perfil e diz o
  veredito. Códigos: 0 ok, 1 conferir, 3 bloquear.

## 6. Sugestão das escolhas

- **Decision**: `sugerir(vaga)`: sem vaga → `br`, `padrao`, 2 páginas, ATS marcado; vaga com local
  nos Estados Unidos ou texto majoritariamente em inglês e local fora da Europa → `us`; local num
  país europeu → `eu`. Idioma pela proporção de palavras comuns de PT e EN (sem IA).

## 7. Skill de chat

- **Decision**: `gerar-curriculo` ganha o passo "Técnicas" (caixas de marcar pela ferramenta de
  opções do assistente, com o catálogo e a sugestão), o arquivo `tecnicas.md` (como escrever cada
  técnica: bullet = ação + escopo + ferramenta + resultado; XYZ só com número confirmado; foco e
  destaques; palavras-chave reformuladas; expressões vazias a evitar) e a conferência obrigatória
  antes de entregar (bloquear = não entrega até resolver). `modelo.json` ganha `tecnicas` e
  `destaques`.

## 8. Testes

- `tests/test_curriculo.py`: gera `.docx` em pasta temporária e confere papel, idioma dos títulos,
  fonte do corpo por estilo, ordem com competências primeiro, destaques, recusa de dados pessoais
  no `us`, e que o JSON sem `tecnicas` gera igual ao de hoje (mesmo XML do documento, sem datas).
- `tests/test_conferir.py`: perfil, vaga e currículo fictícios com número inventado, empresa a mais,
  lacuna em Competências, tabela e contato no cabeçalho; números escritos de jeitos diferentes.
