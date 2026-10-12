#!/usr/bin/env python3
"""graph_spec.py — FONTE ÚNICA do grafo "editar uma área com até 10 referências".

O mesmo grafo sai em dois formatos, gerados daqui (nunca edite os dois à mão):

  * formato UI  (``image-edit-area-multiref.json``) — abre no ComfyUI, com grupos e
    notas.  Gerado por ``python3 graph_spec.py --write-ui``.
  * formato API (``{id: {class_type, inputs}}``) — o que o ``POST /prompt`` aceita.
    Gerado em tempo de execução por ``build_api_prompt()`` (usado pelo
    ``comfy_client.py``), ou exportado com ``python3 graph_spec.py --export-api X``.

Nenhum modelo de IA roda localmente: o único nó de IA é o ``GeminiNanoBanana2V2``
(Partner Node, roda no Google, cobra créditos comfy.org).  Os demais nós só fazem
operações de pixel, sem IA (recorte, mapa da área, recolagem).

Por que um builder e não JSON à mão: a ordem dos ``widgets_values`` do formato UI
não é a ordem do ``/object_info`` (o frontend intercala ``control_after_generate``
logo depois do ``seed``) e o nó de modelo usa DYNAMICCOMBO + AUTOGROW (V3).  A
ordem usada aqui foi copiada dos templates oficiais instalados
(``template_product_placement.json``, ``api_google_nano_banana2_image_edit_continuation.json``,
``basic_mask_operations_and_compositing.json``) e é conferida contra o
``/object_info`` ao vivo por ``--check``.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE_DIR = HERE.parent
UI_JSON = BUNDLE_DIR / "image-edit-area-multiref.json"

MAX_REFS = 10
FIRST_REF_SLOT = 3  # Image 1 = recorte limpo, Image 2 = mapa magenta, Image 3.. = REF 1..

MODEL_NB2 = "Nano Banana 2 (Gemini 3.1 Flash Image)"
MODEL_NB2_LITE = "Nano Banana 2 Lite"
MAGENTA = 0xFF00FF  # cor do mapa da área (EmptyImage.color é um int 0xRRGGBB)

# Texto padrão do system_prompt do nó (copiado do /object_info, mantido intacto).
NB2_SYSTEM_PROMPT = (
    "You are an expert image-generation engine. You must ALWAYS produce an image.\n"
    "Interpret all user input—regardless of format, intent, or abstraction—as literal visual "
    "directives for image composition.\n"
    "If a prompt is conversational or lacks specific visual details, you must creatively invent a "
    "concrete visual scenario that depicts the concept.\n"
    "Prioritize generating the visual representation above any text, formatting, or conversational requests."
)

# ── Textos que vão para o modelo (inglês: o modelo segue melhor) ───────────────
RULES_TEXT = """TASK: localized photo edit (inpainting). Follow these rules strictly.
- Image 1 is the photo to edit. Return Image 1 with exactly the same framing, crop, camera angle, perspective and 1:1 aspect ratio.
- Image 2 is the SAME photo with the EDIT AREA highlighted by a semi-transparent magenta fill and a solid magenta outline. Image 2 is only a map of WHERE to edit: never paint magenta, outlines or tints in the result.
- Change ONLY what is inside the edit area. Everything outside it must stay identical to Image 1: same people, objects, background, text, colors and lighting.
- Make the new content belong to the photo: match perspective and scale, light direction, shadows, reflections, color temperature, contrast, sharpness, depth of field and grain/noise of the surrounding pixels. No visible seams, halos or pasted look at the border of the edit area.
- Images 3 and onward (if present) are REFERENCES. Use each reference only for the role described under REFERENCES and ignore everything else in it (its background, framing and lighting)."""

DEFAULT_INSTRUCTION = (
    "Replace what is inside the edit area with: <DESCREVA AQUI O QUE DEVE APARECER NA ÁREA>."
)

DEFAULT_ROLES = """REFERENCES (Image 3 = REF 1, Image 4 = REF 2, ... Image 12 = REF 10):
- Image 3: <PAPEL DA REF 1 — ex.: the exact object to insert; keep its shape, colors, materials and logos>
- Image 4: <PAPEL DA REF 2 — ex.: fabric/material texture only>
(Apague as linhas das referências que não usar. Sem referências: escreva "none".)"""

INSTRUCTION_DELIMITER = "\n\nEDIT INSTRUCTION:\n"
ROLES_DELIMITER = "\n\n"

# ── Parâmetros padrão (o client pode sobrescrever) ─────────────────────────────
DEFAULTS = {
    "model": MODEL_NB2,
    "resolution": "1K",          # 1K ≈ US$0,08 · 2K ≈ 0,12 · 4K ≈ 0,18 (badge do nó)
    "thinking_level": "HIGH",    # HIGH = melhor perspectiva/oclusão/luz
    "crop_size": 1024,           # mantenha igual à resolução: 1K→1024 · 2K→2048 · 4K→4096
    "context_factor": 2.0,       # quanto contexto em volta da máscara vai junto para a IA
    "mask_expand": 8,            # px: engorda a máscara antes de recortar
    "mask_blend": 32,            # px: suavização da borda na recolagem (feathering)
    "map_opacity": 0.45,         # opacidade do magenta no mapa (Image 2)
    "seed": 42,
    # recorte/recolagem (pixels, sem IA) na GPU: 6000×4000 → ~3,3 s (cpu) vs ~2,6 s (gpu) no grafo todo,
    # garantia de pixels idêntica. Sem CUDA o nó usa o dispositivo do ComfyUI (cpu).
    "crop_device": "gpu (much faster)",
}
RESOLUTION_TO_CROP = {"1K": 1024, "2K": 2048, "4K": 4096}

# ── IDs dos nós (estáveis: o client e a UI usam os mesmos) ─────────────────────
ID_BASE = "10"
ID_INSTRUCTION, ID_ROLES, ID_RULES, ID_CONCAT1, ID_CONCAT2 = "20", "21", "22", "23", "24"
REF_IDS = [str(30 + i) for i in range(MAX_REFS)]  # 30..39
ID_CROP, ID_THRESH, ID_SIZE, ID_COLOR, ID_BLEND = "40", "41", "42", "43", "44"
ID_TINT, ID_GROW, ID_RING, ID_MAP, ID_MAP_PREVIEW = "45", "46", "47", "48", "49"
ID_MODEL, ID_RAW_PREVIEW = "50", "51"
ID_STITCH, ID_SAVE, ID_SAVE_WS, ID_SAFE_MASK, ID_FINAL = "60", "61", "62", "63", "64"
ID_LOCK_IMG, ID_LOCK_BLUR, ID_LOCK_MASK = "65", "66", "67"
LOCK_FEATHER = 16  # px de transição suave da trava (ImageBlur blur_radius); sigma 6

CROP_WIDGETS = [  # ordem = input_order do InpaintCropImproved (sem "image")
    "downscale_algorithm", "upscale_algorithm", "preresize", "preresize_mode",
    "preresize_min_width", "preresize_min_height", "preresize_max_width", "preresize_max_height",
    "mask_fill_holes", "mask_expand_pixels", "mask_invert", "mask_blend_pixels", "mask_hipass_filter",
    "extend_for_outpainting", "extend_up_factor", "extend_down_factor", "extend_left_factor",
    "extend_right_factor", "context_from_mask_extend_factor", "output_resize_to_target_size",
    "output_target_width", "output_target_height", "output_padding", "device_mode",
]


def safety_margin(p: dict) -> int:
    """Quanto a trava engorda a máscara pintada (GrowMask). Cobre a borda suavizada do Stitch
    (expand + blur de blend) com folga. Quando o quadrado de contexto não cabe na foto, o Inpaint
    Crop acolchoa o canvas com máscara 1 e o blend vaza para dentro da borda da foto (medido: 20–42 px);
    a trava devolve o original além desse raio, com transição suave de LOCK_FEATHER px."""
    return int(p["mask_expand"]) + 2 * int(p["mask_blend"])


def guarantee_px(p: dict) -> int:
    """Distância (px) da área pintada a partir da qual o pixel sai IDÊNTICO ao decodificado."""
    return safety_margin(p) + LOCK_FEATHER


def crop_values(p: dict) -> dict:
    s = int(p["crop_size"])
    return {
        "downscale_algorithm": "bilinear", "upscale_algorithm": "bicubic",
        "preresize": False, "preresize_mode": "ensure minimum resolution",
        "preresize_min_width": 1024, "preresize_min_height": 1024,
        "preresize_max_width": 16384, "preresize_max_height": 16384,
        "mask_fill_holes": False,  # True encheria um contorno pintado, mas a trava (máscara crua) desfaria o miolo
        "mask_expand_pixels": int(p["mask_expand"]), "mask_invert": False,
        "mask_blend_pixels": int(p["mask_blend"]), "mask_hipass_filter": 0.1,
        "extend_for_outpainting": False, "extend_up_factor": 1.0, "extend_down_factor": 1.0,
        "extend_left_factor": 1.0, "extend_right_factor": 1.0,
        "context_from_mask_extend_factor": float(p["context_factor"]),
        "output_resize_to_target_size": True, "output_target_width": s, "output_target_height": s,
        "output_padding": "32", "device_mode": p.get("crop_device", DEFAULTS["crop_device"]),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Formato API
# ══════════════════════════════════════════════════════════════════════════════
def build_api_prompt(
    base_image: str,
    ref_images: list[str],
    instruction: str = DEFAULT_INSTRUCTION,
    roles: str = DEFAULT_ROLES,
    *,
    params: dict | None = None,
    output: str = "websocket",       # "websocket" | "disk" | "both"
    simulate: bool = False,
    filename_prefix: str = "inpaint-multiref/api",
) -> dict:
    """Monta o grafo no formato API (o que vai em ``POST /prompt``).

    ``base_image``  nome do arquivo em ``input/`` cujo canal ALFA é a máscara
                    (transparente = área a editar) — exatamente o que o MaskEditor
                    ou o ``/upload/mask`` produzem.
    ``ref_images``  0..10 nomes em ``input/``. Viram ``image_3..image_12`` do modelo,
                    em ordem e sem buracos (o nó descarta slots vazios e renumeraria).
    ``simulate``    troca a IA por "devolver o mapa magenta" — testa recorte, mapa,
                    recolagem e WebSocket SEM gastar crédito.
    """
    if len(ref_images) > MAX_REFS:
        raise ValueError(f"no máximo {MAX_REFS} referências (recebi {len(ref_images)})")
    p = {**DEFAULTS, **(params or {})}
    if "crop_size" not in (params or {}):
        p["crop_size"] = RESOLUTION_TO_CROP.get(p["resolution"], 1024)
    if p["model"] == MODEL_NB2_LITE and p["resolution"] != "1K":
        raise ValueError("Nano Banana 2 Lite só tem resolução 1K")

    g: dict[str, dict] = {}

    def node(nid: str, cls: str, title: str, **inputs):
        g[nid] = {"class_type": cls, "inputs": inputs, "_meta": {"title": title}}

    # ① entrada
    node(ID_BASE, "LoadImage", "BASE", image=base_image)
    # ④ máscara → recorte 1:1 + mapa magenta (pixels, sem IA)
    node(ID_CROP, "InpaintCropImproved", "Recorta área + contexto",
         image=[ID_BASE, 0], mask=[ID_BASE, 1], **crop_values(p))
    node(ID_THRESH, "ThresholdMask", "Máscara nítida p/ o mapa", mask=[ID_CROP, 2], value=0.5)
    node(ID_SIZE, "GetImageSize", "Tamanho do recorte", image=[ID_CROP, 1])
    node(ID_COLOR, "EmptyImage", "Cor do mapa", width=[ID_SIZE, 0], height=[ID_SIZE, 1],
         batch_size=1, color=MAGENTA)
    node(ID_BLEND, "ImageBlend", "Recorte tingido", image1=[ID_CROP, 1], image2=[ID_COLOR, 0],
         blend_factor=float(p["map_opacity"]), blend_mode="normal")
    node(ID_TINT, "ImageCompositeMasked", "Tinge só a área", destination=[ID_CROP, 1],
         source=[ID_BLEND, 0], x=0, y=0, resize_source=False, mask=[ID_THRESH, 0])
    node(ID_GROW, "GrowMask", "Contorno (externo)", mask=[ID_THRESH, 0], expand=6, tapered_corners=True)
    node(ID_RING, "MaskComposite", "Contorno (anel)", destination=[ID_GROW, 0], source=[ID_THRESH, 0],
         x=0, y=0, operation="subtract")
    node(ID_MAP, "ImageCompositeMasked", "Mapa da área (Image 2)", destination=[ID_TINT, 0],
         source=[ID_COLOR, 0], x=0, y=0, resize_source=False, mask=[ID_RING, 0])

    if simulate:
        edited = [ID_MAP, 0]
    else:
        # ② texto → prompt
        node(ID_INSTRUCTION, "PrimitiveStringMultiline", "O que fazer", value=instruction)
        node(ID_ROLES, "PrimitiveStringMultiline", "Papel das referências", value=roles)
        node(ID_RULES, "PrimitiveStringMultiline", "Regras fixas", value=RULES_TEXT)
        node(ID_CONCAT1, "StringConcatenate", "regras + instrução", string_a=[ID_RULES, 0],
             string_b=[ID_INSTRUCTION, 0], delimiter=INSTRUCTION_DELIMITER)
        node(ID_CONCAT2, "StringConcatenate", "+ referências", string_a=[ID_CONCAT1, 0],
             string_b=[ID_ROLES, 0], delimiter=ROLES_DELIMITER)
        # ③ referências: injeção procedural — 1 LoadImage por referência enviada
        model_inputs = {
            "prompt": [ID_CONCAT2, 0],
            "model": p["model"],
            "model.aspect_ratio": "1:1",
            "model.resolution": p["resolution"],
            "model.thinking_level": p["thinking_level"],
            "model.images.image_1": [ID_CROP, 1],
            "model.images.image_2": [ID_MAP, 0],
            "seed": int(p["seed"]),
            "response_modalities": "IMAGE",
            "system_prompt": NB2_SYSTEM_PROMPT,
            "temperature": 1.0,
            "top_p": 0.95,
        }
        for i, name in enumerate(ref_images):
            rid = REF_IDS[i]
            node(rid, "LoadImage", f"REF {i + 1}", image=name)
            model_inputs[f"model.images.image_{FIRST_REF_SLOT + i}"] = [rid, 0]
        node(ID_MODEL, "GeminiNanoBanana2V2", "Nano Banana 2", **model_inputs)
        edited = [ID_MODEL, 0]

    # ⑥ recolagem + saída
    node(ID_STITCH, "InpaintStitchImproved", "Recola só a área", stitcher=[ID_CROP, 0], inpainted_image=edited)
    # trava de segurança: além de (expand + 2×blend) px da área pintada, volta o pixel ORIGINAL
    node(ID_SAFE_MASK, "GrowMask", "Limite de segurança", mask=[ID_BASE, 1],
         expand=safety_margin(p), tapered_corners=True)
    node(ID_LOCK_IMG, "MaskToImage", "Limite → imagem", mask=[ID_SAFE_MASK, 0])
    node(ID_LOCK_BLUR, "ImageBlur", "Borda suave da trava", image=[ID_LOCK_IMG, 0],
         blur_radius=LOCK_FEATHER, sigma=6.0)
    node(ID_LOCK_MASK, "ImageToMask", "Limite suave", image=[ID_LOCK_BLUR, 0], channel="red")
    node(ID_FINAL, "ImageCompositeMasked", "Trava: fora do limite = original", destination=[ID_BASE, 0],
         source=[ID_STITCH, 0], x=0, y=0, resize_source=False, mask=[ID_LOCK_MASK, 0])
    if output in ("websocket", "both"):
        node(ID_SAVE_WS, "SaveImageWebsocket", "Resultado via WebSocket", images=[ID_FINAL, 0])
    if output in ("disk", "both"):
        node(ID_SAVE, "SaveImage", "Resultado em disco", images=[ID_FINAL, 0], filename_prefix=filename_prefix)
    return g


# ══════════════════════════════════════════════════════════════════════════════
#  Formato UI (LiteGraph) — com grupos e notas
# ══════════════════════════════════════════════════════════════════════════════
GREEN = ("#232", "#353")    # você mexe aqui
YELLOW = ("#432", "#653")   # texto que vai para a IA
BLUE = ("#223", "#335")     # nuvem (paga crédito)
CYAN = ("#233", "#355")     # saída
NOTE = ("#222", "#000")


def _md(name: str) -> str:
    return (HERE / "notes" / name).read_text(encoding="utf-8")


def build_ui_workflow() -> dict:
    p = dict(DEFAULTS)
    nodes: list[dict] = []
    links: list[list] = []
    by_id: dict[int, dict] = {}

    def add(nid, ntype, title, pos, size, *, widgets=None, inputs=None, outputs=None,
            color=None, mode=0, extra_props=None, cnr="comfy-core"):
        n = {
            "id": int(nid), "type": ntype, "pos": list(pos), "size": list(size), "flags": {},
            "order": len(nodes), "mode": mode, "inputs": inputs or [], "outputs": outputs or [],
            "properties": {}, "widgets_values": widgets if widgets is not None else [],
        }
        if ntype not in ("MarkdownNote",):
            n["properties"] = {"Node name for S&R": ntype}
            if cnr:
                n["properties"]["cnr_id"] = cnr
        if extra_props:
            n["properties"].update(extra_props)
        if title:
            n["title"] = title
        if color:
            n["color"], n["bgcolor"] = color
        nodes.append(n)
        by_id[int(nid)] = n
        return n

    def out(name, typ):
        return {"name": name, "type": typ, "links": []}

    def inp(name, typ, widget=None, label=None, shape=None):
        d = {"name": name, "type": typ, "link": None}
        if label:
            d["label"] = label
        if shape is not None:
            d["shape"] = shape
        if widget:
            d["widget"] = {"name": widget}
        return d

    def link(src, src_slot, dst, dst_input_name):
        s, d = by_id[int(src)], by_id[int(dst)]
        lid = len(links) + 1
        slot = next(i for i, x in enumerate(d["inputs"]) if x["name"] == dst_input_name)
        typ = s["outputs"][src_slot]["type"]
        links.append([lid, int(src), src_slot, int(dst), slot, typ])
        s["outputs"][src_slot]["links"].append(lid)
        d["inputs"][slot]["link"] = lid

    # ── notas (linha de cima) ────────────────────────────────────────────────
    add(1, "MarkdownNote", "📖 LEIA PRIMEIRO — como usar", (0, -1180), (900, 1120),
        widgets=[_md("01_leia_primeiro.md")], color=NOTE)
    add(2, "MarkdownNote", "🧭 Do guia (Flux Fill + Redux LOCAL) para a API", (940, -1180), (980, 1120),
        widgets=[_md("02_guia_para_api.md")], color=NOTE)
    add(3, "MarkdownNote", "🔧 Ajustes finos + problemas comuns", (1960, -1180), (860, 1120),
        widgets=[_md("03_ajustes.md")], color=NOTE)
    add(4, "MarkdownNote", "🔌 Rodar por script (REST + WebSocket)", (2860, -1180), (900, 1120),
        widgets=[_md("04_api_script.md")], color=NOTE)

    # ── ① BASE ───────────────────────────────────────────────────────────────
    add(ID_BASE, "LoadImage", "① BASE — a foto (pinte a área: botão direito → Open in MaskEditor)",
        (20, 50), (400, 560), widgets=["example.png", "image"],
        inputs=[inp("image", "COMBO", widget="image")],
        outputs=[out("IMAGE", "IMAGE"), out("MASK", "MASK")], color=GREEN)

    # ── ② TEXTO ──────────────────────────────────────────────────────────────
    add(ID_INSTRUCTION, "PrimitiveStringMultiline", "② ✏️ O QUE FAZER NA ÁREA (escreva aqui)",
        (480, 50), (620, 210), widgets=[DEFAULT_INSTRUCTION],
        inputs=[inp("value", "STRING", widget="value")], outputs=[out("STRING", "STRING")], color=GREEN)
    add(ID_ROLES, "PrimitiveStringMultiline", "② 🖼️ PAPEL DE CADA REFERÊNCIA (Image 3 = REF 1 …)",
        (480, 290), (620, 200), widgets=[DEFAULT_ROLES],
        inputs=[inp("value", "STRING", widget="value")], outputs=[out("STRING", "STRING")], color=GREEN)
    add(ID_RULES, "PrimitiveStringMultiline", "② 🔒 Regras fixas (não precisa mexer)",
        (480, 520), (620, 300), widgets=[RULES_TEXT],
        inputs=[inp("value", "STRING", widget="value")], outputs=[out("STRING", "STRING")], color=YELLOW)
    add(ID_CONCAT1, "StringConcatenate", "junta: regras + instrução", (1140, 520), (270, 150),
        widgets=["", "", INSTRUCTION_DELIMITER],
        inputs=[inp("string_a", "STRING", widget="string_a"), inp("string_b", "STRING", widget="string_b")],
        outputs=[out("STRING", "STRING")], color=YELLOW)
    add(ID_CONCAT2, "StringConcatenate", "junta: + referências  → prompt", (1140, 700), (270, 150),
        widgets=["", "", ROLES_DELIMITER],
        inputs=[inp("string_a", "STRING", widget="string_a"), inp("string_b", "STRING", widget="string_b")],
        outputs=[out("STRING", "STRING")], color=YELLOW)

    # ── ③ REFERÊNCIAS (bypass = desligado) ──────────────────────────────────
    for i, rid in enumerate(REF_IDS):
        col, row = i % 5, i // 5
        add(rid, "LoadImage", f"③ REF {i + 1}  →  Image {FIRST_REF_SLOT + i}   (Ctrl+B liga/desliga)",
            (20 + col * 285, 1010 + row * 420), (270, 390), widgets=["example.png", "image"],
            inputs=[inp("image", "COMBO", widget="image")],
            outputs=[out("IMAGE", "IMAGE"), out("MASK", "MASK")], color=GREEN, mode=4)

    # ── ④ MÁSCARA → RECORTE + MAPA ──────────────────────────────────────────
    cv = crop_values(p)
    add(ID_CROP, "InpaintCropImproved", "④ ✂️ Recorta a área + contexto (1:1, sem IA)",
        (1480, 50), (360, 860), widgets=[cv[k] for k in CROP_WIDGETS],
        inputs=[inp("image", "IMAGE"), inp("mask", "MASK", shape=7), inp("optional_context_mask", "MASK", shape=7)],
        outputs=[out("stitcher", "STITCHER"), out("cropped_image", "IMAGE"), out("cropped_mask", "MASK")],
        cnr=None, extra_props={"aux_id": "lquesada/ComfyUI-Inpaint-CropAndStitch"})
    add(ID_THRESH, "ThresholdMask", "máscara nítida", (1880, 50), (240, 82), widgets=[0.5],
        inputs=[inp("mask", "MASK")], outputs=[out("MASK", "MASK")])
    add(ID_SIZE, "GetImageSize", "tamanho do recorte", (1880, 170), (240, 120),
        inputs=[inp("image", "IMAGE")], outputs=[out("width", "INT"), out("height", "INT"), out("batch_size", "INT")])
    add(ID_COLOR, "EmptyImage", "cor do mapa (16711935 = magenta)", (1880, 330), (240, 170),
        widgets=[1024, 1024, 1, MAGENTA],
        inputs=[inp("width", "INT", widget="width"), inp("height", "INT", widget="height")],
        outputs=[out("IMAGE", "IMAGE")])
    add(ID_BLEND, "ImageBlend", "tinge o recorte (opacidade)", (1880, 540), (240, 110),
        widgets=[p["map_opacity"], "normal"], inputs=[inp("image1", "IMAGE"), inp("image2", "IMAGE")],
        outputs=[out("IMAGE", "IMAGE")])
    add(ID_TINT, "ImageCompositeMasked", "tinge SÓ a área", (2160, 50), (240, 140), widgets=[0, 0, False],
        inputs=[inp("destination", "IMAGE"), inp("source", "IMAGE"), inp("mask", "MASK", shape=7)],
        outputs=[out("IMAGE", "IMAGE")])
    add(ID_GROW, "GrowMask", "contorno: engorda 6 px", (2160, 230), (240, 90), widgets=[6, True],
        inputs=[inp("mask", "MASK")], outputs=[out("MASK", "MASK")])
    add(ID_RING, "MaskComposite", "contorno: anel (engordada − original)", (2160, 360), (240, 130),
        widgets=[0, 0, "subtract"], inputs=[inp("destination", "MASK"), inp("source", "MASK")],
        outputs=[out("MASK", "MASK")])
    add(ID_MAP, "ImageCompositeMasked", "④ MAPA DA ÁREA → Image 2", (2160, 530), (240, 140),
        widgets=[0, 0, False],
        inputs=[inp("destination", "IMAGE"), inp("source", "IMAGE"), inp("mask", "MASK", shape=7)],
        outputs=[out("IMAGE", "IMAGE")])
    add(ID_MAP_PREVIEW, "PreviewImage", "👁️ o que a IA recebe (Image 2)", (1880, 700), (520, 520),
        inputs=[inp("images", "IMAGE")])

    # ── ⑤ NUVEM ──────────────────────────────────────────────────────────────
    model_inputs = [inp("prompt", "STRING", widget="prompt")]
    for k in range(1, FIRST_REF_SLOT + MAX_REFS + 1):  # image_1..image_13 (1 slot livre, como o frontend faz)
        model_inputs.append(inp(f"model.images.image_{k}", "IMAGE", label=f"image_{k}", shape=7))
    model_inputs.append(inp("model.files", "GEMINI_INPUT_FILES", label="files", shape=7))
    add(ID_MODEL, "GeminiNanoBanana2V2", "⑤ ☁️ Nano Banana 2 — edita a área (paga crédito)",
        (2480, 50), (460, 940),
        widgets=["", p["model"], "1:1", p["resolution"], p["thinking_level"], p["seed"], "randomize",
                 "IMAGE", NB2_SYSTEM_PROMPT, 1.0, 0.95],
        inputs=model_inputs,
        outputs=[out("IMAGE", "IMAGE"), out("STRING", "STRING"), out("thought_image", "IMAGE")], color=BLUE)
    add(ID_RAW_PREVIEW, "PreviewImage", "👁️ saída crua da IA (só o recorte)", (2480, 1030), (460, 480),
        inputs=[inp("images", "IMAGE")])

    # ── ⑥ RECOLAGEM + SAÍDA ─────────────────────────────────────────────────
    add(ID_STITCH, "InpaintStitchImproved", "⑥ ✂️ Recola SÓ a área na foto original", (3020, 50), (330, 80),
        inputs=[inp("stitcher", "STITCHER"), inp("inpainted_image", "IMAGE")], outputs=[out("image", "IMAGE")],
        cnr=None, extra_props={"aux_id": "lquesada/ComfyUI-Inpaint-CropAndStitch"})
    add(ID_SAFE_MASK, "GrowMask", "⑥ 🛡️ limite de segurança (≥ expand + 2×blend)", (3020, 170), (330, 90),
        widgets=[safety_margin(p), True], inputs=[inp("mask", "MASK")], outputs=[out("MASK", "MASK")])
    add(ID_LOCK_IMG, "MaskToImage", "limite → imagem", (3020, 300), (330, 30),
        inputs=[inp("mask", "MASK")], outputs=[out("IMAGE", "IMAGE")])
    add(ID_LOCK_BLUR, "ImageBlur", f"borda suave da trava ({LOCK_FEATHER} px)", (3020, 380), (330, 90),
        widgets=[LOCK_FEATHER, 6.0], inputs=[inp("image", "IMAGE")], outputs=[out("IMAGE", "IMAGE")])
    add(ID_LOCK_MASK, "ImageToMask", "imagem → limite suave", (3020, 510), (330, 60), widgets=["red"],
        inputs=[inp("image", "IMAGE")], outputs=[out("MASK", "MASK")])
    add(ID_FINAL, "ImageCompositeMasked", "⑥ 🛡️ trava: longe da área = pixel ORIGINAL", (3020, 610), (330, 140),
        widgets=[0, 0, False],
        inputs=[inp("destination", "IMAGE"), inp("source", "IMAGE"), inp("mask", "MASK", shape=7)],
        outputs=[out("IMAGE", "IMAGE")])
    add(ID_SAVE, "SaveImage", "⑥ 💾 RESULTADO FINAL (output/inpaint-multiref/)", (3020, 790), (620, 700),
        widgets=["inpaint-multiref/final"], inputs=[inp("images", "IMAGE")], color=CYAN)

    # ── ligações ────────────────────────────────────────────────────────────
    link(ID_BASE, 0, ID_CROP, "image")
    link(ID_BASE, 1, ID_CROP, "mask")
    link(ID_RULES, 0, ID_CONCAT1, "string_a")
    link(ID_INSTRUCTION, 0, ID_CONCAT1, "string_b")
    link(ID_CONCAT1, 0, ID_CONCAT2, "string_a")
    link(ID_ROLES, 0, ID_CONCAT2, "string_b")
    link(ID_CROP, 2, ID_THRESH, "mask")
    link(ID_CROP, 1, ID_SIZE, "image")
    link(ID_SIZE, 0, ID_COLOR, "width")
    link(ID_SIZE, 1, ID_COLOR, "height")
    link(ID_CROP, 1, ID_BLEND, "image1")
    link(ID_COLOR, 0, ID_BLEND, "image2")
    link(ID_CROP, 1, ID_TINT, "destination")
    link(ID_BLEND, 0, ID_TINT, "source")
    link(ID_THRESH, 0, ID_TINT, "mask")
    link(ID_THRESH, 0, ID_GROW, "mask")
    link(ID_GROW, 0, ID_RING, "destination")
    link(ID_THRESH, 0, ID_RING, "source")
    link(ID_TINT, 0, ID_MAP, "destination")
    link(ID_COLOR, 0, ID_MAP, "source")
    link(ID_RING, 0, ID_MAP, "mask")
    link(ID_MAP, 0, ID_MAP_PREVIEW, "images")
    link(ID_CONCAT2, 0, ID_MODEL, "prompt")
    link(ID_CROP, 1, ID_MODEL, "model.images.image_1")
    link(ID_MAP, 0, ID_MODEL, "model.images.image_2")
    for i, rid in enumerate(REF_IDS):
        link(rid, 0, ID_MODEL, f"model.images.image_{FIRST_REF_SLOT + i}")
    link(ID_MODEL, 0, ID_RAW_PREVIEW, "images")
    link(ID_CROP, 0, ID_STITCH, "stitcher")
    link(ID_MODEL, 0, ID_STITCH, "inpainted_image")
    link(ID_BASE, 1, ID_SAFE_MASK, "mask")
    link(ID_BASE, 0, ID_FINAL, "destination")
    link(ID_STITCH, 0, ID_FINAL, "source")
    link(ID_SAFE_MASK, 0, ID_LOCK_IMG, "mask")
    link(ID_LOCK_IMG, 0, ID_LOCK_BLUR, "image")
    link(ID_LOCK_BLUR, 0, ID_LOCK_MASK, "image")
    link(ID_LOCK_MASK, 0, ID_FINAL, "mask")
    link(ID_FINAL, 0, ID_SAVE, "images")

    for n in nodes:  # o frontend grava null em saída sem ligação
        for o in n["outputs"]:
            if not o["links"]:
                o["links"] = None

    groups = [
        ("① ENTRADA — foto + máscara", (0, -20, 440, 650), "#3f789e"),
        ("② INSTRUÇÕES → prompt (o que fazer + papel das refs)", (460, -20, 970, 890), "#b58b2a"),
        ("③ REFERÊNCIAS — até 10 · roxo = desligado · imagem + Ctrl+B liga · EM ORDEM",
         (0, 940, 1440, 880), "#8A8"),
        ("④ RECORTE 1:1 + MAPA DA ÁREA (local, sem IA, grátis)", (1460, -20, 960, 1260), "#3f5159"),
        ("⑤ NUVEM — paga crédito", (2460, -20, 500, 1550), "#88A"),
        ("⑥ RECOLAGEM + TRAVA → SAÍDA", (3000, -20, 660, 1540), "#a1309b"),
    ]
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "comfyui-agent-skill/image-edit-area-multiref")),
        "revision": 0,
        "last_node_id": max(int(n["id"]) for n in nodes),
        "last_link_id": len(links),
        "nodes": nodes,
        "links": links,
        "groups": [
            {"id": i + 1, "title": t, "bounding": list(b), "color": c, "font_size": 24, "flags": {}}
            for i, (t, b, c) in enumerate(groups)
        ],
        "config": {},
        "extra": {"ds": {"scale": 0.42, "offset": [120, 1260]}},
        "version": 0.4,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Checagem estrutural contra o /object_info ao vivo
# ══════════════════════════════════════════════════════════════════════════════
FRONTEND_ONLY = {"MarkdownNote", "Note"}
# widgets por tipo no formato UI (inclui o control_after_generate do seed e o "upload" do LoadImage)
UI_WIDGET_COUNT = {
    "LoadImage": 2, "PrimitiveStringMultiline": 1, "StringConcatenate": 3, "InpaintCropImproved": 24,
    "ThresholdMask": 1, "GetImageSize": 0, "EmptyImage": 4, "ImageBlend": 2, "ImageCompositeMasked": 3,
    "GrowMask": 2, "MaskComposite": 3, "PreviewImage": 0, "GeminiNanoBanana2V2": 11,
    "InpaintStitchImproved": 0, "SaveImage": 1, "MaskToImage": 0, "ImageBlur": 2, "ImageToMask": 1,
}


def default_server() -> str:
    """COMFY_SERVER, senão COMFY_HOST:COMFY_PORT (as mesmas variáveis do comando `comfyui`)."""
    import os
    return os.environ.get("COMFY_SERVER") or f"{os.environ.get('COMFY_HOST', '127.0.0.1')}:{os.environ.get('COMFY_PORT', '8188')}"


def check(server: str) -> int:
    info = json.load(urllib.request.urlopen(f"http://{server}/object_info", timeout=120))
    wf = json.loads(UI_JSON.read_text(encoding="utf-8"))
    problems = []
    ids = {n["id"] for n in wf["nodes"]}
    link_ids = {lk[0] for lk in wf["links"]}
    for n in wf["nodes"]:
        t = n["type"]
        if t in FRONTEND_ONLY:
            continue
        if t not in info or not info[t].get("python_module"):
            problems.append(f"nó {n['id']} tipo {t} não carregado no servidor")
            continue
        if UI_WIDGET_COUNT.get(t) is not None and len(n["widgets_values"]) != UI_WIDGET_COUNT[t]:
            problems.append(f"nó {n['id']} {t}: {len(n['widgets_values'])} widgets, esperado {UI_WIDGET_COUNT[t]}")
        for i in n["inputs"]:
            if i["link"] is not None and i["link"] not in link_ids:
                problems.append(f"nó {n['id']} input {i['name']} aponta para link inexistente")
    for lk in wf["links"]:
        if lk[1] not in ids or lk[3] not in ids:
            problems.append(f"link {lk[0]} aponta para nó inexistente")
    # valores de COMBO precisam existir no servidor
    crop_req = info["InpaintCropImproved"]["input"]["required"]
    cv = crop_values(DEFAULTS)
    for k, v in cv.items():
        spec = crop_req[k][0]
        if isinstance(spec, list) and v not in spec:
            problems.append(f"InpaintCrop {k}={v!r} fora de {spec}")
    print("\n".join(problems) if problems else "OK: estrutura bate com o /object_info ao vivo")
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-ui", action="store_true", help=f"(re)gera {UI_JSON.name}")
    ap.add_argument("--export-api", metavar="ARQ", help="grava um exemplo do grafo no formato API")
    ap.add_argument("--check", action="store_true", help="confere o .json contra o /object_info ao vivo")
    ap.add_argument("--server", default=default_server())
    a = ap.parse_args(argv)
    if a.write_ui:
        UI_JSON.write_text(json.dumps(build_ui_workflow(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"gravado {UI_JSON}")
    if a.export_api:
        api = build_api_prompt("base.png", ["ref1.png", "ref2.png"], output="both")
        Path(a.export_api).write_text(json.dumps(api, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"gravado {a.export_api}")
    if a.check:
        return check(a.server)
    if not (a.write_ui or a.export_api or a.check):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
