"""IA com reserva (spec 032), sem rede: a principal cai e a próxima da sequência responde; quem respondeu, o aviso e a
marca por thread; o motivo de cada IA quando todas falham; a situação gravada e o alerta; a sequência no painel."""
import json
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]
import ia  # noqa: E402

GEMINI = {"provedor": "gemini", "modelo": "gemini-3.8-flash", "url_base": ""}
OPENROUTER = {"provedor": "openrouter", "modelo": "openrouter/free", "url_base": ""}
GROQ = {"provedor": "groq", "modelo": "", "url_base": ""}
CHAVES = {"GEMINI_API_KEY": "AIzaTESTEgemini0000000000000", "OPENROUTER_API_KEY": "sk-or-teste-000000000000",
          "GROQ_API_KEY": "gsk_teste_00000000000000"}


def config(principal=GEMINI, reservas=(OPENROUTER,)):
    return {"ia": {**principal, "reservas": [dict(r) for r in reservas]}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.cfg = config()
        self.chaves = dict(CHAVES)
        self.respostas = {}  # host -> texto da resposta ou código HTTP de erro
        self.chamadas = []
        self.usar_arquivo = False  # True: a configuração vem do config.json temporário (rotas que gravam)
        for p in (mock.patch.object(ia, "ARQ_ESTADO", self.tmp / "ia-estado.json"),
                  mock.patch.object(ia, "_ler_config", side_effect=self.ler_cfg),
                  mock.patch.object(ia.segredos, "ENV", self.tmp / ".env"),
                  mock.patch.object(ia.segredos, "ler", side_effect=lambda v: self.chaves.get(v, "")),
                  mock.patch.object(ia, "_postar", side_effect=self.postar)):
            p.start()
            self.addCleanup(p.stop)
        ia._local.__dict__.clear()
        self.addCleanup(ia._local.__dict__.clear)

    def ler_cfg(self):
        if self.usar_arquivo:
            import filtros
            return filtros.ler_config()
        return self.cfg

    def postar(self, url, cabecalhos, corpo, tempo, modelo=""):
        host = next((h for h in self.respostas if h in url), None)
        self.chamadas.append(host)
        r = self.respostas.get(host, 503)
        if r == "eco":  # o provedor devolve a chave na mensagem de erro
            raise ia.IAErro("chave errada: " + cabecalhos.get("Authorization", ""))
        if isinstance(r, int):
            raise ia.IAErro(ia.motivo_http(r, "", modelo))
        return {"choices": [{"message": {"content": r}}]}


class TestReserva(Base):  # US1
    def test_principal_cai_e_a_reserva_responde(self):  # SC-001
        self.respostas = {"googleapis": 503, "openrouter": "resposta da reserva"}
        self.assertEqual(ia.responder("pedido"), "resposta da reserva")
        self.assertEqual(self.chamadas, ["googleapis", "openrouter"])
        u = ia.ultima()
        self.assertEqual((u["provedor"], u["modelo"]), ("openrouter", "openrouter/free"))
        self.assertEqual(u["falhas"][0]["nome"], "Gemini (Google)")
        aviso = ia.aviso_reserva()
        self.assertEqual(aviso, "Gemini (Google) fora: o provedor está com problema agora (erro 503); tente mais "
                                "tarde. Respondeu o OpenRouter (openrouter/free).")
        self.assertEqual(ia.marca(), {"provedor": "openrouter", "modelo": "openrouter/free", "reserva": True,
                                      "aviso": aviso})

    def test_principal_funcionando_nao_chama_a_reserva(self):  # SC-002
        self.respostas = {"googleapis": "resposta da principal", "openrouter": "não deveria"}
        self.assertEqual(ia.responder("pedido"), "resposta da principal")
        self.assertEqual(self.chamadas, ["googleapis"])
        self.assertIsNone(ia.aviso_reserva())
        self.assertEqual(ia.marca(), {"provedor": "gemini", "modelo": "gemini-3.8-flash"})

    def test_reserva_sem_chave_e_pulada(self):
        self.cfg = config(reservas=(OPENROUTER, GROQ))
        del self.chaves["OPENROUTER_API_KEY"]
        self.respostas = {"googleapis": 429, "groq": "resposta do groq"}
        self.assertEqual(ia.responder("pedido"), "resposta do groq")
        falhas = ia.ultima()["falhas"]
        self.assertEqual([f["provedor"] for f in falhas], ["gemini", "openrouter"])
        self.assertIn("falta a chave do provedor OpenRouter", falhas[1]["motivo"])
        self.assertIn("Respondeu o Groq", ia.aviso_reserva())

    def test_escolha_explicita_sem_reserva(self):
        self.respostas = {"googleapis": 503, "openrouter": "não deveria"}
        with self.assertRaises(ia.IAErro) as ctx:
            ia.responder("pedido", escolha=GEMINI)
        self.assertEqual(str(ctx.exception), "o provedor está com problema agora (erro 503); tente mais tarde")
        self.assertEqual(self.chamadas, ["googleapis"])

    def test_sem_ia(self):
        self.cfg = {"ia": {"provedor": "nenhum", "modelo": "", "url_base": ""}}
        self.assertEqual(ia.sequencia(), [])
        with self.assertRaises(ia.IAErro) as ctx:
            ia.responder("pedido")
        self.assertIn("desligada", str(ctx.exception))

    def test_formato_antigo_sem_reserva(self):
        self.cfg = {"ia": dict(GEMINI)}
        self.assertEqual(ia.sequencia(), [GEMINI])
        self.respostas = {"googleapis": 503}
        with self.assertRaises(ia.IAErro) as ctx:
            ia.responder("pedido")
        self.assertEqual(str(ctx.exception), "o provedor está com problema agora (erro 503); tente mais tarde")

    def test_marca_por_thread(self):
        self.respostas = {"googleapis": "da principal", "openrouter": "da reserva"}
        marcas = {}

        def rodar(nome, escolha):
            ia.responder("pedido", escolha=escolha)
            marcas[nome] = ia.marca()["provedor"]
        threads = [threading.Thread(target=rodar, args=("a", OPENROUTER)),
                   threading.Thread(target=rodar, args=("b", GEMINI))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(marcas, {"a": "openrouter", "b": "gemini"})
        self.assertIsNone(ia.ultima())  # a thread principal não chamou a IA
        self.assertEqual(ia.marca()["provedor"], "gemini")  # sem chamada: a principal configurada

    def test_respostas_de_formulario_com_o_aviso(self):
        import candidatura_ia
        self.respostas = {"googleapis": 503, "openrouter": '[{"indice": 1, "resposta": "Remoto, no Brasil"}]'}
        campo = {"chave": "c1", "tipo": "texto", "rotulo": "Onde você mora hoje?", "marca": "comum", "limite": 0,
                 "opcoes": [], "obrigatorio": True}
        r = candidatura_ia.propor_respostas({"id": "x", "titulo": "Vaga", "empresa": "Acme"}, [campo],
                                            perfil="Perfil de teste: mora no Brasil e trabalha remoto.")
        self.assertIn("Respondeu o OpenRouter", r["aviso"])
        self.assertEqual(r["ia"]["provedor"], "openrouter")


class TestAviso(Base):  # US2
    def test_todas_fora_com_o_motivo_de_cada_uma(self):  # SC-003
        self.respostas = {"googleapis": 503, "openrouter": 429}
        with self.assertRaises(ia.IAErro) as ctx:
            ia.responder("pedido")
        self.assertEqual(str(ctx.exception),
                         "nenhuma IA respondeu: Gemini (Google): o provedor está com problema agora (erro 503); tente "
                         "mais tarde; OpenRouter: limite de uso atingido no provedor; tente de novo mais tarde")
        self.assertIsNone(ia.aviso_reserva())

    def test_motivo_sem_chave(self):
        self.respostas = {"googleapis": "eco", "openrouter": "eco"}
        with self.assertRaises(ia.IAErro) as ctx:
            ia.responder("pedido")
        for chave in CHAVES.values():
            self.assertNotIn(chave, str(ctx.exception))
        self.assertNotIn(CHAVES["GEMINI_API_KEY"], (self.tmp / "ia-estado.json").read_text(encoding="utf-8"))

    def test_situacao_e_alerta(self):
        self.respostas = {"googleapis": 503, "openrouter": "da reserva"}
        ia.responder("pedido")
        sit = ia.situacao()
        self.assertFalse(sit["gemini|gemini-3.8-flash"]["ok"])
        self.assertIn("erro 503", sit["gemini|gemini-3.8-flash"]["motivo"])
        self.assertTrue(sit["openrouter|openrouter/free"]["ok"])
        a = ia.alerta()
        self.assertEqual((a["nome"], a["modelo"]), ("Gemini (Google)", "gemini-3.8-flash"))
        self.assertIn("erro 503", a["motivo"])
        estado = ia.estado_para_pagina(True)
        self.assertEqual([(e["provedor"], e["principal"], e["chave_ok"], e["gratuito"]) for e in estado["sequencia"]],
                         [("gemini", True, True, False), ("openrouter", False, True, True)])
        self.assertTrue(estado["sequencia"][1]["situacao"]["ok"])
        self.assertEqual(estado["alerta"]["nome"], "Gemini (Google)")
        self.respostas = {"googleapis": "a principal voltou"}
        ia.responder("pedido")
        self.assertIsNone(ia.alerta())  # um sucesso da principal apaga o alerta

    def test_testar_grava_a_situacao(self):
        self.respostas = {"openrouter": "ok"}
        ok, _ = ia.testar(OPENROUTER)
        self.assertTrue(ok)
        self.assertTrue(ia.situacao()["openrouter|openrouter/free"]["ok"])


class TestPainel(Base):  # US3 e o alerta no /api/versao
    def setUp(self):
        super().setUp()
        import http.client

        import banco
        import filtros
        import servidor
        self.http, self.servidor = http.client, servidor
        self.usar_arquivo = True
        filtros_cfg = self.tmp / "config.json"
        filtros_cfg.write_text(json.dumps({"termos": ["x"], "ia": dict(GEMINI)}), encoding="utf-8")
        for p in (mock.patch.object(filtros, "CONFIG", filtros_cfg),
                  mock.patch.object(banco, "ARQUIVO", self.tmp / "banco.db"),
                  mock.patch.object(servidor.Handler, "hosts_permitidos", {"127.0.0.1", "localhost"})):
            p.start()
            self.addCleanup(p.stop)
        self.srv = servidor.ThreadingHTTPServer(("127.0.0.1", 0), servidor.Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.config = filtros_cfg

    def pedir(self, metodo, caminho, corpo=None):
        con = self.http.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=10)
        self.addCleanup(con.close)
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        con.request(metodo, caminho, dados, {"Content-Type": "application/json"} if dados else {})
        r = con.getresponse()
        return r.status, json.loads(r.read())

    def test_gravar_a_sequencia(self):  # SC-004
        with mock.patch.object(self.servidor.analise.FILA, "pedir"):
            status, j = self.pedir("PUT", "/api/ia", {**GEMINI, "reservas": [{**OPENROUTER, "chave": "sk-or-nova-12345678"}]})
        self.assertEqual(status, 200, j)
        self.assertEqual([e["provedor"] for e in j["sequencia"]], ["gemini", "openrouter"])
        texto = self.config.read_text(encoding="utf-8")
        self.assertNotIn("sk-or-nova", texto)  # a chave vai para o .env, nunca para o config.json
        self.assertEqual(json.loads(texto)["ia"]["reservas"], [OPENROUTER])
        self.assertIn("sk-or-nova-12345678", (self.tmp / ".env").read_text(encoding="utf-8"))
        with mock.patch.object(self.servidor.analise.FILA, "pedir"):
            self.assertEqual(self.pedir("PUT", "/api/ia", dict(GEMINI))[0], 200)  # sem "reservas": a lista fica
        self.assertEqual(json.loads(self.config.read_text(encoding="utf-8"))["ia"]["reservas"], [OPENROUTER])
        with mock.patch.object(self.servidor.analise.FILA, "pedir"):
            self.pedir("PUT", "/api/ia", {**GEMINI, "reservas": []})  # lista vazia: apaga
        self.assertNotIn("reservas", json.loads(self.config.read_text(encoding="utf-8"))["ia"])

    def test_regras_das_reservas(self):
        status, j = self.pedir("PUT", "/api/ia", {**GEMINI, "reservas": [OPENROUTER, GROQ, OPENROUTER]})
        self.assertEqual(status, 400)
        self.assertIn("reserva repetida", j["erro"])
        quatro = [OPENROUTER, GROQ, {"provedor": "deepseek"}, {"provedor": "openai"}]
        self.assertIn("no máximo 3 reservas", self.pedir("PUT", "/api/ia", {**GEMINI, "reservas": quatro})[1]["erro"])
        self.assertIn("Sem IA não pode ser reserva",
                      self.pedir("PUT", "/api/ia", {**GEMINI, "reservas": [{"provedor": "nenhum"}]})[1]["erro"])

    def test_alerta_no_api_versao(self):
        self.respostas = {"googleapis": 503}
        with self.assertRaises(ia.IAErro):
            ia.responder("pedido")
        status, j = self.pedir("GET", "/api/versao")
        self.assertEqual(status, 200)
        self.assertEqual(j["ia_alerta"]["nome"], "Gemini (Google)")
        status, j = self.pedir("GET", "/api/ia")
        self.assertEqual(j["alerta"]["nome"], "Gemini (Google)")


if __name__ == "__main__":
    unittest.main()
