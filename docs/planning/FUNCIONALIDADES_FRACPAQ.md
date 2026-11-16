# FracPaQ MATLAB — inventário funcional e base para sprints

**Data da análise:** 13/11/2026. **Escopo:** todos os **164 arquivos** presentes em `fracpaq-matlab`, incluindo subpastas. **Referência principal:** FracPaQ 2.8 / 2.8.0, março de 2021.

Este documento descreve o programa MATLAB fornecido. Os itens identificados podem virar histórias ou tarefas de implementação futura; sua presença aqui **não significa que já estejam implementados no PyFracPaQ**. As sprints ao final são uma proposta de organização, sem estimativa de esforço ou compromisso de prazo.

**Guia de leitura:** seções 3–4 cobrem a interface e as entradas; 5–10 detalham as seis abas; 11 reúne correções; 12 cataloga exportações; 13 registra recursos auxiliares; 14 organiza sprints; 15 permite conferir cada arquivo analisado.

## 1. Cobertura, evidências e interpretação

A análise combinou leitura do código e de suas chamadas, extração das propriedades dos dois arquivos `.fig` (rótulos, grupos, opções, valores iniciais e estados), leitura do manual PDF de 39 páginas, inspeção estrutural de todos os exemplos TXT/SVG e identificação dos arquivos de imagem, documentação e site. O apêndice lista cada arquivo individualmente e sua função.

| Categoria | Arquivos | Tratamento |
| --- | ---: | --- |
| Código MATLAB `.m` | 82 | Interface, callbacks, algoritmos, utilitários, bibliotecas e experimentos |
| Dados `.txt` | 41 | Leitura integral e identificação da estrutura numérica e dos delimitadores |
| Desenhos `.svg` | 14 | Estrutura XML, elementos geométricos, camadas/grupos e recursos incorporados |
| Imagens JPG/JPEG/TIF/TIFF/PNG | 15 | Formato, dimensões, canais e papel no programa/site |
| Interfaces `.fig` | 2 | Estrutura de objetos MATLAB e propriedades dos controles |
| Manual `.pdf` | 1 | Conteúdo completo; conferência visual da página da interface |
| Site: HTML, CSS, JS e JSON | 7 | Conteúdo, apresentação e eventual comportamento |
| README e LICENSE | 2 | Versão, alterações, autoria e condições de redistribuição |
| **Total** | **164** | **Nenhum arquivo da pasta ficou fora do inventário** |

**Limite da verificação:** análise estática; MATLAB e Octave não estavam disponíveis neste ambiente. Não foram executados os cálculos científicos nem a interface original. Os critérios de aceite abaixo são propostas para as futuras sprints, e não testes já realizados. Falhas apontadas na seção 11 são evidências do código ou riscos a reproduzir, com essa diferença indicada.

**Estados usados:** **I** = conectado à interface principal 2.8; **A** = auxiliar utilizável por código/linha de comando; **E** = legado, demonstração ou experimento fora do fluxo principal; **P** = melhoria proposta a partir de uma lacuna. Um recurso I pode ter limitações registradas em `Q-*`.

Fontes principais: [interface e execução](../../fracpaq-matlab/guiFracPaQ2D.m), [layout da interface](../../fracpaq-matlab/guiFracPaQ2D.fig), [README](../../fracpaq-matlab/README.md), [manual 2.8](<../../fracpaq-matlab/FracPaQ User Guide v2.8.pdf>). Quando manual e código divergem, o comportamento encontrado no código é explicitado.

## 2. Modelo de dados e fluxo de uso

| Conceito | Significado no programa |
| --- | --- |
| Nó geométrico | Par `(x, y)` que delimita um segmento; não equivale automaticamente a um nó topológico I, Y ou X |
| Segmento | Linha reta entre dois nós consecutivos; possui comprimento, ângulo e, na entrada por nós, ponto médio |
| Traço / trace | Fratura representada por uma polilinha; comprimento total = soma dos comprimentos dos segmentos |
| Centro do traço | Posição na metade do comprimento percorrido ao longo da polilinha; não é necessariamente o centro de sua caixa envolvente |
| Orientação / strike | Ângulo axial de um segmento, medido em relação ao eixo Y; para várias saídas é duplicado em direções opostas no intervalo de 360° |
| Escala | Pixels por metro; coordenadas/comprimentos são divididos pelo fator quando ele é positivo |
| Área do mapa | Caixa envolvente dos nós em várias rotinas; não há ferramenta geral de delimitação de um polígono de amostragem |
| P21 | Intensidade: dimensão de comprimento por área, ou `L⁻¹` |
| P20 | Densidade: contagem por área, ou `L⁻²`; as rotinas deste pacote trabalham com segmentos |

Fluxo principal: **selecionar/digitar arquivo → escolher/conferir tipo e escala → Preview → conferir mapa e estatísticas → ajustar Flip X/Flip Y e parâmetros → marcar saídas nas seis abas → definir tag → Run → consultar figuras, arquivos e Command Window → Exit**.

As seleções das diferentes abas permanecem nos controles: `Run` executa as opções marcadas em todas elas, e não apenas na aba visível. Wavelets é processada depois das demais análises.

Fontes: `guiFracPaQ2D.m:780–1422`, `guiFracPaQ2Dlist.m:36–237`, `guiFracPaQ2Dimage.m:29–270`.

## 3. Épico UI — janela, controles gerais e estatísticas

**Estado padrão: I. Dependência:** carregamento dos dados para liberar as análises.

| ID | Funcionalidade | Comportamento encontrado / escopo | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| UI-01 | Janela principal única | Interface GUIDE do tipo singleton; entrada à esquerda, mapa de prévia ao centro e opções à direita | Abrir o programa e apresentar as três áreas sem duplicar a janela principal |
| UI-02 | Identidade e versão | Título “Fracture Pattern Quantification”, ícone, logotipo, versão 2.8, março de 2021 e contato por e-mail | Exibir identificação e versão da aplicação |
| UI-03 | Campo Filename | Permite digitar o nome; callback usa a pasta de trabalho como caminho | Digitar uma entrada válida e habilitar sua prévia; tratar caminhos conforme Q-04 |
| UI-04 | Botão Browse... | Abre seletor filtrado para TXT, SVG, JPEG/JPG e TIFF/TIF | Selecionar cada formato admitido e refletir a escolha no campo |
| UI-05 | Tipo de entrada | Radio buttons “Image file” e “Node file”; seleção automática pela extensão e alteração manual | Alternar tipo e habilitar apenas os parâmetros pertinentes |
| UI-06 | Botão Preview | Lê/converte entrada, constrói `traces`, desenha mapa e coleta estatísticas; pode gerar arquivos e a figura de Hough | Prévia e estatísticas corresponderem à entrada; falha não liberar uma execução inválida |
| UI-07 | Área de mapa | Traços em eixos X/Y, proporção geométrica igual, limites e unidades | Preservar proporção e apresentar pixels ou metros corretamente |
| UI-08 | Painel “Statistics for selected file” | Exibe X mínimo, Y mínimo, X máximo, Y máximo e quantidades de traços, segmentos e nós | Conferir os sete valores em um conjunto pequeno conhecido |
| UI-09 | Flip X-axis / Flip Y-axis | Inverte a direção de visualização de cada eixo; flags são repassadas às rotinas de saída | Inversões independentes e repetíveis; validar efeitos nos ângulos e nas saídas |
| UI-10 | Navegação entre seis abas | Maps, Lengths, Angles, Fluid flow, Wavelets e Graphs, implementadas por botões e painéis sobrepostos | Mostrar um painel por vez e preservar escolhas dos demais |
| UI-11 | Habilitação progressiva | Run, abas e flips começam desabilitados; Preview válido os habilita e abre Maps | Impedir Run antes de uma prévia válida |
| UI-12 | Botão Run | Valida parâmetros e dispara o conjunto selecionado de análises | Gerar as saídas marcadas, inclusive quando a aba correspondente não estiver visível |
| UI-13 | Botão Exit | Chama `close all` e `close(gcf)`; o alcance original inclui outras figuras MATLAB | Encerrar a aplicação; decidir conscientemente o alcance de fechamento na migração |
| UI-14 | Mensagens de estado | Ready, instrução para Preview, leitura de nós, Hough, coleta de dados, Running e conclusão | Informar etapa corrente e término ou erro |
| UI-15 | Progresso e mensagens de erro | `waitbar`, `errordlg`, `msgbox`, foco no campo inválido e avisos de compatibilidade | Mostrar progresso nas operações longas e erro compreensível nas entradas inválidas |
| UI-16 | Filename tag for this run | Texto inicial `Run1`; convertido em sufixo `_Run1` para várias saídas | Identificar arquivos de execuções distintas, com exceções tratadas em EXP-03 |
| UI-17 | Figuras independentes | Mapas e gráficos abrem em janelas MATLAB próprias; rótulos, legendas, títulos, escalas e barras de cores variam por análise | Cada resultado identificável e exportável sem depender da prévia |
| UI-18 | Diagnóstico no Command Window | Versão, parâmetros de Hough, estatísticas, conectividade, MLE, permeabilidade e andamento wavelet | Disponibilizar essas informações em console ou painel de resultados |
| UI-19 | Dependências entre controles | Checkboxes habilitam opções subordinadas: nós, círculos, bins, MLE, tensões, abertura e wavelet | Reproduzir as dependências de cada grupo sem exigir campos irrelevantes; ver Q-01 |

Fontes: `guiFracPaQ2D.fig`; `guiFracPaQ2D.m:71–353`, `567–777`, `780–1422`, `1527–1548`, `1721–1783`, `1836–1910`, `2050–2136`, `2221–2343`.

## 4. Épico IN — entrada, geometria, cores e Hough

**Estado padrão: I. Dependência:** base geométrica para todos os épicos analíticos.

| ID | Funcionalidade | Comportamento encontrado / escopo | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| IN-01 | Importação TXT de nós | Pares X/Y separados por tabulação; um traço por linha; pelo menos dois nós; linhas podem ter quantidades diferentes de pares | Importar polilinhas de dois e vários nós e preservar sua separação |
| IN-02 | Construção geométrica | Monta nós, segmentos, comprimentos, ângulos, distâncias acumuladas e posição central do traço | Conferir uma linha e uma polilinha com resultados calculáveis manualmente |
| IN-03 | Tratamento de pontos repetidos | Há tentativa de ignorar segmentos de comprimento zero entre nós consecutivos iguais | Não produzir segmento degenerado nem desalinhamento entre índices; ver Q-07 |
| IN-04 | Escala pixels/metre | Vazio mantém coordenadas originais e rótulos em pixels; positivo divide coordenadas e comprimentos e muda unidades | Mesma geometria importada com e sem escala apresentar a razão esperada |
| IN-05 | Importação SVG | Preview chama `convertSVG2txt_colour2`, gera TXT e depois usa a leitura de nós | Converter exemplos compatíveis e manter quantidade e geometria dos traços |
| IN-06 | Elementos SVG admitidos | Trata linhas, polilinhas e caminhos simples com coordenadas; há reconhecimento por prefixo `<poly`, que também alcança `polygon` | Definir e testar explicitamente o subconjunto aceito; não anunciar suporte SVG geral |
| IN-07 | Caminhos SVG simples | Parser procura `M` e remove `L`; rejeita comandos como A/C/H/Q/V/S/T/Z com mensagem no console | Importar caminho reto compatível; informar claramente comandos sem suporte |
| IN-08 | Separação por cor no SVG | Lê códigos de stroke hexadecimais; reconhece `stroke="#..."` e, em parte do parser, `stroke:#...`; grava arquivos por cor | Preservar grupos por cor e tratar as variações de sintaxe; ver Q-09 |
| IN-09 | Conversão de uma ou várias cores | Uma cor gera `nome_converted.txt`; várias geram `nome_colourHHHHHH_converted.txt` | Gerar os arquivos esperados junto ao SVG e carregá-los corretamente |
| IN-10 | Prévia multicolorida | Agrega os traços dos arquivos por cor, calcula limites/conteagens globais e desenha cores originais | Exibir conjuntos sobrepostos com as cores e estatísticas globais corretas |
| IN-11 | Análise de conjunto individual | É possível carregar manualmente um TXT `colourHHHHHH` e usar sua cor em saídas compatíveis | Executar separadamente um conjunto extraído do SVG; não confundir com processamento automático por grupo |
| IN-12 | Importação de imagem | Seletor aceita JPG/JPEG/TIF/TIFF; Preview exige `BitDepth=8` e `ColorType=grayscale` | Aceitar imagem compatível e rejeitar RGB/profundidade inadequada com motivo |
| IN-13 | Preparação interna para Hough | Lê imagem, inverte intensidades (`imcomplement`) e limpa pixels isolados (`bwmorph(...,'clean')`) | Conferir a imagem efetivamente usada para detecção |
| IN-14 | Transformada de Hough | `hough` com resolução de rho de 1 pixel e theta de 0,5°; `houghpeaks` e `houghlines` extraem linhas | Uma imagem sintética de linhas fornecer detecção controlável pelos parâmetros |
| IN-15 | Parâmetros Hough ajustáveis | Número de picos, limiar relativo, distância para unir lacunas e comprimento mínimo a manter | Cada parâmetro afetar o estágio correspondente e permitir nova prévia |
| IN-16 | Traços extraídos da imagem | Cada linha detectada torna-se um traço de um segmento e dois nós; não reconstrói automaticamente uma polilinha sinuosa | Preservar a distinção entre esse modelo e o TXT/SVG com vários segmentos |
| IN-17 | Diagnóstico Hough | Figura com imagem original e três vistas do acumulador, incluindo o plano de limiar; exportação automática | Permitir avaliar picos e limiar antes da análise final |
| IN-18 | Validação e informação da imagem | Erro de formato mostra aviso e imprime metadados de `imfinfo` no console | Usuário conseguir identificar profundidade e tipo de cor incompatíveis |

