"""
Roda os 3 smoke tests em sequência e imprime resultado consolidado.

Uso:
  .venv/bin/python smoke_all.py
"""

import subprocess
import sys
import time

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
        "nome": "Giskard Smoke",
        "cmd": [sys.executable, "tests/giskard/giskard_smoke.py"],
    },
    {
        "nome": "Garak Smoke",
        "cmd": [sys.executable, "tests/garak/garak_smoke.py"],
    },
]


def main():
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
