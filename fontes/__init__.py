"""Fontes de vagas (portais).

Cada fonte é um módulo nesta pasta com:

    NOME = "indeed"              # nome usado em config.json -> "fontes"
    PLATAFORMA = "Indeed"        # como aparece no dashboard
    AREAS = ("nacional", "internacional")   # opcional: buscas que o portal atende (ausente = as duas)
    POR_PAIS = True              # opcional: False = portal sem filtro de país (fontes do exterior), que
                                 # roda só na consulta internacional global, uma por cargo
    TERMOS = "…"                 # opcional: resumo dos termos de uso, mostrado no painel

    def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
        '''consulta (montada por filtros.consultas): termo, pais (nome do jobspy, ex.
        "brazil"), pais_nome (em português, ex. "Brasil"), local (texto ou None = país
        inteiro), raio_km (ou None), remoto (bool) e, na busca na cidade, cidade e estado
        separados. Devolve (vagas, erros). Cada vaga no formato comum:
        id, titulo, empresa, local, remoto, publicada_em (AAAA-MM-DD), url,
        url_candidatura, salario, tipo, descricao, plataforma. Opcionais, quando o portal
        informa: restricao_local (onde a pessoa precisa estar), moeda (código de 3 letras),
        ats (greenhouse, lever, ashby), idioma (código de 2 letras) e modelo_trabalho
        (remoto, hibrido, presencial; a análise da IA pode corrigir).
        Na consulta global (POR_PAIS = False), pais e local vêm vazios e "empresas" traz as
        empresas acompanhadas.'''

Opcional, para portais cuja busca não traz a descrição:

    def descrever(vaga: dict) -> str:
        '''A descrição completa da vaga. O vagas.py só chama para as vagas que vão para
        o relatório (as que já estão no dashboard não gastam consulta); se levantar um
        erro, a vaga segue com o que já tinha.'''

O `id` precisa ser estável entre buscas (é ele que impede a mesma vaga de voltar).
Use o identificador do próprio portal; para portais novos, prefixe com o nome da
fonte (ex.: "gupy-12345") para não colidir com outros portais.

Para adicionar um portal: crie fontes/<nome>.py seguindo esse contrato e registre
abaixo em FONTES.
"""
from . import ats, getonboard, gupy, himalayas, indeed, jobicy, remoteok, remotive, startupjobs, weworkremotely

FONTES = {indeed.NOME: indeed, gupy.NOME: gupy, startupjobs.NOME: startupjobs,
          # do exterior, sem filtro de país: ligadas no painel da busca internacional
          remotive.NOME: remotive, himalayas.NOME: himalayas, remoteok.NOME: remoteok, jobicy.NOME: jobicy,
          weworkremotely.NOME: weworkremotely, getonboard.NOME: getonboard, ats.NOME: ats}
