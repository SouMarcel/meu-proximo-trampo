# Research: Começar pelo currículo que a pessoa já tem

## 1. De onde vem o currículo

- **Decision**: dos materiais dos primeiros passos (spec 004: enviado pela página, guardado em
  `anexos/primeiros-passos/`) ou de um arquivo que já está em `anexos/` (PDF ou DOCX, qualquer subpasta
  menos `perfis-anteriores/`). O arquivo de `anexos/` entra como material sem ser copiado
  (`primeiros_passos.adicionar_existente`), com a mesma leitura e a mesma máscara de documentos.
- **Rationale**: reaproveita a leitura de PDF/DOCX e a máscara que já existem; não duplica arquivos pessoais.

## 2. Perfil feito do currículo

- **Decision**: o perfil é o texto do currículo (mascarado), com um cabeçalho que diz de onde veio e uma marca
  de origem (`<!-- origem: curriculo arquivo=… data=… -->`) para Meu perfil reconhecer e oferecer a anamnese.
  Sem IA reescrevendo; gravado por `primeiros_passos.gravar_perfil` (guarda o anterior).
- **Rationale**: "só fatos do currículo" fica garantido por construção; a análise das vagas já lê perfil em texto
  livre (`dash/analise.py` manda o perfil inteiro).
- **Alternatives considered**: IA reorganizar o currículo no formato do `perfil.exemplo.md` (é o caminho da
  anamnese, que continua disponível; aqui a pessoa pediu pular).

## 3. Filtros propostos

- **Decision**: `curriculo_base.dados_do_curriculo(texto)` tira cargos, cidade e modelo de trabalho:
  - **sem IA**: cargo da linha "Objetivo/Cargo pretendido/Objective" quando há; senão o cargo mais recente
    (a primeira linha de experiência com período, antes do separador da empresa); cidade pelo padrão
    "Cidade, UF" (ou "City, State/Country"); modelo pelas palavras remoto/remote, híbrido/hybrid;
  - **com IA**: um pedido curto que devolve `{cargos_alvo, cargos_alvo_en, cidade, modelos}` só com o que o
    currículo diz (o texto é dado, nunca instrução); falha da IA cai no caminho sem IA.
  O resultado vira as `respostas` que `primeiros_passos.propor_filtros` já aceita, e a proposta sai validada por
  `filtros.validar`. A pessoa edita cargos (PT e EN), cidade e modelos na mesma tela.
- **Rationale**: um só caminho para propor filtros (spec 004); sem IA, ao menos o cargo mais recente (SC-005).

## 4. Currículo base

- **Decision**: `config.json → curriculo_base: {"pt": "anexos/…", "en": "anexos/…"}` (fora do Git), gravado por
  `curriculo_base.marcar(idioma, arquivo)` mantendo as outras chaves; idioma detectado pelo texto
  (`filtros.idioma_texto`), corrigível. Arquivo precisa estar dentro de `anexos/` e ser PDF ou DOCX.
- **Checklist**: `kit.checklist(v, base)` recebe os currículos base; o item Currículo do idioma da vaga (en para
  vaga em inglês, pt para o resto) mostra o nome e o link e começa "Pronto"; sem o do idioma, diz que falta e fica
  "A fazer". A situação marcada pela pessoa vale sempre. Arquivo sumido: aviso e "A fazer".
- **Link**: `GET /arquivos/curriculo-base/<idioma>` serve só o arquivo marcado daquele idioma, só para pedidos
  deste computador.
- **Nome**: na página, "Seu currículo" (o arquivo da pessoa), para não confundir com o "currículo base" gerado pela
  IA da spec 007, que continua igual.

## 5. Tela de confirmação

- **Decision**: uma tela só (SC-001) no Meu perfil: o texto lido (recolhido), o perfil proposto (editável), os
  filtros propostos (cargos PT, cargos EN, cidade, modelos), a escolha "substituir o perfil / manter o meu e só
  marcar o currículo" quando já há perfil, e "marcar como meu currículo em <idioma>" (marcado). Confirmar grava tudo
  de uma vez (`POST /api/perfil/do-curriculo/confirmar`) e abre o painel de busca. Fechar não grava nada.

## 6. Completar depois

- `primeiros_passos.estado_para_pagina` passa a informar `perfil_do_curriculo` (pela marca de origem); Meu perfil
  mostra o aviso e "Completar com a anamnese", que segue o fluxo de hoje com o currículo como material.

## 7. Chat

- `curriculo_base.py` com linha de comando: `proposta <arquivo>` (mostra perfil e filtros, não grava),
  `usar <arquivo> [--manter-perfil]` (grava, só depois do OK da pessoa na conversa), `marcar <arquivo> [--idioma en]`,
  `lista`. A skill analisar-perfil ganha o caminho "já tenho currículo".

## 8. Testes

- `tests/test_curriculo_base.py`: candidatos em `anexos/`, máscara (SC-002), perfil com a origem, dados sem IA
  (PT e EN, SC-005), com IA falsa, proposta de filtros validada, marcar/desmarcar, item do checklist por idioma
  (SC-004), confirmação grava tudo e sem confirmação nada (SC-003).

## 9. Notas da implementação

- Os filtros propostos partem dos filtros atuais e só trocam cargos, cidade e modelos: a proposta dos primeiros
  passos remontava a busca no exterior e o filtro de idiomas, e gravá-la desligaria o que a pessoa já configurou.
- "Manter o meu perfil" só marca o currículo: perfil e filtros ficam como estão.
- O idioma do currículo é decidido pelas palavras comuns de português e inglês, sem o mínimo de palavras da detecção
  das vagas (currículo é curto).
