# PRD — PyFracPaQ: clone desktop do FracPaQ 2.8 em Python

Vou desenvolver o **PyFracPaQ**, um programa científico local em Python para quantificação de padrões de fraturas em duas dimensões. O produto deverá reproduzir o **FracPaQ MATLAB 2.8**, com as mesmas telas, organização visual, entradas, controles, parâmetros, análises e arquivos de saída, incluindo figuras com o estilo das figuras MATLAB do programa original.

A aplicação será iniciada pelo Python, pelo terminal ou pelo VS Code e abrirá janelas desktop. A entrega será código Python executável em ambiente virtual local, com instalação documentada e funcionamento offline após a instalação das dependências.

**Versão deste PRD:** 1.0 — 13/11/2026. **Estado:** Sprints 0 a 15 implementadas; referências, geometria, TXT/SVG/cores, imagens/Hough, janela desktop, mapas/P21/P20, Angles, Lengths/MLE, conectividade, crack tensors, permeabilidade e estabilidade/Mohr. Q-11/Q-15/Q-17 aprovadas explicitamente pelo usuário e integradas ao Run padrão. Sprints 12/13: blocos, variograma e todos os perfis ALONG/FROM integrados ao Run; Q-14 e extensão P20 de Q-20 aprovadas explicitamente pelo usuário. Sprints14/15: Wavelets2D com Q-12 aprovada, ferramentas locais/APIs complementares e destinação dos19AUX/164arquivos concluídas. Homologação integral permanece pendente na Sprint16, inclusive votos/picos/endpoints Hough. Evidências em [Sprint 0](../parity/sprint-0.md), [Sprint 1](../parity/sprint-1.md), [Sprint 2](../parity/sprint-2.md), [Sprint 3](../parity/sprint-3.md) e [Sprint 4](../parity/sprint-4.md). **Referência funcional:** FracPaQ 2.8 / 2.8.0, março de 2021.

Este documento segue a estrutura do [prd-bruto.md](../../prd-bruto.md): especificações técnicas, requisitos funcionais, requisitos não funcionais, guia de execução e sprints detalhadas em checklist. As tecnologias e os requisitos de corretora/SaaS daquele exemplo não fazem parte deste produto.

**Guia de leitura:** as especificações definem a stack e a arquitetura; RF-01 a RF-10 incorporam o inventário; RF-11 a RF-14 detalham fidelidade visual, algoritmos e arquivos; as seções seguintes definem qualidade, instalação local, sprints e conclusão do produto.

O [FUNCIONALIDADES_FRACPAQ.md](FUNCIONALIDADES_FRACPAQ.md) é a base de rastreabilidade deste PRD e inventaria os 164 arquivos da distribuição. Seus IDs `UI`, `IN`, `MAP`, `LEN`, `ANG`, `FLO`, `WAV`, `GRA`, `EXP`, `AUX` e `Q` são preservados neste documento. Os códigos e o layout em [fracpaq-matlab](../../fracpaq-matlab) permanecem como referência de implementação.

## Objetivo, usuários e resultado esperado

- Atender pesquisadores, geólogos, estudantes e profissionais que usam mapas de fraturas e precisam executar as análises do FracPaQ sem depender de MATLAB na operação do programa.
- Permitir que um usuário familiarizado com o FracPaQ encontre os mesmos controles nos mesmos grupos e execute a mesma sequência de trabalho.
- Reproduzir a janela principal, as seis abas e as janelas de resultados; não substituir a experiência por um dashboard ou por um formulário genérico.
- Produzir dados numéricos equivalentes e figuras visualmente equivalentes, com nomes, unidades, cores, escalas e convenções verificadas.
- Oferecer documentação de instalação, execução pelo terminal/VS Code e rastreabilidade de qualquer diferença deliberada em relação ao original.
- Considerar a entrega principal completa somente após cobrir **todas as funcionalidades integradas à GUI 2.8**, e não apenas uma primeira versão com algumas abas.

## Escopo do produto

| Obrigatório na entrega principal | Complementar, com tratamento explícito | Fora do escopo |
| --- | --- | --- |
| Janela principal, Maps, Lengths, Angles, Fluid flow, Wavelets e Graphs; entradas TXT/SVG/imagem; arquivos e figuras da GUI | Utilitários de pré-processamento e Move; bibliotecas e recursos auxiliares identificados por AUX | SaaS, contas, autenticação, assinaturas, multitenancy, pagamentos, servidores e deploy em VPS |
| Execução local por Python e VS Code; cálculos no próprio computador | API Python para os cálculos e ferramentas de desenvolvimento/validação | Django, FastAPI, React, Streamlit, Dash, Electron, banco de dados obrigatório, Celery, Redis e RabbitMQ |
| Fidelidade funcional, numérica, visual e de arquivos | Recursos experimentais preservados/documentados sem novos controles na tela principal | IA, solução de fluxo 3D, pressão/vazão/transporte, edição completa de traços, GIS e formatos adicionais sem decisão de escopo |

# TECH SPECS DO SISTEMA

## 1. Linguagem, ambiente e bibliotecas

- Usar **CPython 3.13.x**, com o patch exato registrado no início da implementação. Compatibilidade com versões posteriores só poderá ser anunciada depois de verificada.
- Usar ambiente virtual **`.venv` na raiz** do projeto.
- Manter `requirements.txt` na raiz, com versões exatas e compatíveis das dependências necessárias para executar a aplicação. Manter dependências de desenvolvimento em `requirements-dev.txt` e metadados em `pyproject.toml`.
- Resolver e congelar as versões na Sprint 0; não declarar números de releases como “últimos” sem verificação. Atualizações devem passar novamente pela validação científica e visual.
- Implementar o código em inglês, com PEP 8, type hints, nomes claros, funções pequenas e aspas simples como padrão.
- Escrever documentação de desenvolvimento e este PRD em português brasileiro. **Manter os textos da interface e dos gráficos em inglês, conforme o FracPaQ**, inclusive rótulos, abas e nomes das grandezas; a fidelidade ao original prevalece sobre a preferência de idioma do modelo de PRD.

| Biblioteca / recurso | Decisão técnica | Aplicação no produto |
| --- | --- | --- |
| **PySide6 / Qt Widgets** | Toolkit desktop principal | QMainWindow, grupos, checkboxes, radio buttons, campos, combos, diálogos, seleção de arquivos, janelas de resultados e progresso |
| **Matplotlib**, backend **QtAgg** | Motor único de figuras na GUI | Mapa de prévia, gráficos cartesianos, polares, ternários, heatmaps, painéis wavelet e diagnóstico Hough |
| **Matplotlib Agg** | Renderização sem janela para verificações e exportação controlada | Comparação de imagens e geração de figuras em testes; mesmas funções de desenho da GUI |
| **NumPy** | Base numérica em float64 | Coordenadas, comprimentos, ângulos, matrizes, autovalores, vetores e kernels |
| **SciPy** | Estatística e processamento numérico | FFT, distribuições, funções especiais, K-S, operações de imagem e leitura de MAT/FIG na preparação de referências |
| **scikit-image** | Primitivas de processamento e inspeção de imagens | Hough como base adaptável, morfologia, componentes conectados e propriedades de regiões; nunca presumir equivalência automática com funções MATLAB |
| **Pillow** | I/O de imagens e metadados | JPG/JPEG/TIF/TIFF/PNG, verificação de modo/profundidade, gravação e comparação de rasters |
| **defusedxml** | Leitura estruturada de SVG/XML | Interpretar o subconjunto geométrico suportado, sem executar conteúdo externo |
| Biblioteca padrão | `dataclasses`, `pathlib`, `logging`, `argparse`, `json`, `tempfile`, `importlib.resources` | Modelo, caminhos, console, entrypoints, recursos e arquivos temporários |
| **pytest / pytest-qt** | Ferramentas de desenvolvimento | Verificação numérica, controles Qt e fluxos; não são dependências científicas da instalação de execução |

