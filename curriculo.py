#!/usr/bin/env python3
"""Gera o currículo em .docx (e PDF) a partir de um arquivo JSON.

Usado pela skill gerar-curriculo. O JSON traz o conteúdo; este script cuida do layout:
A4, uma coluna, sem tabelas nem imagens e com títulos de seção padrão, para os sistemas
de triagem (ATS) lerem sem tropeçar.

  python curriculo.py curriculos/base.json            gera base.docx e base.pdf ao lado
  python curriculo.py curriculos/base.json --sem-pdf  só o .docx
  python curriculo.py --tecnicas [--vaga-id ID]       técnicas e escolhas, com a sugestão para o alvo (JSON)

Com "tecnicas" no JSON, valem o formato do país (papel e idioma), o estilo, a ordem e o limite de
páginas escolhidos; sem, o layout de sempre. No fim, com perfil, roda a conferência (conferir.py).
Códigos de saída: 0 ok, 1 erro de geração, 2 JSON inválido, 3 acima do limite de páginas ou
conferência "bloquear".

O PDF sai pelo LibreOffice, se estiver instalado, ou pelo Microsoft Word no Windows.
Modelo do JSON: .claude/skills/gerar-curriculo/modelo.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.enum.text import WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor
except ImportError:
    sys.exit("Falta a biblioteca python-docx. Rode: pip install -r requirements.txt")

SECOES = ("resumo", "destaques", "competencias", "experiencia", "projetos", "formacao",
          "certificacoes", "cursos", "idiomas", "extras")
CHAVES = {"idioma", "fonte", "nome", "titulo", "contato", "ordem", "tecnicas", *SECOES}
TITULOS = {
    "pt": {"resumo": "Resumo", "destaques": "Destaques", "competencias": "Competências", "experiencia": "Experiência profissional",
           "projetos": "Projetos", "formacao": "Formação acadêmica", "certificacoes": "Certificações",
           "cursos": "Cursos", "idiomas": "Idiomas"},
    "en": {"resumo": "Summary", "destaques": "Highlights", "competencias": "Skills", "experiencia": "Professional experience",
           "projetos": "Projects", "formacao": "Education", "certificacoes": "Certifications",
           "cursos": "Courses", "idiomas": "Languages"},
}
IDIOMA_WORD = {"pt": "pt-BR", "en": "en-US"}
COR_TITULO = RGBColor(0x1F, 0x2A, 0x37)
COR_SUAVE = RGBColor(0x4B, 0x55, 0x63)
CAMINHOS_SOFFICE = (
    "C:/Program Files/LibreOffice/program/soffice.exe",
    "C:/Program Files (x86)/LibreOffice/program/soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)

# ---------------------------------------------------------------- técnicas (catálogo único: skill e página)

TECNICAS = {
    "ats": {"nome": "ATS", "padrao": True,
            "explicacao": "Leitura fácil por sistemas de triagem: texto simples, seções padrão, contato no corpo e as "
                          "palavras-chave da vaga reformuladas a partir do que você tem (nunca inventadas)."},
    "foco": {"nome": "Foco", "padrao": False,
             "explicacao": "Escolhe e ordena as experiências e itens que mais servem ao cargo-alvo e abre uma seção "
                           "de destaques (até 3)."},
    "xyz": {"nome": "XYZ (estilo Google)", "padrao": False,
            "explicacao": "Conquistas como 'realizou X, medido por Y, fazendo Z', só com número que você confirmou; "
                          "sem número, a conquista fica sem medida."},
    "resultado_primeiro": {"nome": "Resultado primeiro", "padrao": False,
                           "explicacao": "Cada item começa pelo resultado e depois diz como foi feito."},
    "competencias_primeiro": {"nome": "Competências primeiro", "padrao": False,
                              "explicacao": "A seção de competências vem antes da experiência."},
}
ESCOLHAS = {
    "paginas": {"nome": "Páginas", "padrao": 2, "opcoes": {1: "1 página", 2: "Até 2 páginas"}},
    "formato": {"nome": "Formato do país", "padrao": "br",
                "opcoes": {"br": "Brasil (A4, português)",
                           "us": "Estados Unidos (Letter, inglês, sem foto nem dados pessoais)",
                           "eu": "Europa (A4, inglês)"}},
    "estilo": {"nome": "Estilo visual", "padrao": "padrao",
               "opcoes": {"padrao": "Padrão", "compacto": "Compacto (cabe mais por página)",
                          "executivo": "Executivo (fonte maior, mais respiro)"}},
}
FORMATOS = {"br": {"papel": (Cm(21), Cm(29.7)), "idioma": "pt"},
            "us": {"papel": (Cm(21.59), Cm(27.94)), "idioma": "en"},
            "eu": {"papel": (Cm(21), Cm(29.7)), "idioma": "en"}}
# corpo nunca abaixo de 10 pt; "padrao" reproduz o layout anterior às técnicas
ESTILOS = {
    "padrao": {"margem_lado": 1.9, "margem_topo": 1.6, "margem_base": 1.5, "corpo": 10, "depois": 2, "linha": 1.05,
               "marcador": 1, "nome": 20, "titulo": 11.5, "secao": 10.5, "antes_secao": 9},
    "compacto": {"margem_lado": 1.5, "margem_topo": 1.2, "margem_base": 1.2, "corpo": 10, "depois": 1, "linha": 1.0,
                 "marcador": 0, "nome": 17, "titulo": 10.5, "secao": 10, "antes_secao": 6},
    "executivo": {"margem_lado": 2.2, "margem_topo": 1.9, "margem_base": 1.7, "corpo": 10.5, "depois": 3, "linha": 1.1,
                  "marcador": 2, "nome": 22, "titulo": 12, "secao": 11, "antes_secao": 11},
}
PROIBIDOS_US = ("foto", "nascimento", "estado_civil", "nacionalidade", "documentos")
MAX_DESTAQUES = 3
PAISES_EUROPA = ("portugal", "espanha", "spain", "alemanha", "germany", "franca", "france", "holanda", "netherlands",
                 "paises baixos", "irlanda", "ireland", "italia", "italy", "reino unido", "united kingdom", "uk",
                 "england", "inglaterra", "londres", "london", "polonia", "poland", "suecia", "sweden", "suica",
                 "switzerland", "belgica", "belgium", "austria", "dinamarca", "denmark", "noruega", "norway",
                 "finlandia", "finland", "europa", "europe", "emea", "lisboa", "lisbon", "berlim", "berlin",
                 "madrid", "amsterdam", "dublin", "paris")
EUA = ("united states", "estados unidos", "usa", "u.s.", "eua", "us only", "us-based", "new york", "san francisco",
       "california", "texas", "seattle", "boston", "chicago", "austin")
PALAVRAS_EN = set("the and of to in for with you we our your is are will be on as an this that team experience".split())
PALAVRAS_PT = set("de da do das dos para com voce nossa nosso em que uma um os as e experiencia equipe vaga".split())


def _sem_acento(s) -> str:
    import unicodedata
    return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()


def ler_tecnicas(cv: dict) -> dict | None:
    """As técnicas do JSON com os padrões preenchidos; None quando o JSON não traz "tecnicas" (layout de antes)."""
    bruto = cv.get("tecnicas")
    if not isinstance(bruto, dict):
        return None
    tec = {k: bool(bruto.get(k, v["padrao"])) for k, v in TECNICAS.items()}
    tec.update({k: bruto.get(k, v["padrao"]) for k, v in ESCOLHAS.items()})
    return tec


def sugerir(vaga: dict | None = None) -> dict:
    """Escolhas sugeridas para o alvo: sem vaga, Brasil; vaga dos EUA, formato americano; da Europa, europeu."""
    tec = {k: v["padrao"] for k, v in TECNICAS.items()}
    tec.update({k: v["padrao"] for k, v in ESCOLHAS.items()})
    if not vaga:
        return {**tec, "motivo": "currículo base: formato do Brasil"}
    tudo = _sem_acento(" ".join(str(vaga.get(k) or "") for k in ("titulo", "local", "descricao")))
    local = _sem_acento(vaga.get("local"))
    palavras = re.findall(r"[a-z]+", tudo)
    en = sum(p in PALAVRAS_EN for p in palavras)
    pt = sum(p in PALAVRAS_PT for p in palavras)
    na = lambda lista, texto: any(re.search(r"(?<![a-z])" + re.escape(x) + r"(?![a-z])", texto) for x in lista)
    if na(EUA, local) or (en > pt and na(EUA, tudo)):
        return {**tec, "formato": "us", "motivo": "vaga dos Estados Unidos: formato americano, em inglês"}
    if na(PAISES_EUROPA, local) or (en > pt and na(PAISES_EUROPA, tudo)):
        return {**tec, "formato": "eu", "motivo": "vaga na Europa: formato europeu, em inglês"}
    if en > pt * 1.5 and en >= 10:
        return {**tec, "formato": "eu", "motivo": "vaga em inglês fora dos Estados Unidos: formato europeu, em inglês"}
    return {**tec, "motivo": "vaga no Brasil: formato do Brasil"}


def catalogo(vaga: dict | None = None) -> dict:
    """O que a skill e a página mostram como caixas de marcar e escolhas, com a sugestão para o alvo."""
    return {"tecnicas": TECNICAS, "escolhas": {k: {**v, "opcoes": {str(o): r for o, r in v["opcoes"].items()}}
                                              for k, v in ESCOLHAS.items()},
            "sugestao": sugerir(vaga)}



# ---------------------------------------------------------------- conteúdo

def validar(cv: dict) -> list[str]:
    """Erros que impedem gerar; avisos vão para a saída padrão."""
    erros = []
    if not str(cv.get("nome") or "").strip():
        erros.append("'nome' é obrigatório")
    if cv.get("idioma", "pt") not in TITULOS:
        erros.append(f"'idioma' deve ser um de {tuple(TITULOS)}")
    for k in sorted(set(cv) - CHAVES):
        print(f"aviso: chave desconhecida {k!r} ignorada (válidas: {', '.join(sorted(CHAVES))})")
    for k in cv.get("ordem") or []:
        if k not in SECOES:
            erros.append(f"'ordem' tem seção desconhecida {k!r}")
    tec = cv.get("tecnicas")
    if tec is not None:
        if not isinstance(tec, dict):
            erros.append("'tecnicas' deve ser um objeto")
        else:
            for k, v in tec.items():
                if k in TECNICAS:
                    if not isinstance(v, bool):
                        erros.append(f"tecnicas.{k} deve ser true ou false")
                elif k in ESCOLHAS:
                    if v not in ESCOLHAS[k]["opcoes"]:
                        erros.append(f"tecnicas.{k} deve ser um de {tuple(ESCOLHAS[k]['opcoes'])}")
                else:
                    erros.append(f"'tecnicas' tem chave desconhecida {k!r}")
            if tec.get("formato") == "us":
                erros += [f"no formato dos Estados Unidos o currículo não leva '{k}'" for k in PROIBIDOS_US if cv.get(k)]
            formato = FORMATOS.get(tec.get("formato") or "br")
            if formato and cv.get("idioma") and cv["idioma"] != formato["idioma"]:
                print(f"aviso: 'idioma' {cv['idioma']!r} ignorado; o formato {tec.get('formato') or 'br'!r} usa {formato['idioma']!r}")
    destaques = cv.get("destaques")
    if destaques is not None and (not isinstance(destaques, list) or len(destaques) > MAX_DESTAQUES):
        erros.append(f"'destaques' deve ser uma lista com até {MAX_DESTAQUES} itens")
    for i, emp in enumerate(cv.get("experiencia") or []):
        if not emp.get("empresa"):
            erros.append(f"experiencia[{i}] sem 'empresa'")
        if not emp.get("cargos") and not emp.get("cargo"):
            erros.append(f"experiencia[{i}] ({emp.get('empresa')}) sem 'cargos' nem 'cargo'")
    return erros


def _lista(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


# ---------------------------------------------------------------- layout

def _sem_tema(raiz) -> None:
    """Tira as fontes do tema (Calibri Light etc.) para valer a fonte escolhida."""
    for rf in raiz.iter(qn("w:rFonts")):
        for atributo in list(rf.attrib):
            if atributo.endswith("Theme"):
                del rf.attrib[atributo]


def _fonte(rpr, nome: str) -> None:
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(k), nome)


def _borda_inferior(par) -> None:
    ppr = par._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    linha = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "9CA3AF")):
        linha.set(qn(k), v)
    bdr.append(linha)
    ppr.insert_element_before(
        bdr, "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct",
        "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd", "w:snapToGrid",
        "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
        "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl", "w:divId",
        "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange")


class Montador:
    def __init__(self, cv: dict):
        self.cv = cv
        self.tec = ler_tecnicas(cv)
        self.idioma = FORMATOS[self.tec["formato"]]["idioma"] if self.tec else cv.get("idioma", "pt")
        self.e = ESTILOS[self.tec["estilo"] if self.tec else "padrao"]
        self.delta = self.e["corpo"] - 10  # os tamanhos menores acompanham o corpo
        self.doc = Document()
        self._preparar(cv.get("fonte") or "Calibri")

    def t(self, tamanho: float) -> float:
        return tamanho + self.delta

    def _preparar(self, fonte: str) -> None:
        doc, e = self.doc, self.e
        sec = doc.sections[0]
        largura, altura = FORMATOS[self.tec["formato"]]["papel"] if self.tec else (Cm(21), Cm(29.7))
        sec.page_width, sec.page_height = largura, altura
        sec.left_margin = sec.right_margin = Cm(e["margem_lado"])
        sec.top_margin, sec.bottom_margin = Cm(e["margem_topo"]), Cm(e["margem_base"])
        self.largura = largura - 2 * Cm(e["margem_lado"])
        _sem_tema(doc.styles.element)

        normal = doc.styles["Normal"]
        normal.font.size = Pt(e["corpo"])
        _fonte(normal.element.get_or_add_rPr(), fonte)
        normal.paragraph_format.space_before = Pt(0)
        normal.paragraph_format.space_after = Pt(e["depois"])
        normal.paragraph_format.line_spacing = e["linha"]
        lang = OxmlElement("w:lang")
        lang.set(qn("w:val"), IDIOMA_WORD[self.idioma])
        normal.element.get_or_add_rPr().insert_element_before(lang, "w:eastAsianLayout", "w:specVanish", "w:oMath")

        marcador = doc.styles["List Bullet"]
        marcador.paragraph_format.space_after = Pt(e["marcador"])
        marcador.paragraph_format.left_indent = Cm(0.5)
        marcador.paragraph_format.first_line_indent = Cm(-0.35)

        props = doc.core_properties
        props.author = self.cv.get("nome", "")
        props.title = ("Currículo" if self.idioma == "pt" else "Resume") + f" - {self.cv.get('nome', '')}"
        if self.tec:
            props.comments = descrever_tecnicas(self.tec)

    # blocos -------------------------------------------------------------
    def par(self, texto: str = "", *, tamanho=None, negrito=False, cor=None, depois=None, junto=False):
        p = self.doc.add_paragraph()
        if texto:
            r = p.add_run(texto)
            r.bold = negrito
            if tamanho:
                r.font.size = Pt(tamanho)
            if cor:
                r.font.color.rgb = cor
        if depois is not None:
            p.paragraph_format.space_after = Pt(depois)
        if junto:
            p.paragraph_format.keep_with_next = True
        return p

    def titulo_secao(self, chave: str, texto: str | None = None) -> None:
        p = self.par((texto or TITULOS[self.idioma][chave]).upper(), tamanho=self.e["secao"], negrito=True, cor=COR_TITULO,
                     depois=4, junto=True)
        p.paragraph_format.space_before = Pt(self.e["antes_secao"])
        _borda_inferior(p)

    def linha_com_data(self, esquerda: str, direita: str = "", *, negrito=True, tamanho=10.5, complemento: str = ""):
        """Texto à esquerda e período alinhado à direita (tabulação, sem tabela)."""
        tamanho = self.t(tamanho)
        p = self.par(junto=True, depois=1)
        p.paragraph_format.tab_stops.add_tab_stop(self.largura, WD_TAB_ALIGNMENT.RIGHT)
        r = p.add_run(esquerda)
        r.bold, r.font.size = negrito, Pt(tamanho)
        if complemento:
            c = p.add_run(complemento)
            c.font.size, c.font.color.rgb = Pt(tamanho - 0.5), COR_SUAVE
        if direita:
            p.add_run().add_tab()
            d = p.add_run(direita)
            d.font.size, d.font.color.rgb = Pt(self.t(9.5)), COR_SUAVE
        return p

    def marcadores(self, itens) -> None:
        for item in _lista(itens):
            if str(item).strip():
                self.doc.add_paragraph(str(item).strip(), style="List Bullet")

    # seções -------------------------------------------------------------
    def cabecalho(self) -> None:
        cv = self.cv
        self.par(cv["nome"].strip(), tamanho=self.e["nome"], negrito=True, cor=COR_TITULO, depois=1)
        if cv.get("titulo"):
            self.par(cv["titulo"].strip(), tamanho=self.e["titulo"], cor=COR_SUAVE, depois=2)
        contato = [str(c).strip() for c in _lista(cv.get("contato")) if str(c).strip()]
        if contato:
            self.par(" | ".join(contato), tamanho=self.t(9.5), depois=4)

    def resumo(self) -> None:
        self.titulo_secao("resumo")
        for paragrafo in _lista(self.cv["resumo"]):
            self.par(str(paragrafo).strip(), depois=3)

    def destaques(self) -> None:
        self.titulo_secao("destaques")
        self.marcadores(self.cv["destaques"])

    def competencias(self) -> None:
        self.titulo_secao("competencias")
        soltos = []
        for g in _lista(self.cv["competencias"]):
            if isinstance(g, dict):
                p = self.par(depois=2)
                p.add_run(f"{g.get('grupo', '').strip()}: ").bold = True
                p.add_run(", ".join(str(i).strip() for i in _lista(g.get("itens"))))
            else:
                soltos.append(str(g).strip())
        if soltos:
            self.par(" · ".join(soltos), depois=2)

    def experiencia(self) -> None:
        self.titulo_secao("experiencia")
        for emp in self.cv["experiencia"]:
            cargos = emp.get("cargos") or [{"cargo": emp.get("cargo"), "itens": emp.get("itens")}]
            # o período aparece uma vez só: na empresa e, nos cargos, só quando difere dele
            periodo_emp = emp.get("periodo") or (cargos[0].get("periodo") if len(cargos) == 1 else "") or ""
            local = emp.get("local") or ""
            p = self.linha_com_data(emp["empresa"].strip(), periodo_emp, complemento=f" · {local}" if local else "")
            p.paragraph_format.space_before = Pt(5)
            if emp.get("descricao"):
                self.par(emp["descricao"].strip(), tamanho=self.t(9.5), cor=COR_SUAVE, depois=1, junto=True)
            for cargo in cargos:
                periodo = cargo.get("periodo") or ""
                self.linha_com_data(str(cargo.get("cargo") or "").strip(), "" if periodo == periodo_emp else periodo, tamanho=10,
                                    complemento=f" · {cargo['local']}" if cargo.get("local") and cargo.get("local") != local else "")
                self.marcadores(cargo.get("itens"))

    def projetos(self) -> None:
        self.titulo_secao("projetos")
        for pj in self.cv["projetos"]:
            if isinstance(pj, str):
                self.marcadores([pj])
                continue
            p = self.linha_com_data(str(pj.get("nome") or "").strip(), pj.get("periodo") or "", tamanho=10)
            p.paragraph_format.space_before = Pt(3)
            if pj.get("descricao"):
                self.par(pj["descricao"].strip(), depois=1)
            self.marcadores(pj.get("itens"))

    def formacao(self) -> None:
        self.titulo_secao("formacao")
        for f in self.cv["formacao"]:
            if isinstance(f, str):
                self.marcadores([f])
                continue
            status = f" ({f['status']})" if f.get("status") else ""
            self.linha_com_data(f"{str(f.get('curso') or '').strip()}{status}", f.get("periodo") or "", tamanho=10,
                                complemento=f" · {f['instituicao']}" if f.get("instituicao") else "")

    def simples(self, chave: str) -> None:
        self.titulo_secao(chave)
        self.marcadores(self.cv[chave])

    def extras(self) -> None:
        for bloco in _lista(self.cv["extras"]):
            padrao = "Outros" if self.idioma == "pt" else "Other"
            self.titulo_secao("extras", str(bloco.get("titulo") or "").strip() or padrao)
            self.marcadores(bloco.get("itens"))

    def montar(self):
        self.cabecalho()
        for chave in ordem_das_secoes(self.cv, self.tec):
            if not self.cv.get(chave):
                continue
            if chave in ("certificacoes", "cursos", "idiomas"):
                self.simples(chave)
            else:
                getattr(self, chave)()
        return self.doc


def ordem_das_secoes(cv: dict, tec: dict | None) -> list[str]:
    """A ordem do JSON; sem ela, a padrão, com competências antes da experiência se a técnica pedir."""
    if cv.get("ordem"):
        return list(cv["ordem"])
    ordem = list(SECOES)
    if tec and tec["competencias_primeiro"]:
        ordem.remove("competencias")
        ordem.insert(ordem.index("experiencia"), "competencias")
    return ordem


def descrever_tecnicas(tec: dict) -> str:
    marcadas = [TECNICAS[k]["nome"] for k in TECNICAS if tec.get(k)]
    return (f"Técnicas: {', '.join(marcadas) or 'nenhuma'}; formato {tec['formato']}; estilo {tec['estilo']}; "
            f"até {tec['paginas']} página(s)")


def sugestoes_corte(cv: dict) -> list[str]:
    """O que cortar quando passa do limite de páginas (sem encolher a fonte)."""
    sugestoes = []
    exps = _lista(cv.get("experiencia"))
    if len(exps) > 2:
        antigas = ", ".join(str(e.get("empresa")) for e in exps[-2:])
        sugestoes.append(f"resumir ou tirar as experiências mais antigas ({antigas})")
    for e in exps:
        for c in e.get("cargos") or [e]:
            if len(_lista(c.get("itens"))) > 5:
                sugestoes.append(f"deixar até 5 itens em {c.get('cargo') or e.get('empresa')} "
                                 f"(hoje {len(_lista(c.get('itens')))})")
    if len(_lista(cv.get("cursos"))) > 3:
        sugestoes.append("deixar só os cursos mais recentes ou ligados ao alvo")
    if len(" ".join(str(p) for p in _lista(cv.get("resumo")))) > 450:
        sugestoes.append("encurtar o resumo para 3 ou 4 linhas")
    if cv.get("projetos"):
        sugestoes.append("tirar projetos que não falam do alvo")
    return sugestoes or ["revisar os itens menos ligados ao alvo"]


# ---------------------------------------------------------------- PDF

def _soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice") or next(
        (c for c in CAMINHOS_SOFFICE if Path(c).exists()), None)


def para_pdf(docx: Path) -> tuple[Path | None, str]:
    """Converte com LibreOffice ou, no Windows, com o Word. Devolve (pdf, motivo da falha)."""
    pdf = docx.with_suffix(".pdf")
    try:
        pdf.unlink(missing_ok=True)
    except PermissionError:
        return None, f"{pdf.name} está aberto em outro programa; feche e rode de novo"
    soffice = _soffice()
    if soffice:
        r = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
                           capture_output=True, text=True, timeout=240)
        return (pdf, "") if pdf.exists() else (None, f"LibreOffice falhou: {(r.stderr or r.stdout).strip()[:300]}")
    if sys.platform == "win32":
        script = ("$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0; "
                  "try { $d = $w.Documents.Open($env:CV_DOCX, $false, $true); "
                  "$d.ExportAsFixedFormat($env:CV_PDF, 17); $d.Close($false) } finally { $w.Quit() }")
        env = {**os.environ, "CV_DOCX": str(docx.resolve()), "CV_PDF": str(pdf.resolve())}
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                               env=env, capture_output=True, text=True, timeout=240)
        except FileNotFoundError:
            return None, "PowerShell não encontrado"
        return (pdf, "") if pdf.exists() else (None, f"Word não converteu: {(r.stderr or r.stdout).strip()[:300] or 'Word instalado?'}")
    return None, "instale o LibreOffice para gerar o PDF (ou abra o .docx no Word e salve como PDF)"


def paginas(pdf: Path) -> int | None:
    n = len(re.findall(rb"/Type */Page[^s]", pdf.read_bytes()))
    return n or None


# ---------------------------------------------------------------- linha de comando

def rodar_conferencia(cv: dict, docx: Path, vaga: str | None) -> int:
    """Conferência sem IA (conferir.py) contra o perfil do config.json. Devolve 3 com "bloquear"."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conferir
    perfil = conferir.perfil_padrao()
    if not perfil.exists():
        print(f"\nConferência não rodou: perfil não encontrado ({perfil.name}).")
        return 0
    r = conferir.conferir(cv, perfil.read_text(encoding="utf-8"), vaga, docx)
    print("\nConferência (sem IA):\n" + conferir.texto(r))
    if r["veredito"] == "bloquear":
        print("\nNão entregue este currículo antes de resolver os pontos marcados como bloquear.")
        return 3
    return 0


