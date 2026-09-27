# ComfyUI Commercials — RunPod Ops & Agent Skills

Base de conhecimento + sistema de **Agent Skills** para autorar **workflows de vídeo e de edição de
imagem IA** (SCAIL-2, Wan 2.1/2.2, Flux, Flux Fill/Kontext, Qwen-Image-Edit, SAM/inpaint) no **ComfyUI**
e empacotá-los como **bundles prontos para rodar** — por **API online** (Veo 3.1, Kling, Nano Banana, Seedance; sem GPU) ou **self-hosted no RunPod.io** (GPU alugada).

Não é um app: o valor está (1) na pesquisa curada em `docs/`, (2) nas skills em `.agents/skills/` que
injetam esse conhecimento sob demanda, e (3) nos **projetos de workflow** entregáveis em `workflows-api/`
(rodam por API online, sem GPU).

> **Estado atual (2026-08-03):** os bundles entregues são **três**, todos por API em **créditos comfy.org**
> — dois de edição de imagem e um de troca de pessoa em vídeo. A rota **self-hosted** (`workflows-cloud/`,
> GPU RunPod) continua **coberta** pelos registos CoALA `knowledge-runpod-*` + skills `task-launch-runpod-pod`,
> `task-package-workflow-project`, mas **não há bundle GPU versionado no momento**.

> Para **agentes de código** (Claude Code, Cursor, Codex…) a porta de entrada é o `AGENTS.md` +
> `.agents/skills/project-router`. Este README é a porta de entrada para **humanos**.

## Por que existe
Produzir vídeo no ComfyUI/RunPod envolve muito conhecimento não-óbvio e volátil (paths de modelo,
parâmetros de sampler, VRAM/GPU, custom nodes, custo por segundo). Em vez de despejar tudo num
arquivo gigante (que degrada o agente — ETH Zurich, arXiv:2602.11988), o conhecimento vive na
**memória CoALA local** (busca sob demanda) e o procedimento é **fatiado em skills** carregadas sob
demanda (progressive disclosure); tudo **evolui com o uso**, sempre com revisão humana.

## Arquitetura (3 camadas)
1. **`AGENTS.md`** (always-on, mínimo) — comandos e convenções não-óbvias; aponta para o router.
   `CLAUDE.md` é symlink para ele.
2. **`.agents/skills/`** (fonte única; symlink `.claude/skills/`) — skills de **tarefa** (procedural).
   O **conhecimento** (memória semântica) vive na **memória CoALA local**
   (`.agents/comfyui-agent-skill-coala-memory-agent-skill/`): as skills `knowledge-*` foram migradas
   para lá e deletadas em 2026-09-27.
3. **`project-router`** — despacha TODA tarefa para a cadeia de skills certa antes de implementar.

## Estrutura
```
docs/                     # relatórios de pesquisa (a fonte: SCAIL-2, workflows, RunPod, provisioning)
.agents/skills/           # o sistema de skills (catálogo em catalog.md)
  project-router/         #   roteador
  task-*/                 #   tarefas (create-commercial, create-commercial-api, build-workflow, launch-pod,
                          #            debug, package-workflow-project, edit-image)
.agents/comfyui-agent-skill-coala-memory-agent-skill/  # memória CoALA local — TODO o conhecimento
                          #   (chaves knowledge/*: scail2, comfyui-workflows, runpod-infra/-provisioning,
                          #    image-editing, image-masking, comfyui-api, image-enhance, comfyui-api-nodes)
workflows-api/            # bundles que rodam por API online, sem GPU — todos em créditos comfy.org
                          #   (image-edit-nano-banana-2, image-edit-seedream, video-person-swap-seedance-2)
AGENTS.md  ·  CLAUDE.md   # always-on (symlink)
```

