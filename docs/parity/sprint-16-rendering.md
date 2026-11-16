# Continuação da auditoria gráfica S16-04

Esta rodada usa os resultados nativos preservados de SD11A e candidatos novos em `tests/reference/sprint16/final`. **S16-04 concluída em 16/11/2026, após aprovação explícita dos casos 1–16. Os 11 critérios passaram, sem regiões pendentes. A última suíte completa teve 726 testes aprovados; S16-09 tem os pontos 1–3 concluídos (interface, exportações e documentação); faltam pacotes e disponibilização nos pontos 4–5, conforme o [estado da entrega](sprint-16-delivery.md).** As métricas anteriores em `sprint16/sd11a` continuam intactas. Este estado não declara identidade geral entre os programas.

## Contrato de comparação

Os dados científicos são conferidos antes dos pixels. As regiões são definidas a partir dos quadros e painéis nativos, congeladas em `regions-native.json`, cobrem o canvas inteiro e não se sobrepõem. O comparador usa RGB original, SSIM 0,98, sem máscaras, alinhamentos posteriores ou redimensionamentos. Miniaturas têm apenas finalidade de inspeção. Cada exceção mantém sua nota bruta e não recebe um falso resultado de aprovação.

As alterações Q11/Q14/Q15/Q20 e o contrato de centros S01-04 continuam explícitos. A escala P20 dos Graphs muda com Q20; seu eixo dependente dos valores também não é uma comparação de pixels equivalentes. A rasterização produtiva de Wavelets permanece a autorizada em Q12. O núcleo CWT é conferido adicionalmente sobre os mesmos pixels nativos, com evidência separada da execução produtiva. Barras de cores mantêm a geometria responsiva e a distância física de 25 pontos exigidas pelo usuário; essa alteração autorizada não é disfarçada de coincidência com o layout antigo.

## Correções e evidências acrescentadas

- Ticks decimais, limites automáticos, sinais negativos, fontes, layout TeX, margens, legendas e caixas de parâmetros foram confrontados com cenas gráficas nativas independentes.
- Marcadores e linhas usam composição de oito amostras, preservando a ordem e evitando escurecimento de pontos opacos repetidos. Os recursos de marcadores e pontilhados vêm de primitivas sem dados de fraturas; não são recortes dos goldens científicos.
- Os histogramas de Wavelets foram corrigidos: `hist(values, 20)` divide a amplitude em 20 intervalos e usa centros internos. Entradas constantes seguem a convenção nativa. Os quatro contextos Morlet/Mexican Hat, escalas 16/32, L=2/4 e passo 30 graus, conferem coeficientes, seleção, ângulos e histogramas; a contagem produtiva de ângulos continua diferente conforme Q12.
- As imagens nativas usam ticks externos. A camada dos eixos fica abaixo dos dados, reproduzindo `Layer=bottom`. Isso conserva paletas, normalizações, amostras e limites científicos.
- Hough mantém superfícies 3D interativas, mas resolve as câmeras ortográficas originais com teste de profundidade por amostra. As propriedades medidas de uma malha independente são fator de deslocamento de faces 1,5 e viés 0,0001. A triangulação por faixas e as cores planas são mantidas. Arrays Hough seguem os oráculos numéricos nativos.

## Reprodução

Usar a venv e `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib PYTHONPATH=.:scripts`:

1. `scripts/finish_s16.py compute`, seguido de `render`.
2. `scripts/finish_s16_contexts.py` e `scripts/finish_s16_extras.py`.
3. `scripts/audit_s16_figures.py freeze` e `compare`.
4. `scripts/finish_s16.py preview` para inspeção, sem usar miniaturas nas métricas.
5. `scripts/run_isolated_tests.py --report tests/reference/sprint16/final/checks.json` para a suíte completa, em cópia com exatamente os 164 originais.

`--render-only` dos contextos usa somente um cache local verificado por SHA-256 e pelos hashes dos módulos científicos; a execução sem essa opção refaz os cálculos. MATLAB e toolboxes são necessários apenas para recapturar os controles e as referências. Os scripts `capture_s16_*`, `inspect_s16_primitives.m`, `freeze_native_markers.py`, `freeze_native_grids.py` e `calibrate_s16_text.py` registram a procedência. Nenhum código proprietário de toolbox ou fonte MathWorks integra o runtime Python.

## Validação em andamento

