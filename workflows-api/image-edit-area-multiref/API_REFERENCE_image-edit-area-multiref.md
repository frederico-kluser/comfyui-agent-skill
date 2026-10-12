# API_REFERENCE — image-edit-area-multiref

Cards por nó (entradas, parâmetros, armadilhas) e o contrato do cliente headless. Valores conferidos no
`/object_info` do ComfyUI **0.38.0** (commit `f1072eb0`, 2026-10-03).

## `GeminiNanoBanana2V2` — "Nano Banana 2" (partner, `comfy_api_nodes.nodes_gemini`)

| Entrada | Tipo | Valor aqui | Nota |
|---|---|---|---|
| `prompt` | STRING (ligado) | regras + instrução + papéis | `validate_string(min_length=1)` |
| `model` | DYNAMICCOMBO | `Nano Banana 2 (Gemini 3.1 Flash Image)` | ou `Nano Banana 2 Lite` (só 1K) |
| `model.aspect_ratio` | COMBO | **`1:1`** | `auto` segue a 1ª imagem; aqui o recorte é sempre 1:1 |
| `model.resolution` | COMBO | `1K` | 1K/2K/4K (Lite: só 1K) |
| `model.thinking_level` | COMBO | `HIGH` | `MINIMAL`/`HIGH` |
| `model.images.image_1…14` | AUTOGROW (IMAGE) | 1 = recorte, 2 = mapa, 3–12 = REF 1–10 | slots `None` são **descartados** e as imagens **renumeradas**; > 14 = erro na execução |
| `seed` | INT | aleatório | "best effort", não determinístico |
| `response_modalities` | COMBO | `IMAGE` | `IMAGE+TEXT` devolve também o `thought_image` |
| `system_prompt` / `temperature` / `top_p` | opcionais | padrão / 1.0 / 0.95 | — |

- **Endpoint:** `/proxy/vertexai/gemini/gemini-3.1-flash-image` (Lite: `gemini-3.1-flash-lite-image`).
- **Preço (badge, aproximado):** US$ 0,0835 (1K) · 0,1217 (2K) · 0,1848 (4K) · Lite 0,0408. O badge não varia com o número de referências.
- **Auth:** oculto `auth_token_comfy_org` (login na interface) **ou** `api_key_comfy_org` (← `extra_data` do `/prompt`, vira o header `X-API-KEY`).
- **Formato API dos campos dinâmicos:** chaves com ponto, achatadas: `"model": "<opção>"`, `"model.resolution": "1K"`, `"model.images.image_3": ["30", 0]`.
- **Formato UI (`widgets_values`, 11):** `[prompt, model, aspect_ratio, resolution, thinking_level, seed, control_after_generate, response_modalities, system_prompt, temperature, top_p]`.

## `InpaintCropImproved` — "✂️ Inpaint Crop" (custom `lquesada/ComfyUI-Inpaint-CropAndStitch` @ `8584b08`)

Saídas: `stitcher` · `cropped_image` · `cropped_mask`. Sem IA. `device_mode = gpu (much faster)`. Medido nesta máquina
(RTX 4070), numa foto de 6000×4000 re-executada (LoadImage e trava em cache, só recorte → mapa → recolagem): ~3,3 s em
`cpu (compatible)` contra ~2,6 s em `gpu`, com a mesma garantia de pixels. A 1ª execução de uma foto nova desse tamanho
passa de 10 s por causa do `LoadImage` e da `GrowMask` de 72 px (72 passes de dilatação em 24 MP), que não dependem do
modo. Com `--cpu`, o modo `gpu` roda na CPU e é ~2,5× mais lento que `cpu (compatible)`. Por isso o cliente escolhe pelo
`/system_stats` (`--crop-device auto`). Sem CUDA, o ComfyUI 0.38 **não** cai para a CPU sozinho: quebra ao importar. Quem
põe o `--cpu` é o `run.sh`, quando não há `nvidia-smi` ou o torch não tem CUDA.

