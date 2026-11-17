"""Testes das funções puras de delegar.py (sem rodar funcionário nenhum)."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import delegar  # noqa: E402

BRIEF = """# T007 — Função nova em salarios.py

Spec: 051-exemplo
Tamanho: minor

## Contexto

Leia salarios.py.

## O que fazer

Crie a função x.

## Arquivos permitidos

- salarios.py
- tests/test_salarios.py
- `dash/novo/`

## Critério de aceite

- a função existe.
"""


class LerBrief(unittest.TestCase):
    def test_le_tarefa_tamanho_e_permitidos(self):
        info = delegar.ler_brief(BRIEF)
        self.assertEqual(info["tarefa"], "T007")
        self.assertEqual(info["tamanho"], "minor")
        self.assertEqual(info["spec"], "051-exemplo")
        self.assertEqual(info["permitidos"], ["salarios.py", "tests/test_salarios.py", "dash/novo/"])

    def test_sem_arquivos_permitidos_da_erro_claro(self):
        texto = BRIEF.split("## Arquivos permitidos")[0]
        with self.assertRaises(ValueError) as ctx:
            delegar.ler_brief(texto)
        self.assertIn("Arquivos permitidos", str(ctx.exception))

    def test_tamanho_invalido(self):
        with self.assertRaises(ValueError):
            delegar.ler_brief(BRIEF.replace("Tamanho: minor", "Tamanho: enorme"))


class Comando(unittest.TestCase):
    def test_agy_nao_interativo(self):
        cmd = delegar.comando("agy", "C:/x/T007.md", "gemini-3.8-flash-medium", 900)
        self.assertEqual(cmd[0], "agy")
        self.assertTrue(cmd[1].startswith("--print=Leia o arquivo C:/x/T007.md"))
        self.assertIn("--dangerously-skip-permissions", cmd)
        self.assertIn("900s", cmd)
        self.assertIn("gemini-3.8-flash-medium", cmd)

    def test_prompt_diz_a_pasta_de_trabalho(self):
        cmd = delegar.comando("copilot", "C:/x/T007.md", None, 900, pasta="C:/wt")
        self.assertIn("A raiz do repositório onde você trabalha é C:/wt", cmd[-1])

    def test_copilot_nao_interativo(self):
        cmd = delegar.comando("copilot", "C:/x/T007.md", None, 900)
        for flag in ("--allow-all-tools", "--allow-all-paths", "--no-ask-user", "-s", "-p"):
            self.assertIn(flag, cmd)
        self.assertNotIn("--model", cmd)
        self.assertIn("Não faça commit nem push", cmd[-1])

    def test_ollama_nao_tem_linha_de_comando(self):
        with self.assertRaises(ValueError):
            delegar.comando("ollama", "x", None, 1)


class Cota(unittest.TestCase):
    def test_reconhece_sinais(self):
        self.assertTrue(delegar.cota_esgotada("Error: 429 Too Many Requests"))
        self.assertTrue(delegar.cota_esgotada("You have exceeded your QUOTA for today"))
        self.assertTrue(delegar.cota_esgotada("RESOURCE_EXHAUSTED"))

    def test_ignora_texto_normal(self):
        self.assertFalse(delegar.cota_esgotada("Criei a função em salarios.py, linha 4290."))
        self.assertFalse(delegar.cota_esgotada("Ran 312 tests in 4.2s\n\nOK"))


class Escopo(unittest.TestCase):
    PORCELAIN = " M salarios.py\n?? tests/test_salarios.py\n M dash/banco.py\nR  a.py -> dash/novo/b.py\n"

    def test_lista_so_o_que_esta_fora(self):
        fora = delegar.fora_do_escopo(self.PORCELAIN, ["salarios.py", "tests/test_salarios.py", "dash/novo/"])
        self.assertEqual(fora, ["dash/banco.py"])

    def test_pasta_permitida_cobre_subarquivos(self):
        self.assertEqual(delegar.fora_do_escopo("?? dash/novo/x/y.py\n", ["dash/novo/"]), [])


class Status(unittest.TestCase):
    TASKS = "- [X] T001 a\n- [X] T002 b\n- [ ] T003 c\n- [ ] T004 d\n  - sub-item\n"

    def test_porcentagem(self):
        self.assertEqual(delegar.porcentagem_tasks(self.TASKS), (2, 4))

    def test_linha_com_andamento(self):
        estado = {"andamento": {"tarefa": "T003", "funcionario": "agy", "modelo": "gemini-3.8-flash-medium",
                                "tentativa": 1, "inicio": 1000.0}}
        linha = delegar.linha_status("051-exemplo", estado, self.TASKS, agora=1000.0 + 4 * 60 + 5)
        self.assertEqual(
            linha,
            "051-exemplo · 2/4 tarefas (50%) · agora: T003 → agy (gemini-3.8-flash-medium) há 4 min, tentativa 1",
        )

    def test_linha_sem_andamento(self):
        self.assertEqual(delegar.linha_status("051-exemplo", {"andamento": None}, None, 0.0),
                         "051-exemplo · nada em andamento")


class Resumo(unittest.TestCase):
    def base(self, **extra):
        dados = {"tarefa": "T007", "funcionario": "agy", "modelo": "m", "tentativa": 1, "segundos": 65,
                 "rc": 0, "tempo": 900, "head_antes": "abc", "head_depois": "abc", "diff_stat": " salarios.py | 2 +-",
                 "fora": [], "testes": {"ok": True, "resumo": "Ran 3 tests; OK"}, "ultimas": [], "log": "x.log"}
        dados.update(extra)
        return dados

    def test_tudo_ok(self):
        texto, codigo = delegar.resumo(self.base())
        self.assertEqual(codigo, delegar.OK)
        self.assertIn("HEAD: intacto", texto)
        self.assertIn("Resultado: 0", texto)

    def test_head_mudou_e_fora_do_escopo(self):
        _, codigo = delegar.resumo(self.base(head_depois="def"))
        self.assertEqual(codigo, delegar.ESCOPO)
        texto, codigo = delegar.resumo(self.base(fora=["dash/banco.py"]))
        self.assertEqual(codigo, delegar.ESCOPO)
        self.assertIn("Fora do escopo: dash/banco.py", texto)

    def test_entrega_vazia_e_falha(self):
        texto, codigo = delegar.resumo(self.base(diff_stat="", testes=None))
        self.assertEqual(codigo, delegar.FALHOU)
        self.assertIn("sem alterar nada", texto)

    def test_testes_falharam(self):
        _, codigo = delegar.resumo(self.base(testes={"ok": False, "resumo": "FAILED (failures=1)"}))
        self.assertEqual(codigo, delegar.TESTES)

    def test_cota_e_timeout(self):
        texto, codigo = delegar.resumo(self.base(cota=True))
        self.assertEqual(codigo, delegar.COTA)
        self.assertIn("Cota do agy esgotada; próximo: copilot", texto)
        texto, codigo = delegar.resumo(self.base(cota=True, funcionario="copilot"))
        self.assertIn("Claude assume", texto)
        _, codigo = delegar.resumo(self.base(timeout=True, rc=124))
        self.assertEqual(codigo, delegar.FALHOU)


class Ollama(unittest.TestCase):
    def test_fora_nao_inicia_servico(self):
        import urllib.error
        with mock.patch("delegar.urllib.request.urlopen", side_effect=urllib.error.URLError("fora")) as m, \
                mock.patch("delegar.subprocess.run") as run:
            self.assertIsNone(delegar.ollama_modelos())
        self.assertEqual(m.call_args.kwargs.get("timeout"), 2.0)
        run.assert_not_called()


class Rodizio(unittest.TestCase):
    def test_sem_historico_comeca_pelo_primeiro(self):
        self.assertEqual(delegar.proximo_do_rodizio({}), "agy")

    def test_pega_quem_esta_ha_mais_tempo_parado(self):
        self.assertEqual(delegar.proximo_do_rodizio({"ultimo_uso": {"agy": 100.0}}), "copilot")
        self.assertEqual(delegar.proximo_do_rodizio({"ultimo_uso": {"agy": 100.0, "copilot": 200.0}}), "agy")
        self.assertEqual(delegar.proximo_do_rodizio({"ultimo_uso": {"agy": 300.0, "copilot": 200.0}}), "copilot")


class NomeDaSpec(unittest.TestCase):
    def test_dentro_e_fora_de_specs(self):
        self.assertEqual(delegar.nome_da_spec(Path("specs/051-exemplo/delegacao/T007.md")), "051-exemplo")
        self.assertEqual(delegar.nome_da_spec(Path(".cache/delegacao/fumaca/T000.md")), "fumaca")


if __name__ == "__main__":
    unittest.main()
