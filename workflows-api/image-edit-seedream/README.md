# image-edit-seedream — as mesmas 6 edições, no Seedream 5.0/4.5 (créditos comfy.org)

> Gêmeo do [`../image-edit-nano-banana-2/`](../image-edit-nano-banana-2/): **os mesmos 6 processos**,
> no outro melhor editor disponível por crédito comfy.org. **6 arquivos independentes, um por processo.**
> Rode os dois com a mesma entrada e fique com o melhor — eles erram de formas diferentes.

|  |  |
|---|---|
| 🎯 Faz | Edita uma foto por instrução + imagens de referência: roupa, objeto, pessoa, cenário, e insere você na cena |
| 🧠 Técnica | Edição multi-referência (até 14 refs) + **trava de identidade com 2 fotos suas** + **passe local de realismo de celular** |
| 💳 Custo/billing | **Créditos comfy.org** — 1 chamada por execução, em **`Custom 1024×1360`** (o mínimo do modelo) |
| 🔌 Provedores/Nós | `ByteDanceSeedreamNode` (partner) · `BatchImagesNode` · `LoadImage`/`SaveImage` (core) · **+ WAS Suite e KJNodes** no passe de realismo |
| 📥 Entrada | A foto BASE + 1–2 fotos de REFERÊNCIA (**2 ângulos do rosto** nos processos de pessoa) |
| 📤 Saída | **PNG limpo** (`edit/sd_*_limpo_*.png`) para encadear **+ JPG tratado** (`edit/sd_*_FINAL_*.jpg`), o entregável |
| 🧩 Modelos | Seedream 5.0 lite · Seedream 4.5 (`seedream-4-5-251128`) · Seedream 4.0 |
| 🧱 Requer | **Login** em `platform.comfy.org` (sem chave de API). Roda em máquina de 8 GB, sem GPU |
| 🟡 Status | Grafo gerado do `/object_info` ao vivo, **validado estruturalmente (16/16)**; a cadeia de realismo foi **executada e medida** aqui. A chamada ao modelo **ainda não foi executada** (gastaria crédito) |

📇 **Card de API:** [`API_REFERENCE_image-edit-seedream.md`](API_REFERENCE_image-edit-seedream.md)
📱 **Avulso:** [`../foto-realismo-celular/`](../foto-realismo-celular/) — a mesma cadeia de realismo para tratar fotos que já existem.

---

## ⚠️ A diferença que mais importa: o Seedream **não** tem `aspect_ratio: auto`

Ele **sempre** entrega no tamanho que você pedir. O bundle vem em
**`Custom` 1024 × 1360** (retrato 3:4, formato de foto de celular, e **1024 é o mínimo
que o nó aceita** — todos os `size_preset` prontos começam em 2048).

**Se a sua foto BASE não for retrato, troque antes de rodar:**

| Formato da sua BASE | `width` × `height` |
|---|---|
| Retrato 3:4 (padrão) | **1024 × 1360** |
| Paisagem 4:3 | **1360 × 1024** |
| Quadrado | **1024 × 1024** |
| Vertical 9:16 | **1024 × 1820** |

Se deixar em retrato uma foto paisagem, ele **reenquadra** e você perde as bordas.

> Por isso, para *"me colocar na foto"* o **Nano Banana costuma dar menos trabalho** —
> ele preserva o formato sozinho com `aspect_ratio=auto`.

## Qual dos dois usar

| Situação | Escolha |
|---|---|
| Colocar você numa cena com luz difícil (contraluz, neon, luz mista) | **Nano Banana 2** (`thinking_level=HIGH` raciocina sobre a luz) |
| Preservar textura de tecido, estampa, logo, detalhe fino de roupa | **Seedream** |
| A foto BASE não é retrato e você não quer configurar nada | **Nano Banana 2** (`auto`) |
| Cena com muita oclusão (mão na frente do objeto, gente atrás) | **Nano Banana 2** |
| Quer variações rápidas do mesmo enquadramento | **Seedream** (`sequential_image_generation=auto`) |
| Não sei | Rode os dois. É 1 crédito cada e a diferença costuma ser óbvia |

---

## O que mudou nesta versão (e por quê)

| Antes | Agora | Por quê |
|---|---|---|
| `size_preset = 2560x1440 (16:9)` | **`Custom` 1024 × 1360** | Os presets começam em 2048; só o `Custom` alcança o mínimo real (1024). Mais barato, e resolução menor ajuda no look de celular. O 16:9 ainda deformava fotos retrato |
| 1 foto de referência | **2 fotos suas** (ângulos diferentes) nos processos de pessoa | Uma foto só deixa o rosto derivar entre edições |
| Saída direta do modelo | **`ColorMatchV2` contra a sua foto BASE** | Faz a pessoa inserida *pertencer* àquela foto em vez de parecer colada |
| Nada depois do modelo | **Cadeia de realismo de celular** (8 nós, CPU, custo zero) | Modelo entrega imagem limpa demais; grão pedido no prompt não resolve |
| Prompt sem exposição | **Cláusula de exposição** | Corrige o erro que denunciava colagem (você bem exposto na frente de janela estourada) |
| 1 saída | **2 saídas** (PNG limpo + JPG tratado) | PNG para encadear; JPG é o entregável |

