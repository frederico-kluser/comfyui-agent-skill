# image-edit-nano-banana-2 — 6 edições de foto com Nano Banana 2 (créditos comfy.org)

> **6 arquivos independentes, um por processo**: trocar roupa · trocar objeto em cena · trocar a pessoa ·
> **me colocar na foto com a roupa/pose da cena** · **me colocar na foto com a minha roupa/pose** ·
> trocar o local com match de iluminação. Roda **sem GPU**, pagando com os **créditos do comfy.org**.

|  |  |
|---|---|
| 🎯 Faz | Edita uma foto por instrução + imagens de referência: roupa, objeto, pessoa, cenário, e insere você na cena |
| 🧠 Técnica | Edição multi-referência em contexto (até 14 imagens) + **trava de identidade com 2 fotos suas** + **passe local de realismo de celular** |
| 💳 Custo/billing | **Créditos comfy.org** — 1 chamada por execução, **em `1K`** (o mínimo do modelo) |
| 🔌 Provedores/Nós | `GeminiNanoBanana2` (partner) · `BatchImagesNode` · `LoadImage`/`SaveImage` (core) · **+ WAS Suite e KJNodes** no passe de realismo |
| 📥 Entrada | A foto BASE + 1–2 fotos de REFERÊNCIA (**2 ângulos do rosto** nos processos de pessoa) |
| 📤 Saída | **PNG limpo** (`edit/nb2_*_limpo_*.png`) para encadear **+ JPG tratado** (`edit/nb2_*_FINAL_*.jpg`), o entregável |
| 🧩 Modelos | Nano Banana 2 · Gemini 3.1 Flash Image (Google Vertex) |
| 🧱 Requer | **Login** em `platform.comfy.org` (sem chave de API). Roda em máquina de 8 GB, sem GPU |
| 🟡 Status | Grafo gerado do `/object_info` ao vivo, **validado estruturalmente (16/16)**; a cadeia de realismo foi **executada e medida** aqui. A chamada ao modelo **ainda não foi executada** (gastaria crédito) |

📇 **Card de API:** [`API_REFERENCE_image-edit-nano-banana-2.md`](API_REFERENCE_image-edit-nano-banana-2.md)
🔁 **Irmão:** [`../image-edit-seedream/`](../image-edit-seedream/) — os mesmos 6 processos no Seedream. Rode os dois e compare.
📱 **Avulso:** [`../foto-realismo-celular/`](../foto-realismo-celular/) — a mesma cadeia de realismo para tratar fotos que já existem.

---

## O que mudou nesta versão (e por quê)

| Antes | Agora | Por quê |
|---|---|---|
| `resolution = 2K` | **`1K`** | É o mínimo do nó. Mais barato, e resolução menor **ajuda** no look de celular |
| 1 foto de referência | **2 fotos suas** (ângulos diferentes) nos processos de pessoa | O Google documenta que a consistência de personagem *"pode variar"* entre edições — uma foto só deixa o rosto derivar |
| Saída direta do modelo | **`ColorMatchV2` contra a sua foto BASE** | É o que faz a pessoa inserida *pertencer* àquela foto em vez de parecer colada |
| Nada depois do modelo | **Cadeia de realismo de celular** (8 nós, CPU, custo zero) | Modelo entrega imagem limpa demais. Pedir grão no prompt não resolve — só em pixel |
| Prompt sem exposição | **Cláusula de exposição** | Era o defeito visível nas gerações anteriores: você bem exposto na frente de uma janela estourada. Câmera de celular não faz isso |
| 1 saída | **2 saídas** (PNG limpo + JPG tratado) | O PNG serve para encadear processos; o JPG é o entregável |

> ⚠️ **Este bundle não é mais "zero custom node".** A cadeia de realismo usa
> `was-node-suite-comfyui` e `ComfyUI-KJNodes` (ambos já instalados nesta máquina).
> A parte que **paga crédito** continua 100% core.

---

## Pré-requisitos

- ComfyUI atualizado (`GeminiNanoBanana2` e `BatchImagesNode` são **core**).
- **Login** em `platform.comfy.org` pela interface, com créditos.
- Custom nodes do passe de realismo: `was-node-suite-comfyui` · `ComfyUI-KJNodes`.
- Nenhuma GPU necessária.

## Setup

```bash
bash setup.sh
```

## Os 6 processos — um arquivo por técnica

| # | Arquivo | Processo | BASE (Image 1) | REF 1 (Image 2) | REF 2 (Image 3) |
|---|---------|----------|------|------|------|
| 1 | `..._trocar-roupa.json` | Trocar a roupa | a pessoa | a peça (opcional) | — |
| 2 | `..._trocar-objetos-em-cena.json` | Trocar objetos em cena | a cena | o objeto (opcional) | — |
| 3 | `..._trocar-a-pessoa-da-foto.json` | Trocar a pessoa da foto | a cena | a pessoa nova | **2º ângulo** |
| 4 | `..._me-colocar-na-foto-roupa-da-cena.json` | **Eu na foto** — roupa e pose **da cena** | a foto onde quero entrar | **minha** foto | **2º ângulo** |
| 5 | `..._me-colocar-na-foto-minha-roupa.json` | **Eu na foto** — **minha** roupa e pose | a cena de destino | minha foto **de corpo inteiro** | **2º ângulo** |
| 6 | `..._trocar-o-local.json` | Trocar o local (+ match de luz) | a foto a manter | o novo local (opcional) | — |

