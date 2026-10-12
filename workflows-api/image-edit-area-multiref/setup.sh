#!/usr/bin/env bash
# setup.sh — image-edit-area-multiref
#
# Editar SÓ uma área da foto com até 10 referências, 100% por API (Nano Banana 2,
# créditos comfy.org). Nenhum modelo de IA roda localmente.
#
# Diferente dos outros bundles-API, este precisa de UM custom node — o
# ComfyUI-Inpaint-CropAndStitch (só recorte/recolagem de pixels, sem IA). O script:
#   1. confere o servidor;
#   2. instala o custom node se faltar (git clone fixado, sem requirements) e pede restart;
#   3. confere no /object_info que TODOS os nós do grafo estão carregados;
#   4. deixa o .json visível no painel Workflows (symlink para workflows-api/);
#   5. diz se a chave para uso por script (COMFY_ORG_API_KEY) existe — sem mostrá-la.
# Não grava segredo nenhum.
set -euo pipefail

COMFY_HOST="${COMFY_HOST:-127.0.0.1}"
COMFY_PORT="${COMFY_PORT:-8188}"
COMFY_URL="http://${COMFY_HOST}:${COMFY_PORT}"
# como abrir o servidor nesta mesma porta (o comando global `comfyui` lê COMFY_HOST/COMFY_PORT)
START_CMD="comfyui"
[ "$COMFY_PORT" = 8188 ] || START_CMD="COMFY_PORT=${COMFY_PORT} comfyui"
[ "$COMFY_HOST" = 127.0.0.1 ] || START_CMD="COMFY_HOST=${COMFY_HOST} ${START_CMD}"
COMFY_ROOT="${COMFY_ROOT:-$HOME/ComfyUI}"
WF_DIR="${COMFY_ROOT}/user/default/workflows"
CROPSTITCH_REPO="https://github.com/lquesada/ComfyUI-Inpaint-CropAndStitch.git"
CROPSTITCH_REF="${CROPSTITCH_REF:-8584b08}"   # versão validada (2026-09-23, schema de 24 widgets)

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE="$(basename "$HERE")"
REQUIRED_NODES=(LoadImage GeminiNanoBanana2V2 InpaintCropImproved InpaintStitchImproved
  PrimitiveStringMultiline StringConcatenate ThresholdMask GetImageSize EmptyImage ImageBlend
  ImageCompositeMasked GrowMask MaskComposite PreviewImage SaveImage SaveImageWebsocket)

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32mok\033[0m   %s\n' "$*"; }
warn() { printf '  \033[33mAVISO\033[0m %s\n' "$*"; }
die()  { printf '  \033[31mERRO\033[0m %s\n' "$*" >&2; exit 1; }

say "1/5 · servidor ComfyUI em ${COMFY_URL}"
command -v curl >/dev/null || die "curl não encontrado."
if ! curl -fsS -m 5 "${COMFY_URL}/system_stats" -o /dev/null; then
  die "ComfyUI não respondeu em ${COMFY_URL}. Abra outro terminal e rode: ${START_CMD}   (Ctrl+C encerra)"
fi
ok "servidor no ar"

say "2/5 · custom node ComfyUI-Inpaint-CropAndStitch (recorte/recolagem, sem IA)"
CN_DIR="${COMFY_ROOT}/custom_nodes/ComfyUI-Inpaint-CropAndStitch"
NEED_RESTART=0
if [ -d "$CN_DIR" ]; then
  HEAD_REF="$(git -C "$CN_DIR" rev-parse --short=7 HEAD 2>/dev/null || echo '?')"
  if [ "$HEAD_REF" = "${CROPSTITCH_REF:0:7}" ]; then
    ok "já instalado em ${CN_DIR/#$HOME/\~} (${HEAD_REF})"
  else
    warn "instalado em ${CN_DIR/#$HOME/\~}, mas na versão ${HEAD_REF} (validada: ${CROPSTITCH_REF})."
    warn "se o nó mudar de widgets, o .json desalinha. Para fixar: git -C '$CN_DIR' fetch && git -C '$CN_DIR' checkout ${CROPSTITCH_REF}"
  fi
else
  command -v git >/dev/null || die "git não encontrado."
  git clone --quiet "$CROPSTITCH_REPO" "$CN_DIR"
  git -C "$CN_DIR" checkout --quiet "$CROPSTITCH_REF" || { rm -rf "$CN_DIR"; die "checkout de ${CROPSTITCH_REF} falhou (removi o clone parcial)"; }
  ok "instalado (${CROPSTITCH_REF}) — não tem requirements"
  NEED_RESTART=1
fi
if [ "$NEED_RESTART" = 1 ]; then
  warn "reinicie o ComfyUI para carregar o nó novo e rode este script de novo:"
  printf '        no terminal do servidor: Ctrl+C e depois  %s\n' "$START_CMD"
  exit 0
fi

say "3/5 · os nós deste workflow estão carregados?"
OBJ="$(mktemp)"; trap 'rm -f "$OBJ"' EXIT
curl -fsS -m 120 "${COMFY_URL}/object_info" -o "$OBJ" || die "falha ao ler /object_info"
MISSING=()
for n in "${REQUIRED_NODES[@]}"; do
  # python_module não-nulo = carregado de verdade (o /object_info devolve 200 com corpo
  # vazio para nós que o Manager conhece mas não estão instalados)
  if python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if (d.get(sys.argv[2]) or {}).get("python_module") else 1)' "$OBJ" "$n"; then
    ok "$n"; else MISSING+=("$n"); fi
