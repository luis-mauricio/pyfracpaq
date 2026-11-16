# Sprint16 — Auditoria de paridade e entrega local

Auditoria executada em14/11/2026, macOS27.2.1 arm64/CPython3.13.18/Qt6.12.0/MATLAB R2024b Update9. **Entrega local0.1.0rc1; homologação visual e release final ainda abertas.** O usuário aprovou Q05 e adiou Windows/Linux para testes próprios. As tarefas concluídas foram marcadas no PRD; S16-04 e S16-09 permanecem abertas porque seus critérios completos ainda não foram satisfeitos.

## Resultado por tarefa

| Tarefa | Resultado e evidência |
| --- | --- |
| S16-01 | Matriz164 IDs revisada:118GUI,6EXP,19AUX,21Q;30 rotas compute/render disponíveis e executadas juntas. Nenhum seletor obrigatório sem implementação. [Matriz auditada](../../tests/reference/sprint16/functional-matrix.json), [execução integral](../../tests/reference/sprint16/all-outputs/validation.json), [matriz legível](matrix.md). Evidência de testes compartilhada por família; não se afirma um teste independente para cada ID. |
| S16-02 | Q01–21 revisadas, estados históricos corrigidos e decisões científicas preservadas. Q05 aprovada explicitamente após reprodução nativa; Q10 resolvida por preservação das convenções do fonte, sem nova unificação. [Registro Q](divergences.md), [comparação Q05](../../tests/reference/sprint16/q05_comparison.json), [ADR0018](../decisions/0018-local-audit-and-delivery.md). |
| S16-03 |53 nomes PNG e14 tipos de dados/intermediários indexados com origem/hash.52 figuras por Run conjunto e Hough no Preview; quatro TXT do caso pareado idênticos byte a byte. Tags, diretórios congelados, precisões, ordem e falhas/substituição por arquivo cobertos pela suíte. [Catálogo](../../tests/reference/capture_catalog.json), [contrato de saídas](../../tests/reference/sprint16/output-contract.json). |
| S16-04 | **Parcial.** Referências nativas, comparações de arrays e correções Hough/layout executadas;13 comparações de imagens pareadas ainda falham em regiões. Faltam homologação por contexto de todas as famílias e correções visuais restantes. [Famílias/limites](../../tests/reference/sprint16/family-audit.json), [métricas/diferenças](../../tests/reference/sprint16/candidate/validation.json). |
| S16-05 | Mac verificado com sessão desktop real, Browse/Cancel, arquivo com espaços/acentos/extensão maiúscula, abas/estatísticas/Run e figuras.32 capturas Qt em100/125/150/200%, sem cortes. Windows/Linux adiados pelo usuário, sem anúncio de suporte. [Sessão nativa](../../tests/reference/sprint16/desktop-session.json), [capturas](../../tests/reference/sprint16/gui/dpi-100/manifest.json). Isso não é homologação de pixels de todas as telas. |
| S16-06 | Venv limpa CPython3.13, instalação por wheels sem índice, pip check, dois entrypoints do pacote instalado fora da árvore com connect/DNS impedidos. Execução real dos dois entrypoints pelo VS Code; configuração do interpretador corrigida. [Instalação limpa](../../tests/reference/sprint16/clean-install.json), [guia](../install.md). |
| S16-07 | Tempos/RSS reais map1/map7 e heartbeat Qt medidos; apresentação dividida em eventos, Exit entre PNGs e atalho Close verificados. Outra janela permanece aberta. [Medições](../../tests/reference/sprint16/benchmarks/gui/validation.json), [Exit durante exportação](../../tests/reference/sprint16/benchmarks/exit/validation.json). |
| S16-08 | README, instalação/offline/VS Code, manual, ADRs, divergências/matriz/catálogo, changelog e avisos atualizados. Fontes originais e oito resultados preexistentes preservados; manifesto estrito mantido. |
| S16-09 | **Parcial.** Revisão funcional/galeria e candidato local com hashes preparados. A publicação de uma release homologada permanece dependente de S16-04; não se converte captura disponível em aceite visual. [Galeria](sprint-16-gallery.md), [alterações](../../CHANGELOG.md), [manifesto da entrega](../../dist/release-manifest.json). |

