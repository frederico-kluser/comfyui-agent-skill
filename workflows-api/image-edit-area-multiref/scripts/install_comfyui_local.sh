#!/usr/bin/env bash
# install_comfyui_local.sh — ComfyUI LOCAL para Partner Nodes (API): NENHUM modelo de IA roda aqui.
#
# Reproduz a instalação desta máquina (CachyOS, RTX 4070 Laptop 8 GB, revisada em 2026-10-04):
#   · git clone do ComfyUI em ~/ComfyUI (traz custom_nodes/websocket_image_save.py).
#     Validado em f1072eb0 (0.38.0); COMFY_REF=<commit|tag> fixa uma versão, sem ele segue o master.
#   · venv com Python 3.13 via uv (o 3.14 do sistema ainda é arriscado para as rodas do torch)
#   · torch com CUDA (cu130) quando há GPU NVIDIA — a GPU acelera só os nós de imagem
#     (recorte, máscara, recolagem); sem GPU, torch CPU. Se o torch instalado for da variante
#     errada (ex.: instalação antiga CPU-only), ele é REINSTALADO. ComfyUI/models/ fica sem pesos.
#   · requirements.txt (frontend, workflow templates, embedded docs) + websocket-client
#   · run.sh: carrega secrets.env, recusa porta ocupada, põe --cpu sozinho se não houver GPU/CUDA
#     e sobe em PRIMEIRO PLANO em 127.0.0.1:8188
#   · comando global ~/.local/bin/comfyui → run.sh   (Ctrl+C encerra o servidor)
#   · remove a unidade systemd comfyui.service de instalações antigas (servidor agora é só pelo terminal)
# Idempotente: rodar de novo atualiza o código e as dependências. Não sobe o servidor.
set -euo pipefail
shopt -u patsub_replacement 2>/dev/null || true

ROOT="$(realpath -m "${COMFY_ROOT:-$HOME/ComfyUI}")"
PYVER="${COMFY_PYTHON:-3.13}"
TORCH_INDEX="${COMFY_TORCH_INDEX:-}"   # ex.: https://download.pytorch.org/whl/cu130 (vazio = autodetecta)
BIN_DIR="${COMFY_BIN_DIR:-$HOME/.local/bin}"
COMFY_REF="${COMFY_REF:-}"

command -v git >/dev/null || { echo "git não encontrado" >&2; exit 1; }
command -v uv  >/dev/null || { echo "uv não encontrado (pacman -S uv)" >&2; exit 1; }

if [ -d "$ROOT/.git" ]; then
  if [ -n "$COMFY_REF" ]; then git -C "$ROOT" fetch --quiet origin; else git -C "$ROOT" pull --ff-only; fi
