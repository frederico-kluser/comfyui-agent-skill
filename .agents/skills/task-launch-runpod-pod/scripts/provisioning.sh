#!/usr/bin/env bash
# provisioning.sh — RunPod / AI-Dock ComfyUI
# SCAIL-2 + Wan 2.1/2.2 14B + Flux — setup rápido (junho 2026)
# Uso: defina a env PROVISIONING_SCRIPT apontando p/ a raw URL deste arquivo,
#      OU rode manualmente:  bash provisioning.sh
# Fonte/curadoria: docs/config-runpod.md. Edite os arrays NODES/MODELS/WORKFLOWS abaixo.
set -Euo pipefail

# ============ CONFIG ============
# Detecta o ComfyUI (network volume tem prioridade)
if   [ -d "${WORKSPACE:-/workspace}/ComfyUI" ]; then COMFY="${WORKSPACE:-/workspace}/ComfyUI"
elif [ -d "/opt/ComfyUI" ];                      then COMFY="/opt/ComfyUI"
else COMFY="${WORKSPACE:-/workspace}/ComfyUI"; fi
echo ">> ComfyUI em: $COMFY"

HF_TOKEN="${HF_TOKEN:-}"
CIVITAI_TOKEN="${CIVITAI_TOKEN:-}"
PIP="python -m pip install --no-cache-dir"
PAR=3   # downloads simultâneos

# ---- Custom nodes ----
NODES=(
  "https://github.com/ltdrdata/ComfyUI-Manager"
  "https://github.com/kijai/ComfyUI-WanVideoWrapper"
  "https://github.com/kijai/ComfyUI-KJNodes"
  "https://github.com/kijai/ComfyUI-SCAIL-Pose"
  "https://github.com/city96/ComfyUI-GGUF"
  "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite"
  "https://github.com/rgthree/rgthree-comfy"
  "https://github.com/Fannovel16/ComfyUI-Frame-Interpolation"
  "https://github.com/PozzettiAndrea/ComfyUI-SAM3"
  "https://github.com/cubiq/ComfyUI_essentials"
  "https://github.com/Brobert-in-aus/scail-auto-extend"
)

# ---- Modelos: "URL|subpasta_em_models" ----
MODELS=(
  # SCAIL-2 (escolha fp8 OU gguf; aqui fp8_scaled)
  "https://huggingface.co/Comfy-Org/SCAIL-2/resolve/main/diffusion_models/wan2.1_14B_SCAIL_2_fp8_scaled.safetensors|diffusion_models"
  "https://huggingface.co/Comfy-Org/SCAIL-2/resolve/main/loras/wan2.1_SCAIL_2_DPO_lora_bf16.safetensors|loras"
  # Componentes Wan compartilhados
  "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors|text_encoders"
  "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors|vae"
  "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors|clip_vision"
  # LoRA aceleração (4 passos)
  "https://huggingface.co/lightx2v/Wan2.1-I2V-14B-480P-StepDistill-CfgDistill-Lightx2v/resolve/main/loras/Wan21_I2V_14B_lightx2v_cfg_step_distill_lora_rank64.safetensors|loras"
  # SAM 3.1
  "https://huggingface.co/Comfy-Org/sam3.1/resolve/main/checkpoints/sam3.1_multiplex_fp16.safetensors|sam"
  # Wan 2.2 14B I2V (high + low noise)
  "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors|diffusion_models"
  "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors|diffusion_models"
  # Flux (fp8 all-in-one)
  "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors|checkpoints"
)

# ---- Workflows .json ----
WORKFLOWS=(
  "https://github.com/kijai/ComfyUI-WanVideoWrapper/raw/refs/heads/main/example_workflows/wanvideo_2_1_14B_SCAIL_pose_control_example_01.json"
  "https://github.com/kijai/ComfyUI-SCAIL-Pose/raw/refs/heads/main/example_workflows/SCAIL_preprocess_example_01.json"
  # Adicione AQUI seus próprios workflows (raw URL de um Gist/repo):
  # "https://gist.githubusercontent.com/SEU_USER/SEU_GIST/raw/meu_workflow.json"
)

# ============ FUNÇÕES ============
setup_tools() {
  echo ">> Instalando ferramentas (aria2, git)..."
  if ! command -v aria2c >/dev/null 2>&1; then
    apt-get update -y && apt-get install -y aria2 git git-lfs
  fi
}

