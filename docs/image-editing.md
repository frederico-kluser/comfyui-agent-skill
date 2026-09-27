# O Tutorial Definitivo de Edição de Imagens no ComfyUI (Junho/2026)

> Relatório de pesquisa (fonte). O conhecimento destilado vive na memória CoALA local (chaves
> `knowledge/knowledge-image-editing`, `knowledge/knowledge-image-masking`,
> `knowledge/knowledge-comfyui-api`, `knowledge/knowledge-image-enhance` — skills deletadas em 2026-09-27).
> Edite conhecimento via `coala.py add` (supersessão por `--key`), não duplique.

## TL;DR
- **Para selecionar APENAS uma parte da imagem**, três caminhos: máscara manual (MaskEditor nativo — clique direito > "Open in MaskEditor"), seleção semântica por texto (Florence-2 / Grounding DINO + SAM2/SAM3) e detecção automática (Impact Pack: UltralyticsDetector + SAMDetector). Para EDITAR só essa parte, use inpainting com `InpaintModelConditioning` + KSampler com denoise parcial, idealmente com um modelo dedicado (Flux Fill) ou edição por instrução (Flux Kontext / Qwen-Image-Edit).
- **Para fazer o "replace" da região editada de volta na original VIA CÓDIGO**, o padrão de ouro é o par de nós `Inpaint Crop` + `Inpaint Stitch` (lquesada) dentro do ComfyUI; e fora dele, em Python: `Image.paste(edited,(0,0),mask)` com máscara borrada (Pillow), blend NumPy `orig*(1-m)+edited*m`, ou `cv2.seamlessClone` para blending Poisson. A automação completa é feita via API HTTP do ComfyUI (`/prompt`, `/upload/image`, `/history`, `/view`).
- **Melhores modelos open-source em meados de 2026**: Flux.1 Fill (inpaint/outpaint), Flux Kontext Dev e Qwen-Image-Edit 2511 (edição por instrução), Flux.2 [dev] (qualidade máxima), Z-Image Turbo (velocidade) e SDXL (ecossistema). Otimize com fp8/GGUF, SageAttention e `--fast`.

---

## Key Findings

1. **Inpainting moderno no ComfyUI separa-se em duas filosofias**: (a) inpainting "clássico" baseado em máscara + denoise (Set Latent Noise Mask, VAE Encode for Inpainting, InpaintModelConditioning) e (b) edição por instrução textual (Flux Kontext, Qwen-Image-Edit) que dispensa máscara para muitas tarefas. As duas se combinam.
2. **A seleção da região evoluiu de "pintar à mão" para "descrever em texto"**: o SAM 3 (paper Carion et al., arXiv:2511.16719, lançado por Meta em 19/11/2025) segmenta por conceito/texto ("ônibus escolar amarelo") e encontra TODAS as instâncias de uma vez — disponível no ComfyUI via ComfyUI-RMBG v3.0.0.
3. **O "replace" tem solução nativa e definitiva**: os nós `Inpaint Crop and Stitch` recortam só a região mascarada, processam em alta resolução e costuram de volta sem alterar pixels fora da máscara, com blend automático nas bordas. README do lquesada/ComfyUI-Inpaint-CropAndStitch: *"Huge performance improvement of 30x-100x by adding GPU support (new default is GPU, CPU is available as an option for fallback)"* — modo GPU é o padrão e é **30x-100x mais rápido** que CPU, desde que as entradas caibam na memória.
4. **Via código puro**, a composição é matematicamente simples: `out = original*(1-máscara) + editada*máscara`, com a máscara borrada para transição suave. Pillow, NumPy e OpenCV cobrem todos os casos.
5. **Diffusion diferencial (soft inpainting)** elimina bordas duras tratando a máscara como gradiente por pixel, e funciona com checkpoints normais (sem precisar de modelo de inpaint dedicado).

---

## Details

### 1. INPAINTING: selecionar e editar apenas uma parte

#### 1.1 O MaskEditor nativo
No nó **Load Image**, clique direito na imagem > **"Open in MaskEditor"**. Pinte a área a modificar (roda do mouse ajusta o pincel) e clique em **"Save to node"**. O Load Image expõe `IMAGE` e `MASK` (a máscara é o canal alpha/desenhado). Dica: pinte um pouco além do objeto, dando margem para mesclar bordas. Alternativa: carregue uma imagem com canal alpha apagado (GIMP/Photoshop) — o alpha vira máscara.

