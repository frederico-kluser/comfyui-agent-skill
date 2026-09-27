---
name: task-package-workflow-project
description: >-
  Empacota um workflow entregável como um "projeto" versionado em workflows-cloud/<nome>/ (self-hosted GPU)
  ou workflows-api/<nome>/ (API online, sem GPU), contendo o <nome>.json (ComfyUI), um README.md de
  configuração e um setup.sh (provisiona o RunPod, ou instala os nós/chaves de API). Use sempre que o pedido
  for "criar um workflow para X", "empacotar/entregar um workflow",
  "montar um projeto de workflow" ou disponibilizar um pipeline pronto para o pod — mesmo sem citar
  a skill. Adapta um exemplo known-good (não escreve JSON do zero). Difere de task-build-workflow
  (que monta o grafo no ComfyUI); esta EMPACOTA o bundle no repo.
metadata:
  version: 0.2.0
  type: task
---
# Tarefa — Empacotar um Projeto de Workflow

Entrega um workflow como **bundle reproduzível** no repo: uma pasta por projeto com o grafo, as
instruções e o provisioning. O usuário roda o `.sh` (no pod RunPod p/ bundles **GPU**, ou local p/ bundles
**API**), abre o `.json` e usa.

## Quando usar
"Criar um workflow para <tarefa>", "empacotar/entregar um workflow", "montar um projeto de workflow",
"deixar pronto para subir no pod". Para apenas montar/depurar o grafo no ComfyUI (sem empacotar) →
`task-build-workflow` / `task-debug-generation`.

## Contrato da pasta (obrigatório) — escolha a pasta pelo destino da inferência
- **`workflows-cloud/<nome>/`** — self-hosted: o modelo roda numa **GPU alugada** (RunPod).
- **`workflows-api/<nome>/`** — **API online**: o modelo roda num provedor hospedado (fal/partner); **sem GPU**.
```
workflows-{cloud,api}/<nome-do-projeto>/   # kebab-case; o nome descreve a tarefa (ex.: person-swap-scail2)
├── <nome-do-projeto>.json        # workflow ComfyUI (formato UI, carregável arrastando)
├── API_REFERENCE_<wf>.md         # (recomendado, sobretudo em bundles-API) cards por nó: inputs/params/seed gates
├── README.md                     # Card Informativo (tabela) + seções padronizadas (pré-req, setup, como usar, parâmetros, validação, troubleshooting, refs)
└── setup.sh                      # cloud: nodes + modelos + .json (root no pod) · api: nó fal + grava FAL_KEY do ambiente + .json
```

## Procedimento
1. **Roteie o conhecimento** (via `project-router`): identifique a técnica e recupere o registo CoALA
   certo (`knowledge-scail2`, `knowledge-comfyui-workflows`, etc.). Não reinvente o que já está neles.
2. **Adapte um exemplo known-good** — NÃO escreva o JSON do zero (os docs avisam: JSON à mão é frágil).
   **Procure primeiro nos templates oficiais JÁ INSTALADOS** (não precisa baixar nada):
   `…/site-packages/comfyui_workflow_templates_{core,media_api,media_image,media_video,media_other}/templates/*.json`.
   Achar a base de qualquer nó: `grep -rl "<NodeType>" …/comfyui_workflow_templates*/templates/`.
   Só se não houver, baixe de fora (ex.: `kijai/ComfyUI-WanVideoWrapper/example_workflows/…` via `gh api` → `base64 -d`).
   Para bundles com **N blocos repetidos**, gere o JSON por **script Python** (builder de nós/links/grupos) em vez de
   editar à mão — mas a **ordem dos `widgets_values` tem que ser copiada de um template oficial**: o frontend intercala
   `control_after_generate` **logo depois do `seed`**, fora da ordem declarada no `/object_info`, e errar isso embaralha
   os widgets **em silêncio**. Valide com `python3 -c "import json;json.load(...)"`.
3. **Escreva o `setup.sh`** como fork focado de
   `task-launch-runpod-pod/scripts/provisioning.sh` (antes em `knowledge-runpod-provisioning`): só os custom nodes e modelos
   QUE ESTE workflow usa; garanta pré-condições (ex.: ComfyUI nightly p/ SCAIL-2); baixe o próprio `.json`
   do repo público para `ComfyUI/user/default/workflows/`. Rode `bash -n setup.sh`.
