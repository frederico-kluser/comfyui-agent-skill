# video-person-replace — trocar a pessoa de um vídeo que **eu** forneço

> **Você dá o vídeo. O modelo troca quem aparece nele por você.**
> O movimento, o enquadramento, os cortes e a duração do **seu** vídeo são mantidos.
> Roda **sem GPU** — a inferência é na fal.ai.

|  |  |
|---|---|
| 🎯 Faz | Recebe um vídeo seu + uma foto sua e devolve o mesmo vídeo com **você** no lugar da pessoa |
| 🧠 Técnica | `Wan 2.2 Animate 14B` em **modo *replace*** — deriva pose/expressão do próprio vídeo, sem prompt |
| 💳 Custo/billing | **fal.ai**, por segundo de vídeo. **Precisa de `FAL_KEY`** — veja *Como pegar a chave* |
| 🔌 Provedores/Nós | `Wan2214b_animate_replace_character_fal` · `PixverseSwapNode_fal` · `LoadVideoURL` (todos `ComfyUI-fal-API`) |
| 📥 Entrada | Uma **foto sua de corpo inteiro** + o **vídeo original** (comece com 3–6 s) |
| 📤 Saída | `output/video/replace_*.mp4` — com **áudio original** e **fps original** preservados |
| 🧩 Modelos | Wan 2.2 Animate 14B (replace) · Pixverse Swap (alternativa 360p) |
| 🖥️ Resolução | **`480p` por padrão** — o mínimo do modelo, de propósito (mais barato + cara de celular) |
| 🟡 Status | Grafo gerado do `/object_info` ao vivo e **validado estruturalmente** (16/16). **Ainda não executado** — gastaria crédito |

📇 **Card de API:** [`API_REFERENCE_video-person-replace.md`](API_REFERENCE_video-person-replace.md)
🔁 **Irmão:** [`../video-person-swap-seedance-2/`](../video-person-swap-seedance-2/) — roda por crédito comfy.org (só login, sem chave), mas **gera** um vídeo novo em vez de editar o seu.

---

## Por que este bundle existe

O bundle antigo (`video-person-swap-seedance-2`) usa **Seedance 2.0 reference-to-video**.
Ele **gera um vídeo novo** a partir de referências — a coreografia é dele, não sua.
Para *"me colocar num vídeo que eu forneço"* isso é a ferramenta errada.

| | **Wan Animate *replace*** (aqui) | Seedance 2.0 *reference* |
|---|---|---|
| Recebe o **seu** vídeo | ✅ e edita ele | ⚠️ usa só como referência |
| Mantém o movimento original | ✅ | ❌ recria |
| Mantém enquadramento e cortes | ✅ | ❌ |
| Precisa de prompt | ❌ nenhum | ✅ obrigatório |
| Passo manual de `asset_id` | ❌ | ✅ copiar/colar |

---

## 🔑 Como pegar a chave (fal.ai) — 5 min

1. Acesse **https://fal.ai** e crie a conta (login com Google/GitHub serve).
2. Vá em **https://fal.ai/dashboard/keys**.
3. **Add key** → copie o valor. ⚠️ Ele só aparece **uma vez**.
4. Adicione crédito em **https://fal.ai/dashboard/billing**.

Grave em `~/ComfyUI/secrets.env` (permissão `600`, **nunca** commitado):

```bash
FAL_KEY=cole-a-chave-aqui
```

Depois **reinicie o ComfyUI**. O `run.sh` já faz `source ~/ComfyUI/secrets.env`.

> ✅ **Nesta máquina o `FAL_KEY` já está carregado** no processo do ComfyUI.
> Se der `401`, a chave expirou ou acabou o crédito.

**Preço corrente:** https://fal.ai/models/fal-ai/wan/v2.2-14b/animate/replace
(cobrado por segundo; **480p custa bem menos que 720p**).

---

## Pré-requisitos

