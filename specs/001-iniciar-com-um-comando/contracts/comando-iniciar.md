# Contrato: comando `iniciar` e atalhos

## Uso

```text
python iniciar.py [--sim] [--sem-navegador] [--rede] [--porta N]
```

Plataforma: Windows (macOS e Linux na lista de desejos). Se `python` não for reconhecido:
`py iniciar.py …`. Atalho de duplo clique: `iniciar.bat`, que faz o mesmo com os mesmos
argumentos.

| Opção | Efeito |
|---|---|
| `--sim` | aceita a instalação/recriação do ambiente sem perguntar |
| `--sem-navegador` | não abre o navegador (repassada ao servidor) |
| `--rede` | aceita acesso de outros aparelhos da rede local (repassada) |
| `--porta N` | usa a porta N em vez de 8765 (repassada) |
| `-h`, `--help` | ajuda em português |

## Sequência

1. Python abaixo de 3.10 → mensagem com a versão exigida e o link de download; sai com 2.
2. Ferramenta já em execução na porta → abre a página (salvo `--sem-navegador`); sai com 0.
3. Ambiente `pronto` → passo 5.
4. Outros estados → diz o que vai fazer (criar, recriar, instalar o que falta) e pergunta
   `Instalar agora? [S/n]` (pula com `--sim`). Recusa → explica como instalar à mão; sai com 3.
   Falha na instalação → causa provável (internet, `python3-venv`) e "rode o comando de novo";
   sai com 1.
5. Inicia o servidor na mesma janela; ele mostra o endereço e "Feche esta janela (ou Ctrl+C)
   para parar". O código de saída é o do servidor (0 ao parar normalmente; 1 porta ocupada).

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | parou normalmente, ou a ferramenta já estava aberta |
| 1 | falha na instalação ou ao iniciar o servidor (ex.: porta ocupada) |
| 2 | pré-requisito ausente ou argumento inválido |
| 3 | a pessoa recusou a instalação |

## Garantias

- Só escreve dentro de `.venv/`; nunca em `config.json`, `perfil.md`, `dash/dados/` ou outro
  arquivo da pessoa.
- Com o ambiente `pronto`, não pergunta nada e não acessa a internet.
- O atalho mantém a janela aberta (`pause`) quando o código de saída não é 0.

## Página: aviso de próximo passo

Ao carregar, a página consulta `GET /api/config`. Com `existe: false`, o Relatório de Vagas
mostra um aviso com o botão "Filtros da busca" (configurar os cargos e o local antes da primeira
busca). Com `existe: true`, nada muda.