**Justificativa da escolha:** Qt Widgets permite reproduzir o formulário desktop e seus grupos; o `QStackedWidget` permite mostrar um painel por vez, como no programa original. A integração oficial do Matplotlib com Qt suporta PySide6. O estilo final deve ser construído com `rcParams` e funções de desenho próprias, e não depender do tema padrão da máquina. Fontes técnicas: [Qt QStackedWidget](https://doc.qt.io/qtforpython-6.10/PySide6/QtWidgets/QStackedWidget.html), [Matplotlib em Qt](https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_qt_sgskip.html), [customização de figuras](https://matplotlib.org/stable/users/explain/customizing.html).

O Hough e o K-S são pontos de atenção: as APIs disponíveis têm parâmetros e comportamentos próprios; a camada de compatibilidade deverá ser validada contra o MATLAB. Fontes: [Hough no scikit-image](https://scikit-image.org/docs/stable/api/skimage.transform.html), [K-S de duas amostras no SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html). Para imagens e SVG: [formatos do Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html), [projeto defusedxml](https://github.com/tiran/defusedxml).

Essas fontes fundamentam a disponibilidade das bibliotecas; a escolha da arquitetura e a obtenção de paridade são decisões e trabalho deste projeto, não garantias fornecidas por elas.

## 2. Arquitetura e organização

- Separar modelo geométrico, importação, processamento científico, figuras, exportação e GUI.
- O cálculo científico não deve importar Qt nem depender de widgets ou variáveis globais da interface.
- A interface deve construir uma configuração de execução e receber resultados estruturados. A configuração deve ser fotografada no início de cada execução, impedindo que a edição de um campo altere um cálculo em andamento.
- Usar uma função de desenho por tipo de resultado; a mesma função deve alimentar a janela e a exportação.
- Manter um registro declarativo de análises que relacione checkbox, parâmetros, dependências, cálculo, figuras e arquivos. Não duplicar regras entre Preview, Run e testes.
- Os nomes de controles MATLAB devem ser preservados como `objectName` Qt ou ter um mapeamento explícito, para verificar cobertura de todos os controles `.fig`.
- Recursos da aplicação devem ser carregados em relação ao pacote, sem exigir que o diretório corrente contenha logos ou arquivos de tema.
- Preservar a pasta `fracpaq-matlab` sem modificações. Dados de exemplo utilizados em testes precisam ter origem e licença registradas.

Estrutura de referência para implementação:

```text
pyfracpaq/
  __init__.py
  __main__.py
  app.py
  domain/                 # Node, Segment, Trace, Dataset, configurações/resultados
  io/                     # TXT, SVG, imagens, validação e exportadores
  analysis/               # comprimentos, ângulos, mapas, tensores, perfis, wavelets
  geometry/               # interseções, distâncias, limites e centros
  compatibility/          # convenções MATLAB: índices, round, hist, Hough, K-S
  plots/                  # funções de desenho e composição de figuras
  gui/                    # janela principal, abas, controles e figuras
  workers/                # tarefas locais e sinais de progresso
  resources/              # logos, tema Qt, .mplstyle, paletas congeladas
  tools/                  # utilitários complementares por linha de comando
tests/
  fixtures/
  reference/              # dados e imagens de referência + sua procedência
  numerical/
  gui/
  visual/
docs/
  parity/                 # matriz de paridade e divergências
  decisions/              # decisões técnicas/científicas
scripts/                  # validação e captura de referências
run_gui.py
pyproject.toml
requirements.txt
requirements-dev.txt
README.md
LICENSE
THIRD_PARTY_NOTICES.md
```

A estrutura é prescritiva quanto à separação de responsabilidades; nomes de arquivos internos podem ser refinados sem alterar os contratos públicos ou a interface. Não criar módulos vazios apenas para cumprir a árvore.

## 3. Modelo geométrico e convenções

- `Node`: par X/Y e identificação estável.
- `Segment`: referência ao traço e aos nós inicial/final, comprimento, ângulo bruto, ponto médio e distâncias acumuladas no traço.
- `Trace`: lista ordenada de nós/segmentos, comprimento total, ponto na metade do comprimento percorrido e cor do conjunto.
- `Dataset`: traços, segmentos, limites, contagens, origem, modo de entrada, escala e cores; todos os leitores devem preencher o mesmo contrato.
- `AnalysisConfig`: opções e parâmetros das seis abas, norte, flips e tag.
- `RunContext`: diretório corrente de saída, configuração congelada e recursos temporários daquela execução.
- `AnalysisResult`: arrays calculados, estatísticas, definição das figuras e arquivos esperados; erros devem identificar a análise afetada.
- Diferenciar nós geométricos de nós topológicos I/Y/X. Não fundir nós de traços diferentes durante a importação.
- Comprimento de traço = soma dos segmentos; centro de traço = metade do caminho percorrido, e não centroide de todos os vértices.
- Escala vazia mantém pixels; escala positiva em pixels/metre divide as coordenadas antes dos cálculos. Áreas e permeabilidades devem usar a unidade derivada correspondente.
- Ângulo bruto deve seguir a convenção do original em relação ao Y positivo. Correção de norte e espelhamentos devem ser derivados desse ângulo, sem modificar a geometria original repetidamente.
- Não trocar `round` MATLAB por arredondamento NumPy sem tratar empates; não trocar `hist` MATLAB por `histogram` com classes diferentes; não perder a diferença entre centros de bins e bordas.
- Tratar explicitamente índices base 1/base 0, ordem de achatamento de matrizes, orientação linha/coluna, limites inclusivos e ordenação estável de registros.
- O perfil por distância perpendicular deve manter sinal; a representação axial deve preservar a duplicação de direções quando a rotina original a utiliza.

## 4. Processamento local e responsividade

- Usar `QObject` em `QThread`, com sinais para progresso, resultado e erro. Qt e criação/atualização de figuras interativas permanecem na thread principal.
- Executar somente uma análise de usuário por vez; desabilitar Run durante execução e impedir alteração efetiva dos parâmetros em uso.
- Hough, MLE, conectividade, blocos, variograma e wavelets devem informar andamento. Não usar Celery, broker ou serviço externo.
- Planejar vetorização e processamento em blocos para interseções e wavelets; não alocar matrizes quadráticas ou tensores gigantes sem estimar a memória.
- O tratamento de Exit durante uma operação deve encerrar apenas janelas e tarefas da aplicação. Não encerrar o terminal, o VS Code ou outros programas.
- Não adicionar botão Cancel à janela principal, pois ele não existe na referência. O diálogo wavelet auxiliar possui seu próprio Cancel e deverá preservá-lo quando implementado.
- A primeira entrega não exige aceleração por GPU ou paralelismo distribuído. Toda otimização deve preservar resultados e ordenação.

## 5. Política de fidelidade e tratamento de defeitos do original

- A referência principal é `guiFracPaQ2D.m` junto de `guiFracPaQ2D.fig`, versão 2.8. O manual e o inventário complementam a interpretação. `guiFracPaQ2Dtabbed.m` 2.2 não define a tela-alvo.
- “Clone” significa equivalência dos controles, interações, parâmetros, cálculos válidos, estilo e saídas verificadas. Não significa apenas usar as mesmas fórmulas em uma interface diferente.
- Manter os comportamentos observáveis da referência em entradas válidas, inclusive saídas acopladas e convenções específicas descritas nos requisitos.
- Não reproduzir perda de dados, exclusão de arquivos alheios, travamentos por variáveis indefinidas, leitura do caminho errado ou inconsistência de índices.
- Corrigir falhas de validação, I/O e integridade como exceções técnicas documentadas. Isso não autoriza alterar silenciosamente as fórmulas, amostragem, normalizações ou semântica angular.
- Quando um `Q-*` implicar mudança de resultado científico, primeiro reproduzir e registrar a diferença em `docs/parity/divergences.md`, com entrada, resultado original, resultado proposto, fundamento e impacto. A decisão deve ser aprovada antes de promover o comportamento alterado a padrão ou declarar paridade naquele item.
- Não criar dois modos científicos, novas abas ou seletores de “modo corrigido” sem necessidade validada. Pendências numéricas ficam visíveis na matriz de paridade.
- Preservar a grafia e os nomes de arquivos exigidos. A mensagem final deve informar PNG, pois esse é o formato executado por `guiPrint`, apesar de um texto antigo mencionar TIFF.
- Uma diferença deliberada pode ser aceita e registrada; nunca pode ser omitida para anunciar identidade que ainda não foi demonstrada.

# REQUISITOS FUNCIONAIS DO SISTEMA

## Fluxo principal obrigatório

1. Iniciar a aplicação local.
2. Selecionar ou digitar o arquivo, conferir o tipo e informar escala quando necessário.
3. Clicar **Preview**; verificar traços e os sete valores do painel de estatísticas.
4. Ajustar Flip X-axis / Flip Y-axis, parâmetros e saídas nas seis abas.
5. Informar **Filename tag for this run** e clicar **Run**.
6. Acompanhar o processamento, consultar figuras independentes, arquivos e mensagens no terminal.
7. Alterar parâmetros e executar novamente, ou clicar **Exit**.

As tabelas seguintes incorporam o contrato funcional do inventário. A coluna de comportamento descreve a referência a reproduzir; critérios que citam `Q-*` devem obedecer à política de divergências acima. Expressões “atual”, “original” ou “encontrado” referem-se ao MATLAB analisado, e não a código Python já implementado.


## RF-01 — Janela, controles gerais e estatísticas

**Dependências funcionais:** carregamento dos dados para liberar as análises.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
| --- | --- | --- | --- |
| UI-01 | Janela principal única | Referência GUIDE do tipo singleton, a reproduzir em Qt; entrada à esquerda, mapa de prévia ao centro e opções à direita | Abrir o programa e apresentar as três áreas sem duplicar a janela principal |
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
| UI-13 | Botão Exit | Referência chama `close all` e `close(gcf)`; no Python, fechar somente as janelas e tarefas pertencentes à aplicação | Encerrar a aplicação; decidir conscientemente o alcance de fechamento na migração |
| UI-14 | Mensagens de estado | Ready, instrução para Preview, leitura de nós, Hough, coleta de dados, Running e conclusão | Informar etapa corrente e término ou erro |
| UI-15 | Progresso e mensagens de erro | `waitbar`, `errordlg`, `msgbox`, foco no campo inválido e avisos de compatibilidade | Mostrar progresso nas operações longas e erro compreensível nas entradas inválidas |
| UI-16 | Filename tag for this run | Texto inicial `Run1`; convertido em sufixo `_Run1` para várias saídas | Identificar arquivos de execuções distintas, com exceções tratadas em EXP-03 |
| UI-17 | Figuras independentes | Mapas e gráficos abrem em janelas MATLAB próprias; rótulos, legendas, títulos, escalas e barras de cores variam por análise | Cada resultado identificável e exportável sem depender da prévia |
| UI-18 | Diagnóstico no Command Window | Versão, parâmetros de Hough, estatísticas, conectividade, MLE, permeabilidade e andamento wavelet | Disponibilizar essas informações em console ou painel de resultados |
| UI-19 | Dependências entre controles | Checkboxes habilitam opções subordinadas: nós, círculos, bins, MLE, tensões, abertura e wavelet | Reproduzir as dependências de cada grupo sem exigir campos irrelevantes; ver Q-01 |

Fontes: `guiFracPaQ2D.fig`; `guiFracPaQ2D.m:71–353`, `567–777`, `780–1422`, `1527–1548`, `1721–1783`, `1836–1910`, `2050–2136`, `2221–2343`.


## RF-02 — Entrada, geometria, cores e Hough

**Dependências funcionais:** base geométrica para todos os épicos analíticos.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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

### RF-02.1 — Valores iniciais e regras de referência

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


## RF-03 — Maps

**Dependências funcionais:** IN-01/IN-12 e geometria; orientação para cores por strike e estabilidade.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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


## RF-04 — Lengths

**Dependências funcionais:** modelo geométrico; centros de segmentos para variograma.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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


## RF-05 — Angles

**Dependências funcionais:** orientações e comprimentos dos segmentos. A correção de norte é compartilhada com outras análises.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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


## RF-06 — Fluid Flow

**Dependências funcionais:** geometria e interseções; orientação, comprimentos e área para os tensores.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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


## RF-07 — Wavelets

**Dependências funcionais:** traços carregados; rasterização interna; núcleos CWT e FFT.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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


## RF-08 — Graphs

**Dependências funcionais:** geometria, centros e linha escolhida com dois pontos.

| ID | Funcionalidade | Comportamento de referência | Critério de aceite |
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


## RF-09 — Arquivos de saída e impressão

| ID | Estado | Funcionalidade / comportamento de referência | Critério de aceite |
| --- | --- | --- | --- |
| EXP-01 | I | Exportação automática comum de figuras em **PNG a 600 dpi**, área de impressão 20×20 cm (`guiPrint`) | Figura exibida e arquivo exportado representarem o mesmo resultado |
| EXP-02 | I | Tag adicionada ao nome-base antes da extensão, usualmente `_Run1` | Identificar execução e manter nomes previsíveis |
| EXP-03 | I/P | Resultados comuns vão à pasta corrente; conversões SVG ficam junto à origem; alguns intermediários têm nome fixo | Documentar localização e aplicar política de sobrescrita/temporários na migração |
| EXP-04 | I | TXT numéricos de comprimento, orientação, campos P21/P20, conectividade, segmentos e wavelets | Preservar unidades, ordem, quantidade de linhas e significado de colunas |
| EXP-05 | A | Exemplos antigos gravam BMP/JPEG e arquivos sem tag; são saídas de scripts específicos | Não confundir esses formatos com a exportação principal |
| EXP-06 | P | Não foi encontrado projeto/sessão persistente, histórico de parâmetros ou relatório consolidado | Se necessário no produto futuro, criar histórias próprias, sem tratá-las como paridade existente |

### RF-09.1 — Catálogo obrigatório de nomes de figuras

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

### RF-09.2 — Catálogo obrigatório de dados e intermediários

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


## RF-10 — Recursos auxiliares, bibliotecas e legado

Todos os itens AUX precisam de uma destinação registrada. AUX-01 e AUX-02 serão ferramentas complementares locais. Bibliotecas necessárias aos requisitos I devem ser portadas. Experimentos e interfaces antigas ficam preservados/documentados e não devem acrescentar controles à GUI 2.8. Os estados da tabela são os do pacote original, não prioridades de implementação.

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

## RF-11 — Contrato visual da janela e dos controles

- A composição obrigatória é: **Input** no alto à esquerda; **Statistics for selected file** abaixo dele; mapa de prévia ao centro; seis botões de navegação e painel de opções à direita; tag, Run, Exit, versão e logo na área inferior; mensagens de estado no rodapé.
- Reproduzir as proporções do `.fig`: aproximadamente 16% da largura para a coluna de entrada, 43% para a área de mapa e 37% para os painéis da direita, mantendo os espaços e alinhamentos da referência. Medir as posições normalizadas diretamente no `.fig` na Sprint 0 e congelar a referência de layout.
- Usar botões **Maps**, **Lengths**, **Angles**, **Fluid flow**, **Wavelets** e **Graphs**, nessa ordem, acionando painéis em `QStackedWidget`. O estilo deve reproduzir a faixa de botões original, e não um sistema de navegação diferente.
- Usar `QGroupBox` para grupos, `QCheckBox` para opções, `QRadioButton` para escolhas exclusivas, `QComboBox` para listas e `QLineEdit` para campos, com validadores apropriados. Não trocar esses controles por switches, cards ou sliders.
- Usar tema claro determinístico via Qt Fusion e QSS próprio, calibrado com a referência. Impedir que o modo escuro do sistema altere as cores das telas e figuras.
- Preservar títulos dos grupos, ordem vertical dos campos, tooltips disponíveis, estados marcados/desmarcados e habilitação contextual. Cada controle funcional do `.fig` deve ter correspondência na matriz de paridade.
- Manter os sete valores do painel de estatísticas: mínimo X/Y, máximo X/Y, número de traços, segmentos e nós. O painel não deve virar uma tabela de análises extras.
- Inicialmente, nenhuma aba de saída deve ser acionável e Run deve estar desabilitado; Preview válido libera as opções e mostra Maps. As seleções padrão permanecem as da tabela RF-02.1.
- A troca de arquivo, tipo, escala ou parâmetros de extração deve invalidar o resultado da prévia e exigir sua reconstrução antes de Run, evitando usar dados antigos com rótulos novos.
- A escala visual do sistema operacional deve ser considerada em pixels lógicos; botões, campos e textos não podem se sobrepor em 100%, 125%, 150% ou 200% de escala de tela.
- A janela principal deve funcionar em um desktop de 1366×768 pixels lógicos e resoluções maiores. Por solicitação atualizada do usuário em 16/11/2026, abrir como janela normal com toda a largura disponível da tela, incluindo as bordas, e centralizada verticalmente. Manter a altura limitada à área útil, sem obrigar maximização ou tela cheia; permitir redimensionamento posterior. A calibração atual usa proporção cliente 1250×739 do manual e formulário mínimo 1000×591; abaixo disso, manter rolagem restrita à área necessária, preservando o mapa e a organização. Navegação sem borda externa, conforme BorderType=none do FIG. [Revisão visual de 14/11/2026](../parity/ui-calibration.md).
- Nas figuras independentes, permitir as ações usuais de zoom, pan, restauração e salvamento, com toolbar discreta. O conteúdo exportado não inclui a moldura nem a toolbar Qt.
- Preservar logos e atribuições do pacote conforme os recursos de origem; distinguir nos metadados/documentação a versão do port Python da versão FracPaQ de referência. Não inventar recursos de contato ou versões futuras do original.

## RF-12 — Contrato do estilo das figuras MATLAB

- Criar `resources/fracpaq_matlab.mplstyle`, funções auxiliares de eixos, textos, legendas e barras de cor, e uma tabela de parâmetros por figura. “Usar Matplotlib” sozinho não atende ao requisito visual.
- Reproduzir os fundos das áreas de figura e dos eixos, box, grid, aspect ratio, margens, posicionamento de subplots e espaço destinado a títulos/legendas.
- Extrair/calibrar tamanhos de fonte, peso, ticks, notação científica, offsets, linhas, tracejados, bordas e tamanhos de marcadores. Não aplicar estilos Seaborn ou temas genéricos.
- Preferir a fonte da referência capturada, registrando seu nome. Caso não esteja instalada em uma plataforma, selecionar fallback explícito e registrar a variação; validar o ambiente de referência com a mesma fonte. Não redistribuir fontes sem permissão.
- Reproduzir rótulos em inglês, símbolos gregos, índices, expoentes, unidades, títulos em múltiplas linhas e caixas de parâmetros dos ajustes. Usar MathText quando necessário, sem exigir instalação de LaTeX.
- Congelar no pacote as tabelas RGB necessárias da distribuição original, com atribuições. Incluir as 18 famílias de cmocean quando portar a biblioteca AUX-08; para a GUI, priorizar exatamente haline, phase e thermal.
- Também calibrar as paletas MATLAB utilizadas nas rotinas: jet, hot e sua inversão, bone e demais mapas efetivamente necessários. Paletas de nomes iguais entre bibliotecas não devem ser presumidas numericamente idênticas.
- Nos mapas geométricos, manter eixos com proporção igual, espessura de linha de referência e limites correspondentes ao domínio. Nos gráficos quadrados, manter `axis square` quando usado no MATLAB.
- Nos histogramas com dois eixos Y, manter frequência absoluta à esquerda e percentual à direita, com a mesma amostra e bins.
- Nas rosas, implementar os polígonos e círculos percentuais do original. A rosa de área igual deve ter área proporcional à frequência; não substituí-la por barras polares padrão com outro desenho.
- Nas rosas de estabilidade, manter cores, linha vermelha da direção de σ1, bin próprio de 10° e legenda da grandeza. No ternário, manter posições I/Y/X, malha de 10% e linhas CL.
- Nos tensores/permeabilidade, manter norte no topo e sentido horário quando a rotina original o define. Não trocar polos de fraturas por strikes.
- Nos heatmaps, preservar orientação da matriz, extensão espacial, ticks e posição inferior das barras de cor. Nos comprimentos, revisar o acoplamento entre índice de cor e barra logarítmica conforme Q-17 antes de alterar o resultado.
- Em **todas as figuras atuais e futuras**, a barra de cores horizontal deve coincidir com os extremos horizontais da área real do plot; a vertical, com seus extremos verticais. A igualdade de comprimento/altura deve permanecer ao ampliar, reduzir e exportar a figura, após o ajuste do aspecto dos eixos. Manter também folga fixa em pontos entre a barra e os rótulos do eixo, sem variar com o tamanho da janela; em figuras pequenas, reservar espaço no layout sem sobrepor a barra ao label ou ao plot. Usar a fábrica compartilhada `pyfracpaq.plots.colourbars.colourbar`; não fixar retângulos independentes para a barra. [Contrato de barras responsivas](../decisions/0009-responsive-colourbars.md).
- Nos gráficos de Graphs, manter os marcadores e os limites dos eixos da referência, o sinal da distância FROM e a identificação dos pontos da linha.
- Em Hough, manter os quatro painéis: imagem e vistas do acumulador/plano de limiar; não entregar apenas uma sobreposição de linhas na foto.
- Em wavelets, preservar a figura 2×2 por escala: raster de entrada, mapa WC, rosa de orientações ótimas e histograma com frequência log10.
- Exportar PNG com resolução de **600 dpi** e geometria de impressão de **20×20 cm**, como `guiPrint`. Isso corresponde a aproximadamente 4724 pixels por lado; a dimensão raster final deve ser congelada a partir de arquivos MATLAB de referência.
- Não usar `bbox_inches='tight'`, `tight_layout` ou layout automático que mude as margens sem comparação com a referência. Figuras na tela e figuras exportadas podem ter DPIs diferentes, mas devem manter composição e conteúdo.
- Figuras devem ser criadas a partir dos arrays de resultado, e não como screenshots dos widgets. Antialiasing e renderização de texto podem diferir entre motores; a aceitação visual exige a comparação por regiões definida adiante, não identidade binária dos PNG.

## RF-13 — Compatibilidade dos algoritmos

### RF-13.1 — Hough e imagens

- Preservar o intervalo de theta de −90° até 89,5°, com passo de 0,5°, e a resolução de rho de 1 pixel.
- Reproduzir o cálculo de limiar por `ceil(fator × max(H))`, limite de picos, supressão de vizinhança e critérios de desempate, rastreamento de pixels, união por FillGap e corte por MinLength.
- Estabelecer a adaptação de origem/base de coordenadas entre MATLAB e arrays Python. A implementação deve testar o mesmo pixel em ambos os sistemas antes de gerar nós.
- Não substituir o fluxo por `probabilistic_hough_line` ou por outra detecção estocástica e declarar equivalência. Se `hough_line`/`hough_line_peaks` não reproduzirem o original, implementar a parte divergente na camada de compatibilidade.
- Preservar a validação de imagem em escala de cinza de 8 bits. Não converter silenciosamente uma imagem RGB selecionada na GUI; o utilitário AUX-01 faz a preparação fora desse fluxo.
- Reproduzir o complemento e a limpeza morfológica com a mesma vizinhança. Para outros operadores, explicitar conectividade, bordas e critério de convergência.

### RF-13.2 — Estatística, amostragem e topologia

- Portar as equações dos arquivos `fitting*`, `KStest*` e `Plot*`; não substituir a metodologia por uma chamada genérica `.fit()` do SciPy.
- Validar a semântica dos cortes percentuais, tratamento de zeros, valores repetidos, busca de xmin, estatística K-S e gráficos da distribuição acumulada.
- Preservar 2500 comparações sintéticas por modelo. Registrar a diferença original de significância da lei de potência (0,1 no teste e 0,05 em outra contagem) e das demais (0,05); mudanças dependem da decisão Q-15.
- Controlar `method` e hipótese alternativa do K-S em vez de depender de `auto`. Comparar o valor de D e o p-valor com referências compartilhadas.
- Usar gerador aleatório local à análise e semente controlável por API/testes. A mesma semente numérica em bibliotecas diferentes não garante as mesmas amostras: para comparação exata, usar os mesmos vetores sorteados salvos nas fixtures.
- Reproduzir círculos, posições, raios e ordem de exportação de P21/P20. Validar linhas horizontais, verticais, diagonais, tangentes e translações do domínio.
- Reproduzir classificação e limpeza I/Y/X; tratar explicitamente redes sem interseções e classes ausentes. Não promover a interpretação “snap geral” a algoritmo novo sem resolver Q-11.
- No cálculo de blocos, preservar a etapa de rasterização e sua influência na área. Não trocar por poligonização vetorial durante a paridade.
- Portar semivariograma, pares, classes e contagem de contribuições a partir da rotina original, sem adicionar ajuste de curva à GUI.

### RF-13.3 — Tensores, estabilidade e wavelets

- Portar os tensores pelas mesmas potências de comprimento, direções de polos, normalização por área e projeções; conferir simetria e autovalores.
- Preservar abertura fixa/escalada, o fator λ e a dependência cúbica da abertura. Não modelar matriz rochosa ou escoamento resolvido como funcionalidade adicional.
- Na estabilidade, manter tensões, orientação, coesão, atrito e pressão de poros, com os limites e as decisões de normalização documentados. Evitar divisão por zero e índices de cor fora do intervalo.
- Implementar diretamente os núcleos anisotrópicos Morlet e Mexican Hat dos arquivos de origem, usando NumPy/SciPy para FFT, padding e convolução. Uma wavelet 1D padrão de PyWavelets não equivale à CWT 2D utilizada aqui.
- Preservar remoção da média, parâmetros de rotação, L recíproco, resposta self, normalização por a, fator 2.5, maximização e corte em 50% do máximo.
- O raster wavelet faz parte do algoritmo: preservar dimensões, margens, espessuras, inversão e a regra de espessura de 45% do maior traço. Similaridade apenas do gráfico final não é suficiente para aceitar coeficientes diferentes.
- Testar mapas retangulares, limites da amostragem angular e arrays vazios. No contrato de paridade inicial, wavelets continua em pixels e sem correção de norte adicional, pois a rotina original não recebe esses parâmetros.

## RF-14 — Contrato de arquivos e efeitos da execução

- O catálogo RF-09 é obrigatório: preservar prefixos, capitalização, grafia, presença/ausência de `_`, tags e relação entre seleção e arquivo gerado.
- Por padrão, usar o **diretório corrente de execução** para as figuras/dados, conforme o original. Conversões SVG devem ficar junto ao SVG de origem. Assets e módulos não devem depender desse diretório.
- A tag `Run1` produz `_Run1`; digitar outra tag deve manter a mesma regra. Validar a tag para que seja nome de arquivo, sem permitir que contenha um caminho; não alterar seu texto silenciosamente.
- Reexecutar com a mesma tag mantém os mesmos nomes e substitui as saídas correspondentes, como no programa original. Escrever arquivos finais de forma atômica quando possível e registrar substituição no terminal, sem acrescentar uma etapa obrigatória ao fluxo.
- Preservar, quando gerados pela interface, os intermediários `FracPaQ2D_blocksize.bmp` e `FracPaQ2D_wavelet_traces.png`. Arquivos internos de trabalho devem ser exclusivos da execução; impedir duas execuções concorrentes no mesmo destino de nomes fixos.
- Não excluir arquivos de outra execução ou outros `*_converted.txt` da pasta. A limpeza deve se restringir aos temporários que a própria operação criou.
- Preservar o esquema dos TXT: quantidade e ordem de colunas, separador, precisão, ordenação e cabeçalhos ou ausência deles, conforme cada `fprintf` original. Pontos decimais devem ser independentes da configuração regional.
- Para os comprimentos exportados com `%6.2f`, preservar duas casas e ordenação. Para dados de segmento, preservar os campos sequencial/X1/Y1/X2/Y2/ângulo e a precisão definida no fonte. Para SVG convertido, preservar oito casas conforme o conversor atual.
- Não uniformizar todos os TXT num formato CSV novo nem adicionar colunas de metadados aos arquivos legados. Informações de diagnóstico podem ir para o terminal e, em desenvolvimento, para artefatos separados de comparação.
- Manter o TXT de ângulos EZROSE com duplicação axial e ordenação. A distinção dos TXT com ângulos originais deve seguir Q-10; não alinhar convenções sem registrar a diferença.
- Manter efeitos acoplados da referência: Maps P21/P20 escreve ambos os TXT quando uma dessas estimativas é pedida; Graphs P21/P20 produz os dois gráficos; o crack tensor passa pela rotina que grava EZROSE.
- Não gerar todos os arquivos incondicionalmente: cada saída deve respeitar seu gatilho original, inclusive os efeitos acoplados documentados.
- Não exigir salvamento de projeto, relatório PDF, conta ou conexão para gerar os resultados existentes.

# REQUISITOS NÃO FUNCIONAIS DO SISTEMA

## RNF-01 — Fidelidade e precisão

- A aplicação deverá ser validada em quatro eixos independentes: **funcional**, **numérico**, **visual** e **compatibilidade dos arquivos**. Um eixo aprovado não compensa falha no outro.
- Todas as 118 funcionalidades `UI/IN/MAP/LEN/ANG/FLO/WAV/GRA` devem ter evidência de cobertura; `EXP` e os 19 `AUX` devem ter destinação rastreável. Os 21 itens `Q` devem ter análise e decisão registrada.
- Não marcar uma aba como concluída quando existir botão/checkbox sem ação, resultado fictício, função vazia, gráfico de demonstração ou exportação sem dados reais.
- A referência inicial é o programa fornecido; a falta de MATLAB na máquina de implementação não autoriza alegar equivalência numérica já demonstrada.

## RNF-02 — Desempenho e uso de recursos

- A GUI deve permanecer responsiva durante os cálculos e atualizar progresso sem bloquear o ciclo de eventos.
- Após confirmar o início de uma tarefa, atualizar o estado visual em até 200 ms em condições normais; em processamento prolongado, emitir progresso pelo menos a cada 2 s ou por etapa cuja duração seja conhecida.
- Estabelecer na Sprint 0 uma máquina de referência, resolução de tela, versão de SO, CPU e RAM. Registrar tempo e pico de memória por operação e conjunto de dados.
- Usar como cenários reais, após verificar validade, conjuntos pequenos de IYX, `map1_edit_converted.txt`, `map7_edit_converted.txt` e dados Souter; para wavelets, controlar o tamanho do raster e a/L/ângulo.
- Não fixar promessa de tempo absoluto para todos os arquivos. O objetivo inicial é paridade de resultados com uso de memória viável; otimizações posteriores deverão registrar benchmark e diferenças.
- Para arquivos grandes, estimar memória antes de alocar pares de segmentos ou matrizes wavelet; se exceder o limite configurado internamente, terminar com diagnóstico, sem encerrar a aplicação inteira.

## RNF-03 — Integridade, reprodutibilidade e erros

- Uma prévia inválida não libera Run. Cancelar Browse preserva estado consistente, sem referência ao valor 0 como nome de arquivo.
- Não aplicar escala duas vezes, espelhamento duas vezes ou misturar parâmetros de uma execução com dados de outra.
- Manter a ordenação dos traços e segmentos e o vínculo entre comprimento, ângulo, cor e ponto médio.
- Avisos de arquivo/linha devem identificar o problema e evitar importação parcial silenciosa. O suporte ao SVG é um subconjunto explícito, sem aceitar curvas arbitrárias como linhas equivalentes.
- Usar exceções específicas e mensagens claras na interface/terminal; preservar traceback no log de diagnóstico quando ocorrer falha inesperada.
- Operações locais devem funcionar sem telemetria, conta, API paga ou acesso à internet durante os cálculos.
- Parsear listas a/L como números separados por espaços, sem `eval`, execução de código ou interpretação irrestrita de expressões Python/MATLAB.
- A aceitação de seeds e o registro de versões pertencem à API/validação; não acrescentar campos à GUI original apenas por conveniência técnica.

## RNF-04 — Portabilidade, manutenção e distribuição

- Suportar Windows, macOS e Linux com ambiente gráfico, validando ao menos uma máquina de cada sistema antes de anunciar suporte à release.
- O comportamento científico deve ser independente do sistema; diferenças de decoração nativa, renderização de fontes e DPI devem ser registradas nos testes visuais.
- Executar tanto `python run_gui.py` quanto `python -m pyfracpaq` a partir da raiz após instalação. A forma por módulo deve funcionar fora da raiz depois de instalação editável ou do pacote.
- Não exigir MATLAB, MATLAB Runtime, Octave, Docker, banco, Node.js ou navegador para executar o produto.
- Manter documentação local em Markdown: instalação, uso, arquitetura, convenções, paridade, dependências e limitações. Um site hospedado não é requisito da aplicação.
- Incluir testes científicos e de interface relevantes. A frase “não implementar testes” do modelo de outro sistema não é adotada neste PRD: a paridade científica é requisito verificável deste produto.
- Manter créditos e avisos dos recursos portados e dependências em `LICENSE`/`THIRD_PARTY_NOTICES.md`. Não substituir atribuições do código original por autoria exclusiva do port.
- Empacotamento em executável poderá ser uma entrega posterior; o critério obrigatório desta versão é execução pelo Python com dependências instaladas.

# QUALIDADE, PARIDADE E CRITÉRIOS DE ACEITE

## 1. Preparação das referências

- Criar uma matriz em `docs/parity/matrix.md`, com cada ID do inventário, localização do código Python, controle/entrada, fixture, arquivos esperados, estado e divergências.
- Capturar a janela inicial, a prévia e cada aba em um ambiente MATLAB de referência com versão, SO, escala de tela e fonte registrados. Usar o PDF e o `.fig` como apoio, sem tratá-los como substitutos de todas as capturas reais.
- Para cada tipo de figura, salvar o PNG original, os dados usados no desenho, os parâmetros da análise e sua origem. Manter dados intermediários para Hough, MLE, conectividade e CWT.
- A captura de referências pode ser feita em uma máquina com MATLAB durante desenvolvimento. **Não** é dependência da instalação final do usuário.
- Enquanto uma referência MATLAB não estiver disponível, verificar casos analíticos e a estrutura da implementação, mas marcar a comparação de paridade como pendente.

## 2. Critérios de comparação

| Área | Critério obrigatório |
| --- | --- |
| Controles e fluxo | Mesmos controles, rótulos, grupos, defaults, estados e efeitos de seleção; nenhuma opção sem implementação |
| Layout da GUI | Na resolução de referência, posições/tamanhos de grupos e controles com desvio de até 2 pixels lógicos, salvo decoração nativa documentada; sem cortes/sobreposições |
| Contagens e classificação | Mesma quantidade e ordem de traços/segmentos, bins, interseções, classes topológicas e decisões discretas nos casos de referência, salvo divergência científica aprovada |
| Geometria em float64 | Tolerância inicial `rtol=1e-10`; `atol=1e-12 × max(1, escala característica do domínio)`, por grandeza e unidade |
| Tensores/ajustes determinísticos | Tolerância inicial `rtol=1e-8`, com absoluto dimensional definido pela escala da grandeza; limiares/contagens discretos continuam exatos |
| CWT | Comparar coeficientes normalizados por escala com `rtol=1e-6`, `atol=1e-8`; seleção de ótimos e pixels de limiar deve ser conferida separadamente, incluindo empates |
| K-S/Monte Carlo | Com vetores sintéticos compartilhados, comparar D, p e decisões; sem vetores compartilhados, usar repetição estatística e não igualdade por seed |
| PNG | Mesmo nome, quantidade, dimensão/DPI de referência, títulos, eixos, cores, legendas, posições e significado dos dados |
| Aparência das figuras | Comparação por regiões de mapa, curvas, textos, legendas e barras, com SSIM inicial ≥0,98 em cada região gráfica comparável e revisão visual de diferenças; equivalência semântica de todos os textos é obrigatória |
| TXT | Esquema, quantidade de linhas, ordenação, nomes, separadores e precisão iguais ao contrato; números comparados antes e depois da formatação |
| Entradas | TXT com dois/vários nós, SVG simples/multicolorido e imagens compatíveis; nomes com espaços, acentos e arquivo fora do diretório corrente |

As tolerâncias numéricas são metas iniciais deste PRD e precisam ser congeladas por família de grandeza ao capturar as referências. Não afrouxá-las apenas para fazer um teste passar. O SSIM não pode ocultar um gráfico vazio, dados deslocados ou legenda errada; ele complementa os testes dos arrays e a inspeção por regiões. Diferenças de antialiasing só podem ser mascaradas por regra explícita e estreita, sem excluir dados ou textos inteiros da avaliação.

## 3. Casos mínimos de verificação

- Linha horizontal, vertical e oblíqua; polilinha de vários segmentos; nó repetido; traço degenerado; dados vazios e pares incompletos.
- Domínio com mínimos não nulos, coordenadas inteiramente negativas, escala aplicada e todas as combinações de Flip X/Flip Y/norte.
- Círculo com linha secante, tangente, extremidades dentro/fora e segmento totalmente interno; repetir após transladar o domínio.
- Redes com I isolados, Y exato, X, undershoot/overshoot, coincidência, classes ausentes e ausência total de cruzamentos.
- Distribuições sintéticas determinísticas para potência/exponencial/lognormal, zeros/repetidos, cortes extremos e amostra insuficiente.
- Padrão de fraturas unidirecional e isotrópico para tensores; abertura fixa/escalada; λ=0; valores de tensão/atrito degenerados.
- Perfil sem interseção, linha com dois pontos iguais, múltiplas interseções do mesmo traço, e distâncias FROM positivas/negativas.
- CWT com raster conhecido, padrão direcional, duas escalas, ambos os kernels, imagem retangular e passo angular incompatível.
- Execuções sucessivas com tags iguais/diferentes; falha de permissão no destino; atualização de parâmetros após Preview; Exit durante processamento.

## 4. Registro obrigatório de questões Q

Os itens abaixo são o backlog de investigação/correção do inventário. O encaminhamento da última coluna não substitui a aprovação de uma alteração científica prevista na política de fidelidade. Validar falhas operacionais e resultados separadamente.


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

# INSTALAÇÃO E EXECUÇÃO LOCAL

Este guia especifica a instalação que a implementação deverá entregar. Os arquivos de aplicação, requirements e ferramentas citados nos comandos serão produzidos nas sprints; a criação deste PRD não os implementa nem instala dependências.

## 1. Pré-requisitos

- CPython 3.13 instalado, com suporte a `venv` e `pip`.
- Desktop Windows, macOS ou Linux com ambiente gráfico. Terminal aberto na raiz do projeto.
- Internet somente para obter o código/dependências na instalação inicial; a operação científica deve funcionar offline.
- No Linux, disponibilizar as bibliotecas gráficas exigidas pelo wheel Qt e pelo plugin de plataforma utilizado. Diagnosticar falhas de xcb/Wayland pelas dependências efetivas do ambiente; os nomes dos pacotes variam por distribuição. Referência: [requisitos Qt para Linux](https://doc.qt.io/qt-6/linux-requirements.html).
- A documentação final deve registrar as versões de SO e arquitetura realmente verificadas e os requisitos gráficos da instalação testada.

## 2. macOS / Linux

Na raiz do projeto, com Python 3.13 disponível como `python3.13`:

```bash
python3.13 --version
python3.13 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e . --no-deps
.venv/bin/python run_gui.py
```

Forma alternativa de inicialização, usando a mesma instalação:

```bash
.venv/bin/python -m pyfracpaq
```

## 3. Windows / PowerShell

Na raiz do projeto, com Python 3.13 disponível pelo launcher `py`:

```powershell
py -3.13 --version
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe run_gui.py
```

Forma alternativa:

```powershell
.\.venv\Scripts\python.exe -m pyfracpaq
```

O uso direto do interpretador da `.venv` dispensa a ativação do ambiente no shell. A estrutura de `venv` e o uso dos interpretadores por plataforma seguem a [documentação do Python](https://docs.python.org/3.13/library/venv.html); a instalação final de Qt deve seguir o [guia PySide6](https://doc.qt.io/qtforpython-6/gettingstarted.html).

## 4. VS Code

1. Abrir a pasta raiz do projeto.
2. Selecionar o interpretador `.venv/bin/python` no macOS/Linux ou `.venv\Scripts\python.exe` no Windows.
3. Executar `run_gui.py` como arquivo Python; a GUI deve abrir em janela desktop própria.
4. Configurar o diretório de trabalho da execução para a raiz do projeto no cenário documentado. Os arquivos de saída serão gravados nesse diretório corrente, como na referência.
5. Se o usuário mudar o diretório corrente, manter carregamento de assets e funcionamento do módulo; somente o destino padrão das saídas muda.
6. Não depender de notebook, backend inline ou navegador para abrir a janela principal.

## 5. Utilitários e verificação de desenvolvimento

As ferramentas complementares deverão ter `--help` e entrada/saída explícitas. Contratos planejados:

```bash
python -m pyfracpaq.tools.image_preprocess --input foto.jpg --output foto_processed.tif
python -m pyfracpaq.tools.move_to_nodes --input fractures.dat --output fractures.txt --x-column 1 --y-column 3
```

Esses exemplos usam o Python da `.venv` após ativação, ou podem ser chamados pelo caminho completo do interpretador. As colunas do utilitário Move devem ser informadas na convenção documentada base 1, convertida internamente para Python.

Para desenvolvimento, após criar os arquivos correspondentes:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/numerical
python -m pytest tests/gui
python -m pytest tests/visual
```

Testes GUI exigem ambiente gráfico ou configuração de plataforma Qt de testes. Comparações visuais da release devem usar o ambiente de referência, com fontes e escala registrados. Não tratar uma passagem em plataforma offscreen como prova de aparência idêntica em todos os desktops.

# SPRINTS DE IMPLEMENTAÇÃO / DESENVOLVIMENTO

As sprints abaixo são pacotes de trabalho em ordem lógica, sem duração prometida. Cada tarefa tem espaço `[ ]` para marcar `[x]` somente após entregar implementação e evidência. A divisão poderá ser refinada conforme o esforço medido; nenhuma aba obrigatória pode ser retirada para chamar a entrega parcial de clone completo.

## Sprint 0 — Referências e contrato de paridade

**Dependências:** nenhuma. **Entrega:** base verificável para comparar o port, antes das decisões de algoritmos e desenho.

- [X] S00-01 — Criar `docs/parity/matrix.md` com todos os 164 IDs do inventário e distinguir GUI obrigatória, exportações, complementos, legado e questões Q.
- [X] S00-02 — Registrar versão do fonte FracPaQ, checksum dos arquivos e manter a distribuição original intacta.
- [X] S00-03 — Extrair de `guiFracPaQ2D.fig` todos os controles, propriedades, grupos, defaults e posições normalizadas para uma especificação de referência.
- [X] S00-04 — Definir máquina/SO, resolução, escala de tela e fonte do ambiente de comparação.
- [X] S00-05 — Capturar ou obter as telas e figuras MATLAB necessárias; registrar as referências ainda indisponíveis sem marcar a paridade como concluída.
- [X] S00-06 — Selecionar exemplos válidos e criar casos analíticos pequenos para geometria, histogramas, círculos, topologia, tensores e wavelets; cobrir AUX-16.
- [X] S00-07 — Resolver versões compatíveis com Python 3.13, testar importação de Qt/Matplotlib/SciPy/scikit-image e congelar requirements de execução/desenvolvimento.
- [X] S00-08 — Definir tolerâncias dimensionais, critérios visuais e procedimento de decisão para Q-01 a Q-21; registrar licenças e créditos iniciais (AUX-18).

**Evidências da Sprint 0:** [relatório de execução](../parity/sprint-0.md), [matriz](../parity/matrix.md) e [protocolo de captura](../parity/capture-protocol.md). As imagens obtidas do manual são apoio documental; capturas controladas e arrays MATLAB continuam registrados como pendentes, sem declaração de paridade concluída.

## Sprint 1 — Núcleo geométrico e entrada TXT

**Dependências:** Sprint 0. **Entrega:** importar nós e obter uma geometria confiável, independente da GUI.

- [X] S01-01 — Implementar Node, Segment, Trace e Dataset, com campos completos para todos os modos de entrada; IN-02.
- [X] S01-02 — Implementar leitor TXT tabulado com linhas de tamanhos diferentes, validação de pares e diagnóstico por linha; IN-01, AUX-03.
- [X] S01-03 — Implementar remoção controlada de nós consecutivos duplicados, rejeição de traços degenerados e vínculo estável entre arrays; IN-03, Q-07.
- [X] S01-04 — Calcular comprimento de segmentos/traços, ângulos, centros de segmentos e metade do caminho de traços; corrigir uso indevido de coordenadas euclidianas conforme Q-07.
- [X] S01-05 — Implementar limites de domínio, contagens e área, incluindo mínimos não nulos e coordenadas negativas; Q-08.
- [X] S01-06 — Implementar escala e derivação de unidades sem alterar a origem dos dados; IN-04.
- [X] S01-07 — Implementar interseções, coincidência, paralelismo e distâncias ponto–ponto/ponto–segmento; AUX-04.
- [X] S01-08 — Validar linhas e polilinhas conhecidas, dados inválidos, repetidos e aplicação de escala; registrar evidências numéricas.

**Evidências da Sprint 1:** [relatório](../parity/sprint-1.md), [contrato da API](../decisions/0002-geometry-and-txt.md) e [validação numérica](../../tests/reference/sprint1/numerical.json). Originais map1/map7 com traços degenerados são rejeitados com diagnóstico; testes também usam cópias temporárias preparadas explicitamente. Comparação com execução MATLAB permanece pendente.

## Sprint 2 — Janela principal, estados e exportação base

**Dependências:** Sprint 1. **Entrega:** aplicação local com a tela original e prévia real.

- [X] S02-01 — Criar entrypoints `run_gui.py` e `python -m pyfracpaq`, recursos por pacote e janela principal; UI-01/02.
- [X] S02-02 — Construir Input, estatísticas, canvas central, rodapé, tag, Run e Exit com proporções de referência.
- [X] S02-03 — Construir os seis botões e seus painéis empilhados com todos os controles, defaults e nomes; UI-10/19. Controles sem cálculo ainda devem permanecer rastreados como pendentes, sem dados fictícios.
- [X] S02-04 — Implementar Filename, Browse e radio buttons, incluindo cancelar seleção e caminho fora do diretório corrente; UI-03/04/05, Q-04.
- [X] S02-05 — Implementar Preview TXT, os sete valores de estatísticas e habilitação de abas/Run; UI-06/07/08/11.
- [X] S02-06 — Implementar Flip X/Y e seus estados, sem modificar os arrays de origem; UI-09.
- [X] S02-07 — Implementar configuração congelada de Run, mensagens, workers, progresso e encaminhamento de erros ao campo pertinente; UI-12/14/15/18, Q-01/02.
- [X] S02-08 — Implementar invalidar/refazer Preview após alterações de entrada/extração/escala; Q-21.
- [X] S02-09 — Implementar tag, janela de figuras, exportador PNG comum e fechamento das janelas da aplicação; UI-13/16/17, EXP-01/02.
- [X] S02-10 — Comparar janela inicial, estados, prévia e navegação com referências; verificar texto/foco sem cortes em DPI diferentes.

**Evidências da Sprint 2:** [relatório](../parity/sprint-2.md), [contrato desktop/execução](../decisions/0003-desktop-and-execution.md), [validação](../../tests/reference/sprint2/validation.json) e [capturas em quatro escalas](../../tests/reference/sprint2). Os controles estão construídos; Run informa explicitamente as análises ainda indisponíveis. As capturas Qt offscreen não são referências MATLAB nem aprovação de paridade visual final.

## Sprint 3 — Tema MATLAB, mapas básicos e Angles

**Dependências:** Sprint 2. **Entrega:** mapas e figuras angulares visualmente calibrados.

- [X] S03-01 — Criar `.mplstyle`, QSS, helpers de eixos/textos/legendas e tabelas RGB congeladas; AUX-08.
- [X] S03-02 — Implementar mapa de traços e os marcadores de nós/centros; MAP-01/02.
- [X] S03-03 — Implementar mapas de traços/segmentos por comprimento e de segmentos por strike; MAP-04/05/06; registrar Q-17.
- [X] S03-04 — Implementar correção de norte, round MATLAB, duplicação axial e inversões angulares; ANG-07/08, Q-10.
- [X] S03-05 — Implementar histograma angular e eixos de frequência absoluta/percentual; ANG-01.
- [X] S03-06 — Implementar rosa de área igual, bins 5/10/20/30°, ponderação por comprimento e cores por strike; ANG-02/03/04/06.
- [X] S03-07 — Implementar média circular axial, desvio/resultante e linha média opcional; ANG-05.
- [X] S03-08 — Implementar TXT EZROSE e sua ordenação/precisão; ANG-09.
- [X] S03-09 — Conferir figuras, paletas, unidades, flips e norte com casos direcionais e referências exportadas.

**Evidências da Sprint 3:** [relatório](../parity/sprint-3.md), [contrato e tabela visual](../decisions/0004-maps-and-angles.md), [validação e exportações](../../tests/reference/sprint3/validation.json). Mapas básicos e Angles estão conectados ao Run; Na entrega S3, Q-10/Q-17 preservavam o fonte. Q-10 continua pendente; Q-17 foi resolvida na Sprint 11 com aprovação explícita, mantendo a convenção legada de cores por comprimento. A conferência usa casos analíticos/fontes/manual; não declara paridade contra execução MATLAB indisponível.

## Sprint 4 — Lengths: estatísticas, histogramas, log-log e censura

**Dependências:** Sprint 3. **Entrega:** análises básicas de comprimento com exportações compatíveis.

- [X] S04-01 — Implementar estatísticas de traços/segmentos e contagem de exclusões no terminal; LEN-01.
- [X] S04-02 — Implementar bins e histogramas de traços e segmentos, incluindo marcações de mínimo/máximo; LEN-02.
- [X] S04-03 — Implementar os quatro gráficos log-log, frequências simples/complementares e diagonal do domínio; LEN-03/04, Q-08.
- [X] S04-04 — Reproduzir o problema de censura do legado e implementar a decisão de integridade com máscara comum; LEN-05, Q-05.
- [X] S04-05 — Implementar cross-plot com seleção isolada funcional e tratamento angular documentado; LEN-06, Q-03/10.
- [X] S04-06 — Implementar os três TXT de comprimento/ângulo-comprimento, com esquemas e gatilhos originais; LEN-16, EXP-04.
- [X] S04-07 — Conferir bins, dados repetidos, dados censurados e amostras vazias; evitar limites inválidos em escalas logarítmicas.
- [X] S04-08 — Validar todos os nomes de arquivo e o estilo das sete figuras básicas de Lengths.

**Evidências da Sprint 4:** [relatório](../parity/sprint-4.md), [contrato de Lengths/censura](../decisions/0005-lengths-and-censoring.md), [validação e exportações](../../tests/reference/sprint4/validation.json). Sete figuras e três TXT integrados ao Run; Q-03/05/08 têm correções de integridade medidas e Q-10 preserva a distinção angular do fonte. Comparação MATLAB e homologação visual permanecem pendentes.

## Sprint 5 — SVG e múltiplos conjuntos por cor

**Dependências:** Sprints 1–4. **Entrega:** SVG compatível importado e analisado preservando grupos.

- [X] S05-01 — Implementar parser estruturado do subconjunto SVG: line, polyline e paths simples; IN-05/06/07.
- [X] S05-02 — Definir rejeição explícita de comandos/transformações sem suporte e política para polygon, sem conversão silenciosa de curvas.
- [X] S05-03 — Implementar leitura de stroke por atributo e estilo compatível, normalização hexadecimal e conversão RGB; IN-08.
- [X] S05-04 — Gravar `*_converted.txt` e `*_colourHHHHHH_converted.txt` com precisão e localização originais; IN-09.
- [X] S05-05 — Implementar prévia multicolorida, agregação de limites/estatísticas e mapa por cores; IN-10, MAP-03.
- [X] S05-06 — Permitir carregar um TXT de cor para análises individuais; IN-11.
- [X] S05-07 — Corrigir alcance da limpeza, caminhos, maiúsculas e arquivos inválidos; Q-04/09/19.
- [X] S05-08 — Conferir exemplos de uma/várias cores e documentar quais dados de exemplo em vírgulas ou malformados precisam preparação.

**Evidências da Sprint 5:** [relatório](../parity/sprint-5.md), [contrato SVG/cores](../decisions/0006-svg-and-colours.md), [validação](../../tests/reference/sprint5/validation.json). Subconjunto linear, arquivos por cor e mapa agregado implementados; restrições dos exemplos auditadas. Comparação MATLAB e aceite visual nativo permanecem pendentes.

## Sprint 6 — Imagens e transformada de Hough

**Dependências:** Sprints 1–5. **Entrega:** imagem compatível gera traços e diagnóstico equivalentes.

- [X] S06-01 — Implementar leitura/metadados JPG/JPEG/TIF/TIFF e validação de grayscale 8 bits; IN-12/18.
- [X] S06-02 — Implementar complemento e limpeza de pixels isolados conforme vizinhança de referência; IN-13.
- [X] S06-03 — Implementar/adaptar acumulador Hough, grade theta/rho e limiar; IN-14.
- [X] S06-04 — Implementar seleção de picos, desempates, supressão e extração de linhas compatíveis com FillGap/MinLength; IN-15.
- [X] S06-05 — Construir Dataset completo, um segmento por traço detectado, incluindo centros e cores; IN-16, Q-06.
- [X] S06-06 — Implementar figura Hough de quatro painéis e nome de exportação original; IN-17.
- [X] S06-07 — Implementar nova prévia quando parâmetros de Hough mudam; manter escala e coordenadas consistentes.
- [X] S06-08 — Comparar acumulador, picos, endpoints e estatísticas em imagens sintéticas e Macduff/Orkney compatíveis.
- [X] S06-09 — Executar os recursos das sprints anteriores com origem em imagem para detectar dependências indevidas do leitor TXT.

**Evidências da Sprint 6:** [relatório](../parity/sprint-6.md), [contrato imagens/Hough](../decisions/0007-images-and-hough.md), [validação](../../tests/reference/sprint6/validation.json). Imagens compatíveis geram Dataset completo e diagnóstico; casos sintéticos/Macduff/Orkney e famílias anteriores exercitados. Arrays/picos/endpoints e rasters ainda exigem homologação contra MATLAB indisponível nesta sessão.

## Sprint 7 — Maps: intensidade, densidade e amostragem circular

**Dependências:** Sprints 3 e 6. **Entrega:** mapas e dados P21/P20 com círculos verificáveis.

- [X] S07-01 — Implementar quantidade de círculos no lado menor, raio e grade conforme razão de aspecto; MAP-09.
- [X] S07-02 — Implementar contagem de cruzamentos/extremidades com casos analíticos e registrar a decisão Q-20.
- [X] S07-03 — Implementar as estimativas P21/P20 locais e respectivas unidades; MAP-07/08.
- [X] S07-04 — Implementar mapa de círculos e heatmaps com paleta, extensão e barras inferiores; MAP-09.
- [X] S07-05 — Implementar estatísticas globais separadas da estimativa circular; MAP-10.
- [X] S07-06 — Gravar ambos os TXT de centros/valores com o gatilho acoplado original; MAP-18.
- [X] S07-07 — Conferir geometria transladada, linhas horizontais/verticais, tangência e limites vazios.
- [X] S07-08 — Validar cores, figuras, arrays e arquivos para TXT, SVG e origem Hough.

**Evidências da Sprint 7:** [relatório](../parity/sprint-7.md), [contrato circular/Q-20](../decisions/0008-circular-sampling.md), [validação](../../tests/reference/sprint7/validation.json). Contagem geométrica corrigida com autorização explícita do usuário; P21/P20, círculos, globais e ambos os TXT integrados ao Run. Casos analíticos e TXT/SVG/Hough verificados; homologação MATLAB/SSIM continua pendente.

## Sprint 8 — MLE e avaliação estatística

**Dependências:** Sprint 4. **Entrega:** seis ajustes e percentuais estatísticos documentados.

- [X] S08-01 — Portar lei de potência, busca de xmin e correção opcional de amostra finita; LEN-07.
- [X] S08-02 — Portar ajuste exponencial; LEN-08.
- [X] S08-03 — Portar lognormal e reproduzir a questão de truncamento para decisão Q-15; LEN-09.
- [X] S08-04 — Implementar cortes percentuais, validação do intervalo e tamanho mínimo da amostra; LEN-10.
- [X] S08-05 — Implementar K-S, significâncias, 2500 comparações, RNG local e vetores compartilhados de referência; LEN-11.
- [X] S08-06 — Implementar seis figuras com os eixos próprios de cada distribuição, curvas, cortes, legenda e caixa de parâmetros; LEN-12.
- [X] S08-07 — Alinhar retorno dos parâmetros e mensagens; evitar chamar percentuais de testes de probabilidade posterior de modelo.
- [X] S08-08 — Validar modelos sintéticos, zeros/repetidos, resultados determinísticos e variação Monte Carlo; registrar decisão científica de Q-15.

**Evidências da Sprint 8:** [relatório](../parity/sprint-8.md), [contrato MLE/Q-15](../decisions/0010-mle-and-statistical-assessment.md), [figuras/arrays verificados](../../tests/reference/sprint8/candidate/validation.json) e [comparações K-S nativas](../../tests/reference/sprint8/native_ks_comparison.json). O usuário aprovou explicitamente Q-15/Q-11 em 14/11/2026: “Aprovo as Q-15 e a Q-11.” Oito tarefas concluídas; MLE integrado ao Run padrão com cortes coerentes/busca lognormal por cauda. Testes de produção, modelos sintéticos e vetores K-S nativos verificados; homologação visual integral permanece pendente.

## Sprint 9 — Conectividade I-Y-X

**Dependências:** Sprints 1, 5 e 7. **Entrega:** nós, ternário, heatmaps e TXT de conectividade.

- [X] S09-01 — Implementar classificação de I/Y/X entre segmentos de traços diferentes; FLO-01.
- [X] S09-02 — Reproduzir undershoot/overshoot e definir comportamento da tolerância I→Y; FLO-02, Q-11.
- [X] S09-03 — Implementar remoção de duplicatas e política de nós de borda sem perder vínculo dos dados; FLO-03.
- [X] S09-04 — Implementar ternário IYX com linhas CL=2 e CL=3.57; FLO-04, AUX-10.
- [X] S09-05 — Implementar mapa I azul/Y verde/X vermelho e legendas/contagens; FLO-05.
- [X] S09-06 — Implementar heatmaps X+Y/I, número de blocos e escala de cores comum; FLO-06.
- [X] S09-07 — Implementar console e TXT de conectividade; FLO-07.
- [X] S09-08 — Validar redes sem cruzamentos, uma única classe, junções próximas, dados duplicados e total zero.

**Evidências da Sprint 9:** [relatório](../parity/sprint-9.md), [contrato IYX/Q-11](../decisions/0011-connectivity-iyx.md), [figuras/arrays verificados](../../tests/reference/sprint9/candidate/validation.json) e [execução nativa](../../tests/reference/sprint9/native/native_topology.json). Q-11 aprovada explicitamente pelo usuário em 14/11/2026 junto de Q-15; oito tarefas concluídas e conectividade integrada ao Run padrão com proximidade finita/pontas reais. Nós, ternário, heatmaps e TXT verificados; homologação visual integral permanece pendente.

## Sprint 10 — Crack tensors e permeabilidade

**Dependências:** Sprints 3, 4 e 9. **Entrega:** gráficos polares e autovalores com unidades corretas.

- [X] S10-01 — Portar tensores 2/4/8 e termo de ordem 0 com comprimentos e área; FLO-08.
- [X] S10-02 — Implementar o gráfico Crack tensor plot dentro de Fluid flow e seu despacho pela rotina angular, incluindo o gatilho EZROSE.
- [X] S10-03 — Implementar tensor P e K, projeção polar e autovalores; FLO-09/13.
- [X] S10-04 — Implementar abertura fixa, modo escalado, fator/expoente e λ; FLO-10/11/12.
- [X] S10-05 — Conferir limites de parâmetros e abertura zero, sem introduzir dependência automática de λ com conectividade.
- [X] S10-06 — Validar padrões direcionais/isotrópicos, simetria, unidades e escala cúbica da abertura.
- [X] S10-07 — Comparar paletas, orientações, legendas, PNG e valores impressos com as referências.

**Evidências da Sprint 10:** [relatório](../parity/sprint-10.md), [contrato tensoral](../decisions/0012-crack-tensors-and-permeability.md), [comparação nativa](../../tests/reference/sprint10/native_comparison.json) e [figuras/arrays/TXT](../../tests/reference/sprint10/validation.json). Sete tarefas concluídas e integradas ao Run padrão, com cache angular/EZROSE, abertura fixa/escalada, λ independente e casos zero. Referências MATLAB executadas; homologação visual integral continua na auditoria final.

## Sprint 11 — Estabilidade de fraturas e Mohr

**Dependências:** Sprints 3 e 10. **Entrega:** os quatro recursos de estabilidade com mapas/rosas coerentes.

- [X] S11-01 — Implementar parâmetros compartilhados σ1, σ2, direção, C0, Pf e mu com validação contextual; MAP-15.
- [X] S11-02 — Implementar tensões normais/cisalhantes e o diagrama de Mohr total/efetivo com reta de resistência; MAP-16.
- [X] S11-03 — Implementar Slip tendency, normalização, mapa, rosa e TXT segmentdata; MAP-11.
- [X] S11-04 — Implementar Dilation tendency, mapa e rosa; MAP-12.
- [X] S11-05 — Implementar Fracture susceptibility, mapa e rosa em MPa; MAP-13.
- [X] S11-06 — Implementar Critically stressed fractures, cores binárias e decisão de igualdade no limite; MAP-14.
- [X] S11-07 — Implementar rosas com passo 10°, linha de σ1, textos e barras de cores; MAP-17.
- [X] S11-08 — Reproduzir e registrar questões de normalização, mu=0, σ1=σ2 e mapeamento de cor; concluir decisão Q-17 antes da aceitação científica.
- [X] S11-09 — Conferir orientações conhecidas, correção de norte/flips, parâmetros e todos os nomes de saída.

**Evidências da Sprint 11:** [relatório](../parity/sprint-11.md), [contrato estabilidade/Q-17](../decisions/0013-fracture-stability-and-mohr.md), [reprodução/decisão](../../tests/reference/sprint11/q17_comparison.json) e [figuras/arrays/TXT](../../tests/reference/sprint11/validation.json). Nove tarefas concluídas. Usuário aprovou explicitamente “Aprovo a correção Q-17.” em 14/11/2026; normalização/cores/igualdade corrigidas, convenção legada de comprimento preservada. Quatro análises e Mohr integrados ao Run padrão; homologação visual integral permanece pendente.

## Sprint 12 — Blocos e variograma

**Dependências:** Sprints 4 e 7. **Entrega:** três saídas de blocos e semivariograma.

**14/11/2026:** sprint concluída, com variograma e Block size graphs no Run padrão. O usuário aprovou Q-14: “Aprovo ambos Q-14 e Extensão Q-20.” Raster fixo sem escala, exclusão de exterior e áreas/centroides calibrados ativados e verificados. [Relatório e evidências](../parity/sprint-12.md).

- [X] S12-01 — Implementar raster de blocos, binarização e conectividade com resolução de referência; LEN-13.
- [X] S12-02 — Definir política de domínio/região exterior e conversão de área, registrando Q-14.
- [X] S12-03 — Implementar centroides, áreas e as três figuras de blocos; LEN-14.
- [X] S12-04 — Preservar o BMP intermediário visível e isolar temporários internos; EXP-03, Q-16.
- [X] S12-05 — Portar semivariograma com centros dos segmentos e 30 classes, incluindo contagem de pares; LEN-15.
- [X] S12-06 — Preservar parâmetros avançados da biblioteca como API auxiliar sem novos campos na aba; AUX-05.
- [X] S12-07 — Validar retângulos conhecidos, translação, escala, centros de origem Hough e dados com comprimento constante.
- [X] S12-08 — Comparar as quatro figuras e seus nomes com a referência MATLAB.

## Sprint 13 — Graphs: perfis ALONG e FROM

**Dependências:** Sprints 6, 7 e 12. **Entrega:** seleção por dois pontos e todos os gráficos de perfil.

**14/11/2026:** sprint concluída, com seleção, todos os perfis ALONG/FROM e nove figuras no Run padrão. O usuário aprovou a extensão P20 de Q-20: “Aprovo ambos Q-14 e Extensão Q-20.” P20=m/(2πr²) ativo, mantendo a contagem finita e a saída acoplada mapa/P21/P20. [Relatório e evidências](../parity/sprint-13.md).

- [X] S13-01 — Implementar captura de dois cliques no canvas, linha/markers e armazenamento da seleção; GRA-01.
- [X] S13-02 — Validar pontos distintos e tratar ausência de seleção/interseções sem variáveis indefinidas; GRA-02, Q-13.
- [X] S13-03 — Implementar comprimento de traço, comprimento de segmento e ângulo ALONG com distância ao ponto 1; GRA-03/04/05.
- [X] S13-04 — Implementar círculos ALONG e ambos os perfis P21/P20, preservando efeito acoplado; GRA-06/07/08.
- [X] S13-05 — Implementar mapa auxiliar com linha, pontos, círculos, cores e legenda; GRA-09.
- [X] S13-06 — Implementar três gráficos FROM usando distância perpendicular com sinal aos centros; GRA-10/11/12.
- [X] S13-07 — Implementar os nove nomes-base de exportação de Graphs e suas tags; GRA-13.
- [X] S13-08 — Conferir múltiplas interseções por traço, orientação da linha, dados Hough e diferenças de norte/flips descritas no original.

## Sprint 14 — Wavelets 2D

**Dependências:** Sprints 6, 10 e 12. **Entrega:** Morlet/Mexican Hat com dados, raster e figuras por escala.

**14/11/2026:** nove tarefas concluídas; Q-12 aprovada explicitamente: “Aprovo a Q-12.” Wavelets integradas ao Run padrão, com raster1944×1944/72dpi, amostragem axial, coeficientes/self/eta, PNG/TXT e barras responsivas. [Relatório](../parity/sprint-14.md).

- [X] S14-01 — Implementar ativação e habilitação dos controles, tipo, listas a/L e incremento angular; WAV-01/02/03/04/05.
- [X] S14-02 — Implementar parser de listas sem execução de expressões e validar valores/incrementos com decisão Q-12.
- [X] S14-03 — Implementar raster de entrada a 72 dpi com espessura por regra de 45%, dimensões e margens calibradas; WAV-06.
- [X] S14-04 — Portar núcleos anisotrópicos, rotação, FFT/padding e energia eta; WAV-07.
- [X] S14-05 — Portar resposta self, normalização, maximização por L/θ e corte em 50%; WAV-08/09.
- [X] S14-06 — Implementar painel 2×2 e TXT de θ por escala com nome/tag originais; WAV-10/11.
- [X] S14-07 — Implementar flips, progresso e diagnóstico de início/fim, escalas e máximos; WAV-12.
- [X] S14-08 — Gerenciar memória por escala/orientação mantendo equivalência, nome do raster e diretório de execução; Q-16.
- [X] S14-09 — Comparar coeficientes, ótimos, seleção de limiar, raster e figuras nos dois kernels, incluindo imagens retangulares.

## Sprint 15 — Utilitários, bibliotecas e destinação do legado

**Dependências:** Sprints 0–14 conforme o recurso. **Entrega:** recursos complementares documentados e nenhuma funcionalidade AUX esquecida.

**14/11/2026:** nove tarefas concluídas; utilitários preprocess/Move, diálogo wavelet, APIs e exemplos/manual entregues. Todos19AUX e164arquivos com destinação; legado/experimentos preservados sem campos novos na GUI2.8. [Relatório](../parity/sprint-15.md).

- [X] S15-01 — Portar pré-processamento de imagem como ferramenta local com entrada/saída explícitas e painel das seis etapas; AUX-01.
- [X] S15-02 — Portar Move para nós com colunas escolhidas, política de cabeçalho, separação de objetos e último objeto verificados; AUX-02.
- [X] S15-03 — Completar bibliotecas de leitura, geometria, paletas e desenho utilizadas pelo produto; AUX-03/04/08/10.
- [X] S15-04 — Portar como APIs complementares o variograma avançado, tensor 16, rosas lineares/históricas e probePlane; preservar/documentar como experimentos as variantes incompletas de rosas/cores, mantendo todos fora da GUI 2.8; AUX-05/06/07/09/11.
- [X] S15-05 — Reproduzir o diálogo wavelet separado e seus Run/Cancel como ferramenta complementar; portar somente as variantes necessárias e registrar as demais; AUX-12/13.
- [X] S15-06 — Classificar a interface 2.2 sem FIG e scripts com assinaturas antigas como legado de referência; não usá-los como entrypoint; AUX-14/15, Q-19.
- [X] S15-07 — Entregar exemplos válidos, manual local de uso/preparação, créditos e referências; AUX-16/17/18.
- [X] S15-08 — Preservar/documentar a página histórica e seus assets sem criar requisito de hospedagem; explicar que params.json não configura a GUI; AUX-19.
- [X] S15-09 — Registrar destinação de formatos de scripts antigos e manter salvamento de sessão/relatório consolidado como extensão futura, sem novo requisito de GUI; EXP-05/06.

## Sprint 16 — Auditoria de paridade e entrega local

**Dependências:** todas as sprints da entrega principal. **Entrega:** clone verificável, instalável e documentado.

**Estado atual — 16/11/2026:** **S16-04 concluída.** O usuário aprovou todos os casos 1 a 16 após a substituição dos marcadores. Os 11 critérios verificáveis foram satisfeitos; dados, revisão semântica, diferenças autorizadas e aceites visuais permanecem separados. **S16-09: pontos 1–4 concluídos** (interface macOS, exportações, documentação e validação do código para clone/download); falta disponibilizá-lo no GitHub (ponto 5), aguardando autorização. A distribuição é pelo código, conforme definição de 16/11/2026. [Estado final das análises](../../tests/reference/sprint16/final/status.json), [aceite](../../tests/reference/sprint16/final/user-visual-acceptance.json) e [estado da entrega](../../tests/reference/sprint16/delivery/status.json).

- [X] S16-01 — Executar matriz completa de 118 recursos GUI, seis itens EXP e destinação de todos os AUX; nenhum controle obrigatório pode ficar sem ação.
- [X] S16-02 — Revisar Q-01 a Q-21: registrar resoluções, decisões científicas e qualquer divergência ainda impeditiva; não esconder pendências.
- [X] S16-03 — Conferir todos os nomes/gatilhos de PNG/TXT/intermediários, precisão, ordenação, tags e substituição segura; EXP-03/04, Q-16/18.
- [X] S16-04 — Realizar comparação de dados e figuras com o MATLAB em cada família analítica e corrigir diferenças sem regressões.
- [X] S16-05 — Conferir GUI/figuras no macOS, incluindo fontes, DPI, seleção de arquivo e paths com espaços/acentos. Escopo ajustado explicitamente pelo usuário em 14/11/2026: Windows/Linux ficam para seus testes posteriores, sem certificação nesta entrega.
- [X] S16-06 — Verificar instalação limpa em `.venv`, abertura pelos dois entrypoints, execução pelo VS Code e funcionamento offline.
- [X] S16-07 — Medir tempos/picos de memória com conjuntos reais e conferir responsividade, mensagens e encerramento durante processamento.
- [X] S16-08 — Atualizar README, guia de instalação, manual, decisões, matriz de paridade e avisos de terceiros.
- [ ] S16-09 — Fazer revisão final de todas as telas e exportações; publicar a versão do port com descrição clara da referência FracPaQ 2.8 e das diferenças aceitas.

**Execução controlada da S16-09 — 16/11/2026:** por solicitação do usuário, concluir somente um ponto por vez e parar até receber autorização explícita para o próximo. S16-09 permanece sem X enquanto os cinco pontos não forem concluídos.

- [X] S16-09.1 — Revisar a interface no macOS: janela inicial, seis abas, diálogos, mensagens, estados e redimensionamento. **Concluído:** 48 capturas das telas (Cocoa nativo, 100/125/150/200% e mínimo 1000×591), dez capturas nativas adicionais dos fluxos/diálogos, sete verificações nativas e 81 testes GUI aprovados. Nenhum defeito da interface permaneceu nas condições revisadas; o roteiro de captura foi corrigido para aplicar o tamanho solicitado depois da abertura com largura total. [Relatório](../parity/sprint-16-delivery.md), [galeria](../../tests/reference/sprint16/delivery/point-1/index.html) e [evidências](../../tests/reference/sprint16/delivery/point-1/summary.json).
- [X] S16-09.2 — Conferir as exportações da versão final: nomes, tags, unidades, conteúdo e substituição dos arquivos. **Concluído:** 53 PNGs atuais com RGB idêntico às referências aprovadas, 4724×4724/600 dpi e metadados 0.9.0rc1; 11 arquivos principais idênticos byte a byte, 14 modelos de dados cobertos com SVG/auxiliares, tags vazias/acentuadas, unidades pixels/metres e substituição conferidas; 282 testes aprovados. Nenhum defeito produtivo encontrado. [Evidências](../../tests/reference/sprint16/delivery/point-2/summary.json). Registro da etapa anterior: o trabalho parou após o ponto 2 até a autorização para o ponto 3.
- [X] S16-09.3 — Consolidar versão e documentação da entrega: identificação, changelog, instalação e diferenças aceitas. **Concluído:** mantida 0.9.0rc1/November 2026/luismauricio@me.com; notas da versão com diferenças científicas/visuais e evidências, README/changelog/manual/instalação e estados alinhados. Pacotes 0.1.0rc1 identificados como históricos; instruções do novo pacote condicionadas ao ponto 4. [Notas](../releases/0.9.0rc1.md), [relatório](../parity/sprint-16-delivery.md) e [verificações](../../tests/reference/sprint16/delivery/point-3/summary.json).
- [X] S16-09.4 — Preparar e validar a distribuição pelo código: conteúdo do repositório/ZIP do GitHub, exclusões, dependências e execução em ambiente limpo pelos dois entrypoints, sem instalar o pacote PyFracPaQ. **Concluído:** requirements.txt com pins; ZIP de uso enxuto sem testes/relatórios, gerado com git archive/export-ignore em repositório temporário; fontes/recursos e exclusões conferidos. Ambientes CPython 3.13.18 e Miniforge Python 3.13.13/macOS arm64, somente dependências, dois entrypoints por ambiente com Preview/Run e 32 saídas; abertura/Preview nativos pelo VS Code confirmados. Clone completo preserva evidências opcionais. Sem publicação, sem alterar o índice/commits do usuário. [ADR 0019](../decisions/0019-source-distribution.md), [relatório](../parity/sprint-16-delivery.md) e [evidências](../../tests/reference/sprint16/delivery/point-4/summary.json).
- [ ] S16-09.5 — Disponibilizar o código no GitHub para clone/download ZIP e registrar o encerramento. **Responsável pelo envio: usuário**, conforme sua definição explícita; o agente não fará commit/push/publicação. Preparação local do README e do manual concluída; conferência remota e encerramento aguardam o envio e o link do repositório.
  - [X] Preparar README em inglês de apresentação, instruções e links para a documentação.
  - [X] Entregar manuais em pt-BR e inglês britânico, em LaTeX e PDF (73/71 páginas), com as seis abas/30 recursos, 51 figuras numeradas em cada versão, teoria/fórmulas e roteiro SD11A; copiar SD11A para examples com procedência e créditos. A versão inglesa acompanha os rótulos e a terminologia da aplicação, incluindo colour.
  - [X] Usuário revisar e aprovar o README e os dois manuais. **Aprovados explicitamente em 16/11/2026.**
  - [ ] Usuário enviar os arquivos ao GitHub.
  - [ ] Conferir repositório/ZIP remoto após o envio e registrar o encerramento.

**Ponto 5 — preparação local concluída:** README em inglês e manuais LaTeX/PDF em pt-BR e inglês preparados para revisão. [Documentos e compilação](../manual/README.md). Envio ao GitHub será feito pelo usuário; conferência remota e encerramento aguardam seu envio/link. A distribuição não prevê instalação do pacote PyFracPaQ nem entrega de instaladores/wheels. [Estado da execução](../../tests/reference/sprint16/delivery/status.json). Windows/Linux permanecem reservados aos testes posteriores do usuário.



**Histórico da auditoria em 14/11/2026:** [auditoria e critérios então abertos](../parity/sprint-16.md), [matriz executada](../../tests/reference/sprint16/functional-matrix.json), [catálogo com hashes](../../tests/reference/capture_catalog.json), [instalação/entrega offline](../install.md) e [ADR0018](../decisions/0018-local-audit-and-delivery.md). **684 testes passaram.** O port tem candidato local0.1.0rc1; S16-04/S16-09 continuam abertas: há regiões abaixo de SSIM0,98 e contextos sem homologação visual final. Não foi flexibilizado o limite nem declarada paridade geral. Q05 aprovada explicitamente nesta auditoria; Q10 preserva o fonte sem unificação. Originais e resultados preexistentes preservados.

**Complemento de15/11/2026 — SD11A:** por indicação do usuário, o TXT original foi executado diretamente nos dois programas:445 traços/1076 segmentos/1521 nós,30 rotas Python e15 chamadas nativas concluídas,51 figuras pareadas. Dos81 confrontos de arrays/curvas,74 coincidem e sete registram diferenças explicadas; os quatro TXT comparáveis são idênticos byte a byte após corrigir a ordenação estável dos zeros assinados no EZROSE. A função principal Wavelets foi executada integralmente e seu núcleo também conferido sobre os mesmos pixels nativos. **686 testes passaram.** [Relatório e pendências](../parity/sd11a.md), [galeria pareada](../../tests/reference/sprint16/sd11a/gallery.md) e [suíte](../../tests/reference/sprint16/sd11a/checks.json). S16-04/S16-09 permanecem sem X, pois a homologação visual ainda não terminou.

**Continuação da S16-04:** correções de renderização e do histograma automático de Wavelets, quatro contextos adicionais Morlet/Mexican Hat, controles multicoloridos SVG e inspeção gráfica Hough estão documentados no [relatório da continuação](../parity/sprint-16-rendering.md). [Métricas e pendências atuais](../../tests/reference/sprint16/final/status.json) distinguem regiões aprovadas, diferenças autorizadas e falhas; não se reduziu o SSIM0,98. A tarefa permanece sem X enquanto os critérios completos não forem satisfeitos.

**Aceite visual de 16/11/2026:** o usuário aprovou a aparência atual dos cinco títulos revisados (dilatação, suscetibilidade, CSF e Graphs P21/P20) e, posteriormente, as diferenças de renderização das duas vistas laterais Hough, após avaliar os detalhes e seu impacto. O [aceite com histórico e hashes](../../tests/reference/sprint16/final/user-visual-acceptance.json) preserva as notas SSIM originais; as sete diferenças visuais revisadas estão aceitas, sem autorizar divergência numérica. S16-04 e S16-09 permanecem sem X até concluir a revisão semântica e a auditoria restantes.

**Revisão final de 16/11/2026:** concluídas a revisão semântica das 51 figuras SD11A (403 verificações; 368 coincidentes/35 diferenças explicadas; nenhum erro semântico pendente), a inspeção dos controles CWT/Hough/SVG e a medição independente de dez legendas/seis caixas MLE. Relatórios, matriz e auditoria por família foram consolidados. Os [11 critérios de encerramento](../../tests/reference/sprint16/final/status.json) têm somente um pendente: decisão do usuário sobre a aparência dos [16 detalhes apresentados](../../tests/reference/sprint16/final/detail-review/index.html), conforme solicitado para evitar calibração prolongada. SSIM 0,98 e notas brutas foram preservados. Cinco testes novos do auditor passaram separadamente; a suíte completa anterior tem 709 testes aprovados e há outros cinco contratos do renderizador aprovados em execução separada. Nenhum módulo produtivo ou PNG mudou nesta revisão. **S16-04 permanece sem X até esse aceite/correção; S16-09 não está incluída neste encerramento.**

**Aceite parcial dos detalhes — 16/11/2026:** o usuário aprovou os casos **2, 4, 6, 8, 10, 12, 13 e 15**. O [registro de aceite](../../tests/reference/sprint16/final/user-visual-acceptance.json) identifica as oito regiões e seus hashes; há agora 15 regiões aceitas ao incluir os sete títulos/painéis Hough anteriores. Permanecem em discussão **1, 3, 5, 7, 9, 11, 14 e 16**, devido à aparência dos quadrados/círculos. As cores correspondentes de linhas/marcadores Graphs foram consideradas coerentes pelo usuário, sem aceite da forma ainda. Nenhum marcador ou PNG foi alterado nesta discussão. S16-04 continua sem X; S16-09 permanece aberta.

**Marcadores geométricos — 16/11/2026:** implementada a substituição global autorizada por quadrados/círculos padrão, incluindo legendas e nós dos mapas. Tamanhos nominais, cores, dados e barras responsivas preservados. As 51 figuras foram atualizadas (26 PNGs alterados/25 idênticos); revisão semântica repetida sem erros e **726 testes aprovados na suíte completa atual**. [Antes/depois](../../tests/reference/sprint16/final/marker-review/index.html), [registro](../../tests/reference/sprint16/final/marker-change.json) e [testes](../../tests/reference/sprint16/final/geometric-markers-checks.json). Os oito detalhes aprovados mantêm seus pixels e aceites; as notas RGB originais de cada versão continuam explícitas. O estado atual mantém 11 regiões para revisão: oito legendas, o mapa de nós e dois retângulos de títulos Graphs que também contêm marcadores alterados. Não houve mudança dos textos dos títulos. S16-04/S16-09 continuam sem X até o aceite final pertinente.


**Encerramento da S16-04 — 16/11/2026:** aprovação explícita: “Aprovo todos de 1 a 16.” Os 16 detalhes atuais foram vinculados aos hashes das referências e dos candidatos; os cinco títulos e duas vistas Hough anteriormente aceitos permanecem no histórico. As três consequências da substituição global dos marcadores (mapa de nós e dois recortes amplos de títulos Graphs) foram verificadas: **nenhum pixel mudou fora dos limites dos marcadores**, comparados às imagens anteriores com hashes conferidos. Trata-se da propagação técnica da alteração já autorizada, sem inventar três aceites adicionais. As regiões/SSIM originais continuam intactas. Há 21 regiões com aceite direto válido e três resolvidas pela propagação comprovada; nenhuma região pendente na S16-04. Todos os 11 critérios passaram, com 726 testes na última suíte completa e sete contratos do auditor aprovados separadamente. [Prova de propagação](../../tests/reference/sprint16/final/marker-propagation-proof.json). **S16-04 marcada com X; S16-09 permanece aberta.** Os parágrafos anteriores documentam os estados históricos.


**Personalização da interface antes da S16-09 — 16/11/2026:** por solicitação do usuário, o logo fornecido foi movido da raiz para pyfracpaq/resources/pyfracpaq-logo.png e substitui a imagem ao lado de Exit. Versão dos fontes/runtime/pacote atualizada para **0.9.0rc1**, data **November 2026** e e-mail **luismauricio@me.com**. Após o ajuste solicitado pelo usuário, versão, data e e-mail ficam em uma única linha; o logo está aproximadamente 12% maior, preservando sua proporção e sem sobrepor Exit ou o rodapé. A referência FracPaQ 2.8 e suas extrações originais permanecem históricas; os aceites e imagens da S16-04 não foram reescritos. A personalização autorizada integra a futura revisão final da S16-09, que continua aberta.

# DEFINIÇÃO DE CONCLUÍDO DO PRODUTO

- [X] Todas as seis abas e seus controles obrigatórios estão implementados, com os defaults e estados da referência.
- [X] TXT, SVG compatível/multicolorido e imagem grayscale 8 bits funcionam no mesmo contrato geométrico.
- [ ] Os cálculos determinísticos passaram nos critérios numéricos e as comparações estocásticas foram tratadas com metodologia explícita.
- [ ] As telas e todas as famílias de figuras passaram na revisão visual e semântica; o programa não usa apenas o estilo Matplotlib padrão.
- [X] Os arquivos de saída têm nomes, quantidades, unidades, esquemas, gatilhos e precisões compatíveis.
- [ ] Todas as divergências científicas relevantes estão resolvidas ou explicitamente aceitas; pendências não são anunciadas como paridade concluída.
- [X] Utilitários e legado têm destinação registrada; ausência de recurso experimental não pode ser confundida com ausência de recurso da GUI 2.8.
- [X] Uma instalação local limpa inicia o programa por Python/terminal/VS Code e executa análises offline.
- [X] A distribuição original e os documentos de referência estão preservados; documentação e atribuições estão atualizadas.

# REFERÊNCIAS DO PRODUTO

- [Modelo de estrutura do PRD](../../prd-bruto.md).
- [Inventário funcional completo e apêndice dos 164 arquivos](FUNCIONALIDADES_FRACPAQ.md).
- [Interface principal e callbacks 2.8](../../fracpaq-matlab/guiFracPaQ2D.m) e [layout original](../../fracpaq-matlab/guiFracPaQ2D.fig).
- [README da distribuição](../../fracpaq-matlab/README.md), [manual 2.8](<../../fracpaq-matlab/FracPaQ User Guide v2.8.pdf>) e [licença original](../../fracpaq-matlab/LICENSE).
- [Exportação gráfica de referência](../../fracpaq-matlab/guiPrint.m).

Os links técnicos das especificações foram consultados para selecionar as bibliotecas; a equivalência científica e visual deverá ser demonstrada pelas evidências previstas neste PRD. Este arquivo é uma especificação de produto e implementação, e não uma declaração de que o clone já foi desenvolvido.

**Organização aprovada — 16/11/2026:** PRD e inventário funcional movidos para docs/planning; 14 saídas locais preservadas em outputs/previous-runs, fora do Git. Caminhos relativos, ferramentas de manutenção e exclusão do planejamento no ZIP atualizados. README e manuais aprovados pelo usuário permanecem intactos. [Registro da organização](../parity/repository-organisation.md). A S16-09.5 aguarda o envio pelo usuário e a conferência remota.