## Correções verificadas

Hough tinha diferenças de meio bin, vizinhança e ordem que os rasters pequenos não revelavam. A implementação agora coincide exatamente com os estágios MATLAB nos cinco casos, incluindo MacduffBinary/Orkney1aBinary. Isso altera os resultados antigos da S6; seus artefatos continuam históricos. [Votos/picos/endpoints](../../tests/reference/sprint16/hough_comparison.json) registram parâmetros, entradas e hashes; a regressão exige igualdade exata e ordem dos endpoints.

As capturas nativas de geometria confirmaram euclideanLength incorreto no legado; comprimentos, ângulos e centros válidos foram conferidos separadamente. Os quatro vetores log-log do caso direcional têm centros e frequências iguais aos arrays MATLAB. Norte−360/0/12,5/360 e reverseAxis foram executados de fato, preservando wrap único e os TXT com convenções diferentes. [Comparações numéricas](../../tests/reference/sprint16/numeric-comparison.json).

O conversor SVG original gerou NaN e omitiu elementos/grupos nos fixtures, embora a chamada retornasse sucesso. Esses arquivos são preservados como reprodução da Q09, não usados como uma geometria válida que o Python deva reproduzir. O parser XML mantém os elementos do subconjunto autorizado e recusa construções não suportadas antes da escrita. [Comparação SVG](../../tests/reference/sprint16/svg-comparison.json).

Na GUI, Helvetica corresponde aos controles nativos capturados; o fallback é explícito. A abertura1250×739 limitada ao monitor e a navegação sem moldura foram mantidas. O batch MATLAB mede1702×739 neste Mac devido às unidades characters: não se redimensionaram screenshots para simular aprovação em2px. Histogramas, mapas básicos, título e ticks foram calibrados pelos PNGs nativos. As barras continuam passando exclusivamente pelo helper compartilhado e preservam alinhamento e distância fixa exigidos pelo usuário.

Run mantém cálculo no worker e apresentação Matplotlib na thread principal, atendendo um PNG por evento. Busy, contexto e temporários permanecem até o fim; o sinal de conclusão não antecipa os PNGs. Exit interrompe a sequência entre arquivos; o PNG em andamento termina atomicamente. Cmd+W foi testado novamente no desktop após a correção e fecha somente a figura em foco. Testes também verificam que outras janelas permanecem abertas.

## Verificação e desempenho

**684 testes passaram** na suíte completa em venv limpa e cópia isolada, incluindo originais exatamente164 arquivos. O relatório [checks.json](../../tests/reference/sprint16/checks.json) e o JUnit preservam saída, retorno, tempo e procedência. Os avisos são deprecações conhecidas de Qt/Matplotlib e casos de variograma que explicitamente excedem o domínio. A suíte final, depois das calibrações e da regressão da anotação de azimute, terminou em62,90s e conferiu os artefatos atualizados. Também passaram57 testes focados de figuras/barras/janelas e13 de estabilidade.

| Caso | Leitura | Cálculo / total | Pico RSS |
| --- | --- | --- | --- |
| map1 preparado:2120 traços/4356 segmentos |0,0496s |0,0867s de cálculo |141,8MB |
| map7 preparado:4090 traços/10134 segmentos |0,1173s |0,1100s de cálculo |151,5MB |
| GUI map1, oito PNGs reais |incluída |2,40s total; maior intervalo de heartbeat0,359s |347,1MB |
| Exit após primeiro PNG |incluída |0,57s total; demais PNGs não iniciados |308,9MB |

