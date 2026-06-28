#!/usr/bin/env bash
# Executa smoke_all.py --all e salva evidência (log + vídeo opcional).
# Uso: ./scripts/gravar_evidencia.sh [--gravar]
#   --gravar   grava a tela com ffmpeg (requer display ativo)

set -euo pipefail

# ── Cores ─────────────────────────────────────────────────────────────────────
RESET="\033[0m"
BOLD="\033[1m"
VERDE="\033[1;32m"
VERMELHO="\033[1;31m"
AMARELO="\033[1;33m"
AZUL="\033[1;34m"
CIANO="\033[1;36m"
CINZA="\033[0;37m"

# ── Flags ─────────────────────────────────────────────────────────────────────
GRAVAR=false
for arg in "$@"; do
  [[ "$arg" == "--gravar" ]] && GRAVAR=true
done

# ── Caminhos ──────────────────────────────────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCIA_DIR="$ROOT_DIR/relatorios/evidencias"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$EVIDENCIA_DIR/sessao_${TIMESTAMP}.log"
VIDEO_FILE="$EVIDENCIA_DIR/video_${TIMESTAMP}.mp4"
PYTHON="$ROOT_DIR/.venv/bin/python"

mkdir -p "$EVIDENCIA_DIR"

# ── Helpers ───────────────────────────────────────────────────────────────────
separador() { echo -e "${CINZA}──────────────────────────────────────────────────────────${RESET}"; }

ok()   { echo -e "${VERDE}${BOLD}  ✔ $*${RESET}"; }
warn() { echo -e "${AMARELO}${BOLD}  ⚠ $*${RESET}"; }
erro() { echo -e "${VERMELHO}${BOLD}  ✘ $*${RESET}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
clear
echo -e "${BOLD}${AZUL}"
echo "  ██╗  ██╗██████╗      ██████╗ ██╗   ██╗██████╗ ██████╗ ██╗   ██╗"
echo "  ██║  ██║██╔══██╗     ██╔══██╗██║   ██║██╔══██╗██╔══██╗╚██╗ ██╔╝"
echo "  ███████║██████╔╝     ██████╔╝██║   ██║██║  ██║██║  ██║ ╚████╔╝ "
echo "  ██╔══██║██╔══██╗     ██╔══██╗██║   ██║██║  ██║██║  ██║  ╚██╔╝  "
echo "  ██║  ██║██║  ██║     ██████╔╝╚██████╔╝██████╔╝██████╔╝   ██║   "
echo "  ╚═╝  ╚═╝╚═╝  ╚═╝     ╚═════╝  ╚═════╝ ╚═════╝ ╚═════╝   ╚═╝   "
echo -e "${RESET}"
echo -e "${BOLD}  Smoke Tests — HR Buddy ChocolaTech                     $(date '+%d/%m/%Y %H:%M')${RESET}"
echo -e "${CINZA}  Log: $LOG_FILE${RESET}"
separador

# ── Carrega .env ──────────────────────────────────────────────────────────────
[[ -f "$ROOT_DIR/.env" ]] && set -a && source "$ROOT_DIR/.env" && set +a

# ── Pré-requisitos ────────────────────────────────────────────────────────────
echo ""
if [[ ! -x "$PYTHON" ]]; then
  erro "Virtualenv não encontrado em .venv/bin/python"
  erro "Crie com: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
ok "Python   → $("$PYTHON" --version)"

if [[ -z "${N8N_WEBHOOK_URL:-}" ]]; then
  erro "N8N_WEBHOOK_URL não definida — configure no .env"
  exit 1
fi
ok "Webhook  → ${N8N_WEBHOOK_URL:0:45}..."

if [[ -z "${GROQ_API_KEY:-}" ]]; then
  warn "GROQ_API_KEY não definida — juiz LLM desativado"
else
  ok "Groq     → ${GROQ_API_KEY:0:12}..."
fi
separador

# ── Gravação de tela (opcional) ───────────────────────────────────────────────
FFMPEG_PID=""

parar_gravacao() {
  if [[ -n "$FFMPEG_PID" ]]; then
    kill -SIGINT "$FFMPEG_PID" 2>/dev/null
    wait "$FFMPEG_PID" 2>/dev/null || true
    FFMPEG_PID=""
  fi
}

trap parar_gravacao EXIT INT TERM

if [[ "$GRAVAR" == true ]]; then
  if ! command -v ffmpeg &>/dev/null; then
    warn "ffmpeg não encontrado — gravação de tela desativada"
    GRAVAR=false
  else
    DISPLAY_RES=$(xdpyinfo 2>/dev/null | awk '/dimensions/{print $2}' || echo "1920x1080")
    ffmpeg -y \
      -video_size "$DISPLAY_RES" -framerate 30 \
      -f x11grab -i "${DISPLAY:-:0}.0" \
      -c:v libx264 -preset fast -crf 20 \
      "$VIDEO_FILE" \
      >/dev/null 2>&1 &
    FFMPEG_PID=$!
    ok "Gravando → $VIDEO_FILE"
    separador
  fi
fi

# ── Execução ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${CIANO}${BOLD}▶ Iniciando smoke_all.py --all${RESET}"
echo -e "${CINZA}  $(date '+%H:%M:%S')${RESET}\n"

cd "$ROOT_DIR"
"$PYTHON" smoke_all.py --all 2>&1 \
  | sed -u "s|${N8N_WEBHOOK_URL}|https://***.***.n8n.cloud/webhook/hr-buddy|g" \
  | tee -a "$LOG_FILE" || true
EXIT_CODE=${PIPESTATUS[0]}

# ── Evidências geradas ────────────────────────────────────────────────────────
separador
echo ""
echo -e "${BOLD}  Evidências salvas em: relatorios/evidencias/${RESET}"
echo -e "${CINZA}  $(basename "$LOG_FILE")${RESET}"
[[ "$GRAVAR" == true && -f "$VIDEO_FILE" ]] && \
  echo -e "${CINZA}  $(basename "$VIDEO_FILE")${RESET}"
echo ""

[[ "$EXIT_CODE" -eq 0 ]] \
  && echo -e "${VERDE}${BOLD}  Todos os smokes passaram — evidência pronta!${RESET}\n" \
  || echo -e "${AMARELO}${BOLD}  Falhas detectadas — revise antes de publicar.${RESET}\n"

exit "$EXIT_CODE"
