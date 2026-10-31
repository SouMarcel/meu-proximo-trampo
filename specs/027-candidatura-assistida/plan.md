# Plano de implementação: candidatura assistida

**Spec**: [spec.md](spec.md) · **Pesquisa**: [research.md](research.md) · **Data**: 2026-10-23

## Resumo

A ferramenta preenche os campos da página de candidatura aberta na janela dela (a mesma da spec 018), com as
respostas que a pessoa conferiu. Quem clica em Entrar, Continuar e Enviar é sempre a pessoa.

## Estrutura

```text
navegador.py                 + Aba.digitar(), Aba.espaco(), Aba.origem(), aba_atual()
candidatura/__init__.py      erros, estado do recurso (config.json → "candidatura"), trava de preenchimento
candidatura/dominios.py      CONHECIDOS, BLOQUEADOS, situacao(url), liberar(), revogar()
candidatura/formulario.py    JS_LER, ler(aba), classificar, assinatura, preencher(aba, assinatura, respostas)
candidatura/login.py         credencial(portal), estado_credenciais(), gravar/apagar, preencher_login(aba)
candidatura_ia.py            + propor_respostas(vaga, campos), gravar_preenchidas(vaga, itens)
dash/servidor.py             + _candidatura(): rotas /api/candidatura...
dash/API.md                  contrato das rotas novas
tests/test_candidatura_assistida.py
frontend-react: src/services/api/candidatura.ts, src/components/kit/CandidaturaAssistida.tsx, configuração no
                painel de contas conectadas
```

## Constituição (4.0.0)

| Princípio | Como este plano cumpre |
|---|---|
| I | A credencial fica só no `.env`. A página do dashboard recebe só o usuário e os 4 últimos caracteres da senha. Nada vai para log. |
| II | Nada pessoal no código. Os domínios liberados ficam no `config.json` (fora do Git). |
| III | Só a biblioteca padrão e o protocolo de depuração que já existe. Funciona com qualquer provedor de IA, porque a IA só escreve textos. |
| IV | As perguntas sensíveis não vão para a IA e não são preenchidas. A conferência de fatos vale também aqui. |
| V | Nada roda sozinho. A pessoa vê a proposta, edita e clica. O envio é dela. |
| VI | Desligado por padrão. Só preenche em domínio liberado. Indeed e LinkedIn ficam bloqueados (a Nerdin saiu em 2026-10-31, research.md §1). Só campos, nunca botões. Para no bloqueio. A credencial só é digitada no host exato de login. |

## Fluxo

1. Em "Candidatar com ajuda", a rota `POST /api/candidatura/{id}/abrir` abre a URL da vaga na janela.
2. Na tela de login, a rota `POST /api/candidatura/login` preenche usuário e senha, se a credencial estiver guardada
   e o host bater. Quem clica em Entrar é a pessoa.
3. A rota `POST /api/candidatura/{id}/ler` lê a página atual, sem navegar. O que acontece depende do resultado:
   - **bloqueio, teste ou desconhecida:** só o aviso, sem chamar a IA;
   - **domínio não liberado:** pergunta, se ele puder ser liberado;
   - **perguntas:** chama `propor_respostas` e devolve os itens com a assinatura da página.
4. A rota `POST /api/candidatura/{id}/preencher` recebe a assinatura e as respostas confirmadas:
   - lê a página de novo e confere a assinatura;
   - preenche só os campos comuns, sem pisar em valor existente, salvo "trocar";
   - grava as respostas no kit da vaga (`curriculos/…-respostas`);
   - devolve o que foi preenchido e o que ficou para a pessoa.

## Riscos

- **Formulários diferentes do esperado.** O que não é reconhecido fica com a pessoa ("escolha você", "não reconheci
  esta página"). A prova real com o usuário ajusta as heurísticas.
- **Os termos da Gupy não foram lidos.** Fica como pendência para o usuário antes da `master`.
