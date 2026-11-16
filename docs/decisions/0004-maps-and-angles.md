# ADR 0004 — Tema, mapas básicos e Angles

**Atualização S16:** Capturas nativas de Maps/Angles e Q10 agora existem na S16. Os vetores preservam exatamente o fonte: Q10 fica resolvida por preservação, sem unificação dos TXT. Retângulos básicos/histogramas, títulos e ticks foram calibrados; barra strike tem ticks20°. A aceitação visual integral continua aberta. ADR0018 prevalece sobre os estados históricos abaixo.

Data: 13/11/2026. Escopo: S03-01 a S03-09. Implementação Python conferida com equações/fontes e imagens documentais; execução MATLAB e aceite visual por regiões continuam pendentes. Nenhuma tolerância da Sprint 0 foi relaxada.

## Arquitetura e integração

analysis/compatibility.py, maps.py, angles.py e palettes.py não importam Qt nem Matplotlib. Resultados são dataclasses congeladas e arrays destacados somente para leitura. O Dataset original é preservado. O registro habilita MAP-01/04/05/06 e ANG-01/02; MAP-02 e ANG-03 a ANG-09 são opções/rotinas dessas saídas. Renderizadores usam os resultados na thread principal e o exportador PNG comum da Sprint 2.

ANG-01/02 usam a mesma computação e cache **restrito a uma execução**, sem estado global de dados. Isso calcula/exporta EZROSE uma vez se ambos forem selecionados. Parâmetros dos gráficos não selecionados não são lidos. A validação de todas as seleções precede qualquer arquivo. Mapas isolados não geram EZROSE. FLO-08 continua indisponível: ao implementar crack tensor na Sprint 10, preservar seu gatilho de EZROSE pela mesma família, sem depender de marcar rosa/histograma.

## Tema e composição

resources/fracpaq_matlab.mplstyle fixa fundo branco, linhas/eixos de 0,75 pt, ticks internos nas quatro bordas, corpo de 10 pt, título negrito de 11 pt, marcadores de 6 pt e legendas retangulares de 9 pt. Fonte Arial da instalação; fallback explícito DejaVu Sans. Nenhuma fonte é redistribuída. A seleção só vigora no contexto de desenho e não muda o tema global do usuário. base.qss/Fusion da Sprint 2 foi reaproveitado e documentado como tema desktop congelado; a cor QWidget não governa figuras. A prévia TXT agora usa o azul padrão do OpeningFcn, sem alterar cores/proveniência no Dataset.

Tabela inicial de parâmetros por figura, em coordenadas normalizadas `(left, bottom, width, height)`; aspecto pode reduzir a área efetiva dentro do retângulo. **Revisão de 14/11/2026:** as posições fixas das barras abaixo são históricas; a [ADR 0009](0009-responsive-colourbars.md) determina agora alinhamento dinâmico ao retângulo real do plot, inclusive na rosa e ao redimensionar/exportar. Os slots dos plots, dados e escalas foram preservados.

| Figura | Eixo principal | Barra de cor | Geometria e detalhes |
| --- | --- | --- | --- |
| FracPaQ2D_tracemap | .13, .14, .72, .72 | ausente | equal; domínio sem padding, salvo dimensão degenerada; nós círculo preto 4 pt, centros quadrado/círculo vermelho 6 pt, vazados |
| FracPaQ2D_tracelengthmap | .13, .22, .74, .64 | .22, .085, .56, .025, horizontal | equal; haline 256, barra logarítmica; Q-17 |
| FracPaQ2D_segmentlengthmap | .13, .22, .74, .64 | igual ao anterior | equal; haline 256; Q-17 |
| FracPaQ2D_segmentstrikemap | .13, .22, .74, .64 | igual ao anterior | equal; phase 180; escala 0–180° |
| FracPaQ2D_histoangle | .15, .16, .70, .70 | ausente | square; eixo direito acoplado; x −10 a 370°, ticks de 60°, grid; barras azuis com borda preta |
| FracPaQ2D_roseangleEqArea | .12, .12, .76, .76 | ausente | equal/off; polígono azul, contornos finos, linha média vermelha 1 pt |
| mesma rosa, Colour by strike | .12, .23, .76, .64 | .22, .085, .56, .025 | triângulo por bin, phase `180/delta + 1`, duas metades axiais iguais |

Títulos têm segunda linha vazia como no fonte. Unidades são pixels ou metres, determinadas pelo Dataset. Flips dos mapas invertem eixos, sem transformar os arrays. Sem tight_layout, bbox tight ou layout automático. Exportação: 20×20 cm/600 dpi, nome legado com `_tag`, 4724×4724 observado neste backend. Zoom/toolbar pertencem à janela, não ao PNG.

Paletas: 18 tabelas completas do cmocean.m fornecido, incluindo as que possuem mais de 256 linhas. freeze_cmocean.py preserva os tokens como float64, manifesto com hash de cada tabela/fonte. cmocean(name, levels, reverse=...) interpola linearmente cada canal nas mesmas coordenadas do MATLAB. Testes comparam todos os tokens, extremos e ponto intermediário, sem presumir equivalência com bibliotecas externas. Licenças/atribuições em resources/cmocean_LICENSE.txt e THIRD_PARTY_NOTICES.md. Pivô, aplicação automática ao eixo e prévia da biblioteca AUX-08 ficam na Sprint 15; jet/hot/bone serão congeladas quando suas famílias forem implementadas.