A suíte completa final desta rodada passou com **709 testes em 268,91 segundos**, em cópia isolada dos 164 originais. Outros **cinco testes novos de contratos do renderizador** passaram separadamente: profundidade de linhas/faces, preservação de coordenadas, TeX, restauração após falha e rotação das superfícies Hough. [Suíte completa](../../tests/reference/sprint16/final/checks.json) e [contratos do renderizador](../../tests/reference/sprint16/final/renderer-contracts.xml).

Os 81 confrontos numéricos foram repetidos: 74 coincidem e sete mantêm as diferenças documentadas da rodada inicial; os quatro TXT seguem idênticos byte a byte. Os quatro contextos CWT adicionais passam em coeficientes, seleção, ângulos, centros e contagens de histogramas, além das quatro regiões de painel comparáveis. O controle SVG passa nas coordenadas, cores, comprimentos e ângulos por traço e nas regiões gráficas definidas.

### Revisão visual e aceite parcial

Em **16/11/2026**, o usuário comparou os cinco títulos e aprovou sua aparência atual: “Comparei os títulos e aceito do jeito que está. A diferença é mínima. Para mim está satisfatório.” Após avaliar os detalhes das duas vistas laterais Hough e receber a explicação do impacto exclusivamente visual nos casos verificados, também aprovou essas diferenças: “Então eu aceito essa diferença.” O [registro do aceite](../../tests/reference/sprint16/final/user-visual-acceptance.json) preserva as duas decisões e identifica as sete regiões e os hashes das imagens revisadas. As notas SSIM originais permanecem inalteradas; o aceite visual fica separado do resultado automático e não autoriza divergência numérica.

Os sete casos estão reunidos na [revisão visual para o usuário](../../tests/reference/sprint16/final/user-review/LEIA-ME.md), com [comparador HTML](../../tests/reference/sprint16/final/user-review/index.html), zoom 1:1, alternância e links aos PNGs completos. A faixa P20 contém também parte do tick `0,08` do eixo Y; os recortes centrais distinguem esse elemento do título, sem alterar as notas originais.

| Figura/região comparável | SSIM RGB | Limite | Revisão do usuário |
| --- | --- | --- | --- |
| Dilation tendency: título | 0,979338 | 0,98 | Aceito em 16/11/2026 |
| Fracture susceptibility: título | 0,979891 | 0,98 | Aceito em 16/11/2026 |
| CSF: título | 0,976113 | 0,98 | Aceito em 16/11/2026 |
| Graphs P21: título | 0,972508 | 0,98 | Aceito em 16/11/2026 |
| Graphs P20: título | 0,972114 | 0,98 | Aceito em 16/11/2026 |
| Hough: painel lateral rho | 0,955917 | 0,98 | Aceito em 16/11/2026 |
| Hough: painel lateral theta | 0,937944 | 0,98 | Aceito em 16/11/2026 |

As notas são originais, sem mascarar textos ou deslocar imagens. Hough passa no limite automático na imagem de entrada e na vista superior; suas duas vistas laterais ficam abaixo de 0,98 e foram aceitas visualmente pelo usuário. **Não há pendência de aceite entre os sete casos revisados anteriormente.** As regiões científicas dispensadas por diferenças já autorizadas não são classificadas como aprovações automáticas.

### Conclusão das três etapas técnicas — 16/11/2026

1. **Revisão semântica concluída:** as 51 figuras SD11A têm 403 verificações de títulos, eixos, unidades, limites, paletas, legendas e anotações: 368 coincidem e 35 registram diferenças técnicas ou científicas explicadas. Não resta erro semântico identificado. Os seis controles pareados adicionais (quatro CWT sobre pixels nativos, Hough e SVG) e quatro saídas produtivas CWT sob Q12 também foram inspecionados. O [registro de revisão](../../tests/reference/sprint16/final/semantic-review.json) vincula 118 imagens por hash e distingue revisão técnica de aceite visual do usuário; os [confrontos semânticos](../../tests/reference/sprint16/final/semantic-comparison.json) preservam valores e referências nativas.
2. **Legendas e anotações conferidas separadamente:** dez legendas e seis caixas MLE foram medidas em retângulos encontrados exclusivamente nas imagens MATLAB. São verificações suplementares que se sobrepõem aos painéis originais; a partição principal continua completa e sem sobreposição. Nenhum pixel foi removido, mascarado, deslocado ou redimensionado nas métricas. As 16 regiões ficam abaixo de SSIM 0,98 (0,653303 a 0,908318) e foram apresentadas para decisão na [galeria de detalhes](../../tests/reference/sprint16/final/detail-review/index.html), com [notas originais](../../tests/reference/sprint16/final/detail-region-comparison.json). Não houve nova rodada de calibração gráfica.
3. **Consolidação executada:** o [estado final](../../tests/reference/sprint16/final/status.json), a [auditoria por família](../../tests/reference/sprint16/family-audit.json), a matriz e o PRD distinguem evidência concluída de aceite pendente. O script de estado calcula 11 critérios de encerramento; dez estão satisfeitos. O único critério pendente é o aceite/correção dos 16 detalhes apresentados. Um aceite dos títulos anteriores não aprova automaticamente legendas novas; imagens diferentes invalidam o aceite por hash.

