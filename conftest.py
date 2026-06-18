"""
Carrega .env e configura Groq (llama-3.3-70b-versatile) como LLM de avaliação
do DeepEval via endpoint OpenAI-compatível — sem custo OpenAI.

Também salva os resultados DeepEval em .deepeval/results.json após cada sessão
para que relatorio_consolidado.py possa agregá-los.
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da raiz do projeto independente de onde o pytest é chamado
load_dotenv(Path(__file__).parent / ".env")

groq_key = os.environ.get("GROQ_API_KEY")

if groq_key:
    os.environ["OPENAI_API_KEY"] = groq_key
    os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
    os.environ["OPENAI_MODEL_NAME"] = "llama-3.3-70b-versatile"
else:
    print("\n[conftest] GROQ_API_KEY não encontrado no .env nem no ambiente.")
    print("  Adicione ao arquivo .env: GROQ_API_KEY=gsk_...\n")


def pytest_sessionfinish(session, exitstatus):
    """Salva resultados DeepEval em .deepeval/results.json após a sessão."""
    try:
        from deepeval.test_run.test_run import global_test_run_manager

        test_run = global_test_run_manager.get_test_run()
        if not test_run or not test_run.test_cases:
            return

        resultados = []
        for tc in test_run.test_cases:
            metricas = []
            for m in (tc.metrics_data or []):
                metricas.append({
                    "name":      getattr(m, "name", "?"),
                    "score":     getattr(m, "score", None),
                    "threshold": getattr(m, "threshold", None),
                    "success":   getattr(m, "success", None),
                    "reason":    getattr(m, "reason", None),
                })
            resultados.append({
                "name":         tc.name,
                "input":        getattr(tc, "input", ""),
                "actual_output": getattr(tc, "actual_output", ""),
                "success":      tc.success,
                "metrics_data": metricas,
            })

        saida = Path(".deepeval")
        saida.mkdir(exist_ok=True)
        arquivo = saida / "results.json"
        arquivo.write_text(
            json.dumps(resultados, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n[conftest] Resultados DeepEval salvos em {arquivo} ({len(resultados)} testes)")

    except Exception as e:
        print(f"\n[conftest] Não foi possível salvar resultados DeepEval: {e}")