update_comfy() {
  # SCAIL-2 exige ComfyUI nightly/master
  if [ -d "$COMFY/.git" ]; then
    echo ">> Atualizando ComfyUI (nightly p/ SCAIL-2)..."
    ( cd "$COMFY" && git pull --ff-only || true )
    [ -f "$COMFY/requirements.txt" ] && $PIP -r "$COMFY/requirements.txt" || true
  fi
}

get_nodes() {
  echo ">> Instalando custom nodes..."
  mkdir -p "$COMFY/custom_nodes"
  for repo in "${NODES[@]}"; do
    dir="${repo##*/}"; path="$COMFY/custom_nodes/$dir"
    if [ ! -d "$path" ]; then
      echo "   clonando $dir"; git clone --recursive "$repo" "$path" || continue
    else
      ( cd "$path" && git pull --ff-only || true )
    fi
    [ -f "$path/requirements.txt" ] && $PIP -r "$path/requirements.txt" || true
    [ -f "$path/install.py" ] && ( cd "$path" && python install.py || true )
  done
}

# Download de 1 modelo (16 conexões, com header de token p/ gated)
dl_one() {
  local url="$1" dest="$COMFY/models/$2"
  mkdir -p "$dest"
  local fname; fname="$(basename "${url%%\?*}")"
  if [ -f "$dest/$fname" ]; then echo "   [skip] $fname já existe"; return 0; fi
  local hdr=()
  if [[ "$url" == *huggingface.co* ]] && [ -n "$HF_TOKEN" ]; then
    hdr=(--header="Authorization: Bearer $HF_TOKEN")
  fi
  if [[ "$url" == *civitai.com* ]] && [ -n "$CIVITAI_TOKEN" ]; then
    url="${url}?token=${CIVITAI_TOKEN}"
  fi
  echo "   baixando $fname -> models/$2"
  aria2c -c -x16 -s16 -k1M --auto-file-renaming=false --allow-overwrite=false \
         --console-log-level=warn --summary-interval=0 \
         "${hdr[@]}" -d "$dest" -o "$fname" "$url" \
    || wget -nc --content-disposition "${hdr[@]/--header=/--header=}" -P "$dest" "$url"
}

get_models() {
  echo ">> Baixando modelos (paralelo: $PAR)..."
  for entry in "${MODELS[@]}"; do
    dl_one "${entry%%|*}" "${entry##*|}" &
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
  done
  wait
  # SAM em sam/ e também checkpoints/ (workflows variam)
  if [ -f "$COMFY/models/sam/sam3.1_multiplex_fp16.safetensors" ]; then
    mkdir -p "$COMFY/models/checkpoints"
    ln -sf "$COMFY/models/sam/sam3.1_multiplex_fp16.safetensors" \
           "$COMFY/models/checkpoints/sam3.1_multiplex_fp16.safetensors" 2>/dev/null || true
  fi
}

get_workflows() {
  echo ">> Baixando workflows .json..."
  local wfdir="$COMFY/user/default/workflows"
  mkdir -p "$wfdir"
  for w in "${WORKFLOWS[@]}"; do
    wget -nc --content-disposition -P "$wfdir" "$w" || \
      curl -fL --remote-name --output-dir "$wfdir" "$w" || true
  done
}

install_perf() {
  echo ">> (Opcional) SageAttention/Triton p/ acelerar inferência..."
  $PIP triton || true
  if command -v nvcc >/dev/null 2>&1; then
    $PIP sageattention==2.2.0 --no-build-isolation \
      || echo "   SageAttention falhou (build) — siga sem ele ou use wheel prebuilt."
  else
    echo "   nvcc ausente: pulei SageAttention. Use imagem CUDA -devel p/ compilar."
  fi
  echo "   Em Wan: use o node KJNodes 'Patch Sage Attention' (sageattn_qk_int8_pv_fp16_cuda),"
  echo "   NÃO o flag global --use-sage-attention."
}

main() {
  setup_tools
  update_comfy
  get_nodes            # leve e rápido primeiro
  get_workflows        # rápido
  get_models           # pesado, em paralelo
  install_perf         # lento, por último e opcional
  echo "============================================"
  echo " Provisionamento COMPLETO. Reinicie o ComfyUI"
  echo " (Manager > Restart) e pressione 'R' p/ recarregar modelos."
  echo "============================================"
}
main
