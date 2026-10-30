# Research: Materiais em três áreas e OCR

## R1. A área fica no tipo do material

- **Decision**: a área sai do `tipo` que já existe:
  - `linkedin_pdf` e `linkedin_zip` são LinkedIn;
  - `curriculo_pdf`, `curriculo_docx` e `texto` são currículo;
  - `documento_pdf` e `documento_docx` (novos) são documento.

  Mover troca o tipo: um PDF em documento vira `documento_pdf`. O formato vem da extensão do arquivo.
- **Rationale**:
  - não há campo novo para manter em sincronia;
  - os materiais antigos já têm a área certa pelo tipo que a ferramenta adivinhou;
  - a página antiga mostra o tipo novo pelo nome.
- **Alternatives considered**:
  - **campo `area` separado**: duplicaria a informação do tipo;
  - **pastas por área**: mover teria de mexer no arquivo e na marcação de Seu currículo.

## R2. Formatos por área

| Área | Aceita | Mensagem de recusa |
|---|---|---|
| linkedin | .pdf, .zip | "Aqui vão o PDF do perfil do LinkedIn ou o ZIP da exportação. Currículos e documentos vão nas outras áreas." |
| curriculo | .pdf, .docx | "Currículo em PDF ou Word (.docx). O ZIP do LinkedIn vai na área do LinkedIn." |
| documento | .pdf, .docx | "Documento em PDF ou Word (.docx). O ZIP do LinkedIn vai na área do LinkedIn." |

O .doc continua recusado com a mensagem de hoje. Mover para uma área que não aceita o formato também é recusado,
com a mesma mensagem. O texto colado é sempre currículo e não se move.

## R3. Aviso de área trocada (`sugestao_de_area`)

- **Decision**: a função é pura e roda sobre o texto mascarado do material, toda vez que a página pede o estado.
  Assim o aviso se atualiza depois de mover ou do OCR. Ela devolve `{area, motivo}` ou `None`:
  - **área currículo**:
    - se o texto parece LinkedIn (a mesma regra de `extrair`: "linkedin.com/in/" + uma marca que só o PDF do
      LinkedIn tem: "(LinkedIn)", "Top Skills"/"Principais competências" ou "Page 1 of"), sugere `linkedin`.
      Correção de 30/10: "Experience"/"Experiência" deixou de contar, porque quase todo currículo tem o link e essa
      seção. No teste, isso dava o aviso do LinkedIn num currículo e o classificava como LinkedIn quando enviado sem
      área;
    - se não, e o texto é curto (até 3.000 caracteres) e tem marca de certificado, sugere `documento`;
  - **área documento**: se o texto parece LinkedIn, sugere `linkedin`;
  - **área LinkedIn** (só PDF): se o texto não parece LinkedIn, sugere `documento` quando tem marca de certificado, ou
    `curriculo` quando não tem;
  - **sem texto**: sem sugestão.

  As marcas são comparadas sem acento e sem maiúsculas (`tipo_de_documento`):
  - **certificado** (texto de até 3.000 caracteres):
    - "certificado", "certificamos", "certifica que", "carga horaria", "concluiu", "concluido em", "horas de
      duracao", "declaracao de participacao";
    - "certificate of completion", "certificate of achievement", "has successfully completed";
    - ou o nome do arquivo com "certificad", "certificate", "diploma", "declarac" ou "historico";
  - **certificado bem curto** (até 600 caracteres): só a carga horária ("32 horas", "80h");
  - **acadêmico** (qualquer tamanho): "historico escolar", "curriculo escolar", "colacao de grau", "confere o
    titulo", "confere o grau". O motivo é "Parece um diploma ou histórico escolar.".