Fontes: [leitor de nós](../../fracpaq-matlab/guiFracPaQ2Dlist.m), [leitor de imagem/Hough](../../fracpaq-matlab/guiFracPaQ2Dimage.m), [conversor SVG atual](../../fracpaq-matlab/convertSVG2txt_colour2.m), `guiFracPaQ2D.m:780–1035`. A geração de midpoint de segmentos e cores tem diferenças entre os leitores; ver Q-06.

### 4.1 Valores iniciais e validação encontrados

Os valores iniciais vêm do `.fig` e dos ajustes em `OpeningFcn`. “Validação” abaixo descreve o código, inclusive suas lacunas; a migração deve considerar Q-01 e Q-02.

| Parâmetro | Inicial | Validação / interpretação no código |
| --- | --- | --- |
| Tipo de entrada | Node file | Detecção automática pela extensão |
| Scaling | Vazio | Vazio ou número positivo; conversão realizada no Preview |
| Number of Hough peaks | 1000 | Entre 100 e 5000; mensagem pede inteiro, mas não testa integralidade |
| Hough threshold | 0.33 | `0 < valor ≤ 1`; corte `ceil(valor × max(H))` |
| Merge gaps less than | 5 pixels | Testa `> 1`; mensagem menciona tamanho máximo, mas não o verifica |
| Discard lengths less than | 3 pixels | Testa `> 1`; mesma divergência sobre tamanho máximo |
| Traces, segments / Segments, by strike | Marcados | Demais mapas inicialmente desmarcados |
| Número de círculos em Maps | 12 | Testa `≥ 2`; arredonda ao usar; número ao longo do lado menor |
| Sigma 1 / Sigma 2 | 100 / 50 MPa | Números não nulos, com tolerância `1e-8`; não impõe ordenação nem diferença entre eles |
| Ângulo de Sigma 1 | 0° | Entre 0° e 180° |
| Coesão C0 / pressão de poros Pf | 0 / 0 MPa | Números `≥ 0` |
| Coeficiente de atrito mu | 0.6 | Número `≥ 0`, embora haja divisões por mu |
| Histogram of lengths | Marcado | Bins disponíveis 10, 20, 30 e 50; inicial em execução: 20 |
| Log-log / MLE / censura / blocos / variograma / cross-plot | Desmarcados | MLE e seus cortes dependem da habilitação do grupo |
| Cortes inferior/superior de MLE | 0% / 0% | Convertidos em números; sem validação completa dos intervalos/relação |
| Histogram of angles | Desmarcado | Bins 10, 20, 30 e 50; inicial em execução: 20 |
| Rose diagram / Colour by strike | Marcados | Ponderação por comprimento e vetor médio inicialmente desmarcados |
| Bin size da rosa | 10° | Opções 5°, 10°, 20° e 30°; é largura angular, não quantidade de bins |
| Rotate Y-axis from N | 0° | Run aceita de −360° a +360°; em `doubleAngles`, aplica `ângulo − correção` |
| I-Y-X / permeabilidade / crack tensor | Desmarcados | Crack tensor está visualmente em Fluid flow |
| Number of blocks in maps | 12 | Testa `> 1`; mensagem pede inteiro, sem teste de integralidade |
| Distance to count I as Y | 0 antes da prévia | Preview substitui por `max(amplitude X, amplitude Y)/1000`, formatado com duas casas; pode arredondar para zero |
| Lambda | 1 | `0 ≤ λ ≤ 1` |
| Abertura fixa | Selecionada; `1e-3` | Valor `≥ 0`; núcleo usa modo fixo apenas se abertura `> 0` |
| Abertura escalada: fator / expoente | `1e-3` / 1 | Fator entre 0 e 0.1; expoente entre 0.5 e 1; equação `A = a × L^b` |
| Run wavelet analysis | Desmarcado | Habilita listas a/L, incremento e tipo |
| Listas a e L | `2 4 8 16` / `2 4 8 16` | Texto interpretado como vetor MATLAB; valores de L são invertidos internamente (`1/L`) |
| Incremento angular wavelet | 20° | Testa de 1° a 360°, sem garantir inteiro nem bins válidos para a rosa |
| Tipo wavelet | Morlet | Alternativa Mexican Hat |
| Opções de Graphs | Todas desmarcadas | Exigem seleção de dois pontos |
| Círculos em Graphs | 12 | Testa `> 1`; não verifica integralidade |
| Filename tag | Run1 | Sufixo usual `_Run1`; não existe proteção geral contra sobrescrita |

## 5. Épico MAP — aba Maps

**Estado padrão: I. Dependências:** IN-01/IN-12 e geometria; orientação para cores por strike e estabilidade.

| ID | Funcionalidade | Comportamento encontrado / saídas | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| MAP-01 | Traces, segments | Mapa básico das polilinhas com totais de traços, segmentos e nós no título | Geometria e contagens iguais às da prévia |
| MAP-02 | Show nodes | Nós nas extremidades com círculos pretos; centros dos segmentos com quadrados vermelhos; centro dos traços com círculos vermelhos | Marcadores nas posições esperadas de uma polilinha conhecida |
| MAP-03 | Mapa multicolorido | Desenha cada traço na cor guardada em `Colour`, quando há várias cores e a rotina de mapas é acionada | Preservar a identificação dos conjuntos do SVG |
| MAP-04 | Traces, by length | Cor por comprimento total; paleta `haline`, barra de cores com escala logarítmica | Cada traço ter cor consistente com seu comprimento e legenda; revisar Q-17 |
| MAP-05 | Segments, by length | Cor independente para o comprimento de cada segmento; paleta `haline` | Distinguir segmentos de comprimentos diferentes dentro do mesmo traço |
| MAP-06 | Segments, by strike | Cor pela orientação corrigida e invertida conforme flags; paleta cíclica `phase`, barra 0–180° | Orientações equivalentes por 180° compartilharem representação |
| MAP-07 | Estimated Intensity, P21 | Estimativa em grade de janelas circulares: `n/(4r)`, com n = interseções com a circunferência | Validar em geometrias sintéticas e exibir `m⁻¹` ou `pixel⁻¹` |
| MAP-08 | Estimated Density, P20 | Estimativa em grade: `m/(2πr²)`, com m = extremidades de segmentos dentro do círculo | Validar contagens e exibir `m⁻²` ou `pixel⁻²` |
| MAP-09 | Show scan circles | Mapa adicional com localização e tamanho das janelas; número de círculos controla o lado menor | Ajustar cobertura à razão de aspecto e mostrar os círculos usados |
| MAP-10 | Estatísticas globais P21/P20 | Console informa soma de comprimentos/área e número de segmentos/área; são resumos globais distintos da estimativa local por círculos | Conferir valores globais separadamente dos mapas locais |
| MAP-11 | Slip tendency | Calcula `Ts = abs(τ)/abs(σn)`, normaliza e colore segmentos; gera mapa e rosa de área igual | Conferir uma orientação conhecida e compatibilidade entre mapa e rosa; Q-17 |
| MAP-12 | Dilation tendency | Calcula `Td = (σ1 − abs(σn))/(σ1 − σ2)`; gera mapa e rosa | Conferir resposta às orientações e evitar divisão por zero |
| MAP-13 | Fracture susceptibility | Calcula `Sf = abs(σn) − Pf − (abs(τ) − C0)/mu`, em MPa; mapa e rosa coloridos | Conferir parâmetros, sinal e escala de suscetibilidade |
| MAP-14 | Critically stressed fractures | Classificação binária no mapa: `abs(τ) ≥ mu × (abs(σn) − Pf) + C0`; rosa correspondente | Distinguir CSF e Non-CSF e decidir tratamento exato da igualdade; Q-17 |
| MAP-15 | Parâmetros de estabilidade | Tensões principais, orientação de σ1, coesão, pressão de poros e atrito compartilhados pelas quatro análises | Alterações propagarem para as saídas selecionadas |
| MAP-16 | Diagrama de Mohr associado | Gerado quando qualquer análise de estabilidade é marcada; círculos de tensão total/efetiva e reta de resistência/deslizamento | Diagrama compatível com as tensões e o critério; a função atual recebe mas não desenha os pontos `sn,tau` |
| MAP-17 | Rosas de estabilidade | Largura fixa de 10°, cores da grandeza e linha de azimute de σ1; independentes do bin escolhido na aba Angles | Identificar grandeza e azimute e documentar o bin próprio |
| MAP-18 | Exportação dos campos locais | TXT com X, Y e valor de intensidade/densidade por centro de círculo; ao selecionar uma delas, a rotina grava ambas | Relacionar valores exportados às posições corretas da grade |

Fontes: [mapas geométricos e estabilidade](../../fracpaq-matlab/guiFracPaQ2Dtracemap.m), [amostragem circular](../../fracpaq-matlab/guiFracPaQ2Dpattern.m), [rosa de estabilidade](../../fracpaq-matlab/roseEqualAreaColourTendency.m), [Mohr](../../fracpaq-matlab/plotMohr2D.m).

## 6. Épico LEN — aba Lengths

**Estado padrão: I. Dependência:** modelo geométrico; centros de segmentos para variograma.

