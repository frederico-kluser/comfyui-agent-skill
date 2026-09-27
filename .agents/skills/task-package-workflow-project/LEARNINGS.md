> **MEMÓRIA APOSENTADA (2026-09-27):** o conteúdo deste ficheiro foi migrado para a memória CoALA local do repositório (`.agents/comfyui-agent-skill-coala-memory-agent-skill/`). Fica só como **fonte histórica** — não escrever mais aqui. Aprendizado novo: `python3 .agents/comfyui-agent-skill-coala-memory-agent-skill/scripts/coala.py add --type episodic --content "…"`.

# LEARNINGS — task-package-workflow-project

> Memória episódica desta tarefa. Append-only (data + fonte: usuário > inferência).
> `meta-consolidation` deduplica/promove/poda. Promova ao corpo o que virar padrão estável
> (≥2× ou confirmado pelo usuário). Revisão humana via git diff.

<!-- Formato:
## AAAA-MM-DD — <título>
- **Contexto**: <projeto/técnica>
- **Aprendizado**: <base boa, ajuste de setup.sh, passo manual do README, anti-padrão>
- **Fonte**: usuário | inferência
- **Ação**: promover ao corpo? / nova knowledge skill?
-->

## 2026-06-19 — Primeiro bundle: person-swap-scail2 (probação)
- **Contexto**: empacotar o workflow de troca de pessoa em vídeo (SCAIL-2 Replacement).
- **Aprendizado**: (1) o exemplo SCAIL público do kijai (`wanvideo_2_1_14B_SCAIL_pose_control_example_01.json`,
  67 nós) é **pose-control**, não replacement-específico — a wiring do Replacement (máscara colorida + flag)
  precisa ser conferida no pod. (2) Para anotar um JSON UI sem corromper, **clone um `MarkdownNote` já
  existente** no arquivo e troque id/pos/texto (estrutura garantida). (3) `setup.sh` que baixa o próprio
  `.json` do repo público (`raw.githubusercontent.com/.../main/workflows/<proj>/<proj>.json`) deixa o
  bundle "1 arquivo p/ subir e rodar".
- **Fonte**: inferência (pesquisa via gh api + docs do projeto).
- **Ação**: manter em probação até validar no pod; se o padrão "clonar nó p/ anotar" e "setup baixa o
  próprio json" se repetirem, promover ao corpo da SKILL.md.

## 2026-06-20 — Card Informativo + estrutura uniforme em todos os READMEs
- **Contexto**: padronização dos 7 projetos em `workflows/` (sem alterar `.json`/`setup.sh`).
- **Aprendizado**: (1) Todo README abre com um **Card Informativo** (tabela limpa): `🎯 Faz · 🧠 Técnica ·
  🎮 GPU/VRAM · 📥 Entrada · 📤 Saída · 🧩 Modelos · status` (+ `🧱 Requer` p/ pré-condição dura, ex.: ComfyUI
  nightly). (2) Mesma ordem de seções em todos: Card → Status → Pré-req → Setup → Como usar → Parâmetros →
  Validação → Troubleshooting → Referências. (3) **Não renomear pasta/arquivo do projeto**: o `setup.sh` baixa
  `…/main/workflows/<proj>/<proj>.json` por URL fixa — renomear quebra o download (logo "distribuição" = melhorar
  catálogo/apresentação, não mover arquivos). (4) Catálogo da raiz agrupado por categoria (Vídeo & Animação ·
  Edição de imagem · Enquadramento & Fundo) com colunas técnica/GPU/status + legenda 🟢/🟡. (5) Onde há JSON de
  API (scail2-native), o README aponta para os `API_REFERENCE_*.md` (cards por nó).
- **Fonte**: usuário (pediu cards informativos + distribuição intuitiva/profissional; escolheu "tabela limpa").
- **Ação**: promovido ao corpo da SKILL.md (Contrato da pasta + passo 4). Convenção estável.