#### 1.2 Os nós essenciais e suas diferenças
Três formas de "encodar" a máscara para o KSampler — a escolha define a qualidade:
- **VAE Encode (for Inpainting)**: nó dedicado. `grow_mask_by` (6-8 px) cria zona-tampão para blend sem linha. **Exige denoise = 1.0** (denoise menor borra). "True inpainting"; melhor com modelos de inpaint.
- **Set Latent Noise Mask**: ruído só na região latente. Permite **denoise parcial (0.3-0.8)**, ideal para img2img localizado. Usa `VAE Encode` normal antes.
- **InpaintModelConditioning**: o mais flexível e moderno. Condiciona positivo+negativo+latente de uma vez e **permite denoise baixo mesmo com modelos de inpaint** (ex.: 0.45). Recomendado para a maioria dos workflows em 2026.

> Erro comum: usar "Conditioning (Set Mask)" achando que é inpainting — não é (aplica prompt a uma área).

#### 1.3 Controle de força e bordas
- **denoise**: 0.8-1.0 = regeneração completa; 0.5-0.7 = mudança equilibrada; 0.3-0.5 = refinamento sutil.
- **Grow mask**: expande a máscara em N px (buffer). **Blur mask / Gaussian Blur Mask**: feathering, evita costura visível.
- **Differential Diffusion (soft inpainting)**: nó nativo. Combine `Gaussian Blur Mask` → `Differential Diffusion` (no caminho do modelo) → `InpaintModelConditioning` → KSampler. Trata a máscara como gradiente por pixel; funciona com checkpoints comuns. denoise 0.6-0.8. Cuidado: gradiente muito suave altera áreas vizinhas.

#### 1.4 Modelos normais vs especializados
- **Modelos de inpaint dedicados** (SD1.5/SDXL-inpainting): canais extras p/ máscara → transições naturais.
- **Flux.1 Fill [dev]**: estado-da-arte open-source para inpaint/outpaint. Carregue `flux1-fill-dev.safetensors` (Load Diffusion Model) + DualCLIP (clip_l + t5xxl) + VAE (ae.safetensors).
- **ControlNet Inpaint**: modelo padrão com denoise alto sem perder a estrutura sob a máscara.
- **comfyui-inpaint-nodes (Acly)**: Fooocus inpaint patch p/ SDXL, LaMa e MAT para pré-preencher a região.

#### 1.5 Edição por instrução (a revolução de 2025-2026)
Muitas tarefas dispensam máscara — basta descrever:
- **Flux Kontext [dev]**: BFL (HF black-forest-labs/FLUX.1-Kontext-dev, 26/06/2025): *"a 12 billion parameter rectified flow transformer capable of editing images based on text instructions"*. Mantém consistência entre edições. `guidance_scale` padrão 2.5 (0-20). Prompts diretos: "Change the leather jacket to a blue denim jacket". `flux1-dev-kontext_fp8_scaled.safetensors`. 16GB VRAM.
- **Qwen-Image-Edit 2511 / 2509**: 20B (Alibaba). Edição bilíngue de texto na imagem, troca de objetos/fundo, relighting. LoRA Lightning p/ 4 passos. Alimenta a imagem no Qwen2.5-VL (semântica) e no VAE (aparência). Workflow nativo.

---

### 2. SELEÇÃO/MASKING AUTOMÁTICO E SEMÂNTICO

#### 2.1 SAM / SAM2 / SAM3
- **SAM2** (Meta): segmentação por clique/ponto/caixa em imagem e vídeo. ComfyUI via `kijai/ComfyUI-segment-anything-2` (modelos de huggingface.co/Kijai/sam2-safetensors → `ComfyUI/models/sam2`). Nós: `Sam2Segmentation`, `Sam2AutoSegmentation`. Modelos: tiny, small, base_plus, large.
- **SAM3** (19/11/2025): **Promptable Concept Segmentation (PCS)** — uma frase curta ("striped cat") segmenta TODAS as instâncias. Roboflow: *"runs at ~30 ms per image on an H200 GPU, handling 100+ objects, but at ≈840M parameters (≈3.4 GB) it remains a server-scale model"*. ComfyUI via **ComfyUI-RMBG v3.0.0** (1038lab) e Ultralytics 8.3.237+. Requer aprovação de licença no HF para `sam3.pt`.

