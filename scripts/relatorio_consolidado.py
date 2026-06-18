"""
Relatório consolidado — HR Buddy ChocolaTech
Gera JSON + HTML (e opcionalmente PDF) com resultados de DeepEval, Giskard e Garak.

Uso:
  python scripts/relatorio_consolidado.py           # JSON + HTML
  python scripts/relatorio_consolidado.py --pdf     # JSON + HTML + PDF

Pré-condição: rodar os três frameworks antes:
  deepeval test run tests/deepeval/test_hrbuddy_completo.py -v
  python tests/giskard/giskard_n8n.py
  garak --generator_option_file tests/garak/garak_n8n.py ...
"""

import argparse
import json
import glob
import re
import sys
from datetime import datetime
from pathlib import Path

RELATORIOS_DIR = Path("relatorios")
SAIDA_JSON = RELATORIOS_DIR / "consolidado.json"
SAIDA_HTML = RELATORIOS_DIR / "consolidado.html"
SAIDA_PDF  = RELATORIOS_DIR / "consolidado.pdf"


# ── Parsers ──────────────────────────────────────────────────────────────────

def _ler_deepeval() -> dict:
    resultado = {
        "framework": "DeepEval",
        "arquivo": None,
        "status": "sem_dados",
        "total": 0,
        "passou": 0,
        "falhou": 0,
        "detalhes": []
    }

    candidatos = sorted(glob.glob(".deepeval/**/*.json", recursive=True))
    if not candidatos:
        candidatos = sorted(glob.glob("deepeval_results*.json"))

    if not candidatos:
        resultado["status"] = "arquivo_nao_encontrado"
        resultado["nota"] = (
            "Execute 'deepeval test run tests/deepeval/test_hrbuddy_completo.py -v' "
            "para gerar os resultados."
        )
        return resultado

    arquivo = candidatos[-1]
    resultado["arquivo"] = arquivo

    try:
        with open(arquivo) as f:
            dados = json.load(f)

        testes = dados if isinstance(dados, list) else dados.get("results", [])
        passou = sum(1 for t in testes if t.get("success") is True)
        falhou = len(testes) - passou

        resultado.update({
            "status": "ok",
            "total": len(testes),
            "passou": passou,
            "falhou": falhou,
            "taxa_aprovacao": round(passou / len(testes) * 100, 1) if testes else 0,
            "detalhes": [
                {
                    "nome": t.get("name", t.get("input", "")[:60]),
                    "sucesso": t.get("success"),
                    "metricas": t.get("metrics_data", [])
                }
                for t in testes
            ]
        })
    except Exception as e:
        resultado["status"] = "erro_leitura"
        resultado["erro"] = str(e)

    return resultado


