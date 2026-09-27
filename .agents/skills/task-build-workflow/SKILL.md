---
name: task-build-workflow
description: >-
  Procedimento para montar ou adaptar um workflow de vídeo no ComfyUI: partir de um template, resolver missing
  nodes, mapear modelos locais, montar a cadeia WanVideoWrapper (I2V/T2V), aplicar low-VRAM e Context Windows,
  e exportar JSON + ficha de reprodução. Use ao "montar/criar/adaptar um workflow", "ligar os nós", "fazer o
  grafo do SCAIL-2/Wan" — mesmo sem citar a skill. O conhecimento detalhado está nos registos CoALA
  knowledge-comfyui-workflows e knowledge-scail2 (memória CoALA local).
metadata:
  version: 0.1.0
  type: task
---
# Tarefa — Montar/Adaptar um Workflow

Procedimento prático. O detalhe de nós/parâmetros vive nos registos CoALA `knowledge-comfyui-workflows`
(e `knowledge-scail2` p/ SCAIL-2) — recupere conforme o passo (`coala.py search "<termos>" --tags <skill>`).

## Quando usar
"Montar/criar/adaptar workflow", "fazer o grafo", "ligar os nós", "preparar o JSON do SCAIL-2/Wan I2V".

## Procedimento
1. **Parta de um template** (não do zero): `Workflow → Browse Templates` (checa/baixa modelos) ou um example do
   `kijai/ComfyUI-WanVideoWrapper`. Arrastar um PNG/mp4 gerado recarrega o grafo.
2. **Resolva missing nodes** (vermelhos): Manager → "Install Missing Custom Nodes", reinicie, atualize o
   navegador. Ainda vermelho = erro de import (veja o terminal).
3. **Mapeie modelos locais**: dropdown vazio = arquivo na pasta errada ou falta refresh. Confira `models/<subpasta>`
   e a base model dos LoRAs (→ CoALA `knowledge-runpod-provisioning` p/ os paths exatos).
4. **Monte a cadeia** (→ CoALA `knowledge-comfyui-workflows`): Model Loader → Sampler → Decode → VHS_VideoCombine;
   T2V usa EmptyEmbeds, **I2V** usa ImageToVideoEncode + ClipVisionEncode. SCAIL-2: adicione SAM 3.1 +
   `Create SCAIL-2 Colored Mask` (máscara obrigatória).
5. **Parâmetros** (→ CoALA `knowledge-scail2`): euler/simple, 6–8 steps, **cfg=1**, shift 1, 81 frames, dims ÷32. LightX2V lora ativa.
6. **Vídeo longo**: `WanVideoContextOptions` (81 / stride 4 / overlap 16) ou `scail-auto-extend`.
7. **Low-VRAM se preciso**: block swap (20→40) → fp8 → GGUF → menos frames. (→ `task-debug-generation` p/ OOM.)
8. **Organize**: Groups titulados, Get/Set, Subgraphs p/ blocos reusáveis.
9. **Valide com Partial Execution** (rode só o ramo do sampler) e Preview no meio.
10. **Exporte**: salve o **JSON** (Workflows → Export) com nome `AAAAMMDD-proposito-vN.json` em `workflows-cloud/`; p/
    automação use "Save (API Format)". Registre a ficha de reprodução (modelos+hash, custom nodes, versão, seed/size/sampler/steps/cfg).

## Gotchas
- O UI-JSON **não roda** no `/prompt` (precisa do formato API).
- Metadados de mp4 somem em redes sociais → sempre salve o JSON.
- Wan 2.2 = dois modelos (high+low noise) → dois loaders + dois LoRA selects.

## Referências
- CoALA `knowledge-comfyui-workflows`, `knowledge-scail2`; `docs/workflow-guide.md`.

## registo de aprendizado (memória CoALA local)
1. O workflow rodou e gerou o esperado? Só então persista.
2. Persista: arranjo de nós que funcionou, default que mudou, incompatibilidade, template bom. Ignore o óbvio/volátil.
3. Registe na memória CoALA local (`coala.py add --type episodic`, com data/fonte). Destile no corpo se estável (`version++`). Nova área → a memória CoALA local (`coala.py add`).
4. Diff git para revisão. Salve o JSON reusável em `workflows-cloud/` (self-hosted) — ou empacote em `workflows-api/` se for por API.