> ⚠️ **Este bundle não é mais "zero custom node".** A cadeia de realismo usa
> `was-node-suite-comfyui` e `ComfyUI-KJNodes` (já instalados nesta máquina).
> A parte que **paga crédito** continua 100% core.

## Pré-requisitos

- ComfyUI atualizado (`ByteDanceSeedreamNode` e `BatchImagesNode` são **core**).
- **Login** em `platform.comfy.org`, com créditos.
- Custom nodes do passe de realismo: `was-node-suite-comfyui` · `ComfyUI-KJNodes`.

## Setup

```bash
bash setup.sh
```

## Os 6 processos

| # | Arquivo | Processo | BASE (Image 1) | REF 1 (Image 2) | REF 2 (Image 3) |
|---|---------|----------|------|------|------|
| 1 | `..._trocar-roupa.json` | Trocar a roupa | a pessoa | a peça (opcional) | — |
| 2 | `..._trocar-objetos-em-cena.json` | Trocar objetos em cena | a cena | o objeto (opcional) | — |
| 3 | `..._trocar-a-pessoa-da-foto.json` | Trocar a pessoa da foto | a cena | a pessoa nova | **2º ângulo** |
| 4 | `..._me-colocar-na-foto-roupa-da-cena.json` | **Eu na foto** — roupa e pose **da cena** | a foto onde quero entrar | **minha** foto | **2º ângulo** |
| 5 | `..._me-colocar-na-foto-minha-roupa.json` | **Eu na foto** — **minha** roupa e pose | a cena de destino | minha foto **de corpo inteiro** | **2º ângulo** |
| 6 | `..._trocar-o-local.json` | Trocar o local (+ match de luz) | a foto a manter | o novo local (opcional) | — |

## Como usar (:8188)

1. Abra o `.json` do processo.
2. **Confira `width`/`height`** conforme o formato da sua BASE (tabela acima).
3. **Suba as imagens.** A ordem importa: BASE = `Image 1`, REF 1 = `Image 2`, REF 2 = `Image 3`.
   A ByteDance orienta explicitamente nomear as referências **por posição ordinal** no prompt — é o que os prompts deste bundle fazem.
4. **Edite o prompt** onde houver `<DESCREVA AQUI ...>` e **Run**.

> **Encadear:** use o **PNG limpo** como BASE do próximo processo — nunca o JPG tratado.

## Parâmetros não-óbvios

| Onde | Parâmetro | Nota |
|---|---|---|
| `ByteDanceSeedreamNode` | `size_preset` | **`Custom`** — é o único caminho até 1024 |
| | `width`/`height` | **mínimo 1024** (o nó rejeita menos). `step` 2 |
| | `model` | `seedream 5.0 lite` — o mais barato e suficiente para edição |
| | `watermark` | `false` |
| | `sequential_image_generation` | `disabled`. Em `auto` ele pode devolver várias imagens (custa mais) |
| Realismo | preset | Vem no `padrão`. Tabela dos 4 presets na nota verde do grafo |
| | `largest_size` | ⚠️ **Não passe de ~2048** |

## ⚠️ Limite de tamanho no passe de realismo

`Image Film Grain` **supersampleia 4×**. O `ImageScaleToMaxDimension` limita o lado maior
para isso não estourar a RAM — uma imagem de **5248×12800 derrubou o ComfyUI** durante a calibração.

## Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| Nó vermelho `ByteDanceSeedreamNode` | ComfyUI antigo | Atualize (o nó é core) |
| Nó vermelho `Image Film Grain` / `ColorMatchV2` | Falta WAS Suite / KJNodes | Instale pelo Manager e reinicie |
| Cortou as bordas / esticou a foto | `width`/`height` no formato errado | Ajuste pela tabela no topo |
| "Insufficient credits" | Sem crédito / não logado | `platform.comfy.org` |
| Rosto não parece comigo | REF ruim ou só 1 ângulo | Frontal + perfil, nítidas |
| Ainda parece IA | Preset de realismo fraco | Troque para `marcado` |
| Chuvisco / franja colorida | Preset exagerado | Volte para `padrão` ou `limpo` |
| ComfyUI caiu no meio | Imagem gigante no passe de realismo | Baixe o `largest_size` |

Mais casos: `.agents/skills/task-debug-generation`.

## Referências

- Nós de API online: registo CoALA `knowledge-comfyui-api-nodes` (memória CoALA local)
- Técnica de edição: registo CoALA `knowledge-image-editing`
