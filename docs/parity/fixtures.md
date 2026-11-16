# Casos e procedência dos dados

[analytic_cases.json](../../tests/fixtures/analytic_cases.json) contém 46 casos de autoria deste projeto sob LICENSE MIT: geometria horizontal/vertical/oblíqua, polilinha, negativos, escala, duplicatas, inválidos, histogramas, empates/round, norte e quatro combinações de flips, círculos e translações, I/Y/X e gaps, tensores direcionais/isotrópicos, abertura e núcleos wavelet.

Cada caso separa input, expected, questões Q e origem do oráculo. Valores esperados são analíticos e não resultados MATLAB executados. Campos MATLAB nulos indicam ausência, não zero. A seleção de empates de hist, snap I→Y, tangência e ótimos CWT continua pendente quando o original ou a decisão científica é necessária. Domínios topológicos explícitos maiores que os traços isolam os casos da política de exclusão dos nós na borda.

Os TXT em nodes/ têm pares tabulados e linhas de comprimentos diferentes em mixed.txt. Os arquivos empty, incomplete, degenerate, nonfinite e comma são negativos intencionais. Os dois SVG pequenos cobrem linha/polilinha/path reto, uma ou duas cores; não anunciam suporte SVG geral. As imagens sintéticas TIFF têm linha preta sobre branco: directional 32×32 grayscale L, rectangular 48×24 grayscale L e rgb_invalid RGB, que deve ser rejeitada no fluxo GUI.

Os exemplos reais selecionados estão em [examples.json](../../tests/reference/examples.json), com hash, formato, contagens/dimensões e compatibilidade direta inspecionada. Não duplicar os originais sem necessidade:

| Seleção | Uso / resultado da inspeção |
| --- | --- |
| IYXtest1/2_converted.txt | Pequenos candidatos à classificação topológica; tabulados e com pares válidos |
| map1_edit_converted.txt / map7_edit_converted.txt | Pares numericamente válidos; Sprint 1 detectou três/dois traços totalmente repetidos. Originais rejeitados com linhas explícitas; cópias temporárias preparadas são exercitadas em testes |
| Souter_Blue.txt | Exemplo de conjunto individual tabulado |
| souter_all_colour24378D.txt | Exemplo de vírgulas; pares válidos, exige conversão explícita antes do leitor GUI tabulado |
| Macduff.tiff / MacduffBinary.tif / Orkney1a.tiff / Orkney1aBinary.tif | Modo e profundidade inspecionados no manifesto; não presumir grayscale de 8 bits pelo nome Binary |

A licença inicial e a atribuição desses exemplos vêm da distribuição MIT (FracPaQ Contributors, David Healy e Roberto Rizzo), sem presumir autoria individual da coleta/fotografia. Preservar o aviso original em cópias e derivados. Recursos originais completos permanecem na pasta preservada. AUX-16 está coberto na preparação de fixtures; sua integração no produto será validada nas sprints pertinentes.

`scripts/build_fixtures.py` reproduz os casos e a inspeção estrutural/degenerados dos exemplos. Os campos tab_delimited_numeric_pairs e degenerate_trace_lines distinguem sintaxe e geometria; direct_gui_txt só é verdadeiro sem degenerados. A Sprint 0 havia conferido sintaxe/pares; essa verificação semântica foi acrescentada na Sprint 1. O script não é o leitor do produto.

Os testes da Sprint 1 exercitam `pyfracpaq.io.read_txt` contra os oito oráculos geométricos, além de relações/distâncias e dados reais. [numerical.json](../../tests/reference/sprint1/numerical.json) registra medidas, erros absolutos, parâmetros e checksums do código. Os originais map1/map7 são rejeitados nas linhas 1589/1595/1604 e 2496/3242. Para exercitar suas demais geometrias, os testes e o script de validação trocam apenas essas linhas por linhas vazias em cópias temporárias, preservando os números físicos. Isso é preparação explícita de dados, não importação parcial silenciosa.