#### 2.2 Seleção por texto: Grounding DINO + SAM e Florence-2
- **Grounding DINO + SAM** (`storyicon/comfyui_segment_anything`): string semântica ("the sky", "the shirt") → máscara. Nó `GroundingDinoSAMSegment`.
- **Florence-2** (`kijai/ComfyUI-Florence2`): detecção, captioning, OCR, segmentação por expressão. Nó `Florence2Run` com task `referring_expression_segmentation` ou `caption_to_phrase_grounding`. (Bug: referring_expression_segmentation pega 1 segmento por vez p/ múltiplos objetos.)
- **ComfyUI-Grounding** (PozzettiAndrea): 19+ modelos de grounding, Florence-2 e SA2VA p/ raciocínio semântico, gerando máscaras do texto.

#### 2.3 Detecção facial e de partes do corpo (Impact Pack)
**ComfyUI-Impact-Pack** (ltdrdata):
- **UltralyticsDetectorProvider**: YOLO. `bbox/face_yolov8m.pt`, `bbox/hand_yolov8s.pt`, `segm/person_yolov8m-seg.pt`.
- **BBOX/SEGM/SAMDetector**: detecções → SEGS (máscara, bbox, confiança, label).
- **FaceDetailer**: detecta+refina rostos (crop, KSampler interno, cola de volta). BBOX_DETECTOR + SAM p/ silhuetas; 2-pass p/ rostos muito danificados.
- Conversões: `MASK to SEGS`, `SEGS to MASK`, `ToBinaryMask`, `Dilate Mask`, `Gaussian Blur Mask`, `SEGSPaste`.

#### 2.4 Máscara por cor/luminância/profundidade
- `ImageColorToMask` (cor). CLIPSeg (via `CLIPSegDetectorProvider`, máscara por texto sem SAM). Depth/luminância → máscara via threshold.

---

### 3. REPLACE/COMPOSIÇÃO VIA CÓDIGO

#### 3.1 O conceito
A recolagem é alpha matte: `saída = original * (1 - máscara) + editada * máscara`. Máscara 0 (mantém original) a 1 (usa editada). Borrar as bordas (feathering) = transição invisível.

#### 3.2 Nós de composição no ComfyUI
- **ImageCompositeMasked** (nativo): `source` sobre `destination` em (x,y) com máscara. `output = mask*source + (1-mask)*destination`. Nó-base.
- **MaskComposite** (add/subtract/multiply). **JoinImageWithAlpha / SplitImageWithAlpha**. **SEGSPaste** (Impact). **ImageCompositeFromMaskBatch** (essentials). **masquerade-nodes-comfyui** (Cut/Paste By Mask). **ComfyUI_LayerStyle** (camadas estilo Photoshop).

#### 3.3 Stitch — a solução definitiva (Inpaint Crop and Stitch)
O par **`✂️ Inpaint Crop`** + **`✂️ Inpaint Stitch`** (lquesada/ComfyUI-Inpaint-CropAndStitch):
- **Inpaint Crop**: recorta ao redor da máscara (com contexto opcional), redimensiona p/ a resolução-alvo, preenche buracos, cresce/borra a máscara. Saída vai p/ QUALQUER sampling padrão.
- **Inpaint Stitch**: costura de volta **sem alterar pixels fora da máscara** (não passa o resto pelo VAE), blend automático nas bordas.

