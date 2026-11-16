# Sprint 0 — Referências e contrato de paridade

Execução em 13/11/2026. As oito tarefas de preparação foram concluídas. A aplicação e sua paridade funcional, numérica, visual e de arquivos continuam por implementar e verificar nas próximas sprints.

| Tarefa | Evidência entregue |
| --- | --- |
| S00-01 | matrix.md: 164 IDs únicos, 118 GUI, 6 EXP, 19 AUX e 21 Q; controles/entradas, destinos Python planejados, fixtures, saídas, estados e divergências. controls.md relaciona todos os 142 objetos com Tag do FIG principal. |
| S00-02 | source_manifest.json: versão 2.8/2.8.0, tamanhos e SHA-256 dos 164 arquivos. Verificação estrita do conjunto e conteúdo; original intacto. source_catalog.json indexa os 82 fontes MATLAB. |
| S00-03 | Dois JSONs de FIG com 154/14 objetos, propriedades completas salvas, callbacks, pais, posições normalizadas e sobreposição dos painéis após OpeningFcn; gui-reference.md distingue defaults salvos e efetivos. |
| S00-04 | ADR 0001: máquina Apple M5/16 GiB, SO, Python 3.13.18, alvo 1366×768 lógico/100%, Arial e protocolo de DPI. environment.json registra a tela virtual efetiva, separadamente da tela física ainda indisponível. |
| S00-05 | 103 imagens de apoio do manual, texto de 39 páginas e páginas renderizadas; manifestos de origem. capture_catalog.json e capture-protocol.md registram oito estados de tela, 53 nomes-base GUI e dados/intermediários ainda sem captura controlada MATLAB. Nenhuma paridade declarada. |
| S00-06 | 46 casos analíticos; TXT/SVG/TIFF sintéticos; 10 exemplos reais com checksum, formato e compatibilidade inspecionados; AUX-16 e licença/procedência em fixtures.md. |
| S00-07 | 24 pins de execução e 8 exclusivos de desenvolvimento, incluindo transitivos; wheels e hashes registrados. Instalação editável, importação científica, Qt Widgets/Fusion, Agg/QtAgg e pip check validados neste macOS arm64. |
| S00-08 | acceptance.md define tolerâncias por grandeza e unidade, critérios discretos/visuais/arquivos e metodologia estocástica. divergences.md registra as 21 Q e processo de decisão. LICENSE, THIRD_PARTY_NOTICES e avisos/metadata de dependências preservam créditos iniciais AUX-18. |

## Verificação executada

```text
.venv/bin/python -m pytest -q
27 passed

.venv/bin/python -m pip check
No broken requirements found.

.venv/bin/python scripts/source_manifest.py
SHA-256: 164 arquivos originais intactos.

QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/check_environment.py --output ...
Python 3.13.18, Qt 6.12.0: 8 verificações OK (offscreen).

.venv/bin/python -m pip install -e . --no-deps --no-build-isolation
Successfully installed pyfracpaq-0.0.0
```

Os testes verificam integridade dos fontes, completude da matriz, reextração dos FIG, mapeamento de controles, catálogo de capturas, hashes das imagens/avisos, consistência dos fixtures e desenho QtAgg pelo pytest-qt. A verificação de manifestos também prova que alteração, remoção e acréscimo de arquivos são detectados em cópias temporárias. Os testes não executam análises científicas ainda inexistentes no port.

## Limites e continuidade

MATLAB/Octave não foram encontrados no PATH. PNGs originais, arrays científicos compartilhados e capturas controladas das seis abas precisam ser obtidos pelo protocolo antes de aceitar paridade. S00-05 prevê explicitamente registrar essas indisponibilidades; por isso a preparação está concluída sem afirmar que as capturas pendentes já existem.

Nenhuma Q foi promovida a resolvida; não houve decisão científica nova. Windows/Linux, aparência nativa, desempenho dos algoritmos e instalação final com GUI serão verificados nas sprints correspondentes. O .gitignore já excluía fracpaq-matlab e a raiz não era um repositório Git: não houve commit e a preservação foi verificada por checksum. As demais tarefas do PRD continuam desmarcadas.
