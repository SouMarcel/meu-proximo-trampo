# Lista de paridade (FR-020)

Cada função do dashboard atual (`dash/dashboard.html`), onde ela fica na página nova e se foi conferida em uso real.
A troca (História 7) só é proposta com todas as linhas marcadas. "H" é a história que entrega a linha.

Situação hoje: ✅ funciona com dados reais na página nova · ⚠️ existe, mas simulada · ❌ não existe.

## Cabeçalho e geral

| Função no dashboard atual | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Aviso de servidor parado e reconexão sozinha | Faixa no topo; modo demonstração na abertura | 1 | ✅ | [ ] |
| Tema (sistema → claro → escuro) | Botão no cabeçalho | 1 | ✅ (H1) | [ ] |
| Meu perfil | Cabeçalho → Meu perfil | 3 | ⚠️ | [ ] |
| IA (escolher, testar, remover chave) | Cabeçalho → IA | 2 | ⚠️ | [ ] |
| Adicionar vaga | Cabeçalho e quadro | 1 | ✅ | [ ] |
| Atualizar candidaturas | Cabeçalho → Contas conectadas | 6 | ⚠️ | [ ] |
| Apoie o projeto (link externo) | Cabeçalho | 1 | ✅ | [ ] |
| Só leitura de outro aparelho (botões desligados) | Todas as telas | 1–6 | ✅ nas telas da H1 | [ ] |

## Relatório de Vagas e Internacional

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Sub-abas Para decidir / Não seguidas / Fora dos critérios (Seguidas ficou fora de propósito: as seguidas estão no quadro) | Relatório | — | ✅ | [ ] |
| Ordenar por; filtros de senioridade, modelo, plataforma, aderência; Limpar filtros | Relatório | — | ✅ | [ ] |
| Linha da última busca | Topo do Relatório | 1 | ✅ | [ ] |
| Buscar vagas (diálogo com plano, avisos de busca recente e espera, confirmação) | Cabeçalho | 1 | ✅ | [ ] |
| Andamento da busca, Cancelar | Relatório | 1 | ✅ | [ ] |
| Tentar a nota de novo (falha da análise automática) | Relatório | 1 | ✅ | [ ] |
| Completar descrições | Relatório | 1 | ✅ | [ ] |
| Seguir com a vaga, Não seguir, Voltar para triagem | Relatório | 1 | ✅ (Voltar para triagem entrou na H1) | [ ] |
| Marcar todas como não seguidas (dois cliques) | Relatório | 1 | ✅ | [ ] |
| Forçar verificar / Verificando… | Relatório | — | ✅ | [ ] |
| Motivo de "Fora dos critérios" | Relatório | — | ✅ | [ ] |
| Filtros da busca internacional; Abrir o painel internacional (prontidão) | Internacional | 2, 3 | ⚠️ | [ ] |

## Quadro

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Colunas Salva → Encerrada; arrastar; menu ⋯; seletor de etapa | Quadro | — | ✅ | [ ] |
| Resultado (Não aprovado, Desisti, Vaga cancelada, Contratado) | Quadro e detalhe | — | ✅ | [ ] |
| Remover do quadro (dois cliques) | Quadro e detalhe | 1 | ✅ (o segundo clique entrou na H1) | [ ] |
| Preparar entrevista no cartão em Entrevista | Quadro | 5 | ⚠️ | [ ] |
| Lembrete de follow-up no cartão (Feito, Dispensar, Parar lembretes) | Quadro e detalhe | 4 | ❌ | [ ] |

