# Implementation Plan: Nerdin no "Atualizar candidaturas"

**Branch**: `059-nerdin-candidaturas` (worktree saída da `master`) | **Date**: 2026-11-24 | **Spec**: [spec.md](spec.md)

## Summary

Um módulo novo, `contas/nerdin.py`, no contrato de `contas/__init__.py` (spec 018), registrado em `contas.TODAS` com
`ATIVO = True`. O painel, a leitura em segundo plano, a proposta, o casamento (ids e cargo + mesma empresa, spec 058)
e o "Aplicar marcadas" já existem e não mudam. A página do front monta a lista de portais por `GET /api/contas`, então
o front não muda.

Diferente da Gupy e do Indeed, a Nerdin não tem API de candidaturas: o módulo pega o HTML da página aberta na janela
(`aba.avaliar("document.documentElement.outerHTML")`) e lê os cartões em Python, com a biblioteca padrão
(`html.parser`). Assim a leitura fica testável com HTML fictício e nenhum JavaScript da ferramenta mexe na página.

## Constitution Check

- **VI, Conta conectada:** login da pessoa na janela; só leitura; só no clique; nenhum clique (em especial "Cancelar
  candidatura"); sessão apagada no Desconectar (`ORIGENS`). Emenda: liberados Gupy, Indeed e Nerdin.
- **VI, Termos contrários:** decisão do usuário registrada na spec (2026-11-24); o aviso do painel (`AVISO_LOGIN`)
  diz que os termos da Nerdin não permitem acesso automatizado e que a leitura é só da página de candidaturas.
- **V:** a leitura só propõe; nada é gravado sem "Aplicar marcadas".
- **III/II:** o texto da página é dado; título, empresa e local passam por `contas.lida` (limite de tamanho). Os
  testes usam empresas fictícias, nunca as do print.

Gate: passa, com a emenda (T001).

## Decisões

**D1. Endereço da página.** `URL_CANDIDATURAS = "https://www.nerdin.com.br/vagas_candidato.php"`. Em `ler(aba)`:

1. endereço conhecido: `NERDIN_CANDIDATURAS` (`segredos.ler`), senão o guardado em `.cache/contas/nerdin.json`
   (`{"url": ...}`), senão `URL_CANDIDATURAS`;
2. `aba.ir(endereco)`; se a aba foi para `login.php` → `PortalErro(login=True)`;
3. se o HTML não tem cartões e tem um link `vagas_candidato.php?id=<número>` (o menu "Candidato"), vai a ele (pelo
   endereço, sem clicar), guarda em `.cache/contas/nerdin.json` e lê de novo;
4. só aceita endereço em `https://www.nerdin.com.br/vagas_candidato.php?id=<dígitos>` (o do `.env` também passa por
   essa conferência).

**D2. Login.** `HOST_LOGIN = "login.php"` (trecho do endereço). `logado(url)`: host `nerdin.com.br` ou
`www.nerdin.com.br` e caminho sem `login`. `ORIGENS = ("https://www.nerdin.com.br", "https://nerdin.com.br")`.

**D3. Cartão.** Um parser (`HTMLParser`) monta uma árvore simples (tag, atributos, filhos, texto). Cartão = o menor
elemento que contém o texto "Acompanhe sua candidatura" e "Inscrito em". Dele saem:

- `titulo`: o primeiro `h1`–`h6`; sem título, o cartão é ignorado;
- `empresa` e `local`: o texto ao lado do ícone cuja classe tem `building` (empresa) e `map-marker`/`location`
  (local); na falta, as duas primeiras linhas de texto depois do título que não sejam o selo;
- `selo`: "Aberta" ou "Expirada" (texto exato de um elemento do cartão);
- `inscrito`: `Inscrito em: DD/MM/AAAA` → ISO;
- `passos`: os rótulos conhecidos da trilha, na ordem, cada um com `feito` (classe do passo ou do ícone com `success`,
  `done`, `complet`, `check`, `active`, `ativo`) quando der para saber;
- `id`: o primeiro link do cartão com o número da vaga (`fontes.nerdin.id_do_link`, ou `vaga.php?id=<n>` →
  `nerdin-<n>`); `url`: esse link absoluto, ou `https://www.nerdin.com.br/vaga.php?id=<n>`.

**D4. Tradução** (`traduzir(cartao) -> lida`), pela US3:

| Trilha / selo | etapa | resultado | status | aviso | ativa |
|---|---|---|---|---|---|
| "Não selecionado" | encerrada | nao_aprovado | Não selecionado | — | não |
| "Em análise"/"Processo aberto", selo Aberta | aplicada | — | último passo feito, ou "Inscrito" | — | sim |
| idem, selo Expirada | aplicada | — | idem | vaga expirada na Nerdin | não |
| "Processo encerrado" sem "Não selecionado" | None | — | Processo encerrado | processo encerrado na Nerdin | não |
| nada reconhecido | None | — | texto da trilha | status na Nerdin: … | não |

`data` = `inscrito`. Na proposta (sem mudança no código dela): `aplicada` com a vaga já em "aplicada" não aparece;
`encerrada` vira "mudar"; candidatura fora do dashboard e encerrada vai ao histórico.

**D5. Páginas seguintes.** Links do HTML para `vagas_candidato.php` com o mesmo `id` e um parâmetro de página ainda
não visitado; no máximo `MAX_PAGINAS = 5`, com `time.sleep` da pausa da Nerdin (`fontes.nerdin.pausa()["faixa"][0]`)
entre elas.

**D6. Erro de leitura.** Página logada sem nenhum cartão e sem o texto de lista vazia ("nenhuma candidatura" ou
"não se inscreveu") → `PortalErro("não consegui ler as candidaturas da Nerdin")`. Captcha/bloqueio (texto
"captcha", "acesso negado", "too many requests") → `PortalErro` sem nova tentativa.

**D7. Descrição da vaga nova.** `sincronia._descricao`: `portal == "nerdin"` com `url` → `fontes.link.ler(url)` (o
leitor público do Adicionar Vaga, spec 020).

## Arquivos

| Arquivo | Mudança |
|---|---|
| `contas/nerdin.py` | novo (D1–D6) |
| `contas/__init__.py` | importa `nerdin`, entra em `TODAS`; docstring cita a Nerdin |
| `dash/sincronia.py` | `_descricao` (D7) |
| `tests/test_contas_nerdin.py` | novo: parser, tradução, login, endereço, proposta |
| `.specify/memory/constitution.md` | emenda (VI, Conta conectada) |
| `AGENTS.md`, `README.md`, `dash/API.md`, `.agents/skills/buscar-vagas/SKILL.md` (+ cópia) | Nerdin nas contas conectadas |
| `.env.exemplo` | `NERDIN_CANDIDATURAS` comentado |

## Testes

- HTML fictício com os cinco tipos de cartão do print (empresas fictícias): em andamento, recusado, expirado com
  recusa, expirado em andamento, e um passo desconhecido.
- `ler` com uma aba falsa: login (`login.php`), descoberta do link no menu, endereço do `.env` inválido ignorado,
  página sem cartões = erro, nenhum JavaScript além da leitura do HTML (FR-004, SC-005).
- `sincronia.proposta` com as lidas da Nerdin e vagas `nerdin-<n>` no banco (SC-001, SC-002).

## Validação real

No dashboard da `marcel`, Conectar → login → Pronto → Atualizar agora. Esperado (tabela da conversa de 2026-11-24, só
no teste da pessoa): duas sem mudança, duas para "Encerrada · não aprovado" e uma no histórico. Se a marcação dos
passos ou dos links for diferente da suposta, ajustar D3 com o que a página mostrar.
