# PyFracPaQ

Port desktop científico do FracPaQ MATLAB2.8 para CPython3.13. **Candidato local0.1.0rc1; Sprints0–15 integradas e auditoria S16 registrada.** As30 rotas analíticas estão disponíveis, com os53 tipos de PNG e14 tipos de dados/intermediários conferidos. Hough passou a coincidir exatamente com o MATLAB nos cinco casos capturados, incluindo imagens reais. Q05 recebeu aprovação explícita do usuário.

**A homologação visual integral continua aberta:** há regiões abaixo do SSIM0,98 e contextos que ainda exigem comparação final. O wheel é candidato local, sem declaração de paridade geral. Windows/Linux foram adiados por instrução do usuário. [Relatório da auditoria](docs/parity/sprint-16.md), [instalação/VS Code/offline](docs/install.md), [decisões atuais](docs/decisions/0018-local-audit-and-delivery.md) e [alterações da versão](CHANGELOG.md).

**Sprints 8/9 implementadas e integradas ao Run**, com seis ajustes MLE, 2500 testes K-S por modelo e conectividade I/Y/X com quatro figuras/TXT. Resultados originais foram executados no MATLAB R2024b para reproduzir Q-15/Q-11. O usuário aprovou explicitamente as correções em 14/11/2026: cortes coerentes/busca lognormal por cauda e tolerância por proximidade de pontas reais. Os [relatórios da Sprint 8](docs/parity/sprint-8.md) e [Sprint 9](docs/parity/sprint-9.md) incluem as comparações e evidências.

**Sprints 10/11 integradas ao Run:** Crack tensor plot gera ordens 0/2/4/8 e aciona EZROSE; Permeability plot usa abertura fixa/escalada e λ independente. As quatro análises de estabilidade geram mapas/rosas de 10° e um Mohr compartilhado. Slip tendency também grava segmentdata com coordenadas e ângulos brutos. O usuário aprovou Q-17 em 14/11/2026: normalização por tensões corrigidas, cores Sf e igualdade CSF coerentes. A convenção legada das cores por comprimento foi preservada. [Tensores/permeabilidade](docs/decisions/0012-crack-tensors-and-permeability.md) e [estabilidade/Q-17](docs/decisions/0013-fracture-stability-and-mohr.md) detalham unidades, limites e referências nativas.

## Preparação local

