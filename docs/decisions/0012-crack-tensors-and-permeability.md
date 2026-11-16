# ADR 0012 — Crack tensors e permeabilidade

14/11/2026. Implementação integrada ao registro padrão, sem novos controles. Referências: guiFracPaQ2Dangle, guiFracPaQ2Dcracktensor, getF2/4/8tensor e guiFracPaQ2Dtensor fornecidos, por David Healy/FracPaQ. Equações, polaridade, saídas e limites são testados separadamente da aparência.

## Tensores e convenções

Para cada segmento, n=(cosd(polo),sind(polo)) e peso=L²/A. F0=sum(pesos); F2/F4/F8 somam peso vezes o produto externo de n na ordem correspondente. A projeção é sum(peso×(n·v)^ordem), v=(cos(alpha),sin(alpha)), em 361 valores de 0 a 2π, incluindo a repetição final. Os componentes completos simétricos (2^ordem) e as projeções são preservados em arrays float64 somente para leitura.

Crack usa polos **round(ângulo bruto+90−norte)** e depois reverseAxis por cada flip. Permeabilidade aplica reverseAxis aos strikes **sem arredondar** e só então soma 90−norte. Essa diferença do fonte é intencionalmente preservada. Não utilizar o vetor axial duplicado da rosa como se fossem polos ou como uma segunda contagem de segmentos.

A é a área do envelope dos nós dos traços, como getMapLimits nas rotinas tensorais, com amplitudes reais do núcleo geométrico existente. Não é automaticamente a área da tela raster: a imagem pode ter uma margem vazia. Domínio linear tem A=0 e é recusado com diagnóstico; não se inventa largura para permitir uma divisão. O fixture tensor_network.tif fornece uma rede bidimensional após Hough. Os fixtures de uma única linha continuam úteis para outros testes, mas seu envelope não permite esses tensores.

O cálculo usa momentos simétricos e blocos de 1024 segmentos para a projeção, com orçamento conservador de memória de 256 MiB e interrupção cooperativa. Não aloca N×2^8. F16 continua destinado à API complementar da Sprint 15.

## Placas paralelas

Abertura fixa t≥0 na unidade de comprimento corrente; escalada t=a×L^b, com a∈[0,.1] e b∈[.5,1]. λ∈[0,1], independente da conectividade. P=sum(t³×L/A×n⊗n); K=(λ/12)×(tr(P)I−P), com autovalores simétricos e projeção vᵀKv. Abertura zero e λ=0 retornam K zero, sem NaN. O parâmetro inativo não é lido/validado. No chamador MATLAB, abertura fixa zero passa fator/expoente zero e também produz abertura zero; o port representa o modo explicitamente, sem depender desse sentinela.

Dobrar a abertura multiplica K por oito; λ é linear. Reescalar todas as dimensões, incluindo a abertura, por 1/s divide K por s². Informar a abertura já na unidade atual do Dataset; mudar pixels para metros não converte automaticamente o número digitado no campo. No modo escalado, a unidade do fator depende de b.

O fonte inicializa t e Kpol como matrizes quadradas por engano. O port usa vetores e uma única curva polar, removendo as colunas extras de zeros; preserva os coeficientes científicos. Console conserva os rótulos Maximum/Minimum permeability, unidades pixels^2/metres^2 e cinco algarismos significativos observados no num2str nativo. A área usada é registrada separadamente.

## Despacho e figuras

FLO-08 passa pelo mesmo compute_angles/cache das seleções ANG. AngularResult carrega o tensor opcional; EZROSE recebe os strikes axiais duplicados/ordenados, uma única vez por Run. A falha do tensor impede o TXT dessa família. FLO-09 é independente e não exporta TXT novo.

Figuras FracPaQ2D_cracktensor e FracPaQ2D_permeability_polar: norte no topo, sentido horário, linhas 1.5; ordens 0/2/4/8 em magenta/azul/vermelho/verde, legenda horizontal inferior. Permeabilidade azul. Metadata [nativa](../../tests/reference/sprint10/native/layout.json) confirma ticks/limites, rótulos radiais a 10°, grid .15/.15, linewidth .5 e fonte Helvetica. A fábrica de estilo aceita a preferência Helvetica para esses polares, com fallback explícito Arial/DejaVu Sans; os demais gráficos conservam Arial. Nenhuma fonte é redistribuída.

Composição de impressão calibrada pelos PNGs nativos; escala radial usa passos 1/2/5 e notação ×10 por tick. K zero mantém só o tick zero. Exportação comum 20×20 cm/600 dpi, sem tight_layout ou recorte. Não há barras de cores nos polares.

## Evidências e limites

MATLAB 24.2.0.3212159 (R2024b Update 9) executou getF2/4/8tensor, equações P/K, rotinas gráficas e exportações, sem editar a distribuição. [Comparação](../../tests/reference/sprint10/native_comparison.json): erros da ordem de 10^-15 nos tensores/projeções e 10^-22 ou menores em K/projeções nos casos capturados; casos zero exatos. Tolerâncias dimensionais da Sprint 0 preservadas, sem atol absoluto que esconda K pequeno.

[Validação](../../tests/reference/sprint10/validation.json) contém TXT/SVG/Hough, padrão de referência e caso zero: dez PNGs/QA, cinco EZROSE, tensores, P/K, autovalores e parâmetros. Os testes Qt exercitam a janela normal, cache angular e os dois modos de abertura. [checks.json](../../tests/reference/sprint10/checks.json) registra regressão, pacote e integridade. A homologação visual integral por regiões/SSIM e em outras plataformas pertence à auditoria final; não se declara identidade completa a partir de inspeção ou testes numéricos.
