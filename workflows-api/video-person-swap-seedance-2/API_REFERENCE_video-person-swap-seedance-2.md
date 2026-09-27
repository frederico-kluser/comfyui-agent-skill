# API Reference — video-person-swap-seedance-2

> Schemas extraídos do `/object_info` ao vivo (`:8188`), da fonte
> `ComfyUI/comfy_api_nodes/nodes_bytedance.py` e dos templates oficiais instalados.
> Tudo **core** — nenhum custom node.

## `ByteDance2ReferenceNode` — "ByteDance Seedance 2.0 Reference to Video"
- **Categoria:** `partner/video/ByteDance` · **Módulo:** `comfy_api_nodes.nodes_bytedance`
- **Billing:** créditos **comfy.org** (auth por login)
- **Saída:** `VIDEO` **nativo** → vai direto no `SaveVideo`, **áudio preservado**
  (é o padrão B do registo CoALA `knowledge-comfyui-api-nodes`; nós `*_fal` devolvem URL e perdem o áudio)

### Estrutura do input: `COMFY_DYNAMICCOMBO_V3`
O widget `model` é um **combo dinâmico**: os parâmetros mudam conforme a opção escolhida.

| Opção | `resolution` disponível |
|---|---|
| `Seedance 2.0` | `480p` · `720p` · **`1080p`** |
| `Seedance 2.0 Fast` | `480p` · `720p` |

Parâmetros iguais nas duas opções:

| Nome | Tipo | Default | Faixa / opções |
|---|---|---|---|
| `prompt` | STRING multiline | `""` | — |
| `ratio` | COMBO | `adaptive` | `16:9` · `4:3` · `1:1` · `3:4` · `9:16` · `21:9` · `adaptive` |
| `duration` | INT (slider) | `7` | **4 – 15** segundos |
| `generate_audio` | BOOLEAN | `true` | gera áudio novo |
| `auto_downscale` | BOOLEAN (advanced) | `true` | reduz vídeo de referência acima do orçamento de pixels, preservando o formato |
| `auto_upscale` | BOOLEAN (advanced) | `false` | amplia vídeo abaixo do mínimo — **não cria detalhe** |

Fora do combo (sempre presentes):

| Nome | Tipo | Default | Nota |
|---|---|---|---|
| `seed` | INT | `0` | 0 … 2147483647. ⚠️ Tooltip do nó: *"Seed controls whether the node should re-run; results are non-deterministic regardless of seed."* |
| `watermark` | BOOLEAN (advanced) | `false` | — |

### Entradas de referência: `COMFY_AUTOGROW_V3`
| Grupo | Prefixo dos slots | Máximo |
|---|---|---|
| `reference_images` | `model.reference_images.image_1 … image_9` | **9** |
| `reference_videos` | `model.reference_videos.video_1 … video_3` | **3** |
| `reference_audios` | `model.reference_audios.audio_1 … audio_3` | **3** |
| `reference_assets` | `model.reference_assets.asset_1 … asset_9` (STRING, `forceInput`) | **9** |

⛔ **`reference_images` e `reference_videos` NÃO aceitam humano real.** Para humano real, crie um asset
(ver abaixo) e ligue o `asset_id` em `reference_assets.asset_N`.

### Rótulos posicionais no prompt (a regra que mais confunde)
Os assets são anexados ao payload **depois** de `reference_images` / `reference_videos` /
`reference_audios`, e recebem rótulos 1-indexados que **continuam a contagem do mesmo tipo**:

```
0 reference_images + asset_1 (tipo Image) → asset_1 é "Image 1"
1 reference_images + asset_1 (tipo Image) → asset_1 é "Image 2"
0 reference_videos + asset_2 (tipo Video) → asset_2 é "Video 1"
```

O nó reescreve tokens do prompt via regex `\basset ?(\d{1,2})\b` (case-insensitive): **`asset 1`** e
**`asset1`** viram o rótulo — mas **`asset_1` (com underscore) NÃO casa com a regex** e passa cru para o
modelo. Por isso este bundle escreve **`Image 1`** e **`Video 1`** direto no prompt.

