"""Testes para o comando de calibração da nota (spec 062, T007)."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "dash")]

import analise  # noqa: E402
import banco  # noqa: E402
import calibrar_nota  # noqa: E402
import ia  # noqa: E402


def criar_vaga(vid: str, aderencia=75, status="feita", desc="Texto da vaga", **extras) -> dict:
    return {
        "id": vid,
        "titulo": f"Cargo {vid}",
        "empresa": f"Empresa {vid}",
        "analise_status": status,
        "aderencia": aderencia,
        "descricao": desc,
        **extras,
    }


class TestFuncoesPuras(unittest.TestCase):
    def test_partes_do_pedido(self):
        texto = (
            "Texto inicial de regras.\n"
            "## Perfil do usuário (a única fonte)\n"
            "Texto do perfil fictício.\n"
            "## Filtros da busca do usuário\n"
            "Filtros fictícios.\n"
            "## Vagas (dados)\n"
            "Texto da vaga.\n"
        )
        partes = calibrar_nota.partes_do_pedido(texto)
        self.assertEqual(partes["total"], len(texto))
        self.assertEqual(
            partes["regras"] + partes["perfil"] + partes["filtros"] + partes["vaga"],
            partes["total"],
        )
        self.assertGreater(partes["regras"], 0)
        self.assertGreater(partes["perfil"], 0)
        self.assertGreater(partes["filtros"], 0)
        self.assertGreater(partes["vaga"], 0)

    def test_escolher_amostra_filtros(self):
        # Exclui provisória (nota_sem_descricao), sem descrição e sem nota
        vagas = [
            criar_vaga("v1", aderencia=85),  # elegível
            criar_vaga("v2", status="pendente", aderencia=85),  # status errado
            criar_vaga("v3", aderencia=None),  # sem nota
            criar_vaga("v4", aderencia=80, desc=""),  # sem descrição
            criar_vaga("v5", aderencia=80, desc="   "),  # descrição em branco
            criar_vaga("v6", aderencia=80, nota_sem_descricao=True),  # provisória
        ]
        amostra = calibrar_nota.escolher_amostra(vagas, n=10)
        self.assertEqual([v["id"] for v in amostra], ["v1"])

    def test_escolher_amostra_faixas_e_n(self):
        # Cria vagas em todas as 4 faixas
        vagas = [
            criar_vaga("f0_1", aderencia=90),
            criar_vaga("f0_2", aderencia=85),
            criar_vaga("f1_1", aderencia=75),
            criar_vaga("f1_2", aderencia=70),
            criar_vaga("f2_1", aderencia=60),
            criar_vaga("f2_2", aderencia=55),
            criar_vaga("f3_1", aderencia=40),
            criar_vaga("f3_2", aderencia=30),
        ]
        # Respeita n
        amostra_4 = calibrar_nota.escolher_amostra(vagas, n=4, semente=42)
        self.assertEqual(len(amostra_4), 4)
        # Deve ter pegado uma de cada faixa no rodízio
        faixas_pegas = set()
        for v in amostra_4:
            nota = v["aderencia"]
            if nota >= 80:
                faixas_pegas.add(0)
            elif nota >= 65:
                faixas_pegas.add(1)
            elif nota >= 50:
                faixas_pegas.add(2)
            else:
                faixas_pegas.add(3)
        self.assertEqual(faixas_pegas, {0, 1, 2, 3})

    def test_escolher_amostra_prefere_modelo(self):
        vagas = [
            criar_vaga("v_outro_1", aderencia=85, analise_modelo="outro"),
            criar_vaga("v_alvo", aderencia=85, analise_modelo="gemini-flash"),
            criar_vaga("v_outro_2", aderencia=85, analise_modelo="outro"),
        ]
        amostra = calibrar_nota.escolher_amostra(vagas, n=1, modelo="gemini-flash", semente=10)
        self.assertEqual(len(amostra), 1)
        self.assertEqual(amostra[0]["id"], "v_alvo")

    def test_escolher_amostra_mesma_semente_mesmo_resultado(self):
        vagas = [criar_vaga(f"v{i}", aderencia=30 + (i * 7) % 65) for i in range(50)]
        amostra_a = calibrar_nota.escolher_amostra(vagas, n=15, semente=1234)
        amostra_b = calibrar_nota.escolher_amostra(vagas, n=15, semente=1234)
        self.assertEqual([v["id"] for v in amostra_a], [v["id"] for v in amostra_b])

    def test_comparar_e_resumir_passa(self):
        # 10 vagas: 9 com diferença <= 10 e sem troca de fora -> 90% dentro passa
        linhas = []
        for i in range(9):
            vaga = criar_vaga(f"v{i}", aderencia=80, analise_modelo="gpt")
            resp = {"id": f"v{i}", "aderencia": 85}  # dif +5
            linhas.append(calibrar_nota.comparar(vaga, resp))
        # 1 vaga com diferença > 10
        vaga9 = criar_vaga("v9", aderencia=50, analise_modelo="gpt")
        resp9 = {"id": "v9", "aderencia": 70}  # dif +20
        linhas.append(calibrar_nota.comparar(vaga9, resp9))

        res = calibrar_nota.resumir(linhas)
        self.assertEqual(res["respondidas"], 10)
        self.assertEqual(res["dentro_de_10"], 0.9)
        self.assertEqual(res["trocas_fora"], 0)
        self.assertTrue(res["passa"])

    def test_resumir_troca_fora_nao_passa(self):
        linhas = []
        for i in range(10):
            vaga = criar_vaga(f"v{i}", aderencia=80, fora_dos_criterios="motivo" if i == 0 else "")
            # i == 0 tinha fora_antes=True, mas resposta vem sem fora_dos_criterios (troca de fora -> dentro)
            resp = {"id": f"v{i}", "aderencia": 80}
            linhas.append(calibrar_nota.comparar(vaga, resp))

        res = calibrar_nota.resumir(linhas)
        self.assertEqual(res["trocas_fora"], 1)
        self.assertFalse(res["passa"])

    def test_resumir_nenhuma_respondida_nao_passa(self):
        vaga = criar_vaga("v1", aderencia=80)
        linha = calibrar_nota.comparar(vaga, None, erro="falha")
        res = calibrar_nota.resumir([linha])
        self.assertEqual(res["respondidas"], 0)
        self.assertFalse(res["passa"])


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    @mock.patch.object(calibrar_nota, "CACHE")
    @mock.patch("time.sleep")
    @mock.patch("analise.montar_pedido")
    @mock.patch("banco.obter")
    @mock.patch("ia.sequencia")
    @mock.patch("ia.responder")
    @mock.patch("ia.disponivel")
    def test_main_ids_com_sucesso_e_sem_gravar_banco(
        self,
        mock_disp,
        mock_resp,
        mock_seq,
        mock_obter,
        mock_pedido,
        mock_sleep,
        mock_cache,
    ):
        mock_cache.__truediv__.side_effect = lambda f: self.tmp / f
        mock_cache.mkdir.return_value = None
        mock_disp.return_value = True
        mock_seq.return_value = [{"provedor": "gemini", "modelo": "gemini-flash"}]
        mock_pedido.return_value = (
            "Regras fixas.\n"
            "## Perfil do usuário\nPerfil.\n"
            "## Filtros da busca do usuário\nFiltros.\n"
            "## Vagas\nVaga.\n"
        )
        v1 = criar_vaga("id1", aderencia=80, analise_modelo="gemini-flash")
        v2 = criar_vaga("id2", aderencia=70, analise_modelo="gemini-flash")
        mock_obter.side_effect = lambda vid: v1 if vid == "id1" else (v2 if vid == "id2" else None)

        mock_resp.return_value = json.dumps([
            {"id": "id1", "aderencia": 82},
            {"id": "id2", "aderencia": 68},
        ])

        with mock.patch("banco.aplicar_analises") as mock_gravar:
            codigo = calibrar_nota.main(["--ids", "id1,id2"])
            self.assertEqual(codigo, 0)
            mock_gravar.assert_not_called()

        arquivos_json = list(self.tmp.glob("calibracao-*.json"))
        self.assertEqual(len(arquivos_json), 1)
        relatorio = json.loads(arquivos_json[0].read_text(encoding="utf-8"))
        self.assertEqual(relatorio["ia"]["provedor"], "gemini")
        self.assertEqual(relatorio["resumo"]["respondidas"], 2)
        self.assertTrue(relatorio["resumo"]["passa"])

    @mock.patch.object(calibrar_nota, "CACHE")
    @mock.patch("time.sleep")
    @mock.patch("analise.montar_pedido")
    @mock.patch("banco.obter")
    @mock.patch("ia.sequencia")
    @mock.patch("ia.responder")
    @mock.patch("ia.disponivel")
    def test_main_429_espera_e_tenta_de_novo(
        self,
        mock_disp,
        mock_resp,
        mock_seq,
        mock_obter,
        mock_pedido,
        mock_sleep,
        mock_cache,
    ):
        mock_cache.__truediv__.side_effect = lambda f: self.tmp / f
        mock_cache.mkdir.return_value = None
        mock_disp.return_value = True
        mock_seq.return_value = [{"provedor": "gemini", "modelo": "gemini-flash"}]
        mock_pedido.return_value = (
            "Regras\n## Perfil do usuário\nP\n## Filtros da busca do usuário\nF\n## Vagas\nV\n"
        )
        v = criar_vaga("id1", aderencia=80)
        mock_obter.return_value = v

        # Primeiro pedido dá 429 com espera=5; segundo tem sucesso
        mock_resp.side_effect = [
            ia.IAErro("limite atingido", limite=True, espera=5),
            json.dumps([{"id": "id1", "aderencia": 85}]),
        ]

        with mock.patch("banco.aplicar_analises") as mock_gravar:
            codigo = calibrar_nota.main(["--ids", "id1"])
            self.assertEqual(codigo, 0)
            mock_gravar.assert_not_called()

        # Confere que time.sleep(5) foi chamado
        mock_sleep.assert_any_call(5)
        self.assertEqual(mock_resp.call_count, 2)

    @mock.patch.object(calibrar_nota, "CACHE")
    @mock.patch("banco.obter")
    @mock.patch("analise.montar_pedido")
    def test_main_medir(self, mock_pedido, mock_obter, mock_cache):
        mock_cache.__truediv__.side_effect = lambda f: self.tmp / f
        mock_cache.mkdir.return_value = None
        v = criar_vaga("v_medir", desc="Descricao longa")
        mock_obter.return_value = v
        mock_pedido.return_value = (
            "Regras\n## Perfil do usuário\nP\n## Filtros da busca do usuário\nF\n## Vagas\nV\n"
        )

        codigo = calibrar_nota.main(["--medir", "v_medir"])
        self.assertEqual(codigo, 0)
        arq_txt = self.tmp / "pedido-v_medir.txt"
        self.assertTrue(arq_txt.exists())
        self.assertIn("## Vagas", arq_txt.read_text(encoding="utf-8"))

    @mock.patch("ia.disponivel", return_value=False)
    def test_main_sem_ia_retorna_2(self, _mock_disp):
        self.assertEqual(calibrar_nota.main([]), 2)

    @mock.patch("ia.disponivel", return_value=True)
    @mock.patch("banco.listar_vagas", return_value=[])
    def test_main_sem_vagas_retorna_2(self, _mock_listar, _mock_disp):
        self.assertEqual(calibrar_nota.main([]), 2)

    def test_base_antes(self):
        v = criar_vaga("id1", aderencia=80, analise_modelo="outra-ia", fora_dos_criterios="x")
        b = calibrar_nota.base_antes(v, {"id": "id1", "aderencia": 60}, "origin/master")
        self.assertEqual((b["aderencia"], b["fora_dos_criterios"], b["analise_modelo"]),
                         (60, None, "regras de origin/master"))
        self.assertEqual(v["aderencia"], 80)  # a vaga original não muda

    def test_montador_antigo_carrega_a_versao_do_git(self):
        codigo = "SKILL = None\nREGRAS = None\ndef montar_pedido(lote):\n    return 'antigo:' + str(len(lote))\n"
        with mock.patch.object(calibrar_nota, "_git_show", side_effect=lambda rc: codigo if rc.endswith(".py")
                               else "texto"):
            montar = calibrar_nota.montador_antigo("origin/master")
        self.assertEqual(montar([1, 2]), "antigo:2")
        with mock.patch.object(calibrar_nota, "_git_show", return_value=None):
            self.assertIsNone(calibrar_nota.montador_antigo("nao-existe"))

    @mock.patch.object(calibrar_nota, "CACHE")
    @mock.patch("time.sleep")
    @mock.patch("banco.obter")
    @mock.patch("ia.sequencia")
    @mock.patch("ia.responder")
    @mock.patch("ia.disponivel")
    def test_main_antes_compara_regras_na_mesma_ia(self, mock_disp, mock_resp, mock_seq, mock_obter, mock_sleep,
                                                  mock_cache):
        mock_cache.__truediv__.side_effect = lambda f: self.tmp / f
        mock_cache.mkdir.return_value = None
        mock_disp.return_value = True
        mock_seq.return_value = [{"provedor": "claude_code", "modelo": ""}]
        v1 = criar_vaga("id1", aderencia=90, analise_modelo="outra-ia")  # nota gravada bem diferente
        mock_obter.side_effect = lambda vid: v1 if vid == "id1" else None
        pedidos = []

        def responder(pedido, **_):
            pedidos.append(pedido)
            nota = 60 if pedido.startswith("antigo") else 64
            return json.dumps([{"id": "id1", "aderencia": nota}])
        mock_resp.side_effect = responder
        with mock.patch.object(calibrar_nota, "montador_antigo", return_value=lambda lote: "antigo"), \
                mock.patch("analise.montar_pedido", return_value="novo\n## Perfil do usuário\n## Filtros da busca"
                           " do usuário\n## Vagas\n"), \
                mock.patch("banco.aplicar_analises") as mock_gravar:
            codigo = calibrar_nota.main(["--ids", "id1", "--antes", "origin/master"])
        self.assertEqual(codigo, 0)  # 60 -> 64: passa, embora a nota gravada (90) esteja longe
        mock_gravar.assert_not_called()
        self.assertEqual([p[:6] for p in pedidos], ["antigo", "novo\n#"])
        relatorio = json.loads(next(self.tmp.glob("calibracao-*.json")).read_text(encoding="utf-8"))
        linha = relatorio["vagas"][0]
        self.assertEqual((linha["nota_antes"], linha["nota_depois"], linha["modelo_antes"]),
                         (60, 64, "regras de origin/master"))
