# Desenvolvimento e referencias

Material opcional para manutencao e auditoria. O uso normal exige somente as dependencias de requirements.txt; nao depende de testes, scripts ou relatorios. Este arquivo conserva a documentacao tecnica antes reunida no README. Os caminhos dos comandos continuam relativos a raiz do projeto.

# PyFracPaQ

Port desktop científico do FracPaQ MATLAB2.8 para CPython3.13. **Fontes atuais: 0.9.0rc1; Sprints0–15 integradas e S16-04 concluída.** As30 rotas analíticas estão disponíveis, com os53 tipos de PNG e14 tipos de dados/intermediários conferidos. Hough passou a coincidir exatamente com o MATLAB nos cinco casos capturados, incluindo imagens reais. Q05 recebeu aprovação explícita do usuário.

**Distribuição pelo código:** obter a pasta pelo GitHub (clone ou download ZIP), preparar Python 3.13 e as dependências e executar pela raiz, no terminal ou VS Code. Miniforge pode gerenciar o ambiente Python. Não é necessário instalar o pacote PyFracPaQ; não haverá entrega de instalador ou wheel para usuários. [Decisão de distribuição](../docs/decisions/0019-source-distribution.md).

**S16-04 concluída nos contextos analíticos documentados:** comparações numéricas/semânticas e figuras aprovadas, com diferenças autorizadas explícitas. Na S16-09, os pontos 1–3 foram concluídos; o ponto 4 foi redefinido para validar o uso do código por clone/download e continua aberto. Disponibilização no GitHub é o ponto 5, ainda pendente. Windows/Linux ficam para os testes do usuário. [Notas 0.9.0rc1](../docs/releases/0.9.0rc1.md), [estado da entrega](../tests/reference/sprint16/delivery/status.json) e [preparação/VS Code](../docs/install.md).

**Sprints 8/9 implementadas e integradas ao Run**, com seis ajustes MLE, 2500 testes K-S por modelo e conectividade I/Y/X com quatro figuras/TXT. Resultados originais foram executados no MATLAB R2024b para reproduzir Q-15/Q-11. O usuário aprovou explicitamente as correções em 14/11/2026: cortes coerentes/busca lognormal por cauda e tolerância por proximidade de pontas reais. Os [relatórios da Sprint 8](../docs/parity/sprint-8.md) e [Sprint 9](../docs/parity/sprint-9.md) incluem as comparações e evidências.

**Sprints 10/11 integradas ao Run:** Crack tensor plot gera ordens 0/2/4/8 e aciona EZROSE; Permeability plot usa abertura fixa/escalada e λ independente. As quatro análises de estabilidade geram mapas/rosas de 10° e um Mohr compartilhado. Slip tendency também grava segmentdata com coordenadas e ângulos brutos. O usuário aprovou Q-17 em 14/11/2026: normalização por tensões corrigidas, cores Sf e igualdade CSF coerentes. A convenção legada das cores por comprimento foi preservada. [Tensores/permeabilidade](../docs/decisions/0012-crack-tensors-and-permeability.md) e [estabilidade/Q-17](../docs/decisions/0013-fracture-stability-and-mohr.md) detalham unidades, limites e referências nativas.

## Preparação local

Baseline verificada: CPython 3.13.18, macOS arm64. Windows/Linux e outros patches ainda não foram validados. Na raiz, com Python 3.13 instalado:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

No PowerShell, usar `.\.venv\Scripts\python.exe` e definir `$env:QT_QPA_PLATFORM='offscreen'` para os checks; esses comandos ainda precisam de validação naquela plataforma. O modo offscreen verifica integração Qt, sem certificar aparência de desktop. O uso normal instala somente as dependências de requirements.txt. requirements-dev.txt acrescenta as ferramentas de testes/referências para desenvolvimento; não é necessário instalar o projeto com pip.

Depois de preparar as dependências, abrir na raiz da pasta pelo terminal ou VS Code, selecionando o executável `.venv/bin/python` (ou o Python do ambiente Miniforge):

```bash
.venv/bin/python run_gui.py
.venv/bin/python -m pyfracpaq
```

Os dois comandos devem ser executados na raiz do código obtido por clone/download. A versão do port é 0.9.0rc1; 2.8 identifica o original de referência. A interface mostra November 2026 e luismauricio@me.com. Artefatos em dist/ são internos/históricos e não fazem parte da distribuição definida para usuários.

