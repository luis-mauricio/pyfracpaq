# Comparação com SD11A.txt

**Estado posterior — 16/11/2026:** S16-04 concluída após correções, revisão semântica e aceite dos 16 detalhes atuais; S16-09 permanece aberta. [Relatório final](sprint-16-rendering.md) e [estado](../../tests/reference/sprint16/final/status.json). A execução inicial abaixo é preservada como histórico.

Em 15/11/2026, por indicação do usuário, o arquivo original `fracpaq-matlab/SD11A.txt` foi executado no MATLAB R2024b Update 9 e no port Python. **A captura pareada foi concluída; a homologação visual permanece aberta.** Os 164 arquivos originais e os oito resultados preexistentes foram preservados.

## Entrada e configuração

O TXT tem 32.976 bytes, 445 traços, 1.076 segmentos e 1.521 nós. Foi lido diretamente, sem preparar, filtrar ou normalizar suas linhas CR. SHA-256: `96bafa56537444279a748c3f4b7a4300f7e73341a04d2ba4ff8cf1299ad74688`. Não houve diagnóstico de geometria inválida.

Como não foi informada escala física, a unidade é pixels: X=[0;1997,7], Y=[1,8;1988,5], norte 0°, sem inversões. Foram usados 20 bins de comprimento/ângulo, rosa de 10°, 12 círculos, tolerância I→Y de 2 pixels, sem censura/cortes. Os marcadores de nós, círculos e média da rosa foram habilitados para inspeção. Tensões de 100/50 MPa, azimute 0°, coesão/Pf=0, atrito 0,6, abertura fixa 0,001 e lambda=1.

Graphs usa explicitamente a linha horizontal (0;995,15)→(1997,7;995,15). Wavelets usa um caso controlado Morlet, a=32, fator L=2 e passo 90°; **ambas as interfaces passam razão 1/L=0,5 à transformada**. Esse caso não cobre toda a grade padrão da GUI nem Mexican Hat. Todos os parâmetros estão congelados em [parameters.json](../../tests/reference/sprint16/sd11a/parameters.json).

## Execuções e concordância numérica

O Python executou as 30 rotas do registro, com cálculo, renderização e exportação reais: 51 PNGs finais. As 15 chamadas de famílias ao fonte MATLAB também terminaram com sucesso e produziram os 51 PNGs correspondentes. As famílias são mapas básicos, Lengths, Angles, MLE, amostragem circular, conectividade, permeabilidade, quatro análises de estabilidade, blocos, variograma, Graphs e Wavelets. Hough e agrupamento SVG por cor não se aplicam a esta entrada TXT.

Os [81 confrontos de arrays/curvas](../../tests/reference/sprint16/sd11a/numeric-comparison.json) preservam ordem de observação, formas e classes de não finitos. **74 passaram e sete registram diferenças explícitas**, descritas abaixo. Isso não equivale a 81 testes independentes de famílias. Comprimentos e ângulos brutos diferem apenas por arredondamento numérico, com erros máximos de aproximadamente 1,14×10⁻¹³ pixels e 2,84×10⁻¹⁴ graus. Coincidiram histogramas, complementares, ângulos duplicados, tensores F2/F4/F8 e suas curvas, permeabilidade, curvas de Mohr, variograma, três perfis ALONG e os dois perfis FROM de segmentos. As coordenadas dos círculos também coincidem.

Os quatro TXT de comprimentos, pares ângulo/comprimento e EZROSE são **idênticos byte a byte**. O arquivo revelou uma diferença técnica no EZROSE: a ordenação instável trocava a posição de `0.00` e `-0.00`. O exportador agora usa ordenação estável, preservando a sequência de empates nativa, sem mudar os valores científicos. Há regressões com zeros assinados e com o próprio SD11A.

O MLE usa semente 20261115 nos dois ambientes para reprodução local. Geradores diferentes não produzem as mesmas amostras apenas por terem a mesma semente: não se exige igualdade entre percentuais Monte Carlo dessa execução. As curvas observadas e os ajustes determinísticos foram comparados separadamente. Os testes K-S compartilhados da Sprint 8 continuam sendo a evidência de paridade do procedimento estatístico.

## Diferenças identificadas

| Caso | MATLAB original | Python / explicação |
| --- | --- | --- |
| Centro do traço da linha 397 | (1605,9;690,65), fora do segmento | (1605,9;644,75), metade de (1605,9;667,7)→(1605,9;621,8). |
| Centro do traço da linha 389 | Y=772,7301571943 | Y=754,6698428057, metade do caminho acumulado sobre um subsegmento vertical descendente. |
| FROM de traços | Propaga os dois centros incorretos | Propaga os centros corretos; maior diferença de distância: 45,9 pixels. |
| P21 Maps/Graphs | Predicado legado de secantes | Contagem geométrica finita aprovada em Q20. P20 Maps coincide neste caso; P20 Graphs também incorpora a normalização aprovada. |
| Conectividade I/Y/X | 685/155/82 | 606/224/90; classificação aprovada em Q11, com tolerância 2. |
| Blocos | 65 componentes | 67 blocos; diferenças de raster, exterior e calibração aprovadas em Q14. |
| Lognormal de segmentos | Cauda final com 1.076 valores | Cauda com 1.053 valores a partir de xmin=15,3326449121; consistência por cauda aprovada em Q15. |
| Wavelets | Raster e respostas nativos | Raster determinístico aprovado em Q12; diferenças quantificadas à parte. |

