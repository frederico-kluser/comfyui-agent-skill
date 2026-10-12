---
name: task-edit-image
description: >-
  Orquestra a edição de uma imagem fim-a-fim: selecionar a região (máscara manual/semântica/automática),
  editar (inpaint por máscara OU instrução textual; local OU por API online com até 10 referências) e recolar
  (Inpaint Stitch + trava de pixels no grafo, ou composição Python). Use sempre que o pedido for editar/alterar/
  retocar uma imagem, trocar ou remover um objeto, mudar cor/fundo, "edite só esta área", "inpaint com
  referências", ou "edite essa foto" — mesmo sem citar a skill. Decide a técnica e a cadeia de registos CoALA;
  termina com o registo de aprendizado na memória CoALA local. Não é para gerar do zero nem para vídeo.
metadata:
  version: 0.2.0
  type: task
---
# Tarefa — Editar uma Imagem (fim-a-fim)

Leva um pedido de edição a um resultado, escolhendo a técnica e orquestrando o conhecimento da memória
CoALA local. Não o duplica — recupere os registos conforme o passo (`coala.py search --tags <skill>`).

## Quando usar
"Edite/altere/retoque a foto", "troque/remova o objeto", "mude a cor/o fundo", "coloque X no lugar de Y",
"edite só esta área usando estas referências".
Selecionar só a máscara → CoALA `knowledge-image-masking`; só montar o grafo → `task-build-workflow`.

## Primeiro: onde roda o modelo
- **Por API (padrão nesta máquina, 8 GB):** o modelo roda no provedor (partner, créditos comfy.org); o ComfyUI local
  (`comfyui`, primeiro plano, Ctrl+C encerra) só faz pixels. Bundles em `workflows-api/` → CoALA `knowledge-comfyui-api-nodes`.
- **Self-hosted (GPU alugada):** Flux Fill/Kontext/Qwen locais → `task-launch-runpod-pod`. Os bundles `workflows-cloud/`
  citados nos registos (`inpaint-region-cropstitch`, `instruction-edit-kontext`, `qwen-image-edit`, `outpaint-extend`,
  `remove-background`) foram **removidos em 2026-08-03** — recuperáveis no git (commit `e1dd237` e anterior).

## Decisão da técnica (escolha a mais direta)
1. **Edição global por instrução, sem máscara** ("deixe noturno", "troque a jaqueta") → API: `workflows-api/image-edit-nano-banana-2/`
   ou `image-edit-seedream/` (6 processos prontos). Self-hosted: Flux Kontext / Qwen-Image-Edit.
2. **Edição cirúrgica de uma região, com ou sem referências** ("troque só este objeto", "ponha este sofá aqui") →
   **máscara + recorte + edição + recolagem + trava**. API: `workflows-api/image-edit-area-multiref/` (até **10 refs**,
   UI anotada + cliente headless). Self-hosted: Inpaint Crop → `InpaintModelConditioning` + KSampler → Inpaint Stitch.
3. **Estender / tirar fundo** → CoALA `knowledge-image-enhance` (por API: `FluxProExpandNode`, `BriaRemoveImageBackground`… — confira o `/object_info`).

## Procedimento (caso 2 — região)
1. **Selecione a região** (→ CoALA `knowledge-image-masking`): MaskEditor (manual, grava no **alfa**: transparente = área),
   SAM3/Florence/Grounding DINO (por texto), ou Impact Pack (rostos/mãos). Pinte a área **preenchida**.
2. **Edite** (→ CoALA `knowledge-image-editing` › crop-stitch):
   - **API:** nenhum nó de API aceita máscara + várias refs → Inpaint Crop **1:1** → mapa magenta da área (Image 2) →
     `GeminiNanoBanana2V2` (`aspect_ratio 1:1`; Image 1 = recorte, 3… = refs) → Inpaint Stitch.
   - **Local:** `Inpaint Crop` → `InpaintModelConditioning` + KSampler (denoise 0.45–0.7, Flux Fill/SDXL-inpaint) → `Inpaint Stitch`.
3. **Recole e trave**: `Inpaint Stitch` + **trava** `GrowMask(máscara crua, expand+2×blend)` → `ImageBlur(16)` →
   `ImageCompositeMasked(original, stitch)` — garante pixel idêntico além de expand+2×blend+16 px. Fora do ComfyUI:
   alpha blend feathered (→ CoALA `knowledge-comfyui-api`).
4. **Valide sem gastar**: grafo com o nó pago trocado por passthrough (`comfy_client.py --simular`) e conferência numpy
   dos pixels fora da zona; o caminho pago **sem chave** dá 401 (valida o grafo, não cobra). Depois 1 execução real
   em 1K. Erros → `task-debug-generation`.

## Gotchas
- Modelo de inpaint dedicado + `InpaintModelConditioning` = denoise<1 sem incoerência. Máscara 100% opaca (#FFFFFF) no Crop&Stitch.
- Área cinza → não use `VAE Encode for Inpainting` com denoise<1. Fidelidade de pixels exata → alpha blend feathered, não seamlessClone.
- **API:** mantenha o recorte e o `aspect_ratio` do modelo **iguais (1:1)** e o alvo do recorte = resolução do modelo
  (1K→1024). Refs **em ordem, sem buracos** (o nó renumera). Mapa magenta só orienta — quem garante é a trava.
- **Acolchoamento:** quadrado de contexto maior que a foto → o recorte acolchoa e a recolagem vaza na borda; limite o
  fator de contexto e mantenha a trava com borda suave.
- **`mask_fill_holes=True` + trava sobre a máscara crua** = buraco de borda dura num contorno pintado → `False`.
- **Foto de celular:** aplique a orientação EXIF antes de mascarar; máscara com outra proporção = recuse, não estique.
- **Sem máscara** o grafo não falha: a IA roda, **cobra** e devolve a foto igual — valide a máscara antes.

## registo de aprendizado (memória CoALA local) (ao concluir)
1. A edição ficou boa (sem bordas/desvio, região coerente)? Só então persista.
2. Persista: técnica/modelo que funcionou por tipo de edição, combinação de máscara+denoise, anti-padrão. Ignore o óbvio/volátil.
3. Registe na memória CoALA local (`coala.py add --type episodic`, com data/fonte). Destile no corpo se recorrente (`version++`). Técnica nova recorrente → a memória CoALA local (`coala.py add`).
4. Diff git p/ revisão — não faça merge sozinho.
