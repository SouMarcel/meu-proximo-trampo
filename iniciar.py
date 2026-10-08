#!/usr/bin/env python3
"""meu-proximo-trampo: inicia a ferramenta com um comando.

  python iniciar.py                  prepara o que faltar (pergunta antes) e abre a página
  python iniciar.py --sim            aceita a instalação sem perguntar
  python iniciar.py --sem-navegador  não abre o navegador
  python iniciar.py --rede           aceita acesso de outros aparelhos da rede local
  python iniciar.py --porta 8766     usa outra porta

No Windows, se "python" não for reconhecido, use "py iniciar.py" ou dê dois cliques em
iniciar.bat. A ferramenta roda nesta janela: feche-a (ou Ctrl+C) para parar.

Tudo é instalado em .venv/, dentro desta pasta. Só biblioteca padrão, com sintaxe aceita desde o
Python 3.6, para que um Python antigo mostre a mensagem de versão em vez de erro de sintaxe.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VENV = RAIZ / ".venv"
NOME_CARIMBO = ".requisitos-instalados"
REQUISITOS = RAIZ / "requirements.txt"
PORTA_PADRAO = 8765
VERSAO_MINIMA = (3, 10)
DOWNLOAD = "https://www.python.org/downloads/"
NO_WINDOWS = os.name == "nt"

# Roda dentro do Python do .venv: versão de cada pacote pedido (null = não instalado)
VERIFICADOR = (
    "import json, sys\n"
    "from importlib import metadata\n"
    "saida = {}\n"
    "for nome in json.loads(sys.argv[1]):\n"
    "    try:\n"
    "        saida[nome] = metadata.version(nome)\n"
    "    except metadata.PackageNotFoundError:\n"
    "        saida[nome] = None\n"
    "print(json.dumps({'python': sys.version.split()[0], 'pacotes': saida}))\n"
)


# ---------------------------------------------------------------- funções puras

def ler_requisitos(caminho=REQUISITOS):
    """[(nome, versao_minima, linha)] do requirements.txt. Entende `nome` (versão None) e
    `nome>=x.y`; qualquer outro formato volta com versão "?" (basta estar instalado: quem
    garante a versão é o pip, na instalação)."""
    requisitos = []
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        linha = linha.split("#", 1)[0].strip()
        if not linha:
            continue
        m = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:>=\s*([0-9][0-9.]*))?", linha)
        if m:
            requisitos.append((m.group(1), m.group(2), linha))
        else:
            nome = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", linha)
            requisitos.append((nome.group(0) if nome else linha, "?", linha))
    return requisitos


def _numeros(versao):
    partes = []
    for parte in str(versao).split("."):
        m = re.match(r"\d+", parte)
        if not m:
            break
        partes.append(int(m.group(0)))
        if m.group(0) != parte:  # "0rc1": fica o 0 e para
            break
    return tuple(partes)


def versao_ok(instalada, minima):
    """O pacote instalado (versão ou None) atende ao mínimo (None ou "?" = qualquer versão)."""
    if not instalada:
        return False
    if minima in (None, "?"):
        return True
    a, b = _numeros(instalada), _numeros(minima)
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) >= b + (0,) * (n - len(b))


def python_do_venv(venv=VENV):
    return venv / "Scripts" / "python.exe" if NO_WINDOWS else venv / "bin" / "python"


def hash_requisitos(caminho=REQUISITOS):
    """SHA-256 das linhas úteis do requirements.txt (fim de linha e comentários não contam)."""
    texto = "\n".join(linha for _, _, linha in ler_requisitos(caminho))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def ler_carimbo(venv=VENV):
    try:
        dados = json.loads((venv / NOME_CARIMBO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return dados if isinstance(dados, dict) else None


def gravar_carimbo(venv, hash_atual, versao_python):
    (venv / NOME_CARIMBO).write_text(
        json.dumps({"requisitos_sha256": hash_atual, "python": versao_python}) + "\n", encoding="utf-8")


def _home_do_venv(venv):
    try:
        linhas = (venv / "pyvenv.cfg").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for linha in linhas:
        chave, sep, valor = linha.partition("=")
        if sep and chave.strip().lower() == "home":
            return valor.strip()
    return None


def estado_ambiente(venv=VENV, requisitos=REQUISITOS):
    """ausente, invalido, sem_carimbo, desatualizado ou pronto — sem rodar processo e sem rede."""
    if not venv.is_dir():
        return "ausente"
    home = _home_do_venv(venv)
    if not python_do_venv(venv).is_file() or not home or not Path(home).is_dir():
        return "invalido"  # incompleto, ou copiado de outra máquina
    carimbo = ler_carimbo(venv)
    if not carimbo:
        return "sem_carimbo"
    return "pronto" if carimbo.get("requisitos_sha256") == hash_requisitos(requisitos) else "desatualizado"


class _Ajuda(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, prefix="uso: ")


class _Opcoes(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, "%s: erro nas opções: %s\n" % (self.prog, message))


def ler_opcoes(argv=None):
    """(opções, argumentos a repassar ao servidor)."""
    ap = _Opcoes(
        prog="iniciar.py", add_help=False, formatter_class=_Ajuda,
        description="Inicia o meu-proximo-trampo: prepara o que faltar nesta pasta (perguntando antes) "
                    "e abre a página. Para parar, feche a janela ou use Ctrl+C.")
    ap._optionals.title = "opções"
    ap.add_argument("-h", "--help", action="help", help="mostra esta ajuda e sai")
    ap.add_argument("--sim", action="store_true", help="aceita a instalação sem perguntar")
    ap.add_argument("--sem-navegador", action="store_true", help="não abre o navegador")
    ap.add_argument("--rede", action="store_true",
                    help="aceita acesso de outros aparelhos da rede local (ex.: celular no mesmo Wi-Fi)")
    ap.add_argument("--porta", type=int, default=PORTA_PADRAO, help="porta da página (padrão: %(default)s)")
    op = ap.parse_args(argv)
    repassar = []
    if op.sem_navegador:
        repassar.append("--sem-navegador")
    if op.rede:
        repassar.append("--rede")
    if op.porta != PORTA_PADRAO:
        repassar += ["--porta", str(op.porta)]
    return op, repassar


# ---------------------------------------------------------------- passos com efeito

def checar_versao():
    if sys.version_info[:2] < VERSAO_MINIMA:
        print("A ferramenta precisa do Python %d.%d ou mais novo (este é o %d.%d). Baixe em %s"
              % (VERSAO_MINIMA + tuple(sys.version_info[:2]) + (DOWNLOAD,)))
        return 2
    return 0


def perguntar(texto, sim=False):
    if sim:
        return True
    try:
        resposta = input(texto + " [S/n] ").strip().lower()
    except EOFError:  # sem terminal para responder
        return False
    return resposta in ("", "s", "sim", "y", "yes")


def ja_rodando(porta):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/api/versao" % porta, timeout=2) as r:
            return r.status == 200 and "versao" in json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return False


def verificar_instalado(python_venv, requisitos=REQUISITOS):
    """(pacotes que faltam, versão do Python do .venv), ou None se o Python do .venv não roda."""
    reqs = ler_requisitos(requisitos)
    try:
        r = subprocess.run([str(python_venv), "-c", VERIFICADOR, json.dumps([n for n, _, _ in reqs])],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        dados = json.loads(r.stdout.decode("utf-8"))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    instalados = dados.get("pacotes") or {}
    faltando = [linha for nome, minima, linha in reqs if not versao_ok(instalados.get(nome), minima)]
    return faltando, dados.get("python") or "?"


def criar_ambiente(venv=VENV, recriar=False):
    import venv as modulo_venv
    print("Criando o ambiente em .venv …")
    try:
        modulo_venv.EnvBuilder(with_pip=True, clear=recriar).create(str(venv))
    except Exception as e:  # ensurepip ausente, sem permissão, antivírus segurando arquivo…
        print("\nNão deu para criar o ambiente (%s)." % e)
        if not NO_WINDOWS:
            print("No Linux, instale o pacote do venv (ex.: sudo apt install python3-venv).")
        print("Rode o comando de novo depois de resolver.")
        return False
    return True


def instalar(python_venv, venv=VENV, requisitos=REQUISITOS):
    print("Instalando as dependências (precisa de internet; pode levar alguns minutos)…\n")
    codigo = subprocess.call([str(python_venv), "-m", "pip", "install", "-r", str(requisitos),
                              "--disable-pip-version-check", "--no-cache-dir"], cwd=str(RAIZ))
    if codigo != 0:
        print("\nNão deu para instalar as dependências. Confira a conexão com a internet e rode o comando de novo.")
        return False
    verificado = verificar_instalado(python_venv, requisitos)
    if verificado is None or verificado[0]:
        faltam = ", ".join(verificado[0]) if verificado else "o ambiente não respondeu"
        print("\nA instalação terminou, mas ainda falta: %s. Rode o comando de novo." % faltam)
        return False
    gravar_carimbo(venv, hash_requisitos(requisitos), verificado[1])
    print("\nPronto: dependências instaladas.\n")
    return True


def recusou():
    print("\nTudo bem, nada foi instalado. Para preparar à mão, nesta pasta:")
    if NO_WINDOWS:
        print("  py -m venv .venv\n  .venv\\Scripts\\python -m pip install -r requirements.txt")
    else:
        print("  python3 -m venv .venv\n  .venv/bin/python -m pip install -r requirements.txt")
    print("Depois rode de novo: python iniciar.py")
    return 3


def _rodando_no_venv():
    try:
        return Path(sys.prefix).resolve() == VENV.resolve()
    except OSError:
        return False


def iniciar_servidor(python_venv, repassar):
    """Sobe o servidor do dashboard nesta janela e devolve o código de saída dele."""
    print("Iniciando a ferramenta. Para parar, feche esta janela ou use Ctrl+C; seus dados ficam salvos.\n")
    servidor = RAIZ / "dash" / "servidor.py"
    if _rodando_no_venv():
        sys.path.insert(0, str(servidor.parent))
        sys.argv = [str(servidor)] + list(repassar)
        import servidor as modulo_servidor
        return modulo_servidor.main()
    processo = subprocess.Popen([str(python_venv), str(servidor)] + list(repassar), cwd=str(RAIZ))
    while True:
        try:
            return processo.wait()
        except KeyboardInterrupt:  # o Ctrl+C também chega ao servidor; espera ele fechar
            continue


def main(argv=None):
    for fluxo in (sys.stdout, sys.stderr):
        try:  # linha a linha: as mensagens saem na ordem certa mesmo com a saída redirecionada
            fluxo.reconfigure(encoding="utf-8", line_buffering=True)
        except AttributeError:
            pass
    codigo = checar_versao()
    if codigo:
        return codigo
    op, repassar = ler_opcoes(argv)

    if ja_rodando(op.porta):
        endereco = "http://127.0.0.1:%d/" % op.porta
        print("A ferramenta já está aberta em %s" % endereco)
        if not op.sem_navegador:
            webbrowser.open(endereco)
        return 0
    if not REQUISITOS.is_file():
        print("Não achei o requirements.txt nesta pasta (%s). Clone o repositório de novo." % RAIZ)
        return 1

    python_venv = python_do_venv(VENV)
    estado = estado_ambiente()
    if estado in ("sem_carimbo", "desatualizado"):
        verificado = verificar_instalado(python_venv)
        if verificado is None:
            estado = "invalido"
        elif verificado[0]:
            print("A ferramenta precisa de: %s." % ", ".join(verificado[0]))
            if not perguntar("Instalar agora?", op.sim):
                return recusou()
            if not instalar(python_venv):
                return 1
        else:  # já estava tudo instalado (ex.: ambiente preparado à mão): só registra
            gravar_carimbo(VENV, hash_requisitos(), verificado[1])

    if estado in ("ausente", "invalido"):
        if estado == "ausente":
            print("Primeira vez por aqui: vou preparar a ferramenta nesta pasta (.venv), criando o ambiente e "
                  "instalando as dependências. Nada é instalado fora desta pasta.")
        else:
            print("O ambiente desta pasta (.venv) não funciona neste computador (pode ter vindo de outra "
                  "máquina ou ficado pela metade) e precisa ser recriado.")
        if not perguntar("Preparar agora?", op.sim):
            return recusou()
        if not criar_ambiente(VENV, recriar=estado == "invalido") or not instalar(python_venv):
            return 1

    return iniciar_servidor(python_venv, repassar)


if __name__ == "__main__":
    sys.exit(main())