Selecionar TXT, SVG compatível ou JPEG/TIFF grayscale de oito bits, clicar Preview e conferir os sete valores estatísticos. SVG converte nós junto à origem; imagens abrem/exportam o diagnóstico Hough antes do Run. Flips e navegação preservam os dados e escolhas. Alterar entrada, escala ou parâmetros Hough exige nova prévia. Run padrão salva cinco PNGs de 20×20 cm/600 dpi e quatro TXT no diretório corrente; mapas de múltiplas cores acrescentam a figura multicolorida. Lengths oferece histogramas, log-log, cross-plot isolado e censura nas extremidades. Para MLE, selecionar Log-log lengths e MLE analysis; os cortes Lower/Upper removem os menores/maiores valores, respectivamente. Para conectividade, selecionar I-Y-X connectivity em Fluid Flow e ajustar blocos/tolerância. Variogram of segment lengths já está integrado e usa 30 classes sem ajuste de modelo; Block size graphs gera três figuras e o BMP visível, com exclusão do exterior e calibração de área aprovadas em Q-14.

A janela inicia com toda a largura disponível da tela, incluindo as bordas da janela, e fica centralizada verticalmente. A altura inicial permanece limitada à área útil e a 739 pixels lógicos; a janela continua redimensionável. Navegação sem moldura e controles posicionados conforme o FIG, com rolagem apenas quando a área cliente não comporta a superfície mínima. [Revisão visual e capturas atuais](../docs/parity/ui-calibration.md) documenta os ajustes e as verificações nas quatro escalas de tela.

As barras de cores acompanham a área do plot ao redimensionar e exportar: horizontais com a mesma largura, verticais com a mesma altura. A distância aos rótulos do eixo é fixa; janelas pequenas reservam espaço para evitar sobreposição e recuperam a área ao ampliar. A regra é compartilhada por todas as figuras atuais e obrigatória para as próximas implementações. [Contrato e exemplos](../docs/decisions/0009-responsive-colourbars.md).

O subconjunto SVG aceita line, polyline e paths M/L absolutos, com stroke hexadecimal por atributo/style inline/grupo. Curvas, transformações, polygon e CSS/classes exigem preparação explícita; o documento inteiro é recusado antes de substituir os TXT. Os grupos `colourHHHHHH` podem ser recarregados para análise individual. Os exemplos SVG originais e suas restrições estão na [auditoria](../tests/reference/sprint5/original_svg_audit.json). MacduffBinary/Orkney1aBinary são imagens compatíveis; as versões RGBA não são convertidas automaticamente.

Em Maps, selecionar Estimated Intensity, P21 e/ou Estimated Density, P20, definir pelo menos dois círculos no lado menor e, opcionalmente, Show circles. Cada mapa selecionado gera um PNG; Show circles acrescenta uma única figura. Qualquer seleção grava os dois TXT de centros/valores. As estimativas locais usam interseções finitas/extremidades por segmento; os globais do console usam comprimento/área e segmentos/área, separadamente. Domínio de área zero é recusado. [Contrato circular e Q-20](../docs/decisions/0008-circular-sampling.md) detalha tangência, bordas, unidades e formatação histórica dos arquivos.

## Importação TXT pela API

Na raiz do código, com o ambiente Python preparado, executar em Python:

```python
from pyfracpaq.io import read_txt

dataset = read_txt('tests/fixtures/nodes/mixed.txt')
print(dataset.n_traces, dataset.n_segments, dataset.n_nodes)  # 2 3 5
print(dataset.area, dataset.length_unit)  # 24.0 pixels
print(dataset.traces[1].midpoint)  # (4.0, 2.5)

scaled = dataset.with_scale(2)  # pixels/metre, sempre a partir da origem
print(scaled.area, scaled.length_unit)  # 6.0 metres
arrays = scaled.as_arrays()  # float64 e IDs int64 na ordem original
```

O arquivo deve ter um traço por linha e pares X/Y separados por TAB. Erros retornam NodeFileError com caminho, linha/coluna e issues estruturadas; não há importação parcial. Duplicatas consecutivas são removidas com diagnóstico. [Contrato da API](../docs/decisions/0002-geometry-and-txt.md) detalha identidade, escala, unidades e primitivas geométricas.

