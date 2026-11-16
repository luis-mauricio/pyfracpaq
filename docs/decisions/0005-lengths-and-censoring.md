# ADR 0005 — Lengths, censura e arquivos básicos

**Atualização S16:** Q05 aprovada explicitamente pelo usuário em14/11/2026: “Aprovo a Q-05.” Execução MATLAB real confirmou população legada[4,4,4] e pares desalinhados; comparação em sprint16/q05_comparison.json. Distribuições log-log também conferidas com os arrays nativos. Retângulo Lengths atual(.13,.11,.775,.815), título com pad3.5pt e ticks dos histogramas calibrados. A descrição abaixo registra a entrega histórica S4; ADR0018 e relatórioS16 atualizam disponibilidade/estado.

Data: 13/11/2026. Escopo: S04-01 a S04-08, LEN-01 a LEN-06/LEN-16 e parcela Lengths de EXP-04. Oito tarefas implementadas sob solicitação de execução da Sprint 4. Não há execução MATLAB disponível nem aprovação de paridade numérica/visual final.

## Integração e resultados

analysis/lengths.py calcula estatísticas, seleção, histogramas e frequências complementares sem Qt/Matplotlib. LengthSample mantém IDs, máscaras de traços/segmentos, comprimentos e ângulos brutos; arrays destacados somente para leitura. LengthResult inclui estatísticas, distribuições selecionadas, unidade, diagonal, limite geométrico e pares do cross-plot. Dataset e resultados de outras famílias não são alterados pela censura.

O registro habilita LEN-02 (dois histogramas), LEN-03 (quatro log-log) e LEN-06 (um cross-plot). As três seleções usam compute_lengths e cache restrito ao Run, portanto estatísticas e os três TXT são gerados uma vez mesmo com todas marcadas. Desenho e exportação PNG ficam na thread principal. A validação de todas as seleções ocorre antes de qualquer arquivo, inclusive se MLE/blocos/variograma pendentes forem selecionados.

Cross-plot sozinho agora despacha Lengths (Q-03). Apenas essa seleção exige norte; histogramas/log-log não leem norte, tensões ou cortes MLE. Log-log usa o mesmo popup de bins, mesmo quando Histogram of lengths está desmarcado. A habilitação visual desse popup segue o callback original e preserva o último valor congelado. Censura permanece com os estados/callbacks da Sprint 2, sem novos controles ou modos.

O Run padrão do FIG passa a funcionar: mapa de traços, mapa de strike, dois histogramas de comprimento e rosa — cinco PNGs, três TXT Lengths e EZROSE. MLE (Sprint 8), blocos/variograma (Sprint 7), SVG e imagens continuam indisponíveis e não são simulados. Quando essas futuras rotinas passarem a despachar Lengths, devem preservar os três TXT acoplados da família.

## Q-05 — Reprodução e decisão de integridade

A execução solicitada de S04-04 exige corrigir bordas/índices e manter máscara comum. O critério implementado é: **excluir um traço inteiro e todos os seus segmentos se o primeiro ou o último nó estiver exatamente em qualquer uma das quatro bordas reais do Dataset**. Usar X com x_min/x_max, Y com y_min/y_max, e o último nó efetivo. Domínio calculado antes da seleção; sem recalcular limites após excluir traços, tolerância de snap ou censura de segmentos avulsos. Um vértice intermediário na borda, com ambas as extremidades internas, não amplia esse critério baseado nas extremidades dos comentários originais. Inverter ordem dos nós preserva a seleção.

Isso corrige explicitamente a referência ao penúltimo nó e a mistura de eixos, além da perda de associação entre vetores. Uma máscara por traço expande-se pelos IDs dos segmentos; a mesma máscara filtra comprimentos, ângulos e IDs **antes** da duplicação ou ordenação. Não se preenchem arrays com NaN e não se filtram campos independentemente. Correções são deliberadas e podem mudar resultados de censura do legado: não declarar identidade nesse cenário.

Entrada [lengths_edges.txt](../../tests/fixtures/nodes/lengths_edges.txt): domínio [10,30]×[20,50], seis traços/sete segmentos. A tradução estática dos predicados defeituosos mantém os traços 1/2/3 (base zero), perde os dois internos porque Y=30 coincide com x_max e não detecta três bordas. Retém comprimentos [4,4,4], mas associa o prefixo angular [90,90,0], em vez de [90,0,0]. A seleção corrigida mantém os traços 4/5, comprimentos totais [7,5] e segmentos [3,4,5] associados a [90,0,36.86989764584402]. São quatro traços/quatro segmentos excluídos.