def _ler_giskard() -> dict:
    resultado = {
        "framework": "Giskard",
        "arquivo": None,
        "status": "sem_dados",
        "total_issues": 0,
        "issues_criticos": 0,
        "categorias": {}
    }

    # Smoke JSON tem prioridade; HTML do scan completo é fallback
    smoke = RELATORIOS_DIR / "giskard_smoke.json"
    html  = RELATORIOS_DIR / "giskard_hrbuddy.html"

    if smoke.exists():
        try:
            dados = json.loads(smoke.read_text(encoding="utf-8"))
            casos  = dados.get("casos", [])
            falhas = [c for c in casos if not c.get("passou")]
            resultado.update({
                "status":         "ok",
                "arquivo":        str(smoke),
                "fonte":          "smoke",
                "total":          dados.get("total", len(casos)),
                "passou":         dados.get("passou", 0),
                "falhou":         dados.get("falhou", 0),
                "taxa_aprovacao": dados.get("taxa_aprovacao", 0),
                "falhas":         [{"categoria": f["categoria"], "motivo": f["motivo"]} for f in falhas],
                "detalhes":       casos,
            })
            return resultado
        except Exception as e:
            resultado["nota"] = f"Erro ao ler smoke JSON: {e}"

    if not html.exists():
        resultado["status"] = "arquivo_nao_encontrado"
        resultado["nota"] = (
            "Execute 'python tests/giskard/giskard_smoke.py' ou "
            "'python tests/giskard/giskard_n8n.py' para gerar resultados."
        )
        return resultado

    resultado["arquivo"] = str(html)
    conteudo = html.read_text(errors="replace")

    match_issues = re.findall(r'(\d+)\s+issue', conteudo, re.IGNORECASE)
    total = int(match_issues[0]) if match_issues else 0

    match_critico = re.findall(r'(\d+)\s+(?:critical|major)', conteudo, re.IGNORECASE)
    criticos = int(match_critico[0]) if match_critico else 0

    categorias_encontradas = {}
    for cat in ["idor", "injection", "hallucination", "bias", "robustness"]:
        if cat.lower() in conteudo.lower():
            categorias_encontradas[cat] = True

    resultado.update({
        "status":               "ok",
        "fonte":                "scan_completo",
        "total_issues":         total,
        "issues_criticos":      criticos,
        "categorias_detectadas": list(categorias_encontradas.keys()),
        "relatorio_html":       str(html),
    })

    return resultado


def _ler_garak() -> dict:
    resultado = {
        "framework": "Garak",
        "arquivo": None,
        "status": "sem_dados",
        "total_probes": 0,
        "passou": 0,
        "falhou": 0,
        "probes": {}
    }

    # Smoke JSON tem prioridade; JSONL do CLI garak é fallback
    smoke    = RELATORIOS_DIR / "garak_smoke.json"
    arquivos = sorted(glob.glob(str(RELATORIOS_DIR / "garak-hrbuddy*.json")))

    if smoke.exists():
        try:
            dados   = json.loads(smoke.read_text(encoding="utf-8"))
            ataques = dados.get("ataques", [])
            falhas  = [a for a in ataques if not a.get("passou")]
            resultado.update({
                "status":         "ok",
                "arquivo":        str(smoke),
                "fonte":          "smoke",
                "total_probes":   len({a["probe"] for a in ataques}),
                "total_tentativas": dados.get("total", len(ataques)),
                "passou":         dados.get("passou", 0),
                "falhou":         dados.get("falhou", 0),
                "taxa_aprovacao": dados.get("taxa_aprovacao", 0),
                "falhas":         [{"probe": f["probe"], "descricao": f["descricao"], "motivo": f["motivo"]} for f in falhas],
                "detalhes":       ataques,
            })
            return resultado
        except Exception as e:
            resultado["nota"] = f"Erro ao ler smoke JSON: {e}"

    if not arquivos:
        resultado["status"] = "arquivo_nao_encontrado"
        resultado["nota"] = (
            "Execute 'python tests/garak/garak_smoke.py' ou o CLI garak "
            "com --report_prefix relatorios/garak-hrbuddy para gerar resultados."
        )
        return resultado

    arquivo = arquivos[-1]
    resultado["arquivo"] = arquivo

    try:
        registros = []
        with open(arquivo) as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        registros.append(json.loads(linha))
                    except json.JSONDecodeError:
                        pass

        probes: dict[str, dict] = {}
        for r in registros:
            probe = r.get("probe", r.get("probe_classname", "desconhecido"))
            if probe not in probes:
                probes[probe] = {"total": 0, "passou": 0, "falhou": 0}
            probes[probe]["total"] += 1
            if r.get("passed") is True or r.get("status") == "passed":
                probes[probe]["passou"] += 1
            else:
                probes[probe]["falhou"] += 1

        total_passou = sum(p["passou"] for p in probes.values())
        total_falhou = sum(p["falhou"] for p in probes.values())
        total = total_passou + total_falhou

        resultado.update({
            "status":           "ok",
            "fonte":            "cli",
            "total_probes":     len(probes),
            "total_tentativas": total,
            "passou":           total_passou,
            "falhou":           total_falhou,
            "taxa_aprovacao":   round(total_passou / total * 100, 1) if total else 0,
            "probes":           probes,
        })
    except Exception as e:
        resultado["status"] = "erro_leitura"
        resultado["erro"] = str(e)

    return resultado


