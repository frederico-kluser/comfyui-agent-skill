# image-edit-area-multiref — editar SÓ uma área da foto, com até 10 referências (por API)

> Você pinta a área, escreve o que deve aparecer ali e liga até **10 imagens de referência**. O modelo
> roda **na nuvem** (Nano Banana 2, créditos comfy.org) e o resto da foto **não muda**: a IA edita só um
> recorte, e a recolagem mais uma trava devolvem o pixel original em tudo que fica longe da área.
> **Nenhum modelo de IA roda nesta máquina.**

|  |  |
|---|---|
| 🎯 Faz | Inpainting por API: troca, insere ou remove algo **só dentro da máscara**, guiado por texto + até 10 referências |
| 🧠 Técnica | **Recorte 1:1 + mapa magenta da área** → modelo multi-referência → **Inpaint Stitch** → **trava de pixels** (`ImageCompositeMasked` contra a original) |
| 💳 Custo/billing | **Créditos comfy.org**, 1 chamada por Run: ~US$ 0,08 (1K) · 0,12 (2K) · 0,18 (4K) · Lite ~0,04 (badge do nó) |
| 🔌 Provedores/Nós | `GeminiNanoBanana2V2` (partner) · `InpaintCropImproved`/`InpaintStitchImproved` (**custom, sem IA**) · core: `LoadImage`, `ThresholdMask`, `GetImageSize`, `EmptyImage`, `ImageBlend`, `ImageCompositeMasked`, `GrowMask`, `MaskComposite`, `StringConcatenate`, `PrimitiveStringMultiline`, `SaveImage` · `SaveImageWebsocket` (exemplo que vem no `git clone`) |
| 📥 Entrada | 1 foto + máscara (MaskEditor, ou PNG P&B no script) · 0–10 referências · 2 textos (o que fazer + papel das referências) |
| 📤 Saída | Foto no tamanho original (`output/inpaint-multiref/final_*.png`); por script, PNG via WebSocket em `~/ComfyUI/output/inpaint-multiref/script/` |
| 🧩 Modelos | Nano Banana 2 · Gemini 3.1 Flash Image (ou **Lite**, `gemini-3.1-flash-lite-image`), via proxy comfy.org → Google Vertex |
| 🧱 Requer | ComfyUI ≥ 0.38 (nó `GeminiNanoBanana2V2`) · custom node **ComfyUI-Inpaint-CropAndStitch** (o `setup.sh` instala) · **login** comfy.org (interface) ou **`COMFY_ORG_API_KEY`** (script) |
| 🟡 Status | Grafo **executado ponta a ponta** em `--simular` (sem IA), recorte/mapa/recolagem/trava **medidos** (0 pixels alterados fora da zona: meio, cantos, borda, sem máscara, até 6000×4000) e **revisados por um 2º agente**; o Nano Banana 2 foi **chamado e respondeu 401** sem chave, ou seja, o servidor aceitou o grafo. **A chamada paga ainda não foi executada.** |

📇 **Card de API:** [`API_REFERENCE_image-edit-area-multiref.md`](API_REFERENCE_image-edit-area-multiref.md)
🔁 **Irmãos:** [`../image-edit-nano-banana-2/`](../image-edit-nano-banana-2/) e [`../image-edit-seedream/`](../image-edit-seedream/) editam a foto **inteira** por instrução (sem máscara).

---

## Por que esta arquitetura (e não a do guia)

O guia de referência descreve a versão **local**: Flux.1 Fill dev + Flux Redux dev, com 10 `StyleModelApply`
encadeados. Por API isso **não existe numa chamada só**. A pesquisa (verificada no código do ComfyUI, commit
`f1072eb`, 2026-10-03) mostrou:

| Nó de API | Máscara? | Referências |
|---|---|---|
| `OpenAIGPTImageNodeV2` (GPT Image 1…2.5) | ✅ mas **só com 1 imagem** (`Cannot use a mask with multiple image`) e é só orientação | até 16 |
| `FluxProFillNode` / `FluxEraseNode` | ✅ | 0 (só a imagem base) |
| `GeminiNanoBanana2V2` / `GeminiImage2Node` (Nano Banana 2 / Pro) | ❌ | **até 14** |
| `ByteDanceSeedreamNodeV3` (Seedream 4.x/5.0) | ❌ | 10 (14 no 5.0 lite) |
| `Flux3ImageNode` · `Flux2ImageNode` | ❌ | 10 · 8 |