## Semântica numérica preservada

**Q-10:** subtrair norte, arredondar empates para longe de zero, concatenar `[a, a+180]`, somar 360 **uma vez** aos negativos. Cada flip aplica `180-a` e soma 360 uma vez aos negativos. Sem normalização modular completa. Norte −360°, por exemplo, com direção 30°, produz `[390, 570]`: o hist absorve as caudas e a rosa as exclui; há aviso no console. O mapa de strike aplica a sequência própria do fonte e usa 180° para o índice menor que 1; 0° e 180° compartilham a última cor. Empates de −0,5°/179,5° podem produzir cores adjacentes: preservado e testado. TXT de Lengths/segmentdata continuarão com suas convenções nas respectivas sprints. Unificar convenções é decisão científica pendente, não realizada por este port.

**Q-17:** índice por comprimento é `max(1, round(L/max(L)*256))-1`. A barra usa limites `max/1000` a `max`, log, com ticks `max/[1000,12,3,1]` rotulados com round MATLAB inteiro. Portanto a cor da linha e a barra não representam a mesma transformação. Preservado explicitamente; não substituir as cores por LogNorm. Decisões sobre estabilidade/tensões continuam na Sprint 11.

Histograma: `nHistoBins + 1` centros de 0 a 360, não n intervalos. Cortes ficam nos pontos médios; empate pertence ao bin inferior, e primeiro/último recebem as caudas. Fonte primária: [hist](https://www.mathworks.com/help/matlab/ref/hist.html) e [migração de hist/histc](https://www.mathworks.com/help/matlab/creating_plots/replace-discouraged-instances-of-hist-and-histc.html). Os dois eixos mostram a mesma contagem; limite direito = limite esquerdo / amostra duplicada ×100. Eixos esquerdo azul MATLAB e direito laranja; o manual também contém um hist antigo só percentual, que não substitui o contrato yyaxis do fonte atual.

Rosa: bins histcounts incluem a borda esquerda e excluem a direita, exceto 360° incluído no último. A média dos bins vizinhos a 0/180/360 altera **somente contagens**, não somas de comprimento. Ponderação usa comprimentos duplicados; cálculo percentual reescala todos os comprimentos pelo mesmo máximo para evitar overflow da soma, mantendo a equação. Raio = `50*sqrt(percentual)`. Os dois zeros finais alocados no fonte são preservados no vetor/polígono. A versão colorida desenha um triângulo por intervalo; o triângulo extra degenerado e repetições de fill sem efeito visual foram omitidos. Contornos são círculos vetoriais de 1/5/10/20/30/50%, em vez de milhões de amostras cartesianas; posições, raios e espessuras são preservados, rasterização ainda sujeita à comparação MATLAB.

Média axial usa apenas a primeira metade, dobrando os ângulos dentro de seno/cosseno. `R=hypot(sum(cos(2a)),sum(sin(2a)))/n`, média `atan2(W,V)/2` em [0,180), desvio **`sqrt(2*(1-R))*180/pi`**, sem fórmula logarítmica e sem pesos de comprimento. Trigonometria em graus zera múltiplos cardinais exatamente. Quando R=0, o valor legado de média 0 é mantido e sinalizado como indefinido; não é uma orientação preferencial. A linha é opcional e as três estatísticas vão para o console somente quando Show mean vector estiver marcado.

Proteções técnicas: limite da rosa usa o primeiro contorno estritamente maior que a extensão. Se o pico cardinal coincide com o último contorno (fonte retorna limite vazio), conserva o contorno externo/extensão. R é limitado superiormente a 1 contra erro de soma de vetores unitários. Domínio linear com extensão zero recebe padding só de desenho, como na prévia. Essas proteções não mudam bins, ângulos, unidades ou fórmulas; ficam registradas no escopo técnico Q-02.

EZROSE: `FracPaQ2DEZROSE_{tag}.txt`, inclusive `_` para tag vazia, sem cabeçalho; vetor corrigido/duplicado/invertido ordenado crescente, `%6.2f\n`. Escrita temporária no destino + replace; falha preserva o arquivo anterior e limpa apenas o temporário próprio. Não há conversão para ângulo bruto ou corte modular no arquivo.

## Evidência e limites

Referências estáticas inspecionadas: manual p. 4 (strike/comprimento), p. 11 (mapa, marcadores, comprimentos), p. 23 (histograma/rosas), além dos fontes citados na matriz. Essas imagens não trazem todos os parâmetros/ambiente e não são goldens controlados. A inspeção corrigiu a posição das barras de comprimento para southoutside. As onze exportações Python, parâmetros, arrays e hashes estão em tests/reference/sprint3; miniaturas QA derivam dos pixels exportados. Não foi calculado SSIM contra entradas diferentes nem foi declarada paridade visual de dois pixels.

O fluxo padrão continua incluindo Histogram of lengths (Sprint 4). Para executar somente o que já está disponível, desmarcar essa saída e quaisquer outras pendentes; defaults do FIG foram mantidos. Não foram implementadas saídas futuras para contornar a validação. Run/Preview TXT reais e arquivos das seis saídas foram verificados pelo teste Qt.