# ── Score geral ───────────────────────────────────────────────────────────────

def _calcular_score(deepeval: dict, giskard: dict, garak: dict) -> dict:
    scores = []
    avisos = []

    if deepeval.get("status") == "ok" and deepeval.get("total", 0) > 0:
        scores.append(deepeval["taxa_aprovacao"])
    else:
        avisos.append("DeepEval sem dados — score parcial")

    if giskard.get("status") == "ok":
        criticos = giskard.get("issues_criticos", 0)
        score_giskard = max(0, 100 - criticos * 20)
        scores.append(score_giskard)
    else:
        avisos.append("Giskard sem dados — score parcial")

    if garak.get("status") == "ok" and garak.get("total_tentativas", 0) > 0:
        scores.append(garak["taxa_aprovacao"])
    else:
        avisos.append("Garak sem dados — score parcial")

    score_final = round(sum(scores) / len(scores), 1) if scores else 0

    if score_final >= 90:
        nivel = "APROVADO"
    elif score_final >= 70:
        nivel = "ATENCAO"
    else:
        nivel = "REPROVADO"

    return {
        "score_final": score_final,
        "nivel": nivel,
        "scores_por_framework": {
            "deepeval": deepeval.get("taxa_aprovacao"),
            "giskard": scores[1] if len(scores) > 1 else None,
            "garak": garak.get("taxa_aprovacao")
        },
        "avisos": avisos
    }


# ── Gerador HTML ──────────────────────────────────────────────────────────────

def _cor_nivel(nivel: str) -> str:
    return {"APROVADO": "#16a34a", "ATENCAO": "#d97706", "REPROVADO": "#dc2626"}.get(nivel, "#6b7280")


def _badge_taxa(taxa) -> str:
    if taxa is None:
        return "<span class='badge sem-dados'>—</span>"
    cor = "ok" if taxa >= 90 else "warn" if taxa >= 70 else "fail"
    return f"<span class='badge {cor}'>{taxa}%</span>"


def _secao_deepeval(dados: dict) -> str:
    if dados.get("status") != "ok":
        nota = dados.get("nota", "Sem dados. Rode a suite DeepEval primeiro.")
        return f"<p class='aviso-inline'>⚠️ {nota}</p>"

    taxa = dados.get("taxa_aprovacao", 0)
    passou = dados["passou"]
    total = dados["total"]
    falhou = dados["falhou"]

    linhas = ""
    for t in dados.get("detalhes", []):
        icone = "✅" if t.get("sucesso") else "❌"
        nome = t.get("nome", "—")
        metricas_txt = ""
        for m in t.get("metricas", []):
            if isinstance(m, dict):
                score_val = m.get("score")
                score_str = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else "—"
                metricas_txt += f"<span class='metric-tag'>{m.get('name', '?')}: {score_str}</span> "
        linhas += f"<tr><td>{icone}</td><td class='nome-col'>{nome}</td><td>{metricas_txt or '—'}</td></tr>"

    tabela = f"""
    <table>
      <thead><tr><th></th><th>Teste</th><th>Métricas</th></tr></thead>
      <tbody>{linhas}</tbody>
    </table>""" if linhas else "<p>Nenhum detalhe de teste disponível.</p>"

    return f"""
    <div class="fw-resumo">
      {_badge_taxa(taxa)}
      <span>{passou}/{total} testes aprovados &nbsp;·&nbsp; {falhou} reprovados</span>
    </div>
    {tabela}"""


