# ADR 0002 — Núcleo geométrico e TXT

Estado: implementado na Sprint 1, em 13/11/2026. Correções de integridade já previstas em S01-03/04/05 e Q-07/08; nenhuma mudança de metodologia angular, censura, topologia ou amostragem foi aprovada nesta sprint.

## Modelo e identidade

Node, Segment, Trace, TraceInput e Dataset são dataclasses imutáveis. A construção é compartilhada por todos os modos, via `build_dataset(records, input_mode=...)`; somente o leitor TXT está implementado. SVG e imagem deverão produzir TraceInput completos e passar pelo mesmo construtor.

IDs de traços são índices base zero na ordem das linhas não vazias válidas. Node.id é `(trace_id, índice original do par XY)`: a remoção de duplicatas deixa lacunas intencionais, preservando a procedência. Segment.id é `(trace_id, índice do segmento normalizado)` e referencia os próprios objetos Node inicial/final. `source_line` é a linha física base um; coluna de erro também é base um e conta campos separados por TAB. Nós de traços diferentes nunca são fundidos, mesmo quando suas coordenadas são iguais.

Remover apenas duplicatas consecutivas **exatamente iguais**, antes da escala. Registrar cada remoção em Dataset.diagnostics com trace_id, linha, índice original e nó mantido. Não eliminar segmentos pequenos por tolerância nem remover a repetição final de um traço fechado. Rejeitar traço sem segmento não nulo e arquivo inteiro inválido, em vez de importar parcialmente.

Source_traces mantém os dados originais imutáveis, incluindo duplicatas e cores. `with_scale` reconstrói a geometria a partir deles; chamar a mesma escala novamente não divide coordenadas duas vezes. Valores finitos positivos são admitidos; None representa o campo de escala vazio. Zero, negativos, NaN, infinitos, bool e texto são inválidos na API; a futura GUI converterá seu campo vazio para None.

## Grandezas

Comprimento de segmento é a distância euclidiana; distâncias start/end são acumuladas na ordem do traço. Total é a soma percorrida; euclidean_length usa os dois endpoints corretos. O centro do traço fica a metade da distância percorrida, por interpolação no segmento correspondente, inclusive no encontro exato entre segmentos. Não é média dos vértices.

Ângulo bruto preserva `atan(dx/dy)` em graus, acrescentando 180° quando negativo; horizontais são 90° e verticais, inclusive invertidas, são 0°. Não usar normalização modular nova que transforme uma vertical invertida em 180°. Norte, flips, duplicação e round MATLAB não entram nesta sprint; pertencem à Sprint 3/Q-10.

Limites são mínimos/máximos reais de todos os nós. Área é ΔX×ΔY e diagonal é hypot(ΔX,ΔY), invariantes a translação. Domínios lineares têm área zero e continuam importáveis; futuras análises que dividem por área precisam validá-la. Overflow e underflow que colapsam coordenadas/áreas são erros explícitos.

Escala positiva divide posições, centros e comprimentos; área e unidade de permeabilidade são quadráticas, P21 é inversa e P20 inversa quadrática. O núcleo fornece os rótulos de unidade, sem antecipar cálculos de permeabilidade/P21/P20. Todas as posições permanecem no sistema de origem, sem translação automática.

`as_arrays()` entrega cópias float64 e IDs int64, somente para leitura, na mesma ordem dos objetos. Segmentos, comprimentos, ângulos, centros, cumulativas, IDs e cores não usam ordenações independentes. Mesmo que o consumidor torne uma cópia gravável, o Dataset não muda. Nenhum módulo do núcleo importa Qt/Matplotlib.

## TXT

UTF-8 com BOM opcional, terminações de linha usuais, número de pares variável. Cada linha não vazia tem pelo menos dois pares X/Y completos separados por TAB. Espaços em torno de números são permitidos; TABs vazios finais do conversor original também. Campos vazios internos ou iniciais, vírgulas, comentários, expressões, underscores, valores não finitos e pares incompletos são rejeitados. Não executar conteúdo nem selecionar outro delimitador automaticamente.

NodeFileError carrega caminho e uma tupla de InputIssue. O parser coleta o primeiro defeito de cada linha inválida e informa todas essas linhas; não retorna Dataset parcial. Erros de I/O/encoding também têm contexto. Erro de encoding não inventa linha física, porque o buffer de texto pode falhar antes de uma linha ser identificada. Falhas na geometria derivada incluem linha quando atribuíveis a um traço. Não há gravação ou limpeza de arquivos na importação.

## Geometria auxiliar

Interseção retorna none, point ou overlap, com parâmetros nos dois segmentos, flags parallel/coincident e endpoints inclusivos. Retas de suporte coincidentes podem ter segmentos disjuntos; overlap não vira automaticamente um nó I/Y/X. Casos degenerados pontuais são tratados explicitamente. Predicados usam Fraction sobre as coordenadas float64 representadas para evitar cancelamento do determinante; saída é float64. Não há snap ou epsilon espacial oculto. O iterador de pares mantém ordem i/j e não aloca matriz quadrática; não há promessa de desempenho para milhões de pares nesta sprint.

Isso é API geométrica: não se declara identidade binária com a matriz MATLAB que deixa NaN/Inf em pares paralelos e não sinaliza sobreposição no campo intAdjacencyMatrix. As flags geométricas são preservadas separadamente para a futura camada de topologia; sua classificação científica continua em Q-11.

Distâncias ponto–ponto suportam matrizes de pares ou diagonal e normas positivas, incluindo infinito, no domínio 2D. Ponto–segmento retorna distância, projeção e parâmetro limitado a [0,1]. Preservar a regra da biblioteca distancePointEdge original: **comprimento ao quadrado menor que eps(float64)** é tratado como ponto inicial. Essa regra absoluta depende da unidade; não foi generalizada para remover nós/segmentos na importação. Alterá-la em uma futura análise requer decisão explícita. Matrizes de distâncias estimam memória e recusam alocação acima do limite configurável (256 MiB por padrão).

## Exemplos reais e rastreabilidade

A inspeção semântica da Sprint 1 encontrou traços totalmente repetidos em map1_edit_converted.txt nas linhas 1589/1595/1604 e em map7_edit_converted.txt nas linhas 2496/3242. A Sprint 0 havia validado somente estrutura numérica e pares. examples.json agora distingue estrutura de validade geométrica e registra as linhas. O leitor rejeita os originais com esses diagnósticos; os testes exercitam cópias temporárias preparadas explicitamente, mantendo as linhas excluídas vazias para preservar números físicos. Nenhum original foi alterado e não há opção de descarte silencioso.

Os testes usam os oito oráculos geométricos da Sprint 0, casos de borda e exemplos reais. Resultados reproduzíveis ficam em tests/reference/sprint1/numerical.json, gerados por scripts/validate_sprint1.py. MATLAB continua indisponível: correção analítica e implementação não significam paridade executada comprovada.
