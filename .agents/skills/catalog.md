# Catálogo de Skills — ComfyUI Commercials (RunPod)

> Índice operacional das skills deste repo (estilo llms.txt). O `project-router` e o
> `AGENTS.md` leem isto para despachar tarefas. O procedimento detalhado fica em cada
> `SKILL.md` (nível 2) e nos docs em `docs/` (nível 3, sob demanda).
> Fonte única: `.agents/skills/` (symlink: `.claude/skills/`).
> Gerado/curado a partir de `docs/` por `huu_audit-and-improve-skills`.
>
> **NOTA (2026-09-27 — consolidação CoALA):** as skills de conhecimento (`knowledge-*`)
> foram **migradas para a memória CoALA local e deletadas** — o conhecimento vive APENAS no
> CoALA. Nas tabelas abaixo, `knowledge-*` designa a **chave CoALA** `knowledge/<skill>`
> (não uma skill). Consultar via `coala.py search "<termos>" --tags <skill>` ou
> `coala.py recall "<tarefa>"` (motor: `.agents/comfyui-agent-skill-coala-memory-agent-skill/`).
> O `provisioning.sh` (antes em `knowledge-runpod-provisioning/scripts/`) passou para
> `task-launch-runpod-pod/scripts/`.

## Roteador (sempre primeiro)
- **[project-router](project-router/SKILL.md)** — despacha TODA tarefa para a cadeia de skills certa antes de implementar.

## Conhecimento (memória semântica — CoALA, sem skills)
| Chave CoALA | O que injeta | Fonte |
|---|---|---|
| `knowledge/knowledge-scail2` | SCAIL-2: paths de modelo, VRAM/quant, máscara, sampler, gotchas | `docs/SCAIL-2.md` |
| `knowledge/knowledge-comfyui-workflows` | grafo, JSON UI/API, cadeia WanVideoWrapper, low-VRAM, Context Windows | `docs/workflow-guide.md` |
| `knowledge/knowledge-runpod-infra` | tiers de GPU + preço, Pods/Serverless, Network Volume, custo | `docs/runpod-guide.md` |
| `knowledge/knowledge-runpod-provisioning` | `provisioning.sh` (em `task-launch-runpod-pod/scripts/`), manifesto de modelos, custom nodes, caveats | `docs/config-runpod.md` |
| `knowledge/knowledge-image-editing` | inpaint, edição por instrução (Kontext/Qwen), composição, modelos, otimização | `docs/image-editing.md` |
| `knowledge/knowledge-image-masking` | seleção/segmentação: MaskEditor, SAM2/3, Florence-2, Grounding DINO, Impact Pack | `docs/image-editing.md` |
| `knowledge/knowledge-comfyui-api` | API HTTP (/prompt,/upload,/history,/view) + composição Python (Pillow/NumPy/OpenCV) | `docs/image-editing.md` |
| `knowledge/knowledge-image-enhance` | upscale, outpaint, relight (IC-Light), ControlNet, IPAdapter, remoção de fundo | `docs/image-editing.md` |
| `knowledge/knowledge-scail2-native` | grafo NATIVO do SCAIL-2 (WanSCAILToVideo, SCAIL2ColoredMask, SAM3 por texto, toggle Replace, shift 5) | (bundle removido em 2026-08-03; ver git) |
| `knowledge/knowledge-comfyui-api-nodes` | nós de API ONLINE: partner (Comfy credits) vs fal (`*_fal`) vs Replicate; catálogo Veo/Kling/Nano Banana/Seedance/Flux Pro; **seed gates**; chaves; decisão API-vs-self-hosted | `workflows-api/` (+ pesquisa cloud-first) |

