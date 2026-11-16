# ADR 0013 — Estabilidade, Mohr e decisão Q-17

14/11/2026. **Q-17 aprovada explicitamente pelo usuário: “Aprovo a correção Q-17.”** A pergunta apresentou a reprodução numérica, a correção de normalização/cores/igualdade, os limites contextuais e a preservação da convenção de cores por comprimento. As quatro análises estão integradas ao Run padrão, com um único algoritmo científico.

## Reprodução antes da decisão

O MATLAB R2024b Update 9 executou os fontes originais e as expressões intermediárias indicadas neles. Para strikes 0°/90°, σ1=100, σ2=50, azimute=30°, C0=2, Pf=10 e μ=.6: sn=[62.5,87.5], |tau|≈[21.6506351,21.6506351]. Tsmax preliminar=0 porque o fonte o calcula antes da rotação; a chamada real falha com MATLAB:badsubscript.

Sf≈[19.7489415,44.7489415], mas a faixa preliminar é [43.3333333,93.3333333]. O arredondamento antes de multiplicar por 100 deixa ambos os índices em 1. O port aprovado normaliza pelas tensões efetivamente corrigidas: TsNorm=[1,5/7], faixa Sf igual aos valores observados e índices Sf 1/100. A [comparação](../../tests/reference/sprint11/q17_comparison.json) mantém entrada, números e aprovação; a pasta candidate preserva o registro anterior à aprovação.

Os casos μ=0/Sf e σ1=σ2/Td também falham por índice inválido no original. A igualdade σ1=σ2=100, μ=C0=Pf=0 é CSF no mapa e Non-CSF na rosa nativa. MAT conserva inclusive os NaN/Inf das expressões inválidas; native_calls.json registra chamadas reais, diferenciadas de avaliação de fórmulas. Não se atribuem os resultados corrigidos ao original.

## Regra científica aprovada

Parâmetros compartilhados: σ1≥σ2>0 em compressão (mínimo 1e−8 MPa, conforme corte não zero histórico), azimute em [0,180], C0/Pf/μ finitos e não negativos. Não ordenar tensões nem trocar sinais silenciosamente. μ=0 é permitido para Ts/Td/CSF, mas Sf é indefinido e exige μ>0. Tensões iguais permitem Ts/Sf/CSF; Td é indefinido e só essa seleção é recusada. A validação ocorre antes de exportar e identifica o campo.

Strikes do mapa usam a mesma correção, round e flips de strike_indices, inclusive a representação de zero como 180. Polo relativo iAlpha=strike+90−azimute. sn=abs((σ1+σ2)/2+(σ1−σ2)/2×cosd(2iAlpha)); |tau|=abs(−(σ1−σ2)/2×sind(2iAlpha)). Ts=|tau|/sn; Td=(σ1−sn)/(σ1−σ2); Sf=sn−Pf−(|tau|−C0)/μ, em MPa. Não modificar Dataset.

Ts normaliza pelo máximo dos **segmentos corrigidos**. Sf usa seu mínimo/máximo, sem o arredondamento binário do fonte. Rosa usa o mesmo normalizador/faixa do mapa. Cada pétala avalia a orientação central de seu bin; índices saturam nos limites da paleta quando o centro ultrapassa a faixa observada. Valores físicos e razões não saturadas permanecem nos resultados; saturação só afeta cor. Nenhuma otimização ou normalização por máximo teórico foi introduzida.

Normalizador Ts zero ou faixa Sf constante gera normalização zero, sem adicionar epsilon às grandezas. Campo Sf constante usa barra de uma única cor e um único tick com o valor real; o intervalo de exibição é apenas um recurso gráfico. CSF usa **|tau|≥μ×(sn−Pf)+C0** no mapa e nos centros de bins. Não há tolerância numérica na igualdade nem classe intermediária de borda.

A outra parcela de Q-17, cores por comprimento, **preserva a convenção legada aceita** da Sprint 3: índice linear e barra logarítmica. Esta decisão não altera os mapas já existentes ou a paleta haline. A divergência de significado da legenda permanece explicitada, sem afirmar que a correspondência é logarítmica.

## Rosas, cores e Mohr

Rosas têm bins fixos de 10°, dados duplicados pelo mesmo double_angles/reverseAxis da família Angles, frequência não ponderada e raio 50×sqrt(percentual). Reutilizam o contrato de bordas/fechamento e a proteção do limite de 50% já implementados. Q-10 é preservada: valores fora de [0,360] são diagnosticados/excluídos dos bins, sem nova normalização angular silenciosa. Linha vermelha de σ1, círculos percentuais e textos em inglês. O bin escolhido na aba Angles não afeta essas rosas.

jet(100) nos mapas e jet(19) nas rosas, invertida para Sf; CSF usa os índices baixos/altos históricos. Tabelas RGB obtidas da execução MATLAB, com [procedência](../../pyfracpaq/resources/jet_rgb.json), sem presumir equivalência da paleta de mesmo nome no Matplotlib. Barras inferiores passam exclusivamente por colourbar compartilhada: comprimento igual ao quadrado efetivo, folga fixa de 25 pontos dos rótulos e reserva de espaço ao reduzir a janela. Ticks unitários em décimos na impressão, com redução de quantidade em janelas pequenas. As folgas solicitadas pelo usuário têm precedência sobre o pad relativo original.

Mohr usa 361 posições da referência e os círculos total/efetivo (este só é desenhado se Pf>0), reta (0,C0)→(σ1,μσ1+C0), aspecto igual, grid/box e limites originais x=[0,1.1σ1], y=[0,.5σ1]. Assim parte negativa da tensão efetiva continua fora da vista. O fonte recebe sn/tau, mas não desenha esses pontos; o port também não acrescenta pontos. Legenda muda de canto conforme Pf.

## Integração e arquivos

Uma configuração/resultado de estabilidade em cache por Run; cada seleção produz seu mapa/rosa e a primeira produz um único Mohr. SVG de várias cores também aciona uma única figura multicolorida, como o despacho de tracemap. A ausência de áreas bidimensionais não impede a avaliação de tensões, que independe de área.

Somente Slip tendency grava FracPaQ2Dsegmentdata_{tag}.txt: sequencial, X1/Y1/X2/Y2 e ângulo **bruto**, em ordem original, sem cabeçalho, `%4i`, quatro casas nos pontos e uma no ângulo. Não incluir sn/tau ou transformar o TXT em strikes corrigidos. Escrita temporária própria/substituição atômica, tag vazia e outros arquivos preservados. Rosas de estabilidade não geram EZROSE por si; o gatilho angular/crack continua separado.

[Validação](../../tests/reference/sprint11/validation.json): quarenta PNGs/QA, quatro segmentdata, arrays completos e parâmetros, cobrindo TXT/SVG/Hough, caso da captura e Sf constante. Testes cobrem fórmulas nativas válidas, correções aprovadas, igualdade e nextafter, parâmetros contextuais, cores exatas, todos os nomes, redimensionamento e Run. Capturas/layouts MATLAB são genuínos; diferenças científicas deliberadas e a folga de barras modificada não são mascaradas em uma alegação de paridade SSIM. Homologação visual integral permanece pendente da auditoria final.
