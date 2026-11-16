# Sprint 7 — Maps: intensidade, densidade e amostragem circular

Concluída em 14/11/2026: oito tarefas S07 implementadas. O usuário autorizou **“Corrigir a contagem geométrica”** após receber a reprodução concreta da diferença Q-20. [ADR 0008](../decisions/0008-circular-sampling.md) registra a decisão, políticas de tangência/borda, grade, fórmulas, aparência e TXT.

| Tarefa | Evidência |
| --- | --- |
| S07-01 | N no lado menor, r=.99×passo/2, floor no lado maior, ordem aritmética original; testes quadrados, retangulares e transladados. |
| S07-02 | Interseções finitas por segmento, tangente=1, extremos na borda incluídos em n; m estritamente interno, por segmento; fallback racional sem snap. Q-20 aprovada e medida. |
| S07-03 | P21=n/(4r), P20=m/(2πr²); escala muda P21 por fator linear e P20 por fator quadrático, preservando contagens. |
| S07-04 | Círculos vermelhos e traços na cor primária; heatmaps origin lower, hot invertida, extensão de meio passo, aspecto igual, flips e barras inferiores. |
| S07-05 | Comprimento total/área e segmentos/área separados das médias locais, registrados somente conforme os mapas selecionados. |
| S07-06 | Dois TXT gerados por qualquer seleção, cache único por Run, ordem X/Y e formato fixo original; falha de staging preserva destinos anteriores. |
| S07-07 | Horizontais/verticais/oblíquas, translações, reversão dos segmentos, tangências exatas e adjacentes, bordas, janelas vazias, área zero e limites de memória. |
| S07-08 | Run e figuras/arrays/TXT com TXT, SVG multicolorido e Hough; Macduff/Orkney suplementares; testes Qt de seleção isolada e conjunta, cancelamento e pacote fora da raiz. |

**376 testes passaram**, 57 novos sobre a baseline da Sprint 6. As 574 advertências são deprecações existentes no backend Qt do Matplotlib. Nenhuma dependência foi alterada; os 164 arquivos originais foram conferidos por SHA-256 e continuam intactos. [checks.json](../../tests/reference/sprint7/checks.json) registra teste, pacote e auditoria de artefatos.

[validation.json](../../tests/reference/sprint7/validation.json) referencia nove PNGs a 4724×4724/600 dpi, nove miniaturas QA, seis TXT, arrays completos, parâmetros e hashes. Figuras revisadas quanto a círculos/raio, margem branca de imagesc, cores, títulos, unidades e barras. TXT e SVG deste caso têm geometria idêntica e diferem nas cores por traço: a figura circular usa sColour, portanto seus PNGs e os campos locais são iguais, como previsto no contrato original.

| Entrada | Grade (ny,nx) | Raio | P21 global | P20 global |
| --- | --- | --- | --- | --- |
| mixed TXT / SVG multicolorido, pixels | 5×3 | .495 | .4583333333 | .125 |
| Hough rectangular, 2 pixels/metre | 3×7 | 1.485 | .1440972222 | .0104166667 |
| Hough MacduffBinary, pixels | 12×12 | 9.7476923077 | .2975587715 | .0229949951 |
| Hough Orkney1aBinary, pixels | 12×12 | 19.4953846154 | .0179760137 | .0006446838 |

Para TXT/SVG, a média local P21=.1683501684 e P20=.0433030488, evidenciando a distinção dos globais. Os valores Hough dependem da extração Python já documentada na Sprint 6. [Reprodução Q-20](../../tests/reference/sprint7/q20_static_reproduction.json) guarda resultados analíticos corrigidos e tradução estática do fonte, com checksum e autorização. Não é execução MATLAB.

Limitações explícitas: precisão textual histórica de uma casa nos centros; proteção de exibição para mapas todos zero; limite conservador de trabalho 256 MiB; interrupção entre janelas; substituição atômica por arquivo, sem transação conjunta. Paleta hot é reconstrução nominal congelada, ainda sem comparação RGB nativa. Graphs/ALONG reutilizará esta decisão na Sprint 13. MATLAB/Octave indisponíveis impedem homologação nativa e SSIM; tolerâncias da Sprint 0 permanecem intactas.

Reprodução: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint7.py` e `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`.
