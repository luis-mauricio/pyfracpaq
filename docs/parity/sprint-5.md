# Sprint 5 — SVG e múltiplos conjuntos por cor

Concluída em 14/11/2026: oito tarefas S05 implementadas, sem refazer as tarefas já marcadas das Sprints 0–4. [ADR 0006](../decisions/0006-svg-and-colours.md) define o subconjunto, cores, precisão, efeitos e limitações.

| Tarefa | Evidência |
| --- | --- |
| S05-01/02 | XML estruturado; line/polyline/path M/L absoluto; rejeição integral de curvas, transformações, polygon e demais geometrias fora do subconjunto. |
| S05-03 | Stroke por atributo/style inline/grupo, #RGB/#RRGGBB normalizado e conversão RGB; erros explícitos para CSS/sintaxes sem suporte. |
| S05-04 | TXT junto ao SVG, nome de uma/várias cores, oito casas, TAB/CRLF e quantização usada no Dataset. |
| S05-05 | Preview agregado com cores; MAP-03 adicional automático uma vez por família de mapas, com limites/unidades/flips corretos. |
| S05-06 | TXT colourHHHHHH recarregado individualmente; cor propagada para mapas e gráficos compatíveis. |
| S05-07 | Staging, caminhos/extensões maiúsculas e revisão/stamp; sem glob para importar/apagar; sentinelas alheias preservadas. |
| S05-08 | Fixtures simples/multicor e auditoria dos 14 SVG originais; cópia explicitamente preparada de map1_edit e documentação de TXT em vírgulas/degenerados. |

Validação conjunta das Sprints 5/6: **319 testes passaram**, 67 casos novos, com regressões anteriores preservadas. Há 494 avisos de depreciação do backend Qt/Matplotlib instalado (AA_UseHighDpiPixmaps), sem falhas. Nenhuma dependência nova/atualização; os 164 arquivos originais continuam intactos.

[checks.json](../../tests/reference/sprint5/checks.json) registra o JUnit, o wheel e a auditoria de integridade dos artefatos. O pacote foi importado diretamente do zip fora da raiz, convertendo SVG e carregando os novos recursos de imagem/Hough.

[validation.json](../../tests/reference/sprint5/validation.json) registra 18 PNGs, três TXT convertidos, oito TXT analíticos, parâmetros, arrays/cores e hashes. Casos simples e multicor têm dois traços/três segmentos/cinco nós. A cópia de map1_edit retém 2120 traços/4356 segmentos após remover explicitamente três traços degenerados, com origem/checksums registrados; o leitor do produto não descarta esses registros em silêncio.

Revisão visual: [mapa por cor](../../tests/reference/sprint5/qa-FracPaQ2D_tracemap_multicolour_SVG.png), [rosa do conjunto vermelho](../../tests/reference/sprint5/qa-FracPaQ2D_roseangleEqArea_red.png). A inspeção corrigiu o encobrimento de linhas de borda pela moldura. Testes Qt exercitam Preview, três janelas de mapa, recarga de cor individual e descarte de conversão obsoleta antes de publicar arquivos.

Q-04/Q-09 têm correções de integridade/subconjunto implementadas; Q-19 mantém os utilitários/legado restantes na Sprint 15. Comparação com execução MATLAB, arrays nativos e aceite visual por regiões permanecem pendentes; estas evidências não são novos goldens MATLAB.

Reprodução: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint56.py` e `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`.
