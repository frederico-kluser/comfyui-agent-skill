---
name: task-launch-runpod-pod
description: >-
  Procedimento para subir um pod ComfyUI no RunPod pronto para gerar: criar Network Volume, escolher template
  (Blackwell p/ RTX 5090) e GPU, configurar portas/env/tokens, rodar o provisioning, conectar na porta 8188 e
  parar o pod ao terminar. Use ao "subir/criar/ligar o pod", "configurar o RunPod", "começar a gerar na nuvem",
  "preparar a máquina" — mesmo sem citar a skill. Apoia-se nos registos CoALA knowledge-runpod-infra e knowledge-runpod-provisioning.
metadata:
  version: 0.1.0
  type: task
---
# Tarefa — Subir um Pod ComfyUI no RunPod

Sequência repetível para sair do zero a um ComfyUI gerando. O conhecimento de GPU/custo e de modelos/script
vive na memória CoALA local — recupere os registos nos passos indicados (`coala.py search --tags <skill>`).

## Quando usar
"Subir/criar/ligar o pod", "configurar o RunPod", "começar a gerar na nuvem", "preparar a máquina".

## Procedimento
1. **Conta + crédito**: runpod.io, adicione crédito (mín. US$10).
2. **Network Volume primeiro** (Storage → New Network Volume): escolha a **região** da GPU-alvo; 150–200GB p/
   vídeo. Só existe na **Secure Cloud**. (→ CoALA `knowledge-runpod-infra`.)
3. **Escolha a GPU** (→ CoALA `knowledge-runpod-infra`): 480p → RTX 5090; 720p → A100 80GB. Filtre **CUDA 12.8** p/ Blackwell.
4. **Template**: ComfyUI oficial (4090/L40/A100) ou **ComfyUI Blackwell Edition** (5090/B200) ou AI-Dock (p/ usar `PROVISIONING_SCRIPT`).
5. **Configure** (Deploy): Container Disk ≥30GB, Volume mount em `/workspace`, portas **8188** (ComfyUI), 8888
   (Jupyter), 8080 (FileBrowser). Env: `HF_TOKEN`, `CIVITAI_TOKEN`, `COMFYUI_ARGS=--fast`, e — se AI-Dock —
   `PROVISIONING_SCRIPT=<raw_url do provisioning.sh>`. **Nunca** salve template público com tokens.
6. **Deploy On-Demand** (ou Spot p/ jobs toleráveis a interrupção). 1ª inicialização: segundos a ~30min.
7. **Provisione** (se não usou `PROVISIONING_SCRIPT`): web terminal → rode o `provisioning.sh`
   (script nesta skill: `scripts/provisioning.sh`; conhecimento → CoALA `knowledge-runpod-provisioning`).
8. **Conecte**: Connect → "HTTP Service [Port 8188]". Aguarde "All startup tasks have been completed" / a porta
   8188 ficar verde ("Bad Gateway" do Cloudflare some em ~60s).
9. **Pare ao terminar**: **Stop** (desliga a GPU; Volume Disk parado cobra em dobro) ou **Terminate** (apaga o
   efêmero — o Network Volume persiste). Salve workflows/saídas no Network Volume.

## Gotchas
- "Zero GPUs on restart" → GPU esgotada na região; tente outra (modelos no Network Volume recriam rápido).
- Volume e pod precisam estar na **mesma região** (cross-region falha/latência 200ms+).
- FileBrowser (8080) login `admin/adminadmin12` — troque.
- `nvidia-smi` no terminal p/ checar VRAM; GPU em ~0% e geração 10min+ = caiu p/ CPU (reduza quant ou `--lowvram`).

## Referências
- CoALA `knowledge-runpod-infra` (GPU/custo/Network Volume), `knowledge-runpod-provisioning` (script/modelos; script físico em `scripts/provisioning.sh` desta skill).
- `docs/runpod-guide.md`, `docs/config-runpod.md`.

## registo de aprendizado (memória CoALA local)
1. O pod subiu e gerou? Só então persista.
2. Persista: região/GPU com boa disponibilidade, tempo real de boot, ajuste de env que funcionou, erro novo. Ignore o óbvio.
3. Registe na memória CoALA local (`coala.py add --type episodic`, com data/fonte). Destile no corpo se estável (`version++`). Nova área → a memória CoALA local (`coala.py add`).
4. Diff git para revisão humana.