## 2026-06-20 — Split: `workflows/` → `workflows-cloud/` + `workflows-api/`
- **Contexto**: o repo passou a ter duas pastas de bundle, separadas pelo **destino da inferência**: `workflows-cloud/` (self-hosted em GPU RunPod — os 7 projetos originais) e `workflows-api/` (modelo roda num provedor hospedado, fal/partner, **sem GPU**).
- **Aprendizado**: (1) `git mv workflows workflows-cloud` quebra TODA URL fixa `…/main/workflows/<proj>/…` nos `setup.sh` (confirma o learning de 2026-06-19) → corrigido com `sed 's#main/workflows/#main/workflows-cloud/#'` nos `setup.sh` + replace dos 7 nomes de projeto nos `.md`; os dirs runtime `$COMFY/user/default/workflows` **não** mudam. (2) **Bundle-API** difere do contrato-GPU: Card troca `🎮 GPU/VRAM` por `💳 Custo/billing` + `🔌 Provedores/Nós`; `setup.sh` instala `ComfyUI-fal-API` + **grava `FAL_KEY` do ambiente** (sem baixar modelos pesados) e roda **local** (8GB ok), não root-no-pod. (3) bundle-API multi-arquivo (ex.: `commercial-ondokai/` = 19 JSONs) → 1 README de pipeline + `API_REFERENCE_*.md` por nó. (4) `docs/` (relatórios de pesquisa) **não** são editados no rename.
- **Fonte**: usuário (pediu o split + replicar a stack de comercial por API).
- **Ação**: promovido ao corpo (Contrato de 2 pastas + gotcha Bundle-API). Convenção estável.

_(novas entradas abaixo)_

## 2026-06-23 — replace-object & replace-environment: máscara OPCIONAL via grupo em bypass
- **Contexto**: 2 bundles-API novos (espelhados) copiando outfit-swap-api (multi-ref) + mask-edit-cloud (composite). Cada um com 4 workflows: 2 só-prompt + 2 com seleção de área manual; o usuário pediu "se eu não selecionar a área, funciona igual".
- **Aprendizado**: (1) Para "com OU sem máscara no MESMO workflow", junte `Conforma(ImageResizeKJ)` + `GrowMaskWithBlur` + `ImageCompositeMasked` num grupo e **entregue em `mode:4` (bypass) por padrão** → rodar sem fazer nada = edição da imagem inteira (= os só-prompt); o usuário ATIVA (selecionar os 3 nós + `Ctrl+B`) e pinta no MaskEditor p/ limitar à região. (2) **Truque do bypass**: ligue `ImageCompositeMasked` com `destination`=**edição completa**, `source`=**original**, `mask`=**`mask_inverted`** → bypass devolve `destination` (edição completa) e, ativo, cola o original FORA da área pintada (só a região pintada muda; resto pixel-idêntico). Regra de uso uniforme: "pinte o que vai TROCAR" (o objeto / o fundo). (3) Nano Banana exige as 2 imagens do MESMO tamanho: `ImageResizeKJ(get_image_size=base)`×2 → `ImageBatch`; Kontext Multi aceita `image_1`/`image_2` separados (sem batch). (4) Para casar no composite, um `ImageResizeKJ` "Conforma" com `keep_proportion=false`, `divisible_by=1`, `get_image_size=base` força o tamanho EXATO da base.
- **Fonte**: usuário (4 workflows, 2 com seleção de área, "funciona igual sem selecionar") + `/object_info` do ComfyUI local.
- **Ação**: probação — se "grupo de máscara opcional em bypass + composite invertido" reaparecer noutro bundle, promover ao corpo da SKILL.md.

## 2026-06-23 — Bundles I2V/V2V: autorar JSON NOVO a partir do `/object_info` (não copiar)
- **Contexto**: `image-to-video-api/` + `video-to-video-api/` — primeiros bundles cujos workflows **não** existiam na máquina do usuário (pedido: "pesquise e crie os melhores"). 17 workflows-modelo + 4 guias.
- **Aprendizado**: (1) Quando não há JSON known-good p/ copiar, **gerar** o UI-JSON por script a partir do schema do `/object_info` é mais confiável que escrever à mão: um builder lê `input`/`input_order`/`output_name` e monta `inputs[]`/`outputs[]`/`widgets_values` na ordem certa, reusando a moldura provada (`LoadImage/LoadVideo → nó → [cadeia] → SaveVideo`). 21/21 passaram parse + integridade de links. (2) `widgets_values` segue a ordem dos inputs (required→optional); **seed com `control_after_generate`** injeta um valor extra (`"fixed"`) logo após o seed — alinhe ou os widgets seguintes deslocam. (3) **Combo dinâmico** (`COMFY_DYNAMICCOMBO_V3`, ex. Vidu/Grok-extend) serializa `key` + valores aninhados; é o único ponto frágil → documente "confira o dropdown model" na MarkdownNote. (4) Validação sem frontend: `json.tool` + resolver todo `class_type` no `/object_info` ao vivo + checar que cada link casa `inputs[dslot].link` e `outputs[sslot].links`. (5) Padrão de saída decide a fiação: fal `*_fal` → URL → `LoadVideoURL→CreateVideo→SaveVideo`; partner → `VIDEO` → `SaveVideo` direto. (6) Cross-ref útil: SCAIL-2 self-hosted (`workflows-cloud/*scail2*`) ↔ `Wan2214b_animate_*_fal` (mesmo objetivo por API).
- **Fonte**: usuário (pediu pesquisar+criar) + inferência (geração via `/object_info`).
- **Ação**: candidato a promover ao corpo — "quando não há exemplo, gere do schema do `/object_info`" complementa o "adapta exemplo known-good". Validar com smoke real (`FAL_KEY`) antes de marcar 🟢.