Os mapas originais map1_edit_converted.txt e map7_edit_converted.txt contêm três e dois traços degenerados, respectivamente, e são rejeitados com as linhas indicadas. Os testes usam também cópias temporárias preparadas explicitamente; nenhum original foi alterado.

## Verificação e referências

```bash
# Verificação estrita: acusa arquivos extras na pasta original.
.venv/bin/python scripts/source_manifest.py
.venv/bin/python scripts/validate_sprint1.py --output /tmp/pyfracpaq-sprint1.json
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/check_environment.py --output /tmp/pyfracpaq-environment.json
.venv/bin/python scripts/extract_fig_reference.py --output-dir /tmp/pyfracpaq-fig
```

Os testes precisam da pasta original fracpaq-matlab, já excluída pelo .gitignore fornecido. Preservá-la e transportá-la separadamente quando necessário; não gravar resultados nela. Os comandos de verificação e extração não exigem internet após instalar as dependências.

- [Matriz dos 164 IDs](../docs/parity/matrix.md), com estados e destinação AUX/legado.
- [Fonte e padrões encontrados](../docs/parity/source-review.md) e [contrato do FIG](../docs/parity/gui-reference.md).
- [Ambiente congelado](../docs/decisions/0001-environment.md) e [tolerâncias/aceite](../docs/parity/acceptance.md).
- [Fixtures e procedência](../docs/parity/fixtures.md), [questões Q](../docs/parity/divergences.md) e [protocolo de captura](../docs/parity/capture-protocol.md).
- [Relatório da Sprint 0](../docs/parity/sprint-0.md), [PRD](planning/PRD.md) e [créditos/licenças](../THIRD_PARTY_NOTICES.md).
- [Relatório da Sprint 1](../docs/parity/sprint-1.md) e [evidências numéricas](../tests/reference/sprint1/numerical.json).
- [Relatório da Sprint 2](../docs/parity/sprint-2.md), [contrato desktop/execução](../docs/decisions/0003-desktop-and-execution.md) e [captura da prévia](../tests/reference/sprint2/dpi-100/preview.png).
- [Relatório da Sprint 3](../docs/parity/sprint-3.md), [contrato de mapas/Angles](../docs/decisions/0004-maps-and-angles.md) e [exportações verificadas](../tests/reference/sprint3/validation.json).
- [Relatório da Sprint 4](../docs/parity/sprint-4.md), [contrato de Lengths/censura](../docs/decisions/0005-lengths-and-censoring.md) e [exportações verificadas](../tests/reference/sprint4/validation.json).
- [Relatório da Sprint 5](../docs/parity/sprint-5.md), [contrato SVG/cores](../docs/decisions/0006-svg-and-colours.md) e [evidências](../tests/reference/sprint5/validation.json).
- [Relatório da Sprint 6](../docs/parity/sprint-6.md), [contrato de imagens/Hough](../docs/decisions/0007-images-and-hough.md) e [evidências](../tests/reference/sprint6/validation.json).
- [Relatório da Sprint 7](../docs/parity/sprint-7.md), [contrato circular/Q-20](../docs/decisions/0008-circular-sampling.md) e [evidências](../tests/reference/sprint7/validation.json).
- [Relatório da Sprint 8](../docs/parity/sprint-8.md), [contrato MLE/Q-15](../docs/decisions/0010-mle-and-statistical-assessment.md) e [seis figuras MLE](../tests/reference/sprint8/candidate/validation.json).
- [Relatório da Sprint 9](../docs/parity/sprint-9.md), [contrato IYX/Q-11](../docs/decisions/0011-connectivity-iyx.md) e [figuras/arrays/TXT de conectividade](../tests/reference/sprint9/candidate/validation.json).
- [Relatório da Sprint 10](../docs/parity/sprint-10.md), [tensores/permeabilidade](../docs/decisions/0012-crack-tensors-and-permeability.md) e [evidências](../tests/reference/sprint10/validation.json).
- [Relatório da Sprint 11](../docs/parity/sprint-11.md), [estabilidade/Mohr/Q-17](../docs/decisions/0013-fracture-stability-and-mohr.md) e [evidências](../tests/reference/sprint11/validation.json).

