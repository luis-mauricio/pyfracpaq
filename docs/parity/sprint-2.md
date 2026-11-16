# Sprint 2 — Janela principal, estados e exportação base

Execução em 13/11/2026, no ambiente CPython 3.13.18/Qt 6.12.0 congelado. As dez tarefas S02 foram concluídas no escopo de janela, prévia TXT e infraestrutura; os itens já marcados S00/S01 foram preservados. Os cálculos analíticos das abas continuam pendentes e não produzem dados fictícios.

| Tarefa | Evidência |
| --- | --- |
| S02-01 | run_gui.py e pyfracpaq/__main__.py usam app.py; janela singleton, pacote com assets e abertura fora da raiz testadas. |
| S02-02 | Input, sete estatísticas, canvas, rodapé, tag, Run/Exit e identidade nos blocos normalizados do FIG. |
| S02-03 | 142 objetos nomeados do FIG, incluindo 119 controles; seis botões e QStackedWidget, defaults de OpeningFcn e dependências. Registro mantém análises indisponíveis explícitas. |
| S02-04 | Filename, filtros Browse, cancelamento, tipo automático/manual, caixa da extensão e caminhos absolutos/fora da pasta corrente testados. |
| S02-05 | Preview TXT real em worker, contagens/limites/unidades e habilitação progressiva conferidos com mixed.txt. |
| S02-06 | Flips independentes e repetíveis; a geometria original e os arrays permanecem iguais. |
| S02-07 | Contratos congelados, registro declarativo, parâmetros contextuais, worker/sinais, progresso, tratamento de erros e foco. Pipeline exercitado com cálculos reais injetados pelos testes, sem anunciar análises futuras como disponíveis. |
| S02-08 | Invalidação por entrada/tipo/escala/Hough, revisão de carga e verificação de stamp antes de Run; resultado antigo não restaura a prévia. |
| S02-09 | Tag, FigureWindow/toolbar, export_png 600 dpi/20 cm, substituição atômica e fechamento apenas das janelas/tarefas próprias. |
| S02-10 | Referência estática FIG: nomes, textos, seleções, popups, estados e macros. 32 capturas Qt de oito estados em quatro escalas; auditoria sem cortes e acesso por foco. Limites da comparação visual explicitados na ADR 0003. |

## Verificações

**167 testes passaram**, incluindo as 119 verificações anteriores. O relatório final de testes fica em [validation.json](../../tests/reference/sprint2/validation.json). Os testes cobrem a regressão das Sprints 0/1, interface, dois entrypoints, isolamento de recursos, snapshot e thread, invalidação, falha/recuperação, encerramento durante trabalho, janelas independentes e exportação real de uma figura de traços.

O PNG testado tem 4724×4724 pixels e aproximadamente 600 dpi no backend instalado. Falha de escrita preserva o arquivo anterior e o tamanho da figura; arquivos alheios não são removidos. A pasta MATLAB permanece intacta por SHA-256. Dependências não foram atualizadas; pip check não encontrou conflitos. O wheel foi construído com recursos internos e testado fora da raiz.

## Evidências visuais

| Escala | Estado inicial | Prévia e abas | Auditoria |
| --- | --- | --- | --- |
| 100% | [initial.png](../../tests/reference/sprint2/dpi-100/initial.png) | [manifest.json](../../tests/reference/sprint2/dpi-100/manifest.json) | Oito capturas, texto sem cortes, foco e macros conferidos |
| 125% | [initial.png](../../tests/reference/sprint2/dpi-125/initial.png) | [manifest.json](../../tests/reference/sprint2/dpi-125/manifest.json) | Mesmo alvo lógico, DPR 1.25 |
| 150% | [initial.png](../../tests/reference/sprint2/dpi-150/initial.png) | [manifest.json](../../tests/reference/sprint2/dpi-150/manifest.json) | Mesmo alvo lógico, DPR 1.5 |
| 200% | [initial.png](../../tests/reference/sprint2/dpi-200/initial.png) | [manifest.json](../../tests/reference/sprint2/dpi-200/manifest.json) | Mesmo alvo lógico, DPR 2 |

As macros medidas correspondem às posições normalizadas arredondadas do FIG. Os formulários internos refluem para acomodar rótulos e os controles Qt têm métricas próprias; não foi aprovada paridade de dois pixels para cada controle. Capturas são da plataforma offscreen, sem decoração nativa, com dados TXT reais. Não são novas referências MATLAB e não substituem revisão do desktop original, SSIM de figuras ou testes de release em outros sistemas.

O primeiro exame encontrou corte no título Distance FROM the line, corrigido ao distribuir as colunas de Graphs. A revisão também ajustou a interpretação de Position do eixo (área de dados, não canvas inteiro), a proporção dos logos e o foco após erro.

## Uso e continuidade

```bash
.venv/bin/python run_gui.py
.venv/bin/python -m pyfracpaq
```

Selecionar um TXT válido e clicar Preview. As abas preservam as escolhas e os controles subordinados são habilitados conforme a opção. Run captura a configuração e informa as saídas ainda indisponíveis; não salva uma figura de demonstração para substituí-las. SVG, imagem, seleção da linha de Graphs e cálculos/exportações de cada família continuam nas respectivas sprints.

Q-01/04/21 receberam correções da infraestrutura previstas no PRD; Q-02 tem validação técnica parcial, preservando decisões científicas futuras. As mensagens da base refletem PNG em Q-18. Ver [ADR 0003](../decisions/0003-desktop-and-execution.md), [matriz](matrix.md) e [divergências](divergences.md).
