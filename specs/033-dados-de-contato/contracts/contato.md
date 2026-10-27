# Contratos: Dados de contato na candidatura assistida, sem IA

## 1. `candidatura/contato.py`

| Função | Contrato |
|---|---|
| `CAMPOS` | `("nome", "sobrenome", "email", "telefone", "cidade", "estado", "pais", "linkedin", "portfolio", "endereco", "cep")` |
| `arquivo()` | `banco.ARQUIVO.parent / "contato.json"` |
| `ler()` | os dados salvos (`{}` sem arquivo ou com arquivo ilegível) |
| `gravar(dados)` | valida (data-model), grava os não vazios e devolve o que ficou; `ValueError` com a regra que falhou |
| `apagar()` | remove o arquivo; devolve `{}` |
| `propor()` | `{dados, fontes, avisos}` (data-model); não grava |
| `reconhecer(campo)` | o nome do dado que o campo pede, ou `None` (D2) |
| `valor_para(campo, dados)` | o valor no formato do campo (texto ou índice da opção), ou `None` (D5) |

## 2. Rotas (`dash/API.md` §3.11b, todas **[local]**)

**`GET /api/candidatura`**: o de hoje, mais `contato: {…}` (os dados salvos) e `campos_contato: [nomes]`.

**`POST /api/candidatura/contato/proposta`**: sem corpo. Resposta `{dados, fontes, avisos}`, sem gravar. Sem currículo
base, vêm só a memória e os filtros, com aviso.

**`PUT /api/candidatura/contato`**: corpo `{dados: {campo: valor}}`. Resposta `{contato}`. Erro 400 com a regra
("e-mail inválido", "o LinkedIn precisa ser um link do linkedin.com", "parece um documento (CPF/RG/data de
nascimento) em <campo>: não guarde documentos aqui").

**`DELETE /api/candidatura/contato`**: resposta `{contato: {}}`.

**`POST /api/candidatura/vaga/{id}/auto`** ("Preencher esta página"): o de hoje. Em `preenchidos`, os campos de contato
vêm com `fonte: "seus dados de contato"`.

## 3. Front

No painel da candidatura assistida (`ConfigCandidatura.tsx`), a seção **"Seus dados de contato"** tem:
- os campos da tabela do data-model, com endereço e CEP marcados como opcionais;
- **"Propor a partir do currículo"**: preenche o formulário com a proposta e mostra a fonte de cada valor, sem gravar;
- **Salvar** e **Apagar**;
- a dica: "Usados para preencher nome, e-mail, telefone e links em qualquer formulário, sem IA. Ficam só neste
  computador."
