# Contrato das telas: o que cada tela chama e que regra segue

As rotas, os corpos e as respostas estão no `dash/API.md`; aqui fica só o mapa tela → rotas → regras.
Legenda das regras (seção 4 do `dash/API.md`):
- **C**: confirmar antes de gravar ou apagar;
- **IA**: só no clique, com o aviso de custo; sem IA, leva ao painel IA;
- **E**: nada é enviado em nome da pessoa;
- **S**: perguntas sensíveis são da pessoa;
- **L**: só leitura de outro aparelho;
- **T**: texto da internet aparece como texto;
- **P**: respeito aos portais.

| Tela (componente) | Rotas | Consulta periódica | Regras |
|---|---|---|---|
| App (abertura) | `GET /api/vagas`, `/api/buscas/ultima`, `/api/ia`, `/api/config`, `/api/busca`, `/api/busca/plano`, `/api/curriculo/estado`, `/api/perfil/estado` (sem perfil, abre os primeiros passos uma vez por sessão), depois `/api/busca/pendentes` | `/api/versao` 4 s | — |
| Relatório (`TriageReport`) | `PATCH /api/vagas/{id}`, `POST /api/vagas/{id}/analisar`, `GET /api/buscas/ultima` | — | C (marcar todas), T, L |
| Buscar vagas (`SearchJobsModal`) | `GET /api/busca/plano`, `POST /api/busca` (`confirmar_recente`, `confirmar_espera`, `sem_nota`), `GET`/`DELETE /api/busca`, `POST /api/busca/analisar` | `/api/busca` 2 s | IA, P, L |
| Completar descrições | `GET`/`POST /api/busca/pendentes` | `/api/busca/pendentes` 2 s | P, L |
| Adicionar vaga (`AddJobModal`) | `POST /api/vagas/link`, `POST /api/vagas/extrair`, `POST /api/vagas` | — | IA (extrair só preenche), C, T |
| Quadro (`KanbanBoard`) | `PATCH`, `DELETE /api/vagas/{id}` | — | C (remover) |
| Detalhe (`JobDetailModal`) | `PATCH /api/vagas/{id}` (`anotacao`, `email_candidatura`, `assunto_candidatura`, `entrevista_em`, `kit`, `lembretes`, `resultado`) | — | T, E |
| Currículo (no detalhe e em Meu perfil) | `GET /api/curriculo/catalogo?vaga=`, `POST /api/curriculo`, `POST /api/curriculo/tentar`, `GET /api/curriculo/lista?vaga=` ou `?base=1`, links `/arquivos/curriculos/{nome}` | `/api/curriculo/estado` 2 s | IA, L |
| Kit (no detalhe) | `GET /api/kit/lista?vaga=`, `POST /api/kit/carta`, `POST /api/kit/respostas`, `PUT /api/kit/respostas/{nome}`, `/arquivos/curriculo-base/{pt\|en}` | `/api/curriculo/estado` 2 s | IA, S, E, L |
| Filtros (`SearchFiltersModal`, nacional e internacional) | `GET`/`PUT /api/config` | — | — |
| IA (`AISettingsModal`) | `GET`/`PUT /api/ia`, `POST /api/ia/testar`, `DELETE /api/ia/chave/{p}` | — | L; a chave só como `password`, nunca preenchida de volta |
| Meu perfil (`ProfileModal`, `CandidateOnboardingModal`) | `GET /api/perfil/estado`, `PUT`/`DELETE /api/perfil/progresso`, `POST`/`DELETE /api/perfil/material`, `POST /api/perfil/rascunho`, `POST /api/perfil/previa`, `PUT /api/perfil`, `GET`/`POST /api/perfil/filtros-propostos`, `GET /api/perfil/curriculos`, `POST /api/perfil/do-curriculo` (+`/confirmar`), `PUT /api/curriculo-base` | — | C (Ver o que muda, Recomeçar), IA, L |
| Análises (Meu perfil, Internacional) | `GET /api/analises-perfil`, `POST /api/analises-perfil/{lacunas,plano,cargos,cargos/filtros}`, `PUT /api/analises-perfil/marcas` | — | IA, C (levar cargos aos filtros), L |
| Entrevista (`InterviewCoach`) | `GET /api/entrevista/{vid}` e as rotas da tabela do §3.10 | — | IA, C (remover história; rascunhos não salvos), S (salário), L |
| Contas (`ConnectedAccountsModal`) | `GET /api/contas`, `GET /api/candidaturas/estado`, `POST /api/contas/{portal}/{conectar,pronto,desconectar}`, `POST /api/candidaturas/{ler,aplicar}` | as duas a 1,5 s, com o diálogo aberto | C (só os marcados), P, L; ícone como `<img>` |
| Funil (`FunnelAnalytics`) | nenhuma (calcula das vagas) | — | — |
