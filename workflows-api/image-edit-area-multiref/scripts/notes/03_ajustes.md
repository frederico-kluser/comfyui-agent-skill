# 🔧 Ajustes finos

| Onde | Parâmetro | Padrão | Quando mexer |
|---|---|---|---|
| ⑤ Nano Banana 2 | `resolution` | `1K` | Área grande na foto (> ~1000 px) saiu borrada → `2K` **e** ④ alvo `2048`. |
| ④ Inpaint Crop | `output_target_width/height` | `1024` | **Sempre igual à resolução:** 1K→1024 · 2K→2048 · 4K→4096. Mantenha **quadrado**. |
| ⑤ Nano Banana 2 | `aspect_ratio` | `1:1` | **Não mude** — o recorte é quadrado. |
| ④ Inpaint Crop | `context_from_mask_extend_factor` | `2.0` | Luz/perspectiva não casaram → `2.5–3`. Detalhe fraco numa área pequena → `1.5`. |
| ④ Inpaint Crop | `mask_expand_pixels` | `8` | Sobra resto do objeto antigo na borda → pinte com folga ou suba para `32+` (o efeito real é bem menor que o número). |
| ④ Inpaint Crop | `mask_blend_pixels` | `32` | Costura visível → `48–64`. Halo na borda → `16`. |
| ⑥ 🛡️ limite de segurança | `expand` | `72` | Mantenha **≥ `mask_expand_pixels` + 2 × `mask_blend_pixels`** (senão a trava corta a borda suavizada). O `borda suave da trava` (16 px) evita costura seca. |
| ④ Inpaint Crop | `context_from_mask_extend_factor` × área grande | — | Se a área for grande e o quadrado de contexto não couber na foto, ela é acolchoada: o mapa marca o acolchoado e a borda da foto pode mudar até a trava. Baixe para `1.2–1.5`. |
| ④ cor do mapa | `color` | `16711935` (magenta) | Se a foto tiver muito magenta: verde `65280` ou ciano `65535` (troque também nas **regras fixas**). |
| ⑤ Nano Banana 2 | `thinking_level` | `HIGH` | `MINIMAL` = mais rápido, pior em perspectiva/oclusão. |
| ⑤ Nano Banana 2 | `model` | normal | `Nano Banana 2 Lite` = rascunho barato (só 1K). |

# 🩺 Problemas comuns

| Sintoma | Causa provável | Correção |
|---|---|---|
| `Unauthorized: Please login first` | sem login comfy.org | *Settings → User → Sign in* (no script: `COMFY_ORG_API_KEY`) |
| `402` / créditos | conta sem saldo | compre créditos em platform.comfy.org |
| Foto volta idêntica (e cobrou) | **máscara não pintada** | MaskEditor na ① BASE → pinte → **Save** |
| REF ignorada / papéis trocados | slot pulado (REF 1 vazio e REF 2 ligado) | Preencha **em ordem**: o nó descarta vazios e **renumera** as imagens. |
| Resultado com tinta magenta | modelo copiou o mapa | Run de novo (seed muda); reforce "never paint magenta" na instrução. |
| Área encaixada mas "colada" | contexto pequeno | suba `context_from_mask_extend_factor` e `mask_blend_pixels`. |
| Só o contorno mudou, o miolo não | pintou só a borda da área | pinte a área **preenchida** (o recorte não enche buracos — a trava desfaria o miolo). |
| `REF n` não aparece | nó roxo (bypass) | selecione e `Ctrl+B`. |
