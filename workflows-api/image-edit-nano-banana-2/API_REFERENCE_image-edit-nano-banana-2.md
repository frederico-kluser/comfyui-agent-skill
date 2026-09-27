# API Reference — image-edit-nano-banana-2

> Schemas extraídos do `/object_info` do ComfyUI ao vivo (`:8188`) e conferidos contra os templates
> oficiais que acompanham a instalação. Tudo aqui é **core** — nenhum custom node.

## `GeminiNanoBanana2` — "Nano Banana 2"
- **Categoria:** `partner/image/Gemini` · **Módulo:** `comfy_api_nodes.nodes_gemini`
- **Billing:** créditos **comfy.org** (auth por login; `auth_token_comfy_org` é hidden input)
- **Saídas:** `IMAGE` · `STRING` · `thought_image` (IMAGE)

### Inputs
| Nome | Tipo | Obrig. | Default | Nota |
|---|---|---|---|---|
| `prompt` | STRING multiline | ✅ | `""` | A instrução de edição |
| `model` | COMBO | ✅ | — | Única opção: `Nano Banana 2 (Gemini 3.1 Flash Image)` |
| `seed` | INT | ✅ | `42` | 0 … 18446744073709551615. Repetição é *best effort*, **não determinística** |
| `aspect_ratio` | COMBO | ✅ | `auto` | `auto` · `1:1` · `2:3` · `3:2` · `3:4` · `4:3` · `4:5` · `5:4` · `9:16` · `16:9` · `21:9` |
| `resolution` | COMBO | ✅ | — | `1K` · `2K` · `4K` (2K/4K usam o upscaler nativo do Gemini) |
| `response_modalities` | COMBO | ✅ | — | `IMAGE` · `IMAGE+TEXT` |
| `thinking_level` | COMBO | ✅ | — | `MINIMAL` · `HIGH` |
| `images` | IMAGE | — | — | Referências. **Até 14** — use `BatchImagesNode` |
| `files` | GEMINI_INPUT_FILES | — | — | Vem do nó `GeminiInputFiles` |
| `system_prompt` | STRING multiline | — | (longo) | Instruções de base. Neste bundle foi reescrito para compositing fotorrealista |

### Ordem exata dos `widgets_values`
```
[0] prompt
[1] "Nano Banana 2 (Gemini 3.1 Flash Image)"
[2] seed (INT)
[3] control_after_generate   ("randomize" | "fixed" | "increment" | "decrement")
[4] aspect_ratio
[5] resolution
[6] response_modalities
[7] thinking_level
[8] system_prompt
```
> ⚠️ Ordem **diferente** da ordem declarada no `/object_info` (o frontend intercala o
> `control_after_generate` logo depois do `seed`). Reconstruir o nó à mão fora dessa ordem embaralha
> os widgets silenciosamente.

### Slots de input (para religar links à mão)
```
slot 0 → images   (IMAGE)
slot 1 → files    (GEMINI_INPUT_FILES)
```

### Sem seed gate
Diferente dos nós `*_fal` (onde um seed errado **trava** a chamada), aqui qualquer valor é aceito.
`control_after_generate` só decide se o valor muda entre runs.

## `BatchImagesNode` — "Batch Images"
- **Core.** Input `images` é **autogrow** (`COMFY_AUTOGROW_V3`, prefixo `image`, min 1, max 50).
- Slots nomeados **`images.image0`, `images.image1`, …** — repare no **0-indexado**.
- O frontend sempre mantém **um slot livre a mais**, marcado com `"shape": 7`.
- Saída: `IMAGE` (batch). A ordem do batch = a ordem `Image 1`, `Image 2`… vista pelo modelo.
- `widgets_values`: `[]` (nenhum widget).

## `LoadImage` / `SaveImage`
- `LoadImage.widgets_values = [filename, "image"]` · saídas `IMAGE`, `MASK`.
- `SaveImage.widgets_values = [filename_prefix]` · input `images`.

## Custo
Cada bloco **não-bypassado** dispara **uma** chamada ao Nano Banana 2 por `Run`. Bypass (`Ctrl+B`) no
`SaveImage` desliga o bloco inteiro — os nós a montante não executam e nada é cobrado.

`thinking_level=HIGH` e `resolution=4K` custam mais que `MINIMAL`/`1K`. Confira a tabela de preços em
`platform.comfy.org` — os valores mudam e **não** estão fixados aqui de propósito.

## Ver também
- registo CoALA `knowledge-comfyui-api-nodes` — as 3 rotas (partner / fal / Replicate), seed gates, chaves.
- `../image-edit-seedream/API_REFERENCE_image-edit-seedream.md` — o mesmo, para o Seedream.
