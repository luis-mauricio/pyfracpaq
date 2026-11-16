# Contrato estático da interface

[guiFracPaQ2D.json](../../tests/reference/gui/guiFracPaQ2D.json) contém todos os 154 objetos: 119 uicontrol, 14 grupos de botões, cinco painéis, três eixos, 12 textos internos de eixos e a figura. [guiWaveletDialog.json](../../tests/reference/gui/guiWaveletDialog.json) contém os 14 objetos do diálogo auxiliar. Cada registro preserva propriedades salvas, callbacks serializados, Tag e pai. Nenhum callback é executado na extração.

Os 142 objetos com Tag do FIG principal estão relacionados a IDs em [controls.md](controls.md). Usar essas Tags como objectName Qt. Os 12 textos internos sem Tag recebem identificador apenas para indexação; não são controles novos.

## Coordenadas

Position normalizada é relativa ao **pai**, com origem inferior esquerda MATLAB. Os campos normalized_figure_rect compõem a árvore para facilitar comparação. opening_normalized_figure_rect também aplica a sobreposição dos seis painéis em Maps. Esses retângulos geométricos não incluem insets de borda/título nativos; medi-los em captura antes de exigir precisão de dois pixels.

Para um pai Qt com área interna W×H, [x,y,w,h] vira [xW, (1-y-h)H, wW, hH]; preservar float até o arredondamento de pixels e considerar insets reais do pai. A figura raiz é salva em **characters**: [181,36.6,247.428571...,49.266666...]. Sua origem/tamanho absolutos não podem ser convertidos para pixels sem as métricas/fontes do MATLAB. Textos de eixos usam unidades data e não recebem retângulo GUI inventado.

As proporções verificadas no FIG são: Input com largura 0,16124488, mapa com largura 0,43000939 e Maps com largura 0,36576212. A margem e os grupos internos também constam do JSON. Isso corresponde ao arranjo aproximado 16% / 43% / 37% do PRD.

## Estado salvo e estado efetivo

Não confundir um campo ausente no FIG com valor medido em execução: GUIDE omite propriedades que dependem dos defaults MATLAB. O JSON preserva essa ausência. O PRD RF-02.1 e os callbacks complementam o contrato sem fingir execução dinâmica.

guiFracPaQ2D.m:71–150 aplica estas mudanças antes de mostrar a janela:

| Controle / propriedade | Estado efetivo após OpeningFcn |
| --- | --- |
| popupmenu_histolengthbins.Value | 2 → 20 bins (salvo: 1) |
| popupmenu_histoanglebins.Value | 2 → 20 bins (salvo: 1) |
| popupmenu_rosebins.Value | 2 → 10° (salvo: 1) |
| Cinco painéis diferentes de Maps | Position igual à de Maps |
| Todos os seis painéis | Visible='off' |
| edit_filename.Enable | 'on' |
| axes_logo / axes_icon | imagens JPEG da distribuição |
| Estado interno | versão 2.8; graphx=[0,0], graphy=[0,0] |

O FIG salva Node file, Traces/segments, Segments/by strike, Histogram of lengths, Rose diagram, Colour by strike, Fixed aperture e Morlet selecionados. O contrato de entrada contém Hough 1000/0.33/5/3, escala vazia, círculos 12, tensões 100/50, direção 0°, C0/Pf 0, mu 0.6, abertura/fator 1e-3, expoente 1, λ=1, listas 2 4 8 16, passo 20° e tag Run1. Confirmar essas seleções contra captura real ao implementar os widgets.

Após Preview válido, Run/abas/flips são habilitados, Maps é mostrada e a tolerância I→Y é calculada como max(ΔX,ΔY)/1000, com duas casas. Os callbacks de opções habilitam nós, círculos, bins, MLE/cortes, tensões, abertura, wavelet e Graphs. Reproduzir dependências válidas; Q-01/02/21 exigem validação contextual e invalidação da prévia. A extração estática não certifica essas transições em runtime.

A imagem de apoio do manual na página 5 mostra a janela inicial; página 6 contém prévia. Inclui cortes de rótulos no original e ambiente sem métricas conhecidas. Não é licença para reproduzir cortes no port nem substitui captura controlada de todas as abas.

## Revisão da implementação visual — 14/11/2026

A especificação instalada agora preserva BorderType e FontWeight. Em particular, uibgTabButtons tem BorderType=none; os outros 18 grupos têm beveledin. O código aplica os retângulos relativos dos controles internos, sem QHBoxLayout/QGridLayout alterando larguras, alturas ou a disposição das abas. Insets explícitos separam o título da área útil dos grupos. Rótulos associados a campos são limitados ao espaço anterior ao campo e recebem altura para sua linha completa, em vez de sobrepor/cortar texto.

As capturas documentais mostram área cliente de cerca de 2500×1478 pixels físicos; a calibração usa 1250×739 lógicos como referência de aspecto, sem presumir métricas characters→pixels do MATLAB. O tamanho inicial é limitado à área disponível do monitor e centralizado, sem largura fixa de 1366. [Auditoria visual](ui-calibration.md) registra as correções, dimensões medidas, fontes, limites e capturas atuais.