Parâmetros: `context_expand_pixels`/`context_expand_factor` (contexto = coerência c/ prompt); `blend_pixels` (raio de feathering da recolagem); `rescale_factor` / free/forced/ranged (>1 upscale p/ detalhe, depois reduz; <1 evita "dupla cabeça"); `rescale_algorithm` (bicubic rápido / bislerp qualidade). README: trocar CPU→GPU *"will be 30x-100x faster - however, the inputs must fit in memory"*. Dicas: use `InpaintModelConditioning` (denoise <1), máscara 100% opaca (#FFFFFF), resolução nativa (1024 SDXL/Flux).

#### 3.4 Composição em Python puro

**Pillow — paste com máscara borrada:**
```python
from PIL import Image, ImageFilter
original = Image.open('original.png').convert('RGB')
edited   = Image.open('edited.png').convert('RGB')
mask     = Image.open('mask.png').convert('L')   # 255 = substitui, 0 = mantém
mask_blur = mask.filter(ImageFilter.GaussianBlur(radius=10))   # feathering
result = original.copy()                 # paste() altera in-place; copie antes
result.paste(edited, (0, 0), mask_blur)  # 3º arg = máscara
result.save('result.png')
```
Equivalente: `Image.composite(edited, original, mask_blur)` (mesmo tamanho; image1 onde a máscara é branca).

**NumPy — alpha blend:**
```python
import numpy as np
from PIL import Image
orig   = np.array(Image.open('original.png').convert('RGB')).astype(np.float64)
edited = np.array(Image.open('edited.png').convert('RGB')).astype(np.float64)
m = np.array(Image.open('mask.png').convert('L')).astype(np.float64) / 255.0
m = m[..., np.newaxis]          # (H,W) -> (H,W,1), broadcast p/ 3 canais
out = orig * (1.0 - m) + edited * m
out = np.clip(out, 0, 255).astype(np.uint8)
Image.fromarray(out).save('result.png')
```
Normalize a máscara (`/255`) ANTES de multiplicar; use `m[..., np.newaxis]` p/ broadcast.

**OpenCV — seamlessClone (Poisson blending):**
```python
import cv2, numpy as np
src  = cv2.imread('edited.png')     # patch editado (BGR)
dst  = cv2.imread('original.png')   # destino (BGR)
mask = cv2.imread('mask.png', cv2.IMREAD_GRAYSCALE)
_, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
x, y, w, h = cv2.boundingRect(mask)
center = (x + w // 2, y + h // 2)    # (x,y), não (linha,coluna)
normal = cv2.seamlessClone(src, dst, mask, center, cv2.NORMAL_CLONE)
cv2.imwrite('result_normal.png', normal)
```
`NORMAL_CLONE` preserva a textura do src; `MIXED_CLONE` mistura gradientes (melhor p/ estruturas finas). Cuidados: o src ao redor do center deve caber no dst (senão erro -215); guarde contra máscaras vazias (`if np.any(mask)`); pode deslocar cor/iluminação — p/ fidelidade de pixels, prefira o alpha blend feathered.

#### 3.5 Automação via API HTTP do ComfyUI
Ative **Settings > "Enable Dev mode Options"** p/ revelar **"Save (API Format)"** — o `/prompt` SÓ aceita o JSON achatado (`{node_id: {class_type, inputs}}`), não o JSON da UI.
- `POST /prompt` — `{"prompt": <API JSON>, "client_id": <id>}` → `prompt_id`.
- `POST /upload/image` — multipart (campo `image`, `type=input`).
- `GET /history/{prompt_id}` — outputs. `GET /view?filename=&subfolder=&type=` — bytes. `GET /ws?clientId=` — progresso.
```python
import json, uuid, urllib.request, urllib.parse, requests, websocket  # pip install websocket-client
server = "127.0.0.1:8188"; client_id = str(uuid.uuid4())
def upload_image(path, name, image_type="input", overwrite=True):
    with open(path, "rb") as f:
        files = {"image": (name, f, "image/png")}
        data  = {"type": image_type, "overwrite": str(overwrite).lower()}
        return requests.post(f"http://{server}/upload/image", files=files, data=data).json()
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    req = urllib.request.Request(f"http://{server}/prompt", data=json.dumps(p).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())
def get_history(pid):
    with urllib.request.urlopen(f"http://{server}/history/{pid}") as r: return json.loads(r.read())
def get_image(filename, subfolder, ftype):
    q = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": ftype})
    with urllib.request.urlopen(f"http://{server}/view?{q}") as r: return r.read()
workflow = json.load(open("inpaint_workflow_api.json"))
up = upload_image("original.png", "original.png")
workflow["10"]["inputs"]["image"] = up["name"]            # LoadImage
workflow["6"]["inputs"]["text"]   = "a red sports car"    # CLIPTextEncode +
workflow["3"]["inputs"]["seed"]   = 12345                 # KSampler (mude p/ re-rodar)
ws = websocket.WebSocket(); ws.connect(f"ws://{server}/ws?clientId={client_id}")
pid = queue_prompt(workflow)["prompt_id"]
while True:
    out = ws.recv()
    if isinstance(out, str):
        m = json.loads(out)
        if m["type"]=="executing" and m["data"]["node"] is None and m["data"]["prompt_id"]==pid: break
ws.close()
for node_id, node_out in get_history(pid)[pid]["outputs"].items():
    for img in node_out.get("images", []):
        open(img["filename"], "wb").write(get_image(img["filename"], img["subfolder"], img["type"]))
```
A máscara pode ir pelo mesmo `upload_image` → "Load Image (as Mask)", ou como canal alpha. Ref. oficial: `script_examples/websockets_api_example.py`. Sem auth nativa — proxy em produção. Re-rodar exige mudar a seed (senão retorna o cache).

#### 3.6 Custom nodes que rodam Python
Nós de "Python script"/"execute code" rodam Python arbitrário. `ComfyUI-to-Python-Extension` converte um workflow inteiro em script standalone.

---

### 4. OUTRAS TÉCNICAS PARA IMAGENS
- **Outpainting**: `Pad Image for Outpainting` (borda + máscara) + Flux Fill/inpaint. `Extend Image for Outpainting` (CropAndStitch) traz rescale/blend/restitch.
- **Upscaling**: *Model upscale* (ESRGAN/RealESRGAN/4x-UltraSharp/4x-Foolhardy-Remacri) via `Upscale Image (using Model)`. *Ultimate SD Upscale* (ssitu): tiles + re-difusão, `tile_size`/`seam_fix`/linear-chess, ControlNet Tile p/ coerência. *SUPIR* (kijai/ComfyUI-SUPIR): restauração SDXL, pesado (32GB+ RAM, fp8 ajuda). Comum: SUPIR p/ 2K → 4x Remacri p/ 8K.
- **ControlNet** (canny/depth/openpose/lineart/scribble/tile): estrutura. 2026: Union/Flux ControlNet padrão. `comfyui_controlnet_aux` p/ pré-processadores.
- **IPAdapter** (`ComfyUI_IPAdapter_plus`): estilo/conceito de imagem-ref. **InstantID / PuLID** (Flux PuLID): consistência facial de uma foto.
- **Image-to-image**: VAE Encode + denoise 0.4-0.7 p/ variações.
- **Regional prompting**: `ConditioningSetArea` / `ConditioningSetMask`.
- **LoRAs**: `LoraLoaderModelOnly`; Lightning/Turbo (4-8 passos).
- **Detail**: FaceDetailer, hand detailer (LoRA de mãos), Detailer (SEGS).
- **Relighting**: **IC-Light** (kijai/ComfyUI-IC-Light, huchenlei/ComfyUI-IC-Light-Native): `iclight_sd15_fc` (foreground), `iclight_sd15_fbc` (background). `IC Light Apply Mask Grey` p/ a área mascarada. Combine c/ Image Composite Masked + IPAdapter p/ fotografia de produto.
- **Remoção de fundo**: **ComfyUI-RMBG** (RMBG-2.0, INSPYRENET, BEN2, BiRefNet, SAM3) e BiRefNet. v3.0.0 (01/01/2026) traz SAM3.
- **Color matching**: nós de color match p/ corrigir desvio de cor pós-inpaint (Flux).

#### Geração base — melhores modelos open-source (meados 2026)
- **Flux.2 [dev]** (BFL, github.com/black-forest-labs/flux2): *"[25.11.2025] We are releasing FLUX.2 [dev], a 32B parameter model for text-to-image generation, and image editing"*; *"sets a new standard... consistently outperforming all open-weights alternatives by a significant margin"*. 15/01/2026: **FLUX.2 [klein]** (distiladas, Apache). Múltiplas imagens de ref; ~13GB fp8. Dev é non-commercial.
- **Z-Image Turbo** (6B, 8 passos, Apache 2.0): velocidade; texto bilíngue; 16GB.
- **Qwen-Image 2512 / Qwen-Image-Edit 2511**: all-rounder, edição por instrução + texto na imagem.
- **Flux.1 [dev]/[schnell]**: ecossistema maduro; schnell Apache 2.0 (1-4 passos).
- **SDXL**: ecossistema, LoRAs, velocidade em hardware modesto.

---

### 5. OTIMIZAÇÕES DE QUALIDADE E VELOCIDADE
**Sampler**: SDXL/SD1.5 `dpmpp_2m`+`karras`, 25-30 passos, CFG 6-7. Flux/Flux Fill euler/res_multistep; Kontext guidance ~2.5. Qwen distilled ~10 passos, CFG 1.0. Lightning/Turbo 4-8 passos.
**Quantização**: **GGUF** Q8/Q5 ≈ FP16; Q4 amolece; Q3- perde. `Unet Loader (GGUF)`. **fp8** (e4m3fn): MindStudio *"FP8 quantization cuts VRAM usage by approximately 40% while maintaining similar quality"*; `--fast`. **NF4/FP4** p/ Blackwell.
**Aceleração**: **SageAttention** (`--sage-attention`); 2/3 ganham em alta resolução. **torch.compile** (KJNodes) ~6% em imagens. **TeaCache/MagCache/WaveSpeed** (cache de passos; pode degradar).
**Resoluções**: 1024×1024 (SDXL/Flux/Qwen), 512 (SD1.5). No inpaint, force a região à resolução nativa.

---

## Recommendations (pipeline do iniciante ao avançado)
1. **Simples**: Load Image → MaskEditor → `InpaintModelConditioning` → KSampler (denoise 0.5-0.7) → VAE Decode → Save. 80% dos casos. Bordas/cor ruins → passo 2.
2. **Crop & Stitch + Differential Diffusion**: `Inpaint Crop` antes, `Inpaint Stitch` depois (`blend_pixels` 16-32, GPU). + `Differential Diffusion` + `Gaussian Blur Mask`. Resolve bordas, ganha resolução, acelera 30-100x. Precisa selecionar por descrição → passo 3.
3. **Seleção semântica**: SAM3 (ComfyUI-RMBG) ou Florence-2/Grounding DINO + SAM2 (máscara por texto). Rostos/mãos → Impact Pack (UltralyticsDetector + FaceDetailer).
4. **Sem máscara**: Flux Kontext Dev ou Qwen-Image-Edit 2511 (prompt de instrução). Trocar cor/estilo/fundo c/ consistência. Combine c/ inpaint mascarado p/ controle cirúrgico.
5. **Automação**: exporte API Format, suba via `/prompt`+`/upload/image`; composição fora do ComfyUI em Python (alpha blend feathered = fidelidade; seamlessClone = harmonização de cor/luz).

**Modelos a baixar primeiro**: Flux.1 Fill dev, Flux Kontext Dev fp8, SDXL-inpainting, SAM2/SAM3 + Florence-2, 4x-UltraSharp + SUPIR, face_yolov8m + sam_vit_b.

**Erros comuns**: *Bordas* → grow_mask_by 6-8 + blur + Differential Diffusion + blend_pixels. *Desvio de cor (Flux)* → Color Match c/ a área não-mascarada. *Contexto perdido* → ↑context_expand. *Área cinza/vazia* → denoise baixo c/ VAE Encode for Inpainting (use 1.0 ou troque p/ Set Latent Noise Mask / InpaintModelConditioning). *"Dupla cabeça"* → ↓rescale_factor (<1).

---

## Caveats
- Ritmo de lançamento altíssimo; nomes de versão (Flux.2 dev/klein, Qwen-Image 2512, SAM 3.1) são de meados de 2026 e mudarão. Verifique datas/licenças (Flux.2 dev non-commercial; Z-Image Turbo e Flux schnell Apache 2.0).
- Fontes SEO/comerciais (RunComfy, MimicPC, apatero) cruzadas c/ docs oficiais (docs.comfy.org, GitHub) quando possível.
- SAM3 e Flux.2 exigem hardware robusto; SAM3 requer aprovação de licença no HF.
- `cv2.seamlessClone` harmoniza cor/luz mas pode suavizar detalhes e alterar cor — p/ fidelidade de pixels prefira alpha blend feathered.
- Ganhos de torch.compile variam por GPU/SO; teste no seu setup.
