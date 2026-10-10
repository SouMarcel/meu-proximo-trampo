# Research: Análise de perfil contínua

## 1. Lacunas das vagas (sem IA)

- **Fontes por vaga**: as `lacunas` da análise (texto da IA, spec 002) e os requisitos do anúncio marcados como
  `lacuna` pela conferência de requisitos que já existe (`conferir.conferir_requisitos`, spec 006, contra o perfil
  atual). Vagas sem análise entram só pelos requisitos.
- **Agrupamento**: cada lacuna vira o conjunto dos seus termos significativos (`conferir.termos`) menos uma lista de
  palavras genéricas PT/EN ("experiência", "conhecimento", "anos", "sólida", "experience", "strong", "knowledge",
  "years"…). Lacunas que compartilham um termo distintivo ficam no mesmo grupo (união por termo); o rótulo é o termo
  mais frequente do grupo, e um exemplo literal acompanha. A mesma vaga conta uma vez por grupo.
- **Peso da vaga**: `aderência/100` (50 quando não há nota) × 1,5 se a pessoa seguiu (triagem "seguir" ou no quadro)
  × 0,5 se fora dos critérios ou "não seguir". Peso do grupo = soma dos pesos das vagas em que aparece.
- **Níveis**: parte do peso total das vagas da visão: crítica ≥ 50%, alta 25–50%, média 10–25%; abaixo, fora.
- **Visões**: "seguidas" (triagem "seguir" ou com etapa) e "todas". Mínimo de 5 vagas analisadas na visão.
- **Rationale**: tudo calculável sem IA, reaproveitando a conferência de requisitos; o peso segue o pedido desta
  fase (vagas que a pessoa quase atende pesam mais).

## 2. Plano de estudo e cargos-alvo (com IA)

- Pedidos curtos à IA escolhida (`ia.responder`), só no clique, com o perfil (sem documentos de identificação) e,
  no plano, as lacunas do topo. Texto do perfil e das vagas é dado, nunca instrução.
- **Cargos-alvo**: JSON `[{titulo, titulo_en, tipo: lateral|degrau|vizinho, evidencia, lacuna}]`, de 5 a 10;
  `evidencia` precisa aparecer no perfil (comparação sem acento e sem pontuação, por termos): sem isso, o cargo fica
  marcado "conferir"; tipo fora das opções ou título repetido, descartado.
- **Plano de estudo**: JSON `[{lacuna, passos: [até 3], tempo_estimado_semanas}]` para até 5 lacunas; o pedido
  proíbe afirmar experiência e manda usar só o que o perfil diz como ponto de partida.

## 3. Levar cargos para os filtros

- Reaproveita `curriculo_base.montar_filtros` (spec 011): entra a lista de cargos (os atuais mais os escolhidos, sem
  repetir), o resto dos filtros fica igual; a página mostra o que muda (`mudancas`) e grava com `filtros.salvar`
  só depois da confirmação.

## 4. Prontidão internacional (sem IA)

| Item | De onde vem | Pronto quando |
|---|---|---|
| Inglês | linha de idiomas do perfil ("Inglês — avançado", "English — fluent") | nível intermediário ou mais |
| Fuso | `internacional.fuso_horas` | informado (> 0) |
| Contratação | `internacional.contratacao` | ao menos uma forma |
| Passaporte e autorização | `internacional.passaporte`, `autorizacao_trabalho` | passaporte marcado (autorização é informativa) |
| Currículo em inglês | seu currículo em inglês (spec 011) ou currículo gerado em formato us/eu (spec 006/007) | existe |
| LinkedIn em inglês | marcação da pessoa | marcado |

Cada item com `situacao` (pronto, falta, nao_informado), `origem` e `acao` (abrir o painel internacional, gerar o
currículo, abrir Meu perfil).

## 5. Onde fica

- `dash/dados/analises-perfil.json` (pasta de dados, fora do Git): a última análise de cada tipo com a data e as
  marcações da pessoa (LinkedIn em inglês). Gravado atômico.
- Módulo `analise_perfil.py` (raiz), rotas `/api/analises-perfil…` no servidor, passo "Análises" em Meu perfil e
  linha de comando para a skill.

## 6. Testes

- `tests/test_analise_perfil.py`: agrupamento de variações, peso e níveis (SC-001), mínimo de 5 (SC-002), visões,
  cargos com evidência inventada marcados (SC-003, IA falsa), levar para os filtros sem gravar antes (SC-004),
  prontidão com perfil e filtros de teste (SC-005), salvar e ler.