## Como usar (:8188)

1. Abra o `.json` do processo (painel *Workflows* → `api/`).
2. **Suba as imagens.** A **ordem importa**: `BASE` é `Image 1`, `REF 1` é `Image 2`, `REF 2` é `Image 3`.
   O prompt cita as imagens **por posição** — é assim que o modelo sabe quem é a base e quem é a referência.
3. **Edite o prompt.** Onde houver `<DESCREVA AQUI ...>`, troque pelo seu texto.
4. **Run.** Saem os dois arquivos em `output/edit/`.

> **Encadear:** use o **PNG limpo** de um processo como BASE do próximo (ex.: rode o 5 e depois o 1).
> Não encadeie a partir do JPG tratado — o tratamento acumularia.

### As fotos de referência que funcionam

- Rosto **nítido**, luz neutra, **sem** óculos escuros, **uma pessoa só**.
- **Dois ângulos diferentes** (frontal + perfil/3-4). É o que trava a identidade em 3D.
- No processo 5, a REF 1 precisa ser **de corpo inteiro** (é dela que sai a sua roupa e pose).

## Parâmetros não-óbvios

| Onde | Parâmetro | Nota |
|---|---|---|
| `GeminiNanoBanana2` | `resolution` | **`1K`** — o mínimo. `4K` só na finalização |
| | `aspect_ratio` | `auto` mantém o formato da BASE. Mudar **reenquadra** |
| | `thinking_level` | `HIGH` — é o que resolve perspectiva, escala e sombra |
| | `seed` | `randomize`. Gostou? Troque para `fixed` e anote (repetição é *best effort*) |
| | `system_prompt` | Calibrado para compositing fotorrealista. **Não apague** |
| `BatchImagesNode` | ordem dos slots | `image0` = Image 1, `image1` = Image 2… Inverter troca o sentido do prompt |
| | slots extras | Aceita até **14** imagens |
| Realismo | preset | Vem no `padrão`. Tabela completa dos 4 presets na nota verde do grafo |
| | `largest_size` | ⚠️ **Não passe de ~2048** — veja o aviso abaixo |

### As 3 cláusulas finais do prompt

Todo prompt termina com três parágrafos. **Se apagar, volta a parecer colagem.**

1. **Exposição** — manda o modelo *errar* a exposição como uma câmera de celular erraria.
2. **Luz / lente / grão** — casa direção de luz, temperatura, sombra de contato, profundidade de campo.
3. **Look de celular** — enquadramento casual, sem cara de estúdio.

## ⚠️ Limite de tamanho no passe de realismo

O nó `Image Film Grain` **supersampleia 4× internamente**. O nó 2
(`ImageScaleToMaxDimension`) limita o lado maior justamente para isso não estourar a RAM.
Durante a calibração, uma imagem de **5248×12800 derrubou o ComfyUI** nesta máquina.
**Não aumente `largest_size` acima de ~2048.**

## Validação (primeiro load)

1. Nenhum nó **vermelho**. Se aparecer, falta um custom node (WAS/KJNodes) ou o ComfyUI está desatualizado.
2. O `Nano Banana 2` mostra: prompt · model · seed · aspect_ratio · **resolution=1K** · response_modalities · thinking_level=HIGH · system_prompt.
3. Teste barato: `thinking_level=MINIMAL` no processo 1 primeiro.

## Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| Nó vermelho `GeminiNanoBanana2` | ComfyUI antigo | Atualize (o nó é core, vem em `comfy_api_nodes`) |
| Nó vermelho `Image Film Grain` / `ColorMatchV2` | Falta WAS Suite / KJNodes | Instale pelo Manager e reinicie |
| "Insufficient credits" / erro de auth | Não logado ou sem crédito | Login em `platform.comfy.org` e confira o saldo |
| Devolve a foto quase igual | Prompt genérico ou `thinking_level=MINIMAL` | `HIGH` + seja específico ("replace X with Y") |
| Rosto não parece comigo | REF ruim ou só 1 ângulo | Frontal + perfil, nítidas, luz neutra |
| Pele plástica / borda de recorte | Cláusulas finais apagadas | Restaure o fim do prompt e o `system_prompt` |
| Ainda parece IA | Preset de realismo fraco | Troque para `marcado` (tabela na nota verde) |
| Ficou com chuvisco / franja colorida | Preset exagerado | Volte para `padrão` ou `limpo` |
| ComfyUI caiu no meio | Imagem gigante no passe de realismo | Baixe o `largest_size` |
| Reenquadrou a imagem | `aspect_ratio` ≠ `auto` | Volte para `auto` |

Mais casos: `.agents/skills/task-debug-generation`.

## Referências

- Nós de API online: registo CoALA `knowledge-comfyui-api-nodes` (memória CoALA local)
- Técnica de edição: registo CoALA `knowledge-image-editing` · realce: `knowledge-image-enhance`
- Template oficial de origem: `comfyui_workflow_templates_media_image/templates/api_google_nano_banana2_image_edit.json`