## Detalhe da vaga

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Nota, resumo, Encaixe, Lacunas, Atenção, sinais, autorização, inglês, contratação, fuso, riscos | Detalhe | 1 | ✅ | [ ] |
| Descrição com markdown mínimo, como texto | Detalhe | 1 | ✅ | [ ] |
| Anotação, e-mail e assunto da candidatura (Salvar) | Detalhe | 1 | ✅ (e-mail e assunto entraram na H1) | [ ] |
| Data da entrevista | Detalhe | — | ✅ | [ ] |
| Candidatar no … (só abre o portal); Enviar por e-mail (`mailto:`) | Detalhe | 1, 4 | ✅ Abrir a vaga e Enviar por e-mail; ⚠️ rótulo "Candidatar no …" na H4 | [ ] |
| O que esta candidatura pede (checklist, acrescentar e remover item, currículo base) | Detalhe | 4 | ⚠️ | [ ] |
| Gerar currículo (técnicas, opções, aviso de IA), andamento, Tentar de novo | Detalhe | 4 | ❌ | [ ] |
| Ver currículos (PDF, DOCX, conferência, cortes sugeridos) | Detalhe | 4 | ❌ | [ ] |
| Carta ou mensagem (Escrever, Copiar) | Detalhe | 4 | ❌ | [ ] |
| Respostas de formulário (Preparar respostas, sensíveis, Escrever a minha, Salvar) | Detalhe | 4 | ❌ | [ ] |
| Ver análise e anotações | Detalhe | — | ✅ | [ ] |

## Adicionar vaga

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Por link (vaga, post do LinkedIn); link ilegível abre o formulário preenchido | Diálogo | 1 | ✅ | [ ] |
| Colar texto de post ou mensagem → Preencher com IA → conferir → Adicionar | Diálogo | 1 | ✅ | [ ] |
| Preencher à mão; destino Relatório ou etapa do quadro | Diálogo | 1 | ✅ | [ ] |
| Aviso quando a vaga cai em Fora dos critérios | Diálogo | 1 | ✅ | [ ] |

## Filtros e IA

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Cargos, Localidade, Modo de trabalho, Senioridade, Tipo de emprego, Data de publicação, Idiomas aceitos, Moedas aceitas, Empresas a excluir, Portais | Filtros da busca | 2 | ⚠️ | [ ] |
| Internacional: países, regiões, salário e fuso, contratação aceita, fontes do exterior, empresas que você acompanha, frases | Filtros internacionais | 2 | ⚠️ | [ ] |
| Provedor, modelo, chave (4 últimos), Testar conexão, Remover, o que é enviado | IA | 2 | ⚠️ | [ ] |

## Meu perfil

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Primeiros passos: materiais (arquivo e texto), rascunho com e sem IA, conflitos, anamnese, diagnóstico, revisão (Ver o que muda), Gravar | Meu perfil | 3 | ⚠️ | [ ] |
| Contato no perfil e link do LinkedIn | Meu perfil | 3 | ⚠️ | [ ] |
| Filtros propostos (Confirmar e gravar nos filtros, Pular), cargos em inglês com IA | Meu perfil | 3 | ⚠️ | [ ] |
| Já tenho currículo: currículos da pasta anexos, proposta, Usar este currículo | Meu perfil | 3 | ❌ | [ ] |
| Seu currículo (pt e en): marcar e trocar | Meu perfil | 3 | ❌ | [ ] |
| Recomeçar / Atualizar o perfil | Meu perfil | 3 | ⚠️ | [ ] |
| Análises: lacunas das vagas, prontidão internacional, carreiras e cargos-alvo (levar para os filtros), plano de estudo | Meu perfil → Análises | 3 | ❌ | [ ] |
| Currículo base (gerar e ver) | Meu perfil | 4 | ❌ | [ ] |

## Preparar entrevista

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Dossiê, Sobre a empresa (Salvar o texto), Resumo com IA | Entrevista | 5 | ⚠️ | [ ] |
| Perguntas prováveis, Mais perguntas com IA | Entrevista | 5 | ⚠️ | [ ] |
| Suas histórias: editar, Salvar esta história, Remover (dois cliques), rascunhos da IA não salvos | Entrevista | 5 | ⚠️ | [ ] |
| Simulação pt/en com retorno | Entrevista | 5 | ⚠️ | [ ] |
| Salário (sem valores inventados) | Entrevista | 5 | ⚠️ | [ ] |
| Como foi a entrevista (Salvar anotação); entrevistas anteriores | Entrevista | 5 | ❌ | [ ] |

## Contas conectadas

| Função | Na página nova | H | Hoje | Conferido |
|---|---|---|---|---|
| Conectar, Pronto, Desconectar (Gupy, Indeed) | Contas | 6 | ⚠️ | [ ] |
| Atualizar agora / Ler de novo, andamento | Contas | 6 | ⚠️ | [ ] |
| Proposta com itens marcados; Aplicar; Importar como histórico | Contas | 6 | ⚠️ | [ ] |
