# video-person-swap-seedance-2 — me colocar num vídeo no lugar de uma pessoa (Seedance 2.0)

> ### 👉 Quer editar **o vídeo que você mesmo gravou**? Use [`../video-person-replace/`](../video-person-replace/)
> Este bundle usa **Seedance 2.0 reference-to-video**: ele **gera um vídeo novo** a partir de
> referências — a coreografia é do modelo, não a do seu vídeo. Para *"pegar o meu vídeo e trocar
> quem aparece nele, mantendo o movimento, o enquadramento e os cortes"*, a ferramenta certa é
> **Wan 2.2 Animate em modo *replace*** (`../video-person-replace/`), que recebe o seu vídeo e o edita.
>
> | | `video-person-replace` | **este bundle** |
> |---|---|---|
> | Recebe o **seu** vídeo e edita ele | ✅ | ⚠️ usa só como referência |
> | Mantém movimento/enquadramento/cortes | ✅ | ❌ recria a cena |
> | Precisa de prompt | ❌ | ✅ |
> | Chave de API | `FAL_KEY` | nenhuma (só login) |
>
> Continue aqui se você **não quer usar chave de API** (este roda só com login/crédito comfy.org)
> ou se quer **gerar** um plano novo em vez de editar um existente.

> Troca a pessoa de um vídeo por **você**, mantendo a **pose, a roupa, a câmera e a iluminação** do
> plano original. Roda **sem GPU**, pagando com os **créditos do comfy.org**.

|  |  |
|---|---|
| 🎯 Faz | Substitui a pessoa de um vídeo por você, preservando performance, figurino, enquadramento e luz |
| 🧠 Técnica | Reference-to-video multimodal (imagem + vídeo de referência) com **asset verificado de humano real** |
| 💳 Custo/billing | **Créditos comfy.org** — 1 chamada de vídeo por `Run` do PASSO 3. Criar asset é uma chamada separada e barata |
| 🔌 Provedores/Nós | `ByteDance2ReferenceNode` · `ByteDanceCreateImageAsset` · `ByteDanceCreateVideoAsset` · `GeminiNode` (partner) — **tudo core, zero custom node** |
| 📥 Entrada | Uma foto sua + o vídeo original (≤ 15 s) |
| 📤 Saída | `VIDEO` nativo (áudio preservado) em `output/video/eu-no-video-seedance2_*` |
| 🧩 Modelos | Seedance 2.0 / Seedance 2.0 Fast (ByteDance) · Gemini 3.1 Pro (helper de prompt) |
| 🧱 Requer | **Login** em `platform.comfy.org` + **verificação facial** no navegador (obrigatória para humano real) |
| 🟡 Status | Grafo gerado a partir dos templates oficiais `api_seedance2_0_r2v_real_human.json` e `template_seedance2_0_viral_videos_character_swap.json` + `/object_info` ao vivo, validado estruturalmente. **Ainda não executado** — valide no primeiro load |

📇 **Card de API:** [`API_REFERENCE_video-person-swap-seedance-2.md`](API_REFERENCE_video-person-swap-seedance-2.md)

## ⚠️ A parte que trava todo mundo: humano real exige verificação

O Seedance 2.0 **recusa** foto ou vídeo de **pessoa real** nas entradas normais (`reference_images` /
`reference_videos`). Como o objetivo aqui é justamente colocar **você** — uma pessoa real — no vídeo,
o caminho obrigatório é o de **asset verificado**:

```
LoadImage(sua foto)  → ByteDance Create Image Asset → asset_id ─┐
                                                                ├→ Seedance 2.0 → SaveVideo
LoadVideo(o vídeo)   → ByteDance Create Video Asset → asset_id ─┘
```

**Como a verificação acontece (só na primeira vez):**
1. Rode o **PASSO 1**. O nó `Create Image Asset` **para e imprime um link no console do servidor
   ComfyUI** — o terminal onde o ComfyUI roda. **Não aparece na interface.**
2. Abra o link no navegador e faça a **verificação facial**.
3. Terminada a verificação, os `PreviewAny` mostram o **`asset_id`** e o **`group_id`**.