| Parâmetro | Aqui | Efeito |
|---|---|---|
| `mask_fill_holes` | **`false`** | se `true`, encheria um contorno pintado — mas a trava usa a máscara **crua** e desfaria o miolo. Pinte a área preenchida |
| `mask_expand_pixels` | `8` | engorda a máscara (efeito visível menor que o número: medido 8 → ~2 px, 24 → ~5 px) |
| `mask_blend_pixels` | `32` | suavização da recolagem (`expand_m(blend)` + `blur_m(blend × 0,5)`; a borda visível fica em ~20 px a 1:1) |
| `context_from_mask_extend_factor` | `2.0` | contexto em volta do retângulo da máscara |
| `output_resize_to_target_size` + `output_target_width/height` | `true`, `1024×1024` | recorte **quadrado** no tamanho do modelo |
| `extend_for_outpainting` | `false` | — |

- **Máscara vazia** → o contexto vira a foto inteira e o blend sai ~0. Não dá erro: a IA roda e cobra.
- Quando o contexto passa da borda da foto, o canvas é **acolchoado**, e a máscara do acolchoado é `1`. O blend
  vaza para dentro da borda da foto (medido: ~20 px a 1:1 e até ~42 px com o recorte ampliado ~4×). A **trava** (abaixo) corrige.
- **Formato UI (24):** a ordem é o `input_order` do nó sem `image` (o exemplo oficial do repo tem 23, de uma versão sem `device_mode`).

## `InpaintStitchImproved` — "✂️ Inpaint Stitch"

`stitcher` + `inpainted_image`. Redimensiona a imagem editada (qualquer tamanho) para o retângulo de contexto e
mistura com `cropped_mask_for_blend`. Devolve a foto no tamanho original.

## Trava de pixels (core)

`GrowMask(mask = LoadImage.MASK, expand = 72, tapered_corners = true)` → `MaskToImage` → `ImageBlur(blur_radius = 16,
sigma = 6)` → `ImageToMask(red)` → `ImageCompositeMasked(destination = foto original, source = stitch, mask = limite
suave)`. O kernel do desfoque tem suporte finito (16 px), então a máscara é **exatamente 0** além de 72 + 16 = **88 px**,
e ali `destination·1 + source·0` devolve **o valor exato** do pixel original (o arredondamento float32 → 8 bits é exato
para os 256 níveis). Regra: `expand ≥ mask_expand_pixels + 2 × mask_blend_pixels`. O desfoque existe porque, quando o
recorte acolchoa a borda da foto, a recolagem muda pixels da borda e um corte seco a 72 px deixaria uma costura.

"Original" = **o que o `LoadImage` decodificou**. No ComfyUI 0.38 o JPEG/WebP pode diferir ±1–3 níveis de um decode
PIL, e um PNG em tons de cinza vira RGB com ±1. O cliente envia sempre **PNG RGB** (decodificado pelo PIL, já em pé
pelo EXIF): por script, a fidelidade é bit a bit com essa versão.

## Mapa da área (core) — "Image 2"

`ThresholdMask(0.5)` → `GetImageSize` → `EmptyImage(w, h, color = 16711935)` → `ImageBlend(recorte, magenta, 0.45,
normal)` → `ImageCompositeMasked(recorte, tingido, mask)` → contorno: `GrowMask(+6)` − máscara
(`MaskComposite subtract`) → `ImageCompositeMasked(…, magenta, anel)`. O mapa **só orienta** o modelo; a garantia
de pixels vem da recolagem e da trava.

## `LoadImage` (base) e a máscara

`MASK = 1 − alfa`: **transparente = área a editar**. Sem alfa, devolve uma máscara **64×64 de zeros** (o Inpaint Crop
redimensiona). É o que o MaskEditor grava e o que o `/upload/mask` produz.

## `SaveImageWebsocket` (exemplo em `custom_nodes/websocket_image_save.py`)

Não é core: o arquivo vem no repositório, e o `git clone` o carrega por padrão (não carrega com
`--disable-all-custom-nodes`). Envia cada imagem pelo hook de progresso como PNG de tamanho cheio, sem metadados.

---

## Cliente headless (REST + WebSocket)

`scripts/comfy_client.py`, nesta ordem:

