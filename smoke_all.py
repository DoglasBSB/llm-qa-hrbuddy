"""
Roda os smoke tests em sequência e imprime resultado consolidado.

Uso:
  .venv/bin/python smoke_all.py              # DeepEval + Garak
  .venv/bin/python smoke_all.py --all        # inclui Promptfoo (requer Node.js + npx)
"""

import subprocess
import sys
import shutil
import time

_incluir_promptfoo = "--all" in sys.argv

TESTES = [
    {
        "nome": "DeepEval",
        "cmd": [
            sys.executable, "-m", "pytest",
            "tests/deepeval/test_hrbuddy_completo.py",
            "-k", "mem01 or grd05 or qua04 or sec01",
            "-v", "--tb=short"
        ],
    },
    {
        "nome": "Garak Smoke",
        "cmd": [sys.executable, "tests/garak/garak_smoke.py"],
    },
    *([{
        "nome": "Promptfoo Smoke",
        "cmd": [
            "npx", "promptfoo", "eval",
            "--config", "tests/promptfoo/promptfooconfig.yaml",
            "--no-cache"
        ],
    }] if _incluir_promptfoo else []),
]


def main():
    if _incluir_promptfoo and not shutil.which("npx"):
        print("AVISO: npx não encontrado. Instale Node.js para rodar o Promptfoo.")
        print("       Rodando sem o Promptfoo Smoke.\n")
        TESTES.pop()

    print("=" * 60)
    print("  SMOKE TESTS — HR BUDDY CHOCOLATECH")
    print("=" * 60)
    print()

    resultados = []

    for teste in TESTES:
        print(f"▶ Rodando: {teste['nome']}...")
        inicio = time.time()

        resultado = subprocess.run(teste["cmd"], capture_output=False)

        duracao = round(time.time() - inicio, 1)
        passou = resultado.returncode == 0
        resultados.append((teste["nome"], passou, duracao))
        print()

    print("=" * 60)
    print("  RESULTADO FINAL")
    print("=" * 60)
    for nome, passou, duracao in resultados:
        icone = "✅" if passou else "❌"
        print(f"  {icone}  {nome:<20} {duracao}s")

    total = len(resultados)
    aprovados = sum(p for _, p, _ in resultados)
    print()
    print(f"  {aprovados}/{total} suites OK")
    print("=" * 60)

    sys.exit(0 if aprovados == total else 1)


if __name__ == "__main__":
    main()