## 2026-07-10 — `text-to-music-api`: 1º bundle de ÁUDIO; provedor decidido por LICENÇA; script standalone + JSON de template on-disk
- **Contexto**: usuário pediu pasta de geração de música **comercializável** (instrumental/ambient p/ jogo pago na Steam), "só APIs em nuvem" + "vender para sempre mesmo cancelando a assinatura". Ancorou no ACE-Step. Precedido de `/deep-research` (105 agentes) sobre licenças de APIs de música.
- **Aprendizado**: (1) **Não existe node fal/partner de MÚSICA** no ComfyUI (só `ElevenLabs*`=voz e o partner `api_stability_ai_text_to_audio`=Stable Audio, licença revogável). → o bundle-API vira **script standalone** (Node `gerar_trilhas.mjs`, precedente `extract_assets.py`) + **JSON local opcional** (ACE-Step é **core**, roda em ~8GB VRAM, sem custom node). Um bundle-API pode ser **script-primeiro**, sem `ComfyUI-fal-API`. (2) **O provedor é decisão JURÍDICA, não técnica**: mesmo modelo (ACE-Step, **1.5=MIT / v1=Apache-2.0**) — no **Replicate** a ToS §5.1+§9.5 **dá posse do output e sobrevive ao cancelamento** (melhor p/ vender); **local** = licença mais limpa (sem host); **Suno/Udio** em litígio; **Mubert/Beatoven** atrelados à assinatura (reprovados). Doc isso no README/API_REFERENCE com citação. (3) **Templates oficiais ACE-Step já estão on-disk** em `~/ComfyUI/venv/.../comfyui_workflow_templates_media_*/templates/audio_ace_step_*` → `cp` + **Edits cirúrgicos** (tags→preset; `SaveAudioMP3`→`SaveAudio`) bate escrever à mão. (4) **`SaveAudio` = FLAC lossless (1 widget `filename_prefix`)**; `SaveAudioOpus`=OGG; `SaveAudioMP3` **quebra loop perfeito** (encoder padding) → para loop use **WAV/FLAC/OGG, nunca MP3**. (5) `setup.sh` de bundle-script: `npm i` das libs + grava chaves (`FAL_KEY`/`REPLICATE_API_TOKEN`) do ambiente em `secrets.env`; checkpoint local atrás de `DOWNLOAD_CHECKPOINT=1` (não baixa 3.5GB por padrão).
- **Fonte**: usuário (pasta de música comercializável, cloud-only, vender-para-sempre) + `/deep-research` (licenças, fontes primárias) + templates/`/object_info` do ComfyUI local.
- **Ação**: probação — se "bundle script-primeiro + provedor escolhido por licença" reaparecer, promover ao corpo (hoje o contrato assume `<nome>.json` central). Também alimentei `knowledge-comfyui-api-nodes` (seção Música). Falta **smoke real** (gerar 1 faixa com chave) antes de 🟢.

