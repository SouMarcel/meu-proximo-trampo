"""Dados de contato da pessoa (spec 033): nome, e-mail, telefone, cidade e links, para a candidatura assistida preencher
em qualquer formulário, sem IA. O campo é reconhecido pelo sentido: o atributo autocomplete, o tipo e sinônimos.

  ler() / gravar(dados) / apagar()   os dados que a pessoa confirmou, em dash/dados/contato.json (fora do Git)
  propor()                           a proposta tirada do currículo base, das respostas já dadas e dos filtros da busca;
                                     não grava nada
  reconhecer(campo)                  qual dado de contato o campo pede, ou None
  valor_para(campo, dados)           o valor no formato do campo (texto ou índice da opção), ou None

Os dados nunca vão para a IA (constituição I e IV). CPF, RG e data de nascimento não entram.
"""
from __future__ import annotations

import json
import os
import re
import threading
import unicodedata

import banco

CAMPOS = ("nome", "sobrenome", "email", "telefone", "cidade", "estado", "pais", "linkedin", "portfolio", "endereco", "cep")
OPCIONAIS = ("endereco", "cep")
FONTE = "seus dados de contato"
TAMANHO, TAMANHO_TELEFONE = 200, 40
TRAVA = threading.Lock()

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DOMINIO = re.compile(r"^(https?://)?[\w-]+(\.[\w-]+)+(/\S*)?$", re.I)
CPF_FORMATADO = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")  # no telefone, 11 dígitos sem pontos são um celular

# autocomplete (padrão HTML) -> dado de contato
AUTOCOMPLETE = {"given-name": "nome", "family-name": "sobrenome", "name": "nome_completo", "email": "email",
                "tel": "telefone", "tel-national": "telefone", "address-level2": "cidade", "address-level1": "estado",
                "country": "pais", "country-name": "pais", "postal-code": "cep", "address-line1": "endereco",
                "street-address": "endereco"}
# a pergunta inteira (normalizada, sem "obrigatório" e afins) precisa ser um destes sinônimos
SINONIMOS = {
    "nome": {"nome", "primeiro nome", "seu nome", "first name", "firstname", "given name", "forename", "name first"},
    "sobrenome": {"sobrenome", "ultimo nome", "last name", "lastname", "family name", "surname", "name last"},
    "nome_completo": {"nome completo", "seu nome completo", "full name", "fullname", "your name", "name", "your full name",
                      "legal name", "full legal name"},
    "email": {"e mail", "email", "seu e mail", "seu email", "endereco de e mail", "endereco de email", "email address",
              "e mail address", "your email", "your email address"},
    "telefone": {"telefone", "celular", "telefone celular", "seu telefone", "seu celular", "whatsapp", "telefone whatsapp",
                 "celular whatsapp", "phone", "phone number", "mobile", "mobile number", "mobile phone", "cell phone",
                 "your phone", "telephone", "contact number"},
    "cidade": {"cidade", "cidade atual", "cidade onde mora", "city", "current city", "town"},
    "estado": {"estado", "uf", "state", "province", "state province", "region"},
    "pais": {"pais", "country", "pais onde mora", "current country"},
    "cep": {"cep", "codigo postal", "postal", "postal code", "zip", "zip code", "zipcode", "postcode"},
    "endereco": {"endereco", "endereco completo", "address", "street address", "address line 1", "street"},
    "linkedin": {"linkedin", "linkedin url", "linkedin profile", "linkedin profile url", "perfil do linkedin",
                 "perfil no linkedin", "link do linkedin", "url do linkedin", "linkedin link"},
    "portfolio": {"portfolio", "portfolio url", "link do portfolio", "site", "website", "web site", "personal website",
                  "site pessoal", "github", "github url", "github profile", "website url", "other website"},
}
# palavras de preenchimento que não mudam o sentido da pergunta
RUIDO = re.compile(r"\b(obrigatorio|obrigatoria|required|optional|opcional|campo)\b")
# o "name" do campo (ex.: first_name, job_application[email]) também conta
NOME_CAMPO = (("first name", "nome"), ("firstname", "nome"), ("given name", "nome"), ("last name", "sobrenome"),
              ("lastname", "sobrenome"), ("family name", "sobrenome"), ("surname", "sobrenome"),
              ("full name", "nome_completo"), ("email", "email"), ("phone", "telefone"), ("telefone", "telefone"),
              ("celular", "telefone"), ("linkedin", "linkedin"), ("city", "cidade"), ("cidade", "cidade"),
              ("zip", "cep"), ("postal", "cep"), ("cep", "cep"))