| ID | Funcionalidade | Comportamento encontrado / saídas | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| LEN-01 | Estatísticas de comprimento | Console: totais, quantidades excluídas, mínimo, máximo e média de traços e segmentos | Conferir separadamente comprimentos totais e comprimentos de segmentos |
| LEN-02 | Histogram of lengths | Dois histogramas: traços e segmentos; frequência absoluta e percentual, com marcações de mínimo/máximo | Contagens e percentuais coerentes e escolha de 10/20/30/50 bins |
| LEN-03 | Log-log: distribuição de frequência | Dois gráficos frequência × comprimento, para traços e segmentos | Eixos logarítmicos e dados positivos tratados corretamente |
| LEN-04 | Log-log: frequência acumulada | Dois gráficos de frequência acumulada complementar; mínimo, máximo e limite geométrico indicados | Conferir monotonicidade da curva e diagonal do domínio; ver Q-08 |
| LEN-05 | Censor lengths at map edges | Intenção: excluir traços que toquem os limites e seus segmentos; trabalha com NaN | Excluir corretamente os quatro lados sem desalinhamento de vetores; Q-05 |
| LEN-06 | Cross-plot lengths v angles | Dispersão de comprimentos de segmentos × ângulos axiais duplicados; correção de norte e flips no gráfico | Gerar também quando for a única opção selecionada; Q-03 |
| LEN-07 | MLE: lei de potência | Ajuste de traços e segmentos com estimativa de α e xmin por busca da distância K-S | Dois ajustes reproduzíveis em dados de referência e parâmetros apresentados |
| LEN-08 | MLE: exponencial | Ajuste de traços e segmentos com taxa λ e limiar xmin | Dois ajustes e curvas observadas/estimadas consistentes |
| LEN-09 | MLE: lognormal | Ajuste de traços e segmentos com μ, σ e xmin | Dois ajustes e documentação do intervalo efetivamente ajustado; Q-15 |
| LEN-10 | Cortes percentuais MLE | Campos Lower cut-off e Upper cut-off alteram a seleção dos dados ordenados | Validar percentuais, preservar amostra suficiente e conferir o sentido dos dois cortes |
| LEN-11 | Avaliação K-S dos ajustes | Cada distribuição compara com 2500 amostras sintéticas; imprime percentuais de resultados de testes | Exibir a métrica como resultado estatístico do procedimento, sem interpretá-la como probabilidade posterior da distribuição |
| LEN-12 | Figuras dos ajustes | Seis figuras: três distribuições × traços/segmentos; curvas observadas/estimadas, cortes e caixa de parâmetros | Associar corretamente cada gráfico à população e ao modelo |
| LEN-13 | Block size graphs | Rasteriza mapa, binariza, identifica componentes conectados e calcula áreas/centroides dos espaços delimitados | Validar blocos de áreas conhecidas e política de bordas/escala; Q-14 |
| LEN-14 | Saídas de tamanho de blocos | Mapa de centroides, curva acumulada log-log de áreas e histograma percentual de áreas | Três resultados coerentes com o mesmo conjunto de blocos |
| LEN-15 | Variogram of segment lengths | Semivariograma experimental dos comprimentos usando centros dos segmentos; 30 classes de distância | Conferir posições, distâncias e γ(h) em dados pequenos; sem presumir ajuste de curva |
| LEN-16 | Exportações numéricas | TXT de comprimentos ordenados de segmentos e traços e pares ângulo/comprimento | Conferir contagens, precisão, tag e convenção angular; Q-10 |

Detalhe estatístico: `KStestPower` usa `alpha=0.1` no `kstest2`, mas conta também `p>0.05`; exponencial e lognormal usam `alpha=0.05`. As rotinas não fixam semente aleatória. Os nomes `Hpercent`/`Ppercent` e as mensagens originais devem ser interpretados com cuidado. As assinaturas de retorno e a lógica de cortes/ajuste precisam da revisão Q-15.

Fontes: [análises de comprimentos](../../fracpaq-matlab/guiFracPaQ2Dlength.m), `fittingPL.m`, `fittingExponential.m`, `fittingLognormal.m`, `KStestPower.m`, `KStestexp.m`, `KStestLogNorm.m`, `PlotPowerLaw.m`, `PlotExp.m`, `PlotLogNorm.m`, `variogram.m`.

## 7. Épico ANG — aba Angles

**Estado padrão: I. Dependência:** orientações e comprimentos dos segmentos. A correção de norte é compartilhada com outras análises.

| ID | Funcionalidade | Comportamento encontrado / saídas | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| ANG-01 | Histogram of angles | Histograma de ângulos com frequência absoluta/percentual; usa dados duplicados em sentidos opostos | Conferir simetria axial e classes 10/20/30/50 |
| ANG-02 | Rose diagram (equal area) | Rosa de área igual; raio proporcional à raiz da frequência percentual; círculos de referência percentual | A área dos setores representar frequência corretamente |
| ANG-03 | Bin size | Larguras angulares de 5°, 10°, 20° e 30° | Agregar orientações nos setores corretos, inclusive fronteiras 0°/180°/360° |
| ANG-04 | Length weighted? | Usa soma dos comprimentos em cada setor dividida pelo comprimento total | Distinguir duas amostras com mesmas direções e comprimentos diferentes |
| ANG-05 | Show mean vector? | Calcula média circular axial, desvio padrão circular e resultante; desenha direção média em vermelho e imprime estatísticas | Conferir dados unimodais conhecidos e documentar significado axial |
| ANG-06 | Colour by strike? | Colore setores com `cmocean('phase')`, equivalência de 180° e barra de strike | Correspondência das cores com o mapa de orientação |
| ANG-07 | Rotate Y-axis from N | Campo compartilhado: `doubleAngles` arredonda `ângulo − correção` e acrescenta a direção oposta | Fixar convenção de sinal e normalizar ângulos de modo consistente; Q-10 |
| ANG-08 | Aplicação de Flip X/Y | Usa `reverseAxis` nos ângulos duplicados | Conferir inversões simples e duplas com uma direção conhecida |
| ANG-09 | Exportação EZROSE | TXT dos ângulos duplicados, corrigidos, invertidos e ordenados | Reproduzir a lista usada nas saídas angulares |

**Posição do crack tensor:** o controle está em **Fluid Flow**. Ele faz parte da seleção que aciona `guiFracPaQ2Dangle`, mas seu inventário funcional está em FLO-08, abaixo. Não há seletor de rosa linear na interface principal: `flag_equalarea` está fixo em 1; rotinas alternativas constam em AUX.

Fontes: [análises angulares](../../fracpaq-matlab/guiFracPaQ2Dangle.m), `roseEqualArea.m`, `roseEqualAreaColour.m`, `circStat.m`, `doubleAngles.m`, `reverseAxis.m`.

## 8. Épico FLO — aba Fluid Flow

**Estado padrão: I. Dependência:** geometria e interseções; orientação, comprimentos e área para os tensores.

| ID | Funcionalidade | Comportamento encontrado / saídas | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| FLO-01 | I-Y-X connectivity | Identifica extremidades isoladas I, junções Y e cruzamentos X, comparando segmentos de traços diferentes | Conferir redes sintéticas com contagens conhecidas |
| FLO-02 | Distance to count I as Y | Tolerância de proximidade usada na classificação e remoção de I próximos às interseções | Testar junção exata, undershoot e overshoot; resolver a diferença entre manual e implementação em Q-11 |
| FLO-03 | Limpeza topológica | Remove duplicatas de interseções e exclui I na borda; tenta resolver sobreposição das listas X/Y/I | Não contar duplicatas e explicitar política de borda |
| FLO-04 | Diagrama ternário I-Y-X | Proporções Y:X:I, contagem total e linhas de referência `CL=2` e `CL=3.57` | Ponto consistente com as contagens e tratamento de total zero |
| FLO-05 | Mapa de nós topológicos | Traços pretos e nós I azuis, Y verdes e X vermelhos, com legenda e contagens | Identificar visualmente cada classe no local correto |
| FLO-06 | Heatmaps de conectividade | Contagens locais de X+Y e de I; número de blocos ajustável, razão de aspecto respeitada e escala de cor comum | Grades e valores consistentes; tratar classes ausentes |
| FLO-07 | Exportação de conectividade | TXT com contagens I, X e Y; console com proporções e totais antes/depois de limpeza | Conferir resultado exportado com os mapas e o ternário |
| FLO-08 | Crack tensor plot | Gráfico polar conjunto das ordens 0, 2, 4 e 8; combina comprimentos ao quadrado, polos das orientações e área | Conferir padrão isotrópico e padrão direcional; manter polos distintos dos strikes |
| FLO-09 | Permeability plot (polar) | Estimativa 2D por placas paralelas; monta tensor P e `K=(λ/12)×(tr(P)I−P)` | Tensor simétrico e resposta direcional coerente com caso simples |
| FLO-10 | Fixed aperture | Abertura constante para os segmentos, inicial `1e-3` unidades | Abertura positiva produzir dependência cúbica esperada em K |
| FLO-11 | Scaled apertures | Abertura `A=a×L^b`, com fator e expoente editáveis | Calcular abertura por segmento e conferir efeito na permeabilidade |
| FLO-12 | Lambda factor | Fator de escala hidráulica entre 0 e 1; valor informado pelo usuário | K escalar linearmente com λ, incluindo λ=0 |
| FLO-13 | Extremos e unidades de permeabilidade | Console imprime autovalores mínimo/máximo em metros² ou pixels²; gráfico polar mostra anisotropia | Conferir autovalores e rótulos com a escala da entrada |

O programa **estima permeabilidade e caracteriza conectividade**. Não foi encontrado um solucionador de fluxo com condições de contorno, campo de pressão, vazão ou transporte. Não atribuir essas funcionalidades ao nome da aba.

Fontes: [conectividade](../../fracpaq-matlab/getConnectivity.m), `guiFracPaQ2Dpattern.m:272–334`, [permeabilidade](../../fracpaq-matlab/guiFracPaQ2Dtensor.m), [crack tensors](../../fracpaq-matlab/guiFracPaQ2Dcracktensor.m), `getF2tensor.m`, `getF4tensor.m`, `getF8tensor.m`.

## 9. Épico WAV — aba Wavelets

**Estado padrão: I. Dependências:** traços carregados; rasterização interna; núcleos CWT e FFT.

| ID | Funcionalidade | Comportamento encontrado / saídas | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| WAV-01 | Ativar análise 2D | Checkbox “Run wavelet analysis”, com aviso de custo de processamento | Executar somente quando marcado e mostrar andamento |
| WAV-02 | Escolha de wavelet | Morlet ou Mexican Hat | Aplicar o núcleo correspondente aos mesmos dados |
| WAV-03 | Lista de escalas a | Permite analisar várias escalas numa execução | Produzir resultados identificados para cada a |
| WAV-04 | Lista de fatores L | Controla anisotropia/forma; interface recebe inteiros e passa seus recíprocos ao cálculo | Interpretar lista e inversão corretamente, sem zeros ou valores inválidos |
| WAV-05 | Incremento angular | Controla amostragem de orientações no intervalo axial; menor incremento aumenta o trabalho | Usar incremento válido e compatível com os gráficos; Q-12 |
| WAV-06 | Rasterização do mapa | Grava `FracPaQ2D_wavelet_traces.png` a 72 dpi; traços com pelo menos 45% do maior comprimento são desenhados mais espessos | Registrar e validar essa ponderação visual; resultado depende da imagem gerada |
| WAV-07 | Transformada contínua 2D | Núcleos rotacionados/escalados, convolução por FFT, remoção da média e medidas internas de energia `eta` | Comparar com referência numérica de cada núcleo |
| WAV-08 | Normalização e otimização | Normaliza pela resposta da wavelet a si mesma, divide por a, aplica fator 2.5 e maximiza sobre L e orientação | Conferir coeficientes normalizados e seleção de orientação dominante |
| WAV-09 | Limiar de coeficientes | Seleciona orientações onde WC é maior que 50% do máximo; limiar está fixo no código | Validar seleção e documentar o valor fixo; não anunciar slider de limiar |
| WAV-10 | Painel por escala | Figura 2×2: imagem binária, mapa WC, rosa de orientações ótimas e histograma de WC com log10 da frequência | Gerar quatro painéis coerentes para cada a |
| WAV-11 | Exportação de orientações | TXT `theta` por escala, com orientações ótimas convertidas em graus e duplicadas axialmente | Dados exportados corresponderem à seleção representada na rosa |
| WAV-12 | Flips e diagnóstico | Flags X/Y alteram representação e orientações; console informa tamanho da imagem, escala, máximo WC e início/fim | Conferir comportamento de espelhamento e acompanhamento do processamento |