- **Rationale**:
  - nos arquivos do teste, os certificados têm entre 70 e 1.900 caracteres, e os currículos passam de 3.000;
  - o limite de tamanho evita acusar um currículo que cita "certificado" na seção de certificações;
  - a primeira versão só com as marcas de certificado deixou 11 de 44 sem aviso: declarações ("declaração de
    participação"), certificados que só trazem nome, curso e horas, e diplomas e históricos longos. As regras de nome
    de arquivo, carga horária e marca acadêmica cobriram os 44.
- **Alternatives considered**:
  - **pedir à IA para classificar**: seria lento, dependeria de IA e mandaria o texto à toa;
  - **classificar sozinho no envio**: contraria a decisão 2 (avisar, sem mudar).

## R4. OCR do Windows pelo PowerShell

- **Decision**:
  - **Script**: `ocr_windows.ps1` (raiz). Recebe `-Caminho <pdf> -MaxPaginas 5` e escreve na saída padrão, em UTF-8, o
    JSON `{paginas: N, textos: [..]}` ou `{erro: "..."}`.
  - **Leitura de cada página**:
    1. a página vira imagem com `Windows.Data.Pdf` (PdfPage.RenderToStreamAsync), com o lado maior em 1.600 px;
    2. a imagem é decodificada com `BitmapDecoder` e passa por `OcrEngine.TryCreateFromLanguage("pt-BR")`, ou pelo
       primeiro idioma disponível;
    3. se a leitura tiver menos de 40 caracteres de letras, a página é lida de novo com 1.200 e 2.400 px, e fica a
       leitura mais longa.
  - **Chamada**: `ocr.ler_pdf` chama `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File
    ocr_windows.ps1 -Caminho <arquivo>` com `subprocess.run` (lista de argumentos, sem shell), `timeout=30` e
    `CREATE_NO_WINDOW`.
  - **Saída**: o JSON é lido e as páginas são juntadas com uma linha em branco.
  - **Erros**: qualquer falha (sem PowerShell, sem idioma, tempo esgotado, JSON inválido) vira `("", [motivo])`, sem
    exceção.
- **Rationale**:
  - foi testado na máquina do usuário: 7 de 7 certificados lidos, 1,8 s no total;
  - 2.400 px falhou em parte dos certificados do teste, e 1.600 px saiu quase perfeito;
  - `Bypass` só vale para esse processo e não muda a política do sistema;
  - o script vai junto do repositório, então não é código baixado.
- **Alternatives considered**:
  - **Tesseract**: precisa de instalação;
  - **IA com visão**: mandaria a imagem sem máscara de CPF para fora;
  - **pypdf para extrair a imagem e OCR dela**: exigiria decodificar formatos de imagem sem biblioteca, e o
    `Windows.Data.Pdf` já entrega a página pronta.

## R5. Onde o OCR entra

- **Decision**:
  - **Onde roda**: `primeiros_passos.ler_pdf`. Quando o pypdf não acha texto e `ocr.disponivel()`, chama
    `ocr.ler_pdf`.
  - **Com texto lido**: devolve o texto com o aviso "Texto lido da imagem (OCR): confira nomes, datas e números", e
    `extrair` marca `ocr: True`.
  - **Sem texto lido**: fica o aviso de hoje, com o motivo do OCR quando houver.
  - **Quem ganha a leitura**: `curriculo_base.ler` usa `pp.extrair` e ganha o OCR sem mudança (FR-018).
- **Botão OCR**: `reler_material(estado, id)` só para material com arquivo PDF e sem texto. Ele roda `extrair(arquivo,
  area_atual)` de novo e atualiza `texto`, `avisos`, `contato` e `ocr`, mantendo `id`, `nome`, `arquivo` e área.
- **Pedido à IA**:
  - cabeçalho da fonte `### Fonte: <nome> (área: currículo|LinkedIn|certificado ou documento[; texto lido por OCR,
    pode ter erros de leitura])`;
  - regras novas:
    - "Fontes da área certificado ou documento entram só em formação e certificações, nunca como experiência.";
    - "Em texto lido por OCR, não use número, data ou nome que pareça mal lido; deixe de fora."

## R6. Seu currículo e a lista da pasta anexos

- **Decision**:
  - `curriculo_base.candidatos()` tira os arquivos que aparecem nos materiais (`pp.carregar()`) com área documento
    ou LinkedIn.
  - Ao mover para documento ou LinkedIn um arquivo que é o Seu currículo (`marcados()` pt ou en), a marcação daquele
    idioma é apagada (`marcar(idioma, None)`), e a resposta traz o aviso "Este arquivo era o seu currículo em
    <idioma>; a marcação saiu."
- **Rationale**: a lista da pasta anexos e o seletor usam a mesma fonte (`candidatos`), então uma regra só resolve os
  dois lugares. A marcação apontaria para algo que deixou de ser currículo.

## R7. Front

- **Decision**:
  - **Componente**: `Materiais` sai do `MeuPerfil.tsx` para `perfil/Materiais.tsx` (o arquivo passa de 1.500
    linhas).
  - **Cada área**: título, frase do que vai ali, envio (input com `accept` da área e arrastar), lista dos materiais
    com `area` igual à da seção.
  - **Cada arquivo**:
    - nome e rótulo;
    - Mover para: `<select>` com as áreas que aceitam o formato, que só aparece para arquivo;
    - aviso amarelo com o botão "Mover para <área>" quando há `sugestao`;
    - botão **OCR** quando é PDF sem texto (`!tem_texto`);
    - "Usar este currículo…" só na área currículo;
    - Remover;
    - Texto lido.
  - **Ordem das áreas**: LinkedIn (com o link e o "Como baixar"), Currículos (com a pasta anexos e o texto colado) e
    Documentos.
- **Rationale**: as decisões da spec, com a mesma estrutura de seção (`SEC`, `H`, `DICA`) do resto do Meu perfil.