Então o grafo faz a máscara **fora do modelo**:

```
① BASE + máscara ──► ④ ✂️ Inpaint Crop (1:1, contexto 2×) ──┬──► Image 1  (recorte limpo)
                                                             └──► mapa magenta ──► Image 2  (ONDE editar)
③ REF 1…10 ─────────────────────────────────────────────────────► Image 3…12
② regras + "o que fazer" + "papel das refs" ───────────────────► prompt
                                ⑤ Nano Banana 2 (nuvem, paga) ──► recorte editado
⑥ ✂️ Inpaint Stitch (cola só a área, borda suavizada) ──► 🛡️ trava suave (> 88 px da área = pixel ORIGINAL) ──► Save
```

A **trava** existe por um caso medido: quando o quadrado de contexto não cabe na foto, o Inpaint Crop acolchoa a
imagem e a suavização do Stitch vazava para dentro da borda (~20 px a 1:1, até ~42 px com o recorte ampliado). A
composição final contra a original zera isso: `GrowMask` de `expand + 2 × blend` = 72 px, depois um desfoque de 16 px
(`ImageBlur`) para a transição não ficar seca. Além de **88 px** da área pintada, o pixel é **idêntico** ao original.
O cliente de script ainda reduz o contexto sozinho quando o quadrado não caberia, e aí o acolchoamento nem acontece.
Todos os casos testados (meio, cantos, borda, área grande, só o contorno, sem máscara, 1001×777, cinza, RGBA, até
6000×4000) deram **0 pixels alterados** fora da zona.

> "Original" = a foto **como o ComfyUI a decodificou**. Na interface, JPEG/WebP podem diferir ±1–3 níveis de outros
> decodificadores; para fidelidade bit a bit com o arquivo, suba **PNG RGB** (o cliente de script já converte).

## Pré-requisitos

- ComfyUI local rodando: num terminal, **`comfyui`** (sobe em primeiro plano em `http://127.0.0.1:8188`; **Ctrl+C
  encerra**; `COMFY_PORT=8189 comfyui` para outra porta). Instalação reproduzível em
  [`scripts/install_comfyui_local.sh`](scripts/install_comfyui_local.sh): Python 3.13, torch **CUDA 13.0** (torch CPU
  sem GPU NVIDIA; reinstala se a variante instalada for a errada), comando global em `~/.local/bin/comfyui`. Sem GPU ou
  sem CUDA, o `comfyui` sobe sozinho com `--cpu`. A GPU só acelera os nós de imagem: `ComfyUI/models/` não tem pesos e
  **nenhum modelo de IA roda localmente**. Validado no ComfyUI `f1072eb0` (0.38.0); `COMFY_REF=f1072eb0` fixa essa versão.
- Conta em **platform.comfy.org** com créditos.
- Para script: chave em `~/ComfyUI/secrets.env` → `COMFY_ORG_API_KEY=...` (`chmod 600`, **nunca** commitar).

## Setup

```bash
cd workflows-api/image-edit-area-multiref && bash setup.sh
```

O script confere o servidor, **instala o ComfyUI-Inpaint-CropAndStitch** se faltar (pede restart), confere os
16 nós no `/object_info` (com `python_module` não-nulo), cria o symlink do painel *Workflows* e avisa se a
chave de script está faltando. Não grava segredo.

## Como usar (interface, `http://127.0.0.1:8188`)

1. *Workflows* → `api/image-edit-area-multiref/image-edit-area-multiref.json`.
2. **① BASE**: suba a foto → **botão direito → Open in MaskEditor** → pinte a área **inteira** (preenchida, não só o contorno) → **Save**.
3. **② O QUE FAZER**: troque `<DESCREVA AQUI…>` (inglês funciona melhor; português também é aceito).
4. **③ REF 1…10** (opcional): carregue a imagem e **`Ctrl+B`** para ligar o nó (roxo = desligado).
   **Em ordem, sem pular**: o nó descarta slots vazios e renumera as imagens, e aí o texto do passo 5 não bate.