**Guarde o `group_id`.** Cole-o no widget do nó `Create Image/Video Asset` nas próximas vezes e a
verificação é **pulada** para a mesma pessoa. Regras:
- O `group_id` vale **só para a conta que verificou** — não passa entre contas.
- Cada imagem/vídeo usado para criar asset deve conter **uma pessoa só**.

> Se o vídeo-fonte **não** tiver pessoa real (animação, 3D, personagem sintético), pule o
> `Create Video Asset` e ligue o `LoadVideo` direto no slot `model.reference_videos.video_1`.

## Como o prompt enxerga as entradas (o erro mais comum)

O modelo não conhece "asset_1". Ele recebe **rótulos posicionais**, na ordem
`reference_images` → `reference_videos` → `reference_audios` → `reference_assets`:

| O que está ligado | Vira, no prompt |
|---|---|
| `asset_1` = a sua foto (asset de **imagem**) | **`Image 1`** |
| `asset_2` = o vídeo original (asset de **vídeo**) | **`Video 1`** |
| se você também ligar `reference_images.image_1` | esse vira `Image 1` e o seu asset vira **`Image 2`** |

Por isso o prompt do PASSO 3 fala em **`Image 1`** e **`Video 1`**. **Se mudar as ligações, renumere o prompt.**

> Curiosidade útil: o nó reescreve tokens como `asset 1` / `asset1` para esses rótulos, mas **não**
> reescreve `asset_1` (com underscore) — a regex não cobre o underscore. Usar `Image 1` / `Video 1`
> direto evita o problema por completo.

## Pré-requisitos
- ComfyUI atualizado (todos os nós são **core**, em `comfy_api_nodes/nodes_bytedance.py`).
- **Login** em `platform.comfy.org` com créditos.
- Vídeo-fonte de **≤ 15 s** (limite do modelo). Mais longo? Corte em trechos e junte no editor.
- Uma foto sua nítida, frontal, luz neutra, **uma pessoa só** no quadro. Para o processo funcionar bem
  com o corpo inteiro em quadro, use uma foto sua **de corpo inteiro**.

## Setup
```bash
bash setup.sh
```
Confere servidor, os 8 nós no `/object_info` e a presença do `.json` no painel. **Não instala nada**
(não há custom node) e **não grava segredo** (a auth é o login).

## Como usar (:8188)
1. Abra **`video-person-swap-seedance-2.json`** e leia o nó **LEIA PRIMEIRO**.
2. **PASSO 1** — suba a sua foto no `LoadImage`. **Run**. Faça a verificação pelo link do console.
   Anote o `group_id` que aparece no `PreviewAny`.
3. **PASSO 2** — suba o vídeo original no `LoadVideo`. **Run**. Mesma coisa (mesma pessoa? cole o
   `group_id` do passo 1 e pule a verificação).
4. **PASSO 3** — ajuste o prompt (ele já vem completo) e os parâmetros:
   `resolution`, `duration` (4–15 s), `generate_audio`. **Run**.
5. O vídeo sai em `output/video/`.
6. **PASSO 4 (opcional, em bypass)** — se o plano for complexo, ative os 4 nós do grupo (**Ctrl+B**),
   rode só ele, copie o texto do `PreviewAny` e cole no prompt do PASSO 3. Depois volte ao bypass.

### Rascunhe barato
Primeiro passe: `model=Seedance 2.0 Fast`, `resolution=480p`, `duration=4`. Confirmou o enquadramento e
a identidade? Aí sim `Seedance 2.0` + `1080p` + a duração cheia.

