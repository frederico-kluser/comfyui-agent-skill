---
name: task-create-commercial-api
description: >-
  Pipeline ponta-a-ponta para produzir um comercial de vídeo 100% por API ONLINE (sem GPU pesada): protagonista
  sintético ancorado em Nano Banana Pro → keyframe→vídeo com Veo 3.1 → extensão dirigida (Veo handoff / Kling
  nativo / Seedance barato) → ColorMatch → concat ffmpeg. Identity lock por âncora+frase, gramática Veo 3.1,
  rascunho barato Seedance, 16:9/9:16. Use sempre que o pedido for criar/produzir um comercial, anúncio ou clipe
  SEM alugar GPU (na nuvem/por API) — mesmo sem citar a skill. Orquestra o registo CoALA
  knowledge-comfyui-api-nodes e o bundle workflows-api/commercial-ondokai. Para a variante self-hosted (SCAIL-2/Wan em GPU) use task-create-commercial.
metadata:
  version: 0.1.0
  type: task
---
# Tarefa — Criar um Comercial de Vídeo por API (cloud, sem GPU)

Leva um briefing a um comercial entregável usando **modelos hospedados** (Veo 3.1, Nano Banana Pro, Kling, Seedance)
dentro do ComfyUI. A máquina só orquestra — cabe em **8 GB**. Conhecimento dos nós/seed gates/chaves: CoALA `knowledge-comfyui-api-nodes`.
Bundle pronto: **`workflows-api/commercial-ondokai/`** (19 workflows). Variante self-hosted (SCAIL-2/Wan em GPU) → `task-create-commercial`.

## Quando usar
"Criar/produzir um comercial/anúncio/clipe **na nuvem / por API / sem GPU**", "comercial com Veo/Kling", "não quero
alugar GPU". Para um passo isolado (1 cena, 1 edição) use a skill específica.

## Pré-requisitos
- `ComfyUI-fal-API` + **`FAL_KEY`** (Veo 3.1, Nano Banana Pro, Seedance) e **login** comfy.org (nós Kling). KJNodes + VideoHelperSuite.
- Suba o bundle: `cd workflows-api/commercial-ondokai && FAL_KEY=... bash setup.sh`. Chaves em `~/ComfyUI/secrets.env` (nunca `~/.secrets`).

## Procedimento
1. **Formato no início** (não no fim): 16:9 master (1080p). 9:16 Reels → gere nativo onde der; 1:1 **não** é saída oficial do Veo (recorte no post). Clipes de 4/6/8 s por beat.
2. **Âncora de identidade** (`10_ANCORA`): gere o protagonista 1× com `NanoBananaPro_fal` e salve. **Nano Banana Pro não tem seed** → a identidade é travada por **(a)** a imagem-âncora no input `images` de cada cena **e (b)** a frase `<<PROTAGONISTA — ...>>` **idêntica em todos os prompts**. Nomeie figurino/props ("gray hoodie, round glasses"). Rosto real pode ser bloqueado por moderação → use o sintético.
3. **Rascunho barato** (opcional): teste timing/câmera de um beat com `SeedanceImageToVideo_fal` **480p** (`20_FERRAMENTA`) antes de gastar Veo.
4. **Cada cena** = keyframe → vídeo: `NanoBananaPro_fal`(prompt + âncora) → `Veo31_fal`(`first_frame`). Cena com transição = **morph** (2 keyframes → `first_frame`+`last_frame`). Cenas estáticas = só o keyframe.
5. **Cena longa (>8 s)** → extensão **dirigida** (ação nova por segmento): **A** Veo handoff (`GetImageRangeFromBatch(-1)` → próximo Veo), **B** Kling nativo (`KlingVideoExtendNode` encadeia `video_id`), **C** Seedance barato (`end_image`). Arquivos `40/41/42`.
6. **Cor**: `ColorMatch` (`hm-mkl-hm`, **0.4**) de **cada** clipe contra **UM** hero frame canônico — não contra o clipe anterior (evita deriva acumulada).
7. **Áudio + montagem**: ⚠️ a cadeia `LoadVideoURL→CreateVideo` extrai **só frames** → perde o áudio nativo do Veo; baixe a `video_url` original p/ manter. Concatene: `ffmpeg -f concat -safe 0 -i lista.txt -r 24 -c:v libx264 -pix_fmt yuv420p ondokai.mp4`. 16:9→9:16: `crop=ih*9/16:ih,scale=1080:1920`.
8. **Entregar**: exporte os `.json` + a **render ledger** (`| shot | modelo+versão | seed | aspect | dur | prompt | hero-frame |`). Finalize 1080p só com a composição travada (teste em 480p/720p).

## Gramática de prompt Veo 3.1 (cinematografia primeiro)
`[plano + movimento de câmera + lente] + [sujeito + figurino] + [ação + física/timing] + [cenário + hora] + [estilo] + [áudio]`.
**UM movimento de câmera por plano** (dolly/truck/orbit/pedestal/push-in/locked-off); **varie por beat**. `Veo31_fal`
**não tem campo negative** → negativos em prosa (*no morphing, face morphing, flicker, camera shake, identity drift, changing wardrobe*),
ou use um nó com negative (`KlingImage2VideoNode`, `SeedanceProImageToVideo_fal`). A gramática completa está no `01_GUIA` do bundle.

## Custo: itere barato, finalize caro
Rascunho → Seedance 480p; iteração → endpoints **warm** (Nano Banana Pro/Kontext ~30–60 s); final → Veo 3.1 1080p. fal cobra por chamada
e os nós `*_fal` **bloqueiam sem barra** (cold-start pode ficar minutos em `IN_QUEUE` e ainda completar).

## Gotchas de produção
- Consistência = âncora no `images` + frase `<<PROTAGONISTA>>` idêntica + figurino nomeado. Cor = ColorMatch vs UM hero frame.
- `NanoBananaEdit_fal` (Gemini 2.5) é **fraco** ("devolve a foto") → use `NanoBananaPro_fal` (Gemini 3).
- Seed gates: ver CoALA `knowledge-comfyui-api-nodes` (Veo/Nano Banana **sem seed**; Seedance **tem**).
- SCAIL-2 **não tem nó** Comfy/fal; substituto por API = **Wan 2.2 Animate** (`Wan2214b_animate_{move,replace}_character_fal`).

## registo de aprendizado (memória CoALA local) (passo obrigatório ao concluir)
1. O comercial saiu coerente (identidade estável, sem morph, cor casada)? Só persista se **SIM**.
2. Persista o que vale: um prompt Veo eficaz, uma combinação de câmera por beat, um método de extend que funcionou, um anti-padrão (o que morfou/derivou), um cold-start medido, um seed gate novo. Ignore o óbvio/volátil (preço de hoje).
3. Registe na memória CoALA local (`coala.py add --type episodic --key "learnings/task-create-commercial-api" --content "… (data + fonte: usuário > inferência)"`). Se acumular padrão estável, destile no corpo e `version++`.
4. Nó/modelo novo ou área nova → a memória CoALA local (`coala.py add`) (suplantar a chave `knowledge/knowledge-comfyui-api-nodes` ou propor skill).
5. **Não** faça merge sozinho: deixe como diff git p/ revisão humana.