## Tarefa (memória procedural)
| Skill | O que faz |
|---|---|
| [task-create-commercial](task-create-commercial/SKILL.md) | pipeline end-to-end de um comercial **self-hosted** (Flux→SCAIL-2/Wan→RIFE→upscale→edição) |
| [task-create-commercial-api](task-create-commercial-api/SKILL.md) | pipeline de comercial 100% **por API** (Nano Banana Pro→Veo 3.1→extend→ColorMatch→ffmpeg), sem GPU |
| [task-launch-runpod-pod](task-launch-runpod-pod/SKILL.md) | subir um pod ComfyUI pronto para gerar |
| [task-build-workflow](task-build-workflow/SKILL.md) | montar/adaptar um workflow de vídeo |
| [task-debug-generation](task-debug-generation/SKILL.md) | diagnosticar falhas (OOM, vídeo preto, nós vermelhos) |
| [task-package-workflow-project](task-package-workflow-project/SKILL.md) | empacotar um workflow entregável em `workflows-cloud/` (GPU) ou `workflows-api/` (API) — json + README + setup.sh |
| [task-edit-image](task-edit-image/SKILL.md) | editar uma imagem fim-a-fim (selecionar → editar → recolar) |

## Meta (auto-evolução)
| Skill | O que faz |
|---|---|

## Cadeias típicas (para o router)
Notação: `task-*` = skill viva; `CoALA knowledge-*` = registo na memória CoALA local (chave `knowledge/<skill>`).

| Pedido do usuário | Cadeia de skills |
|---|---|
| "criar/produzir um comercial" | `task-create-commercial` → CoALA `knowledge-scail2` + `knowledge-comfyui-workflows` (+ `task-launch-runpod-pod`) |
| "qual GPU / quanto custa / Pod ou Serverless" | CoALA `knowledge-runpod-infra` |
| "subir o pod / baixar os modelos / configurar" | `task-launch-runpod-pod` → CoALA `knowledge-runpod-provisioning` + `knowledge-runpod-infra` |
| "montar/adaptar um workflow" | `task-build-workflow` → CoALA `knowledge-comfyui-workflows` (+ `knowledge-scail2`) |
| "deu OOM / vídeo preto / nó vermelho / não gera" | `task-debug-generation` → CoALA `knowledge-comfyui-workflows` |
| "animar personagem com SCAIL-2" | CoALA `knowledge-scail2` + `knowledge-comfyui-workflows` |
| "criar um workflow para X / empacotar workflow" | `task-package-workflow-project` → `task-build-workflow` + conhecimento da técnica (CoALA) |
| "editar/retocar imagem, trocar objeto/cor/fundo" | `task-edit-image` → CoALA `knowledge-image-editing` + `knowledge-image-masking` |
| "editar por instrução (sem máscara)" | CoALA `knowledge-image-editing` (projetos `instruction-edit-kontext` / `qwen-image-edit`) |
| "automatizar por API / recolar via código" | CoALA `knowledge-comfyui-api` |
| "criar comercial SEM GPU / por API / Veo-Kling-Seedance" | `task-create-commercial-api` → CoALA `knowledge-comfyui-api-nodes` (bundle removido em 2026-08-03; ver git) |
| "rodar workflow por API / qual provedor / custo em créditos / fal vs Comfy / nó fal travou" | CoALA `knowledge-comfyui-api-nodes` |
| "editar foto por API: trocar roupa · objeto · pessoa · local (+ match de luz)" | `task-edit-image` → CoALA `knowledge-comfyui-api-nodes` + `knowledge-image-editing` (bundles `workflows-api/image-edit-nano-banana-2/` · `image-edit-seedream/`) |
| "me colocar numa FOTO no lugar de uma pessoa (mesma roupa/pose, **ou** com a minha)" | CoALA `knowledge-comfyui-api-nodes` (blocos 4 e 5 dos bundles `image-edit-*`) |
| "me colocar num VÍDEO no lugar de uma pessoa (Seedance 2.0)" | CoALA `knowledge-comfyui-api-nodes` (bundle `workflows-api/video-person-swap-seedance-2/`) — ⚠️ humano real exige **asset verificado** |
| "upscale / outpaint / relight / tirar fundo" | CoALA `knowledge-image-enhance` |
| nenhuma skill cobre | memória CoALA local (`coala.py add`) — proposta de skill nova como diff para revisão |
