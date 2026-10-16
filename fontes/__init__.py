"""Fontes de vagas (portais).

Cada fonte é um módulo nesta pasta com:

    NOME = "indeed"              # nome usado em config.json -> "fontes"
    PLATAFORMA = "Indeed"        # como aparece no dashboard
    AREAS = ("nacional", "internacional")   # opcional: buscas que o portal atende (ausente = as duas)
    POR_PAIS = True              # opcional: False = portal sem filtro de país (fontes do exterior), que
                                 # roda só na consulta internacional global, uma por cargo
    GLOBAL = True                # opcional: portal por país que também roda na consulta global
                                 # ("mundo todo"), além das consultas por país (ex.: LinkedIn)
    TERMOS = "…"                 # opcional: resumo dos termos de uso, mostrado no painel

    def buscar(consulta: dict, horas: int, por_termo: int) -> tuple[list[dict], list[str]]:
        '''consulta (montada por filtros.consultas): termo, pais (nome do jobspy, ex.
        "brazil"), pais_nome (em português, ex. "Brasil"), local (texto ou None = país
        inteiro), raio_km (ou None), remoto (bool) e, na busca na cidade, cidade e estado
        separados. Devolve (vagas, erros). Cada vaga no formato comum:
        id, titulo, empresa, local, remoto, publicada_em (AAAA-MM-DD), url,
        url_candidatura, salario, tipo, descricao, plataforma. Opcionais, quando o portal
        informa: restricao_local (onde a pessoa precisa estar), moeda (código de 3 letras),
        ats (greenhouse, lever, ashby), idioma (código de 2 letras), modelo_trabalho
        (remoto, hibrido, presencial; a análise da IA pode corrigir) e tipo_emprego (lista
        com os códigos de filtros.TIPOS_EMPREGO).
        Na consulta global (POR_PAIS = False ou GLOBAL = True), pais e local vêm vazios e "empresas" traz as
        empresas acompanhadas.'''

Opcional, para portais cuja busca não traz a descrição:

    def descrever(vaga: dict) -> str:
        '''A descrição completa da vaga. O vagas.py só chama para as vagas que vão para
        o relatório (as que já estão no dashboard não gastam consulta); se levantar um
        erro, a vaga segue com o que já tinha.'''

Opcionais, para portais que limitam os pedidos (ex.: LinkedIn):

    AGRUPAR = True               # o vagas.py junta as consultas de um mesmo grupo numa só: a consulta chega com
                                 # "termos" (os cargos desta parte), "termo" (a expressão de filtros.expressao_or,
                                 # com as aspas de cada cargo) e "agrupada": True
    MAX_DESCRICOES = 20          # no máximo N chamadas a descrever() por busca (contando as que falham); a fila
                                 # começa pelas vagas do dashboard com descricao_pendente desta plataforma, e as
                                 # candidatas que ficarem sem texto saem com descricao_pendente = True

    def espera() -> dict | None:
        '''{"ate": ISO, "motivo": texto} enquanto o portal está em espera depois de um bloqueio; None fora dela.
        Na espera, buscar() devolve ([], [aviso]) na primeira consulta da busca e ([], []) nas outras, e
        descrever() devolve a descrição que a vaga já tinha, sem pedido.'''

    def parada() -> bool:
        '''Verdadeiro se o portal bloqueou nesta busca ou está em espera: a vaga sem texto fica pendente (e não
        é um erro da vaga).'''

O `id` precisa ser estável entre buscas (é ele que impede a mesma vaga de voltar).
Use o identificador do próprio portal; para portais novos, prefixe com o nome da
fonte (ex.: "gupy-12345") para não colidir com outros portais.

Para adicionar um portal: crie fontes/<nome>.py seguindo esse contrato e registre
abaixo em FONTES.
"""
from . import ats, getonboard, gupy, himalayas, indeed, jobicy, linkedin, remoteok, remotive, startupjobs, weworkremotely

FONTES = {indeed.NOME: indeed, gupy.NOME: gupy, linkedin.NOME: linkedin, startupjobs.NOME: startupjobs,
          # do exterior, sem filtro de país: ligadas no painel da busca internacional
          remotive.NOME: remotive, himalayas.NOME: himalayas, remoteok.NOME: remoteok, jobicy.NOME: jobicy,
          weworkremotely.NOME: weworkremotely, getonboard.NOME: getonboard, ats.NOME: ats}
