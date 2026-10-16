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
import types
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


class TestDescricoesPendentes(Base):  # spec 015, US1 (limite) e US2
    def setUp(self):
        super().setUp()
        for p in (mock.patch.object(fonte_falsa, "MAX_DESCRICOES", 1, create=True),
                  mock.patch.object(fonte_falsa, "COM_DESCRICAO", False)):
            p.start()
            self.addCleanup(p.stop)

    def buscar(self, cfg=CFG):
        return vagas.executar(cfg, filtros.efetivos(cfg), ["falsa"], 40, pausa=0)

    def test_limite_e_marca_nas_que_sobram(self):
        r = self.buscar()
        self.assertEqual(len(fonte_falsa.DESCRITAS), 1)  # 3 candidatas e 2 fora: só 1 pedido
        cand = {v["id"] for v in r["candidatas"]}
        self.assertTrue(set(fonte_falsa.DESCRITAS) <= cand)  # candidatas antes das fora
        pend = [v for v in r["candidatas"] if v.get("descricao_pendente")]
        self.assertEqual(len(pend), 2)
        self.assertTrue(all(not v["descricao"] for v in pend))
        self.assertFalse(any(v.get("descricao_pendente") for v in r["fora"]))  # fora não vai para a IA
        g = vagas.gravar_resultado(r, sem_avaliacao=True, status_sem_nota="pendente")
        self.assertEqual(g["pendentes"], 2)
        no_banco = [v for v in banco.listar_vagas() if v.get("descricao_pendente")]
        self.assertEqual(len(no_banco), 2)
        self.assertFalse(any(analise.precisa(v) or banco.precisa_analise(v) for v in no_banco))  # sem nota sem texto
        self.assertEqual(len(banco.pendentes_de_descricao("Falsa")), 2)

    def test_proxima_busca_le_pendentes_primeiro_e_completa(self):
        vagas.gravar_resultado(self.buscar(), sem_avaliacao=True, status_sem_nota="pendente")
        ids_pend = {v["id"] for v in banco.pendentes_de_descricao("Falsa")}
        fonte_falsa.DESCRITAS.clear()
        fonte_falsa.MAX_DESCRICOES = 3
        r = self.buscar({**CFG, "termos": ["gerente"]})  # vagas novas também
        self.assertEqual(set(fonte_falsa.DESCRITAS[:2]), ids_pend)
        self.assertEqual(len(fonte_falsa.DESCRITAS), 3)
        self.assertEqual({c["id"] for c in r["descricoes_completadas"]}, ids_pend)
        g = vagas.gravar_resultado(r, sem_avaliacao=True, status_sem_nota="pendente")
        self.assertEqual(g["completadas"], 2)
        for vid in ids_pend:
            v = banco.obter(vid)
            self.assertNotIn("descricao_pendente", v)
            self.assertIn("lida à parte", v["descricao"])
            self.assertTrue(analise.precisa(v))  # agora vai para a IA

    def test_fonte_parada_nao_pede_e_deixa_pendente(self):
        with mock.patch.object(fonte_falsa, "parada", lambda: True, create=True):
            r = self.buscar()
        self.assertEqual(fonte_falsa.DESCRITAS, [])
        self.assertEqual(sum(1 for v in r["candidatas"] if v.get("descricao_pendente")), 3)

    def test_erro_da_vaga_tira_a_marca(self):
        vagas.gravar_resultado(self.buscar(), sem_avaliacao=True, status_sem_nota="pendente")
        fonte_falsa.MAX_DESCRICOES = 3
        with mock.patch.object(fonte_falsa, "descrever", side_effect=ValueError("respondeu 404")), \
                mock.patch.object(fonte_falsa, "parada", lambda: False, create=True):
            r = self.buscar()
        self.assertEqual(len(r["descricoes_completadas"]), 2)
        self.assertTrue(any("respondeu 404" in e for e in r["erros"]))
        vagas.gravar_resultado(r, sem_avaliacao=True, status_sem_nota="pendente")
        self.assertEqual(banco.pendentes_de_descricao("Falsa"), [])

    def test_descartada_ou_no_quadro_sai_da_fila(self):
        vagas.gravar_resultado(self.buscar(), sem_avaliacao=True, status_sem_nota="pendente")
        a, b = banco.pendentes_de_descricao("Falsa")
        banco.atualizar_usuario(a["id"], {"triagem": "visitada"})
        banco.atualizar_usuario(b["id"], {"triagem": "seguir", "etapa": "salva"})
        self.assertEqual(banco.pendentes_de_descricao("Falsa"), [])

    def test_chat_grava_pendente_sem_nota(self):
        r = self.buscar()
        vagas.gravar_resultado(r, avals=[])  # o chat não avalia as pendentes
        pend = [v for v in banco.listar_vagas() if v.get("descricao_pendente")]
        self.assertEqual(len(pend), 2)
        self.assertTrue(all(v["analise_status"] == "sem_analise" for v in pend))

    def test_fonte_sem_limite_continua_igual(self):
        with mock.patch.object(fonte_falsa, "MAX_DESCRICOES", None):
            r = self.buscar()
        self.assertEqual(len(fonte_falsa.DESCRITAS), 5)
        self.assertFalse(any(v.get("descricao_pendente") for v in r["candidatas"]))
        self.assertEqual(r["descricoes_completadas"], [])


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
        for _ in range(60):  # o Windows solta a trava do processo morto logo depois, não no mesmo instante
            if vagas.ocupada() is None:
                break
            time.sleep(0.05)
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

    def test_um_portal_bloqueado_e_outro_sem_vagas_nao_e_bloqueio(self):
        vazia = types.SimpleNamespace(NOME="vazia", PLATAFORMA="Vazia", buscar=lambda c, h, n: ([], []))
        fonte_falsa.ERRO = "o LinkedIn limitou as consultas (excesso de pedidos)"
        (self.tmp / "config.json").write_text(json.dumps({**CFG, "fontes": ["falsa", "vazia"]}), encoding="utf-8")
        with mock.patch.dict(vagas.FONTES, {"vazia": vazia}):
            e = self.busca_pagina().estado()
        self.assertEqual(e["situacao"], "concluida", e)  # a Vazia respondeu: a busca vale, com zero vagas
        self.assertEqual(e["resumo"]["novas"], 0)
        self.assertTrue(e["erros"] and all(x.startswith("falsa: ") for x in e["erros"]))
        r = {"brutas": 0, "por_busca": {"falsa: a": 0, "vazia: a": 0}, "erros": ["falsa: a: erro"]}
        self.assertFalse(vagas.bloqueio_provavel(r))
        self.assertTrue(vagas.bloqueio_provavel({**r, "erros": ["falsa: a: erro", "vazia: a: erro"]}))

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

    def test_portal_em_espera_pede_confirmacao(self):  # spec 015, US3
        parada = types.SimpleNamespace(NOME="parada", PLATAFORMA="Parada", CHAMADAS=[],
                                       espera=lambda: {"ate": "2026-10-15T17:00", "motivo": "excesso de pedidos"})
        parada.buscar = lambda c, h, n: (parada.CHAMADAS.append(c), ([], []))[1]
        cfg = {**CFG, "fontes": ["falsa", "parada"]}
        (self.tmp / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
        with mock.patch.dict(vagas.FONTES, {"parada": parada}):
            pl = buscador.Busca().plano()
            self.assertEqual(pl["espera"],
                             [{"portal": "Parada", "ate": "2026-10-15T17:00", "motivo": "excesso de pedidos"}])
            self.assertFalse(pl["so_espera"])
            with self.assertRaises(buscador.BuscaRecusada) as ctx:  # sem confirmar: não começa
                buscador.Busca().iniciar()
            self.assertTrue(ctx.exception.precisa_confirmar)
            self.assertIn("em espera até 17:00", str(ctx.exception))
            self.assertEqual(fonte_falsa.CHAMADAS, [])
            b = self.busca_pagina(confirmar_espera=True)
            self.assertEqual(b.estado()["situacao"], "concluida")
            self.assertTrue(fonte_falsa.CHAMADAS)
            vagas._gravar_registro({"origem": "pagina", "situacao": "concluida", "fim": "2026-01-01T00:00:00"})
            (self.tmp / "config.json").write_text(json.dumps({**CFG, "fontes": ["parada"]}), encoding="utf-8")
            self.assertTrue(buscador.Busca().plano()["so_espera"])
            with self.assertRaises(buscador.BuscaRecusada) as ctx:  # só ele: não há o que buscar
                buscador.Busca().iniciar(confirmar_espera=True)
            self.assertFalse(ctx.exception.precisa_confirmar)
            self.assertIn("único portal", str(ctx.exception))

    def test_terminal_sai_com_5_na_espera(self):  # spec 015, US3
        parada = types.SimpleNamespace(NOME="parada", PLATAFORMA="Parada",
                                       espera=lambda: {"ate": "2026-10-15T17:00", "motivo": "pediu login"})
        parada.buscar = lambda c, h, n: ([], [])
        saida = io.StringIO()
        with mock.patch.dict(vagas.FONTES, {"parada": parada}), \
                mock.patch.object(vagas.sys.stdin, "isatty", return_value=False), \
                contextlib.redirect_stderr(saida), contextlib.redirect_stdout(io.StringIO()):
            with mock.patch.object(sys, "argv", ["vagas.py", "buscar", "--fontes", "falsa", "parada", "--pausa", "0"]):
                self.assertEqual(vagas.main(), 5)
            self.assertEqual(fonte_falsa.CHAMADAS, [])
            self.assertIn("--confirmar-espera", saida.getvalue())
            with mock.patch.object(sys, "argv", ["vagas.py", "buscar", "--fontes", "falsa", "parada", "--pausa", "0",
                                                 "--confirmar-espera"]):
                self.assertEqual(vagas.main(), 0)
            self.assertTrue(fonte_falsa.CHAMADAS)

    def test_interrompida_aparece_no_estado(self):
        vagas._gravar_registro({"origem": "pagina", "inicio": "2026-10-09T10:00:00", "situacao": "rodando"})
        e = buscador.Busca().estado()
        self.assertEqual(e["situacao"], "interrompida")
        self.assertIn("nada dela foi gravado", e["mensagem"])


if __name__ == "__main__":
    unittest.main()
