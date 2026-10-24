# Pesquisa: candidatura assistida

## 1. Termos de uso para candidatos (lidos em 2026-10-23)

Trechos literais das páginas oficiais. Isto não é parecer jurídico.

| Portal | Página | O que diz | Decisão |
|---|---|---|---|
| Indeed | br.indeed.com/legal (Termos de Serviço, 01/04/2026), seção A, item 5 | "É proibido o uso de qualquer automação, script ou bots para automatizar o processo de candidatura do Indeed que não seja por meio dos fornecedores e ferramentas oficiais do Indeed." | **Bloqueado**, sem opção de liberar (constituição VI: "seguir os termos de cada fonte") |
| Nerdin | nerdin.com.br/candidato_termo_plano_premium.php (21/09/2026), item 7 | "É proibido, sem autorização: … utilizar robôs, scraping, automações ou mecanismos de coleta/acesso não autorizados" | **Bloqueado**, sem opção de liberar |
| LinkedIn | (spec 018) | restringe contas que considera automatizadas | **Bloqueado**, sem opção de liberar |
| Gupy | gupy.io/termos-de-uso e variações: HTTP 404; o aviso de privacidade institucional não trata do assunto | não foi possível ler termos para candidatos | **Conhecido**, com pendência: o usuário confere o "Aviso de Privacidade … para Pessoas Candidatas" e o suporte de candidatos antes da entrega na `master` |
| Greenhouse | greenhouse.com/legal: só documentos para clientes | não trata de candidatos | Conhecido |
| Lever | lever.co/legal/terms-of-service: contrato com a empresa | não trata de candidatos | Conhecido |
| Workday | workday.com/legal/site-terms: vale para www.workday.com, não para os sites de vagas | não trata de candidatos em myworkdayjobs.com | Conhecido |

Páginas de login de candidato encontradas:

| Portal | Login |
|---|---|
| Gupy | `login.gupy.io` |
| Greenhouse | `my.greenhouse.io` |
| Lever | sem login central de candidato |
| Workday | login próprio de cada empresa, no mesmo endereço da vaga |

Decisão: só a Gupy e o Greenhouse ganham credencial guardada. No Lever e no Workday, a pessoa faz o login à mão.

**Desvio da spec.** A spec dizia que um portal com termos contrários ficaria fora da lista e a pessoa poderia
liberá-lo. Foi trocado por bloqueio, porque liberar contraria o princípio VI, e a spec foi atualizada.

## 2. Como ler o formulário de qualquer portal

- **Decisão:** leitura genérica do DOM da página atual. Um único JavaScript devolve, para cada campo visível:
  - um identificador estável (`id`, senão `name` e o tipo, senão a posição);
  - o rótulo (`label[for]`, `label` em volta, `aria-labelledby`, `aria-label`, `legend` do `fieldset`,
    `placeholder`);
  - o tipo, as opções, o `maxlength`, `required` e o valor atual.

  Também devolve até 4.000 caracteres do texto visível da página e os endereços dos `iframe`. A classificação da
  página (login, perguntas, teste, bloqueio ou desconhecida) e a de cada campo (comum, sensível, cadastro,
  consentimento, arquivo, senha ou outro) ficam em Python, onde dá para testar sem navegador.
- **Por quê:** funciona em qualquer portal e não depende de API privada nem de pedido de escrita. Ajustes por portal
  podem vir depois, quando a prova com o usuário mostrar a necessidade.
- **Alternativa descartada:** a API privada de cada portal. Não tem documentação, muda sem aviso e exigiria POST.

## 3. Como escrever sem clicar

- **Texto:** foca o campo (`el.focus()`), confere que o elemento ativo é mesmo aquele campo de texto e só então
  digita com `Input.insertText` do protocolo de depuração. É digitação de verdade: as páginas em React recebem os
  eventos de entrada normais.
- **Seleção nativa:** troca o valor com o setter nativo e dispara `input` e `change`.
- **Lista com busca** (react-select, ex.: Greenhouse, 2026-10-24): o `input` tem `role="combobox"` e as opções só
  existem com a lista aberta. Para ler, a ferramenta abre (seta para baixo), lê as opções (`role="option"`) e fecha
  (Esc). Para escolher, digita o texto da opção, leva o destaque até a opção exata (seta para baixo) e aperta Tab, que
  escolhe sem enviar; depois confere o valor escolhido. Teclas permitidas: seta para baixo, Esc, Tab e espaço
  (`Aba.TECLAS`); a de confirmar não existe. Campos escondidos de validação (`aria-hidden`, `tabindex=-1` e opacidade
  0) não são perguntas.
- **Captcha:** o reCAPTCHA invisível (selo `.grecaptcha-badge`, `size=invisible` ou tamanho zero) e o aviso
  "protected by reCAPTCHA" não param a ferramenta. Param: a caixa "não sou um robô", o desafio de imagens, o Turnstile
  visível e frases de verificação ("verify you are human", "código de verificação").
- **Opção (radio) e caixas:** foca a opção e aperta espaço (`Input.dispatchKeyEvent`). O espaço só é enviado depois
  de conferir que o elemento ativo é aquele `input` de radio ou checkbox. Assim, nunca cai num botão por engano.
- **Fica com a pessoa:** seletores que não são nativos (listas feitas com `div`). A ferramenta marca o campo como
  "escolha você".
- **Nunca:** `click()`, `submit()`, `requestSubmit()`, tecla Enter, `fetch` de escrita. Um teste procura essas
  palavras no JavaScript do módulo.

## 4. Senha

- `segredos.py` guarda `LOGIN_<PORTAL>_USUARIO` e `LOGIN_<PORTAL>_SENHA` no `.env`.
- A senha só sai do disco para o `Input.insertText`, na conexão local com a janela, quando a página está:
  - em `https`;
  - num host exato da lista de login do portal;
  - com um único campo de senha visível.
- A página do dashboard recebe só o usuário e os 4 últimos caracteres da senha.
- **Gerenciador de Credenciais do Windows:** fica na lista de desejos. Exigiria `ctypes` com a API do Windows ou uma
  dependência nova.

## 5. Página que mudou

A leitura devolve uma assinatura: hash dos identificadores e dos rótulos dos campos. O preenchimento lê a página de
novo e só segue se a assinatura bater.
