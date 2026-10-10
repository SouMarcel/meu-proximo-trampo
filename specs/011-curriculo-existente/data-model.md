# Data Model: Começar pelo currículo que a pessoa já tem

## Configuração (`config.json`, fora do Git)

```text
curriculo_base: {pt: "anexos/…/arquivo.pdf", en: "anexos/…/resume.docx"}   # no máximo um por idioma; vazio por padrão
```

Validação: caminho relativo dentro de `anexos/`, extensão `.pdf` ou `.docx`, arquivo existente na hora de marcar.

## Perfil feito do currículo (`perfil.md`)

```text
<!-- origem: curriculo arquivo=anexos/… data=AAAA-MM-DD -->
# Meu perfil de carreira

> Montado a partir do seu currículo (arquivo, data). Para completar (números, níveis, idiomas, interesse em vagas
> de fora), use "Completar com a anamnese" em Meu perfil.

<texto do currículo, com documentos de identificação escondidos>
```

## Proposta (não gravada)

| Campo | Regra |
|---|---|
| `texto` | texto lido do currículo, mascarado (até o limite da spec 004) |
| `idioma` | `pt` ou `en`, pelo texto |
| `perfil` | Markdown acima |
| `dados` | `{cargos_alvo, cargos_alvo_en, cidade, modelos, origem: ia|texto}` |
| `filtros` | resultado de `propor_filtros` (validado) |
| `existe_perfil` | se já há perfil (a tela pergunta substituir ou manter) |

## Checklist (calculado)

Item `curriculo` ganha `base: {idioma, nome, url}` quando há currículo base no idioma da vaga, ou
`falta_base: idioma` quando não há; estado padrão `pronto` com base, `a_fazer` sem.
