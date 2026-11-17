#!/usr/bin/env python3
"""Delega uma tarefa de implementação a um "funcionário" (outro assistente de código) e resume o resultado.

Ferramenta de desenvolvimento, como sincronizar_skills.py: o assistente principal (Claude Code) planeja,
escreve o brief da tarefa em specs/NNN-nome/delegacao/T0XX.md, manda um funcionário executar sem
interação na worktree da feature e recebe só o resumo (diff, escopo, testes), nunca o transcript.
O processo inteiro está em docs/delegacao.md.

  python delegar.py funcionarios              quem está disponível (agy, copilot, ollama)
  python delegar.py status                    quem está fazendo o quê e a % de cada spec
  python delegar.py rodar <brief.md> [--funcionario agy|copilot|ollama] [--modelo M]
                    [--pasta DIR] [--tempo 1800] [--tentativa N] [--limpar]
  python delegar.py resultado <brief.md> (--go | --no-go) --nota "..." [--tentativa N]

Códigos de saída de `rodar`: 0 pronto para validar; 2 diff fora do escopo ou HEAD mudou; 3 testes
falharam; 4 funcionário não terminou, não encontrado ou Ollama fora; 5 cota esgotada (tentar o
próximo da fila). O Ollama nunca é iniciado por aqui: só um GET na API, com 2 s de espera.
Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CACHE = RAIZ / ".cache" / "delegacao"
ARQUIVO_STATUS = CACHE / "status.json"

OK, USO, ESCOPO, TESTES, FALHOU, COTA = 0, 1, 2, 3, 4, 5

FILA = ("agy", "copilot")
FUNCIONARIOS = ("agy", "copilot", "ollama")
MODELOS = {
    "agy": {"minor": "gemini-3.8-flash-medium", "major": "gemini-4-argon-medium"},
    "copilot": {"minor": None, "major": None},
    "ollama": {"patch": "qwen2.5-coder:3b", "minor": "qwen2.5-coder:3b", "major": "qwen2.5-coder:3b"},
}
OLLAMA = "http://127.0.0.1:11434"
PROMPT = (
    "Leia o arquivo {brief} e execute exatamente o que ele pede. A raiz do repositório onde você "
    "trabalha é {pasta}: todo caminho do brief é relativo a ela e só ela recebe mudanças. "
    "Não faça commit nem push. Ao terminar, liste os arquivos que alterou."
)
SINAIS_COTA = (
    "quota", "rate limit", "rate_limit", "ratelimit", "limit reached", "usage limit",
    "insufficient", "too many requests", "resource exhausted", "resource_exhausted",
)
ULTIMAS_LINHAS = 30


# ---------------------------------------------------------------- funções puras


def ler_brief(texto: str) -> dict:
    """Lê do brief o id da tarefa, o título, a spec, o tamanho e os arquivos permitidos."""
    titulo = ""
    for linha in texto.splitlines():
        if linha.startswith("# "):
            titulo = linha[2:].strip()
            break
    m = re.search(r"\bT\d{3}\b", titulo)
    tarefa = m.group(0) if m else "T???"
    tamanho = _campo(texto, "Tamanho") or "minor"
    tamanho = tamanho.split()[0].lower().strip("`*")
    if tamanho not in ("patch", "minor", "major"):
        raise ValueError(f"Tamanho inválido no brief: {tamanho!r} (use patch, minor ou major).")
    permitidos = _lista_da_secao(texto, "Arquivos permitidos")
    if not permitidos:
        raise ValueError("O brief precisa da seção '## Arquivos permitidos' com ao menos um caminho.")
    return {
        "tarefa": tarefa,
        "titulo": titulo,
        "spec": _campo(texto, "Spec") or "",
        "tamanho": tamanho,
        "permitidos": permitidos,
    }


def _campo(texto: str, nome: str) -> str | None:
    m = re.search(rf"^\**{nome}\**\s*:\s*(.+)$", texto, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else None


def _lista_da_secao(texto: str, titulo: str) -> list[str]:
    itens: list[str] = []
    dentro = False
    for linha in texto.splitlines():
        if linha.startswith("## "):
            dentro = linha[3:].strip().lower() == titulo.lower()
            continue
        if dentro and linha.strip().startswith(("- ", "* ")):
            item = linha.strip()[2:].strip().strip("`").strip()
            if item:
                itens.append(item.replace("\\", "/"))
    return itens


def comando(funcionario: str, brief: str, modelo: str | None, tempo: int, pasta: str = ".") -> list[str]:
    """Linha de comando do funcionário em modo não interativo (o agy quer o prompt colado na flag)."""
    prompt = PROMPT.format(brief=brief, pasta=pasta)
    if funcionario == "agy":
        cmd = ["agy", f"--print={prompt}", "--dangerously-skip-permissions",
               "--print-timeout", f"{tempo}s"]
        if modelo:
            cmd += ["--model", modelo]
        return cmd
    if funcionario == "copilot":
        cmd = ["copilot", "--allow-all-tools", "--allow-all-paths", "--no-ask-user", "-s",
               "--no-auto-update"]
        if modelo:
            cmd += ["--model", modelo]
        return cmd + ["-p", prompt]
    raise ValueError(f"Funcionário sem linha de comando: {funcionario}")


def cota_esgotada(texto: str) -> bool:
    """Reconhece na saída do funcionário os sinais de limite de uso."""
    baixo = texto.lower()
    if any(s in baixo for s in SINAIS_COTA):
        return True
    return re.search(r"\b429\b", texto) is not None


def arquivos_do_status(porcelain: str) -> list[str]:
    """Caminhos alterados a partir de `git status --porcelain` (renomeio conta o destino)."""
    arquivos = []
    for linha in porcelain.splitlines():
        if len(linha) < 4:
            continue
        caminho = linha[3:].strip()
        if " -> " in caminho:
            caminho = caminho.split(" -> ", 1)[1]
        arquivos.append(caminho.strip('"').replace("\\", "/"))
    return arquivos


def fora_do_escopo(porcelain: str, permitidos: list[str]) -> list[str]:
    """Arquivos alterados que não estão na lista de permitidos (um caminho ou uma pasta/)."""
    fora = []
    for caminho in arquivos_do_status(porcelain):
        if any(caminho == p or caminho.startswith(p.rstrip("/") + "/") for p in permitidos):
            continue
        fora.append(caminho)
    return fora


def porcentagem_tasks(tasks_md: str) -> tuple[int, int]:
    """(feitas, total) pelas marcas `- [X] T...` e `- [ ] T...` do tasks.md."""
    feitas = len(re.findall(r"^\s*- \[[xX]\] T\d{3}", tasks_md, re.MULTILINE))
    abertas = len(re.findall(r"^\s*- \[ \] T\d{3}", tasks_md, re.MULTILINE))
    return feitas, feitas + abertas


def linha_status(spec: str, estado: dict, tasks_md: str | None, agora: float) -> str:
    """Uma linha por spec: quem está fazendo o quê e quanto já foi."""
    partes = [spec]
    if tasks_md is not None:
        feitas, total = porcentagem_tasks(tasks_md)
        pct = round(100 * feitas / total) if total else 0
        partes.append(f"{feitas}/{total} tarefas ({pct}%)")
    andamento = estado.get("andamento")
    if andamento:
        minutos = int((agora - andamento["inicio"]) // 60)
        modelo = f" ({andamento['modelo']})" if andamento.get("modelo") else ""
        partes.append(
            f"agora: {andamento['tarefa']} → {andamento['funcionario']}{modelo} há {minutos} min, "
            f"tentativa {andamento['tentativa']}"
        )
    else:
        partes.append("nada em andamento")
    return " · ".join(partes)


def resumo(dados: dict) -> tuple[str, int]:
    """Texto do resumo e código de saída a partir do que aconteceu na rodada."""
    linhas = []
    cab = (f"== {dados['tarefa']} → {dados['funcionario']}"
           + (f" ({dados['modelo']})" if dados.get("modelo") else "")
           + f", tentativa {dados['tentativa']}, {_duracao(dados['segundos'])}, saída {dados['rc']}")
    linhas.append(cab)
    codigo = OK
    if dados.get("timeout"):
        linhas.append(f"O funcionário não terminou em {dados['tempo']} s.")
        codigo = FALHOU
    elif dados.get("cota"):
        proximo = _proximo(dados["funcionario"])
        linhas.append(f"Cota do {dados['funcionario']} esgotada; próximo: {proximo or 'nenhum (Claude assume)'}.")
        codigo = COTA
    elif dados["rc"] != 0:
        linhas.append("O funcionário saiu com erro.")
        codigo = FALHOU
    elif not dados.get("diff_stat", "").strip() and not dados.get("resposta"):
        linhas.append("O funcionário terminou sem alterar nada na worktree (mexeu em outra pasta?).")
        codigo = FALHOU
    diff = dados.get("diff_stat", "").strip()
    linhas.append("Arquivos alterados (git diff --stat):")
    linhas.append(diff if diff else "  nenhum")
    fora = dados.get("fora", [])
    linhas.append("Fora do escopo: " + (", ".join(fora) if fora else "nenhum"))
    if dados.get("head_antes") != dados.get("head_depois"):
        linhas.append("HEAD: MUDOU (o funcionário commitou; desfaça antes de validar)")
        codigo = max(codigo, ESCOPO) if codigo in (OK, ESCOPO) else codigo
    else:
        linhas.append("HEAD: intacto")
    if fora and codigo == OK:
        codigo = ESCOPO
    testes = dados.get("testes")
    if testes is None:
        linhas.append("Testes: não rodados")
    elif testes["ok"]:
        linhas.append(f"Testes: OK ({testes['resumo']})")
    else:
        linhas.append(f"Testes: FALHARAM ({testes['resumo']})")
        if codigo == OK:
            codigo = TESTES
    ultimas = dados.get("ultimas", [])
    if ultimas:
        linhas.append(f"Últimas {len(ultimas)} linhas do funcionário:")
        linhas.extend("  " + l for l in ultimas)
    if dados.get("log"):
        linhas.append(f"Log: {dados['log']}")
    if dados.get("resposta"):
        linhas.append(f"Resposta do Ollama (não edita arquivos): {dados['resposta']}")
    rotulos = {OK: "pronto para validar", ESCOPO: "fora do escopo ou HEAD mudou", TESTES: "testes falharam",
               FALHOU: "funcionário não entregou", COTA: "cota esgotada"}
    linhas.append(f"Resultado: {codigo} ({rotulos[codigo]})")
    return "\n".join(linhas), codigo


def _proximo(funcionario: str) -> str | None:
    if funcionario in FILA:
        i = FILA.index(funcionario)
        return FILA[i + 1] if i + 1 < len(FILA) else None
    return FILA[0]


def _duracao(segundos: float) -> str:
    s = int(segundos)
    return f"{s // 60} min {s % 60} s" if s >= 60 else f"{s} s"


def nome_da_spec(brief: Path) -> str:
    """specs/NNN-nome/delegacao/T0XX.md → NNN-nome; fora de specs/, o nome da pasta do brief."""
    partes = [p for p in brief.resolve().parts]
    if "specs" in partes:
        i = partes.index("specs")
        if i + 1 < len(partes):
            return partes[i + 1]
    return brief.resolve().parent.name


# ---------------------------------------------------------------- disponibilidade


def ollama_modelos(timeout: float = 2.0) -> list[str] | None:
    """Modelos do Ollama se a API já estiver no ar; None se estiver fora. Nunca inicia o serviço."""
    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=timeout) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None
    return [m.get("name", "?") for m in dados.get("models", [])]


def disponiveis() -> dict[str, str | None]:
    """Funcionário → como achá-lo (caminho ou modelos), ou None se estiver fora."""
    estado: dict[str, str | None] = {}
    for nome in ("agy", "copilot"):
        estado[nome] = shutil.which(nome)
    modelos = ollama_modelos()
    estado["ollama"] = ", ".join(modelos) if modelos else None
    return estado


# ---------------------------------------------------------------- status.json


def carregar_status() -> dict:
    if ARQUIVO_STATUS.exists():
        try:
            return json.loads(ARQUIVO_STATUS.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"specs": {}}


def gravar_status(status: dict) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    ARQUIVO_STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def marcar_inicio(spec: str, pasta: Path, tarefa: str, funcionario: str, modelo: str | None, tentativa: int) -> None:
    status = carregar_status()
    entrada = status["specs"].setdefault(spec, {"pasta": str(pasta), "andamento": None, "fechadas": []})
    entrada["pasta"] = str(pasta)
    entrada["andamento"] = {"tarefa": tarefa, "funcionario": funcionario, "modelo": modelo,
                            "tentativa": tentativa, "inicio": time.time()}
    gravar_status(status)


def marcar_fim(spec: str, tarefa: str, funcionario: str, tentativa: int, codigo: int) -> None:
    status = carregar_status()
    entrada = status["specs"].setdefault(spec, {"pasta": "", "andamento": None, "fechadas": []})
    entrada["andamento"] = None
    entrada["fechadas"].append({"tarefa": tarefa, "funcionario": funcionario, "tentativa": tentativa,
                                "codigo": codigo, "quando": datetime.now().isoformat(timespec="minutes")})
    entrada["fechadas"] = entrada["fechadas"][-20:]
    gravar_status(status)


def marcar_resultado(spec: str, tarefa: str, go: bool, tentativa: int) -> None:
    status = carregar_status()
    entrada = status["specs"].setdefault(spec, {"pasta": "", "andamento": None, "fechadas": []})
    entrada["fechadas"].append({"tarefa": tarefa, "funcionario": "validação", "tentativa": tentativa,
                                "codigo": 0 if go else 1, "go": go,
                                "quando": datetime.now().isoformat(timespec="minutes")})
    entrada["fechadas"] = entrada["fechadas"][-20:]
    gravar_status(status)


# ---------------------------------------------------------------- git e testes


def git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.stdout


def python_da_pasta(pasta: Path) -> str:
    for base in (pasta, RAIZ):
        for rel in ("Scripts/python.exe", "bin/python"):
            cand = base / ".venv" / rel
            if cand.exists():
                return str(cand)
    return sys.executable


def rodar_testes(pasta: Path) -> dict:
    r = subprocess.run([python_da_pasta(pasta), "-m", "unittest", "discover", "-s", "tests"], cwd=pasta,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    saida = (r.stdout + r.stderr).strip().splitlines()
    rodados = next((l for l in reversed(saida) if l.startswith("Ran ")), "")
    ultima = saida[-1] if saida else ""
    return {"ok": r.returncode == 0, "resumo": f"{rodados}; {ultima}".strip("; ")}


def limpar_escopo(pasta: Path, permitidos: list[str]) -> None:
    """Desfaz as mudanças só nos arquivos permitidos (tracked volta; novo é apagado)."""
    rastreados = set(git(["ls-files"], pasta).splitlines())
    for p in permitidos:
        alvo = pasta / p
        if p in rastreados:
            subprocess.run(["git", "checkout", "--", p], cwd=pasta, capture_output=True)
        elif alvo.is_file():
            alvo.unlink()


# ---------------------------------------------------------------- comandos


def cmd_funcionarios() -> int:
    for nome, estado in disponiveis().items():
        print(f"{nome:8} {'disponível' if estado else 'fora'}" + (f"  ({estado})" if estado else ""))
    print(f"Fila: {' → '.join(FILA)}; Ollama só para texto puro, e só se já estiver ligado.")
    return OK


def cmd_status() -> int:
    status = carregar_status()
    if not status["specs"]:
        print("Nenhuma delegação registrada ainda.")
        return OK
    agora = time.time()
    for spec, estado in status["specs"].items():
        pasta = Path(estado.get("pasta") or RAIZ)
        tasks = None
        for base in (pasta, RAIZ):
            cand = base / "specs" / spec / "tasks.md"
            if cand.exists():
                tasks = cand.read_text(encoding="utf-8")
                break
        print(linha_status(spec, estado, tasks, agora))
        for f in estado.get("fechadas", [])[-5:]:
            if f.get("funcionario") == "validação":
                rotulo = "GO" if f.get("go") else "NO GO"
                print(f"  {f['tarefa']} → validação: {rotulo} (tentativa {f['tentativa']})")
            else:
                print(f"  {f['tarefa']} → {f['funcionario']} saiu com {f['codigo']} (tentativa {f['tentativa']})")
    return OK


def cmd_rodar(args: argparse.Namespace) -> int:
    brief = Path(args.brief)
    if not brief.is_file():
        print(f"Brief não encontrado: {brief}")
        return USO
    try:
        info = ler_brief(brief.read_text(encoding="utf-8"))
    except ValueError as e:
        print(e)
        return USO
    pasta = Path(args.pasta).resolve() if args.pasta else Path.cwd()
    if not (pasta / ".git").exists():
        print(f"A pasta não é uma worktree do Git: {pasta}")
        return USO
    funcionario = args.funcionario or ("ollama" if info["tamanho"] == "patch" else FILA[0])
    modelo = args.modelo or MODELOS[funcionario].get(info["tamanho"])
    spec = nome_da_spec(brief)
    tarefa = info["tarefa"]
    log_dir = CACHE / spec
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"{tarefa}-tentativa-{args.tentativa}.log"

    if args.limpar:
        limpar_escopo(pasta, info["permitidos"])

    dados = {"tarefa": tarefa, "funcionario": funcionario, "modelo": modelo, "tentativa": args.tentativa,
             "tempo": args.tempo, "log": str(log)}
    dados["head_antes"] = git(["rev-parse", "HEAD"], pasta).strip()
    inicio = time.time()

    if funcionario == "ollama":
        modelos = ollama_modelos()
        if modelos is None:
            print(f"Ollama fora (API {OLLAMA} não respondeu em 2 s); não inicio o serviço. "
                  f"Use --funcionario {FILA[0]} ou faça a tarefa.")
            return FALHOU
        marcar_inicio(spec, pasta, tarefa, funcionario, modelo, args.tentativa)
        rc, saida, estourou = _ollama_gerar(brief.read_text(encoding="utf-8"), modelo, args.tempo)
        resposta = brief.with_suffix(".resposta.md")
        resposta.write_text(saida, encoding="utf-8")
        dados["resposta"] = str(resposta)
    else:
        if shutil.which(funcionario) is None:
            print(f"{funcionario} não está no PATH. Veja `delegar.py funcionarios`.")
            return FALHOU
        marcar_inicio(spec, pasta, tarefa, funcionario, modelo, args.tentativa)
        cmd = comando(funcionario, str(brief.resolve()), modelo, args.tempo, str(pasta))
        rc, saida, estourou = _executar(cmd, pasta, args.tempo)

    dados["segundos"] = time.time() - inicio
    dados["rc"] = rc
    dados["timeout"] = estourou
    log.write_text(saida, encoding="utf-8")
    dados["cota"] = cota_esgotada(saida)
    dados["head_depois"] = git(["rev-parse", "HEAD"], pasta).strip()
    porcelain = git(["status", "--porcelain"], pasta)
    dados["diff_stat"] = git(["diff", "--stat", "HEAD"], pasta) + _novos(porcelain)
    dados["fora"] = fora_do_escopo(porcelain, info["permitidos"])
    if porcelain.strip() and not estourou and not dados["cota"]:
        dados["testes"] = rodar_testes(pasta)
    linhas = [l for l in saida.splitlines() if l.strip()]
    dados["ultimas"] = linhas[-ULTIMAS_LINHAS:]
    texto, codigo = resumo(dados)
    marcar_fim(spec, tarefa, funcionario, args.tentativa, codigo)
    print(texto)
    return codigo


def _novos(porcelain: str) -> str:
    novos = [l[3:].strip() for l in porcelain.splitlines() if l.startswith("??")]
    return ("\n" + "\n".join(f" {n} (novo)" for n in novos)) if novos else ""


def _executar(cmd: list[str], pasta: Path, tempo: int) -> tuple[int, str, bool]:
    try:
        r = subprocess.run(cmd, cwd=pasta, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=tempo + 60, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as e:
        saida = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        return 124, saida, True
    except OSError as e:
        return 127, str(e), False
    return r.returncode, r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr.strip() else ""), False


def _ollama_gerar(prompt: str, modelo: str, tempo: int) -> tuple[int, str, bool]:
    corpo = json.dumps({"model": modelo, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(f"{OLLAMA}/api/generate", data=corpo,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=tempo) as resp:
            dados = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError) as e:
        return 1, f"Ollama não respondeu: {e}", True
    except ValueError as e:
        return 1, f"Resposta inválida do Ollama: {e}", False
    return 0, dados.get("response", ""), False


def cmd_resultado(args: argparse.Namespace) -> int:
    brief = Path(args.brief)
    if not brief.is_file():
        print(f"Brief não encontrado: {brief}")
        return USO
    info = ler_brief(brief.read_text(encoding="utf-8"))
    quando = datetime.now().strftime("%Y-%m-%d %H:%M")
    if args.go:
        bloco = f"\n## Resultado\n\n- GO em {quando}, tentativa {args.tentativa}. {args.nota}\n"
    else:
        bloco = f"\n## Refazer (tentativa {args.tentativa + 1})\n\n- NO GO em {quando}, tentativa {args.tentativa}: {args.nota}\n"
    with brief.open("a", encoding="utf-8") as f:
        f.write(bloco)
    marcar_resultado(nome_da_spec(brief), info["tarefa"], args.go, args.tentativa)
    print(("GO" if args.go else "NO GO") + f" registrado em {brief}")
    return OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Delega tarefas a outros assistentes de código.")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("funcionarios", help="quem está disponível")
    sub.add_parser("status", help="quem está fazendo o quê")
    r = sub.add_parser("rodar", help="roda um brief num funcionário")
    r.add_argument("brief")
    r.add_argument("--funcionario", choices=FUNCIONARIOS)
    r.add_argument("--modelo")
    r.add_argument("--pasta", help="worktree onde o funcionário trabalha (padrão: pasta atual)")
    r.add_argument("--tempo", type=int, default=1800, help="segundos de espera (padrão 1800)")
    r.add_argument("--tentativa", type=int, default=1)
    r.add_argument("--limpar", action="store_true", help="desfaz antes as mudanças nos arquivos permitidos")
    v = sub.add_parser("resultado", help="registra GO ou NO GO no brief")
    v.add_argument("brief")
    g = v.add_mutually_exclusive_group(required=True)
    g.add_argument("--go", action="store_true")
    g.add_argument("--no-go", dest="go", action="store_false")
    v.add_argument("--nota", default="")
    v.add_argument("--tentativa", type=int, default=1)
    args = parser.parse_args(argv)
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")
    if args.comando == "funcionarios":
        return cmd_funcionarios()
    if args.comando == "status":
        return cmd_status()
    if args.comando == "rodar":
        return cmd_rodar(args)
    return cmd_resultado(args)


if __name__ == "__main__":
    sys.exit(main())