### Ordem exata dos `widgets_values`
```
[0]  model               ("Seedance 2.0" | "Seedance 2.0 Fast")
[1]  prompt
[2]  resolution
[3]  ratio
[4]  duration (INT)
[5]  generate_audio (bool)
[6]  auto_downscale (bool)
[7]  auto_upscale (bool)
[8]  seed (INT)
[9]  control_after_generate
[10] watermark (bool)
```
> O `prompt` pode ser convertido em **input socket** (`model.prompt`, tipo STRING). Quando isso acontece,
> ele vira o **slot 0** e `widgets_values[1]` fica `""`. Neste bundle o prompt é widget (editável no nó).

### Slots de input deste workflow (ordem no arquivo)
```
slot 0 → model.reference_images.image_1   (IMAGE)  — livre
slot 1 → model.reference_videos.video_1   (VIDEO)  — livre (use se o vídeo NÃO tiver humano real)
slot 2 → model.reference_audios.audio_1   (AUDIO)  — livre
slot 3 → model.reference_assets.asset_1   (STRING) ← asset_id da SUA foto     → "Image 1"
slot 4 → model.reference_assets.asset_2   (STRING) ← asset_id do VÍDEO        → "Video 1"
```

## `ByteDanceCreateImageAsset` / `ByteDanceCreateVideoAsset`
- **Entrada:** `image` (IMAGE) / `video` (VIDEO) · **Widget:** `group_id` (STRING, `""`)
- **Saídas:** `asset_id` (STRING) · `group_id` (STRING)
- `widgets_values`: `[group_id]`

**Fluxo de verificação:** com `group_id` vazio, o nó chama
`POST /proxy/seedance/visual-validate/sessions`, **loga um link H5 no console do servidor** e fica em
polling até a verificação facial ser concluída no navegador. Preencher o `group_id` de uma verificação
anterior **pula** essa etapa para a mesma pessoa.

O `asset_id` é validado antes de cada geração (`GET /proxy/seedance/assets/{id}`): se o status não for
`Active`, o nó falha com `Reference asset N (Id=...) is not Active`.

> Padrão dos templates oficiais: o `asset_id` passa por um `PreviewAny` **antes** de ir ao Seedance —
> o `PreviewAny` mostra **e repassa** a STRING. Este bundle segue o mesmo caminho.

## `GeminiNode` (helper do PASSO 4)
- **Categoria:** `partner/…/Gemini` · **Saída:** `STRING`
- **Modelos:** `gemini-3-1-pro` · `gemini-3-1-flash-lite` · `gemini-3-pro-preview` · `gemini-2.5-pro` · `gemini-2.5-flash` (+ previews antigos)
- **Inputs:** `images` (IMAGE) · `audio` (AUDIO) · `video` (VIDEO) · `files` (GEMINI_INPUT_FILES)
- **Ordem dos `widgets_values`:**
```
[0] prompt
[1] model
[2] seed (INT)
[3] control_after_generate
[4] system_prompt
```
- **Slots de input:** `0 → images`, `1 → audio`, `2 → video`, `3 → files`

## `StringConcatenate` / `PreviewAny` / `LoadVideo` / `SaveVideo`
| Nó | Widgets | Inputs | Outputs |
|---|---|---|---|
| `StringConcatenate` | `[string_a, string_b, delimiter]` | `string_b` (convertido em socket aqui) | `STRING` |
| `PreviewAny` | `[null, null, null]` | `source` (`*`) | `STRING` (repassa) |
| `LoadVideo` | `[filename, "image"]` | — | `VIDEO` |
| `SaveVideo` | `[filename_prefix, format, codec]` | `video` | — |

## Custo
- **PASSO 3** = uma geração de vídeo por `Run`. É a chamada cara; escala com `resolution` e `duration`.
- **PASSOS 1 e 2** = criação de asset (chamada barata) + a verificação, que é única por pessoa/conta.
- **PASSO 4** = uma chamada Gemini por `Run` — por isso vem em **bypass**.

Preços atuais: tabela em `platform.comfy.org` (mudam; não fixados aqui de propósito).

## Ver também
- registo CoALA `knowledge-comfyui-api-nodes` — as 3 rotas de billing, os 2 padrões de saída de vídeo, seed gates.
- Doc oficial: <https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-0-real-human>
