# Sprint 10 — Crack tensors e permeabilidade

Concluída em 14/11/2026, integrada ao Run padrão. [ADR 0012](../decisions/0012-crack-tensors-and-permeability.md) detalha fórmulas, unidades, polos, envelope de área e contratos.

| Tarefa | Evidência |
| --- | --- |
| S10-01 | F0 e componentes completos F2/F4/F8 com pesos L²/A; projeções de 361 pontos e arrays imutáveis; referências MATLAB direcionais/isotrópicas/oblíquas. |
| S10-02 | FLO-08 em compute_angles/cache angular, resultado do tensor e um único EZROSE; Run isolado e conjunto com histogramas/rosa. |
| S10-03 | P, K, autovalores simétricos e projeção polar; comparações nativas com tolerâncias dimensionais. |
| S10-04 | Aberturas fixa/escalada, a/b e λ dentro dos limites; apenas parâmetros ativos validados. |
| S10-05 | Abertura zero, λ zero, área inválida e interrupção tratados; λ não deriva da conectividade. |
| S10-06 | Casos direcionais/isotrópicos, simetria exata, escala de unidades, dependência cúbica e 10 mil segmentos sem matrizes N×N. |
| S10-07 | Dois PNGs MATLAB, layouts/ticks/fontes/legenda capturados, composição calibrada e valores impressos Maximum/Minimum comparados. |

[Referências nativas](../../tests/reference/sprint10/native_provenance.json) foram executadas no MATLAB R2024b Update 9, sem modificar os fontes. [Comparação numérica](../../tests/reference/sprint10/native_comparison.json): máximo erro de componentes/projeções ~1.97e−15; K/projeções ~2.12e−22 nos casos testados; zeros exatos. Não houve alteração das tolerâncias da Sprint 0.

[Evidências Python](../../tests/reference/sprint10/validation.json): dez PNGs 4724×4724/600 dpi, dez miniaturas revisadas, cinco EZROSE, tensores/P/K/projeções/autovalores e parâmetros para TXT, SVG, Hough, padrão nativo e zero. Área tensoral segue o envelope dos traços, que pode diferir da tela raster. Imagens de uma única linha não recebem uma área fictícia.

[checks.json](../../tests/reference/sprint10/checks.json) registra testes, pacote fora da raiz e integridade dos originais. A inspeção/calibração visual não substitui a homologação integral por regiões/SSIM e por plataforma da Sprint 16.

**558 testes passaram**, com 68 novos sobre a baseline de 490. As 1631 advertências são deprecações do backend Qt/Matplotlib. Pacote verificado fora da raiz, com onze PNGs 600 dpi e ambos os TXT acoplados.

Reprodução: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint1011.py`. MATLAB só é necessário para recapturar referências; a aplicação opera offline sem MATLAB.
