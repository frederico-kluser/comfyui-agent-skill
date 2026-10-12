# 🧭 Do guia (Flux Fill + Redux LOCAL) para a API

O guia descreve a versão **local** (pesos na GPU). Aqui **nenhum modelo de IA roda localmente** — cada fase do
guia virou o equivalente por API:

| Fase do guia | Versão local (guia) | Neste workflow (API) |
|---|---|---|
| **1. Loaders** | `UNETLoader` flux1-fill-dev · `DualCLIPLoader` t5xxl+clip_l · `VAELoader` ae · `StyleModelLoader` redux · `CLIPVisionLoader` sigclip | **Nenhum loader.** O modelo roda no Google; o acesso é o **login comfy.org**. |
| **2. Estilo múltiplo** | 10× `LoadImage → CLIPVisionEncode → StyleModelApply` em cascata | **③** 10× `LoadImage` direto nos slots `image_3…12`. O "peso" de cada referência é dito **em texto** (② PAPEL). |
| **3. Máscara** | alfa/`ImageToMask` → dilatar/feather → `InpaintModelConditioning` | **① MaskEditor** → **④ ✂️ Inpaint Crop** (`mask_expand_pixels` + `mask_blend_pixels` = dilatar + feather) + **mapa magenta** |
| **4. Inferência** | `KSampler` euler/simple, cfg ≈ 1 | **⑤ Nano Banana 2** — resolução, `thinking_level`, seed |
| **5. Extração** | `VAEDecode → SaveImageWebsocket` | **⑥ ✂️ Inpaint Stitch → SaveImage** (na tela) · `SaveImageWebsocket` (no script) |

## ✅ O que o guia acerta (conferido no código do ComfyUI 0.38)
- `POST /prompt` devolve só o `prompt_id`; o resultado vem depois (WebSocket ou `/history`).
- `executing` com `node: null` = **fim** do prompt — vale para sucesso **e** erro (veja `execution_error`).
- Frame binário = **8 bytes** de cabeçalho (4 tipo de evento + 4 formato: 1=JPEG, 2=PNG) → `bytes[8:]`.
- `/upload/mask` usa `original_ref` e grava a original com o alfa da máscara.

## ⚠️ O que o guia erra ou omite
- **Máscara + 10 referências numa chamada não existe por API.** GPT Image aceita máscara só com **1**
  imagem; Flux Fill/Erase só 1 imagem; Nano Banana (14), Seedream (10/14), Flux 3 (10) **não têm máscara**.
  → recorte + mapa + recolagem.
- **Redux:** os templates oficiais encadeiam `StyleModelApply` com **strength 1.0** (o 0,1–0,3 do guia é
  heurística: não achamos fonte oficial). O Flux Fill oficial usa **FluxGuidance 30** + `KSampler cfg 1` — o guia omite o 30.
- **`SaveImageWebsocket` não é nó core:** é um exemplo em `custom_nodes/websocket_image_save.py`, que
  já vem no `git clone` e carrega por padrão.
- **`/upload/mask` lê o canal ALFA**, não tons de cinza: transparente = área a editar.
- **Deduplicação no upload é condicional:** só quando já existe arquivo com o **mesmo nome** e o hash
  bate; mesmo nome com conteúdo diferente vira `nome (1).png`.
- **Abrir o WS antes do `/prompt`** evita perder eventos (o servidor não reenvia), mas o `/history`
  ainda entrega o resultado — não é "perda irreversível".
- **VRAM, FP8, GGUF, TensorRT, `/free`**: irrelevantes aqui — não há modelo local para descarregar.