## Parâmetros não-óbvios
| Onde | Parâmetro | Nota |
|---|---|---|
| `ByteDance2ReferenceNode` | `model` | `Seedance 2.0` = máxima qualidade, até **1080p**. `Seedance 2.0 Fast` = mais rápido/barato, **teto de 720p** |
| | `resolution` | `480p` / `720p` / `1080p` (1080p só no não-Fast) |
| | `ratio` | `adaptive` herda o formato do vídeo de referência. Forçar 16:9/9:16 **reenquadra** |
| | `duration` | **4 a 15** segundos. Clipe maior = mais crédito |
| | `generate_audio` | `true` gera **áudio novo**. Quer o áudio **original**? Ponha `false` e case o áudio na edição |
| | `seed` | ⚠️ Serve **só para forçar re-execução**. O resultado **não é determinístico** nem com seed fixa (está no tooltip do próprio nó) |
| | `auto_downscale` | Deixe `true`: reduz o vídeo de referência ao orçamento de pixels do modelo, preservando o formato |
| | `auto_upscale` | Deixe `false`. Ampliar fonte pequena **não cria detalhe** e piora o resultado |
| | `watermark` | `false` |
| `Create Image/Video Asset` | `group_id` | Vazio = dispara verificação. Preenchido com um `group_id` já verificado = pula |
| `GeminiNode` (PASSO 4) | `model` | `gemini-3-1-pro`. O `system_prompt` já pede luz, lente, timing e mecânica do movimento |

### Limites de referência do Seedance 2.0
| Tipo | Máximo |
|---|---|
| Imagens | 9 |
| Vídeos | 3 |
| Áudios | 3 |

## Validação (primeiro load)
1. Nenhum nó vermelho.
2. `Seedance 2.0 — o swap` tem **5 slots de input**, nesta ordem:
   `model.reference_images.image_1` · `model.reference_videos.video_1` · `model.reference_audios.audio_1` ·
   `model.reference_assets.asset_1` · `model.reference_assets.asset_2`.
3. `asset_1` recebe o `PreviewAny` do **PASSO 1** e `asset_2` o do **PASSO 2**.
4. Os 4 nós do PASSO 4 estão roxos (bypass).
5. Teste barato antes do primeiro vídeo caro: rode só o PASSO 1 e confirme que o `asset_id` aparece.

## Troubleshooting
| Sintoma | Causa provável | Correção |
|---|---|---|
| Nó vermelho `ByteDance2ReferenceNode` | ComfyUI antigo | Atualize o ComfyUI (nó core) |
| O workflow "trava" no `Create Image Asset` | Está esperando a verificação facial | Olhe o **console do servidor**, abra o link, complete a verificação |
| "asset is not Active" | Verificação não concluída ou asset expirado | Refaça o PASSO 1/2 |
| Erro ao usar humano real | Foto/vídeo ligado direto em `reference_images`/`reference_videos` | Use o caminho de **asset** (PASSOS 1 e 2) |
| Trocou a pessoa errada do quadro | Prompt ambíguo | Diga a posição: "the person on the left, in the dark jacket" |
| Rosto muda ao longo do clipe | Clipe longo / foto de referência fraca | Reduza para 4–6 s e use foto frontal nítida |
| Ele trocou a roupa também | Prompt não fixou o figurino | Descreva a peça original **item por item** no bloco WARDROBE |
| Proporção de corpo errada | Referência só de rosto | Use foto sua **de corpo inteiro** no PASSO 1 |
| Luz não casa | Plano com luz complexa | Rode o **PASSO 4** e cole a análise do Gemini no prompt |
| Áudio sumiu / mudou | `generate_audio=true` gera áudio novo | Ponha `false` e recoloque o áudio original na edição |
| Vídeo maior que 15 s | Limite do modelo | Corte em trechos ≤15 s, rode um por vez, junte no editor |
| Gastou crédito de vídeo sem querer no PASSO 4 | O PASSO 3 estava ativo junto | Deixe o `SaveVideo` do PASSO 3 em bypass enquanto roda só o helper |

Mais casos: `.agents/skills/task-debug-generation`.

## Referências
- Nós de API online: registo CoALA `knowledge-comfyui-api-nodes` (memória CoALA local)
- Doc oficial da verificação de humano real:
  <https://docs.comfy.org/tutorials/partner-nodes/bytedance/seedance-2-0-real-human>
- Templates oficiais de origem: `api_seedance2_0_r2v_real_human.json` e
  `template_seedance2_0_viral_videos_character_swap.json` (em `comfyui_workflow_templates_media_other`)
- Fonte do nó: `ComfyUI/comfy_api_nodes/nodes_bytedance.py`
