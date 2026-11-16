# ADR 0007 — Imagens, Hough determinístico e domínio raster

**Atualização S16:** A auditoria S16 executou os três estágios MATLAB em cinco rasters, corrigiu quantização/vizinhança/ordem e obteve igualdade exata inclusive Macduff/Orkney. O estado “sem MATLAB” e os números da S6 abaixo são históricos. Contrato atual: trigonometria em radianos; arredondar coordenada positiva do bin após offset; NHoodSize=2*ceil(size(H)/100)+1; ordenar endpoints pelo eixo de maior extensão crescente. ADR0018 e sprint16/hough_comparison.json prevalecem sobre as estimativas anteriores.

Data: 14/11/2026. Escopo: S06-01 a S06-09. O port implementa o fluxo do fonte fornecido e fixa convenções testáveis. **Sem MATLAB/Octave, ainda não foi demonstrada igualdade de votos em todos os empates, supressão, endpoints ou rasters com uma execução nativa.** Resultados abaixo são medições Python, não referências MATLAB inventadas.

## Leitura e preparação

io/images.py aceita conteúdo JPEG/TIFF com um frame, modo L, grayscale de oito bits. Não converte RGB/RGBA, paleta, modo binário de um bit ou profundidade maior; extensão não substitui inspeção do conteúdo. Metadados de formato, modo, largura/altura, bit depth, número de frames e caminho são registrados no console antes da validação e acompanhando o erro. Não aplicar orientação EXIF automaticamente. MacduffBinary.tif e Orkney1aBinary.tif são compatíveis; Macduff.tiff e Orkney1a.tiff fornecidos são RGBA e são rejeitados explicitamente.