As pequenas diferenças nas caixas/legendas envolvem fonte, espaçamento, símbolos e molduras. No caso 12, μ/σ do ajuste lognormal de segmentos também mudam de 3,8925/0,55553 para 3,9241/0,51722 por **Q15 já aprovada**; a galeria não pede nova autorização científica. No caso 16, os pequenos traços da legenda Graphs mudam de cor; os quadrados continuam identificando corretamente Point 1/2 em ciano/verde. Esse detalhe foi explicitamente apresentado ao usuário.

A revisão confirmou a faixa Sf de Q17 (mínimo 26,4087343145 versus 26,4156081756 MPa), a diagonal corrigida de Q08/S01 (ceil 2819 versus 2818), as populações Q11/Q14 e as escalas Q20. A diferença mínima de limites ocultos das rosas deriva do último ponto de `-r:0.0005:r` versus o raio exato; frequências e ângulos não mudam, e as regiões RGB comparáveis passam. A notação polar `0,5×10⁻¹²` versus `5×10⁻¹³` representa o mesmo número. O comparador passou a distinguir histograma/CCDF de blocos pelo eixo Y e a resolver empates de RGB nas extremidades da paleta cíclica, mantendo a mesma tolerância. Não foi encontrado erro correspondente no programa.

**Validação adicional:** cinco testes do próprio auditor passaram em execução separada, cobrindo paleta cíclica/inversão, identificação correta dos contextos nativos e rejeição de aceite com hash, região ou recorte diferentes: [resultado](../../tests/reference/sprint16/final/audit-contracts.xml). A suíte completa de 709 e os cinco contratos do renderizador citados acima continuam sendo execuções distintas. Nenhum módulo produtivo ou PNG foi alterado nesta revisão final.

### Decisão parcial sobre os detalhes — 16/11/2026

O usuário aprovou explicitamente os casos **2, 4, 6, 8, 10, 12, 13 e 15**: seis caixas MLE, legenda Mohr e legenda de crack tensors. O aceite foi vinculado aos hashes atuais e aos retângulos medidos, preservando as notas SSIM. Continuam em discussão **1, 3, 5, 7, 9, 11, 14 e 16**: quadrados com cantos recortados nas legendas MLE/Graphs e círculos deformados em I-Y-X. Os marcadores são declarados como quadrados/círculos; a camada personalizada de rasterização e o contorno mínimo da legenda introduzem essa aparência. Não existe requisito científico para os recortes. O usuário considerou mais coerentes as cores correspondentes entre linhas/quadrados do caso 16; a forma desse marcador continua em discussão. Nenhum marcador ou PNG foi alterado nesta etapa de discussão.

**S16-04 continua sem X pelas oito legendas em discussão. S16-09 permanece aberta para revisão de telas/exportações e publicação.** Windows/Linux permanecem adiados pelo usuário; os 164 fontes e os oito resultados preexistentes foram conferidos por hash e preservados.


### Marcadores geométricos normais — 16/11/2026

Por instrução explícita: “Substitua essa renderização dos marcadores por formas geométricas normais.” Os quadrados/círculos agora usam os caminhos padrão do Matplotlib em todos os DPI, tanto nos gráficos/legendas como nos nós dos mapas. Foram removidos a interceptação do renderizador, os glyphs do atlas, o fallback poligonal e o passe combinado de linhas/marcadores. As linhas mantêm seu renderizador; os marcadores dos mapas usam PathCollection normal. A legenda preserva a espessura definida pelo marcador, sem engrossamento mínimo. O fator de tamanho já estabelecido para os quadrados foi mantido. As cores Point 1/2 continuam correspondentes entre linhas e quadrados. O atlas antigo fica apenas como evidência histórica e não é consultado pelo runtime.

