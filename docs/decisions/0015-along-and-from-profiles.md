# 0015 — Perfis dirigidos ALONG/FROM

Data: 14/11/2026. Todos os perfis ALONG/FROM, mapa e círculos integrados ao Run padrão. **A extensão de normalização P20 de Q-20 foi aprovada explicitamente pelo usuário:** “Aprovo ambos Q-14 e Extensão Q-20.” As duas seleções circulares estão ativas.

O contrato vem de guiFracPaQ2Dgraphs.m, callback Select end points e getMapLimits, confrontados com os modelos e padrões da aplicação. A [captura nativa](../../scripts/capture_native_s1213.m) registra nove PNGs e arrays de eixos, além de três PNGs da chamada apenas density. A falha de interseção ausente/linha nula foi executada e consta de native_calls.json; a verificação por soma de coordenadas no callback foi inspecionada estaticamente. [Procedência](../../tests/reference/sprint13/native_provenance.json) distingue esses casos.

## Seleção e estado

Select end points usa dois cliques no canvas da prévia em cache. Guarda ProfileLine imutável com coordenadas finitas e comprimento positivo, desenha linha/quadrados vermelhos, pede outro segundo ponto quando coincide com o primeiro e aceita soma de coordenadas zero. Escape ou botão direito cancelam a tentativa preservando a última seleção completa. Run é desabilitado enquanto a seleção está incompleta. Clique fora dos eixos/sem coordenada é ignorado.

Arquivo, modo, escala, parâmetros Hough ou nova prévia limpam a seleção; flips e norte a preservam. As coordenadas pertencem ao domínio da prévia e já têm sua escala, inclusive para imagem. A configuração congelada do Run leva a seleção; o worker não consulta widgets e Graphs não relê TXT/SVG/imagem. Seleção ausente identifica o botão antes de criar arquivos. Não existe nova aba nem seletor científico.

## Valores

ALONG intersecta a linha **finita** com cada segmento, mantendo a ordem de entrada e um registro por segmento intersectado. Suportes coincidentes são excluídos, inclusive contato collinear nas pontas. Um vértice comum não collinear pode gerar duas observações; várias interseções do mesmo traço repetem seu comprimento. Não se ordena nem se deduplica o resultado. A abscissa é distância da interseção ao ponto 1, e a ordenada é comprimento total do traço, comprimento do segmento ou ângulo bruto. Ausência de interseções produz vetores vazios e três figuras explicativas; não bloqueia FROM/círculos.

FROM usa a reta suporte **infinita**, com distância assinada (dy×(px−x1)−dx×(py−y1))/L. Para linha horizontal da esquerda à direita, pontos acima têm distância negativa. Comprimentos de traços usam seu centro no meio do percurso; segmentos e ângulos usam centros geométricos dos segmentos, também preenchidos no modelo Hough. Inverter a linha troca o sinal de FROM e a origem de ALONG; os IDs continuam na ordem original. Norte e flips não transformam os valores brutos desses perfis. Flips afetam somente o mapa auxiliar.

## Círculos e decisão P20 aprovada

N≥2 círculos têm r=L/(2N), centros nas frações (k+.5)/N e abscissas linspace(r,L−r,N). Qualquer uma das seleções P21/P20 produz **mapa e ambos os perfis**, uma única vez por Run. O mapa usa traços na cor primária, linha magenta, ponto 1 ciano/ponto 2 verde em quadrados preenchidos e círculos vermelhos .5 ponto. Limites do envelope dos nós, aspecto igual e legenda Point 1/Point 2 abaixo.

O predicado circle_counts compartilhado de Maps implementa a contagem finita previamente aprovada em Q-20: n conta interseções de cada segmento com a circunferência (tangente uma vez), m conta extremos estritamente internos por segmento. Não há aproximação pelo suporte infinito nem deduplicação topológica de vértices.

P21=n/(4r). **A extensão aprovada é P20**: Graphs nativo usa m/(2πr), mas rotula área⁻¹; Maps usa m/(2πr²). Para a linha (-6,0)→(6,0), N=3, r=2 e m=[0,2,0], o MATLAB retorna [0,.1591549431,0]. O Run aprovado usa [0,.0795774715,0], com normalização por r², mantendo a contagem autorizada. [Comparação concreta](../../tests/reference/sprint13/candidate/q20_density_comparison.json). A aprovação anterior “Corrigir a contagem geométrica” foi complementada pela autorização explícita da extensão de normalização em 14/11/2026. GRA-06/07 estão disponíveis no registro padrão; a contagem finita continua compartilhada com Maps.

## Figuras, integração e limites

Os nove nomes são exatamente guiFracPaQ2D_tracelengthalonggraph, guiFracPaQ2D_segmentlengthalonggraph, guiFracPaQ2D_segmentanglealonggraph, guiFracPaQ2D_graphtracemap, guiFracPaQ2D_intensityalonggraph, guiFracPaQ2D_densityalonggraph, guiFracPaQ2D_tracelengthfromgraph, guiFracPaQ2D_segmentlengthfromgraph e guiFracPaQ2D_segmentanglefromgraph. Recebem _{tag}.png pelo exportador existente, 20×20 cm/600 dpi. Graphs não grava TXT.

Dispersão azul preenchida, tamanho 6, grid/box, eixos nativos (.13,.11,.775,.815), ângulos [0,180], ALONG começando em zero até a última distância observada. FROM tem limites externos de ticks. Os seis perfis conferem valores, títulos, unidades e limites com a captura. Ausência de dados ou valores todos zero recebem limites gráficos representáveis sem inventar medidas. Unidades circulares acompanham metres/pixels, corrigindo apenas os textos que o fonte fixa como pixel. Não se afirma identidade de pixels/fontes entre motores.

Um único compute_graphs/cache por Run reúne as famílias escolhidas, sem arquivos no núcleo, com progresso, cancelamento e orçamento de memória. Os renderizadores executam na thread gráfica e usam o tema comum. Nenhuma das novas figuras tem barra de cores; não foi alterado o contrato global de barras responsivas.
