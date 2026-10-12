# 🔌 Rodar por script — REST + WebSocket (headless)

O mesmo grafo roda sem abrir a tela, pelo cliente `scripts/comfy_client.py` deste bundle (com o servidor aberto
noutro terminal por `comfyui`):

```bash
~/ComfyUI/.venv/bin/python scripts/comfy_client.py \
  --base sala.jpg --mask mascara.png \
  --ref sofa.jpg --ref tecido.jpg \
  --edit "Replace what is inside the edit area with the sofa from Image 3, upholstered in the fabric of Image 4." \
  --roles "- Image 3: the exact sofa (shape, legs, proportions).\n- Image 4: fabric texture and color only."
```

- **Máscara:** P&B com **branco = área**, mesma proporção da foto. Sem `--mask`, usa a **transparência** da base (PNG). A orientação EXIF (foto de celular em pé) é respeitada.
- **Com `--ref`, `--roles` é obrigatório** (o texto de exemplo não vai para o modelo pago).
- **Chave:** `COMFY_ORG_API_KEY` em `~/ComfyUI/secrets.env` (gere em *platform.comfy.org → API Keys*).
- **`--simular`**: testa tudo **sem IA e sem crédito** (devolve a área em magenta).
- `--resolution 2K` · `--lite` · `--seed N` · `--salvar-no-servidor` · `--export-api grafo.json`

## O que o cliente faz, em ordem

| # | Chamada | Detalhe |
|---|---|---|
| 1 | `ws://…/ws?clientId=<uuid>` | aberto **antes** do `/prompt` |
| 2 | `POST /upload/image` | base + referências; nome = hash do conteúdo (reenvio não duplica) |
| 3 | `POST /upload/mask` | máscara convertida para **alfa** + `original_ref` (`overwrite=true`: aqui a dedup do servidor nunca casa) |
| 4 | monta o grafo API | **1 `LoadImage` por referência**, ligada em `model.images.image_3…12` |
| 5 | `POST /prompt` | `{prompt, client_id, prompt_id, extra_data.api_key_comfy_org}` |
| 6 | eventos | `status` · `execution_start` · `execution_cached` · `executing` · `progress` · `execution_error` · `execution_success` |
| 7 | frames binários | do `SaveImageWebsocket` → `bytes[8:]` = PNG → `~/ComfyUI/output/inpaint-multiref/script/` (`--out`) |
| 8 | plano B | `GET /history/{id}` + `GET /view` (com `--salvar-no-servidor`) |

> A chave **não** fica no histórico: o servidor a separa (`SENSITIVE_EXTRA_DATA_KEYS`) antes de gravar.