5. **② PAPEL DE CADA REFERÊNCIA**: `Image 3` = REF 1, `Image 4` = REF 2, … Apague as linhas não usadas.
6. **Settings → User → Sign in** (1ª vez) e **Run**.

O workflow tem 4 notas no topo: **LEIA PRIMEIRO**, **Do guia para a API** (o que mudou e o que o guia
erra), **Ajustes finos + problemas** e **Rodar por script**. Os nós verdes são onde você mexe, os amarelos são o
texto que vai para a IA, o azul é o único que custa crédito e os sem cor rodam sozinhos na máquina (pixels, sem IA).

## Como usar (script, headless)

```bash
PY=~/ComfyUI/.venv/bin/python
# 1) teste o encanamento SEM IA e SEM crédito (a área volta pintada de magenta):
$PY scripts/comfy_client.py --base sala.jpg --mask mascara.png --simular
# 2) para valer:
$PY scripts/comfy_client.py --base sala.jpg --mask mascara.png \
    --ref sofa.jpg --ref tecido.jpg \
    --edit "Replace what is inside the edit area with the sofa from Image 3, upholstered in the fabric of Image 4." \
    --roles "- Image 3: the exact sofa (shape, legs, proportions).\n- Image 4: fabric texture and color only."
```

`--mask`: P&B, **branco = área**, mesma proporção da foto (sem `--mask`, vale a transparência de um PNG); a orientação EXIF
é respeitada. Com `--ref`, `--roles` é **obrigatório**. Saída padrão: `~/ComfyUI/output/inpaint-multiref/script/`. O servidor
vem de `--server`, senão `COMFY_SERVER`, senão `COMFY_HOST:COMFY_PORT` (as mesmas variáveis do `comfyui`). Opções:
`--resolution 1K|2K|4K` · `--crop-device auto|gpu|cpu` (auto = GPU se o servidor estiver em CUDA) ·
`--lite` · `--thinking MINIMAL|HIGH` · `--context` · `--expand` · `--blend` · `--seed` · `--salvar-no-servidor` ·
`--export-api grafo.json` (grava o grafo final sem a chave e sai). A sequência REST + WebSocket está detalhada no
[Card de API](API_REFERENCE_image-edit-area-multiref.md#cliente-headless-rest--websocket).

## Parâmetros não-óbvios

| Onde | Parâmetro | Padrão | Por quê |
|---|---|---|---|
| ④ Inpaint Crop | `output_target_width/height` | `1024` | **Igual à resolução do modelo** (1K→1024, 2K→2048, 4K→4096) e **quadrado** |
| ⑤ Nano Banana 2 | `aspect_ratio` | `1:1` | O recorte é 1:1. Com `auto`, o modelo pode reenquadrar e a recolagem desalinha |
| ④ Inpaint Crop | `context_from_mask_extend_factor` | `2.0` | Contexto em volta da área: ajuda a casar luz e perspectiva |
| ④ Inpaint Crop | `mask_expand_pixels` / `mask_blend_pixels` | `8` / `32` | Engorda a máscara e suaviza a costura (o "feathering" do guia); o efeito visível é menor que os números |
| ④ Inpaint Crop | `mask_fill_holes` | `false` | A trava usa a máscara crua: encher buracos no recorte faria a trava desfazer o miolo. **Pinte a área preenchida** |
| ⑥ 🛡️ limite | `GrowMask.expand` + `ImageBlur` | `72` + `16` | **expand ≥ mask_expand + 2 × mask_blend**; se for menor, a trava corta a borda suavizada. O desfoque evita costura seca; a garantia vale além de expand + 16 px |
| ④ Inpaint Crop | `device_mode` | `gpu (much faster)` | Recorte/recolagem na GPU (pixels, sem IA). Sem GPU, o `comfyui` sobe com `--cpu` e o nó roda na CPU; ali `cpu (compatible)` é mais rápido (o script escolhe sozinho) |
| ④ mapa | `ImageBlend.blend_factor` / `EmptyImage.color` | `0.45` / magenta | Opacidade e cor do mapa (Image 2). Se trocar a cor, troque também nas regras |
| ⑤ Nano Banana 2 | `thinking_level` | `HIGH` | Melhor perspectiva, oclusão e luz (mesmo preço no badge) |
| ⑤ Nano Banana 2 | `seed` | `randomize` | O seed **não é determinístico** no Gemini (*best effort*); cada Run gera uma variação nova e é cobrado |

## Validação (no primeiro uso)

1. `bash setup.sh` → 16/16 nós `ok`.
2. Script com `--simular` → o PNG volta com a área **em magenta** e o resto **idêntico**.
3. Interface: carregue foto + máscara e rode **sem** login → todos os nós locais rodam e o ⑤ para com
   `Unauthorized: Please login first` (nada é cobrado). Confira o **👁️ o que a IA recebe**.
4. Faça login e rode **1×** em 1K, com uma referência. Confira o **👁️ saída crua** e o resultado final.

## Troubleshooting

| Sintoma | Causa | Correção |
|---|---|---|
| `Unauthorized: Please login first` (401) | sem login ou chave | interface: *Sign in*; script: `COMFY_ORG_API_KEY` |
| `402` / créditos | conta sem saldo | platform.comfy.org → Credits |
| Foto volta idêntica (e cobrou) | máscara não pintada | MaskEditor → pinte → **Save** (o script recusa máscara vazia antes de cobrar) |
| Nó vermelho `InpaintCropImproved` | custom node ausente | `bash setup.sh` e reinicie |
| Nó vermelho `GeminiNanoBanana2V2` | ComfyUI < 0.38 | `git pull` + requirements |
| Papéis das referências trocados | slot pulado | preencha REF 1, 2, 3… em ordem |
| Magenta no resultado | o modelo copiou o mapa | rode de novo; reforce "never paint magenta" |
| Só o contorno mudou | pintou só a borda | pinte a área **preenchida** |
| Costura visível / "colado" | contexto ou blend baixos | `context_from_mask_extend_factor` 2,5–3 · `mask_blend_pixels` 48–64 (e suba a trava) |
| Área grande borrada | 1K esticado para a área | `resolution 2K` + alvo do recorte `2048` |
| Script: `sem resposta em 900s` | fila travada ou API lenta | veja a fila em `:8188`; `--timeout` maior |

Mais casos: skill `task-debug-generation`.

## Arquivos

| Arquivo | O que é |
|---|---|
| `image-edit-area-multiref.json` | o workflow (formato UI), **gerado** — não edite à mão |
| `scripts/graph_spec.py` | **fonte única** do grafo: gera o `.json` da UI (`--write-ui`), o grafo API (`build_api_prompt`) e confere tudo contra o `/object_info` ao vivo (`--check`) |
| `scripts/notes/*.md` | o texto das 4 notas do workflow (edite aqui e rode `--write-ui`) |
| `scripts/comfy_client.py` | cliente headless REST + WebSocket |
| `scripts/install_comfyui_local.sh` | instalação do ComfyUI local só-API, idempotente |
| `setup.sh` | verificador + instala o custom node |

## Referências

- Registos CoALA: `knowledge-comfyui-api-nodes` (catálogo, billing) · `knowledge-image-editing` (crop & stitch) · `knowledge-comfyui-api` (API HTTP).
- Código verificado: `comfy_api_nodes/nodes_gemini.py` (`GeminiNanoBanana2V2`, até 14 imagens) · `nodes_openai.py` (máscara só com 1 imagem) · `server.py` (`/upload/mask`, `compare_image_hash`) · `custom_nodes/websocket_image_save.py` · `protocol.py` (`BinaryEventTypes`).
- docs.comfy.org: *api-key-integration* (`extra_data.api_key_comfy_org`) · *comms_messages* (eventos do WebSocket) · *partner-nodes/pricing*.
- Templates oficiais usados como base de serialização: `template_product_placement.json`, `api_google_nano_banana2_image_edit_continuation.json`, `basic_mask_operations_and_compositing.json`.
