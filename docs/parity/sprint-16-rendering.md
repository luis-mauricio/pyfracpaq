# Continuação da auditoria gráfica S16-04

Esta rodada usa os resultados nativos preservados de SD11A e candidatos novos em `tests/reference/sprint16/final`. **A tarefa permanece em validação; este documento não é um aceite de paridade.** As métricas anteriores em `sprint16/sd11a` continuam intactas.

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

### Pendências objetivas desta rodada

Os sete casos estão reunidos na [revisão visual para o usuário](../../tests/reference/sprint16/final/user-review/LEIA-ME.md), com [comparador HTML](../../tests/reference/sprint16/final/user-review/index.html), zoom 1:1, alternância e links aos PNGs completos. A faixa P20 contém também parte do tick `0,08` do eixo Y; os recortes centrais distinguem esse elemento do título, sem alterar as notas originais.

| Figura/região comparável | SSIM RGB | Limite |
| --- | --- | --- |
| Dilation tendency: título | 0,979338 | 0,98 |
| Fracture susceptibility: título | 0,979891 | 0,98 |
| CSF: título | 0,976113 | 0,98 |
| Graphs P21: título | 0,972508 | 0,98 |
| Graphs P20: título | 0,972114 | 0,98 |
| Hough: painel lateral rho | 0,955917 | 0,98 |
| Hough: painel lateral theta | 0,937944 | 0,98 |

As notas são originais, sem mascarar textos ou deslocar imagens. Hough passa na imagem de entrada e na vista superior; suas duas vistas laterais ainda não passam. As regiões científicas dispensadas por diferenças já autorizadas não são classificadas como aprovações. Ainda é necessária a revisão semântica final e a partição de legendas/anotações onde hoje estão incluídas em painéis maiores. **S16-04 e S16-09 continuam sem X.** Windows/Linux permanecem adiados pelo usuário; os 164 fontes e os oito resultados preexistentes foram conferidos por hash e preservados.
