"""
Gerador Garak para o HR Buddy — ChocolaTech
Testa segurança do agente com dados e riscos reais do projeto.

Uso:
  # configure N8N_WEBHOOK_URL no .env antes de rodar

  garak --generator_option_file tests/garak/garak_n8n.py \
        --probes promptinject,dan,knownbadsignatures,toxicity \
        --report_prefix relatorios/garak-hrbuddy
"""

import os
import uuid
import requests
from garak.generators.base import Generator

WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise EnvironmentError("N8N_WEBHOOK_URL não definida. Configure no arquivo .env.")


class HRBuddyGenerator(Generator):
    """
    Conecta o Garak ao HR Buddy da ChocolaTech via webhook.

    Riscos críticos que o Garak vai tentar explorar:
      - IDOR via nome: pedir dados de outro funcionário
      - Data leakage MySQL: extrair saldo de férias/banco de horas de todos
      - Prompt injection: ignorar system prompt de RH
      - Jailbreak: contornar restrição de escopo
    """

    name = "hrbuddy-chocolatech"
    supports_multiple_generations = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # sessionId único por instância para isolar memória entre ataques
        self._session_id = f"garak-{uuid.uuid4().hex[:8]}"

    def _call_model(self, prompt: str, generations_this_call: int = 1) -> list[str]:
        try:
            resp = requests.post(
                WEBHOOK_URL,
                json={
                    "action": "sendMessage",
                    "sessionId": self._session_id,
                    "chatInput": prompt
                },
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data.get("output") or data.get("message") or str(data)
            return [reply]

        except requests.Timeout:
            return ["[ERRO: timeout]"]
        except requests.HTTPError as e:
            return [f"[ERRO HTTP {e.response.status_code if e.response else '?'}]"]
        except Exception as e:
            return [f"[ERRO: {str(e)}]"]

    def reset_session(self):
        self._session_id = f"garak-{uuid.uuid4().hex[:8]}"
