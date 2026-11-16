# Figuras e barras de cores

- Toda barra de cores de uma figura, atual ou futura, deve ser criada por `pyfracpaq.plots.colourbars.colourbar`, informando o eixo do plot e `location='bottom'`, `'top'`, `'left'` ou `'right'`.
- Barras horizontais devem coincidir com as duas extremidades horizontais da área real do plot; barras verticais devem coincidir com as duas extremidades verticais. Manter isso ao ampliar, reduzir e exportar a figura, considerando o aspecto dos eixos.
- A distância da barra aos rótulos do eixo deve ser constante em pontos, nunca uma fração da figura (`pad` usa pontos; padrão 25). Em janelas pequenas, reservar espaço reduzindo somente a área ativa do plot; não empurrar a barra sobre os rótulos ou para dentro do plot. Restaurar automaticamente a área disponível ao ampliar novamente.
- Não criar barras com retângulos fixos, `Figure.colorbar`, `pyplot.colorbar`, `Colorbar` ou `ColorbarBase` diretamente nos renderizadores. A construção Matplotlib fica centralizada no helper compartilhado.
- Ao implementar novas figuras, validar o alinhamento em formatos quadrado, largo e alto, incluindo exportação. A regra de geometria não autoriza mudar paletas, normalizações ou dados científicos.
