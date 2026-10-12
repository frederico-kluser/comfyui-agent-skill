#!/usr/bin/env python3
"""comfy_client.py — roda "editar uma área com até 10 referências" SEM abrir a interface.

Fluxo (o mesmo do guia, com as correções verificadas no código do ComfyUI 0.38):

  1. abre o WebSocket  ws://<servidor>/ws?clientId=<uuid>   ANTES do POST /prompt
     (o servidor não reenvia eventos perdidos; o /history continua como plano B)
  2. POST /upload/image  — foto base e referências (multipart: image, type, subfolder, overwrite)
     · o nome do arquivo leva o hash do conteúdo: reenviar a mesma imagem reaproveita o arquivo
       (o servidor só deduplica quando o NOME já existe e o hash bate)
  3. POST /upload/mask   — a máscara + original_ref={"filename","subfolder","type"}
     · o servidor copia o canal ALFA da máscara para a foto original (transparente = editar);
       por isso convertemos a sua máscara P&B (branco = editar) para alfa antes de enviar
  4. monta o grafo no formato API, injetando 1 LoadImage por referência (image_3 … image_12)
  5. POST /prompt  {prompt, client_id, extra_data.api_key_comfy_org}
  6. escuta: status · execution_start · execution_cached · executing · progress · executed ·
     execution_success · execution_error · execution_interrupted
     · frames BINÁRIOS do SaveImageWebsocket: 4 bytes tipo de evento (1=PREVIEW_IMAGE) +
       4 bytes formato (1=JPEG, 2=PNG) + a imagem  →  bytes[8:]
     · `executing` com node=null e o nosso prompt_id = terminou (com sucesso OU erro)

Uso (rode com o Python do ComfyUI, que já tem websocket-client e Pillow):

  ~/ComfyUI/.venv/bin/python comfy_client.py --base foto.jpg --mask mascara.png \\
      --ref sofa.jpg --ref tecido.jpg \\
      --edit "Replace what is inside the edit area with the sofa from Image 3, upholstered in the fabric of Image 4." \\
      --roles "- Image 3: the exact sofa (shape, proportions, legs).\\n- Image 4: fabric texture and color only."

  --simular   testa recorte → mapa → recolagem → WebSocket SEM IA e SEM gastar crédito.

Chave: COMFY_ORG_API_KEY (ambiente ou ~/ComfyUI/secrets.env). Gere em
https://platform.comfy.org/profile/api-keys. Sem ela, os Partner Nodes respondem 401.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

try:
    import websocket  # pacote websocket-client
    from PIL import Image, ImageOps
except ImportError as e:  # pragma: no cover
    sys.exit(f"falta dependência ({e.name}). Rode com ~/ComfyUI/.venv/bin/python, ou instale: "
             "uv pip install --python ~/ComfyUI/.venv/bin/python websocket-client pillow")

sys.dont_write_bytecode = True  # sem __pycache__ dentro do bundle (o repo não tem .gitignore)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import graph_spec as gs  # noqa: E402

UPLOAD_SUBFOLDER = "inpaint-multiref"
COMFY_ROOT = Path(os.environ.get("COMFY_ROOT") or Path.home() / "ComfyUI")  # mesma variável do comando `comfyui`
DEFAULT_OUT = COMFY_ROOT / "output" / "inpaint-multiref" / "script"
PRICE_USD = {("nb2", "1K"): 0.0835, ("nb2", "2K"): 0.1217, ("nb2", "4K"): 0.1848, ("lite", "1K"): 0.0408}
BIN_PREVIEW_IMAGE, BIN_PREVIEW_IMAGE_WITH_METADATA = 1, 4  # protocol.BinaryEventTypes
IMAGE_FORMATS = {1: "jpg", 2: "png"}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_api_key() -> str | None:
    key = os.environ.get("COMFY_ORG_API_KEY")
    if key:
        return key.strip()
    secrets = COMFY_ROOT / "secrets.env"
    if secrets.is_file():
        for line in secrets.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[len("export "):]
            if line.startswith("COMFY_ORG_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"") or None
    return None


class ComfyError(RuntimeError):
    pass


class ComfyClient:
    def __init__(self, server: str = "127.0.0.1:8188", api_key: str | None = None):
        self.server = server
        self.client_id = str(uuid.uuid4())
        self.api_key = api_key

    # ── REST ──────────────────────────────────────────────────────────────
    def _http(self, path: str, data: bytes | None = None, headers: dict | None = None, timeout: int = 120) -> bytes:
        req = urllib.request.Request(f"http://{self.server}{path}", data=data, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            raise ComfyError(f"HTTP {e.code} em {path}: {body[:2000]}") from None
        except urllib.error.URLError as e:
            raise ComfyError(f"servidor ComfyUI inacessível em {self.server} ({e.reason}). "
                             "Abra-o noutro terminal com `comfyui` e repita.") from None

    def _multipart(self, path: str, fields: dict[str, str], file_field: str, filename: str, payload: bytes) -> dict:
        boundary = f"----comfy{uuid.uuid4().hex}"
        parts = []
        for k, v in fields.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n".encode() + payload + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        return json.loads(self._http(path, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))

    def upload_image(self, payload: bytes, filename: str, subfolder: str = UPLOAD_SUBFOLDER) -> str:
        """POST /upload/image — devolve o nome a usar no LoadImage ("subpasta/arquivo")."""
        r = self._multipart("/upload/image", {"type": "input", "subfolder": subfolder, "overwrite": "false"},
                            "image", filename, payload)
        return f"{r['subfolder']}/{r['name']}" if r.get("subfolder") else r["name"]

    def upload_mask(self, mask_rgba_png: bytes, filename: str, original_name: str,
                    subfolder: str = UPLOAD_SUBFOLDER) -> str:
        """POST /upload/mask — o servidor grava a ORIGINAL com o alfa desta máscara.

        overwrite=true de propósito: a deduplicação do servidor compara os bytes da MÁSCARA enviada com
        o arquivo já mesclado (sempre diferentes) e criaria "nome (1).png", "(2)"… a cada execução.
        O nome já carrega o hash de base+máscara, então sobrescrever é idempotente.
        """
        orig_sub, _, orig_file = original_name.rpartition("/")
        original_ref = json.dumps({"filename": orig_file, "subfolder": orig_sub, "type": "input"})
        r = self._multipart("/upload/mask", {"type": "input", "subfolder": subfolder, "overwrite": "true",
                                             "original_ref": original_ref}, "image", filename, mask_rgba_png)
        return f"{r['subfolder']}/{r['name']}" if r.get("subfolder") else r["name"]

    def queue_prompt(self, prompt: dict, prompt_id: str) -> dict:
        payload = {"prompt": prompt, "client_id": self.client_id, "prompt_id": prompt_id}
        if self.api_key:
            # o servidor tira isto do histórico/fila (SENSITIVE_EXTRA_DATA_KEYS)
            payload["extra_data"] = {"api_key_comfy_org": self.api_key}
        try:
            return json.loads(self._http("/prompt", json.dumps(payload).encode(), {"Content-Type": "application/json"}))
        except ComfyError as e:
            raise ComfyError(explain_prompt_error(str(e))) from None

    def history(self, prompt_id: str) -> dict:
        return json.loads(self._http(f"/history/{prompt_id}")).get(prompt_id, {})

    def view(self, filename: str, subfolder: str, kind: str) -> bytes:
        q = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": kind})
        return self._http(f"/view?{q}", timeout=300)

    # ── WebSocket ─────────────────────────────────────────────────────────
    def connect(self) -> websocket.WebSocket:
        ws = websocket.WebSocket()
        try:
            ws.connect(f"ws://{self.server}/ws?clientId={self.client_id}", timeout=30)
        except (OSError, websocket.WebSocketException) as e:
            raise ComfyError(f"servidor ComfyUI inacessível em {self.server} ({e}). Abra-o noutro terminal com "
                             "`comfyui` (ou COMFY_PORT=<porta> comfyui) e repita.") from None
        return ws

    def listen(self, ws: websocket.WebSocket, prompt_id: str, ws_nodes: set[str], titles: dict[str, str],
               timeout: float) -> list[tuple[str, bytes]]:
        """Escuta até `executing` com node=None do nosso prompt. Devolve [(extensão, bytes)]."""
        images: list[tuple[str, bytes]] = []
        current = None
        failure = None
        deadline = time.monotonic() + timeout
        plan_b = f"se o servidor seguir no ar, o resultado pode estar em http://{self.server}/history/{prompt_id}"
        while True:
            left = deadline - time.monotonic()
            if left <= 0:  # vale também com tráfego constante (status de outros clientes, progress…)
                raise ComfyError(f"passou de {timeout:.0f}s sem terminar — {plan_b}")
            ws.settimeout(max(1.0, left))
            try:
                frame = ws.recv()
            except websocket.WebSocketTimeoutException:
                raise ComfyError(f"sem resposta em {timeout:.0f}s — confira a fila em http://{self.server}") from None
            except (websocket.WebSocketConnectionClosedException, ConnectionError, OSError):
                frame = ""
            if frame in ("", b""):
                raise ComfyError("o servidor foi encerrado ou reiniciado no meio da execução (Ctrl+C no comfyui?) — "
                                 "esta execução se perdeu: abra o servidor de novo e repita o comando")
            if isinstance(frame, (bytes, bytearray)):
                if len(frame) < 8:
                    continue
                event = struct.unpack(">I", frame[:4])[0]
                if event == BIN_PREVIEW_IMAGE and current in ws_nodes:
                    fmt = struct.unpack(">I", frame[4:8])[0]
                    images.append((IMAGE_FORMATS.get(fmt, "bin"), bytes(frame[8:])))
                elif event == BIN_PREVIEW_IMAGE_WITH_METADATA and current in ws_nodes:
                    # só chega se o cliente anunciar feature_flags.supports_preview_metadata (não anunciamos)
                    n = struct.unpack(">I", frame[4:8])[0]
                    meta = json.loads(frame[8:8 + n])
                    images.append((meta.get("image_type", "image/png").split("/")[-1], bytes(frame[8 + n:])))
                continue
            msg = json.loads(frame)
            kind, data = msg.get("type"), msg.get("data", {})
            if kind == "status":
                q = data.get("status", {}).get("exec_info", {}).get("queue_remaining")
                if q is not None:
                    log(f"  · fila: {q} na fila")
                continue
            if data.get("prompt_id") not in (None, prompt_id):
                continue  # evento de outro trabalho
            if kind == "execution_start":
                log("  · execução iniciada")
            elif kind == "execution_cached":
                cached = data.get("nodes") or []
                if cached:
                    log(f"  · reaproveitados do cache: {', '.join(titles.get(n, n) for n in cached)}")
            elif kind == "executing":
                node = data.get("node")
                if node is None:
                    break  # fim do NOSSO prompt (sucesso ou erro)
                current = node
                log(f"  → {titles.get(node, node)}")
            elif kind == "progress":
                log(f"    {data.get('value')}/{data.get('max')}")
            elif kind == "execution_error":
                failure = data
            elif kind == "execution_interrupted":
                failure = {"exception_message": "execução interrompida", "node_id": data.get("node_id")}
            elif kind == "execution_success":
                log("  · execução concluída")
        if failure:
            raise ComfyError(explain_execution_error(failure, titles))
        return images


def explain_prompt_error(raw: str) -> str:
    """Erro de validação do POST /prompt (HTTP 400) em texto legível."""
    try:
        body = json.loads(raw.split(": ", 1)[1])
    except Exception:
        return raw
    lines = [f"o servidor rejeitou o grafo: {body.get('error', {}).get('message', body.get('error'))}"]
    for nid, ne in (body.get("node_errors") or {}).items():
        for err in ne.get("errors", []):
            lines.append(f"  nó {nid} ({ne.get('class_type')}): {err.get('message')} — {err.get('details')}")
    return "\n".join(lines)


def explain_execution_error(d: dict, titles: dict[str, str]) -> str:
    nid = str(d.get("node_id"))
    msg = d.get("exception_message", "").strip()
    hint = ""
    low = msg.lower()
    if "401" in msg or "login" in low or "unauthorized" in low:
        hint = ("\n  dica: falta a chave da comfy.org. Gere em https://platform.comfy.org/profile/api-keys e grave "
                "COMFY_ORG_API_KEY=... em ~/ComfyUI/secrets.env (chmod 600).")
    elif "402" in msg or "credit" in low:
        hint = "\n  dica: sem créditos na conta comfy.org — compre em platform.comfy.org."
    tb = "".join(d.get("traceback", [])[-3:]).strip()
    return (f"falhou no nó {nid} ({titles.get(nid, d.get('node_type'))}): {d.get('exception_type', '')} {msg}"
            f"{hint}" + (f"\n  traceback (fim):\n{tb}" if tb else ""))


# ── preparação das imagens ───────────────────────────────────────────────────
def content_name(data: bytes, stem: str, ext: str) -> str:
    """Nome determinístico pelo conteúdo: mesma imagem → mesmo nome → servidor reaproveita."""
    return f"{hashlib.sha256(data).hexdigest()[:12]}_{stem}{ext}"


def open_8bit(path: Path) -> Image.Image:
    """Abre já em pé (EXIF) e em 8 bits.

    Foto de celular em retrato vem "deitada" com EXIF orientation=6; sem o exif_transpose o PNG
    enviado perde o EXIF e a máscara (feita na foto em pé) cairia na área errada — numa chamada paga.
    16 bits (I;16) e paleta com transparência quebravam no convert() direto.
    """
    im = ImageOps.exif_transpose(Image.open(path))
    im.load()
    if im.mode.startswith("I;16") or im.mode in ("I", "F"):
        import numpy as np
        arr = np.asarray(im, dtype=np.float64)
        top = 1.0 if im.mode == "F" and arr.max() <= 1.0 else (255.0 if arr.max() <= 255 else 65535.0)
        im = Image.fromarray((arr / top * 255.0).clip(0, 255).round().astype(np.uint8), "L")
    elif im.mode in ("P", "PA", "LA", "La"):
        im = im.convert("RGBA" if (im.mode in ("PA", "LA", "La") or "transparency" in im.info) else "RGB")
    return im


def prepare_base_and_mask(base_path: Path, mask_path: Path | None) -> tuple[bytes, bytes | None, dict]:
    """Devolve (PNG da base, PNG RGBA cuja ALFA é a máscara, {size, bbox}) — alfa 0 = área a editar.

    Sem --mask, a base precisa ser um PNG com transparência (alfa 0 = área), como sai do MaskEditor.
    """
    base = open_8bit(base_path)
    if mask_path is None:
        if "A" not in base.getbands():
            raise ComfyError("sem --mask, a foto base precisa de transparência (alfa 0 = área a editar)")
        alpha = base.getchannel("A")
        # o Inpaint Crop ignora máscara < 0,1 (alfa > ~230): exija área de verdade (alfa < 128) antes de cobrar
        if alpha.getextrema()[0] >= 128:
            raise ComfyError("a transparência da base não marca área nenhuma (precisa de alfa < 50% na área)")
        buf = io.BytesIO()
        base.convert("RGBA").save(buf, "PNG")
        # o Inpaint Crop usa máscara > 0,1 → alfa < ~230
        return buf.getvalue(), None, {"size": base.size, "bbox": alpha.point(lambda v: 255 if v < 230 else 0).getbbox()}
    gray = open_8bit(mask_path).convert("L")  # branco = editar (convenção mais comum)
    if gray.size != base.size:
        rb, rm = base.width / base.height, gray.width / gray.height
        if abs(rb - rm) > 0.01 * rb:
            raise ComfyError(f"a máscara ({gray.width}×{gray.height}) não tem a proporção da foto "
                             f"({base.width}×{base.height}) — esticar poria a área no lugar errado")
        gray = gray.resize(base.size, Image.Resampling.NEAREST)
    if gray.getextrema()[1] < 128:
        raise ComfyError("a máscara está toda preta: pinte de BRANCO a área a editar")
    rgba = Image.new("RGBA", base.size, (0, 0, 0, 255))
    rgba.putalpha(gray.point(lambda v: 255 - v))  # branco → alfa 0 → LoadImage dá mask=1
    b1, b2 = io.BytesIO(), io.BytesIO()
    base.convert("RGB").save(b1, "PNG")
    rgba.save(b2, "PNG")
    return b1.getvalue(), b2.getvalue(), {"size": base.size, "bbox": gray.point(lambda v: 255 if v > 25 else 0).getbbox()}


def context_cap(info: dict, wanted: float) -> float:
    """Maior fator de contexto cujo quadrado 1:1 ainda cabe na foto.

    O Inpaint Crop cresce o retângulo da máscara por `fator` e depois o completa até 1:1. Se o
    quadrado passa do menor lado da foto, o canvas é acolchoado com máscara 1: o mapa (Image 2)
    marca o acolchoado como área e a recolagem vaza para a borda da foto. Folga de 64 px para o
    arredondamento do `output_padding`.
    """
    (w_img, h_img), bbox = info["size"], info["bbox"]
    if not bbox:
        return wanted
    side = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
    cap = (min(w_img, h_img) - 64) / side if side else wanted
    return max(1.0, min(wanted, cap))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, type=Path, help="foto a editar")
    ap.add_argument("--mask", type=Path, help="máscara P&B (BRANCO = área a editar). Omitida: usa a transparência da base")
    ap.add_argument("--ref", action="append", default=[], type=Path, help="referência (repita até 10x; ordem = Image 3, 4, …)")
    ap.add_argument("--edit", default=gs.DEFAULT_INSTRUCTION, help="o que fazer na área (inglês recomendado)")
    ap.add_argument("--roles", default=None, help='papel de cada referência; "\\n" vira quebra de linha')
    ap.add_argument("--resolution", choices=["1K", "2K", "4K"], default="1K")
    ap.add_argument("--lite", action="store_true", help="Nano Banana 2 Lite (só 1K, ~metade do preço)")
    ap.add_argument("--thinking", choices=["MINIMAL", "HIGH"], default="HIGH")
    ap.add_argument("--context", type=float, default=gs.DEFAULTS["context_factor"], help="contexto em volta da máscara (≥1)")
    ap.add_argument("--expand", type=int, default=gs.DEFAULTS["mask_expand"], help="px para engordar a máscara")
    ap.add_argument("--blend", type=int, default=gs.DEFAULTS["mask_blend"], help="px de suavização da borda")
    ap.add_argument("--seed", type=int, default=None, help="padrão: aleatória")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"pasta dos resultados (padrão: {DEFAULT_OUT})")
    ap.add_argument("--salvar-no-servidor", action="store_true", help="além do WebSocket, grava em output/ do ComfyUI")
    ap.add_argument("--simular", action="store_true", help="sem IA e sem crédito: devolve o mapa magenta recolado")
    ap.add_argument("--export-api", type=Path, help="grava o grafo API final (sem a chave) e sai sem executar")
    ap.add_argument("--crop-device", choices=["auto", "gpu", "cpu"], default="auto",
                    help="onde rodam recorte/recolagem (sem IA); auto = GPU se o servidor estiver em CUDA")
    ap.add_argument("--server", default=gs.default_server(),
                    help="host:porta (padrão: COMFY_SERVER, senão COMFY_HOST:COMFY_PORT, senão 127.0.0.1:8188)")
    ap.add_argument("--timeout", type=float, default=900, help="segundos para esperar o resultado")
    a = ap.parse_args(argv)

    if len(a.ref) > gs.MAX_REFS:
        ap.error(f"no máximo {gs.MAX_REFS} referências")
    if a.lite and a.resolution != "1K":
        ap.error("--lite só funciona em 1K")
    roles = (a.roles.replace("\\n", "\n") if a.roles is not None
             else ("REFERENCES: none" if not a.ref else gs.DEFAULT_ROLES))
    if not a.simular and "<DESCREVA" in a.edit:
        ap.error("--edit ainda tem o texto de exemplo: descreva o que deve aparecer na área")
    if not a.simular and a.ref and a.roles is None:
        ap.error('com --ref, diga o papel de cada uma em --roles (ex.: "- Image 3: the exact sofa.\\n- Image 4: fabric only.")')

    api_key = None if a.simular else load_api_key()
    cli = ComfyClient(a.server, api_key)

    # 1) WebSocket primeiro — nenhum evento do nosso prompt se perde
    ws = None if a.export_api else cli.connect()
    try:
        # 2-3) uploads
        base_png, mask_png, info = prepare_base_and_mask(a.base, a.mask)
        context = context_cap(info, a.context)
        if context < a.context:
            log(f"ℹ contexto reduzido de {a.context:g} para {context:.2f}: o quadrado 1:1 não cabia na foto"
                + (" (a área é maior que o lado menor da foto: algum acolchoamento é inevitável)" if context == 1.0 else ""))
        crop_device = a.crop_device
        if crop_device == "auto":
            devices = json.loads(cli._http("/system_stats")).get("devices") or [{}]
            crop_device = "gpu" if devices[0].get("type") == "cuda" else "cpu"
        base_name = cli.upload_image(base_png, content_name(base_png, a.base.stem, ".png"))
        log(f"✓ base enviada: {base_name}")
        if mask_png is not None:
            masked = cli.upload_mask(mask_png, content_name(base_png + mask_png, a.base.stem + "_mask", ".png"),
                                     base_name)
            log(f"✓ máscara aplicada no alfa via /upload/mask: {masked}")
        else:
            masked = base_name
        refs = []
        for i, r in enumerate(a.ref, 1):
            data = r.read_bytes()
            refs.append(cli.upload_image(data, content_name(data, r.stem, r.suffix.lower() or ".png")))
            log(f"✓ REF {i} → Image {gs.FIRST_REF_SLOT + i - 1}: {refs[-1]}")

        # 4) grafo API com injeção procedural das referências
        params = {"model": gs.MODEL_NB2_LITE if a.lite else gs.MODEL_NB2, "resolution": a.resolution,
                  "thinking_level": a.thinking, "context_factor": context, "mask_expand": a.expand,
                  "crop_device": "gpu (much faster)" if crop_device == "gpu" else "cpu (compatible)",
                  "mask_blend": a.blend, "seed": a.seed if a.seed is not None else random.randrange(2**32)}
        output = "both" if a.salvar_no_servidor else "websocket"
        prompt = gs.build_api_prompt(masked, refs, a.edit, roles, params=params, output=output, simulate=a.simular)
        if a.export_api:
            a.export_api.write_text(json.dumps(prompt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            log(f"✓ grafo API gravado em {a.export_api} (sem a chave)")
            return 0
        if a.simular:
            log("ℹ modo --simular: sem IA, sem crédito (o resultado mostra a área em magenta)")
        else:
            price = PRICE_USD[("lite" if a.lite else "nb2", a.resolution)]
            log(f"ℹ Nano Banana 2{' Lite' if a.lite else ''} {a.resolution} · {len(refs)} referência(s) · "
                f"~US$ {price:.4f} por execução (estimativa do badge do nó)")
            if not api_key:
                log("⚠ COMFY_ORG_API_KEY ausente: o nó de IA vai responder 401 (nada é cobrado).")

        # 5) enfileira
        prompt_id = str(uuid.uuid4())
        resp = cli.queue_prompt(prompt, prompt_id)
        log(f"✓ na fila: prompt_id={resp.get('prompt_id', prompt_id)} (posição {resp.get('number')})")

        # 6) escuta e coleta os frames binários do SaveImageWebsocket
        titles = {nid: n["_meta"]["title"] for nid, n in prompt.items()}
        images = cli.listen(ws, prompt_id, {gs.ID_SAVE_WS}, titles, a.timeout)
    finally:
        if ws is not None:
            ws.close()

    a.out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    saved = []
    for i, (ext, data) in enumerate(images):
        p = a.out / f"{a.base.stem}_{'simulado' if a.simular else 'editado'}_{stamp}_{prompt_id[:8]}_{i}.{ext}"
        p.write_bytes(data)
        saved.append(p)
    if not saved:  # plano B: /history + /view (só existe se SaveImage estiver no grafo)
        for node_out in cli.history(prompt_id).get("outputs", {}).values():
            for im in node_out.get("images", []):
                p = a.out / im["filename"].replace("/", "_")
                p.write_bytes(cli.view(im["filename"], im.get("subfolder", ""), im.get("type", "output")))
                saved.append(p)
    if not saved:
        raise ComfyError("terminou sem imagem — rode com --salvar-no-servidor e confira o /history")
    for p in saved:
        print(p)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ComfyError as e:
        log(f"✗ {e}")
        sys.exit(1)
