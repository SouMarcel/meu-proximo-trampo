# Data Model: Informações básicas e idiomas com nível

Nenhum arquivo muda de formato. Esta spec muda só o que a pergunta de idiomas mostra e o texto gravado.

## Idioma declarado (uma linha da pergunta)

| Campo | Tipo | Regra |
|---|---|---|
| `idioma` | texto | Uma das `IDIOMAS_PERFIL` (`Inglês`, `Português (BR)`, `Francês`, `Alemão`, `Espanhol`) ou `Outro`. |
| `outro` | texto | Nome do idioma quando `idioma = Outro`, até 60 caracteres. Obrigatório nesse caso. |
| `nivel` | texto | `A1`, `A2`, `B1`, `B2`, `C1`, `C2`, `Nativo` ou vazio (só na conversão de resposta antiga; a página não deixa avançar vazio). |
| `original` | texto | O texto antigo quando a conversão não achou o nível ou o idioma. Só para mostrar; não é gravado. |

**Texto gravado** (item de `respostas.idiomas`): `"{nome do idioma} — {rotulo do nível}"`.
- O nome do idioma é `idioma`, ou `outro` quando a linha é Outro.
- Exemplos: `Inglês — B2 (Intermediário superior)`, `Italiano — A2 (Básico)`, `Português (BR) — Nativo`.

**Regras de conjunto**:
- linha sem idioma e sem nível é ignorada;
- nome repetido (sem acento e sem maiúsculas) bloqueia o avanço;
- até 30 linhas, o limite que `validar_respostas` já aplica.

## Nível (`NIVEIS_IDIOMA`)

| valor | rotulo | descricao |
|---|---|---|
| A1 | A1 (Iniciante) | Frases básicas do cotidiano, apresentações simples |
| A2 | A2 (Básico) | Textos curtos e informações previsíveis |
| B1 | B1 (Intermediário) | Textos claros sobre assuntos familiares |
| B2 | B2 (Intermediário superior) | Textos complexos, inclusive técnicos da própria área |
| C1 | C1 (Avançado) | Textos longos e implícitos, uso flexível do idioma |
| C2 | C2 (Proficiência plena) | Compreende com facilidade praticamente tudo |
| Nativo | Nativo | Língua materna |

## Resposta antiga `respostas.ingles`

- Ela continua no progresso de quem respondeu antes. O id `ingles` segue aceito em `IDS`, mas a pergunta não aparece
  mais.
- Na montagem do perfil, a linha "Inglês (nível declarado)" sai quando `respostas.idiomas` tem uma linha de inglês com
  nível do formato novo.

## Informações básicas

São os mesmos dados de hoje, só mostrados em outro lugar:
- dados de contato (spec 033);
- respostas guardadas (spec 027/035);
- sites conhecidos, liberados e bloqueados (spec 027).