Há referências documentais do manual e extrações estáticas dos FIG. Na avaliação das Sprints 8/9, MATLAB R2024b executou os ajustes originais, sete casos topológicos, hist3 e 7500 comparações K-S com vetores compartilhados; scripts, resultados e procedência estão preservados. As Sprints 10/11 acrescentam tensores/permeabilidade, estabilidade, jet RGB, layouts e PNGs nativos; Q-17 foi reproduzida e corrigida com aprovação. A S16 acrescenta estados reais da GUI por print/propriedades e capturas dos53 nomes de figuras. A S16-04 foi concluída nos contextos capturados, com aceites por região e decisões científicas explícitas; as revisões finais de telas/exportações foram concluídas nos pontos 1–2 da S16-09. O ponto 3 consolidou a documentação; o ponto 4 agora valida o código para clone/download, sem instalação do pacote. A disponibilização no GitHub permanece pendente no ponto 5.

Sprints 12/13: selecionar Variogram of segment lengths em Lengths gera o semivariograma e os três TXT da família. Em Graphs, Select end points captura dois cliques na prévia; Escape cancela, entrada/escala nova limpa a linha e flips/norte a preservam. Os seis perfis de comprimento/ângulo ALONG/FROM já funcionam com TXT/SVG/imagem. Blocos e P21/P20 ALONG estão ativos no Run após a aprovação explícita de Q-14 e da extensão P20 de Q-20: blocos excluem a região exterior, mantêm a resolução original e calibram as áreas/centroides; Graphs usa P20=m/(2πr²). Selecionar qualquer opção circular produz mapa e ambos os perfis uma única vez. [Sprint 12](../docs/parity/sprint-12.md) e [Sprint 13](../docs/parity/sprint-13.md).

API auxiliar do variograma: `from pyfracpaq.analysis.variogram import experimental_variogram`; aceita posições N×D, valores escalares e `nrbins`, `maxdist`, `kind`, `anisotropy`, `thetastep`, `subsample`, `seed` e `subsample_indices`. Retorna valores, centros, contagens e proveniência da amostra. `from pyfracpaq.plots.variogram import variogram` acrescenta `plotit=True` e retorna resultado/figura sem abrir janelas nem salvar automaticamente. [Convenções e limites](../docs/decisions/0014-blocks-and-variogram.md).

**Sprints14/15 concluídas:** Wavelets2D Morlet/Mexican Hat integradas ao Run, com Q-12 aprovada explicitamente. Listas a/L positivas inteiras e incremento divisor de180; raster72dpi, painéis por escala e theta TXT preservados. Ferramentas locais preprocess/Move, diálogo wavelet Run/Cancel e APIs complementares disponíveis por `python -m pyfracpaq.tools --help`. [Manual local](../docs/user-guide.md), [exemplos válidos](../examples/README.md), [destinação dos19AUX](../docs/parity/legacy.md), [Sprint14](../docs/parity/sprint-14.md) e [Sprint15](../docs/parity/sprint-15.md). A auditoria S16-04 e a revisão final de telas/exportações estão concluídas nos contextos documentados; a preparação do código para clone/download permanece no ponto 4 e a disponibilização no GitHub no ponto 5, conforme a ADR 0019. Ver as notas da versão e as métricas vinculadas acima.

## Uso e desenvolvimento separados

requirements.txt instala apenas as bibliotecas de execução. Para testes e referências, instalar requirements-dev.txt no ambiente de desenvolvimento. O clone preserva tests/, scripts/ e os relatórios; o ZIP de uso os exclui por .gitattributes/export-ignore. Não apagar os arquivos dourados e aceites de tests/reference: eles mantêm a rastreabilidade científica. A descoberta de testes no VS Code fica desativada por padrão e pode ser habilitada localmente por quem desenvolve.

A validação sem instalar o pacote utiliza scripts/prepare_source_archive.py e scripts/check_source_delivery.py. O primeiro cria somente um repositório Git temporário e exporta o candidato com os atributos; o segundo exige que o código venha da pasta fornecida e que não exista distribuição PyFracPaQ instalada, e exercita Preview/Run com conexões e DNS bloqueados no Python. Os fixtures de uso vêm de examples/; testes e MATLAB não entram na cópia validada.

Os scripts build_local_release.py, check_local_delivery.py e validate_local_release.py têm origem na etapa anterior de empacotamento; wheels e instalação do projeto não são o fluxo de distribuição adotado. O checker de fontes reaproveita somente as verificações de janela/exportação do checker antigo, exigindo importação pela pasta e ausência de instalação do projeto.