Preparação reproduz `imcomplement(uint8)` seguido de conversão numérica para lógico: **todo pixel diferente de 255** vira foreground. Não há limiar de cinza adaptativo, edge detector ou skeletonização. Clean remove apenas foreground sem nenhum dos oito vizinhos, com exterior falso; implementado por convolução 3×3 sem centro. Pixels 128/254 ligados a vizinhos permanecem, como exige a interpretação numérica de [bwmorph](https://www.mathworks.com/help/images/ref/bwmorph.html). Os arrays originais não são modificados.

Limites: leitura até 16.777.216 pixels; a memória prevista para H, cópia de supressão, coordenadas e buffers precisa caber em 256 MiB. O cálculo estima o custo antes de materializar as coordenadas de foreground. O diagnóstico de malha completa aceita até 1.100.000 células por painel; recusa entradas maiores com mensagem, sem reduzir a grade ou o número de ângulos silenciosamente.

## Acumulador

analysis/hough.py não usa detector probabilístico. Grade theta = −90:0.5:89.5, 360 colunas. Rho de −ceil(D) a +ceil(D), passo 1, com D=hypot(height−1,width−1). Votos usam `rho=x*cos(theta)+y*sin(theta)` com primeiro pixel interno em (0,0), de acordo com [hough](https://www.mathworks.com/help/images/ref/hough.html). Matriz `[rho,theta]` int64; cada pixel vota uma vez por coluna. Quantização explícita para inteiro usa round de empates para longe de zero. Trigonometria em graus compartilha a convenção cardinal da Sprint 3. Buffers são processados por ângulo, com progresso/interrupção cooperativa.

Um oráculo escalar independente percorre pontos/theta e confere todos os votos de uma imagem pequena, não apenas o pico máximo. Horizontais, verticais e diagonais conferem células conhecidas. As matrizes inteiras são preservadas; nenhum comparador usa tolerância para aceitar contagens diferentes. Arredondamento de meio bin/trigonometria nos limites ainda exige vetores MATLAB para homologação.

## Picos e linhas

Limiar = `ceil(fator*max(H))`. Seleção inclui valor igual ao limiar, limita a quantidade de picos e para se não houver votos positivos, mesmo com threshold=0. NHoodSize é o menor ímpar ≥size(H)/50, conforme [houghpeaks](https://www.mathworks.com/help/images/ref/houghpeaks.html). Em empates, o primeiro máximo em ordem de coluna/linha é escolhido; a cópia de trabalho zera a vizinhança, mantendo H original. Ao cruzar a costura angular, a supressão reflete rho e circula theta. Essa política é explícita e determinística, mas os detalhes não especificados pelo toolbox devem ser comparados com a versão MATLAB do projeto; não apresentar essa escolha como resultado nativo observado.

Para cada pico, recuperar exatamente os pixels que votam naquele bin. Ordenar de forma estável pela projeção na tangente da linha; separar quando a distância euclidiana entre pixels consecutivos for **maior** que FillGap. Distância igual é unida. Manter fragmentos com distância euclidiana entre endpoints ≥MinLength. Endpoints são pixels reais, não projeções artificiais, devolvidos como `(col+1,row+1)`. Preservar ordem dos picos/fragmentos e não deduplicar linhas de picos diferentes. Esses critérios seguem a finalidade de [houghlines](https://www.mathworks.com/help/images/ref/houghlines.html); igualdade exata de associação, empate e limites de lacuna com o toolbox permanece pendente. Testes de lacuna 4/3.99 e comprimento 3/3.01 tornam a decisão auditável.

GUI valida npeaks inteiro 100–5000, limiar >0 e ≤1, FillGap/MinLength finitos >1 pixel. A API permite npeaks 1–5000 para casos direcionais controlados, sem novo seletor na tela. Parâmetros e diretório/tag são congelados ao iniciar Preview. Alterar entrada, tipo, escala ou qualquer parâmetro Hough invalida o resultado e exige nova prévia.

## Modelo e Q-06

Cada fragmento é um TraceInput azul com dois nós/um segmento, construído pelo mesmo núcleo dos outros leitores. Centros de traço/segmento, cor, comprimento total, ângulo bruto e end_length do **próprio segmento** ficam preenchidos. Não usar o comprimento do primeiro traço para todos os demais. IDs seguem a ordem de extração.

Dataset ganhou source_bounds opcional em coordenadas não escaladas. Para imagem, conservar [0,width]×[0,height] como no fonte, mesmo se as linhas ocuparem apenas uma parte do raster; não redefinir área pela caixa das detecções. build_dataset valida contenção e aplica escala uma vez. with_scale reconstrói a partir dos registros e preserva esse domínio, evitando escala cumulativa. TXT/SVG sem domínio explícito continuam usando os nós. Isso permite usar os mesmos mapas, Lengths e Angles sem depender de campos particulares do leitor TXT. As famílias futuras de conectividade, variograma e Graphs continuam indisponíveis, mas recebem o contrato geométrico completo quando implementadas.

Array de imagem mantém a ordem original das linhas; votos internos usam origem zero, endpoints e desenho usam centros de pixels base um. Y não sofre flip cumulativo: a prévia e a imagem diagnóstica exibem Y normal, como o fonte. Flip X/Y da aplicação altera a visualização e as rotinas angulares existentes, sem modificar a detecção.

Sem linhas, manter diagnóstico e parâmetros, exportar a figura e informar erro em MinLength; não criar Dataset fictício nem liberar Run. Metadados inválidos e parâmetros inválidos não geram figura. Resultados obsoletos não publicam diagnóstico; recursos temporários próprios são isolados e liberados.

## Diagnóstico e cores

plots/hough.py gera `FracPaQ2D_Houghstuff_{tag}.png` no Preview, no diretório corrente capturado, pelo exportador comum 20×20 cm/600 dpi. O diagnóstico usa a tag atual congelada, evitando depender da tag global de um Preview/Run anterior. Sem sobreposição de moldura/toolbar ou screenshot do widget.

| Painel | Conteúdo |
| --- | --- |
| superior esquerdo | imagem de entrada em bone; X/Y pixels, Y normal, aspecto igual, domínio raster |
| superior direito | malha completa H(theta,rho) e plano H=threshold; vista lateral em rho/H |
| inferior esquerdo | malha completa em vista superior, rho invertido; theta/rho e mapa hot |
| inferior direito | mesma malha e plano, vista lateral em theta/H |

Três malhas usam todas as células com passo 1; não reduzir a projeção a um perfil máximo nem decimar a superfície. Projeção ortográfica. MATLAB e Matplotlib usam referências de azimute diferentes: vistas laterais foram traduzidas para azimutes 0 e −90 do Matplotlib, com elevação 0; plano usa −90/90. Ticks/rótulos de eixos colapsados são ocultados para impedir sobreposição. O plano tem borda preta visível. Figura/eixos brancos, títulos 9 pt, labels 9 pt/ticks 8 pt no layout 2×2. A posição do label theta no topo da vista plan é uma variação do motor ainda sujeita à calibração nativa.

hot/bone de 256 níveis estão congeladas em matlab_rgb.npz, com método em matlab_rgb.json e gerador freeze_matlab_palettes.py. São reconstruções independentes das rampas nominais (hot por trechos; bone=(7*gray+fliplr(hot))/8), **não tabelas capturadas do MATLAB**. Não se presume igualdade só por usar um nome de colormap. Âncoras, formas e limites são testados; a comparação RGB nativa permanece pendente. Referências: [hot](https://www.mathworks.com/help/matlab/ref/hot.html), [bone](https://www.mathworks.com/help/matlab/ref/bone.html).

## Medições e limites de aceite

Parâmetros GUI padrão (1000, .33, 5, 3), sem escala: directional tem H 89×360, max=24, threshold=8, sete picos/sete traços; rectangular H 107×360, max=40, threshold=14, três picos/três traços; MacduffBinary H 723×360, max=126, threshold=42, 355 picos/1507 traços; Orkney1aBinary H 1447×360, max=364, threshold=121, 29 picos/169 traços. Essas são **medições Python**, não quantidades homologadas no FracPaQ.

tests/reference/sprint6 contém arrays completos de raw/clean/H/theta/rho/picos/endpoints/estatísticas, parâmetros, hashes e 17 PNGs (quatro diagnósticos e 13 análises anteriores com origem em imagem). Testes Qt verificam prévia, exportação, reescala, invalidação, erro de formato, ausência de linhas e Run padrão. Manual p. 7 é referência documental do diagnóstico. Não há SSIM aprovado, capturas MATLAB controladas ou equivalência anunciada em Windows/Linux. As tolerâncias congeladas permanecem intactas.
