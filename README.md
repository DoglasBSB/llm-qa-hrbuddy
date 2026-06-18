# HR Buddy QA — ChocolaTech

Suite de testes automatizados para o **HR Buddy**, assistente virtual de RH da ChocolaTech construído no n8n com Cohere, Groq e Railway MySQL.

## Visão geral

O HR Buddy responde dúvidas de RH (férias, banco de horas, benefícios, licenças) identificando o funcionário pelo nome e consultando dados reais do MySQL. Esta suite valida qualidade, segurança e robustez do agente com três frameworks complementares.

| Framework | O que testa | Testes |
|---|---|---|
| **DeepEval** | Memória de sessão, guardrails, qualidade de resposta, segurança | 39 testes |
| **Giskard** | Vulnerabilidades automáticas: IDOR, injection, alucinação, bias | 40 inputs |
| **Garak** | Red team adversarial: DAN, prompt injection, payloads maliciosos | 3 probes |

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
│   ├── Run_Test.md                         # Guia completo de execução
│   ├── plano-de-testes.md
│   └── contrato-dados-mysql.md
├── smoke_all.py                            # Roda os 3 smokes em sequência
├── conftest.py                             # Configura Groq como LLM de avaliação
└── requirements.txt
```

## Pré-requisitos

- Python 3.10+
- Workflow **HR Buddy** ativo no n8n
- Chave Groq (usada como LLM de avaliação pelo DeepEval)

## Instalação

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Crie o arquivo `.env` na raiz:

```env
GROQ_API_KEY=gsk_...
# N8N_WEBHOOK_URL=https://...  # opcional, tem default no código
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

## Licença

MIT — veja [LICENSE](LICENSE).
