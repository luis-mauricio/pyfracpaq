# Manual local do PyFracPaQ

O manual ilustrado contém o roteiro SD11A, os 30 recursos analíticos, figuras, teoria e fórmulas. Está disponível em **português brasileiro** ([PDF](manual/pyfracpaq-user-manual.pdf), [LaTeX](manual/pyfracpaq-user-manual.tex)) e **inglês** ([PDF](manual/pyfracpaq-user-manual-en.pdf), [LaTeX](manual/pyfracpaq-user-manual-en.tex)). As [instruções de compilação](manual/README.md) acompanham as duas versões. Este documento mantém a consulta rápida em português em Markdown.

O port usa a interface FracPaQ 2.8 e funciona offline após preparar as bibliotecas. Versão **0.9.0rc1**, November 2026, contato luismauricio@me.com. Execute o código pela raiz no terminal ou VS Code, com Python 3.13 ou ambiente Miniforge; não é necessário instalar o pacote do projeto. [Preparação do ambiente](install.md), [notas e diferenças aceitas](release-notes.md), [créditos](../THIRD_PARTY_NOTICES.md) e [licença](../LICENSE). MATLAB e os testes não são necessários para usar o programa. Windows/Linux permanecem para testes posteriores do mantenedor.

## Instalar e iniciar

Na raiz do projeto, criar .venv com Python3.13 (ou usar um ambiente Miniforge Python3.13) e instalar as dependências de requirements.txt. Não é necessário instalar o pacote PyFracPaQ. O procedimento completo, dependências de desenvolvimento e comandos PowerShell estão no [README](../README.md). Iniciar com `.venv/bin/python run_gui.py` ou `.venv/bin/python -m pyfracpaq`. No VS Code, selecionar o interpretador de .venv. Não é necessário MATLAB durante a operação.

Escolher o arquivo, clicar Preview, conferir estatísticas, selecionar as saídas nas seis abas e clicar Run. A tag Run1 produz o sufixo _Run1. Os PNGs têm 20×20cm/600dpi; arquivos são gravados no diretório corrente de execução. Repetir tag substitui os mesmos arquivos. Os originais não devem ser usados como diretório de saída.

## Preparar entradas

TXT exige um traço por linha, pares X/Y separados por TAB e ao menos dois nós distintos. Não usar cabeçalho, vírgulas ou comentário no TXT da GUI. O leitor genérico complementar é uma API separada. Escala vazia mantém pixels; pixels/metre positivo divide coordenadas e deriva áreas/unidades. Alterar entrada/escala/Hough exige nova prévia.

SVG aceita line, polyline e path M/L no subconjunto documentado, sem transformações, curvas ou CSS externo. Preparar as camadas no editor externo e usar stroke hexadecimal por atributo/style/grupo compatível. Não converter curvas para retas automaticamente. Os TXT convertidos ficam junto ao SVG; carregar um TXT de cor permite análise individual. Não há edição/digitalização de traços dentro da aplicação.

Imagens da GUI devem ser JPG/JPEG/TIF/TIFF grayscale de oito bits. RGB/alpha não são convertidos silenciosamente. A ferramenta complementar preprocess prepara fotografias RGB; conferir seu resultado antes de importar. Preview apresenta os quatro painéis Hough; ajustar peaks, threshold, FillGap e MinLength antes de executar as análises. [Exemplos válidos](../examples/README.md).

## Escolher análises

Maps produz traços/nós, mapas de comprimento/ângulo, P21/P20 e estabilidade/Mohr. Os mapas circulares usam pelo menos dois círculos no lado menor; qualquer estimativa grava ambos os TXT de centros/valores. A contagem geométrica finita é a correção Q-20 aprovada. Slip tendency também grava segmentdata com coordenadas/ângulo bruto.

Lengths oferece histogramas, distribuições log-log, MLE, cross-plot, censura, blocos e variograma. MLE depende de Log-log; cortes Lower/Upper removem as caudas menores/maiores. A censura usa uma máscara coerente por traço. Blocos Q-14 usam componentes brancos fechados, resolução original e conversão de área, com BMP visível de nome fixo; não medem área vetorial. Variograma usa centros/comprimentos dos segmentos, 30 classes, sem ajuste teórico. A família grava os três TXT mesmo se somente blocos/variograma estiverem selecionados.

Angles produz histograma e rosa de área, com opções de ponderação/cor/média. Fluid flow tem I/Y/X, crack tensors 0/2/4/8 e permeabilidade com abertura fixa/escalada e λ. A conectividade e os ajustes estatísticos usam as correções Q-11/Q-15 aprovadas; estabilidade usa Q-17. Não se modelam vazão ou pressão 3D.

Graphs: Select end points captura dois cliques na prévia. Escape ou botão direito cancelam a tentativa. ALONG mede cada interseção com a linha finita, repetindo traços quando há vários segmentos; FROM usa distância perpendicular assinada à reta infinita. Norte não altera esses ângulos brutos. Selecionar P21 ou P20 gera mapa e ambos os perfis; P20=m/(2πr²), conforme extensão Q-20 aprovada. Alterar entrada/escala limpa a linha; flips preservam a seleção.

## Wavelets

Marcar Run wavelet analysis e escolher Morlet ou Mexican Hat. Informar listas de inteiros positivos a/L, por exemplo `8 16` e `2 4`; o cálculo usa os recíprocos dos fatores L. O incremento angular deve ser inteiro divisor de180, por exemplo10,20,30,45,60 ou90. Expressões MATLAB como `2:2:8` não são executadas; escrever `2 4 6 8`.