## Como usar
**Com um agente** (recomendado): faça o pedido em linguagem natural ("crie um workflow para trocar a
pessoa de um vídeo", "qual GPU para 720p?", "deu OOM"). O `project-router` seleciona as skills e executa.

**Criar um projeto de workflow** (`workflows-cloud/<nome>/` self-hosted, ou `workflows-api/<nome>/` por API): a skill
`task-package-workflow-project` adapta um exemplo known-good e gera o trio `<nome>.json` + `README.md` + `setup.sh`. Cada
README abre com um **Card Informativo** (faz · técnica · GPU/VRAM **ou** custo/billing · entrada · saída · modelos · status)
e segue a mesma ordem de seções.

**Rodar um workflow no RunPod**:
1. Suba um pod ComfyUI (→ skill `task-launch-runpod-pod`).
2. No pod, rode o `setup.sh` do projeto como root (instala nodes + baixa modelos + o `.json`).
3. Abra o ComfyUI (porta 8188), carregue o workflow e siga o README do projeto.

**Rodar um bundle por API** (sem GPU): no ComfyUI local, rode o `setup.sh` do bundle (`workflows-api/<nome>/`).
Os bundles atuais são **100% nós partner (core)** — o `setup.sh` não instala nada e não grava segredo: ele confere
o servidor, verifica os nós no `/object_info` e deixa o `.json` no painel. A autenticação é o **login em
`platform.comfy.org`**; a cobrança é em **créditos comfy.org**. Conhecimento: registo CoALA `knowledge-comfyui-api-nodes`.

## Projetos de workflow
> Legenda de status: 🟢 validado em execução · 🟡 grafo validado estruturalmente, ainda não executado.
> Cada projeto abre com um **Card Informativo** (faz · técnica · custo/billing · entrada · saída · modelos · status)
> no topo do seu README.

### ☁️ Por API online — `workflows-api/` (sem GPU, créditos comfy.org)
| Projeto | O que faz | Provedores/Nós | Billing | Status |
|---|---|---|---|---|
| [`image-edit-nano-banana-2`](workflows-api/image-edit-nano-banana-2/) | **6 edições de foto** num arquivo: roupa · objeto em cena · trocar a pessoa · **me pôr na foto (roupa/pose da cena)** · **me pôr na foto (minha roupa/pose)** · trocar o local + match de luz | `GeminiNanoBanana2` (partner) | comfy.org | 🟡 |
| [`image-edit-seedream`](workflows-api/image-edit-seedream/) | **As mesmas 6 edições**, no outro melhor editor — rode os dois e compare | `ByteDanceSeedreamNode` (partner, 5.0 lite / 4.5) | comfy.org | 🟡 |
| [`video-person-swap-seedance-2`](workflows-api/video-person-swap-seedance-2/) | **Me colocar num vídeo** no lugar de uma pessoa, mantendo pose, roupa, câmera e iluminação. Inclui o fluxo obrigatório de **asset verificado de humano real** | `ByteDance2ReferenceNode` + `ByteDanceCreate{Image,Video}Asset` + `GeminiNode` (partner) | comfy.org | 🟡 |

Os três são **core do ComfyUI**: zero custom node, zero chave de API — só o login em `platform.comfy.org`.

> **Histórico:** os bundles anteriores (fal/`*_fal`, SCAIL-2 self-hosted em `workflows-cloud/`,
> comercial, música, image/video-to-video) foram removidos em 2026-08-03 para consolidar tudo em
> créditos comfy.org. Estão recuperáveis no git — veja o commit `e1dd237` e o anterior a ele.

## Memória evolutiva (e suas salvaguardas)
Skills de tarefa registam aprendizados na **memória CoALA local** (`coala.py add`) ao concluir;
o conhecimento de domínio vive **apenas** nela (chaves `knowledge/*`). Atualização por supersessão
(`--key`), propostas de skill nova como **diff git para revisão humana** — conteúdo gerado por
LLM é rascunho até a curadoria. Só se persiste aprendizado de tarefa que passou nos critérios (estilo Voyager).

## Convenções e segurança
- **API online vs self-hosted:** `workflows-api/` (modelo roda no provedor) · `workflows-cloud/` (você roda em GPU RunPod; sem bundle versionado hoje). Ver registo CoALA `knowledge-comfyui-api-nodes`.
- **Credencial por rota:** nós **partner** (os três bundles atuais) = **login** em `platform.comfy.org`, **sem chave**. Nós `*_fal`/Replicate = chave em `~/ComfyUI/secrets.env` (`chmod 600`), **nunca** `~/.secrets`.
- Modelos vão em `ComfyUI/models/<subpasta>` no Network Volume (`/workspace`). ComfyUI na porta 8188.
- SCAIL-2/Wan destilado (LightX2V): **cfg=1**, 6–8 steps, shift 1; dims **÷32** (SCAIL-2). Itere em 480p, finalize em 720p.
- **Nunca** commitar tokens (`HF_TOKEN`, `CIVITAI_TOKEN`, `.env`). `setup.sh` lê tokens do ambiente, nunca embute.
- Pare o pod ao terminar (cobrança por segundo).

## Mapa de skills
Catálogo completo: [`.agents/skills/catalog.md`](.agents/skills/catalog.md). Convenções de autoria e o
mecanismo de evolução: memória CoALA local (supersessão por `--key`, `doctor`/`backup`; propostas de
skill nova como diff para revisão humana).
