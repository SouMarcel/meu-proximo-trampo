# Quickstart: validar a spec 037

## Pré-requisitos

- O backend da `037-materiais-por-area` mesclado na branch pessoal.
- O build do front copiado para `dash/front/`, sem commit.
- O dashboard reiniciado (`--sem-navegador`).

## Automático

```text
python -m unittest discover -s tests          # inclui tests/test_ocr.py e os testes novos de materiais
(frontend-react) pnpm exec tsc --noEmit && pnpm exec vite build --base ./
```

## Na página (Meu perfil → Materiais)

1. **As três áreas**: Perfil do LinkedIn (com o link e o "Como baixar"), Currículos (com a pasta anexos e o texto
   colado) e Outros documentos e certificações.
2. **Os certificados enviados como currículo**:
   - aparecem em Currículos com o aviso amarelo "Parece um certificado";
   - o botão do aviso, ou Mover para → Documento, leva cada um para Outros documentos, onde não há "Usar este
     currículo".
3. **Os PDFs sem texto**:
   - têm o botão **OCR**;
   - um clique mostra o texto em "Texto lido", com o aviso "Texto lido da imagem (OCR): confira…";
   - depois disso, o aviso de área passa a valer para eles.
4. **Envio novo** de um PDF só de imagem em Documentos: o texto já vem lido.
5. **Envio de Word na área do LinkedIn**: é recusado com a mensagem da área certa.
6. **Currículo base → Seu currículo**: o seletor não mostra os certificados nem o PDF do LinkedIn.
7. **Rascunho com IA** (se quiser): os certificados entram em Certificações, não em Experiência.
8. **Tema escuro e celular**: as três áreas empilham sem rolagem lateral.

## Antes da entrega

- `git checkout -- dash/front` na branch pessoal e apagar os assets novos.
- Procurar dados pessoais no diff que vai para a `master`.