elif [ ! -e "$ROOT" ] || [ -z "$(ls -A "$ROOT")" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git "$ROOT"
else
  echo "$ROOT existe e não é um clone do ComfyUI — abortei para não sobrescrever." >&2; exit 1
fi
[ -z "$COMFY_REF" ] || git -C "$ROOT" checkout --quiet "$COMFY_REF"
echo "ComfyUI em $(git -C "$ROOT" log -1 --format='%h %cs')"

HAS_NVIDIA=0
if command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1; then HAS_NVIDIA=1; fi
if [ -z "$TORCH_INDEX" ]; then
  if [ "$HAS_NVIDIA" = 1 ]; then
    TORCH_INDEX="https://download.pytorch.org/whl/cu130"   # exige driver NVIDIA ≥ 580
  else
    TORCH_INDEX="https://download.pytorch.org/whl/cpu"
  fi
fi
echo "torch de: $TORCH_INDEX"

cd "$ROOT"
[ -x .venv/bin/python ] || uv venv --python "$PYVER" .venv
WANT=cpu; [[ $TORCH_INDEX =~ /cu[0-9]+/?$ ]] && WANT=cuda
HAVE="$(.venv/bin/python -c 'import torch; print("cuda" if torch.version.cuda else "cpu")' 2>/dev/null || echo none)"
REINSTALL=()
if [ "$HAVE" != none ] && [ "$HAVE" != "$WANT" ]; then
  echo "torch instalado é '$HAVE', o desejado é '$WANT' — reinstalando torch/torchvision/torchaudio"
  REINSTALL=(--reinstall-package torch --reinstall-package torchvision --reinstall-package torchaudio)
fi
uv pip install --python .venv/bin/python "${REINSTALL[@]}" torch torchvision torchaudio --index-url "$TORCH_INDEX"
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python websocket-client
CUDA_OK="$(.venv/bin/python -c 'import torch; print(int(torch.cuda.is_available()))')"
echo "torch $(.venv/bin/python -c 'import torch; print(torch.__version__)') · cuda disponível: $CUDA_OK"
if [ "$HAS_NVIDIA" = 1 ] && [ "$WANT" = cuda ] && [ "$CUDA_OK" != 1 ]; then
  echo "AVISO: há GPU NVIDIA mas o torch não enxerga CUDA (driver antigo?). O run.sh vai subir com --cpu." >&2
fi

cat > run.sh <<'RUN'
#!/usr/bin/env bash
# run.sh — sobe o ComfyUI em PRIMEIRO PLANO (Ctrl+C encerra). Chamado pelo comando global `comfyui`.
# A GPU fica disponível para os nós de imagem (recorte, máscara, recolagem), mas NENHUM modelo de IA
# roda aqui: ComfyUI/models/ não tem pesos e toda geração acontece nos Partner Nodes (API, créditos comfy.org).
set -euo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
ROOT="$PWD"
PY="$ROOT/.venv/bin/python"   # caminhos absolutos: o processo aparece como .../ComfyUI/main.py no ps/pkill
if [ ! -x "$PY" ]; then
  echo "comfyui: venv ausente em $ROOT/.venv — rode o install_comfyui_local.sh do bundle image-edit-area-multiref." >&2
  exit 1
fi

# só informação (--help): repassa direto, sem checar porta nem mostrar banner
for a in "$@"; do case "$a" in -h|--help) exec "$PY" "$ROOT/main.py" "$@" ;; esac; done

# Segredos (ex.: FAL_KEY para nós *_fal). Nunca versionar. A COMFY_ORG_API_KEY é lida pelo cliente, não pelo servidor.
if [ -f secrets.env ]; then set -a; . ./secrets.env; set +a; fi
HOST="${COMFY_HOST:-127.0.0.1}"
PORT="${COMFY_PORT:-8188}"
# `comfyui --port N` / `--listen X` também valem (o argparse do main.py usa o último); a checagem e o banner seguem eles
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
  case "${args[i]}" in
    --port) PORT="${args[i + 1]:-$PORT}" ;;
    --port=*) PORT="${args[i]#--port=}" ;;
    --listen)
      nxt="${args[i + 1]:-}"
      if [ -n "$nxt" ] && [ "${nxt#-}" = "$nxt" ]; then HOST="$nxt"; else HOST="0.0.0.0"; fi ;;
    --listen=*) HOST="${args[i]#--listen=}" ;;
  esac
done
CHECK_HOST="${HOST%%,*}"
case "$CHECK_HOST" in 0.0.0.0 | :: | "") CHECK_HOST=127.0.0.1 ;; esac
if (exec 3<>"/dev/tcp/${CHECK_HOST}/${PORT}") 2>/dev/null; then
  echo "comfyui: a porta ${PORT} já está em uso (outro ComfyUI aberto?)." >&2
  echo "         feche-o com Ctrl+C no terminal dele (ou: pkill -f 'ComfyUI/main.py.*--port ${PORT}')," >&2
  echo "         ou use outra porta: COMFY_PORT=$((PORT + 1)) comfyui" >&2
  exit 1
fi

