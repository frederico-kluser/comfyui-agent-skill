# workflows-api — bundles que rodam por API online (sem GPU)

Cinco bundles. **Nenhum precisa de GPU.** A maioria paga com **créditos do comfy.org**
(só login, sem chave); um usa **fal.ai** (precisa de `FAL_KEY`); e um roda **de graça, local**.

| Bundle | O que faz | Nó principal | Billing |
|---|---|---|---|
| [`image-edit-nano-banana-2`](image-edit-nano-banana-2/) | 6 edições de foto, um arquivo por processo | `GeminiNanoBanana2` | crédito comfy.org |
| [`image-edit-seedream`](image-edit-seedream/) | As **mesmas** 6 edições, no outro melhor editor | `ByteDanceSeedreamNode` | crédito comfy.org |
| [`video-person-replace`](video-person-replace/) | **Trocar a pessoa de um vídeo que eu forneço** | `Wan2214b_animate_replace_character_fal` | **fal.ai (`FAL_KEY`)** |
| [`video-person-swap-seedance-2`](video-person-swap-seedance-2/) | Gerar um vídeo novo comigo, a partir de referências | `ByteDance2ReferenceNode` | crédito comfy.org |
| [`foto-realismo-celular`](foto-realismo-celular/) | Deixar **qualquer** foto com cara de foto de celular | WAS Suite + KJNodes | **grátis (CPU local)** |

## Vídeo: qual dos dois

Os dois nomes parecem a mesma coisa e **não são**:

| | `video-person-replace` | `video-person-swap-seedance-2` |
|---|---|---|
| Recebe o **seu** vídeo e edita ele | ✅ | ⚠️ usa só como referência |
| Mantém movimento, enquadramento e cortes originais | ✅ | ❌ recria a cena |
| Precisa de prompt | ❌ | ✅ |
| Chave de API | `FAL_KEY` | nenhuma (login) |

👉 **"Quero me colocar num vídeo que eu gravei"** → `video-person-replace`.

## Os 6 processos de imagem (iguais nos dois bundles de imagem)

| # | Processo | BASE (Image 1) | REF 1 (Image 2) | REF 2 (Image 3) |
|---|---|---|---|---|
| 1 | Trocar a roupa | a pessoa | a peça | — |
| 2 | Trocar objetos em cena | a cena | o objeto novo | — |
| 3 | Trocar a pessoa da foto | a cena | a pessoa nova | **2º ângulo** |
| 4 | **Eu na foto** — roupa e pose **da cena** | a cena | **minha** foto | **2º ângulo** |
| 5 | **Eu na foto** — **minha** roupa e pose | a cena | minha foto de corpo inteiro | **2º ângulo** |
| 6 | Trocar o local (+ match de iluminação) | a foto a manter | o novo local | — |

**Um arquivo `.json` por processo.** Abra o que precisa e rode — sem bypass, sem alternar blocos.

## A arquitetura (o que mudou e por quê)

Antes, cada workflow era uma chamada única: `LoadImage → modelo → SaveImage`.
Isso é o que produzia o resultado "colado", com rosto derivando e aspecto de IA. Agora:

```
BASE  ─┐
REF 1 ─┼→ Batch → MODELO (na MENOR resolução) → ┬→ PNG limpo   (encadear)
REF 2 ─┘        (paga crédito)                  └→ ColorMatch → realismo de celular → JPG (entregável)
                                                   └────── CPU local, custo zero ──────┘
```

1. **Resolução no mínimo** — Nano Banana `1K`, Seedream `Custom 1024×1360`, Wan Animate `480p`.
   Mais barato **e** melhor para o look pretendido.
2. **Duas fotos suas** (ângulos diferentes) nos processos de pessoa — trava a identidade.
3. **`ColorMatchV2` contra a foto BASE** — faz a pessoa inserida pertencer àquela foto.
4. **Passe de realismo de celular** — 8 nós locais, custo zero, com valores **medidos** (não chutados).
5. **Duas saídas** — PNG limpo para encadear, JPG tratado como entregável.

### Por que o passe de realismo é em pixel, e não no prompt

Modelo de imagem entrega uma imagem **matematicamente limpa**: gradiente perfeito, pele sem poro,
tudo igualmente nítido, zero ruído de sensor. É esse conjunto que o olho lê como "IA".