O resultado usa coordenadas da imagem rasterizada, em pixels. A função principal de wavelet não recebe a correção de norte nem o fator de escala como parâmetros: não presumir correção geográfica ou escala física idênticas às demais abas. Não há botão de cancelamento de processamento na aba principal; o `Cancel` existente pertence ao diálogo auxiliar legado.

Fontes: [wavelet integrada](../../fracpaq-matlab/guiFracPaQ2Dwavelet.m), `guiFracPaQ2D.m:1367–1422`, `morlet.m`, `mexicanhat.m`, `morletCWT.m`, `mexicanhatCWT.m`, `morletCWTself.m`, `mexicanhatCWTself.m`.

## 10. Épico GRA — aba Graphs

**Estado padrão: I. Dependências:** geometria, centros e linha escolhida com dois pontos.

| ID | Funcionalidade | Comportamento encontrado / saídas | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| GRA-01 | Select end points | Captura dois cliques com `ginput(2)` e desenha a linha no mapa | Guardar ponto inicial/final, desenhar linha e rejeitar comprimento zero |
| GRA-02 | Validação de linha | Run exige pontos quando há opção de Graphs selecionada | Impedir execução sem linha e aceitar coordenadas negativas/válidas; Q-13 |
| GRA-03 | ALONG: Trace length | Intersecta a linha com segmentos; gráfico do comprimento do traço associado × distância da interseção ao ponto 1 | Conferir posição e comprimento em cada interseção |
| GRA-04 | ALONG: Segment length | Comprimento do segmento intersectado × distância ao longo da linha | Mostrar apenas os segmentos intersectados |
| GRA-05 | ALONG: Segment angle | Ângulo do segmento intersectado × distância ao longo da linha | Ângulos e interseções coerentes; observar que usa os ângulos originais |
| GRA-06 | ALONG: Estimated intensity, P21 | Janelas circulares igualmente espaçadas sobre a linha estimam intensidade | Validar círculos, raios, interseções e posição de cada amostra |
| GRA-07 | ALONG: Estimated density, P20 | Mesmas janelas estimam densidade por extremidades internas | Conferir contagem e unidades por área |
| GRA-08 | Número de scan circles | Controla diâmetro e distribuição das janelas ao longo do segmento selecionado | Círculos cobrirem a linha de forma regular e sem diâmetro nulo |
| GRA-09 | Mapa auxiliar do perfil | Exibe traços, linha, pontos 1/2 e círculos, com legenda | Relacionar amostras e resultados com sua localização |
| GRA-10 | FROM: Trace length | Comprimento total × distância perpendicular **com sinal** do centro do traço à reta | Valores de lados opostos com sinais opostos; inclui todos os traços |
| GRA-11 | FROM: Segment length | Comprimento × distância perpendicular com sinal do centro de cada segmento | Incluir todos os segmentos e seus centros corretos |
| GRA-12 | FROM: Segment angle | Ângulo original × distância perpendicular com sinal do centro de cada segmento | Orientações no intervalo representado de 0–180° |
| GRA-13 | Exportação de gráficos | Grava PNG para cada gráfico e mapa auxiliar pelo mecanismo comum | Nomes e tag identificarem o tipo e a execução |

**Particularidades atuais:** marcar apenas intensidade **ou** densidade acaba gerando os dois gráficos, pois compartilham um único bloco de execução. ALONG pode representar o mesmo traço mais de uma vez se a linha cruzar mais de um de seus segmentos. FROM usa a distância à reta definida pelos pontos, sem limitar a projeção ao trecho finito. A rotina não recebe correção de norte; flips são aplicados no mapa auxiliar, não como transformação geral dos dados dos perfis. Não foi encontrada exportação TXT dos perfis nesta rotina.

Fontes: `guiFracPaQ2D.m:666–699`, `1160–1191`, [gráficos ao longo e a partir de linha](../../fracpaq-matlab/guiFracPaQ2Dgraphs.m).

## 11. Épico Q — limitações, divergências e correções para planejamento

Todos os itens desta seção são **P**: revisão/correção proposta. São separados das funcionalidades existentes para evitar que a migração replique erros. **P0** = pode comprometer dados ou execução básica; **P1** = resultado, consistência ou fluxo funcional; **P2** = manutenção e clareza. A prioridade é sugestão técnica.

| ID | Prioridade | Evidência encontrada | Encaminhamento / critério de aceite |
| --- | --- | --- | --- |
| Q-01 | P1 | Run valida vários campos de outras análises mesmo quando elas estão desmarcadas (`guiFracPaQ2D.m:1046–1159`) | Validar somente parâmetros necessários às saídas selecionadas |
| Q-02 | P1 | Mensagens pedem inteiros, mas vários campos só testam intervalo; a/L usam `isempty(str2double(...))`, que não valida vetores; faltam verificações de limites/casos degenerados | Validar integralidade, finitude, listas não vazias, cortes, tolerância I→Y e intervalos coerentes |
| Q-03 | P1 | `flag_length` não inclui `flag_crossplot` (`guiFracPaQ2D.m:1300`), apesar do manual anunciar a correção | Cross-plot executar como seleção única |
| Q-04 | P1 | `imfinfo` usa texto do campo sem `selpath`, enquanto leitura usa caminho combinado; cancelamento de Browse recebe 0 mas testa `~isempty`; detecção SVG usa busca sensível a maiúsculas | Testar arquivo fora da pasta atual, caminho completo digitado, cancelamento e extensão `.SVG` |
| Q-05 | P0 | Censura compara Y com limites X, usa `Node(nSeg)` em vez do último nó e perde alinhamento ao filtrar comprimentos antes dos ângulos (`guiFracPaQ2Dlength.m:49–105`) | Corrigir bordas e índices; usar uma máscara comum para comprimentos/ângulos e definir o que é censurado |
| Q-06 | P0 | Leitor de imagem não preenche `Segment.midpointX/Y` nem `Colour`; usa comprimento do primeiro traço em `endLength` dos demais (`guiFracPaQ2Dimage.m:108–122`) | Unificar campos de `traces` e testar todas as seis abas com imagem, inclusive nós, variograma e FROM |
| Q-07 | P0 | Leitores podem manter nós repetidos enquanto contam segmentos de outra forma; `euclideanLength` usa X no lugar do Y final (`guiFracPaQ2Dlist.m:86–115,167–168`; também em `readTraces`) | Normalizar nós sem perder pares, conferir comprimentos e rejeitar traços sem segmento |
| Q-08 | P1 | Máximos iniciais em 0 em `getMapLimits`/leitor principal falham para mapas inteiramente negativos; comprimento máximo possível usa `sqrt(xMax²+yMax²)`, sem subtrair mínimos | Conferir domínio transladado, coordenadas negativas e diagonal a partir das amplitudes |
| Q-09 | P0 | Conversor SVG é textual e sensível à ordem/forma de atributos; não aplica transformações gerais; limpeza de TXT vazios busca `*_converted.txt` em toda a pasta atual (`convertSVG2txt_colour2.m:369–376`) | Limitar limpeza aos arquivos criados naquela conversão e definir parser/subconjunto SVG seguro e verificável |
| Q-10 | P1 | Correção de norte é subtraída e arredondada, embora o manual diga adicionada; normalização angular não usa módulo completo; TXT ângulo/comprimento e `segmentdata` usam ângulo original | Fixar convenção angular única e documentar/exportar dados corrigidos de forma consistente |
| Q-11 | P0 | Manual descreve snap I→Y para undershoot/overshoot; código depende de interseções existentes e tem criação de novos Y comentada (`getConnectivity.m:135–168`); há referências a `xint`/`XU` sem garantia de inicialização | Implementar ou delimitar o snap; testar rede sem cruzamentos, só I, só X, só Y, duplicatas e junções próximas |
| Q-12 | P1 | Wavelet aceita incremento até 360°, mas sua amostragem é axial e a rosa exige classes coerentes; matrizes usam ordem nx/ny que exige atenção em imagens retangulares; não recebe norte/escala física | Testar incremento >180°, passo incompatível, dados vazios, imagens retangulares e tratamento geográfico |
| Q-13 | P1 | Graphs verifica ausência pela soma das coordenadas, não exige pontos distintos e usa interseções sem garantir que existam; redes sem interseção podem deixar `xInt` indefinido | Validar seleção geometricamente e retornar resultado vazio controlado; conferir caminho de seleção após imagem |
| Q-14 | P1 | Tamanho de blocos vem de áreas em pixels da rasterização; não há exclusão explícita da região exterior nem conversão física inequívoca após escala | Definir domínio, bordas, resolução e conversão de área; conferir retângulos de áreas conhecidas |
| Q-15 | P1 | Chamadas MLE em `guiFracPaQ2Dlength` não alinham todos os nomes de retorno às assinaturas; cortes usam índices com semântica a revisar; lognormal busca xmin sem truncar a amostra no laço (`fittingLognormal.m:89–107`) | Validar algoritmos, sentido dos cortes, retorno de todos os parâmetros, repetidos/zeros e tamanho mínimo de amostra |
| Q-16 | P1 | Imagens intermediárias de blocos/wavelets têm nomes fixos; arquivos finais abrem em modo de escrita e podem sobrescrever resultados | Definir política de nomes por execução e temporários isolados; conferir execuções sucessivas |
| Q-17 | P1 | Ts/Sf usam normalizações preliminares diferentes das orientações corrigidas por σ1; mu=0 ou σ1=σ2 causam divisões problemáticas; mapa CSF usa `≥` e rosa `>`; cores de comprimento usam índice linear com barra logarítmica | Revisar consistência numérica e visual, limites de índices, casos degenerados e acordo mapa/rosa |
| Q-18 | P2 | Mensagem final fala em `.tif`, mas `guiPrint.m:35–36` grava PNG; comentários preservam antigas alternativas TIFF/JPEG | Mensagens e documentação refletirem o formato efetivamente exportado |
| Q-19 | P2 | Há scripts com assinaturas antigas, nome de função diferente do arquivo e recursos externos ausentes; exemplos em vírgulas convivem com leitor GUI tabulado | Classificar legado, parametrizar utilitários e disponibilizar exemplos válidos; ver apêndice |
| Q-20 | P1 | Estimativas circulares usam teste de secante com condição adicional de mudança de sinal em X **e** Y (`guiFracPaQ2Dpattern.m:226–239`; repetido em Graphs) | Validar contagem para linhas horizontais, verticais, oblíquas, tangentes e círculos transladados |
| Q-21 | P1 | Preview aplica escala, mas Run relê o campo sem reconstruir necessariamente a geometria; mudança posterior pode gerar rótulos incompatíveis | Invalidar/refazer prévia quando escala, arquivo ou parâmetros de extração mudarem |

As falhas de condições/índices são observáveis na leitura do código. A extensão do impacto em cada conjunto de dados precisa ser confirmada por execução e casos de referência. Esta análise não modifica os arquivos MATLAB.

## 12. Épico EXP — arquivos de saída, impressão e rastreabilidade

| ID | Estado | Funcionalidade / comportamento encontrado | Critério de aceite para implementação futura |
| --- | --- | --- | --- |
| EXP-01 | I | Exportação automática comum de figuras em **PNG a 600 dpi**, área de impressão 20×20 cm (`guiPrint`) | Figura exibida e arquivo exportado representarem o mesmo resultado |
| EXP-02 | I | Tag adicionada ao nome-base antes da extensão, usualmente `_Run1` | Identificar execução e manter nomes previsíveis |
| EXP-03 | I/P | Resultados comuns vão à pasta corrente; conversões SVG ficam junto à origem; alguns intermediários têm nome fixo | Documentar localização e aplicar política de sobrescrita/temporários na migração |
| EXP-04 | I | TXT numéricos de comprimento, orientação, campos P21/P20, conectividade, segmentos e wavelets | Preservar unidades, ordem, quantidade de linhas e significado de colunas |
| EXP-05 | A | Exemplos antigos gravam BMP/JPEG e arquivos sem tag; são saídas de scripts específicos | Não confundir esses formatos com a exportação principal |
| EXP-06 | P | Não foi encontrado projeto/sessão persistente, histórico de parâmetros ou relatório consolidado | Se necessário no produto futuro, criar histórias próprias, sem tratá-las como paridade existente |

