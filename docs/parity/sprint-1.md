# Sprint 1 — Núcleo geométrico e entrada TXT

Execução em 13/11/2026, CPython 3.13.18 no ambiente congelado da Sprint 0. As oito tarefas S01 foram concluídas; os itens S00 marcados permanecem preservados. A entrega é uma API científica local sem dependência de widgets. As análises das abas e a comparação executada com MATLAB continuam nas próximas sprints.

| Tarefa | Implementação / evidência |
| --- | --- |
| S01-01 | [models.py](../../pyfracpaq/domain/models.py): Node, Segment, Trace e Dataset imutáveis, identidade, vínculo entre objetos, origem, escala, cores e arrays. [construction.py](../../pyfracpaq/domain/construction.py) fornece o mesmo contrato aos três modos; testes constroem origens TXT/SVG/imagem, sem antecipar os dois leitores futuros. |
| S01-02 | [nodes.py](../../pyfracpaq/io/nodes.py): TXT tabulado, pares variáveis, UTF-8/BOM/CRLF, números finitos, rejeição atômica e erros estruturados por linha/coluna; nenhum I/O de escrita. AUX-03 coberto no subconjunto necessário à GUI. |
| S01-03 | Normalização de duplicatas consecutivas com registro de cada remoção e IDs do par original. Traços fechados e nós coincidentes de traços diferentes são preservados. Traços degenerados são rejeitados com contexto; Q-07 atualizada. |
| S01-04 | Comprimentos de segmentos, cumulativas, total percorrido e euclidiana correta, ângulo bruto MATLAB e centros por metade do caminho. Oráculo polilinha: comprimentos 3/4, total 7, euclidiana 5, centro (4,2.5). |
| S01-05 | [Bounds](../../pyfracpaq/geometry/primitives.py): mínimos/máximos reais, amplitudes, área e diagonal. Caso negativo: limites (-9,-8,-6,-4), área 12 e diagonal 5. Translação preserva essas grandezas; Q-08 atualizada no escopo do núcleo. |
| S01-06 | Escala positiva divide a geometria a partir de source_traces originais; with_scale é idempotente para a mesma escala e permite restaurar pixels. Unidades de comprimento, área, P21/P20 e permeabilidade derivadas. Falhas de representação numérica são explícitas. |
| S01-07 | [Interseções](../../pyfracpaq/geometry/intersections.py): pontos, endpoints, paralelas, coincidência de suporte, overlap e degenerados, com parâmetros e ordem estável. Distâncias ponto–ponto e ponto–segmento, normas/diagonal e proteção de memória. Sem classificação topológica nem snap implícito. |
| S01-08 | [test_nodes.py](../../tests/numerical/test_nodes.py) e [test_geometry.py](../../tests/numerical/test_geometry.py); [evidência numérica](../../tests/reference/sprint1/numerical.json) reproduzível por scripts/validate_sprint1.py. Matriz e registro de implementação atualizados sem declarar paridade não demonstrada. |

## Validação

```text
.venv/bin/python -m pytest -q
119 passed

.venv/bin/python scripts/validate_sprint1.py
8 casos analíticos, 5 exemplos reais e 3 relações geométricas: OK.

.venv/bin/python -m pip check
No broken requirements found.

.venv/bin/python scripts/source_manifest.py
SHA-256: 164 arquivos originais intactos.
```

São 92 verificações novas somadas às 27 da Sprint 0. Os oito oráculos geométricos coincidem com os valores registrados, com erros absolutos medidos iguais a zero nesses casos. A evidência registra input/checksum, parâmetros, medidas, erros, versões e checksum de todos os módulos Python. Não é um novo conjunto de goldens MATLAB.

Os testes também verificam quatro quadrantes e reversões, domínio negativo/transladado/linear, escala repetida e restauração, dados inválidos, arquivos externos e com acentos, IDs e alinhamento de arrays, imutabilidade, ausência de imports Qt/Matplotlib e respostas a underflow/overflow. Geometria auxiliar inclui determinante com cancelamento, linhas quase paralelas, sobreposição, segmentos pontuais, projeção limitada e normas/distâncias com controle de memória.

## Exemplos reais

| Entrada | Validação geométrica |
| --- | --- |
| IYXtest1_converted.txt | Aceito: 13 traços, 14 segmentos, 27 nós |
| IYXtest2_converted.txt | Aceito: 13 traços, 14 segmentos, 27 nós |
| Souter_Blue.txt | Aceito: 2561 traços, 4075 segmentos, 6636 nós |
| map1_edit_converted.txt | Original rejeitado nas linhas 1589/1595/1604. Cópia temporária explicitamente preparada: 2120 traços, 4356 segmentos, 6476 nós; 11 duplicatas consecutivas removidas com diagnóstico |
| map7_edit_converted.txt | Original rejeitado nas linhas 2496/3242. Cópia temporária explicitamente preparada: 4090 traços, 10134 segmentos, 14224 nós; 15 duplicatas consecutivas removidas com diagnóstico |

A verificação da Sprint 0 era estrutural: pares numéricos válidos não garantiam traços não degenerados. examples.json e fixtures.md agora registram essa distinção. O leitor de produção não descarta linhas inválidas silenciosamente. Os originais permanecem byte a byte intactos.

## Decisões e limites

A [ADR 0002](../decisions/0002-geometry-and-txt.md) documenta IDs/base de índices, escala, validação e grandezas. Q-07 recebeu correção de integridade prevista no PRD; Q-08 foi corrigida no núcleo, mas a utilização em Lengths pertence à Sprint 4. Nenhuma questão científica aberta foi promovida a resolvida ou aprovada por inferência.

A API de interseções expõe relações geométricas, sem transformar overlap automaticamente em classe I/Y/X. Predicados racionais sobre float64 evitam cancelamento; isso não certifica identidade com matrizes MATLAB em casos degenerados. A regra original de distância ponto–segmento, comprimento² < eps(float64), foi preservada e documentada; não foi aplicada à remoção de nós.

As APIs genéricas readtext, geometria além do subconjunto 2D e conversão hex/RGB continuam com destinação AUX/Sprint 15 ou Sprint 5. Importação SVG/imagem, GUI, algoritmos analíticos, ajustes, figuras e exportadores não foram antecipados. MATLAB continua indisponível; paridade numérica executada, visual e de arquivos permanece explicitamente pendente.