O raster de entrada é sempre 1944×1944, 27inches a72dpi, com margens da referência e traços longos (≥45% do maior) em4pontos, demais em1ponto. A escala física/norte não são adicionados às coordenadas do raster. Q-12 aprovada documenta as diferenças de raster/antialiasing e o desempate numérico de orientações isotrópicas. Uma orientação ótima em L=1 pode ser indeterminada fisicamente; o desempate está declarado nas evidências.

Cada a gera um painel 2×2 com imagem, WC normalizado, rosa e histograma de log10 da frequência, mais FracPaQ2Dwavelet_theta_a{a}_{tag}.txt. O corte é fixo: WC estritamente maior que50% do máximo; não há slider. FracPaQ2D_wavelet_traces.png é um intermediário visível sem tag. As barras verticais acompanham a altura dos plots ao redimensionar/exportar e mantêm a folga física compartilhada.

Wavelets podem ser demoradas. Reduzir o número de escalas, fatores L e orientações diminui o trabalho. Há estimativa prévia e orçamento de memória específico de2GiB; entradas acima do limite são recusadas com mensagem antes da alocação maior. Coeficientes são processados por orientação/L, sem tensor global de todas as combinações. A aba principal não ganha botão Cancel; o diálogo auxiliar tem seu próprio Cancel.

## Ferramentas complementares

Executar da raiz após instalação; caminhos podem conter espaços quando passados entre aspas:

```bash
.venv/bin/python -m pyfracpaq.tools preprocess foto.jpg preparada.tif --panel etapas.png
.venv/bin/python -m pyfracpaq.tools move examples/move_objects.dat nos.txt --x-column 1 --y-column 3 --skip-header 1
.venv/bin/python -m pyfracpaq.tools wavelet-dialog FracPaQ2D_wavelet_traces.png --output-directory . --tag Run1
```

Preprocess exige entrada e saídas distintas: TIFF grayscale0/255 e painel das seis etapas. Reproduz conversão cinza, mediana20×20, diferença saturada, Sobel, fechamento e afinamento/inversão. O painel permite decidir se o preparo preserva as fraturas desejadas; não há segmentação por IA.

Move usa colunas em base1, por padrão1/3, objetos separados por linhas vazias e cabeçalho explicitamente contado. Default é zero linhas de cabeçalho; a última fratura é preservada mesmo sem linha vazia final. Conversão inválida não substitui a saída existente. O TXT usa quatro casas decimais e TAB, como o script.

O diálogo wavelet separado reutiliza um raster L/RGB de oito bits, com os mesmos controles/defaults do FIG auxiliar. Run congela os parâmetros e processa em QThread; Cancel fecha somente o diálogo/solicita interrupção do trabalho próprio, aguardando uma etapa segura. Seus TXT preservam o nome auxiliar **sem tag**, enquanto os PNGs usam a tag fornecida pela ferramenta. Ele não substitui a aba principal nem altera a prévia de traços.

## APIs e legado

APIs complementares: readtext em `pyfracpaq.io.text`; tensor16 e probe_plane em `pyfracpaq.analysis.auxiliary`; rosas linear/histórica em `pyfracpaq.analysis.roses`; variograma avançado em `pyfracpaq.analysis.variogram`; paletas em `pyfracpaq.analysis.palettes`; desenho em `pyfracpaq.plots.auxiliary`. Não são seletores da GUI2.8. Os contratos técnicos e a destinação completa constam em docs/parity/legacy.md no repositório completo; não são necessários ao uso.

Os scripts antigos podem ter formatos EPS/JPEG/TIFF, caminhos fixos e assinaturas incompatíveis. Ficam preservados como referências, sem execução automática. Não há salvamento de sessão nem relatório consolidado na GUI; seriam extensões futuras. index.html/assets/params.json são a página histórica, não um frontend web nem configuração da aplicação.

## Auditoria e encerramento —0.1.0rc1

A GUI usa Helvetica da referência, com fallback explícito Arial/DejaVu Sans quando ausente. Plots usam Arial/fallback. Run mantém a interface ocupada até concluir também a apresentação dos PNGs, atendendo eventos entre arquivos. Exit interrompe a sequência após a figura em andamento; os arquivos já salvos permanecem. Cada figura admite o atalho padrão Close (Cmd+W no Mac/Ctrl+W em outras plataformas); fechar uma figura não fecha a janela principal. A ordenação dos endpoints Hough foi corrigida na S16, portanto os resultados antigos da S6 são históricos.

A censura Q05 foi aprovada explicitamente: excluir traço inteiro quando sua primeira/última extremidade toca qualquer borda real e aplicar a mesma máscara a IDs, comprimentos e ângulos. Dados corrigidos podem divergir do MATLAB defeituoso. A convenção angular Q10 foi preservada: norte é subtraído e arredondado; EZROSE é corrigido/duplicado, enquanto pares de comprimento e segmentdata guardam ângulos brutos.

Para conferência dos arquivos, consultar o catálogo/manifestos da S16. Uma captura disponível não equivale a paridade: ainda há diferenças de layout/ticks/textos e famílias sem homologação completa por região. Não usar esse candidato como declaração de identidade científica/visual geral.