A [galeria de antes/depois](../../tests/reference/sprint16/final/marker-review/index.html) mostra os oito casos e o mapa de nós. Foram renderizadas novamente as 51 figuras SD11A: 26 PNGs mudaram e 25 continuam idênticos byte a byte. Os dados vêm do mesmo cache científico verificado; nenhum módulo de analysis/domain/geometry/io mudou. A revisão semântica foi repetida sem issues. Os originais nativos, valores, tamanhos nominais, cores e barras responsivas foram preservados.

**726 testes passaram em 225,25 segundos**, em cópia isolada com os 164 originais: [suíte atual](../../tests/reference/sprint16/final/geometric-markers-checks.json). Os hashes dos módulos e recursos foram confrontados com a cópia efetivamente testada. As comparações com os paths padrão cobrem quadrados/círculos, preenchidos/vazios, em 100/200/600 dpi. Os testes antigos que exigiam pixels do atlas foram substituídos por esse contrato geométrico, autorizado pelo usuário; não se exige simultaneamente reproduzir os recortes antigos.

Os oito detalhes aprovados mantêm os mesmos pixels nos seus retângulos completos. Seus aceites foram preservados por SHA256 regional, mesmo quando o PNG inteiro mudou por marcadores em outras partes. As notas SSIM continuam brutas. Há 13 aceites válidos para as imagens atuais; as 15 aprovações históricas permanecem registradas. Dois retângulos amplos de títulos Graphs também contêm pontos e, portanto, mudaram de hash: o texto/estilo dos títulos não mudou, mas o aceite estrito da imagem anterior não é transferido automaticamente. O plot do mapa de nós passou a SSIM 0,94066 com marcadores padrão; essa diferença esperada foi acrescentada à galeria, sem mascarar pixels nem flexibilizar 0,98.

O estado atual registra **11 regiões para revisão da aparência**: oito legendas alteradas, o plot do mapa de nós e os dois retângulos de títulos Graphs que contêm marcadores. Isso não representa erro numérico identificado. A autorização para implementar formas normais é registrada separadamente do aceite visual final das novas imagens; S16-04/S16-09 permanecem sem X. [Registro da alteração](../../tests/reference/sprint16/final/marker-change.json).


### Encerramento — aprovação dos casos 1 a 16

Em 16/11/2026, o usuário declarou: **“Aprovo todos de 1 a 16.”** O [registro de aceite](../../tests/reference/sprint16/final/user-visual-acceptance.json) identifica os 16 detalhes na versão geométrica atual, por hashes de imagem e coordenadas. O histórico dos aceites anteriores é preservado; as notas SSIM e seus resultados automáticos não foram alterados.

A alteração dos marcadores já havia sido autorizada globalmente. A [verificação de propagação](../../tests/reference/sprint16/final/marker-propagation-proof.json) compara os PNGs atuais aos anteriores, conferidos contra seus hashes: no plot do mapa, 893250 pixels mudaram; nos dois recortes amplos dos títulos Graphs, 930/939 pixels. **Zero pixels mudaram fora dos limites dos marcadores efetivamente posicionados pelos artistas.** O mapa satisfazia o limite anterior; os títulos já tinham aceite. Os textos dos títulos não mudaram. Essa prova resolve consequências mecânicas do estilo aprovado, sem atribuir ao usuário uma aprovação explícita de três novas imagens. A atribuição diferencial não é uma máscara SSIM: as regiões completas e as notas brutas permanecem inalteradas.

O [estado final](../../tests/reference/sprint16/final/status.json) registra **21 regiões com aceite visual direto válido, três consequências técnicas de marcadores verificadas e zero regiões pendentes**. Todos os **11 critérios de encerramento** estão satisfeitos. A última suíte completa permanece em **726 testes aprovados**; sete testes do auditor passaram separadamente, incluindo rejeição de propagação sem autorização/aceite de estilo, hashes atuais, população de casos completa ou prova de ausência de diferenças externas. [Contratos do aceite](../../tests/reference/sprint16/final/acceptance-contracts.xml).

**S16-04 marcada com X no PRD. S16-09 continua aberta**, incluindo a revisão final de telas/exportações e a publicação. Não se declara identidade universal de pixels nem certificação Windows/Linux. As seções anteriores preservam a evolução histórica da auditoria.