MEMORIA = {"nome": ("first name", "nome", "primeiro nome", "given name"),
           "sobrenome": ("last name", "sobrenome", "family name", "surname"),
           "email": ("email address", "email", "e mail"), "telefone": ("phone", "telefone", "celular", "mobile"),
           "cidade": ("city", "cidade"), "estado": ("state", "estado"), "cep": ("postal", "postal code", "zip", "cep"),
           "endereco": ("address", "endereco"), "linkedin": ("linkedin", "linkedin profile", "linkedin url")}


def arquivo():
    return banco.ARQUIVO.parent / "contato.json"


def _sem_acento(s) -> str:
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def _norm(s) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", _sem_acento(s)).split())


# ---------------------------------------------------------------- dados salvos

def ler() -> dict:
    """Os dados que a pessoa salvou; {} sem arquivo ou com arquivo ilegível."""
    try:
        d = json.loads(arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(d, dict):
        return {}
    return {k: v.strip() for k, v in d.items() if k in CAMPOS and isinstance(v, str) and v.strip()}


def _parece_documento(campo: str, valor: str) -> bool:
    import primeiros_passos as pp  # na raiz do projeto: as mesmas expressões que tiram documentos do perfil
    cpf = CPF_FORMATADO if campo == "telefone" else pp.CPF
    return bool(cpf.search(valor) or pp.RG.search(valor) or pp.NASCIMENTO.search(valor))


def gravar(dados) -> dict:
    """Valida e grava os dados que a pessoa confirmou (os vazios não entram). ValueError com a regra que falhou."""
    if not isinstance(dados, dict):
        raise ValueError("dados inválidos")
    limpos = {}
    for campo in CAMPOS:
        valor = " ".join(str(dados.get(campo) or "").split())
        if not valor:
            continue
        if len(valor) > (TAMANHO_TELEFONE if campo == "telefone" else TAMANHO):
            raise ValueError(f"{campo}: texto longo demais")
        if _parece_documento(campo, valor):
            raise ValueError(f"parece um documento (CPF, RG ou data de nascimento) em {campo}: não guarde documentos aqui")
        if campo == "email" and not EMAIL.match(valor):
            raise ValueError("e-mail inválido")
        if campo == "linkedin" and "linkedin.com/" not in valor.lower():
            raise ValueError("o LinkedIn precisa ser um link do linkedin.com (ex.: linkedin.com/in/seu-nome)")
        if campo == "portfolio" and not DOMINIO.match(valor):
            raise ValueError("o portfólio precisa ser um link (ex.: https://seu-site.com)")
        limpos[campo] = valor
    with TRAVA:
        arq = arquivo()
        arq.parent.mkdir(parents=True, exist_ok=True)
        tmp = arq.with_name(arq.name + ".tmp")
        tmp.write_text(json.dumps(limpos, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, arq)
    return limpos


def apagar() -> dict:
    with TRAVA:
        try:
            arquivo().unlink()
        except FileNotFoundError:
            pass
    return {}


# ---------------------------------------------------------------- proposta

def _nome_da_linha(texto: str) -> tuple[str, str] | None:
    """(nome, sobrenome) da primeira linha que parece um nome: de 2 a 6 palavras, só letras, até 60 caracteres."""
    for linha in str(texto or "").splitlines()[:8]:
        linha = " ".join(linha.split())
        if not linha:
            continue
        palavras = linha.split()
        if (len(linha) <= 60 and 2 <= len(palavras) <= 6 and "@" not in linha
                and all(re.fullmatch(r"[^\W\d_]+(['’-][^\W\d_]+)*\.?", p) for p in palavras)):
            return palavras[0], " ".join(palavras[1:])
        return None  # a primeira linha com texto não é um nome: melhor deixar para a pessoa
    return None


def _do_curriculo(dados: dict, fontes: dict, avisos: list) -> None:
    try:
        import curriculo_base
        import primeiros_passos as pp
        marcados = curriculo_base.marcados()
    except Exception:  # config ausente ou com erro: segue com a memória e os filtros
        marcados = {}
    caminho = marcados.get("pt") or marcados.get("en")
    if not caminho:
        avisos.append("sem currículo base marcado: a proposta usa as respostas já dadas e os filtros da busca")
        return
    try:
        lido = pp.extrair(caminho)
    except Exception as e:  # PDF ilegível, falta o pypdf…: vira aviso
        avisos.append(f"não deu para ler o currículo base ({e})")
        return
    contato = lido.get("contato") or pp.reconhecer_contato(lido.get("texto") or "")
    nome = _nome_da_linha(lido.get("texto") or "")
    if nome:
        dados["nome"], dados["sobrenome"] = nome
    for campo, lista in (("email", contato.get("emails") or []), ("telefone", contato.get("telefones") or [])):
        if lista:
            dados[campo] = lista[0]
            if len(lista) > 1:
                avisos.append(f"o currículo traz {len(lista)} {'e-mails' if campo == 'email' else 'telefones'}; ficou o primeiro")
    if contato.get("linkedin"):
        dados["linkedin"] = contato["linkedin"]
    for campo in dados:
        fontes[campo] = "currículo"


def _da_memoria(dados: dict, fontes: dict) -> None:
    from . import memoria
    guardadas = memoria._carregar()
    for campo, chaves in MEMORIA.items():
        if dados.get(campo):
            continue
        for k in chaves:
            r = guardadas.get(k)
            if r and str(r.get("resposta") or "").strip():
                dados[campo], fontes[campo] = str(r["resposta"]).strip(), "respostas anteriores"
                break


def _dos_filtros(dados: dict, fontes: dict) -> None:
    try:
        import filtros
        loc = filtros.efetivos(filtros.ler_config())["localidade"]
    except Exception:
        return
    for campo, valor in (("cidade", loc.get("cidade")), ("estado", loc.get("estado")), ("pais", loc.get("pais"))):
        if valor and not dados.get(campo):
            dados[campo], fontes[campo] = str(valor), "filtros da busca"


def propor() -> dict:
    """{dados, fontes, avisos}: a proposta para a pessoa conferir. Não grava nada."""
    dados, fontes, avisos = {}, {}, []
    _do_curriculo(dados, fontes, avisos)
    _da_memoria(dados, fontes)
    _dos_filtros(dados, fontes)
    dados = {k: v for k, v in dados.items() if k in CAMPOS and v}
    return {"dados": dados, "fontes": {k: fontes[k] for k in dados}, "avisos": avisos}


# ---------------------------------------------------------------- reconhecer e preencher

def _pergunta(campo: dict) -> str:
    t = _norm(campo.get("rotulo"))
    return " ".join(RUIDO.sub(" ", t).split())


def reconhecer(campo: dict) -> str | None:
    """O dado de contato que o campo pede (nome, sobrenome, nome_completo, email, telefone, cidade, estado, pais, cep,
    endereco, linkedin, portfolio) ou None. Campo sensível nunca recebe dado de contato."""
    if campo.get("marca") == "sensivel":
        return None
    pergunta, nome_html = _pergunta(campo), _norm(campo.get("nome"))
    fala_linkedin = "linkedin" in pergunta or "linkedin" in nome_html
    ac = _sem_acento(campo.get("autocomplete")).split()
    for token in ac:
        if token == "url":
            return "linkedin" if fala_linkedin else "portfolio"
        if token in AUTOCOMPLETE:
            return AUTOCOMPLETE[token]
    tipo_html = str(campo.get("tipo_html") or "").lower()
    if tipo_html == "email":
        return "email"
    if tipo_html == "tel":
        return "telefone"
    if tipo_html == "url":
        return "linkedin" if fala_linkedin else "portfolio"
    for dado, nomes in SINONIMOS.items():
        if pergunta in nomes:
            return dado
    if not pergunta:
        for trecho, dado in NOME_CAMPO:
            if re.search(rf"(^| ){trecho}( |$)", nome_html):
                return dado
    return None


def _opcao(campo: dict, alvos: list[str]) -> str | None:
    alvos = {_norm(a) for a in alvos if a}
    achados = [o["valor"] for o in campo.get("opcoes") or [] if not o.get("vazia") and _norm(o.get("texto")) in alvos]
    return achados[0] if len(achados) == 1 else None


def valor_para(campo: dict, dados: dict) -> str | None:
    """O valor do dado de contato no formato do campo: texto, ou o índice da opção numa lista. None sem o dado, sem
    opção que bata ou quando não cabe no campo."""
    dado = reconhecer(campo)
    if not dado:
        return None
    if dado == "nome_completo":
        valor = " ".join(x for x in (dados.get("nome"), dados.get("sobrenome")) if x)
    else:
        valor = dados.get(dado) or ""
    if not valor:
        return None
    tipo = campo.get("tipo")
    if tipo in ("selecao", "lista", "unica"):
        alvos = [valor]
        if dado == "pais":
            import filtros
            alvos.append(filtros.PAISES.get(valor, ""))
            if valor == "Estados Unidos":
                alvos += ["united states", "united states of america"]
        elif dado == "estado":
            from fontes import _comum
            sigla = valor.strip().upper()
            alvos += [_comum.UFS.get(sigla, ""), *[k for k, v in _comum.UFS.items() if v == _norm(valor)]]
        return _opcao(campo, alvos)
    if tipo not in ("texto", "area"):
        return None
    limite = int(campo.get("limite") or 0)
    return None if limite and len(valor) > limite else valor