Baseline verificada: CPython 3.13.18, macOS arm64. Windows/Linux e outros patches ainda não foram validados. Na raiz, com Python 3.13 instalado:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip install -e . --no-deps --no-build-isolation
.venv/bin/python -m pip check
.venv/bin/python scripts/run_isolated_tests.py --report /tmp/pyfracpaq-tests.json
```

No PowerShell, usar `.\.venv\Scripts\python.exe` e definir `$env:QT_QPA_PLATFORM='offscreen'` para os checks; esses comandos ainda precisam de validação naquela plataforma. O modo offscreen verifica integração Qt, sem certificar aparência de desktop. A instalação de execução usa requirements.txt; requirements-dev.txt também instala preparação de referências e testes. Setuptools fica nas dependências de desenvolvimento para instalação editável sem resolução implícita do backend.

Após instalar, abrir pelo terminal ou pelo VS Code, selecionando o executável `.venv/bin/python`:

```bash
.venv/bin/python run_gui.py
.venv/bin/python -m pyfracpaq
```

A forma por módulo funciona também fora da raiz após instalação. A janela carrega seus recursos do pacote. A versão do port é0.1.0rc1;2.8 identifica o original de referência. Os dois entrypoints também foram executados pelo VS Code no desktop macOS.

Selecionar TXT, SVG compatível ou JPEG/TIFF grayscale de oito bits, clicar Preview e conferir os sete valores estatísticos. SVG converte nós junto à origem; imagens abrem/exportam o diagnóstico Hough antes do Run. Flips e navegação preservam os dados e escolhas. Alterar entrada, escala ou parâmetros Hough exige nova prévia. Run padrão salva cinco PNGs de 20×20 cm/600 dpi e quatro TXT no diretório corrente; mapas de múltiplas cores acrescentam a figura multicolorida. Lengths oferece histogramas, log-log, cross-plot isolado e censura nas extremidades. Para MLE, selecionar Log-log lengths e MLE analysis; os cortes Lower/Upper removem os menores/maiores valores, respectivamente. Para conectividade, selecionar I-Y-X connectivity em Fluid Flow e ajustar blocos/tolerância. Variogram of segment lengths já está integrado e usa 30 classes sem ajuste de modelo; Block size graphs gera três figuras e o BMP visível, com exclusão do exterior e calibração de área aprovadas em Q-14.

A janela abre centralizada e ajustada à área útil da tela, até 1250×739 pixels lógicos. Navegação sem moldura e controles posicionados conforme o FIG, com rolagem apenas quando a área cliente não comporta a superfície mínima. [Revisão visual e capturas atuais](docs/parity/ui-calibration.md) documenta os ajustes e as verificações nas quatro escalas de tela.

As barras de cores acompanham a área do plot ao redimensionar e exportar: horizontais com a mesma largura, verticais com a mesma altura. A distância aos rótulos do eixo é fixa; janelas pequenas reservam espaço para evitar sobreposição e recuperam a área ao ampliar. A regra é compartilhada por todas as figuras atuais e obrigatória para as próximas implementações. [Contrato e exemplos](docs/decisions/0009-responsive-colourbars.md).

O subconjunto SVG aceita line, polyline e paths M/L absolutos, com stroke hexadecimal por atributo/style inline/grupo. Curvas, transformações, polygon e CSS/classes exigem preparação explícita; o documento inteiro é recusado antes de substituir os TXT. Os grupos `colourHHHHHH` podem ser recarregados para análise individual. Os exemplos SVG originais e suas restrições estão na [auditoria](tests/reference/sprint5/original_svg_audit.json). MacduffBinary/Orkney1aBinary são imagens compatíveis; as versões RGBA não são convertidas automaticamente.

Em Maps, selecionar Estimated Intensity, P21 e/ou Estimated Density, P20, definir pelo menos dois círculos no lado menor e, opcionalmente, Show circles. Cada mapa selecionado gera um PNG; Show circles acrescenta uma única figura. Qualquer seleção grava os dois TXT de centros/valores. As estimativas locais usam interseções finitas/extremidades por segmento; os globais do console usam comprimento/área e segmentos/área, separadamente. Domínio de área zero é recusado. [Contrato circular e Q-20](docs/decisions/0008-circular-sampling.md) detalha tangência, bordas, unidades e formatação histórica dos arquivos.

## Importação TXT pela API

Após a instalação editável, executar em Python:

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

O arquivo deve ter um traço por linha e pares X/Y separados por TAB. Erros retornam NodeFileError com caminho, linha/coluna e issues estruturadas; não há importação parcial. Duplicatas consecutivas são removidas com diagnóstico. [Contrato da API](docs/decisions/0002-geometry-and-txt.md) detalha identidade, escala, unidades e primitivas geométricas.

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

- [Matriz dos 164 IDs](docs/parity/matrix.md), com estados e destinação AUX/legado.
- [Fonte e padrões encontrados](docs/parity/source-review.md) e [contrato do FIG](docs/parity/gui-reference.md).
- [Ambiente congelado](docs/decisions/0001-environment.md) e [tolerâncias/aceite](docs/parity/acceptance.md).
- [Fixtures e procedência](docs/parity/fixtures.md), [questões Q](docs/parity/divergences.md) e [protocolo de captura](docs/parity/capture-protocol.md).
- [Relatório da Sprint 0](docs/parity/sprint-0.md), [PRD](PRD.md) e [créditos/licenças](THIRD_PARTY_NOTICES.md).
- [Relatório da Sprint 1](docs/parity/sprint-1.md) e [evidências numéricas](tests/reference/sprint1/numerical.json).
- [Relatório da Sprint 2](docs/parity/sprint-2.md), [contrato desktop/execução](docs/decisions/0003-desktop-and-execution.md) e [captura da prévia](tests/reference/sprint2/dpi-100/preview.png).
- [Relatório da Sprint 3](docs/parity/sprint-3.md), [contrato de mapas/Angles](docs/decisions/0004-maps-and-angles.md) e [exportações verificadas](tests/reference/sprint3/validation.json).
- [Relatório da Sprint 4](docs/parity/sprint-4.md), [contrato de Lengths/censura](docs/decisions/0005-lengths-and-censoring.md) e [exportações verificadas](tests/reference/sprint4/validation.json).
- [Relatório da Sprint 5](docs/parity/sprint-5.md), [contrato SVG/cores](docs/decisions/0006-svg-and-colours.md) e [evidências](tests/reference/sprint5/validation.json).
- [Relatório da Sprint 6](docs/parity/sprint-6.md), [contrato de imagens/Hough](docs/decisions/0007-images-and-hough.md) e [evidências](tests/reference/sprint6/validation.json).
- [Relatório da Sprint 7](docs/parity/sprint-7.md), [contrato circular/Q-20](docs/decisions/0008-circular-sampling.md) e [evidências](tests/reference/sprint7/validation.json).
- [Relatório da Sprint 8](docs/parity/sprint-8.md), [contrato MLE/Q-15](docs/decisions/0010-mle-and-statistical-assessment.md) e [seis figuras MLE](tests/reference/sprint8/candidate/validation.json).
- [Relatório da Sprint 9](docs/parity/sprint-9.md), [contrato IYX/Q-11](docs/decisions/0011-connectivity-iyx.md) e [figuras/arrays/TXT de conectividade](tests/reference/sprint9/candidate/validation.json).
- [Relatório da Sprint 10](docs/parity/sprint-10.md), [tensores/permeabilidade](docs/decisions/0012-crack-tensors-and-permeability.md) e [evidências](tests/reference/sprint10/validation.json).
- [Relatório da Sprint 11](docs/parity/sprint-11.md), [estabilidade/Mohr/Q-17](docs/decisions/0013-fracture-stability-and-mohr.md) e [evidências](tests/reference/sprint11/validation.json).

Há referências documentais do manual e extrações estáticas dos FIG. Na avaliação das Sprints 8/9, MATLAB R2024b executou os ajustes originais, sete casos topológicos, hist3 e 7500 comparações K-S com vetores compartilhados; scripts, resultados e procedência estão preservados. As Sprints 10/11 acrescentam tensores/permeabilidade, estabilidade, jet RGB, layouts e PNGs nativos; Q-17 foi reproduzida e corrigida com aprovação. A S16 acrescenta estados reais da GUI por print/propriedades e capturas dos53 nomes de figuras. A homologação visual geral continua pendente: disponibilidade de captura, casos analíticos e smoke tests não substituem o aceite por região.

Sprints 12/13: selecionar Variogram of segment lengths em Lengths gera o semivariograma e os três TXT da família. Em Graphs, Select end points captura dois cliques na prévia; Escape cancela, entrada/escala nova limpa a linha e flips/norte a preservam. Os seis perfis de comprimento/ângulo ALONG/FROM já funcionam com TXT/SVG/imagem. Blocos e P21/P20 ALONG estão ativos no Run após a aprovação explícita de Q-14 e da extensão P20 de Q-20: blocos excluem a região exterior, mantêm a resolução original e calibram as áreas/centroides; Graphs usa P20=m/(2πr²). Selecionar qualquer opção circular produz mapa e ambos os perfis uma única vez. [Sprint 12](docs/parity/sprint-12.md) e [Sprint 13](docs/parity/sprint-13.md).

API auxiliar do variograma: `from pyfracpaq.analysis.variogram import experimental_variogram`; aceita posições N×D, valores escalares e `nrbins`, `maxdist`, `kind`, `anisotropy`, `thetastep`, `subsample`, `seed` e `subsample_indices`. Retorna valores, centros, contagens e proveniência da amostra. `from pyfracpaq.plots.variogram import variogram` acrescenta `plotit=True` e retorna resultado/figura sem abrir janelas nem salvar automaticamente. [Convenções e limites](docs/decisions/0014-blocks-and-variogram.md).

**Sprints14/15 concluídas:** Wavelets2D Morlet/Mexican Hat integradas ao Run, com Q-12 aprovada explicitamente. Listas a/L positivas inteiras e incremento divisor de180; raster72dpi, painéis por escala e theta TXT preservados. Ferramentas locais preprocess/Move, diálogo wavelet Run/Cancel e APIs complementares disponíveis por `python -m pyfracpaq.tools --help`. [Manual local](docs/user-guide.md), [exemplos válidos](examples/README.md), [destinação dos19AUX](docs/parity/legacy.md), [Sprint14](docs/parity/sprint-14.md) e [Sprint15](docs/parity/sprint-15.md). A auditoria S16 está documentada, com aceite visual/release final ainda abertos; ver relatório e métricas vinculadas acima.