### 12.1 Catálogo de nomes de figuras da interface principal

Salvo os intermediários citados abaixo, cada nome-base recebe **`{tag}.png`**, sendo `{tag}` por exemplo `_Run1`. A tabela também permite conferir a cobertura das saídas automáticas.

| Grupo | Nomes-base encontrados |
| --- | --- |
| Diagnóstico Hough | `FracPaQ2D_Houghstuff` |
| Mapa básico e cores | `FracPaQ2D_tracemap`, `FracPaQ2D_tracemap_multicolour`, `FracPaQ2D_tracelengthmap`, `FracPaQ2D_segmentlengthmap`, `FracPaQ2D_segmentstrikemap` |
| Estabilidade e Mohr | `FracPaQ2D_Mohrplot`, `FracPaQ2D_sliptendencymap`, `FracPaQ2D_sliptendencyrose`, `FracPaQ2D_dilationtendencymap`, `FracPaQ2D_dilationtendencyrose`, `FracPaQ2D_fracsuscepmap`, `FracPaQ2D_fracsusceprose`, `FracPaQ2D_CSFmap`, `FracPaQ2D_CSFrose` |
| P21/P20 | `FracPaQ2D_scancircle`, `FracPaQ2D_intensityP21`, `FracPaQ2D_densityP20` |
| Histogramas de comprimento | `FracPaQ2D_histotracelength`, `FracPaQ2D_histosegmentlength` |
| Log-log | `FracPaQ2D_loglogplottracelengthdensity`, `FracPaQ2D_loglogplottracelength`, `FracPaQ2D_loglogplotsegmentlengthdensity`, `FracPaQ2D_loglogplotsegmentlength` |
| Cross-plot | `FracPaQ2D_crossplotsegmentlengthangle` |
| MLE | `FracPaQ2D_tracelengthsFittingPowerLaw`, `FracPaQ2D_tracelengthsFittingExponential`, `FracPaQ2D_tracelengthsFittingLogNormal`, `FracPaQ2D_segmentlengthsFittingPowerLaw`, `FracPaQ2D_segmentlengthsFittingExponential`, `FracPaQ2D_segmentlengthsFittingLogNormal` |
| Blocos e variograma | `FracPaQ2D_blocksizecentroidmap`, `FracPaQ2D_blocksizeloglog`, `FracPaQ2D_blocksizehisto`, `FracPaQ2D_segmentlength_variogram` |
| Ângulos | `FracPaQ2D_roseangleEqArea`, `FracPaQ2D_histoangle` |
| Conectividade | `FracPaQ2D_IYXnodes_traces`, `FracPaQ2D_XYnodes_traces_heat`, `FracPaQ2D_Inodes_traces_heat`, `FracPaQ2D_IYXtriangle` |
| Tensores | `FracPaQ2D_permeability_polar`, `FracPaQ2D_cracktensor` |
| Wavelet | `FracPaQ2Dwavelet_a{a}` |
| Graphs ALONG | `guiFracPaQ2D_tracelengthalonggraph`, `guiFracPaQ2D_segmentlengthalonggraph`, `guiFracPaQ2D_segmentanglealonggraph`, `guiFracPaQ2D_intensityalonggraph`, `guiFracPaQ2D_densityalonggraph` |
| Graphs FROM e mapa | `guiFracPaQ2D_tracelengthfromgraph`, `guiFracPaQ2D_segmentlengthfromgraph`, `guiFracPaQ2D_segmentanglefromgraph`, `guiFracPaQ2D_graphtracemap` |

`FracPaQ2D_roseangleLinear` aparece num ramo atualmente desativado, e não é saída selecionável da GUI principal.

### 12.2 Catálogo de dados e intermediários

| Nome / padrão | Gatilho | Conteúdo / particularidade |
| --- | --- | --- |
| `FracPaQ2Dsegmentlengths{tag}.txt` | Execução da rotina Lengths | Comprimentos de segmentos ordenados, uma coluna, duas casas decimais |
| `FracPaQ2Dtracelengths{tag}.txt` | Execução da rotina Lengths | Comprimentos totais ordenados, uma coluna, duas casas |
| `FracPaQ2Dsegmentangleslengths{tag}.txt` | Execução da rotina Lengths | Ângulo original e comprimento de cada segmento; ver Q-10 |
| `FracPaQ2DEZROSE{tag}.txt` | Execução da rotina Angles, inclusive ao pedir crack tensor | Ângulos duplicados/corrigidos/invertidos, ordenados |
| `FracPaQ2Dintensity{tag}.txt` | P21 ou P20 | X, Y e intensidade por centro de círculo |
| `FracPaQ2Ddensity{tag}.txt` | P21 ou P20 | X, Y e densidade por centro de círculo |
| `FracPaQ2Dconnectivity{tag}.txt` | I-Y-X | Contagens rotuladas I, X e Y |
| `FracPaQ2Dsegmentdata{tag}.txt` | Slip tendency | Índice sequencial, X1, Y1, X2, Y2 e ângulo original; não contém os valores de Ts |
| `FracPaQ2Dwavelet_theta_a{a}{tag}.txt` | Wavelet, por escala | Orientações ótimas duplicadas, em graus |
| `nome_converted.txt` | SVG com uma cor ou sem separação multicolorida | Nós convertidos; não usa a tag da execução |
| `nome_colourHHHHHH_converted.txt` | SVG com várias cores | Nós por cor, permitindo carregar cada conjunto separadamente |
| `FracPaQ2D_blocksize.bmp` | Block size graphs | Raster intermediário de 300 dpi, nome fixo |
| `FracPaQ2D_wavelet_traces.png` | Wavelet | Raster intermediário de 72 dpi, nome fixo |
| `FracPaQ2D_Example1_processed.tif` | Script de pré-processamento | Imagem preparada para Hough; fora do fluxo GUI |

## 13. Épico AUX — outros recursos encontrados

Estas capacidades existem nos arquivos, mas seu estado deve ser preservado no planejamento: uma biblioteca com determinada opção não significa que a GUI a ofereça.

| ID | Estado | Recurso | Escopo e critério de aceite para eventual aproveitamento |
| --- | --- | --- | --- |
| AUX-01 | A | Pré-processamento de fotografia | `FracPaQ2D_imagePreprocess`: RGB→cinza, filtro de mediana 20×20, diferença, bordas Sobel, fechamento, afinamento e inversão; painel de seis etapas e TIFF. Parametrizar entrada/saída antes de integrar |
| AUX-02 | A | Importação de Midland Valley Move | `Move2FracPaq`: converte ASCII com três coordenadas e objetos separados por linhas vazias em pares de nós; permite escolher colunas, inicialmente 1 e 3. Conferir cabeçalho e último objeto antes de usar |
| AUX-03 | A | Leitor de texto genérico | `readtext`: delimitadores, comentários, aspas, dados numéricos/textuais/mistos, vazios, estatísticas/máscaras e formatos de fim de linha. A GUI usa tabulação numérica para nós |
| AUX-04 | A | Geometria computacional | Interseção de segmentos, identificação de paralelos/coincidentes, distâncias ponto–segmento e ponto–ponto, limites do mapa e conversão hex→RGB. Validar casos degenerados e precisão |
| AUX-05 | A | Variograma além da GUI | Biblioteca admite número de classes, distância máxima, nuvens de variograma, subamostragem aleatória e anisotropia 2D com passo angular. GUI usa apenas semivariograma padrão com 30 classes; integração avançada seria nova história |
| AUX-06 | A/E | Crack tensor de ordem 16 | `getF16tensor` calcula tensor/projeção polar de ordem 16, mas não é chamado pela GUI. Expor somente após avaliar custo e utilidade |
| AUX-07 | E | Rosas alternativas | `roseLinear`, `rosePlot`, `roseEqualArea2` oferecem variantes lineares/área e opções históricas; não são seletores da GUI principal. Rever assinaturas antes de aproveitar |
| AUX-08 | A | Paletas perceptuais | `cmocean`: 18 famílias (thermal, haline, solar, ice, gray, oxy, deep, dense, algae, matter, turbid, speed, amp, tempo, balance, delta, curl e phase), quantidade de níveis, inversão, pivô de divergência e aplicação ao eixo; GUI usa sobretudo haline, phase e thermal. A prévia sem argumentos depende de `cmocean.png`, ausente |
| AUX-09 | E | Cores experimentais | `newCM` e `testCM` exploram reamostragem não linear de paletas e mapas; não são controles da aplicação |
| AUX-10 | A/E | Desenho auxiliar | Elipse rotacionada, arcos, eixos centralizados e utilitários de diagrama ternário; úteis para visualização, sem botões próprios |
| AUX-11 | E | Probe plane / scanlines | `probePlane` mede interseções por comprimento em várias orientações e retorna medidas m, m_ij e mq; não está conectado ao Run atual |
| AUX-12 | E | Diálogo wavelet separado | `guiWaveletDialog.m/.fig`: listas a/L, incremento, Morlet/Mexican Hat, Run, Cancel e texto Ready; chama `guiFracPaQ2Dwavelet2` |
| AUX-13 | E | Variantes wavelet | `guiFracPaQ2Dwavelet2` reutiliza raster; `wavelet3` e `FracPaQ2Dwave_2_Morlet` leem imagem fixa e usam apresentações/exportações alternativas. Requerem revisão de entradas e dependências |
| AUX-14 | E | Interface antiga 2.2 | `guiFracPaQ2Dtabbed` preserva callbacks e chamada ao diálogo wavelet; seu `.fig` homônimo não está incluído e suas chamadas têm assinaturas antigas |
| AUX-15 | E | Scripts de demonstração | Testes de imagem, mapas, cores, wavelets, blocos, tensores, rosa/ternário e histogramas; não formam suíte automatizada com asserções |
| AUX-16 | A | Conjuntos de exemplo | Mapas de falhas/juntas, Souter por cores, lâmina H12Z, tiles, mapas editados, casos IYX e fotos de Macduff/Orkney; úteis como candidatos a fixtures após validar o formato |
| AUX-17 | A | Manual e orientação de preparação | Guia explica digitalização em software externo, SVG 1.1, camadas/cores, escala, Hough e métodos; a aplicação não é um editor completo de digitalização |
| AUX-18 | A | Documentação e distribuição | README 2.8.0, licença MIT, créditos/bibliografia; página HTML com links GitHub e downloads ZIP/TAR.GZ, CSS responsivo e estilo de impressão |
| AUX-19 | E | Arquivos do site sem função analítica | `params.json` é metadado antigo do gerador de site; não guarda preferências da aplicação. `main.js` só escreve uma mensagem no console; não é uma versão web do FracPaQ |

Dependências identificadas: MATLAB/GUI GUIDE, Image Processing Toolbox para Hough, operações morfológicas, rasterização/análise de blocos e partes das wavelets; funções estatísticas como `kstest2`, `exprnd`, `lognrnd`, `logncdf` e `hist3` usadas em estatística/conectividade. Há aviso geral para MATLAB R2015a ou posterior e aviso de R2016a para gráficos com eixo Y duplo; isso não comprova compatibilidade completa, pois o código usa APIs de versões posteriores. O manual registra desenvolvimento em R2018a/R2018b, em Windows, macOS e Linux.

Não foram encontrados controles próprios de edição de traços, desfazer/refazer, importação GIS/shapefile/DXF, processamento 3D, treinamento de IA, geração de redes sintéticas como fluxo de usuário, ajuste de curva do variograma na GUI, cancelamento assíncrono geral, salvamento de sessão ou processamento em lote de arquivos arbitrários. Caso desejados, devem ser tratados como **novas funcionalidades**, não como recursos já presentes.

## 14. Proposta de decomposição em sprints

