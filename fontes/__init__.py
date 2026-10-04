"""Fontes de vagas (portais).

Cada fonte é um módulo nesta pasta com:

    NOME = "indeed"              # nome usado em config.json -> "fontes"
    PLATAFORMA = "Indeed"        # como aparece no dashboard

    def buscar(termo: str, cfg: dict, horas: int, por_termo: int, remoto: bool) -> tuple[list[dict], list[str]]:
        '''Devolve (vagas, erros). Cada vaga no formato comum:
        id, titulo, empresa, local, remoto, publicada_em (AAAA-MM-DD), url,
        url_candidatura, salario, tipo, descricao, plataforma'''

O `id` precisa ser estável entre buscas (é ele que impede a mesma vaga de voltar).
Use o identificador do próprio portal; para portais novos, prefixe com o nome da
fonte (ex.: "gupy-12345") para não colidir com outros portais.

Para adicionar um portal: crie fontes/<nome>.py seguindo esse contrato e registre
abaixo em FONTES.
"""
from . import indeed

FONTES = {indeed.NOME: indeed}
