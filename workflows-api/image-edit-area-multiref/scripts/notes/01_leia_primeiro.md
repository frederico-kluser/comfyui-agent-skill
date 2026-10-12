# 🎯 Editar SÓ uma área da foto — com até 10 imagens de referência

**Tudo roda por API** (Nano Banana 2, créditos comfy.org). **Nenhum modelo de IA roda nesta máquina:**
os nós locais só recortam, pintam um mapa e recolam pixels (sem IA, custo zero).

> 🖥️ **Servidor:** num terminal, `comfyui` → abre `http://127.0.0.1:8188`. **Ctrl+C** no terminal encerra.

## ▶️ Passo a passo

| # | Onde | O que fazer |
|---|---|---|
| 1 | **① BASE** | *choose file to upload* → escolha a foto. Depois **botão direito no nó → Open in MaskEditor**, **pinte a área inteira** (preenchida, não só o contorno) e clique **Save**. |
| 2 | **② O QUE FAZER** | Troque o texto `<DESCREVA AQUI…>` pelo que deve aparecer na área. |
| 3 | **③ REF 1…10** *(opcional)* | Em cada slot que for usar: carregue a imagem e, com o nó selecionado, **`Ctrl+B`** para **ligar** (roxo = desligado = ignorado). **Preencha em ordem**: REF 1, REF 2, … sem pular. |
| 4 | **② PAPEL DE CADA REFERÊNCIA** | Diga para que serve cada uma (*"Image 3: o objeto exato"*, *"Image 4: só a textura"*). Apague as linhas que não usar. |
| 5 | **Run** (`Ctrl+Enter`) | Resultado em **⑥ RESULTADO FINAL** e em `ComfyUI/output/inpaint-multiref/`. |

> 🔐 **Antes do 1º Run:** *Settings → User → Sign in* (conta **platform.comfy.org**) e créditos na conta.

## 🧩 O que o modelo recebe

| Slot do modelo | Conteúdo |
|---|---|
| **Image 1** | recorte **limpo** da área + contexto (quadrado 1:1) |
| **Image 2** | o **mesmo** recorte com a área **pintada de magenta** = mapa de **ONDE** editar (veja em 👁️) |
| **Image 3 … 12** | **REF 1 … REF 10** (na ordem dos slots) |

O texto final é **regras fixas + o que fazer + papel das referências** (nós amarelos).

## 🛡️ Por que o resto da foto não muda

Nenhum modelo de API aceita **máscara + 10 referências** na mesma chamada. Então a IA edita **só um
recorte**, o **✂️ Inpaint Stitch** cola de volta **apenas a área mascarada** (com borda suavizada) e a
**🛡️ trava** devolve o pixel **original** em tudo que fica a mais de **88 px** da área pintada
(`expand 8 + 2 × blend 32` = 72 px, mais 16 px de transição suave). Testado: **0 pixels alterados** fora dessa
zona — no meio, nos cantos, na borda da foto e em fotos de até 6000×4000.

> ℹ️ "Original" = a foto **como o ComfyUI a decodificou**. Em **JPEG/WebP** o decodificador do ComfyUI
> pode diferir ±1–3 níveis de outros programas. Para fidelidade bit a bit com o arquivo, use **PNG RGB**.

> ⚠️ **Sem máscara pintada, a IA roda e cobra, mas a foto volta idêntica.** Pinte antes do Run.

## 💳 Custo por Run (badge do nó, aproximado)

| Nano Banana 2 | 1K | 2K | 4K |
|---|---|---|---|
| normal | ~US$ 0,08 | ~US$ 0,12 | ~US$ 0,18 |
| **Lite** (rascunho) | ~US$ 0,04 | — | — |

O badge do nó não varia com o nº de referências. O seed é **aleatório** a cada Run (cada Run = nova variação = nova cobrança).