Pedir grão no prompt faz o modelo **desenhar** uma imitação de grão — não produz a assinatura do
sensor. Ela só entra depois, em pixel. Detalhe: nenhum fornecedor documenta um conjunto de tokens
de "celular moderno", e não há dado público de eficácia para isso via prompt. O passe de
pós-processamento é **o único lever que dá para medir** — e foi medido aqui.

> ⚠️ **Calibração importa.** A primeira tentativa (aberração 0.35, grão 0.14) ficou horrível:
> franja colorida em toda borda e chuvisco de JPEG velho. Foto de celular moderno **em boa luz é
> limpa** — o que denuncia é o **tone-mapping HDR**, o **over-sharpening** e o **JPEG**, não ruído pesado.

## Começar

```bash
cd image-edit-nano-banana-2 && bash setup.sh     # imagem, por crédito
cd video-person-replace     && bash setup.sh     # vídeo, precisa de FAL_KEY
cd foto-realismo-celular    && bash setup.sh     # grátis, local
```

O `setup.sh` **não instala nada**: confere o servidor, verifica no `/object_info` que os nós existem
(e, no bundle de vídeo, se o `FAL_KEY` está presente) e garante que os `.json` aparecem no painel
*Workflows* — criando o symlink `~/ComfyUI/user/default/workflows/api` → este diretório.

Depois: abra o workflow no `:8188` e **leia o nó "LEIA PRIMEIRO"**.

## Chaves de API

| Bundle | Precisa de chave? | Como obter |
|---|---|---|
| imagem (NB2 / Seedream) | ❌ | Login em `platform.comfy.org` (Settings → User) + créditos |
| `video-person-swap-seedance-2` | ❌ | idem |
| `video-person-replace` | ✅ **`FAL_KEY`** | https://fal.ai → [dashboard/keys](https://fal.ai/dashboard/keys) → *Add key* (aparece **uma vez**) → crédito em [dashboard/billing](https://fal.ai/dashboard/billing) |
| `foto-realismo-celular` | ❌ | nada — roda local |

Grave em `~/ComfyUI/secrets.env` (`chmod 600`, **nunca** commitado) e reinicie o ComfyUI:

```bash
export FAL_KEY=sua-chave-aqui
```

## Antes de gastar crédito

1. Esteja **logado** em `platform.comfy.org` e confira o saldo.
2. Rascunhe barato: Nano Banana em `1K`/`MINIMAL`; vídeo em `480p`, clipe de 3–6 s.
3. Comece pelo bundle de imagem — é ordens de grandeza mais barato que vídeo.

## Convenções destes bundles

- **Prompts em inglês.** Os modelos seguem instrução em inglês com bem mais fidelidade.
  Onde houver `<DESCREVA AQUI ...>`, troque pelo seu texto.
- **A ordem das imagens é o contrato do prompt.** `image0` do `Empilha as imagens` é `Image 1`,
  `image1` é `Image 2`, `image2` é `Image 3`. Google e ByteDance documentam essa convenção
  ordinal explicitamente — inverter inverte o sentido da instrução.
- **As 3 cláusulas finais do prompt** (exposição · luz/lente/grão · look de celular) são o que faz
  o resultado casar com a foto original. Apagou, volta a parecer colagem.
- **Encadeie a partir do PNG limpo**, nunca do JPG tratado (o tratamento acumularia).
- ⚠️ **`largest_size` ≤ ~2048** no passe de realismo. O nó de grão supersampleia 4×; uma imagem
  de 5248×12800 **derrubou o ComfyUI** durante a calibração.

## Status

| Parte | Status |
|---|---|
| Estrutura dos grafos | 🟢 **validada contra o `/object_info` ao vivo** — 16/16 arquivos |
| Cadeia de realismo | 🟢 **executada e medida** nesta máquina |
| Chamadas aos modelos pagos | 🟡 **não executadas** — gastariam crédito. Valide no primeiro load |

## Ver também

- registo CoALA `knowledge-comfyui-api-nodes` — rotas de billing (partner / fal / Replicate), catálogo, seed gates, chaves.
- `.agents/skills/task-package-workflow-project` — como um bundle destes é montado.
- `.agents/skills/task-debug-generation` — quando algo falha.