## 2026-07-10 (correção) — MÚSICA por API TEM nós partner clicáveis; e um bundle deve expor um workflow CLICÁVEL, não só script
- **Contexto**: usuário reclamou que "só o `text-to-music-local` funciona e não tem um totalmente API/cloud". Investiguei o `/object_info` ao vivo (1775 nós) + 2ª `/deep-research`.
- **Correção do registro anterior** (que dizia "não existe node partner de música"): **EXISTEM** nós partner de música clicáveis, pré-instalados: **`StabilityTextToAudio`** (Stable Audio 2.5) e **`SoniloTextToMusic`** (Sonilo), categoria `partner/audio/*`, billing comfy.org. Também `Replicate meta/musicgen` via `comfyui-replicate` (mas MusicGen=CC-BY-NC **não-comercial**).
- **Licença (2ª pesquisa, corrige a 1ª)**: a licença **revogável/teto US$1M** do Stable Audio é só dos **pesos self-hosted** (Community License); a **API hospedada** tem ToS diferente que **§4.a CEDE a posse** do output e **sobrevive ao cancelamento** (§12.e) → **comercial-limpo**. `SoniloTextToMusic` = comercial só no tier pago, **sem sobrevivência** (atrelado à assinatura). **Créditos comfy.org não dão direito por si** (ToS do comfy.org define "Output" só como **visual**; áudio é regido pela ToS do provedor).
- **Aprendizado de empacotamento**: um bundle-API cujo usuário navega no **painel Workflows** do ComfyUI DEVE entregar **≥1 workflow `.json` clicável** para o caminho principal — não só um script CLI (o usuário não "acha" o caminho cloud se ele não é um grafo). Aqui: adicionei `text-to-music-cloud.json` (`StabilityTextToAudio`→`SaveAudio` FLAC, adaptado do template `api_stability_ai_text_to_audio.json`). Antes de afirmar "não existe nó X", **grep no `/object_info` ao vivo** (não confie na memória da skill).
- **Fonte**: usuário + `/object_info` ao vivo + 2ª `/deep-research` (ToS Stability §4.a/§12.e, Sonilo, comfy.org, MusicGen CC-BY-NC).
- **Ação**: corrigi `knowledge-comfyui-api-nodes` (seção Música). Promover a regra "bundle-API entrega workflow clicável + valide nós no /object_info antes de negar existência".

## 2026-08-03 — Os templates oficiais JÁ ESTÃO instalados (o melhor "exemplo known-good") + setup.sh de bundle 100% partner
- **Contexto**: reconstrução do `workflows-api/` do zero — 3 bundles novos (`image-edit-nano-banana-2`, `image-edit-seedream`, `video-person-swap-seedance-2`), todos em créditos comfy.org.
- **Aprendizado**:
  1. 🏆 **Não precisa baixar exemplo do GitHub.** O ComfyUI instala os templates oficiais em
     `…/site-packages/comfyui_workflow_templates_{core,media_api,media_image,media_video,media_other}/templates/*.json`.
     Achar a base para qualquer nó: `grep -rl "<NodeType>" …/comfyui_workflow_templates*/templates/`.
     Isso resolveu casos que eu não teria acertado à mão (ex.: `api_seedance2_0_r2v_real_human.json` revelou que **humano real exige asset verificado**).
  2. **Gerar o JSON por script Python** (builder mínimo de nós/links/grupos) > editar JSON à mão, quando o bundle tem N blocos repetidos. O que **não** pode ser inventado é a **ordem dos `widgets_values`** — essa tem que sair de um template oficial (o frontend intercala `control_after_generate` logo depois do `seed`, fora da ordem do `/object_info`).
  3. **Validação estrutural barata e que pega quase tudo**: (a) todo `link` aponta para nós existentes; (b) todo `input.link` existe no array `links`; (c) todo `type` existe no `/object_info` (exceto `MarkdownNote`, que é frontend-only e **não** aparece lá); (d) `len(widgets_values)` bate com o do mesmo tipo nos templates oficiais.
  4. **Bundle 100% partner não instala nada**: sem custom node, sem chave (a auth é o **login** em `platform.comfy.org`). O `setup.sh` vira um **verificador**: servidor no ar → nós presentes com `python_module` **não-nulo** → `.json` visível no painel.
  5. 🐛 **Armadilha do `find` com symlink**: `~/ComfyUI/user/default/workflows/api` é symlink para `workflows-api/`. `find "$WF_DIR" -name x.json` **não entra em symlink** → o script concluía "não achei" e copiava o `.json` para dentro do próprio repo, poluindo a raiz de `workflows-api/`. **Use `find -L`.** E, no fallback, prefira **criar o symlink** a copiar (cópia solta dessincroniza do repo em silêncio).
  6. **Card Informativo honesto**: 🟡 = "grafo validado estruturalmente, **não executado**" — executar um bundle-API gasta crédito de verdade, então não dá para prometer 🟢 sem o usuário rodar.
- **Fonte**: usuário (pedido) + templates oficiais instalados + `/object_info` ao vivo.
- **Ação**: promover ao corpo da skill os itens 1, 3 e 4 (mudam o procedimento padrão: passo 2 "adapte um exemplo known-good" deve apontar primeiro para os templates locais).
