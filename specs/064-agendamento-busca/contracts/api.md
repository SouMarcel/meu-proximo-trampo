# Contratos: Busca agendada e retomada depois da espera

Vai para o `dash/API.md` como a seção **3.3b Agendamento e retomada** (depois da 3.3 Busca). Rotas de escrita só
deste computador (`[local]`), como a busca.

## `GET /api/agendamento`

```json
{
  "agendamento": {"ligado": true, "horario": "08:00", "continuar": true},
  "proxima": "2026-11-28T08:00",          // null com o agendamento desligado
  "hoje": {"situacao": "rodou", "em": "2026-11-27T08:00:12", "motivo": null},  // null se ainda não chegou a hora
  "retomadas": [
    {"nome": "linkedin", "portal": "LinkedIn", "proxima": "2026-11-27T14:00", "em_espera_ate": "2026-11-27T14:00",
     "consultas": 2, "descricoes": 18, "tentativas": 0, "criada_em": "2026-11-27T08:00", "origem_busca": "agendada"}
  ],
  "historico": [ /* os eventos de .cache/agendamento.json (data-model.md), até 10 */ ],
  "aviso_login": "MyGreenhouse Jobs fica de fora da busca agendada (portal com login roda só no botão Buscar)",
  "pode_alterar": true
}
```

`hoje.situacao`: `rodou`, `pulada` (motivo: "busca manual às 07:30"), `perdida` ("o dashboard não estava ligado às
08:00"), `devida` (esperando outra busca terminar) ou `rodando`.

## `PUT /api/agendamento` `[local]`

Corpo: `{"ligado": bool, "horario": "HH:MM", "continuar": bool}` (campo ausente fica como está). Responde como o GET.
Erro 400 `{"erro": "horário inválido: use HH:MM"}`. Desmarcar `continuar` apaga as retomadas.

## `DELETE /api/agendamento/retomadas/<nome>` `[local]`

Cancela a retomada do portal (`linkedin`, `infojobs`…). Responde como o GET; 404 se não houver.

## Estado da busca (acréscimo em `GET /api/busca` e `/api/versao` → `busca`)

`origem` ganha `agendada` e `retomada`; com `retomada`, o estado traz `"retomada": {"nome": "linkedin", "portal":
"LinkedIn"}`. O resumo final traz `"bloqueados": ["LinkedIn"]` e, quando o portal ganhou retomada,
`"retomada_as": "2026-11-27T14:00"`. `POST /api/busca` continua só com origem `pagina`.

`POST /api/busca/pendentes` (Completar descrições) e o Forçar verificar seguem recusando com a busca agendada ou a
retomada rodando (mesma mensagem da busca da página).

## Terminal

```text
PY vagas.py agendamento                         mostra: ligado, horário, continuar, próxima, retomadas, último evento
PY vagas.py agendamento --ligar 08:00           liga no horário (grava no config.json)
PY vagas.py agendamento --desligar
PY vagas.py agendamento --continuar sim|nao
PY vagas.py agendamento --cancelar-retomada linkedin
```

Saída 0; horário inválido sai com código 2 e a mensagem. O `vagas.py buscar` registra as retomadas quando
`continuar` está ligado e avisa no fim: "LinkedIn bloqueou; com o dashboard ligado, a retomada roda às 14:00".

## `.env`

```text
# Espera depois de um bloqueio, em minutos (60 a 2880; padrão 360 = 6 horas)
# LINKEDIN_ESPERA=360
# INFOJOBS_ESPERA=360
# VAGASCOM_ESPERA=360
# JOBGETHER_ESPERA=360
# FULLSTACK_ESPERA=360
# MYGREENHOUSE_ESPERA=360
```