4. **Escreva o `README.md`** (estrutura padrão). Comece com o **Card Informativo** — tabela limpa no topo:
   `🎯 Faz · 🧠 Técnica · 🎮 GPU/VRAM · 📥 Entrada · 📤 Saída · 🧩 Modelos · 🟢/🟡 Status` (+ `🧱 Requer` só se
   houver pré-condição dura, ex.: ComfyUI nightly). Depois, **na mesma ordem em todos os projetos**: pré-req
   (GPU/VRAM → CoALA `knowledge-runpod-infra`); setup; **como anexar os inputs** (qual nó recebe o vídeo, qual recebe a
   foto; passos manuais como gerar máscara ou clicar no `PointsEditor`); parâmetros não-óbvios (tabela); **passos
   de validação no pod**; troubleshooting (tabela) → `task-debug-generation`; referências. Referencie os registos
   CoALA; não duplique o conteúdo deles.
5. **Registre no catálogo**: adicione o projeto à lista certa (`workflows-cloud/` ou `workflows-api/`) no `README.md` raiz (e, se virar
   um tipo recorrente, uma cadeia no `catalog.md`).
6. **Valide** (estrutural agora; funcional no pod/primeiro load). Checagem barata que pega quase tudo:
   JSON parseia · todo `link` aponta para nós existentes · todo `input.link` existe no array `links` ·
   todo `type` existe no `/object_info` (exceto `MarkdownNote`, frontend-only, que **não** aparece lá) ·
   `len(widgets_values)` bate com o do mesmo tipo nos templates oficiais · `bash -n setup.sh` · sem segredos no `.sh`.

## Gotchas
- **Honestidade:** marque o `.json` como rascunho a validar no pod quando a técnica for nova/instável
  (ex.: SCAIL-2). Não prometa "runnable" sem teste — explique a validação no README.
- **Sem tokens** no `setup.sh` (lê `HF_TOKEN`/`CIVITAI_TOKEN`/`FAL_KEY` do ambiente). Nunca versione segredos.
- **Bundle-API:** o Card troca `🎮 GPU/VRAM` por `💳 Custo/billing` + `🔌 Provedores/Nós`. Conhecimento: CoALA `knowledge-comfyui-api-nodes`.
  - rota **fal**: o `setup.sh` instala `ComfyUI-fal-API` e **grava a `FAL_KEY` do ambiente** (chaves em `~/ComfyUI/secrets.env`).
  - rota **partner** (créditos comfy.org): **não instala nada e não grava segredo** — a auth é o **login** em `platform.comfy.org`.
    O `setup.sh` vira um **verificador**: servidor no ar → cada nó presente no `/object_info` com **`python_module` não-nulo**
    (200 com corpo vazio = o Manager conhece mas **não está carregado**) → `.json` visível no painel.
- 🐛 **`find` não entra em symlink.** `~/ComfyUI/user/default/workflows/api` costuma ser symlink para `workflows-api/`;
  `find "$WF_DIR" -name x.json` devolve vazio e o script acaba **copiando o `.json` para dentro do próprio repo**.
  Use **`find -L`** e, no fallback, **crie o symlink** em vez de copiar (cópia solta dessincroniza em silêncio).
- **Status honesto no Card:** 🟡 = "grafo validado estruturalmente, **não executado**". Rodar um bundle-API gasta crédito
  de verdade — não prometa 🟢 antes de o usuário rodar.
- **Reuso:** modelos/paths vêm de CoALA `knowledge-runpod-provisioning`; não recopie manifestos divergentes.
- O `setup.sh` roda como **root** no pod (instala apt/git, baixa modelos) — isso é esperado e seguro no pod descartável.

## Referências
- CoALA `knowledge-runpod-provisioning` (manifesto; script base em `task-launch-runpod-pod/scripts/provisioning.sh`),
  CoALA `knowledge-comfyui-workflows` (grafo/JSON),
  `task-build-workflow` (montar o grafo), `task-launch-runpod-pod` (subir o pod).
- Exemplo de referência **atual** (bundle-API partner, com `API_REFERENCE_*.md`): `workflows-api/image-edit-nano-banana-2/`
  e `workflows-api/video-person-swap-seedance-2/`. Exemplos antigos (fal, e self-hosted `workflows-cloud/person-swap-scail2/`)
  foram removidos em 2026-08-03 — recuperáveis no git (commit `e1dd237` e anterior).

## registo de aprendizado (memória CoALA local) (ao concluir)
1. O bundle ficou consistente (JSON válido, `bash -n` ok, README cobre anexar inputs + validação)? Só então persista.
2. Persista: um exemplo-base bom para uma técnica, um ajuste de `setup.sh` que funcionou, um passo manual
   não-óbvio do README, um anti-padrão. Ignore o óbvio/volátil.
3. Registe na memória CoALA local (`coala.py add --type episodic --key "learnings/task-package-workflow-project"`, data + fonte: usuário > inferência). Destile no corpo se recorrente (`version++`).
4. Se a técnica for nova e recorrente, registe o conhecimento na memória CoALA local (`coala.py add`); se faltar procedimento, proponha skill nova como diff (só procedimento — conhecimento fica no CoALA).
5. Diff git p/ revisão humana — não faça merge sozinho.
