# ADR 0009 — Barras de cores alinhadas ao plot durante redimensionamento

Data: 14/11/2026. Decisão solicitada explicitamente pelo usuário para todas as figuras atuais e futuras. Barras horizontais devem ter exatamente a largura da área visível do plot; verticais, exatamente a altura. Isso permanece válido ao aumentar/reduzir a janela e ao exportar.

## Implementação compartilhada obrigatória

Usar `pyfracpaq.plots.colourbars.colourbar(host, location=...)`, também exposta em `pyfracpaq.plots`. O eixo `host` identifica o plot associado à barra. `location` aceita bottom/top (horizontal) e left/right (vertical). Novos renderizadores não devem chamar Colorbar/ColorbarBase/Figure.colorbar/pyplot.colorbar diretamente, nem criar retângulos fixos de barras. A regra está em AGENTS.md, no PRD RF-12 e em um teste de arquitetura que inspeciona os renderizadores.

Exemplo para uma futura figura com barra vertical:

```python
from pyfracpaq.plots import colourbar

bar = colourbar(axes, location='right', cmap=palette, norm=normalization)
bar.set_label('Quantity, units')
```

O locator é chamado pelo Matplotlib em cada desenho, inclusive QtAgg, Agg e savefig. Primeiro aplica o aspecto do eixo principal e consulta seu retângulo efetivo; não usa o slot original que pode conter margens vazias após axis equal/axis square. Bottom/top herdam x0/x1; left/right herdam y0/y1. Também acompanha locators próprios do eixo principal, sem depender da ordem de desenho. A rotina nativa da barra continua responsável pela paleta, escala, ticks e eventuais extensões.

Não há callback de resize, segundo redraw para corrigir a imagem ou ajuste de escala científica. Limites, amostras, normalizações, cores e unidades permanecem iguais. **Correção de espaçamento:** `pad` agora usa pontos físicos, com padrão de 25 pontos, medidos a partir da caixa real dos rótulos/ticks do eixo no lado da barra. A folga não é uma porcentagem da janela e permanece constante inclusive com DPI diferente. O valor preserva aproximadamente a folga inicial da janela de 700×700 (medida anterior: 24,92 pontos). A espessura continua .025 da dimensão perpendicular da figura.

Um layout compartilhado pelos locators do plot e da barra mede o aspecto, os textos e o espaço necessário em cada desenho. Quando a janela fica pequena, reduz somente a área ativa disponível para o plot, preservando o slot original para restauração ao ampliar. Não empurra a barra sobre o label nem para dentro do plot para encaixar seu texto. A mesma regra vale para barras verticais, considerando os rótulos no lado correspondente. O cálculo converge no próprio desenho e não acumula redução entre redimensionamentos. Os extremos horizontais/verticais da barra continuam coincidentes com os do plot. Se uma figura for fisicamente menor que todo o texto somado a um plot mínimo de um ponto, não há espaço para exibir tudo; mesmo nesse limite o layout não sacrifica a folga para sobrepor a barra ao eixo.

## Saídas atuais e futuras

As seis saídas existentes com barra foram migradas:

| ID | Figura |
| --- | --- |
| MAP-04 | Traces, by length |
| MAP-05 | Segments, by length |
| MAP-06 | Segments, by strike |
| ANG-02 / opção Colour by strike | Rosa de área igual colorida |
| MAP-07 | Estimated Intensity, P21 |
| MAP-08 | Estimated Density, P20 |

Comprimentos preservam Q-17 (lookup linear e barra logarítmica); strike/rosa preservam phase e os ticks 0–180°; P21/P20 preservam hot invertida e proteção de mapa zero. Figuras sem barra não receberam uma barra nova. Ainda não há família científica implementada com barra vertical; a fábrica e os testes já garantem esse comportamento para as próximas sprints, sem apresentar a demonstração vertical como análise científica.

As posições fixas das barras documentadas nas ADRs 0004/0008 e nas capturas históricas das Sprints 3–7 foram substituídas por esta regra a pedido do usuário. As evidências históricas não foram sobrescritas.

## Verificação

49 testes da família verificam extremos em pixels após um único draw, quatro lados, aspecto livre/equal/square/polar, mudança de limites, locator dependente do renderer, todas as seis saídas em domínios quadrados/largos/altos, paletas e normalizações, janela Qt real e exportação comum 600 dpi seguida de restauração da janela. A revisão acrescentou oito casos específicos de folga fixa nos quatro lados, incluindo valores configuráveis, comparação direta com a caixa do label, reserva de espaço e restauração. Os testes Qt também maximizam a janela e reduzem até 340×280, em escalas de tela 100% e 200%. A folga é conferida em pontos e os extremos em pixels, com tolerância 1e−8; não é relaxamento de tolerância científica. A suíte completa passa com **433 testes** numa cópia isolada do projeto com os 164 arquivos originais da distribuição.

[Validação atual](../../tests/reference/colourbar-spacing/validation.json) contém 35 capturas de figuras em formatos quadrado/largo/alto/pequeno/grande e sete exportações de 4724×4724 a 600 dpi, com extremos, folgas medidas e hashes. [Checks](../../tests/reference/colourbar-spacing/checks.json) registra os testes e o pacote. Exemplos: [janela pequena](../../tests/reference/colourbar-spacing/FracPaQ2D_intensityP21_small.png), [janela grande](../../tests/reference/colourbar-spacing/FracPaQ2D_segmentstrikemap_large.png) e [barra vertical](../../tests/reference/colourbar-spacing/vertical_layout_small.png). As evidências anteriores em colourbar-layout foram preservadas como histórico.

O workspace recebeu sete saídas adicionais junto aos fontes MATLAB, fora do manifesto congelado. Foram preservadas, sem mover/apagar ou presumir parâmetros de captura. A verificação estrita no workspace acusa esses extras; a validação isolada usa exatamente a distribuição congelada. Separadamente, todos os 164 hashes originais foram conferidos no workspace e continuam iguais. O relatório lista os extras preservados. Essa condição não exige alterar o verificador original nem tratar os novos PNGs como goldens controlados.

Reprodução das figuras e medições: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_colourbars.py`. Referências de execução MATLAB ou comparações SSIM não são necessárias para verificar a igualdade geométrica solicitada; não se declara paridade de toda a aplicação a partir desta mudança.
