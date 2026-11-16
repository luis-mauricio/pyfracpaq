# ADR 0011 — Conectividade I/Y/X e proximidade de pontas (Q-11)

14/11/2026. Estado: **Q-11 aprovada e conectividade ativada no Run padrão**. Após a reprodução e a revisão da proposta, o usuário declarou: **“Aprovo as Q-15 e a Q-11.”** A aprovação autoriza a regra limitada de proximidade, pontas reais e classificação com tolerância zero descrita abaixo. FLO-01 está associado a compute_connectivity/render_connectivity no registro padrão. O registro temporário de revisão foi removido; não há seletor de modo científico.

## Referência nativa e candidato

O MATLAB R2024b Update 9 executou getConnectivity.m original com domínio [-3,3]×[-3,3], três blocos no lado menor e sete redes descritas em `scripts/capture_native_s89.m`. O processo batch foi separado da sessão interativa e não alterou os fontes. [Resultado nativo](../../tests/reference/sprint9/native/native_topology.json) e [comparação proposta](../../tests/reference/sprint9/candidate/q11_comparison.json):

| Rede | MATLAB original (I/Y/X) | Candidato |
| --- | --- | --- |
| Isolada | Falha: XU indefinido | 2/0/0 |
| T exato, tolerância 0 | 3/0/1 | 3/1/0 |
| T exato, tolerância .2 | 3/1/0 | 3/1/0 |
| Cruzamento | 4/0/1 | 4/0/1 |
| Undershoot .1, tolerância .2 | Falha: xint indefinido | 3/1/0 |
| Overshoot .1, tolerância .2 | 3/1/0 | 3/1/0 |
| Cruzamento em vértice interno de polilinha | 4/1/0 | 4/0/1 |

Os casos sem interseção podem falhar antes das figuras no original. O candidato trata esses casos, pontas exatas com tolerância zero e vértices internos com listas completas. Criar Y para undershoot e mudar kink-cross/tee-zero altera contagens científicas; a mudança foi aprovada explicitamente pelo usuário em 14/11/2026, independentemente da autorização circular Q-20 anterior.

## Regra aprovada, limitada e rastreável

Interseções finitas são calculadas entre segmentos de traços diferentes, por predicados exatos já existentes. Auto-interseções não são junções entre traços. Sobreposições colineares de comprimento positivo são registradas/ignoradas, sem converter um intervalo em ponto fictício. Contato pontual finito é preservado. Duplicação exata de coordenadas é removida mantendo todos os IDs incidentes de traços/segmentos.

Uma interseção que envolve ponta real de traço dentro da tolerância euclidiana é Y; cruzamento entre interiores é X. O vértice interno de uma polilinha não é ponta de traço. Quando pares diferentes chegam à mesma coordenada, um cruzamento entre interiores tem prioridade X, sem duplicação em Y. Esta segue uma classificação de eventos por pontas/interiores, não reconstrói um grafo geral por valência; encontros ponta-ponta são eventos Y segundo esse critério. Traços fechados não oferecem pontas I.

Para uma ponta ainda não conectada, procura-se o segmento finito mais próximo de outro traço dentro da tolerância, incluindo igualdade. Um undershoot sem interseção cria Y inferido na projeção sobre o segmento; sua posição original e IDs são guardados em Snap. Um overshoot próximo usa a interseção existente. Não se cria uma segunda junção por proximidade se o segmento terminal já cruza esse alvo em ponto distante. Empates usam distância, coordenadas da projeção e IDs. Não há aglomeração geral de pontos próximos, deslocamento do Dataset ou ligação entre partes do mesmo traço.

O uso de projeção finita desativa apenas nesta análise o cutoff absoluto de eps de distancePointEdge. O comportamento padrão da primitiva da Sprint 1 permanece igual. Assim a tolerância topológica usa a unidade física corrente e a classificação é preservada quando geometria e tolerância são reescaladas juntas.

I vem das duas pontas verdadeiras de cada traço aberto: remover conectadas, excluir exatamente as quatro bordas do domínio e deduplicar coordenadas. X/Y na borda não são censurados como I. Listas preservam vínculos; a limpeza não remove pontas próximas a interseções alheias sem participação. Os casos degenerados/ambíguos são documentados em vez de presumir que isso é um solucionador de fluxo ou uma topologia GIS completa.

## Grades, arquivos e interface

Busca de interseções por varredura de bounding boxes; não cria matriz N×N. Proximidade usa árvores de midpoints separadas por comprimento, com raio conservador e projeção finita para a decisão final. A análise tem progresso, interrupção cooperativa e orçamento de trabalho de 256 MiB. Classes são coordenadas float64 somente para leitura; contagens int64, IDs em tuplas. Flips afetam somente o desenho.

Heatmaps seguem hist3 com NBins, contagens no lado menor e round MATLAB no maior pela razão de aspecto do domínio. Para cada classe não vazia, centros/limites vêm da própria extensão dos nós, como no original; a matriz (ny,nx) corresponde à transposição usada em imagesc. Um intervalo constante expande pelos bins em passos unitários, conforme hist3; os casos compartilhados foram conferidos no MATLAB. Classes vazias usam grade zero no domínio, sem inventar nós ou centros sem referência espacial. [Documentação de hist3](https://www.mathworks.com/help/stats/hist3.html). Ambas as imagens usam o mesmo máximo e hot invertida; zero total mantém array zero, norma de exibição [0,1] e único tick zero.

Quatro figuras sempre completas: mapa com traços pretos .5, I azul/Y verde/X vermelho de tamanho 3 e legenda por classe existente; heatmaps X+Y e I; ternário. Barras dos heatmaps usam a fábrica compartilhada: extremos coincidem com o plot e folga fixa de 25 pontos até os rótulos, inclusive ao redimensionar/exportar. Domínio linear sem área não permite a divisão de grades e gera erro contextual antes da exportação da família.

TXT `FracPaQ2Dconnectivity_{tag}.txt`, três linhas sem cabeçalho em ordem **I, X, Y**, formato `%s %i\n`, inclusive underscore com tag vazia. Escrita temporária própria e substituição atômica individual; arquivos alheios preservados. Console inclui tolerância, contagens antes/depois da limpeza, proporções Y:X:I e total, pares/overlaps/snaps. Total zero informa proporções indefinidas, sem NaN.

## Ternário e validação

Vértices Y inferior esquerdo, X inferior direito e I superior; linhas vermelhas pontilhadas a 10%, contorno preto, marcador na cor do conjunto e linhas CL=2/3.57 com os pares percentuais do fonte. A projeção usa sqrt(3) exato em vez de 173.2 aproximado de tripts, correção gráfica que não altera contagens ou percentuais. Total zero mostra mensagem, sem criar ponto fictício.

As rotinas triplot/tripts continuam atribuídas a Gerry Middleton (1995), modificadas por Dave Healy (2017), sob a licença FracPaQ preservada. A geometria foi implementada em Python pelos contratos/equações.

Testes cobrem redes isoladas, T/X, undershoot/overshoot, tolerância exata e nextafter, kinks, duplicatas, auto-interseções, traços fechados, bordas, classes ausentes, total zero, escala/translação, cancelamento, grade nativa e arquivo. O Run padrão com SVG/Hough gera quatro figuras/um TXT por execução; TXT/SVG/Hough/zero têm [16 PNGs e arrays](../../tests/reference/sprint9/candidate/validation.json). A aprovação encerra a decisão Q-11 e S09-02; a ativação foi validada por testes de Run com MainWindow e o registro padrão. A homologação visual nativa integral continua pendente.