done
if [ ${#MISSING[@]} -gt 0 ]; then
  die "nós ausentes: ${MISSING[*]}
  · GeminiNanoBanana2V2 e os demais core vêm do ComfyUI ≥ 0.38: cd '${COMFY_ROOT}' && git pull &&
    uv pip install --python .venv/bin/python -r requirements.txt   (depois: Ctrl+C no servidor e ${START_CMD})
    ou rode de novo scripts/install_comfyui_local.sh deste bundle
  · SaveImageWebsocket vem de custom_nodes/websocket_image_save.py (já incluído no git clone)
  · Inpaint* vêm do passo 2 (reinicie depois de instalar)"
fi

say "4/5 · workflow visível no painel"
BUNDLES_DIR="$(dirname "$HERE")"           # .../workflows-api
mkdir -p "$WF_DIR"
# -L: seguir symlinks (sem isso o find não entra em workflows/api quando ele aponta
# para o repo, e o script acabaria copiando o .json para dentro do próprio repo).
FOUND="$(find -L "$WF_DIR" -path "*/${BUNDLE}/*.json" 2>/dev/null | head -1 || true)"
if [ -n "$FOUND" ]; then
  ok "já aparece em: ${FOUND/#$HOME/\~}"
elif [ ! -e "${WF_DIR}/api" ]; then
  ln -s "$BUNDLES_DIR" "${WF_DIR}/api"
  ok "symlink criado: ${WF_DIR/#$HOME/\~}/api -> ${BUNDLES_DIR/#$HOME/\~}"
else
  warn "${WF_DIR}/api existe mas não contém ${BUNDLE}/. Aponte-o para o repo:"
  printf '        rm -rf "%s/api" && ln -s "%s" "%s/api"\n' "$WF_DIR" "$BUNDLES_DIR" "$WF_DIR"
fi

say "5/5 · uso por script (opcional)"
PY="${COMFY_ROOT}/.venv/bin/python"
if [ -x "$PY" ] && "$PY" -c "import websocket" 2>/dev/null; then
  ok "websocket-client presente no Python do ComfyUI"
else
  warn "falta websocket-client para o cliente: uv pip install --python ${PY} websocket-client"
fi
if [ -n "${COMFY_ORG_API_KEY:-}" ] || grep -qs '^[[:space:]]*\(export[[:space:]]\+\)\?COMFY_ORG_API_KEY=.\+' "${COMFY_ROOT}/secrets.env"; then
  ok "COMFY_ORG_API_KEY configurada (valor não exibido)"
else
  warn "sem COMFY_ORG_API_KEY: a INTERFACE funciona com login; o SCRIPT headless precisa da chave."
  warn "gere em https://platform.comfy.org/profile/api-keys e grave em ${COMFY_ROOT}/secrets.env (chmod 600)"
fi

SERVER_ARG=""
[ "${COMFY_HOST}:${COMFY_PORT}" = "127.0.0.1:8188" ] || SERVER_ARG=" --server ${COMFY_HOST}:${COMFY_PORT}"

cat <<EOF

  Pronto. Falta o que este script não pode fazer por você:

    1. Na interface (${COMFY_URL}): Settings → User → Sign in (conta platform.comfy.org) + créditos.
    2. Painel Workflows → api/${BUNDLE}/${BUNDLE}.json → leia o nó "📖 LEIA PRIMEIRO".
    3. Teste o encanamento sem gastar crédito:
         ${PY} ${HERE}/scripts/comfy_client.py --base FOTO --mask MASCARA --simular${SERVER_ARG}

EOF
