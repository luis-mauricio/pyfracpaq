# Sprint 3 — Tema MATLAB, mapas básicos e Angles

Execução em 13/11/2026. As nove tarefas S03 foram implementadas e conferidas no escopo de fontes, casos analíticos e referências documentais disponíveis. Itens marcados das Sprints 0–2 preservados. A aprovação de paridade contra uma execução MATLAB continua pendente.

| Tarefa | Evidência |
| --- | --- |
| S03-01 | fracpaq_matlab.mplstyle, QSS/Fusion reaproveitado, helpers de eixos/texto/legenda/barras; 18 tabelas cmocean congeladas com proveniência, interpolação e inversão testadas. AUX-08 restante na Sprint 15. |
| S03-02 | MAP-01 com polilinhas reais e MAP-02 com extremidades/centros nas posições do Dataset; marcadores, clipping no domínio e flips testados. |
| S03-03 | MAP-04/05/06 conectados ao Run; haline/phase, unidades e barras inferiores; índice linear/barra log preservados em Q-17. |
| S03-04 | round MATLAB, norte, duplicação e quatro combinações de flip; extremos ±360 e assimetrias documentados em Q-10. |
| S03-05 | Hist com centros legados e n+1 classes para 10/20/30/50, empates/caudas, eixos absoluto/percentual vinculados. |
| S03-06 | Rosa com polígonos de área igual, quatro larguras, contagens e ponderação, patch de fronteiras e cores axiais phase. |
| S03-07 | Média/desvio/resultante axial, exemplo unimodal e R=0, console e linha vermelha opcional. |
| S03-08 | EZROSE sem cabeçalho, crescente, duas casas, tag/nome exatos, substituição atômica; apenas um arquivo por Run angular. |
| S03-09 | Casos direcionais, escala, norte/flips, artistas, paletas, imagens do manual e onze PNGs exportados inspecionados; comparação controlada MATLAB pendente. |

**208 testes passaram**, incluindo regressões anteriores e 41 novos casos. Há 104 avisos de depreciação do backend Qt/Matplotlib instalado, ligados a AA_UseHighDpiPixmaps; nenhum erro. A integração Qt seleciona os seis outputs reais, inclui nós, norte, flip, ponderação e média, abre seis janelas e confere seis PNGs 4724×4724/600 dpi mais o TXT. O cálculo não importa Qt/Matplotlib e a renderização permanece na thread principal.

[checks.json](../../tests/reference/sprint3/checks.json) registra o resultado dos testes, checksum do JUnit e verificação de integridade das evidências. O wheel final foi construído sem resolver novas dependências; paletas, estilo e licença foram carregados diretamente do zip fora da raiz do projeto e uma figura foi renderizada nesse contexto.

[validation.json](../../tests/reference/sprint3/validation.json) registra 11 PNGs, quatro EZROSE TXT, arrays, parâmetros, fontes, ambiente e hashes. Casos: base de cinco traços/seis segmentos, rosa ponderada de 5°, rosa colorida ponderada de 20° e norte 10°/dois flips/metres com rosa de 30°. Os testes numéricos complementam 10° e flips simples. Todas as 18 tabelas RGB são iguais aos tokens float64 do fonte. A pasta MATLAB mantém os 164 arquivos intactos por SHA-256. pip check não encontrou conflitos e nenhuma dependência foi adicionada/atualizada.

Exemplos para revisão: [mapa com nós](../../tests/reference/sprint3/qa-FracPaQ2D_tracemap_Run1.png), [comprimento](../../tests/reference/sprint3/qa-FracPaQ2D_segmentlengthmap_Run1.png), [histograma](../../tests/reference/sprint3/qa-FracPaQ2D_histoangle_Run1.png), [rosa colorida ponderada](../../tests/reference/sprint3/qa-FracPaQ2D_roseangleEqArea_strike_colour.png). Arquivos qa são miniaturas do exportador comum, sem nova composição.

Contrato, tabela por figura e limites estão na [ADR 0004](../decisions/0004-maps-and-angles.md). Q-10/Q-17 permanecem abertos para decisão científica; o comportamento do fonte foi preservado e medido em Python. MATLAB/Octave não estão disponíveis: não há novas referências nativas, SSIM homologado ou aprovação final de paridade. Capturas históricas da Sprint 2 não foram sobrescritas; a prévia TXT agora usa azul de referência.

Para reproduzir as evidências:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint3.py
.venv/bin/python scripts/source_manifest.py
```

Uso: selecionar TXT/Preview, escolher Maps/Angles e desmarcar saídas ainda pendentes, incluindo Histogram of lengths marcado por padrão. Run exporta apenas as seleções disponíveis; SVG/imagens, multicolour, comprimentos estatísticos e crack tensor permanecem nas sprints previstas.