# sem GPU NVIDIA ou com torch sem CUDA, o ComfyUI precisa de --cpu (senão quebra ao iniciar)
DEVICE=GPU
case " $* " in *" --cpu "*) DEVICE=CPU ;; esac
if [ "$DEVICE" = GPU ]; then
  if ! grep -qsE "^cuda(: [^=]+)? = '[0-9]" .venv/lib/python3*/site-packages/torch/version.py ||
     ! command -v nvidia-smi >/dev/null || ! nvidia-smi -L >/dev/null 2>&1; then
    set -- --cpu "$@"
    DEVICE=CPU
  fi
fi
printf '\n  ComfyUI → http://%s:%s    (%s · Ctrl+C encerra o servidor)\n\n' "$CHECK_HOST" "$PORT" "$DEVICE" >&2
exec "$PY" "$ROOT/main.py" --listen "$HOST" --port "$PORT" "$@"
RUN
chmod +x run.sh

if [ ! -f secrets.env ]; then
  ( umask 077; cat > secrets.env <<'SEC'
# ~/ComfyUI/secrets.env — chmod 600, NUNCA commitar.
# Chave da plataforma comfy.org para rodar Partner Nodes por script (POST /prompt
# headless). Gere em https://platform.comfy.org/profile/api-keys e descomente:
# COMFY_ORG_API_KEY=comfyui-xxxxxxxxxxxxxxxx
SEC
  )
fi
chmod 600 secrets.env

mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/comfyui" <<'CMD'
#!/usr/bin/env bash
# comfyui — abre o servidor ComfyUI local em primeiro plano; Ctrl+C encerra.
#   comfyui                      → http://127.0.0.1:8188
#   COMFY_PORT=8189 comfyui      → outra porta (comfyui --port 8189 também funciona)
#   comfyui --help               → opções do main.py do ComfyUI (argumentos extras são repassados)
# Instalado por workflows-api/image-edit-area-multiref/scripts/install_comfyui_local.sh
set -euo pipefail
COMFY_ROOT="${COMFY_ROOT:-$HOME/ComfyUI}"
if [ ! -e "$COMFY_ROOT/run.sh" ]; then
  echo "comfyui: não achei $COMFY_ROOT/run.sh (defina COMFY_ROOT ou rode o install_comfyui_local.sh)" >&2
  exit 1
fi
[ -x "$COMFY_ROOT/run.sh" ] || { echo "comfyui: $COMFY_ROOT/run.sh não é executável (chmod +x)" >&2; exit 1; }
exec "$COMFY_ROOT/run.sh" "$@"
CMD
if [ "$ROOT" != "$HOME/ComfyUI" ]; then
  # raiz fora do padrão: grava o caminho já escapado (espaço, &, | etc. não quebram a linha)
  printf -v QROOT '%q' "$ROOT"
  TMP="$(mktemp)"
  # shellcheck disable=SC2016  # aspas simples de propósito: comparar/gravar o texto literal
  while IFS= read -r line; do
    if [ "$line" = 'COMFY_ROOT="${COMFY_ROOT:-$HOME/ComfyUI}"' ]; then
      printf 'COMFY_ROOT=${COMFY_ROOT:-%s}\n' "$QROOT"
    else
      printf '%s\n' "$line"
    fi
  done < "$BIN_DIR/comfyui" > "$TMP"
  mv "$TMP" "$BIN_DIR/comfyui"
fi
chmod +x "$BIN_DIR/comfyui"

# instalações antigas subiam como serviço systemd; agora o servidor é só pelo terminal
UNIT="$HOME/.config/systemd/user/comfyui.service"
if [ -f "$UNIT" ]; then
  systemctl --user disable --now comfyui.service 2>/dev/null || true
  rm -f "$UNIT"
  systemctl --user daemon-reload 2>/dev/null || true
  echo "removida a unidade systemd antiga: $UNIT"
fi

case ":$PATH:" in *":$BIN_DIR:"*) ;; *) echo "AVISO: $BIN_DIR não está no PATH — adicione-o para usar o comando 'comfyui'." >&2 ;; esac
echo
echo "Pronto. Abra o servidor com:  comfyui      (Ctrl+C encerra)"