[q05_static_reproduction.json](../../tests/reference/sprint4/q05_static_reproduction.json) contém máscaras, pares e checksum do fonte. emulate_legacy_censor existe só no script de referência, sem modo defeituoso no produto. Não é resultado de uma execução MATLAB. A interpretação do índice lógico curto segue a explicação da [equipe de suporte MathWorks](https://www.mathworks.com/matlabcentral/answers/101714-can-i-perform-logical-indexing-when-the-logical-indexing-matrix-is-smaller-then-the-indexed-matrix-i): posições faltantes são falsas; após remover NaNs dos comprimentos, o teste passa a selecionar apenas o prefixo dos ângulos. Homologação científica externa e comparação nativa permanecem pendentes; a correção de integridade é a implementação solicitada para esta sprint.

## Estatísticas e bins

Console registra totais encontrados, números excluídos, números retidos e mínimo/máximo/média de cada população na unidade corrente. O total de segmentos encontrados agora se refere ao Dataset inteiro; o retido é informado separadamente, corrigindo o rótulo ambíguo do fonte após censura. Média por fsum/n, com normalização equivalente para a API isolada se a soma exceder float64. Estatísticas usam dados não formatados; console/TXT apresentam duas casas como no fonte.

Histogramas e distribuições simples usam centros `min:(max-min)/nBins:max`: 10/20/30/50 representam **n+1 centros**. Cortes são pontos médios; empate vai para o bin inferior, como em hist_centres da Sprint 3. Primeiro e último recebem caudas. Construção simétrica dos centros fixa os extremos e calcula cada metade a partir da borda correspondente, sem arange que ultrapasse o fim. A documentação [colon](https://www.mathworks.com/help/matlab/ref/double.colon.html) e o [suporte MathWorks sobre precisão](https://www.mathworks.com/matlabcentral/answers/95742-why-do-i-get-incorrect-results-with-floating-point-arithmetic-when-using-the-colon-operator) fundamentam essa escolha; empates nos últimos bits ainda exigem arrays MATLAB, não estão homologados por esses testes.

Frequência complementar preserva a equação do fonte: `C(L)=N-cumsum(hist(...))`, sem normalizar por N ou substituir por uma ECDF ordenada. Em pixels, centros `min:1:max`, incluindo o último valor somente se atingido pelo passo; a cauda entra no último centro mesmo que este seja menor que max. Em metros, 1000 intervalos/1001 centros, independentemente do popup. Por exemplo, comprimentos [1.2,1.4,2.1,2.6,3.9] em pixels produzem centros [1.2,2.2,3.2], contagens [2,2,1] e C=[3,1,0]. Zeros permanecem nos arrays e só são omitidos ao desenhar em log; o console registra essa quantidade.

**Q-08:** o limite geométrico usa `ceil(hypot(x_max-x_min,y_max-y_min))`, mantendo ceil do fonte e aplicando a diagonal corrigida na Sprint 1. Para o fixture, diagonal ≈36.05551275 e marcador 37; com os mesmos limites, a fórmula antiga baseada em (30,50) daria 59 (derivação, não execução MATLAB). Transladar para coordenadas negativas ou deslocar a origem não muda o marcador. Em metros a diagonal e o ceil são calculados após a escala. Em polilinhas cujo comprimento percorrido exceda a diagonal, os limites X acumulados incluem tanto o comprimento como o marcador, evitando inversão/corte da curva. Não se impõe um teto geométrico artificial às observações.

## Cross-plot e Q-10

Usa os segmentos retidos na ordem original. Reutiliza double_angles: subtrair norte, round MATLAB, duplicar a direção oposta e aplicar cada flip, sem módulo completo. Comprimentos duplicados na mesma ordem. Eixos do gráfico não são invertidos: os flips atuam nos ângulos. Valores fora de [0,360] continuam no resultado com aviso e são cortados pelos limites gráficos legados −10 a 370°.

O TXT de pares contém **ângulo bruto e comprimento**, sem duplicação, correção de norte, flips ou ordenação por comprimento. EZROSE continua pertencendo a Angles e usa seu vetor corrigido. A distinção está preservada, não houve unificação científica de convenções; Q-10 continua aberto nesse aspecto.

## Casos degenerados e limites de recursos

- Se a censura excluir tudo, erro associado a checkbox_censor antes de criar TXT/figuras, com contagens no console; arquivos anteriores permanecem intactos e a GUI abre Lengths. Não publicar mínimo/média NaN ou sucesso de uma amostra vazia.
- Valores iguais, inclusive um único segmento, geram um centro com toda a contagem. Não introduzir jitter nem uma população fictícia para contornar o passo zero do fonte. Barra de largura 10% do valor para desenho; min/max continuam exatos. Complementar zero gera eixos válidos e a indicação “No positive complementary frequencies.”, sem ponto substituto.
- Comprimentos não positivos/não finitos/vetores vazios são rejeitados pela API. Centros adjacentes indistinguíveis em float64 e escalas com limites de desenho inválidos produzem erro explícito antes dos TXT.
- A grade acumulada em pixels admite até 1.000.001 centros por população (limite configurável pela API). Acima disso, recusar com contexto; não reamostrar silenciosamente. A grade em metros continua com 1001. Isso evita alocações proporcionais a coordenadas enormes e mantém as frequências para entradas aceitas.

Essas proteções pertencem ao escopo técnico Q-02/S04-07. Não alteram amostragem válida, taxas, pesos, frequências ou fórmulas de ajuste. As tolerâncias da Sprint 0 não foram alteradas.

## Figuras e arquivos

Tema e exportador da Sprint 3: Arial/fallback DejaVu Sans, fundo branco, box/grid, proporção square, retângulo normalizado (.15,.16,.70,.70), título 11 pt negrito com segunda linha vazia, corpo 10 pt. Sem tight_layout/bbox tight. PNG automático 20×20 cm/600 dpi; 4724×4724 neste backend.

| Basename | Dados e apresentação |
| --- | --- |
| FracPaQ2D_histotracelength | centros/contagem dos traços, barras azuis; min/max verticais vermelhos 1 pt; X 0..1.1max, Y 0..1.2max(contagem); frequência absoluta azul e percentual laranja à direita |
| FracPaQ2D_histosegmentlength | mesmo contrato para segmentos; porcentagens usam a população retida de segmentos |
| FracPaQ2D_loglogplottracelengthdensity | frequência simples de traços, quadrados preenchidos 6 pt sem linha, contornos de marcador 1 pt; min/max vermelhos; X .9min..1.1max, Y .1..1.2max(contagem) |
| FracPaQ2D_loglogplottracelength | C(L) de traços; mais linha vermelha tracejada na diagonal/ceil; Y .1..1.2N; X inclui diagonal e comprimentos |
| FracPaQ2D_loglogplotsegmentlengthdensity | mesmo contrato de frequência simples para segmentos |
| FracPaQ2D_loglogplotsegmentlength | mesmo contrato complementar para segmentos |
| FracPaQ2D_crossplotsegmentlengthangle | quadrados preenchidos 2 pt; min/max horizontais vermelhos, diagonal tracejada; X −10..370°, ticks de 60°, Y 0..1.1max(segmento) |

Log-log tem ticks X principais explicitamente em 10⁻³ a 10⁴ como no fonte, formatação em potências de dez, sem rótulos secundários artificiais e grade secundária pontilhada. Isso pode deixar uma faixa estreita sem rótulo X principal. Rótulos/títulos/unidades em inglês preservados. Inspeção documental: manual p. 18 (dois histogramas), p. 19 (log-log) e p. 21 (cross-plot); parâmetros completos/arrays desses exemplos não são conhecidos, portanto não há SSIM homologado ou comparação entre populações diferentes.

TXT, gerados uma vez por despacho de Lengths, inclusive cross-plot isolado:

| Nome | Conteúdo |
| --- | --- |
| FracPaQ2Dsegmentlengths_{tag}.txt | segmentos retidos ordenados, uma coluna, `%6.2f\n` |
| FracPaQ2Dtracelengths_{tag}.txt | totais dos traços retidos ordenados, mesmo formato |
| FracPaQ2Dsegmentangleslengths_{tag}.txt | pares brutos na ordem de entrada, `%6.2f\t%6.2f\n` |

Sem cabeçalho; tag vazia mantém `_`. Três arquivos temporários próprios são inteiramente escritos antes da primeira substituição. Cada replace é atômico, como nos exportadores existentes; falha de staging preserva todos os arquivos anteriores e limpa somente temporários próprios. O conjunto não é uma transação de filesystem: falha de replace após outro replace concluído pode deixar arquivos de execuções distintas; o erro é propagado e não há mensagem de sucesso. Não apagar arquivos alheios nem reescrever a tag.