Cada ID acima pode ser convertido em uma história/tarefa. Para uma sprint, registrar responsável, estimativa, dados de teste, decisões de convenção/unidades e os critérios de aceite já listados. A ordem abaixo privilegia uma base geométrica confiável antes das análises dependentes. Todos os itens continuam **a planejar**, sem indicar conclusão no projeto Python.

| Sprint sugerida | Resultado demonstrável | Escopo / IDs | Dependências |
| --- | --- | --- | --- |
| S0 — referência e base científica | Modelo de nós/segmentos, unidades e exemplos pequenos com resultados esperados | IN-02/03/04, AUX-04/16/18; Q-07/08; convenções Q-10 | Nenhuma; definir contrato de dados antes das telas |
| S1 — interface e entrada TXT | Selecionar arquivo, prévia, estatísticas, abas, flips, Run/Exit e tag | UI-01 a UI-19; IN-01; EXP-01/02; Q-01/02/04/21 | S0 |
| S2 — SVG e grupos por cor | Converter SVG compatível, preservar conjuntos e executar um conjunto isolado | IN-05 a IN-11; MAP-03; Q-09/19 | S1 |
| S3 — imagens e Hough | Carregar imagem, ajustar detecção e conferir o diagnóstico | IN-12 a IN-18; AUX-01; Q-06 | S1; contrato geométrico de S0 |
| S4 — mapas e orientações | Mapas básicos/por atributo, histograma angular e rosa configurável | MAP-01/02/04/05/06; ANG-01 a ANG-09; Q-10 e cores de Q-17 | S1; S2/S3 para validar as demais entradas |
| S5 — comprimentos e exportações | Histogramas, log-log, cross-plot, censura e arquivos numéricos | LEN-01 a LEN-06 e LEN-16; EXP-03/04; Q-03/05/08/16/18 | S4 |
| S6 — modelos estatísticos | Seis ajustes, cortes e avaliação K-S com critérios documentados | LEN-07 a LEN-12; Q-15; reprodutibilidade de amostras sintéticas | S5 |
| S7 — estatística espacial | Mapas P21/P20, círculos, blocos e variograma | MAP-07 a MAP-10 e MAP-18; LEN-13 a LEN-15; Q-14/20 | S4/S5 |
| S8 — conectividade | Nós classificados, ternário, heatmaps e contagens exportadas | FLO-01 a FLO-07; Q-11 | S2 e base de interseções; S7 para padrões de mapas |
| S9 — tensores e permeabilidade | Crack tensors 0/2/4/8 e permeabilidade por abertura fixa/escalada | FLO-08 a FLO-13 | S4/S5; convenções e área validadas |
| S10 — estabilidade de fraturas | Mapas, rosas e Mohr consistentes com parâmetros de tensão/resistência | MAP-11 a MAP-17; Q-17 | S4/S9; casos científicos de referência |
| S11 — perfis Graphs | Seleção de linha e gráficos ALONG/FROM com resultado vazio controlado | GRA-01 a GRA-13; Q-13/20 | S3/S5/S7 para centros e amostragem |
| S12 — wavelets | Morlet/Mexican Hat por escala, figuras e orientação exportada | WAV-01 a WAV-12; Q-12/16 | S3/S4; rasterização e desempenho |
| S13 — complementos e revisão de paridade | Utilitários escolhidos, documentação e cobertura final por entrada | AUX-02/03/05 a AUX-19 conforme prioridade; EXP-05/06; Q-19 | Selecionar explicitamente o que sai do estado experimental |

### 14.1 Condições de conclusão por entrega

- **Paridade funcional:** o ID gera o resultado descrito; limitações intencionais e melhorias em relação ao original ficam registradas.
- **Verificação numérica:** usar casos pequenos com valores esperados, além de exemplos reais do pacote; para MLE/wavelets, referências específicas e tolerâncias explícitas.
- **Cobertura de entrada:** conferir TXT, SVG simples, SVG multicolorido e imagem compatível nas análises que os suportam, incluindo Q-06.
- **Casos de borda relevantes:** vazio, traço degenerado, linha sem interseção, mapa transladado/negativo, ausência de uma classe topológica, valores repetidos e unidades diferentes.
- **Apresentação e dados:** unidades, títulos, cores, arquivos, tag e parâmetros devem concordar com o cálculo exibido.
- **Rastreabilidade:** guardar quais opções e convenções produziram os resultados de referência; não usar defeitos conhecidos do MATLAB como único oráculo de correção.

### 14.2 Modelo de cartão para a ferramenta de sprints

```text
ID / título: LEN-06 — Cross-plot de comprimentos e ângulos
Tipo: paridade funcional com correção Q-03
Objetivo: relacionar comprimento e orientação de cada segmento.
Dependências: modelo de segmentos, correção de norte e inversões de eixo.
Entrada: conjunto com segmentos de comprimentos e direções conhecidos.
Saída: gráfico e exportação identificados pela tag da execução.
Critérios de aceite: gerar com seleção única; conferir pares X/Y,
duplicação axial, convenção angular, unidades e arquivo exportado.
Referência: guiFracPaQ2Dlength.m:357–389; guiFracPaQ2D.m:1300.
Responsável / estimativa / sprint: a definir.
```


## 15. Apêndice — inventário de todos os arquivos

Os estados abaixo indicam uso no pacote original, não progresso de implementação. Os 82 arquivos MATLAB têm papel identificado individualmente. Exemplos numéricos foram examinados como dados, sem atribuir uma funcionalidade nova a cada conjunto.

### 15.1 Código MATLAB — 82 arquivos

