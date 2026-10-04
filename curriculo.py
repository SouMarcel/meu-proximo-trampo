#!/usr/bin/env python3
"""Gera o currículo em .docx (e PDF) a partir de um arquivo JSON.

Usado pela skill gerar-curriculo. O JSON traz o conteúdo; este script cuida do layout:
A4, uma coluna, sem tabelas nem imagens e com títulos de seção padrão, para os sistemas
de triagem (ATS) lerem sem tropeçar.

  python curriculo.py curriculos/base.json            gera base.docx e base.pdf ao lado
  python curriculo.py curriculos/base.json --sem-pdf  só o .docx

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

SECOES = ("resumo", "competencias", "experiencia", "projetos", "formacao",
          "certificacoes", "cursos", "idiomas", "extras")
CHAVES = {"idioma", "fonte", "nome", "titulo", "contato", "ordem", *SECOES}
TITULOS = {
    "pt": {"resumo": "Resumo", "competencias": "Competências", "experiencia": "Experiência profissional",
           "projetos": "Projetos", "formacao": "Formação acadêmica", "certificacoes": "Certificações",
           "cursos": "Cursos", "idiomas": "Idiomas"},
    "en": {"resumo": "Summary", "competencias": "Skills", "experiencia": "Professional experience",
           "projetos": "Projects", "formacao": "Education", "certificacoes": "Certifications",
           "cursos": "Courses", "idiomas": "Languages"},
}
IDIOMA_WORD = {"pt": "pt-BR", "en": "en-US"}
LARGURA_TEXTO = Cm(21 - 2 * 1.9)
COR_TITULO = RGBColor(0x1F, 0x2A, 0x37)
COR_SUAVE = RGBColor(0x4B, 0x55, 0x63)
CAMINHOS_SOFFICE = (
    "C:/Program Files/LibreOffice/program/soffice.exe",
    "C:/Program Files (x86)/LibreOffice/program/soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


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
        self.idioma = cv.get("idioma", "pt")
        self.doc = Document()
        self._preparar(cv.get("fonte") or "Calibri")

    def _preparar(self, fonte: str) -> None:
        doc = self.doc
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(1.9)
        sec.top_margin, sec.bottom_margin = Cm(1.6), Cm(1.5)
        _sem_tema(doc.styles.element)

        normal = doc.styles["Normal"]
        normal.font.size = Pt(10)
        _fonte(normal.element.get_or_add_rPr(), fonte)
        normal.paragraph_format.space_before = Pt(0)
        normal.paragraph_format.space_after = Pt(2)
        normal.paragraph_format.line_spacing = 1.05
        lang = OxmlElement("w:lang")
        lang.set(qn("w:val"), IDIOMA_WORD[self.idioma])
        normal.element.get_or_add_rPr().insert_element_before(lang, "w:eastAsianLayout", "w:specVanish", "w:oMath")

        marcador = doc.styles["List Bullet"]
        marcador.paragraph_format.space_after = Pt(1)
        marcador.paragraph_format.left_indent = Cm(0.5)
        marcador.paragraph_format.first_line_indent = Cm(-0.35)

        props = doc.core_properties
        props.author = self.cv.get("nome", "")
        props.title = ("Currículo" if self.idioma == "pt" else "Resume") + f" - {self.cv.get('nome', '')}"

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
        p = self.par((texto or TITULOS[self.idioma][chave]).upper(), tamanho=10.5, negrito=True, cor=COR_TITULO, depois=4, junto=True)
        p.paragraph_format.space_before = Pt(9)
        _borda_inferior(p)

    def linha_com_data(self, esquerda: str, direita: str = "", *, negrito=True, tamanho=10.5, complemento: str = ""):
        """Texto à esquerda e período alinhado à direita (tabulação, sem tabela)."""
        p = self.par(junto=True, depois=1)
        p.paragraph_format.tab_stops.add_tab_stop(LARGURA_TEXTO, WD_TAB_ALIGNMENT.RIGHT)
        r = p.add_run(esquerda)
        r.bold, r.font.size = negrito, Pt(tamanho)
        if complemento:
            c = p.add_run(complemento)
            c.font.size, c.font.color.rgb = Pt(tamanho - 0.5), COR_SUAVE
        if direita:
            p.add_run().add_tab()
            d = p.add_run(direita)
            d.font.size, d.font.color.rgb = Pt(9.5), COR_SUAVE
        return p

    def marcadores(self, itens) -> None:
        for item in _lista(itens):
            if str(item).strip():
                self.doc.add_paragraph(str(item).strip(), style="List Bullet")

    # seções -------------------------------------------------------------
    def cabecalho(self) -> None:
        cv = self.cv
        self.par(cv["nome"].strip(), tamanho=20, negrito=True, cor=COR_TITULO, depois=1)
        if cv.get("titulo"):
            self.par(cv["titulo"].strip(), tamanho=11.5, cor=COR_SUAVE, depois=2)
        contato = [str(c).strip() for c in _lista(cv.get("contato")) if str(c).strip()]
        if contato:
            self.par(" | ".join(contato), tamanho=9.5, depois=4)

    def resumo(self) -> None:
        self.titulo_secao("resumo")
        for paragrafo in _lista(self.cv["resumo"]):
            self.par(str(paragrafo).strip(), depois=3)

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
                self.par(emp["descricao"].strip(), tamanho=9.5, cor=COR_SUAVE, depois=1, junto=True)
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
        for chave in self.cv.get("ordem") or SECOES:
            if not self.cv.get(chave):
                continue
            if chave in ("certificacoes", "cursos", "idiomas"):
                self.simples(chave)
            else:
                getattr(self, chave)()
        return self.doc


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

def main() -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", help="JSON com o conteúdo do currículo")
    ap.add_argument("--sem-pdf", action="store_true", help="gera só o .docx")
    args = ap.parse_args()

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

    docx = origem.with_suffix(".docx")
    try:
        Montador(cv).montar().save(docx)
    except PermissionError:
        print(f"{docx.name} está aberto em outro programa; feche e rode de novo.", file=sys.stderr)
        return 1
    print(f"Gerado: {docx}")
    if args.sem_pdf:
        return 0
    pdf, motivo = para_pdf(docx)
    if not pdf:
        print(f"PDF não gerado: {motivo}", file=sys.stderr)
        return 1
    n = paginas(pdf)
    print(f"Gerado: {pdf}" + (f" ({n} página{'s' if n != 1 else ''})" if n else ""))
    if n and n > 2:
        print(f"aviso: {n} páginas; o alvo é no máximo 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