MB decimal, RSS macOS em bytes; processos separados, imports incluídos. Tempos de leitura/cálculo excluem renderização nos dois primeiros casos. As cópias de map1/map7 removem explicitamente somente3/2 traços inteiramente degenerados, com linhas/hashes registrados; os leitores de produção continuam recusando esses registros. Não são garantias de tempo para todo dataset. A execução conjunta inclui raster/FFT wavelet de produção e guarda seu próprio RSS/tempo/seed MLE no relatório.

## Critérios ainda abertos

Em15/11/2026 foi acrescentada a [comparação com SD11A.txt](sd11a.md), indicada pelo usuário:445 traços/1076 segmentos/1521 nós,30 rotas Python e15 chamadas nativas concluídas,51 figuras pareadas. Foram conferidos81 arrays/curvas e quatro TXT; a ordenação estável do EZROSE corrigiu os empates de zeros assinados. Dois centros incorretos do leitor original foram identificados, sem alterar a geometria Python já exigida por S01-04. As diferenças aprovadas e os desvios visuais continuam explícitos; a rodada não encerra S16-04/S16-09.

Não se reduziu o SSIM0,98 nem se usaram máscaras ou redimensionamentos na comparação quantitativa. As regiões exploratórias atuais são faixas fixas de título/corpo/rodapé, não substituem a separação final de dados/textos/legenda/barra por família. Há diferenças verificáveis de ticks, fontes/margens e rosas; o corpo de vários mapas/histogramas já supera0,98, enquanto outras regiões não passam. Nenhuma figura completa recebe homologação só por isso.

Os53 nomes nativos da auditoria inicial incluem contextos distintos e uma captura da variante wavelet2. A rodada SD11A acrescenta execução e exportação completas da função principal de wavelets, no contexto controlado Morlet a32/L2/passo90; isso não cobre todos os parâmetros/kernels. As diferenças científicas Q05/11/12/14/15/17/20 foram autorizadas e não são tratadas como identidade com resultados defeituosos. A geometria responsiva das barras exigida pelo usuário prevalece sobre o espaçamento relativo do legado; a avaliação deve distinguir essa diferença aceita dos desvios restantes.

O próximo fechamento de S16-04 deve parear todas as configurações/entradas, comparar arrays antes dos pixels, definir regiões independentes sem excluir curvas/textos, corrigir os desvios restantes e executar a revisão visual/semântica final. Somente então S16-09 pode declarar uma release homologada. A versão local0.1.0rc1 permite instalar, executar e inspecionar o trabalho atual sem esconder essa pendência.

A continuação desta auditoria está registrada em [renderização S16-04](sprint-16-rendering.md), com candidatos separados e [estado verificável](../../tests/reference/sprint16/final/status.json). Ela corrige também a divisão automática dos histogramas de Wavelets, conferida com centros/contagens nativos, e acrescenta quatro contextos completos Morlet/Mexican Hat e controles SVG/Hough. Os relatórios anteriores permanecem como evidência histórica. A continuação não altera o limite SSIM nem equivale ao encerramento da tarefa.

## Reprodução

`audit_sprint16.py native` confere capturas existentes; `baseline` gera o contexto pareado/SSIM/TXT; `all` executa todas as rotas; `map1`/`map7` medem dados reais em cópias preparadas. `benchmark_desktop.py` mede eventos/exportação/Exit. Usar `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib` e Qt offscreen para esses comandos de verificação. Os scripts capture_native_s16*.m exigem MATLAB/toolboxes apenas para recaptura, nunca para rodar o port.

Depois de gerar evidências, executar index_sprint16.py, build_parity_index.py e review_sprint16.py. Eles validam hashes e preservam estados independentes; não geram goldens MATLAB a partir do Python. O [guia de instalação](../install.md) descreve wheels, VS Code, offline e suíte isolada. O arquivo de fontes da entrega contém exatamente a baseline original e exclui venvs, segredos, caches e resultados pessoais.
