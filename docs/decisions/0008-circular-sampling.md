# ADR 0008 — Amostragem circular e decisão Q-20

Data: 14/11/2026. Escopo: S07-01 a S07-08, MAP-07/08/09/10/18. Referência: guiFracPaQ2Dpattern.m, de David Healy e Nikolai Andrianov, na distribuição FracPaQ 2.8 preservada. Execução MATLAB indisponível; este documento registra implementação e conferência analítica, sem declarar paridade nativa.

## Decisão científica autorizada

Foi apresentada ao usuário a diferença para um círculo de raio 1 e segmento horizontal (−2,0)→(2,0): o predicado do legado produz n=0/P21=0, enquanto a geometria finita produz n=2/P21=.5. O usuário respondeu **“Corrigir a contagem geométrica”** em 14/11/2026. Essa autorização define a contagem corrigida como padrão, sem acrescentar modo ou controle à GUI.

Cada segmento fechado contribui com o número de pontos distintos em que encontra a circunferência. Uma secante finita contribui com dois, tangência com um, e interseção na extremidade com um. Um segmento interno não contribui para n; uma reta que encontra o círculo apenas fora do intervalo do segmento também não contribui. Inverter o segmento preserva as contagens. Pontos de encontro comuns a segmentos diferentes são contados por segmento, sem deduplicação entre eles.

Para m, mantém-se o interior estrito do original: cada extremidade de cada segmento contribui se distância < r; igualdade com a borda não contribui. Um nó interno compartilhado por dois segmentos contribui duas vezes. Não se trocam extremidades de segmentos por extremidades de traços. Esses critérios resolvem explicitamente a tangência pendente do fixture da Sprint 0.

O teste exige projeção dentro do segmento e discriminante geométrico, sem a condição incorreta de mudança de sinal simultânea em X e Y. O caminho vetorizado usa coordenadas relativas e precisão estendida; sinais próximos do erro aritmético são recalculados com Fraction a partir dos float64 originais. O limite de erro apenas aciona o cálculo exato; não faz snap, não torna o círculo maior e não converte quase tangência em tangência. Saídas são float64/contagens int64, sem Qt ou Matplotlib no núcleo científico.

[q20_static_reproduction.json](../../tests/reference/sprint7/q20_static_reproduction.json) contrapõe os fixtures analíticos à tradução estática dos predicados do fonte. **Não é resultado de execução MATLAB.** O emulador fica somente no script de referência, fora do produto. Graphs continua pendente na Sprint 13 e deverá reutilizar a decisão, sem anunciar que já foi corrigido.

## Grade, estimadores e domínio

Com N círculos no lado menor, usa-se passo menor = amplitude/(N+1), r=.99×passo/2. O passo maior é reconstruído por 2r/.99 e a quantidade maior é floor(amplitude/passo−1), seguindo a ordem aritmética do fonte. Domínio quadrado usa N×N. Não arredondar razões quase inteiras com epsilon. Centros são min+passo×índice, a partir de 1. As matrizes têm forma (ny,nx), com linhas em Y crescente e colunas em X crescente; os TXT percorrem X por fora e Y por dentro (ravel order F).

P21 local = n/(4r), em pixel⁻¹ ou metre⁻¹. P20 local = m/(2πr²), em pixel⁻² ou metre⁻². Separadamente, os globais são soma dos comprimentos de todos os segmentos/área e quantidade de segmentos/área. Não são médias das janelas. O domínio vem do Dataset já validado, incluindo área completa de imagem e correções anteriores de limites; escala reconstrói coordenadas a partir da origem. Flips são exclusivamente de apresentação para esta família.

Exige-se inteiro N≥2, largura/altura/área positivas e finitas, centros distintos/representáveis e denominadores/resultados representáveis. Domínio de área zero é erro contextual em edit_numscancircles antes de exportar a família. Limite técnico de trabalho: 256 MiB, estimativa conservadora de 128 bytes por janela e 1024 por segmento, sem matriz janelas×segmentos. Grade excessiva/aspecto extremo é recusado antes de alocação volumosa. Interrupção é consultada entre círculos e antes dos TXT; progresso é integrado ao intervalo da análise no Run. Não se preenchem resultados inválidos com zero/NaN.

## Integração, arquivos e aparência

MAP-07 e MAP-08 compartilham cálculo/cache apenas no Run corrente. Selecionar qualquer um escreve **ambos** FracPaQ2Dintensity_{tag}.txt e FracPaQ2Ddensity_{tag}.txt, uma vez. Cada linha: `%8.1f %8.1f %14.8f\n`, sem cabeçalho, três colunas X/Y/valor. O underscore permanece com tag vazia. A precisão histórica de uma casa para centros pode produzir coordenadas textuais repetidas em unidades pequenas; os arrays mantêm a precisão completa. Não aumentar silenciosamente a precisão. As duas escritas são preparadas antes de substituir destinos, com substituição atômica individual, não transação de grupo. Arquivos alheios são preservados.

Show circles acrescenta uma única figura para a família, antes do primeiro mapa selecionado. Não cria seleção independente de análise. O mapa de círculos usa a primeira cor do conjunto para os traços, como sColour no original; não cria o mapa multicolorido acoplado aos mapas básicos. Desenho/exportação PNG permanecem na thread principal; cálculos ocorrem no worker.

| Propriedade | Implementação |
| --- | --- |
| Scan map | FracPaQ2D_scancircle; traços .75, círculos vermelhos .25, raio em coordenadas reais, aspecto igual e limites completos |
| Título scan | Mapped trace segments, n={segmentos}, seguido de linha vazia |
| Heatmaps | FracPaQ2D_intensityP21 / FracPaQ2D_densityP20; matriz sem flip, origin lower, amostragem nearest |
| Extensão imagesc | Primeiro/último centro ± meio passo; limites dos eixos continuam os do domínio completo, com margem branca |
| Títulos | Estimated Intensity of segments (P21) / Estimated Density of segments (P20), seguidos de linha vazia |
| Eixos | X/Y, pixels ou metres; flips independentes nos eixos |
| Paleta | hot nominal reconstruída de 256 níveis, invertida, mesmo recurso da Sprint 6; comparação RGB MATLAB pendente |
| Barra | Horizontal inferior, [0,max], unidade singular pixel ou metre com expoente −1/−2; largura vinculada ao plot em cada desenho/redimensionamento/exportação, conforme [ADR 0009](0009-responsive-colourbars.md) |
| Janelas todas zero | Arrays continuam zero; norm de exibição [0,1] e único tick zero evitam caxis [0,0] inválido, sem fabricar estimativas |
| Exportação | Rotina comum, 20×20 cm/600 dpi, tag, 4724×4724 observados neste backend |

Mantêm-se as tolerâncias congeladas da Sprint 0: contagens exatas, taxas rtol=1e−10/atol=1e−12 na unidade apropriada. A correção Q-20 é divergência científica deliberada, não igualdade com o predicado defeituoso. Homologação MATLAB de grades, arquivos e rasters/SSIM continua pendente.