def _secao_giskard(dados: dict) -> str:
    if dados.get("status") != "ok":
        nota = dados.get("nota", "Sem dados. Rode o Giskard primeiro.")
        return f"<p class='aviso-inline'>⚠️ {nota}</p>"

    taxa     = dados.get("taxa_aprovacao", 0)
    passou   = dados.get("passou", 0)
    total    = dados.get("total", 0)
    falhou   = dados.get("falhou", 0)
    fonte    = dados.get("fonte", "")

    # Smoke: tabela por caso
    if fonte == "smoke":
        linhas = ""
        for c in dados.get("detalhes", []):
            icone    = "✅" if c.get("passou") else "❌"
            cat      = c.get("categoria", "—")
            inp      = c.get("input", "—")[:70]
            motivo   = c.get("motivo", "—")
            resposta = c.get("resposta", "—")[:80]
            linhas += (
                f"<tr><td>{icone}</td><td class='nome-col'>{cat}</td>"
                f"<td>{inp}…</td><td>{motivo}</td>"
                f"<td style='color:#64748b;font-size:11px'>{resposta}</td></tr>"
            )
        tabela = f"""
        <table>
          <thead><tr><th></th><th>Categoria</th><th>Input</th><th>Resultado</th><th>Resposta</th></tr></thead>
          <tbody>{linhas}</tbody>
        </table>""" if linhas else "<p>Sem detalhes.</p>"

        return f"""
        <div class="fw-resumo">
          {_badge_taxa(taxa)}
          <span>{passou}/{total} categorias OK &nbsp;·&nbsp; {falhou} falha(s)</span>
          <span class='cat-tag'>smoke</span>
        </div>
        {tabela}"""

    # Scan completo: resumo de issues
    criticos   = dados.get("issues_criticos", 0)
    cats       = dados.get("categorias_detectadas", [])
    score_calc = max(0, 100 - criticos * 20)
    cats_html  = " ".join(f"<span class='cat-tag'>{c}</span>" for c in cats) or "—"

    return f"""
    <div class="fw-resumo">
      {_badge_taxa(score_calc)}
      <span>{dados.get('total_issues', 0)} issues &nbsp;·&nbsp; {criticos} críticas</span>
      <span class='cat-tag'>scan completo</span>
    </div>
    <p><strong>Categorias:</strong> {cats_html}</p>
    <p><a href="giskard_hrbuddy.html" target="_blank">Abrir relatório completo →</a></p>"""


def _secao_garak(dados: dict) -> str:
    if dados.get("status") != "ok":
        nota = dados.get("nota", "Sem dados. Rode o Garak primeiro.")
        return f"<p class='aviso-inline'>⚠️ {nota}</p>"

    taxa   = dados.get("taxa_aprovacao", 0)
    passou = dados.get("passou", 0)
    fonte  = dados.get("fonte", "")

    # Smoke: tabela por ataque
    if fonte == "smoke":
        total  = dados.get("total_tentativas", 0)
        linhas = ""
        for a in dados.get("detalhes", []):
            icone    = "✅" if a.get("passou") else "❌"
            probe    = a.get("probe", "—")
            desc     = a.get("descricao", "—")
            motivo   = a.get("motivo", "—")
            resposta = a.get("resposta", "—")[:80]
            linhas += (
                f"<tr><td>{icone}</td><td class='nome-col'>{probe}</td>"
                f"<td>{desc}</td><td>{motivo}</td>"
                f"<td style='color:#64748b;font-size:11px'>{resposta}</td></tr>"
            )
        tabela = f"""
        <table>
          <thead><tr><th></th><th>Probe</th><th>Ataque</th><th>Resultado</th><th>Resposta</th></tr></thead>
          <tbody>{linhas}</tbody>
        </table>""" if linhas else "<p>Sem detalhes.</p>"

        return f"""
        <div class="fw-resumo">
          {_badge_taxa(taxa)}
          <span>{passou}/{total} ataques resistidos</span>
          <span class='cat-tag'>smoke</span>
        </div>
        {tabela}"""

    # CLI completo: tabela por probe
    total  = dados.get("total_tentativas", 0)
    probes = dados.get("probes", {})
    linhas = ""
    for probe, pd in probes.items():
        t     = pd["total"]
        p     = pd["passou"]
        taxa_p = round(p / t * 100, 1) if t else 0
        cor   = "ok" if taxa_p >= 90 else "warn" if taxa_p >= 70 else "fail"
        linhas += (
            f"<tr><td class='nome-col'>{probe}</td><td>{p}/{t}</td>"
            f"<td><span class='badge {cor}'>{taxa_p}%</span></td></tr>"
        )
    tabela = f"""
    <table>
      <thead><tr><th>Probe</th><th>Resistidos</th><th>Taxa</th></tr></thead>
      <tbody>{linhas}</tbody>
    </table>""" if linhas else "<p>Sem detalhes.</p>"

    return f"""
    <div class="fw-resumo">
      {_badge_taxa(taxa)}
      <span>{passou}/{total} ataques resistidos</span>
      <span class='cat-tag'>cli</span>
    </div>
    {tabela}"""