- **Custom nodes** (já instalados nesta máquina):
  `ComfyUI-fal-API` · `ComfyUI-VideoHelperSuite` · `was-node-suite-comfyui`
- `FAL_KEY` no ambiente do ComfyUI.
- Nenhuma GPU: a inferência roda na fal.ai.

## Setup

```bash
bash setup.sh
```

Confere servidor no ar, presença dos nós no `/object_info`, presença do `FAL_KEY`
e deixa os `.json` visíveis no painel. **Não grava segredo em disco.**

---

## Os 2 arquivos

| Arquivo | Modelo | Resolução | Áudio | Quando usar |
|---|---|---|---|---|
| `video-person-replace_wan-animate.json` | Wan 2.2 Animate *replace* | **480p** | remontado do original | **Padrão.** Melhor semelhança |
| `video-person-replace_pixverse-360p.json` | Pixverse Swap | **360p** | vem junto automático | Mais barato/rápido |

### Fluxo do arquivo principal

```
MINHA FOTO ──┐
             ├→ Wan 2.2 Animate (replace, 480p) → video_url
VÍDEO ───────┤                                       ↓
             │                            Load Video (URL) → quadros
             └→ GetVideoComponents → áudio ───┐        ↓
                                              │   grão de celular (CPU, grátis)
                     VHS_VideoInfo → fps ─────┼────────┤
                                              └→ Create Video → Save Video
```

O `video_url` volta como **texto**; o `Load Video (URL)` traz os quadros de volta,
e o `Create Video` remonta usando o **áudio do seu vídeo original** e o **fps real**
do resultado. É por isso que o mp4 final não sai mudo nem acelerado.

---

## Regras que mudam o resultado

- **Foto de corpo inteiro.** O modelo precisa ver tronco e pernas. Foto só do rosto → corpo inventado.
- **Vídeo curto.** Comece com **3–6 s**. Custo e risco crescem por segundo.
- **Uma pessoa em cena.** Com várias, ele pode trocar a errada (use `keyframe_id` no Pixverse).
- **Roupa parecida ajuda.** Manga longa no vídeo + regata na foto = improviso.

## Parâmetros não-óbvios

| Widget | Vem como | Nota |
|---|---|---|
| `resolution` | **`480p`** | Mínimo do modelo. Suba para `720p` só na versão final |
| `turbo` | `True` | Bem mais rápido/barato |
| `guidance_scale` | `1.0` | ⚠️ **Não mexa.** Modelo destilado: `>1` **borra o vídeo** |
| `shift` | `8` | Padrão do modelo |
| `variations` | `1` | `>1` multiplica o custo |
| `num_inference_steps` | `20` | Com `turbo`, subir daqui rende pouco |

## Troubleshooting

| Sintoma | Causa provável | Correção |
|---|---|---|
| Nó vermelho | Falta `ComfyUI-fal-API` | Instale pelo Manager e reinicie |
| `401` / `Unauthorized` | `FAL_KEY` ausente/inválida | Veja *Como pegar a chave* |
| Trocou a pessoa errada | Várias pessoas em cena | Corte o trecho com só uma pessoa |
| Corpo estranho | Foto só do rosto | Use foto de corpo inteiro |
| Vídeo mudo | `GetVideoComponents` desligado | Religue o `audio` no `Create Video` |
| Vídeo acelerado/lento | `fps` desligado | Religue `VHS_VideoInfo → fps` no `Create Video` |
| Grão demorando muito | Filtros rodam quadro a quadro na CPU | Apague os 3 nós verdes e ligue os quadros direto no `Create Video` |

Mais casos: `.agents/skills/task-debug-generation`.

## Referências

- Nós de API online: registo CoALA `knowledge-comfyui-api-nodes` (memória CoALA local)
- Endpoint fal: `fal-ai/wan/v2.2-14b/animate/replace` — `resolution ∈ {480p, 580p, 720p}`, default `480p`