| Arquivo | Estado | Papel / ligação funcional |
| --- | --- | --- |
| [arc.m](../../fracpaq-matlab/arc.m) | A/E | Desenha arco em azul, passo de 5°; AUX-10. |
| [arc2.m](../../fracpaq-matlab/arc2.m) | A/E | Desenha arco pontilhado em preto, usado em rosa histórica; AUX-10. |
| [blocksize.m](../../fracpaq-matlab/blocksize.m) | E | Experimento de centroides/áreas a partir do BMP intermediário; AUX-15. |
| [centax2.m](../../fracpaq-matlab/centax2.m) | A/E | Redesenha eixos centralizados em origem escolhida; AUX-10. |
| [circStat.m](../../fracpaq-matlab/circStat.m) | I | Média axial, dispersão e resultante circular; ANG-05. |
| [cmocean.m](../../fracpaq-matlab/cmocean.m) | I/A | Biblioteca de 18 paletas, níveis, inversão e pivô; AUX-08. |
| [convertSVG2txt.m](../../fracpaq-matlab/convertSVG2txt.m) | E | Conversor antigo monocromático; ignora paths e gera nome sem _ antes de converted. |
| [convertSVG2txt_colour.m](../../fracpaq-matlab/convertSVG2txt_colour.m) | E | Conversor antigo por cores, anterior ao suporte de paths atual; AUX-14. |
| [convertSVG2txt_colour2.m](../../fracpaq-matlab/convertSVG2txt_colour2.m) | I | Conversor atual por cores, linhas, polilinhas e paths simples; IN-05 a IN-09. |
| [distancePointEdge.m](../../fracpaq-matlab/distancePointEdge.m) | I/A | Distância/projeção limitada de pontos sobre segmentos; AUX-04. |
| [distancePoints.m](../../fracpaq-matlab/distancePoints.m) | I/A | Distâncias entre pontos com norma configurável e modo diagonal; AUX-04. |
| [doubleAngles.m](../../fracpaq-matlab/doubleAngles.m) | I | Correção de norte, arredondamento e duplicação axial; ANG-07. |
| [fittingExponential.m](../../fracpaq-matlab/fittingExponential.m) | I | Estima λ/xmin, aplica cortes e chama K-S/plot; LEN-08. |
| [fittingLognormal.m](../../fracpaq-matlab/fittingLognormal.m) | I | Estima μ/σ/xmin, aplica cortes e chama K-S/plot; LEN-09, Q-15. |
| [fittingPL.m](../../fracpaq-matlab/fittingPL.m) | I/A | Estima α/xmin, cortes e correção opcional de amostra finita por argumento; LEN-07. |
| [FracPaQ2D_imagePreprocess.m](../../fracpaq-matlab/FracPaQ2D_imagePreprocess.m) | A | Pré-processamento demonstrativo de imagem e TIFF; AUX-01. |
| [FracPaQ2Dwave_2_Morlet.m](../../fracpaq-matlab/FracPaQ2Dwave_2_Morlet.m) | E | Análise Morlet em imagem fixa, painel e JPEG; AUX-13. |
| [getConnectivity.m](../../fracpaq-matlab/getConnectivity.m) | I | Classificação I/Y/X, limpeza e mapas de nós/heatmaps; FLO-01 a FLO-06. |
| [getF16tensor.m](../../fracpaq-matlab/getF16tensor.m) | A/E | Tensor de ordem 16 e projeção polar; fora da GUI; AUX-06. |
| [getF2tensor.m](../../fracpaq-matlab/getF2tensor.m) | I | Tensor de ordem 2 e projeção polar; FLO-08/09. |
| [getF4tensor.m](../../fracpaq-matlab/getF4tensor.m) | I | Tensor de ordem 4 e projeção polar; FLO-08. |
| [getF8tensor.m](../../fracpaq-matlab/getF8tensor.m) | I | Tensor de ordem 8 e projeção polar; FLO-08. |
| [getMapLimits.m](../../fracpaq-matlab/getMapLimits.m) | I | Limites X/Y a partir dos nós; Q-08. |
| [guiFracPaQ2D.m](../../fracpaq-matlab/guiFracPaQ2D.m) | I | Inicialização 2.8, validações, callbacks, navegação e despacho Run; UI/IN. |
| [guiFracPaQ2Dangle.m](../../fracpaq-matlab/guiFracPaQ2Dangle.m) | I | Histograma, rosa, exportação EZROSE e chamada de crack tensor; ANG/FLO-08. |
| [guiFracPaQ2Dcracktensor.m](../../fracpaq-matlab/guiFracPaQ2Dcracktensor.m) | I | Gráfico polar dos tensores 0/2/4/8; FLO-08. |
| [guiFracPaQ2Dgraphs.m](../../fracpaq-matlab/guiFracPaQ2Dgraphs.m) | I | Perfis ALONG/FROM e círculos ao longo da linha; GRA. |
| [guiFracPaQ2Dimage.m](../../fracpaq-matlab/guiFracPaQ2Dimage.m) | I | Leitura de imagem, Hough e construção dos traços; IN-12 a IN-18. |
| [guiFracPaQ2Dlength.m](../../fracpaq-matlab/guiFracPaQ2Dlength.m) | I | Comprimentos, histogramas, log-log, MLE, blocos e variograma; LEN. |
| [guiFracPaQ2Dlist.m](../../fracpaq-matlab/guiFracPaQ2Dlist.m) | I | Leitura TXT tabulado, segmentos e prévia; IN-01 a IN-04. |
| [guiFracPaQ2Dpattern.m](../../fracpaq-matlab/guiFracPaQ2Dpattern.m) | I | Círculos P21/P20, exportação e coordenação IYX; MAP/FLO. |
| [guiFracPaQ2Dtabbed.m](../../fracpaq-matlab/guiFracPaQ2Dtabbed.m) | E | Interface antiga 2.2; falta .fig homônimo e usa assinaturas antigas; AUX-14. |
| [guiFracPaQ2Dtensor.m](../../fracpaq-matlab/guiFracPaQ2Dtensor.m) | I | Aberturas, tensor hidráulico e permeabilidade polar; FLO-09 a FLO-13. |
| [guiFracPaQ2Dtracemap.m](../../fracpaq-matlab/guiFracPaQ2Dtracemap.m) | I | Mapas geométricos, por atributo e estabilidade/Mohr/rosas; MAP. |
| [guiFracPaQ2Dwavelet.m](../../fracpaq-matlab/guiFracPaQ2Dwavelet.m) | I | Rasterização, CWT por escala, painel e TXT de orientação; WAV. |
| [guiFracPaQ2Dwavelet2.m](../../fracpaq-matlab/guiFracPaQ2Dwavelet2.m) | E | Variante que reutiliza raster de nome fixo; chamada pelo diálogo auxiliar. |
| [guiFracPaQ2Dwavelet3.m](../../fracpaq-matlab/guiFracPaQ2Dwavelet3.m) | E | Variante com imagem fixa e figuras separadas; AUX-13. |
| [guiPrint.m](../../fracpaq-matlab/guiPrint.m) | I | Exportação comum PNG 600 dpi e tag; EXP-01/02. |
| [guiWaveletDialog.m](../../fracpaq-matlab/guiWaveletDialog.m) | E | Callbacks do diálogo separado de wavelet, Run/Cancel; AUX-12. |
| [guiWaveletTest.m](../../fracpaq-matlab/guiWaveletTest.m) | E | Chamada de ensaio com assinatura/variáveis históricas de wavelet; AUX-15. |
| [hexRGB.m](../../fracpaq-matlab/hexRGB.m) | I | Hexadecimal para string RGB normalizada; IN-08. |
| [KStestexp.m](../../fracpaq-matlab/KStestexp.m) | I | 2500 comparações K-S com amostras exponenciais; LEN-11. |
| [KStestLogNorm.m](../../fracpaq-matlab/KStestLogNorm.m) | I | 2500 comparações K-S com amostras lognormais; LEN-11. |
| [KStestPower.m](../../fracpaq-matlab/KStestPower.m) | I | 2500 comparações K-S com amostras de lei de potência; LEN-11. |
| [lineSegmentIntersect.m](../../fracpaq-matlab/lineSegmentIntersect.m) | I/A | Interseções vetorizadas, coordenadas, paralelismo e coincidência; AUX-04. |
| [logplots.m](../../fracpaq-matlab/logplots.m) | E | Demonstra histogramas/log-log lendo exportação de nome antigo sem tag; AUX-15. |
| [mexicanhat.m](../../fracpaq-matlab/mexicanhat.m) | I | Núcleo Mexican Hat anisotrópico/rotacionado; WAV-02/07. |
| [mexicanhatCWT.m](../../fracpaq-matlab/mexicanhatCWT.m) | I | Convolução CWT 2D via FFT e energia eta; WAV-07. |
| [mexicanhatCWTself.m](../../fracpaq-matlab/mexicanhatCWTself.m) | I | Resposta do núcleo a si mesmo para normalização; WAV-08. |
| [morlet.m](../../fracpaq-matlab/morlet.m) | I | Núcleo Morlet complexo anisotrópico/rotacionado; WAV-02/07. |
| [morletCWT.m](../../fracpaq-matlab/morletCWT.m) | I | CWT 2D via FFT, retorno real e energia eta; WAV-07. |
| [morletCWTself.m](../../fracpaq-matlab/morletCWTself.m) | I | Resposta Morlet a si mesma para normalização; WAV-08. |
| [Move2FracPaq.m](../../fracpaq-matlab/Move2FracPaq.m) | A | Conversor ASCII Move para arquivo de nós; AUX-02. |
| [newCM.m](../../fracpaq-matlab/newCM.m) | A/E | Reamostragem não linear de paleta haline por limites; AUX-09. |
| [plotCrackTensor.m](../../fracpaq-matlab/plotCrackTensor.m) | E | Demonstração de tensores com comprimentos/direções sintéticos; AUX-15. |
| [plotEllipse.m](../../fracpaq-matlab/plotEllipse.m) | A/E | Elipse preenchida com eixos e rotação relativa ao norte; AUX-10. |
| [PlotExp.m](../../fracpaq-matlab/PlotExp.m) | I | Curva observada/ajustada exponencial, cortes e parâmetro; LEN-08/12. |
| [PlotLogNorm.m](../../fracpaq-matlab/PlotLogNorm.m) | I | Curva observada/ajustada lognormal, cortes e parâmetros; LEN-09/12. |
| [plotMohr.m](../../fracpaq-matlab/plotMohr.m) | E | Variante curta de Mohr; declara função plotMohr2D, diferente do arquivo; Q-19. |
| [plotMohr2D.m](../../fracpaq-matlab/plotMohr2D.m) | I | Mohr total/efetivo e reta de resistência; MAP-16. |
| [PlotPowerLaw.m](../../fracpaq-matlab/PlotPowerLaw.m) | I | Curva observada/ajustada de potência, cortes e parâmetros; LEN-07/12. |
| [plotSouterMap.m](../../fracpaq-matlab/plotSouterMap.m) | E | Composição de conjuntos Souter; chama guiFracPaQ2Dtracemap2, ausente. |
| [probePlane.m](../../fracpaq-matlab/probePlane.m) | A/E | Varredura por scanlines direcionais e medidas de interseção; AUX-11. |
| [readtext.m](../../fracpaq-matlab/readtext.m) | I/A | Leitor genérico de texto, delimitadores, máscaras e estatísticas; AUX-03. |
| [readTraces.m](../../fracpaq-matlab/readTraces.m) | A/E | Leitor alternativo com figura própria e tentativa de remover traços degenerados; Q-07. |
| [reverseAxis.m](../../fracpaq-matlab/reverseAxis.m) | I | Transformação angular 180° − ângulo, com ajuste de negativos; ANG-08. |
| [roseEqualArea.m](../../fracpaq-matlab/roseEqualArea.m) | I | Rosa de área igual, ponderação opcional e média circular; ANG-02/04/05. |
| [roseEqualArea2.m](../../fracpaq-matlab/roseEqualArea2.m) | E | Variante experimental de rosa colorida com mensagens de depuração; AUX-07. |
| [roseEqualAreaColour.m](../../fracpaq-matlab/roseEqualAreaColour.m) | I | Rosa de área igual colorida por strike; ANG-06. |
| [roseEqualAreaColourTendency.m](../../fracpaq-matlab/roseEqualAreaColourTendency.m) | I | Rosas de Ts/Td/Sf/CSF com azimute de σ1; MAP-17. |
| [roseLinear.m](../../fracpaq-matlab/roseLinear.m) | E | Rosa linear por contagem/comprimento; ramo desativado na GUI; AUX-07. |
| [rosePlot.m](../../fracpaq-matlab/rosePlot.m) | A/E | Rosa histórica, dados direcionais/axiais e escala de área/linear; AUX-07. |
| [testCM.m](../../fracpaq-matlab/testCM.m) | E | Experimento de paleta com dado cape; declara função newCM, diferente do arquivo. |
| [testImage.m](../../fracpaq-matlab/testImage.m) | E | Imagem sintética diagonal, complemento, limpeza e exportação BMP; AUX-15. |
| [testmaps.m](../../fracpaq-matlab/testmaps.m) | E | Mapas experimentais por comprimento/strike, com paletas parula/hsv; AUX-15. |
| [testWavelet.m](../../fracpaq-matlab/testWavelet.m) | E | Ensaio de wavelet com chamada antiga e referência a test.jpg ausente; AUX-15. |
| [trilines.m](../../fracpaq-matlab/trilines.m) | A/E | Desenha linhas auxiliares para gráfico ternário; AUX-10. |
| [triplot.m](../../fracpaq-matlab/triplot.m) | I | Moldura ternária I/Y/X com malha de 10%; FLO-04. |
| [tripts.m](../../fracpaq-matlab/tripts.m) | I | Converte proporções ternárias e desenha pontos/linhas/rótulos; FLO-04. |
| [tritest.m](../../fracpaq-matlab/tritest.m) | E | Demonstração do ternário com chamada antiga de tripts; AUX-15. |
| [variogram.m](../../fracpaq-matlab/variogram.m) | I/A | Semivariograma isotrópico/direcional, nuvens e subamostragem; LEN-15/AUX-05. |
| [waveletDialog.m](../../fracpaq-matlab/waveletDialog.m) | E | Protótipo de diálogo que apenas escolhe Red/Green/Blue e Close; não processa wavelet. |

### 15.2 Interfaces, manual, documentação e site — 12 arquivos

| Arquivo | Papel identificado |
| --- | --- |
| [guiFracPaQ2D.fig](../../fracpaq-matlab/guiFracPaQ2D.fig) | Layout e valores iniciais de todos os controles da interface 2.8; inclui as seis abas, estatísticas, Run e Exit. |
| [guiWaveletDialog.fig](../../fracpaq-matlab/guiWaveletDialog.fig) | Layout auxiliar com a/L, incremento, tipos wavelet, Run, Cancel e mensagem Ready. |
| [FracPaQ User Guide v2.8.pdf](../../fracpaq-matlab/FracPaQ%20User%20Guide%20v2.8.pdf) | Manual de 39 páginas, preparação de dados, métodos, exemplos de saída e bibliografia. |
| [README.md](../../fracpaq-matlab/README.md) | Identifica versão 2.8.0 e alterações em SVG, MLE, conectividade e novos mapas. |
| [LICENSE](../../fracpaq-matlab/LICENSE) | Licença MIT e autoria dos contribuidores; preservar atribuições aplicáveis. |
| [index.html](../../fracpaq-matlab/index.html) | Página institucional estática, GitHub, downloads ZIP/TAR.GZ e créditos; texto histórico menciona 1.6. |
| [params.json](../../fracpaq-matlab/params.json) | Metadados de regeneração da página; texto histórico menciona 2.0; não é configuração da GUI. |
| [javascripts/main.js](../../fracpaq-matlab/javascripts/main.js) | Somente console.log; nenhuma análise ou interação funcional da aplicação. |
| [stylesheets/normalize.css](../../fracpaq-matlab/stylesheets/normalize.css) | Normalização de estilos HTML entre navegadores. |
| [stylesheets/stylesheet.css](../../fracpaq-matlab/stylesheets/stylesheet.css) | Tema do site, botões, tipografia, tabelas e ajustes responsivos. |
| [stylesheets/github-light.css](../../fracpaq-matlab/stylesheets/github-light.css) | Realce de sintaxe no site e licença própria do GitHub. |
| [stylesheets/print.css](../../fracpaq-matlab/stylesheets/print.css) | Tema de impressão, formatação e ocultação de downloads; arquivo existe, mas index.html não o referencia. |

### 15.3 Exemplos TXT — 41 arquivos

“Linhas” conta registros não vazios; “colunas” conta coordenadas por registro, sem vazios finais. Tabulação é o formato esperado pelo leitor GUI. Os exemplos com vírgulas requerem conversão/seleção de delimitador; a presença de `.txt` não garante compatibilidade direta.

