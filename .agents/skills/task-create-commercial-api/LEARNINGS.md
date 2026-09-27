> **MEMÓRIA APOSENTADA (2026-09-27):** o conteúdo deste ficheiro foi migrado para a memória CoALA local do repositório (`.agents/comfyui-agent-skill-coala-memory-agent-skill/`). Fica só como **fonte histórica** — não escrever mais aqui. Aprendizado novo: `python3 .agents/comfyui-agent-skill-coala-memory-agent-skill/scripts/coala.py add --type episodic --content "…"`.

# LEARNINGS — task-create-commercial-api

> Memória episódica desta tarefa. Append-only (data + fonte: usuário > inferência).
> `meta-consolidation` deduplica/promove/poda. Promova ao corpo o que virar padrão estável.

## 2026-06-20 — Gênese: pipeline do comercial Ondokai por API
- **Contexto**: replicado do `5-comercial-ondokai/` da máquina local (19 workflows) → bundle `workflows-api/commercial-ondokai/`.
- **Aprendizado**: (1) Identidade do protagonista sintético = âncora no input `images` + frase `<<PROTAGONISTA>>` idêntica em todo prompt (Nano Banana Pro **não tem seed**). (2) Cena = `NanoBananaPro_fal`(keyframe) → `Veo31_fal` (8s/16:9/1080p, **24 fps**); morph = 2 keyframes → `first_frame`+`last_frame`. (3) Extend **dirigido** (ação nova/segmento): A=Veo handoff (`GetImageRangeFromBatch(-1)`), B=Kling `video_id` encadeado, C=Seedance barato (`end_image`). (4) `Veo31_fal` **não tem campo negative** → negativos em prosa. (5) `LoadVideoURL→CreateVideo` perde o áudio do Veo (baixe a URL original). (6) Cor = `ColorMatch` (hm-mkl-hm, 0.4) contra **UM** hero frame, não o clipe anterior. (7) Rascunho barato = Seedance 480p antes de gastar Veo.
- **Fonte**: usuário (workflows + GUIA/GLOSSARIO da máquina local).
- **Ação**: validar geração real com `FAL_KEY`; promover presets de prompt Veo que funcionarem; SCAIL-2 não tem API → substituto = Wan 2.2 Animate.

_(novas entradas abaixo)_
