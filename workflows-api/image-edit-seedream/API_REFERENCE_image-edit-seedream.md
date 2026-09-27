# API Reference — image-edit-seedream

> Schemas extraídos do `/object_info` ao vivo (`:8188`), da fonte
> `ComfyUI/comfy_api_nodes/nodes_bytedance.py` e dos templates oficiais instalados.
> Tudo **core** — nenhum custom node.

## `ByteDanceSeedreamNode` — "ByteDance Seedream 4.5 & 5.0"
- **Categoria:** `partner/image/ByteDance` · **Módulo:** `comfy_api_nodes.nodes_bytedance`
- **Billing:** créditos **comfy.org** (auth por login)
- **Saída:** `IMAGE`

### Inputs
| Nome | Tipo | Obrig. | Default | Nota |
|---|---|---|---|---|
| `model` | COMBO | ✅ | — | `seedream 5.0 lite` · `seedream-4-5-251128` · `seedream-4-0-250828` |
| `prompt` | STRING multiline | ✅ | `""` | Estilo **frase única** |
| `size_preset` | COMBO | ✅ | — | ver tabela abaixo |
| `image` | IMAGE | — | — | Referência(s). Batch via `BatchImagesNode` |
| `width` / `height` | INT | — | `2048` | Só com `size_preset=Custom`. `width` 1024–6240, `height` 1024–4992, passo 2 |
| `sequential_image_generation` | COMBO | — | `disabled` | `disabled` · `auto` |
| `max_images` | INT | — | `1` | 1–15, só com `auto`. Entrada + geradas ≤ 15 |
| `seed` | INT | — | `0` | 0 … 2147483647 |
| `watermark` | BOOLEAN | — | `false` | marca d'água "AI generated" |
| `fail_on_partial` | BOOLEAN | — | `true` | aborta em vez de devolver resultado parcial |

### `size_preset` — opções
`2048x2048 (1:1)` · `2304x1728 (4:3)` · `1728x2304 (3:4)` · `2560x1440 (16:9)` · `1440x2560 (9:16)` ·
`2496x1664 (3:2)` · `1664x2496 (2:3)` · `3024x1296 (21:9)` · `3072x3072 (1:1)` · `4096x4096 (1:1)` · `Custom`

### ⚠️ Pisos e tetos de pixels (validados no cliente, antes da chamada)
| Modelo | Mínimo de pixels na saída | Máximo | Máx. imagens de referência | Formato de saída |
|---|---|---|---|---|
| `seedream-5-0-260128` (5.0 lite) | **3.686.400** (≈2560×1440) | 10.404.496 | **14** | PNG |
| `seedream-4-5-251128` | **3.686.400** | 16.777.216 | 10 | padrão do provedor |
| `seedream-4-0-250828` | **921.600** | 16.777.216 | 10 | padrão do provedor |

Preset abaixo do piso → o nó **rejeita antes de gastar crédito**. `2048x2048` (4,19 MP) passa;
`2304x1728` (3,98 MP) passa; nada menor que ~3,69 MP passa no 4.5/5.0.

### Ordem exata dos `widgets_values`
```
[0]  model
[1]  prompt
[2]  size_preset
[3]  width
[4]  height
[5]  sequential_image_generation
[6]  max_images
[7]  seed (INT)
[8]  control_after_generate
[9]  watermark (bool)
[10] fail_on_partial (bool)
```

### Slots de input
```
slot 0 → image (IMAGE)
```

### Sem seed gate
Ao contrário dos nós `*_fal`, nenhum valor de seed **trava** a chamada aqui.

## `ByteDanceSeedreamNodeV2`
Existe no `/object_info` com o **mesmo display name**. Usa o schema novo `COMFY_DYNAMICCOMBO_V3`
(os parâmetros vivem **dentro** da opção de modelo escolhida), o que muda toda a ordem dos
`widgets_values`. **Este bundle usa a V1** de propósito: ordem estável e igual à dos templates oficiais.
Se você trocar o nó pela V2 na interface, os widgets **não** são compatíveis.

## `BatchImagesNode`
- Input `images` **autogrow** (`COMFY_AUTOGROW_V3`, prefixo `image`, min 1, max 50).
- Slots: **`images.image0`, `images.image1`, …** (0-indexado); o frontend mantém um slot livre com `"shape": 7`.
- `widgets_values`: `[]`.
- A ordem do batch = *the first image*, *the second image*… no prompt.

## `LoadImage` / `SaveImage`
- `LoadImage.widgets_values = [filename, "image"]` · saídas `IMAGE`, `MASK`.
- `SaveImage.widgets_values = [filename_prefix]` · input `images`.

## Custo
Uma chamada por bloco **não-bypassado** por `Run`. `sequential_image_generation=auto` com
`max_images=N` gera (e cobra) até N imagens. Preços atuais: tabela em `platform.comfy.org` — não fixados
aqui de propósito, porque mudam.

## Ver também
- registo CoALA `knowledge-comfyui-api-nodes`
- `../image-edit-nano-banana-2/API_REFERENCE_image-edit-nano-banana-2.md`
