---
name: project-router
description: >-
  Roteia TODA tarefa neste repo (ComfyUI, SCAIL-2, Wan 2.1/2.2, Flux, RunPod) para as
  skills certas ANTES de qualquer implementação — mesmo que o usuário não cite skills.
  Use para qualquer pedido: gerar vídeo/imagem, montar/adaptar workflow, subir pod,
  escolher GPU, estimar custo, baixar modelos, debugar geração ou criar comercial.
  Não é fonte de conhecimento — ela despacha; o conhecimento vive na memória CoALA
  local (chaves knowledge/*), o procedimento nas skills task-*.
metadata:
  version: 0.1.0
  type: router
---
# Project Router

Ponto de entrada único. O procedimento deste projeto está fatiado em skills de tarefa
carregadas sob demanda (progressive disclosure); o **conhecimento semântico vive na memória
CoALA local** (chaves `knowledge/*` — skills `knowledge-*` deletadas em 2026-09-27). Sua
função: montar a cadeia certa de skills + registos CoALA e carregá-los ANTES de agir, para
não reler docs nem escanear o repo.

## Protocolo (execute antes de qualquer trabalho)
1. **Classifique a tarefa**: domínio(s) tocado(s) — SCAIL-2 / ComfyUI / RunPod-infra /
   API-online (fal/partner) / provisioning / comercial; tipo — gerar / montar workflow / setup / debug / decisão de custo;
   complexidade (passo único vs pipeline).
2. **Consulte o catálogo** (`catalog.md` → "Cadeias típicas") e selecione as skills/registos relevantes.
3. **Monte a cadeia**: ordem + o que pode rodar em paralelo via subagentes (contexto isolado
   para análise pesada, p.ex. ler um doc inteiro ou escanear `workflows-api/`/`workflows-cloud/`).
4. **Carregue o conhecimento**: skills de tarefa → leia os `SKILL.md`; conhecimento de domínio →
   memória CoALA local (`coala.py search "<termos>" --tags <skill>` / `coala.py recall "<tarefa>"`;
   docs `docs/` de nível 3 só se o registo não bastar).
5. **Execute** a cadeia.
6. **Feche**: garanta que cada skill de tarefa registou o aprendizado na memória CoALA local
   (`coala.py add --type episodic`; propor skill nova também via `coala.py add`).

## Cadeias típicas (resumo — ver `catalog.md`)
Notação: `task-*` = skill viva; `CoALA knowledge-*` = registo na memória CoALA (chave `knowledge/<skill>`).
- Criar comercial → `task-create-commercial` (orquestra CoALA `knowledge-scail2` + `knowledge-comfyui-workflows` + provisioning).
- Criar comercial **por API / sem GPU** → `task-create-commercial-api` + CoALA `knowledge-comfyui-api-nodes` (bundle `workflows-api/commercial-ondokai/`).
- Animar **imagem→vídeo** ou transformar **vídeo→vídeo** por API (Veo/Kling/Seedance/Wan 2.2 Animate/Runway Aleph) → CoALA `knowledge-comfyui-api-nodes` (bundles `workflows-api/image-to-video-api/` · `video-to-video-api/`).
- Subir pod / baixar modelos → `task-launch-runpod-pod` + CoALA `knowledge-runpod-provisioning` + `knowledge-runpod-infra`.
- Montar/adaptar workflow → `task-build-workflow` + CoALA `knowledge-comfyui-workflows` (+ `knowledge-scail2`).
- Debug de geração → `task-debug-generation` + CoALA `knowledge-comfyui-workflows`.
- Criar/empacotar um projeto de workflow → `task-package-workflow-project` (adapta exemplo + gera setup.sh) + o registo CoALA da técnica.
- Editar imagem (inpaint/instrução/trocar objeto/fundo) → `task-edit-image` + CoALA `knowledge-image-editing` + `knowledge-image-masking` (+ `knowledge-comfyui-api` p/ código/API, `knowledge-image-enhance` p/ upscale/relight/fundo).
- Rodar/montar workflow **por API online** (Veo/Kling/Nano Banana/fal), escolher provedor, custo em créditos, nó fal travado → CoALA `knowledge-comfyui-api-nodes`.
- "Qual GPU / quanto custa" → CoALA `knowledge-runpod-infra`.

## Regras
- Se **nenhuma** skill cobre a tarefa, invoque a memória CoALA local (`coala.py add`) para propor uma nova — não improvise
  conhecimento volátil de cabeça.
- Em **ambiguidade** entre skills/registos, prefira o mais específico do domínio (ex.: SCAIL-2 vence ComfyUI genérico).
- Nunca **pule** o registo de aprendizado na memória CoALA local ao concluir uma skill de tarefa.
- O router **não** implementa nem guarda conhecimento de domínio — ele só despacha. Conhecimento mora
  na memória CoALA local (por quê: mantém o router estável e barato, e o conhecimento curável em um lugar só).

## Evolução
Se você rotear errado (skill errada, faltante ou descrição ambígua), registe na memória CoALA
local (`coala.py add --type episodic --key "learnings/project-router"`) com: a tarefa, a cadeia
escolhida e a que seria correta. A memória CoALA local (supersessão por `--key`) usa esse
registro para refinar as `description` das skills (gatilho de poda quando o erro de roteamento passa
de ~10–20%).