| Arquivo | Linhas | Colunas mín.–máx. | Estrutura / finalidade |
| --- | ---: | --- | --- |
| [102.txt](../../fracpaq-matlab/102.txt) | 471 | 4–4 | Coordenadas de exemplo; tabulações |
| [103.txt](../../fracpaq-matlab/103.txt) | 610 | 4–4 | Coordenadas de exemplo; tabulações |
| [166.txt](../../fracpaq-matlab/166.txt) | 224 | 4–28 | Coordenadas de exemplo; tabulações |
| [69.txt](../../fracpaq-matlab/69.txt) | 698 | 4–46 | Coordenadas de exemplo; tabulações |
| [83.txt](../../fracpaq-matlab/83.txt) | 426 | 4–58 | Coordenadas de exemplo; tabulações |
| [Fractures_H12Z.txt](../../fracpaq-matlab/Fractures_H12Z.txt) | 2161 | 4–58 | Lâmina/fraturas H12Z; tabulações |
| [IYXtest1_converted.txt](../../fracpaq-matlab/IYXtest1_converted.txt) | 13 | 4–6 | Caso pequeno de conectividade; tabulações |
| [IYXtest2_converted.txt](../../fracpaq-matlab/IYXtest2_converted.txt) | 13 | 4–6 | Caso pequeno de conectividade; tabulações |
| [SD11A.txt](../../fracpaq-matlab/SD11A.txt) | 445 | 4–38 | Coordenadas de exemplo; tabulações |
| [SD11B.txt](../../fracpaq-matlab/SD11B.txt) | 660 | 4–44 | Coordenadas de exemplo; tabulações |
| [Souter_All.txt](../../fracpaq-matlab/Souter_All.txt) | 2792 | 4–52 | Conjunto Souter, agregado ou separado por cor; tabulações |
| [Souter_Blue.txt](../../fracpaq-matlab/Souter_Blue.txt) | 2561 | 4–36 | Conjunto Souter, agregado ou separado por cor; tabulações |
| [Souter_Green.txt](../../fracpaq-matlab/Souter_Green.txt) | 177 | 4–46 | Conjunto Souter, agregado ou separado por cor; tabulações |
| [Souter_Green_colour008000.txt](../../fracpaq-matlab/Souter_Green_colour008000.txt) | 177 | 4–46 | Conjunto Souter, agregado ou separado por cor; tabulações |
| [Souter_Red.txt](../../fracpaq-matlab/Souter_Red.txt) | 54 | 4–52 | Conjunto Souter, agregado ou separado por cor; tabulações |
| [ThinSection_H12Z.txt](../../fracpaq-matlab/ThinSection_H12Z.txt) | 1687 | 2–50 | Lâmina/fraturas H12Z; contém 30 registros curtos/ímpares e 21 tokens não numéricos; vírgulas |
| [ThinSection_H12Zconverted.txt](../../fracpaq-matlab/ThinSection_H12Zconverted.txt) | 1664 | 4–50 | Lâmina/fraturas H12Z; tabulações |
| [Tile 1 No BG.txt](../../fracpaq-matlab/Tile%201%20No%20BG.txt) | 3028 | 4–34 | Mapa de tile e variante sem fundo; tabulações |
| [Tile 1.txt](../../fracpaq-matlab/Tile%201.txt) | 3028 | 4–34 | Mapa de tile e variante sem fundo; tabulações |
| [Tile 4 No BG.txt](../../fracpaq-matlab/Tile%204%20No%20BG.txt) | 2225 | 4–66 | Mapa de tile e variante sem fundo; tabulações |
| [Tile 4.txt](../../fracpaq-matlab/Tile%204.txt) | 2225 | 4–66 | Mapa de tile e variante sem fundo; tabulações |
| [leftsideFaults.txt](../../fracpaq-matlab/leftsideFaults.txt) | 544 | 4–16 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [leftsideFaults2.txt](../../fracpaq-matlab/leftsideFaults2.txt) | 540 | 4–16 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [leftsideFaults_converted.txt](../../fracpaq-matlab/leftsideFaults_converted.txt) | 544 | 4–34 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [leftsideFaultsconverted.txt](../../fracpaq-matlab/leftsideFaultsconverted.txt) | 544 | 4–34 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [leftsideJoints.txt](../../fracpaq-matlab/leftsideJoints.txt) | 450 | 4–20 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [leftsideJointsconverted.txt](../../fracpaq-matlab/leftsideJointsconverted.txt) | 450 | 4–24 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [map1_edit_converted.txt](../../fracpaq-matlab/map1_edit_converted.txt) | 2123 | 4–62 | Mapa convertido ou subconjunto de teste; tabulações |
| [map1_edit_converted2.txt](../../fracpaq-matlab/map1_edit_converted2.txt) | 10 | 4–4 | Mapa convertido ou subconjunto de teste; tabulações |
| [map7_converted.txt](../../fracpaq-matlab/map7_converted.txt) | 4093 | 4–76 | Mapa convertido ou subconjunto de teste; tabulações |
| [map7_edit_converted.txt](../../fracpaq-matlab/map7_edit_converted.txt) | 4092 | 4–76 | Mapa convertido ou subconjunto de teste; tabulações |
| [method b1.txt](../../fracpaq-matlab/method%20b1.txt) | 79 | 4–10 | Conjunto comparativo de exemplo; tabulações |
| [method b2.txt](../../fracpaq-matlab/method%20b2.txt) | 148 | 4–14 | Conjunto comparativo de exemplo; tabulações |
| [rightsideFaults.txt](../../fracpaq-matlab/rightsideFaults.txt) | 370 | 4–16 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [rightsideFaultsconverted.txt](../../fracpaq-matlab/rightsideFaultsconverted.txt) | 370 | 4–34 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [rightsideJoints.txt](../../fracpaq-matlab/rightsideJoints.txt) | 389 | 4–18 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [rightsideJointsconverted.txt](../../fracpaq-matlab/rightsideJointsconverted.txt) | 389 | 4–28 | Traços de falhas/juntas e variantes convertidas; tabulações |
| [souter_all_colour24378D.txt](../../fracpaq-matlab/souter_all_colour24378D.txt) | 2561 | 4–36 | Conjunto Souter, agregado ou separado por cor; vírgulas |
| [souter_all_colour5BB030.txt](../../fracpaq-matlab/souter_all_colour5BB030.txt) | 177 | 4–46 | Conjunto Souter, agregado ou separado por cor; vírgulas |
| [souter_all_colourE42A12.txt](../../fracpaq-matlab/souter_all_colourE42A12.txt) | 54 | 4–52 | Conjunto Souter, agregado ou separado por cor; vírgulas |
| [souter_all_mytest.txt](../../fracpaq-matlab/souter_all_mytest.txt) | 177 | 4–46 | Conjunto Souter, agregado ou separado por cor; vírgulas |

### 15.4 Exemplos SVG — 14 arquivos

Contagens abaixo descrevem os elementos no XML, não garantem que todos sejam importados. Paths podem usar comandos não aceitos; `polygon` não tem fechamento garantido pelo conversor atual. Grupos, transformações e imagens incorporadas não equivalem a suporte integral SVG.

| Arquivo | Elementos relevantes encontrados | Observação |
| --- | --- | --- |
| [ThinSection_H12Z.svg](../../fracpaq-matlab/ThinSection_H12Z.svg) | line: 732, polyline: 934, path: 121 | Exemplo de entrada vetorial |
| [ThinSection_H12Z_new.svg](../../fracpaq-matlab/ThinSection_H12Z_new.svg) | line: 732, polyline: 934, path: 121 | Exemplo de entrada vetorial |
| [Tile 1 No BG copy.svg](../../fracpaq-matlab/Tile%201%20No%20BG%20copy.svg) | line: 1787, polyline: 1466, path: 25, g: 2 | Exemplo de entrada vetorial |
| [Tile 1 No BG.svg](../../fracpaq-matlab/Tile%201%20No%20BG.svg) | line: 1787, polyline: 1466, path: 25, g: 2 | Exemplo de entrada vetorial |
| [Tile 4 No BG.svg](../../fracpaq-matlab/Tile%204%20No%20BG.svg) | line: 1183, polyline: 1045, path: 29, polygon: 1, g: 2 | Exemplo de entrada vetorial |
| [blocksizetest.svg](../../fracpaq-matlab/blocksizetest.svg) | line: 7, polyline: 2, path: 2 | Exemplo pequeno para blocos |
| [leftsideFaults.svg](../../fracpaq-matlab/leftsideFaults.svg) | line: 268, polyline: 276, path: 113, g: 2, image: 1 | Contém imagem incorporada além dos traços |
| [leftsideJoints.svg](../../fracpaq-matlab/leftsideJoints.svg) | line: 278, polyline: 172, path: 1, g: 2, image: 1 | Contém imagem incorporada além dos traços |
| [map1.svg](../../fracpaq-matlab/map1.svg) | line: 1293, polyline: 830, polygon: 1, g: 1 | Exemplo de entrada vetorial |
| [map1_edit.svg](../../fracpaq-matlab/map1_edit.svg) | line: 1293, polyline: 830, g: 1 | Variante editada de mapa |
| [map7.svg](../../fracpaq-matlab/map7.svg) | line: 1616, polyline: 2476, polygon: 1, g: 1 | Exemplo de entrada vetorial |
| [map7_edit.svg](../../fracpaq-matlab/map7_edit.svg) | line: 1616, polyline: 2476, g: 1 | Variante editada de mapa |
| [rightsideFaults.svg](../../fracpaq-matlab/rightsideFaults.svg) | line: 182, polyline: 188, path: 3, g: 2, image: 1 | Contém imagem incorporada além dos traços |
| [rightsideJoints.svg](../../fracpaq-matlab/rightsideJoints.svg) | line: 243, polyline: 146, path: 4, g: 2, image: 1 | Contém imagem incorporada além dos traços |

### 15.5 Imagens — 15 arquivos

| Arquivo | Dimensões | Papel identificado |
| --- | --- | --- |
| [FracPaQicon.jpeg](../../fracpaq-matlab/FracPaQicon.jpeg) | 119×120 | Ícone da janela principal |
| [FracPaQlogo.jpeg](../../fracpaq-matlab/FracPaQlogo.jpeg) | 367×84 | Logotipo da janela principal |
| [Macduff.tiff](../../fracpaq-matlab/Macduff.tiff) | 256×256 | Imagem de exemplo Macduff/Orkney em cores; requer preparação para Hough |
| [MacduffBinary.tif](../../fracpaq-matlab/MacduffBinary.tif) | 256×256 | Exemplo em cinza de 8 bits para entrada Hough |
| [MacduffColour.tif](../../fracpaq-matlab/MacduffColour.tif) | 263×258 | Imagem de exemplo Macduff/Orkney em cores; requer preparação para Hough |
| [MacduffColourCropped.jpg](../../fracpaq-matlab/MacduffColourCropped.jpg) | 263×258 | Foto usada pelo script de pré-processamento |
| [Orkney1a.jpg](../../fracpaq-matlab/Orkney1a.jpg) | 512×512 | Imagem de exemplo Macduff/Orkney em cores; requer preparação para Hough |
| [Orkney1a.tiff](../../fracpaq-matlab/Orkney1a.tiff) | 512×512 | Imagem de exemplo Macduff/Orkney em cores; requer preparação para Hough |
| [Orkney1aBinary.tif](../../fracpaq-matlab/Orkney1aBinary.tif) | 512×512 | Exemplo em cinza de 8 bits para entrada Hough |
| [images/body-bg.jpg](../../fracpaq-matlab/images/body-bg.jpg) | 175×175 | Textura de fundo do site |
| [images/download-button.png](../../fracpaq-matlab/images/download-button.png) | 202×78 | Arte de botão de download do site |
| [images/github-button.png](../../fracpaq-matlab/images/github-button.png) | 202×80 | Arte de botão GitHub do site |
| [images/header-bg.jpg](../../fracpaq-matlab/images/header-bg.jpg) | 80×800 | Fundo de cabeçalho do site |
| [images/highlight-bg.jpg](../../fracpaq-matlab/images/highlight-bg.jpg) | 960×573 | Fundo de destaque do site |
| [images/sidebar-bg.jpg](../../fracpaq-matlab/images/sidebar-bg.jpg) | 102×504 | Fundo de barra lateral do site |

### 15.6 Observações de completude e arquivos referenciados ausentes

- A distribuição analisada soma **82 MATLAB + 12 interfaces/documentação/site + 41 TXT + 14 SVG + 15 imagens = 164 arquivos**.
- Alguns scripts se referem a recursos que não estão no pacote: `guiFracPaQ2Dtabbed.fig`, `guiFracPaQ2Dtracemap2.m`, `cmocean.png`, `Fractures_H12Z.tif`, `test.jpg` e o exemplo externo `DAT/S2.dat`. São dependências ausentes de caminhos auxiliares/legados, não novos arquivos analisados.
- `plotMohr.m` declara `plotMohr2D`, `testCM.m` declara `newCM` e alguns ensaios chamam assinaturas antigas; não considerar todos os scripts imediatamente executáveis.
- Os dados de exemplo têm sobreposições e versões convertidas; nomes semelhantes não comprovam igualdade de geometria nem resultado de referência validado.
- O manual contém bibliografia, orientações de uso e recomendações de digitalização; procedimentos realizados em Illustrator/CorelDRAW/Inkscape/Move não são botões ou ferramentas internas do FracPaQ.