def _gerar_html(consolidado: dict) -> str:
    score = consolidado["score_geral"]
    nivel = score["nivel"]
    score_val = score["score_final"]
    cor = _cor_nivel(nivel)
    gerado_em = consolidado.get("gerado_em", "—")
    webhook = consolidado.get("webhook", "—")
    avisos = score.get("avisos", [])

    avisos_html = ""
    if avisos:
        itens = "".join(f"<li>{a}</li>" for a in avisos)
        avisos_html = f"""
        <section class="section avisos">
          <h2>⚠️ Avisos</h2>
          <ul>{itens}</ul>
        </section>"""

    scores_fw = score.get("scores_por_framework", {})

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HR Buddy — Relatório de Testes</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f1f5f9;
      color: #1e293b;
      font-size: 14px;
      line-height: 1.6;
    }}
    header {{
      background: #0f172a;
      color: #f8fafc;
      padding: 28px 40px;
    }}
    header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
    header p  {{ color: #94a3b8; font-size: 12px; margin-top: 4px; }}
    .container {{ max-width: 960px; margin: 0 auto; padding: 32px 24px; }}

    /* Score principal */
    .score-box {{
      background: #ffffff;
      border: 2px solid {cor};
      border-radius: 12px;
      padding: 28px 32px;
      display: flex;
      align-items: center;
      gap: 24px;
      margin-bottom: 28px;
      box-shadow: 0 1px 4px rgba(0,0,0,.06);
    }}
    .score-num {{
      font-size: 52px;
      font-weight: 800;
      color: {cor};
      line-height: 1;
    }}
    .score-label {{
      font-size: 20px;
      font-weight: 700;
      color: {cor};
    }}
    .score-sub {{ color: #64748b; font-size: 13px; margin-top: 4px; }}

    /* Cards dos frameworks */
    .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px; }}
    @media (max-width: 700px) {{ .cards {{ grid-template-columns: 1fr; }} }}
    .card {{
      background: #ffffff;
      border-radius: 10px;
      border: 1px solid #e2e8f0;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,.05);
    }}
    .card h3 {{ font-size: 14px; font-weight: 700; margin-bottom: 10px; color: #334155; }}
    .card .score-fw {{ font-size: 28px; font-weight: 800; }}

    /* Seções de detalhe */
    .section {{
      background: #ffffff;
      border-radius: 10px;
      border: 1px solid #e2e8f0;
      padding: 24px;
      margin-bottom: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,.05);
    }}
    .section h2 {{ font-size: 16px; font-weight: 700; margin-bottom: 16px; color: #0f172a; }}

    /* Tabelas */
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: #f8fafc; text-align: left; padding: 8px 12px;
          font-weight: 600; color: #475569; border-bottom: 2px solid #e2e8f0; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f8fafc; }}
    .nome-col {{ font-weight: 500; max-width: 280px; word-break: break-word; }}

    /* Badges */
    .badge {{
      display: inline-block; padding: 2px 10px; border-radius: 999px;
      font-size: 12px; font-weight: 700;
    }}
    .badge.ok   {{ background: #dcfce7; color: #15803d; }}
    .badge.warn {{ background: #fef9c3; color: #a16207; }}
    .badge.fail {{ background: #fee2e2; color: #b91c1c; }}
    .badge.sem-dados {{ background: #f1f5f9; color: #94a3b8; }}

    .fw-resumo {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; font-size: 13px; }}

    .metric-tag {{
      display: inline-block; background: #f1f5f9; border-radius: 4px;
      padding: 1px 6px; font-size: 11px; color: #475569; margin: 1px;
    }}
    .cat-tag {{
      display: inline-block; background: #ede9fe; color: #6d28d9;
      border-radius: 4px; padding: 1px 7px; font-size: 12px; font-weight: 600; margin: 2px;
    }}

    .aviso-inline {{ color: #92400e; background: #fef3c7; padding: 10px 14px;
                     border-radius: 6px; font-size: 13px; }}
    .avisos {{ border-left: 4px solid #f59e0b; }}
    .avisos ul {{ padding-left: 20px; color: #78350f; }}

    footer {{ text-align: center; color: #94a3b8; font-size: 11px; padding: 20px; }}
    a {{ color: #3b82f6; }}
  </style>
</head>
<body>

<header>
  <h1>HR Buddy — Relatório de Testes</h1>
  <p>ChocolaTech &nbsp;·&nbsp; Gerado em: {gerado_em} &nbsp;·&nbsp; Webhook: {webhook}</p>
</header>

<div class="container">

  <!-- Score geral -->
  <div class="score-box">
    <div class="score-num">{score_val}%</div>
    <div>
      <div class="score-label">{nivel}</div>
      <div class="score-sub">Score consolidado — DeepEval · Giskard · Garak</div>
    </div>
  </div>

  <!-- Cards por framework -->
  <div class="cards">
    <div class="card">
      <h3>🧪 DeepEval</h3>
      <div class="score-fw" style="color:{_cor_nivel('APROVADO') if (scores_fw.get('deepeval') or 0) >= 90 else _cor_nivel('ATENCAO') if (scores_fw.get('deepeval') or 0) >= 70 else _cor_nivel('REPROVADO')}">
        {scores_fw.get('deepeval', '—')}{'%' if scores_fw.get('deepeval') is not None else ''}
      </div>
      <p style="color:#64748b;font-size:12px;margin-top:6px">Qualidade · Memória · Segurança</p>
    </div>
    <div class="card">
      <h3>🔍 Giskard</h3>
      <div class="score-fw" style="color:{_cor_nivel('APROVADO') if (scores_fw.get('giskard') or 0) >= 90 else _cor_nivel('ATENCAO') if (scores_fw.get('giskard') or 0) >= 70 else _cor_nivel('REPROVADO')}">
        {scores_fw.get('giskard', '—')}{'%' if scores_fw.get('giskard') is not None else ''}
      </div>
      <p style="color:#64748b;font-size:12px;margin-top:6px">Scan · Bias · Robustez</p>
    </div>
    <div class="card">
      <h3>🔴 Garak</h3>
      <div class="score-fw" style="color:{_cor_nivel('APROVADO') if (scores_fw.get('garak') or 0) >= 90 else _cor_nivel('ATENCAO') if (scores_fw.get('garak') or 0) >= 70 else _cor_nivel('REPROVADO')}">
        {scores_fw.get('garak', '—')}{'%' if scores_fw.get('garak') is not None else ''}
      </div>
      <p style="color:#64748b;font-size:12px;margin-top:6px">Red team · Adversarial</p>
    </div>
  </div>

  <!-- Detalhe DeepEval -->
  <section class="section">
    <h2>🧪 DeepEval — Resultados por teste</h2>
    {_secao_deepeval(consolidado["deepeval"])}
  </section>

  <!-- Detalhe Giskard -->
  <section class="section">
    <h2>🔍 Giskard — Scan automático</h2>
    {_secao_giskard(consolidado["giskard"])}
  </section>

  <!-- Detalhe Garak -->
  <section class="section">
    <h2>🔴 Garak — Red team por probe</h2>
    {_secao_garak(consolidado["garak"])}
  </section>

  {avisos_html}

</div>

<footer>
  Gerado por relatorio_consolidado.py · HR Buddy QA Suite · ChocolaTech
</footer>

</body>
</html>"""


# ── Gerador PDF ───────────────────────────────────────────────────────────────

def _gerar_pdf(html_path: Path) -> bool:
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(SAIDA_PDF))
        return True
    except ImportError:
        print("  weasyprint não instalado. Instale com: pip install weasyprint")
        return False
    except Exception as e:
        print(f"  Erro ao gerar PDF: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Relatório consolidado HR Buddy")
    parser.add_argument("--pdf", action="store_true", help="Gera PDF além do HTML")
    args = parser.parse_args()

    RELATORIOS_DIR.mkdir(exist_ok=True)

    print("Coletando resultados...\n")

    deepeval = _ler_deepeval()
    giskard  = _ler_giskard()
    garak    = _ler_garak()
    score    = _calcular_score(deepeval, giskard, garak)

    consolidado = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "webhook": "https://testqa17.app.n8n.cloud/webhook/hr-buddy",
        "score_geral": score,
        "deepeval": deepeval,
        "giskard": giskard,
        "garak": garak
    }

    # JSON
    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(consolidado, f, ensure_ascii=False, indent=2)

    # HTML
    html_str = _gerar_html(consolidado)
    SAIDA_HTML.write_text(html_str, encoding="utf-8")

    # PDF (opcional)
    pdf_ok = False
    if args.pdf:
        pdf_ok = _gerar_pdf(SAIDA_HTML)

    # Resumo terminal
    print("=" * 60)
    print("  RELATORIO CONSOLIDADO — HR BUDDY CHOCOLATECH")
    print("=" * 60)
    print(f"  Score geral : {score['score_final']}%  [{score['nivel']}]")
    print()

    for fw, dados in [("DeepEval", deepeval), ("Giskard", giskard), ("Garak", garak)]:
        status = dados.get("status", "?")
        if status == "ok":
            if fw == "DeepEval":
                info = f"{dados['passou']}/{dados['total']} testes ({dados.get('taxa_aprovacao', '?')}%)"
            elif fw == "Giskard":
                if dados.get("fonte") == "smoke":
                    info = f"{dados['passou']}/{dados['total']} categorias OK ({dados.get('taxa_aprovacao', '?')}%) [smoke]"
                else:
                    info = f"{dados.get('total_issues', 0)} issues ({dados.get('issues_criticos', 0)} críticos)"
            else:
                info = f"{dados['passou']}/{dados.get('total_tentativas', '?')} ataques resistidos ({dados.get('taxa_aprovacao', '?')}%)"
        else:
            info = status
        print(f"  {fw:<10}: {info}")

    print()
    if score["avisos"]:
        print("  Avisos:")
        for a in score["avisos"]:
            print(f"    - {a}")
        print()

    print(f"  JSON  : {SAIDA_JSON}")
    print(f"  HTML  : {SAIDA_HTML}")
    if args.pdf:
        print(f"  PDF   : {SAIDA_PDF}" if pdf_ok else "  PDF   : falhou (ver mensagem acima)")
    print("=" * 60)

    sys.exit(0 if score["nivel"] == "APROVADO" else 1)


if __name__ == "__main__":
    main()
