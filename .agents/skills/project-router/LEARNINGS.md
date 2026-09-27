> **MEMÓRIA APOSENTADA (2026-09-27):** o conteúdo deste ficheiro foi migrado para a memória CoALA local do repositório (`.agents/comfyui-agent-skill-coala-memory-agent-skill/`). Fica só como **fonte histórica** — não escrever mais aqui. Aprendizado novo: `python3 .agents/comfyui-agent-skill-coala-memory-agent-skill/scripts/coala.py add --type episodic --content "…"`.

# LEARNINGS — project-router

> Memória episódica desta skill (erros de roteamento). Append-only durante o trabalho
> (data + fonte: usuário > inferência). `meta-consolidation` deduplica/promove/poda
> periodicamente. Revisão humana via git diff.

<!-- Formato de entrada:
## AAAA-MM-DD — <título curto>
- **Tarefa**: <pedido do usuário>
- **Cadeia escolhida**: <skills>
- **Cadeia correta**: <skills>
- **Causa**: <description ambígua? domínio sobreposto? skill faltante?>
- **Ação**: refinar description de X / criar skill / atualizar catalog.md
-->

## 2026-06-26 — Separar/recortar assets de imagem por texto → rota **API**, não local
- **Tarefa**: "pasta de workflows: mando uma imagem + contexto, nomeio cada elemento em texto, recebo cada asset recortado com fundo transparente" (separar assets de UIs geradas por IA).
- **Cadeia escolhida** (inicial): `task-package-workflow-project` + `knowledge-image-masking` + `knowledge-image-enhance` → **workflows-cloud** (SAM/BiRefNet local; cheguei a propor rodar no 8GB local).
- **Cadeia correta**: `task-package-workflow-project` + **`knowledge-comfyui-api-nodes`** (+ `knowledge-comfyui-api` p/ o script) → **workflows-api**. `NanoBananaPro_fal` (isola por texto) + `RecraftRemoveBackgroundNode` (alpha).
- **Causa**: as descriptions de `knowledge-image-masking`/`-enhance` ("segmentar/remover fundo") puxaram p/ os nós LOCAIS; pesei demais a nota "máscara é local" e apliquei mal a regra dos 8GB→API (ela vale p/ DIFUSÃO; aqui o usuário quer o MELHOR modelo e isolar+remover-fundo TEM rota API). Usuário corrigiu enfaticamente ("quero o melhor, via API + comfy credits").
- **Ação**: ao rotear "separar/recortar/extrair asset(s) de imagem por texto", oferecer a rota **API** (Nano Banana Pro isola + Recraft remove-bg) como **primária** quando o pedido prioriza qualidade/sem-GPU; manter local (SAM/BiRefNet) só como alternativa de pixel-exato. Cruza com LEARNINGS de `knowledge-comfyui-api-nodes` (2026-06-26).