| # | Chamada | Corpo / detalhe |
|---|---|---|
| 1 | `GET ws://HOST/ws?clientId=<uuid>` | **antes** do `/prompt`: o servidor não reenvia eventos; ao conectar já chega um `status` |
| 2 | `POST /upload/image` | multipart: `image` (arquivo), `type=input`, `subfolder=inpaint-multiref`, `overwrite=false` → `{name, subfolder, type}` |
| 3 | `POST /upload/mask` | idem + `original_ref={"filename","subfolder","type":"input"}`. O servidor abre a original, copia o **canal alfa** da máscara enviada e grava um PNG RGBA com o **nome da máscara**. Se a original não existir, responde 200 e não grava nada |
| 4 | grafo API | `graph_spec.build_api_prompt()`: 1 `LoadImage` por referência (`30…39`) → `model.images.image_3…12` |
| 5 | `POST /prompt` | `{"prompt", "client_id", "prompt_id"(uuid minúsculo), "extra_data": {"api_key_comfy_org"}}` → `{prompt_id, number, node_errors}`. Com grafo inválido, **HTTP 400** + `node_errors` |
| 6 | eventos (texto) | `status` (`data.status.exec_info.queue_remaining`) · `execution_start` · `execution_cached` (`nodes`) · `executing` (`node`; **`null` = fim, com sucesso ou erro**) · `progress` (`value`/`max`) · `executed` · `execution_success` · `execution_error` (`exception_type`, `exception_message`, `node_id`, `traceback`) · `execution_interrupted` |
| 7 | eventos (binário) | `>I` tipo (1 = PREVIEW_IMAGE) + `>I` formato (1 = JPEG, 2 = PNG) + bytes → **`frame[8:]`**. Atribuído ao nó do último `executing` (o `SaveImageWebsocket` = id `62`) |
| 8 | plano B | `GET /history/{prompt_id}` → `outputs[*].images[]` → `GET /view?filename=&subfolder=&type=` (só com `SaveImage` no grafo: `--salvar-no-servidor`) |

**Armadilhas verificadas**

- **Dedup no upload:** só acontece quando já existe um arquivo com o **mesmo nome** e o hash bate; com nome diferente,
  o servidor grava outra cópia. Por isso o cliente nomeia pelo hash do conteúdo (`<sha256[:12]>_<nome>`).
- **`overwrite`** é comparado como string exata (`"true"` ou `"1"`; `"True"` não conta).
- **`/upload/mask` nunca deduplica:** o hash comparado é o da máscara **enviada** contra o PNG **já mesclado** no
  disco, que sempre diferem. Com `overwrite=false`, cada envio cria `nome (1).png`, `(2)`… O cliente usa `overwrite=true`
  com nome = hash(base + máscara): é idempotente.
- **Chave:** se o prompt é válido, o servidor tira `api_key_comfy_org` de `extra_data` (`SENSITIVE_EXTRA_DATA_KEYS`) antes
  da fila e do histórico. Não existe fallback por variável de ambiente **no servidor**: quem lê `COMFY_ORG_API_KEY` é o
  cliente.
- **Frames tipo 4** (`PREVIEW_IMAGE_WITH_METADATA`: 4 bytes de tipo + 4 de tamanho do JSON + JSON + imagem) só
  chegam se o cliente anunciar `feature_flags.supports_preview_metadata`. Este cliente não anuncia, mas trata o tipo 4.
- **Só o `client_id` dono recebe** os eventos de execução. Sem `client_id` no `/prompt`, o WebSocket fica mudo.
- **`/free`** (`{"unload_models": true, "free_memory": true}`) não serve para nada aqui: não há modelo local.

## Erros e o que significam

| Mensagem | Origem | Ação |
|---|---|---|
| `Unauthorized: Please login first to use this node.` | 401 do proxy comfy.org | login (UI) / `COMFY_ORG_API_KEY` (script) |
| `402` / créditos insuficientes | billing | comprar créditos |
| `API Error: Not Found` (404) | rota não servida pelo comfy.org | confira docs.comfy.org/tutorials/partner-nodes/pricing |
| `The current maximum number of supported images is 14.` | > 14 imagens no Nano Banana | máx. 10 REFs (+ recorte e mapa) |
| `invalid_prompt_id` | `prompt_id` fora do formato UUID minúsculo | gere com `uuid4()` |
