# Research: Nota sem desperdício de IA

## R1. Onde fica o arquivo de regras

- **Decision:** `.agents/skills/buscar-vagas/regras-da-nota.md`, ao lado da skill.
- **Rationale:** a skill aponta para um arquivo da própria pasta, o que funciona em qualquer assistente que lê
  `.agents/skills/`. O `sincronizar_skills.py` já copia a pasta inteira para `.claude/skills/`, e o código já lê a
  skill desse caminho (`analise.SKILL`).
- **Alternatives:** `dash/regras_nota.md` (a skill teria de apontar para fora da pasta dela, e o Claude Code lê só a
  cópia); manter as regras na skill e recortar menos (continua com duas audiências num texto só, que é o que faz o
  pedido levar texto do chat).

## R2. Regras de portal só para a vaga do portal

- **Decision:** subseções `### <PLATAFORMA>` em `## Portais`, incluídas depois de `## Vagas` só para as plataformas
  do grupo.
- **Rationale:** cerca de 1,5 mil caracteres do texto atual explicam portais que a maioria das vagas não usa; depois de
  `## Vagas`, não quebram o começo idêntico (FR-007). O nome igual ao `PLATAFORMA` da fonte evita uma tabela de
  correspondência.
- **Alternatives:** tudo sempre (gasta em todo pedido); regras de portal no bloco de cada vaga (repete o texto quando o
  grupo tem duas vagas do mesmo portal).

## R3. Como saber que foi limite (429) e quanto esperar

- **Decision:** `IAErro.limite` e `IAErro.espera`, preenchidos em `_postar` a partir do código 429, do cabeçalho
  `Retry-After` (segundos) ou do `retryDelay` do corpo (Gemini); sem nenhum, 60 s; teto de 300 s.
- **Rationale:** hoje o código e os cabeçalhos se perdem na mensagem. Atributos com padrão não quebram quem faz
  `except IAErro` e usa só o texto. O teto evita que uma cota diária ("tente em 20 h") prenda a fila; nesse caso, as
  3 recusas encerram a rodada e as vagas voltam na próxima busca.
- **Alternatives:** procurar "limite de uso" na mensagem (frágil, a mensagem é para pessoas); exceção nova
  `IALimite(IAErro)` (equivalente, mas `responder` junta várias falhas e precisaria decidir a classe da mesma forma).

## R4. Quando todas as IAs falham e só uma foi por limite

- **Decision:** o erro final tem `limite=True` se alguma falha foi por limite.
- **Rationale:** a principal com a chave errada e a reserva no limite: esperar e tentar de novo faz a reserva
  responder. Com as 3 recusas, não há laço infinito.
- **Alternatives:** só quando todas foram por limite (a fila desistiria na primeira vez, num caso que se resolve
  sozinho).

## R5. Forçar em grupo: ler primeiro, mandar depois

- **Decision:** decidido no clarify: a fila lê as descrições até juntar 3 vagas prontas, ou até a fila esvaziar, e faz
  um pedido só.
- **Rationale:** a leitura já é sequencial e com a pausa do portal; juntar não aumenta o tempo total e economiza dois
  envios das regras e do perfil a cada 3 vagas.
- **Alternatives:** juntar só as que já estão prontas; espera máxima de 30 s (não formam grupo no LinkedIn, onde a
  pausa é de 60 s).

## R6. A API do Forçar e a página

- **Decision:** a API não muda: `verificando` = grupo + fila; `verificando_agora` = a vaga lida agora ou a primeira
  do grupo.
- **Rationale:** a página (React, outra branch) mostra "Verificando…" para a atual e "Na fila (posição N)" para as
  outras; com o grupo, as vagas prontas mostram "Na fila", o que é verdade (esperam o pedido). Mudar o front exigiria
  um PR na `frontend-react` sem ganho para a pessoa.
- **Alternatives:** `verificando_agora` como lista (contrato novo e mudança no front).

## R7. Calibração contra a nota gravada

- **Decision:** comparar a nota nova com a gravada, preferindo vagas cuja nota gravada veio do mesmo modelo da IA
  principal de hoje, e mostrar o modelo de cada uma no relatório.
- **Rationale:** é uma rodada só (cerca de 10 pedidos de 3 vagas), barata para as cotas gratuitas. Com o mesmo modelo,
  a diferença mede as regras, não a troca de modelo.
- **Alternatives:** rodar as regras antigas e as novas agora, com a mesma IA (mede melhor, mas dobra o custo e exige
  manter o recorte antigo no código); só comparação manual (descartada no clarify).

### R7, revisto na calibração (26/11)

Comparar com a nota gravada não serviu: a IA principal era o Claude Code, e as notas gravadas vinham de IAs gratuitas
(22 de 30 do `openrouter/free`, que sorteia o modelo). Resultado: 46,7% dentro de 10 pontos, média −7,5, com o Claude
mais rigoroso (−10 contra o `openrouter/free`, +5,75 contra o Gemini). A comparação justa, regras antigas x novas no
mesmo Claude e nas mesmas 30 vagas, deu 100% dentro de 10 pontos (média +0,8); o Claude contra ele mesmo, em duas
rodadas, também 100% (média −0,5). As 5 trocas de fora/dentro têm motivo na vaga: 4 vagas presenciais no exterior
(Lisboa, Hyderabad, França, Suécia), que as regras novas marcam fora com o perfil "Aceita morar fora: não" (as
antigas marcavam uma vaga de Lisboa fora e outra não), e 1 vaga em Pune sem modelo na descrição, que as novas deixam
dentro com o alerta "confirmar se aceita remoto do Brasil". Pela SC-002: passa. Daí o modo `--antes REF` do comando.

## R8. Tirar a seção Contato

- **Decision:** cortar do título `## Contato` até o próximo `## ` (ou o fim), só no pedido de nota.
- **Rationale:** é o título que `primeiros_passos.py` grava (`L += ["", "## Contato", ...]`); um perfil escrito à mão
  sem esse título vai como está (caso de borda da spec), sem caçar e-mail ou telefone no texto.
- **Alternatives:** expressão regular para e-mail e telefone em todo o perfil (pode apagar fatos, como um número de
  conquista).