Os sete confrontos não coincidentes são: centros dos traços, FROM de traços, P21 Maps, P21/P20 Graphs e as duas coordenadas da curva lognormal estimada de segmentos. A contagem I/Y/X e os blocos ficam em registros próprios, sem tratar populações diferentes como arrays iguais.

O erro dos centros foi reproduzido no leitor original, que desloca para cima quando o segmento vertical é descendente. **O Python já cumpria S01-04, que exige metade do caminho do traço; sua geometria não foi alterada nesta comparação.** O caso complementa a evidência técnica de Q07. Não se promoveu uma nova fórmula científica nem se reproduziu um centro fora do traço para obter igualdade de pixels.

Para Wavelets, há uma verificação adicional do núcleo Python sobre os **mesmos pixels nativos**, separada do Run real com raster Python. O maior erro absoluto dos coeficientes foi 6,94×10⁻¹⁷; máscara e 23.568 ângulos duplicados coincidiram exatamente, com 11.784 pixels selecionados. Nos rasters de produção, 5,1916% dos pixels diferem, com erro absoluto médio de 7,2312 em 255 níveis de cinza; a propagação resulta em 23.568 ângulos nativos contra 21.654 Python. Portanto, a concordância do núcleo sobre pixels compartilhados **não significa igualdade das saídas de produção**. [wavelet-comparison.json](../../tests/reference/sprint16/sd11a/wavelet-comparison.json) preserva as duas verificações.

## Figuras e pendências

As [51 figuras pareadas e diferenças](../../tests/reference/sprint16/sd11a/gallery.md) podem ser inspecionadas em folhas lado a lado ou nos PNGs completos. Os cálculos SSIM RGB usam os PNGs originais, sem alinhamento artificial, translação ou redimensionamento. Somente as miniaturas da galeria são reduzidas para navegação.

As [métricas por figura/região](../../tests/reference/sprint16/sd11a/image-comparison.json) são diagnósticas: as regiões ancoradas nos eixos Python podem se sobrepor e ainda não representam a partição semântica independente exigida para homologação final. Nenhum dos 51 PNGs completos atingiu SSIM0,98; os valores globais variam de 0,786851 a 0,979517. Há diferenças visíveis de ticks e limites automáticos, margens, preenchimento de marcadores, legendas e disposição das rosas. Resultados científicos aprovados também afetam os pixels e são mantidos explícitos. A geometria responsiva e a folga fixa das barras exigidas pelo usuário continuam preservadas.

**S16-04 e S16-09 continuam abertas.** Não se marcou X pela mera disponibilidade de capturas, não se reduziu SSIM0,98 e não se declarou identidade visual. Esta rodada fornece o caso real pedido e identifica os próximos ajustes com evidência.

## Procedência e reprodução

- [Procedência MATLAB](../../tests/reference/sprint16/sd11a/native-provenance.json), [chamadas nativas](../../tests/reference/sprint16/sd11a/native/native_calls.json) e [script de captura](../../scripts/capture_sd11a.m).
- [Procedência Python](../../tests/reference/sprint16/sd11a/python-provenance.json), [execução das 30 rotas](../../tests/reference/sprint16/sd11a/python/validation.json) e [comparador](../../scripts/compare_sd11a.py).
- [Suíte completa e JUnit](../../tests/reference/sprint16/sd11a/checks.json):686 testes passaram em77,56s, em cópia isolada com exatamente os 164 originais. Windows/Linux permanecem adiados conforme orientação do usuário.

Com a venv do projeto e `PYTHONPATH=.:scripts`, executar `scripts/compare_sd11a.py prepare`, depois `python`; recapturar MATLAB com `run('scripts/capture_sd11a.m')`; por fim executar as fases `numeric`, `wavelet`, `images`, `gallery` e `provenance`. Usar `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib` nas fases Python. MATLAB/toolboxes são necessários somente para recaptura. PNGs existentes com os mesmos hashes podem reutilizar as métricas verificadas.

A captura inicial em `diagnostic-initial-direct-L2` foi preservada somente para rastreabilidade: sua chamada wavelet passou L diretamente antes da revisão do callback da GUI. Ela está excluída da referência pareada e de seu manifesto. A captura válida em `native` usa o recíproco exatamente como o callback original.

## Continuação

Os ajustes posteriores e as métricas atuais estão no [relatório de renderização S16-04](sprint-16-rendering.md) e no [estado consolidado](../../tests/reference/sprint16/final/status.json). Os números visuais desta página descrevem a rodada inicial preservada, não os candidatos posteriores. Os 81 confrontos numéricos e quatro TXT foram repetidos sobre os candidatos novos, mantendo as diferenças científicas explícitas.
