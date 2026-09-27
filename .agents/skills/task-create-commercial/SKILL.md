---
name: task-create-commercial
description: >-
  Pipeline end-to-end para produzir um comercial de vídeo IA: Flux (hero frames) → SCAIL-2/Wan I2V
  (animação) → RIFE (interpolação) → upscale → edição/áudio, com presets 480p (iterar) e 720p (finalizar),
  formatos 9:16 e 16:9 e a estrutura de prompt Wan. Use sempre que o pedido for criar, produzir ou montar
  um comercial, anúncio ou clipe promocional — mesmo sem citar a skill. Orquestra o conhecimento
  (memória CoALA local, chaves knowledge/*) e termina com o registo de aprendizado na memória CoALA local.
metadata:
  version: 0.1.0
  type: task
---
# Tarefa — Criar um Comercial de Vídeo IA

Procedimento para levar um briefing a um comercial entregável. Orquestra o conhecimento da memória
CoALA local (chaves `knowledge/*`); não o duplica — recupere cada registo conforme o passo
(`coala.py search "<termos>" --tags <skill>`).

## Quando usar
"Criar/produzir um comercial", "fazer um anúncio", "gerar um clipe do produto/personagem", "montar a campanha
em vídeo". Para um passo isolado (só workflow, só pod), use a skill específica.

## Pré-requisitos
- Pod ComfyUI no ar com modelos → `task-launch-runpod-pod` (+ CoALA `knowledge-runpod-provisioning`).
- Decisão de GPU/custo → CoALA `knowledge-runpod-infra` (itere 480p na RTX 5090; finalize 720p na A100).

## Procedimento
1. **Briefing → formato**: defina o aspect ratio **no início** do workflow, não no fim. 9:16 (Reels/TikTok)
   720×1280 ou 704×1280; 16:9 (YouTube) 832×480 ou 1280×704. Múltiplos de 32. Clipes de 3–5s por cena.
2. **Hero frames (imagem)**: gere a imagem de referência com **Flux** (licença: schnell/FLUX.2 klein = Apache 2.0,
   comercial livre; dev = non-commercial). A imagem define o "o quê".
3. **Animação (vídeo)**:
   - Personagem com performance → **SCAIL-2** (driving video + máscara colorida) — ver CoALA `knowledge-scail2`.
   - Produto/movimento simples → **Wan 2.1/2.2 I2V** — ver CoALA `knowledge-comfyui-workflows`.
   - V2V (filmagem real como condutor) → Replacement Mode. O prompt descreve **como** se move, não o que aparece.
4. **Interpolação**: RIFE VFI (gere a 16 fps no SCAIL-2 e interpole 2× → ~30fps).
5. **Upscale**: 480p→alvo (4x-AnimeSharp p/ anime, NMKD/SCAX p/ fotorrealismo) via CR Upscale Image.
6. **Edição/áudio**: junte clipes (~5s/81 frames cada) mantendo **mesma imagem de referência + mesmas cores de
   máscara + seed + versão de modelo** entre clipes. Áudio (ex.: Epidemic Sound), montagem (CapCut/DaVinci), CTA/legendas.
7. **Entregar**: exporte o JSON do workflow (não confie em metadados de mp4) + ficha de reprodução. Finalize em
   720p só quando a composição estiver travada em 480p.

## Estrutura de prompt (Wan, 80–120 palavras)
Sujeito + Cena + Movimento + Linguagem de câmera + Atmosfera + Estilo. Inclua ângulo, iluminação, tipo de
movimento, mood. Comece com movimento sutil e aumente a intensidade. Negative: "morphing, warping, distortion,
blurry, low quality, face deformation, flickering".

## Presets (salve 3)
- **preview**: 480p, GGUF/fp8, 6 steps, sem upscale (Mute o ramo).
- **balanced**: 480p + RIFE + upscale 2×.
- **final**: 720p, fp8/fp16, RIFE + upscale, DPO lora ativo.

## Gotchas de produção
- Consistência entre clipes = mesma ref + mesmas cores de máscara + seed travado.
- cfg=1 com LightX2V (senão borra). Máscara colorida obrigatória no SCAIL-2.
- Verifique a licença de cada modelo/LoRA p/ uso comercial (Wan/SCAIL-2 Apache 2.0; Flux dev non-commercial).

## registo de aprendizado (memória CoALA local) (passo obrigatório ao concluir)
1. A tarefa atingiu o resultado (clipe entregue, sem artefatos)? Só persista aprendizados se **SIM**.
2. Identifique o que vale persistir: preset que funcionou, combinação de modelos, prompt eficaz, anti-padrão
   (o que borrou/morfou), gotcha novo. Ignore o óbvio e o volátil.
3. Registe na memória CoALA local: `coala.py add --type episodic --key "learnings/task-create-commercial" --content "… (data + fonte: usuário > inferência)"`.
4. Se a memória acumular padrão estável, destile no corpo desta SKILL.md e incremente `version`.
5. Se emergiu uma **nova área** (ex.: um novo modelo, uma técnica de áudio), invoque a memória CoALA local (`coala.py add`) p/ propor skill nova.
6. **Não** faça merge sozinho: deixe como diff git para revisão humana.
