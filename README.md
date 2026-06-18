# HR Buddy QA — ChocolaTech

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![DeepEval](https://img.shields.io/badge/DeepEval-1.4.0+-orange)
![Garak](https://img.shields.io/badge/Garak-red_team-red)
![Giskard](https://img.shields.io/badge/Giskard-risk_scan-green)
![n8n](https://img.shields.io/badge/n8n-workflow-blueviolet)
![License](https://img.shields.io/badge/license-MIT-green)

Suite de testes automatizados para o **HR Buddy**, assistente virtual de RH da ChocolaTech construído no n8n com Cohere, Groq e Railway MySQL.

## Visão geral

O HR Buddy responde dúvidas de RH (férias, banco de horas, benefícios, licenças) identificando o funcionário pelo nome e consultando dados reais do MySQL. Esta suite valida qualidade, segurança e robustez do agente com três frameworks complementares.

| Framework | O que testa | Testes |
|---|---|---|
| **DeepEval** | Memória de sessão, guardrails, qualidade de resposta, segurança | 39 testes |
| **Giskard** | Vulnerabilidades automáticas: IDOR, injection, alucinação, bias | 40 inputs |
| **Garak** | Red team adversarial: DAN, prompt injection, payloads maliciosos | 3 probes |

## Arquitetura do agente

```
Telegram / Webhook
        ↓
Basic LLM Chain (Groq) ← Guardrail: classifica rh_valido / fora_escopo / suspeito
        ↓
Switch (3 rotas)
  ├── rh_valido   → AI Agent (Cohere) → RAG + MySQL → resposta
  ├── fora_escopo → mensagem de escopo
  └── suspeito    → mensagem de recusa
```

## Estrutura

```
├── tests/
│   ├── deepeval/test_hrbuddy_completo.py   # Suite principal (4 categorias)
│   ├── giskard/giskard_n8n.py              # Scan automático completo
│   ├── giskard/giskard_smoke.py            # Smoke — 5 categorias críticas
│   ├── garak/garak_n8n.py                  # Gerador para CLI red team
│   └── garak/garak_smoke.py                # Smoke — 5 ataques adversariais
├── scripts/relatorio_consolidado.py        # Relatório JSON + HTML + PDF
├── workflows/hr-buddy-webhook-guardrail.template.json
├── docs/
│   ├── plano-de-testes.md                  # Plano completo (14 seções)
│   ├── relatorio-execucao.md               # Resultados dos 14 casos executados
│   ├── casos-de-teste/
│   │   ├── CT-MEM.md                       # Memória e isolamento de sessão
│   │   ├── CT-GRD.md                       # Guardrail de classificação
│   │   ├── CT-QUA.md                       # Qualidade RAG e alucinação
│   │   └── CT-SEC.md                       # IDOR, injection, jailbreak
│   ├── evidencias/
│   │   └── BUG-001-IDOR.md                 # IDOR confirmado — output n8n + causa raiz
│   └── Run_Test.md                         # Guia de execução dos testes
├── smoke_all.py                            # Roda os 3 smokes em sequência
├── conftest.py                             # Configura Groq como LLM de avaliação
└── requirements.txt
```

## Pré-requisitos

- Python 3.10+
- Workflow **HR Buddy** ativo no n8n (veja `workflows/`)
- Chave Groq gratuita em [console.groq.com](https://console.groq.com)

## Instalação

```bash
git clone https://github.com/DoglasBSB/llm-qa-hrbuddy.git
cd llm-qa-hrbuddy

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
# edite .env com sua GROQ_API_KEY e N8N_WEBHOOK_URL
```

## Executando os testes

### Smoke tests — verificação rápida (~1 min)

```bash
.venv/bin/python smoke_all.py
```

Roda um teste representativo de cada framework em sequência e imprime resultado consolidado.

### Testes individuais

```bash
# DeepEval — smoke (4 testes, um por categoria)
.venv/bin/pytest tests/deepeval/test_hrbuddy_completo.py \
  -k "mem01 or grd05 or qua04 or sec01" -v

# DeepEval — suite completa (39 testes)
.venv/bin/pytest tests/deepeval/test_hrbuddy_completo.py -v

# Giskard smoke
.venv/bin/python tests/giskard/giskard_smoke.py

# Garak smoke
.venv/bin/python tests/garak/garak_smoke.py
```

### Categorias DeepEval

| Classe | Testes | Cobre |
|---|---|---|
| `TestMemoria` | mem01–mem07 | Persistência de sessão, troca de identidade |
| `TestGuardrail` | grd01–grd10 | Classificação rh_valido / fora_escopo / suspeito |
| `TestQualidade` | qua01–qua12 | Políticas de férias, banco de horas, benefícios |
| `TestSeguranca` | sec01–sec10 | IDOR, SQL injection, prompt injection, toxicidade |

## Relatório consolidado

```bash
# HTML + JSON
.venv/bin/python scripts/relatorio_consolidado.py

# Com PDF
.venv/bin/python scripts/relatorio_consolidado.py --pdf
```

Saída em `relatorios/consolidado.html` com score geral e tabela de resultados por framework.

## Workflow n8n

O arquivo `workflows/hr-buddy-webhook-guardrail.template.json` é a versão sanitizada do workflow (IDs de credenciais removidos). Para usar:

1. Importe no n8n
2. Reconecte as credenciais: Cohere, Groq, MySQL, Telegram
3. Ative o workflow
4. Rode os testes apontando para o webhook gerado

## Contexto

Desenvolvido durante a **Imersão Agentes de IA — Alura (2026)**, com camada adicional de testes de IA/LLM aplicada pelo QA após a construção do agente.

Ferramentas de teste:
[Garak](https://github.com/NVIDIA/garak) ·
[DeepEval](https://github.com/confident-ai/deepeval) ·
[Giskard](https://github.com/Giskard-AI/giskard)
