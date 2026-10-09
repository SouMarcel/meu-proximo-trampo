"""Testes da busca (vagas.py) e da busca pela página (dash/buscador.py), com a fonte falsa. Nenhum portal é consultado."""
import contextlib
import os
import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash"), str(Path(__file__).resolve().parent)]
import analise  # noqa: E402
import banco  # noqa: E402
import buscador  # noqa: E402
import filtros  # noqa: E402
import fonte_falsa  # noqa: E402
import vagas  # noqa: E402

CFG = {"fontes": ["falsa"], "termos": ["analista", '"cientista de dados"'],
       "localidade": {"pais": "Brasil", "estado": "PR", "cidade": "Curitiba", "raio_km": 25},
       "modelos": {"remoto": True, "hibrido": True, "presencial": False},
       "empresas_excluir": ["Empresa 1"], "janela_horas": 168, "ia": {"provedor": "nenhum"}}
SEGURAR = """import sys, time
sys.path[:0] = [sys.argv[1], sys.argv[1] + "/dash"]
import vagas
from pathlib import Path
vagas.CACHE = Path(sys.argv[2])
trava = vagas.TravaBusca(sys.argv[3])
trava.__enter__()
print("travado", flush=True)
sys.stdin.read()
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "config.json").write_text(json.dumps(CFG), encoding="utf-8")
        self.patches = [mock.patch.object(vagas, "CACHE", self.tmp / ".cache"),
                        mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                        mock.patch.object(filtros, "CONFIG", self.tmp / "config.json"),
                        mock.patch.object(buscador, "RAIZ", self.tmp),
                        mock.patch.object(buscador, "PAUSA", 0),
                        mock.patch.dict(vagas.FONTES, {"falsa": fonte_falsa}),
                        mock.patch.object(analise.FILA, "pedir", mock.Mock(return_value=True))]
        for p in self.patches:
            p.start()
        fonte_falsa.PAUSA, fonte_falsa.ERRO = 0.0, ""
        fonte_falsa.CHAMADAS.clear()
        fonte_falsa.DESCRITAS.clear()
        self.processos = []

    def tearDown(self):
        for proc in self.processos:
            proc.kill()
            proc.wait(10)
            proc.stdin.close()
            proc.stdout.close()
        for p in reversed(self.patches):
            p.stop()
        fonte_falsa.PAUSA, fonte_falsa.ERRO = 0.0, ""
        shutil.rmtree(self.tmp, ignore_errors=True)

    def segurar_trava(self, origem):
        proc = subprocess.Popen([sys.executable, "-c", SEGURAR, str(RAIZ), str(self.tmp / ".cache"), origem],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                env={**os.environ, "TRAMPO_BANCO": str(self.tmp / "outro.db")})
        self.processos.append(proc)
        self.assertEqual(proc.stdout.readline().strip(), "travado")
        return proc

    def efetivos(self):
        return filtros.efetivos(CFG)

    def busca_pagina(self, **kw):
        b = buscador.Busca()
        b.iniciar(**kw)
        b._thread.join(20)
        return b


class TestExecutar(Base):
    def test_progresso_e_resultado(self):
        eventos = []
        r = vagas.executar(CFG, self.efetivos(), ["falsa"], 40, pausa=0, progresso=eventos.append)
        consultas = [e for e in eventos if e["etapa"] == "consulta"]
        self.assertEqual(len(consultas), 8)  # antes e depois de cada uma das 4 consultas
        self.assertEqual([e["feitas"] for e in consultas], [0, 1, 1, 2, 2, 3, 3, 4])
        self.assertTrue(all(e["total"] == 4 and e["portal"] == "Falsa" for e in consultas))
        self.assertEqual(consultas[0]["cargo"], "analista")
        self.assertEqual(consultas[-1]["encontradas"], r["brutas"])
        descricoes = [e for e in eventos if e["etapa"] == "descricoes"]
        self.assertEqual(len(descricoes), len(r["candidatas"]) + len(r["fora"]))
        self.assertEqual(len(r["fora"]), 2)  # Empresa 1, nos dois cargos
        self.assertEqual(r["parametros"]["consultas"], 4)

    def test_cancelar_para_antes_da_proxima(self):
        feitas = []
        cancelado = lambda: len(fonte_falsa.CHAMADAS) >= 1
        with self.assertRaises(vagas.Cancelada):
            vagas.executar(CFG, self.efetivos(), ["falsa"], 40, pausa=0, cancelado=cancelado,
                           progresso=lambda e: feitas.append(e))
        self.assertEqual(len(fonte_falsa.CHAMADAS), 1)
        self.assertEqual(banco.listar_vagas(), [])

    def test_terminal_grava_e_registra(self):
        saida = io.StringIO()
        with mock.patch.object(sys, "argv", ["vagas.py", "buscar", "--pausa", "0", "--gravar"]), \
                contextlib.redirect_stdout(saida):
            self.assertEqual(vagas.main(), 0)
        self.assertIn("Gravadas no dashboard: 3 vaga(s) nova(s)", saida.getvalue())
        self.assertTrue(all(v["analise_status"] == "sem_analise" for v in banco.listar_vagas()))
        b = banco.ultima_busca()
        self.assertEqual((b["origem"], b["situacao"], b["com_nota"]), ("terminal", "concluida", False))
        self.assertEqual(vagas.ultima()["situacao"], "concluida")
        self.assertEqual(vagas.ultima()["origem"], "terminal")

    def test_gravar_resultado_pendente(self):
        r = vagas.executar(CFG, self.efetivos(), ["falsa"], 40, pausa=0)
        g = vagas.gravar_resultado(r, sem_avaliacao=True, status_sem_nota="pendente", origem="pagina")
        status = {v["id"]: (v["triagem"], v["analise_status"]) for v in banco.listar_vagas()}
        self.assertEqual(g["para_decidir"], 3)
        self.assertTrue(all(s == ("pendente", "pendente") for vid, s in status.items() if "-1" not in vid))
        self.assertTrue(all(s == ("fora", "sem_analise") for vid, s in status.items() if vid.endswith("-1")))
        b = banco.ultima_busca()
        self.assertEqual((b["origem"], b["com_nota"]), ("pagina", True))


class TestTrava(Base):
    def test_entre_processos_e_interrompida(self):
        proc = self.segurar_trava("pagina")
        self.assertEqual(vagas.ocupada()["origem"], "pagina")
        with self.assertRaises(vagas.BuscaOcupada) as ctx:
            with vagas.TravaBusca("terminal"):
                pass
        self.assertIn("pela página do dashboard", str(ctx.exception))
        erro = io.StringIO()
        with mock.patch.object(sys, "argv", ["vagas.py", "buscar", "--pausa", "0"]), contextlib.redirect_stderr(erro):
            self.assertEqual(vagas.main(), 4)
        self.assertIn("Espere ela terminar ou cancele por lá", erro.getvalue())
        self.assertEqual(fonte_falsa.CHAMADAS, [])
        proc.kill()
        proc.wait(10)
        self.assertIsNone(vagas.ocupada())
        self.assertEqual(vagas.ultima()["situacao"], "interrompida")
        with vagas.TravaBusca("terminal") as t:
            t.situacao = "falha"
        self.assertEqual(vagas.ultima()["situacao"], "falha")

    def test_cancelada_e_erro_no_registro(self):
        with self.assertRaises(vagas.Cancelada):
            with vagas.TravaBusca("pagina"):
                raise vagas.Cancelada()
        self.assertEqual(vagas.ultima()["situacao"], "cancelada")
        with self.assertRaises(RuntimeError):
            with vagas.TravaBusca("pagina"):
                raise RuntimeError("x")
        self.assertEqual(vagas.ultima()["situacao"], "erro")


class TestIntervalo(unittest.TestCase):
    def test_regras(self):
        agora = datetime(2026, 10, 9, 12, 0)
        ult = lambda situacao, minutos: {"situacao": situacao, "fim": (agora - timedelta(minutes=minutos)).isoformat()}
        self.assertEqual(buscador.Busca.intervalo(ult("concluida", 10), agora), ("2026-10-09T12:20", True))
        self.assertEqual(buscador.Busca.intervalo(ult("concluida", 120), agora), (None, True))
        self.assertEqual(buscador.Busca.intervalo(ult("concluida", 7 * 60), agora), (None, False))
        self.assertEqual(buscador.Busca.intervalo(ult("falha", 5), agora)[0], "2026-10-09T12:25")
        for situacao in ("cancelada", "interrompida", "erro", "rodando"):
            self.assertEqual(buscador.Busca.intervalo(ult(situacao, 5), agora), (None, False))
        self.assertEqual(buscador.Busca.intervalo(None, agora), (None, False))


class TestBuscaPagina(Base):
    def test_sem_ia_grava_sem_nota_e_nao_mexe_no_chat(self):
        vagas.CACHE.mkdir(parents=True)
        (vagas.CACHE / "candidatas.json").write_text('{"do": "chat"}', encoding="utf-8")
        b = self.busca_pagina()
        e = b.estado()
        self.assertEqual(e["situacao"], "concluida", e)
        self.assertEqual(e["resumo"]["novas"], 3)
        self.assertEqual(e["resumo"]["fora_criterios"], 2)
        self.assertFalse(e["resumo"]["com_nota"])
        self.assertEqual((e["feitas"], e["total"]), (4, 4))
        self.assertTrue(all(v["analise_status"] == "sem_analise" for v in banco.listar_vagas()))
        analise.FILA.pedir.assert_not_called()
        self.assertEqual((vagas.CACHE / "candidatas.json").read_text(encoding="utf-8"), '{"do": "chat"}')
        self.assertTrue((vagas.CACHE / "pagina" / "candidatas.json").exists())
        self.assertEqual(banco.ultima_busca()["origem"], "pagina")
        self.assertEqual(vagas.ultima()["situacao"], "concluida")

    def test_com_ia_e_perfil_fica_pendente_e_pede_nota(self):
        (self.tmp / "perfil.md").write_text("# Perfil", encoding="utf-8")
        with mock.patch.object(buscador._ia(), "disponivel", return_value=True):
            b = self.busca_pagina()
        self.assertTrue(b.estado()["resumo"]["com_nota"])
        novas = [v for v in banco.listar_vagas() if v["triagem"] == "pendente"]
        self.assertTrue(novas and all(v["analise_status"] == "pendente" for v in novas))
        analise.FILA.pedir.assert_called_once()

    def test_sem_perfil_ou_sem_nota_nao_vai_para_ia(self):
        with mock.patch.object(buscador._ia(), "disponivel", return_value=True):
            self.busca_pagina()  # sem perfil
            self.assertTrue(all(v["analise_status"] == "sem_analise" for v in banco.listar_vagas()))
            (self.tmp / "perfil.md").write_text("# Perfil", encoding="utf-8")
            pl = buscador.Busca().plano()
            self.assertTrue(pl["perfil_ok"] and pl["ia"]["ligada"])
        analise.FILA.pedir.assert_not_called()

    def test_cancelar(self):
        fonte_falsa.PAUSA = 0.3
        b = buscador.Busca()
        b.iniciar()
        for _ in range(100):
            if fonte_falsa.CHAMADAS:
                break
            time.sleep(0.02)
        self.assertEqual(b.cancelar()["situacao"], "cancelando")
        b._thread.join(10)
        e = b.estado()
        self.assertEqual(e["situacao"], "cancelada")
        self.assertEqual(len(fonte_falsa.CHAMADAS), 1)
        self.assertEqual(banco.listar_vagas(), [])
        self.assertEqual(vagas.ultima()["situacao"], "cancelada")
        self.assertIsNone(b.plano()["proxima_em"])  # cancelada não conta para o intervalo

    def test_bloqueio_conta_para_o_intervalo(self):
        fonte_falsa.ERRO = "HTTP 403"
        b = self.busca_pagina()
        e = b.estado()
        self.assertEqual(e["situacao"], "falha")
        self.assertIn("bloqueio", e["mensagem"])
        self.assertEqual(banco.listar_vagas(), [])
        self.assertTrue(b.plano()["proxima_em"])

    def test_recusas(self):
        sem_cargos = {**CFG, "termos": []}
        (self.tmp / "config.json").write_text(json.dumps(sem_cargos), encoding="utf-8")
        self.assertFalse(buscador.Busca().plano()["filtros_ok"])
        with self.assertRaises(ValueError):
            buscador.Busca().iniciar()
        (self.tmp / "config.json").write_text(json.dumps(CFG), encoding="utf-8")
        b = self.busca_pagina()
        with self.assertRaises(buscador.BuscaRecusada) as ctx:  # logo depois: intervalo mínimo
            b.iniciar()
        self.assertIn("a partir das", str(ctx.exception))
        fim = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
        vagas._gravar_registro({"origem": "pagina", "situacao": "concluida", "fim": fim})
        with self.assertRaises(buscador.BuscaRecusada) as ctx:  # recente: pede confirmação
            b.iniciar()
        self.assertTrue(ctx.exception.precisa_confirmar)
        self.segurar_trava("terminal")
        self.assertEqual(b.estado()["situacao"], "externa")
        self.assertEqual(b.resumo(), {"situacao": "externa", "origem": "terminal"})
        with self.assertRaises(buscador.BuscaRecusada) as ctx:  # busca no terminal
            b.iniciar(confirmar_recente=True)
        self.assertIn("terminal ou no chat", str(ctx.exception))

    def test_interrompida_aparece_no_estado(self):
        vagas._gravar_registro({"origem": "pagina", "inicio": "2026-10-09T10:00:00", "situacao": "rodando"})
        e = buscador.Busca().estado()
        self.assertEqual(e["situacao"], "interrompida")
        self.assertIn("nada dela foi gravado", e["mensagem"])


if __name__ == "__main__":
    unittest.main()