def _vaga(args) -> tuple[dict | None, str | None]:
    """(vaga do dashboard ou do arquivo, texto dela) para a sugestão e a conferência."""
    if args.vaga_id:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "dash"))
        import banco
        v = banco.obter(args.vaga_id)
        if not v:
            raise ValueError(f"vaga {args.vaga_id} não encontrada no dashboard")
        return v, "\n".join(str(x) for x in (v.get("titulo"), v.get("empresa"), v.get("local"), v.get("descricao")) if x)
    if args.vaga:
        texto = Path(args.vaga).read_text(encoding="utf-8")
        return {"descricao": texto}, texto
    return None, None


def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", nargs="?", help="JSON com o conteúdo do currículo")
    ap.add_argument("--sem-pdf", action="store_true", help="gera só o .docx")
    ap.add_argument("--tecnicas", action="store_true", help="mostra as técnicas e escolhas, com a sugestão, em JSON")
    ap.add_argument("--vaga-id", help="vaga do dashboard (sugestão e conferência dos requisitos)")
    ap.add_argument("--vaga", help="arquivo com o texto da vaga")
    args = ap.parse_args()
    try:
        vaga, vaga_texto = _vaga(args)
    except (OSError, ValueError) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    if args.tecnicas:
        print(json.dumps(catalogo(vaga), ensure_ascii=False, indent=1))
        return 0
    if not args.arquivo:
        ap.error("informe o arquivo JSON (ou use --tecnicas)")

    origem = Path(args.arquivo)
    try:
        cv = json.loads(origem.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {origem}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"JSON inválido em {origem}: {e}", file=sys.stderr)
        return 2
    erros = validar(cv)
    if erros:
        for e in erros:
            print(f"erro: {e}", file=sys.stderr)
        return 2

    tec = ler_tecnicas(cv)
    docx = origem.with_suffix(".docx")
    try:
        Montador(cv).montar().save(docx)
    except PermissionError:
        print(f"{docx.name} está aberto em outro programa; feche e rode de novo.", file=sys.stderr)
        return 1
    print(f"Gerado: {docx}" + (f" ({descrever_tecnicas(tec)})" if tec else ""))
    codigo = 0
    if args.sem_pdf:
        if tec:
            print("aviso: sem PDF, as páginas não foram medidas.")
    else:
        pdf, motivo = para_pdf(docx)
        if not pdf:
            print(f"PDF não gerado: {motivo}", file=sys.stderr)
            codigo = 1
        else:
            n = paginas(pdf)
            print(f"Gerado: {pdf}" + (f" ({n} página{'s' if n != 1 else ''})" if n else ""))
            limite = tec["paginas"] if tec else 2
            if n and n > limite and tec:
                print(f"acima do limite: deu {n} páginas; o limite é {limite}. Em vez de encolher a fonte, corte:")
                for sugestao in sugestoes_corte(cv):
                    print(f"  - {sugestao}")
                codigo = 3
            elif n and n > limite:
                print(f"aviso: {n} páginas; o alvo é no máximo 2.")
            elif not n and tec:
                print("aviso: as páginas não foram medidas.")
    return max(codigo, rodar_conferencia(cv, docx, vaga_texto))


if __name__ == "__main__":
    sys.exit(main())
