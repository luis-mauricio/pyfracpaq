# Sprint 4 — Lengths: estatísticas, histogramas, log-log e censura

Execução em 13/11/2026. S04-01 a S04-08 concluídas, preservando as tarefas já marcadas das sprints anteriores. A entrega inclui as sete figuras básicas, os três TXT, censura com associação íntegra e seleção isolada de cross-plot. MLE, blocos e variograma permanecem nas sprints próprias.

| Tarefa | Evidência |
| --- | --- |
| S04-01 | LengthStatistics, totais encontrados/retidos/excluídos no console; mínimo, máximo e média por população e unidade. |
| S04-02 | Histogramas com 10/20/30/50 intervalos e n+1 centros, frequências vinculadas, min/max e tratamento de dados iguais. |
| S04-03 | Quatro log-log preservam contagens/curva complementar binned; grades pixels/metres distintas e diagonal por amplitudes com ceil. Q-08 aplicado. |
| S04-04 | Q-05 reproduzida por tradução estática; primeiro/último nó correto, quatro bordas e máscara comum para comprimentos, ângulos e IDs. |
| S04-05 | LEN-06 executa isoladamente; duplicação/norte/flips e pares filtrados; convenção bruta do TXT mantida em Q-10. |
| S04-06 | Três nomes/esquemas de TXT exatos, ordenação só das listas univariadas, staging e substituição por arquivo; uma exportação por Run Lengths. |
| S04-07 | Amostra censurada vazia, um único valor, repetidos, bins indistinguíveis, limite de memória e limites logarítmicos verificados; zeros preservados nos dados. |
| S04-08 | Sete basenames e respectivas composições conferidos; 21 PNGs reais e nove TXT em três cenários, integração Qt e revisão das imagens do manual. |

**252 testes passaram**, incluindo 44 novos casos. O backend Qt/Matplotlib instalado emite 314 avisos de depreciação AA_UseHighDpiPixmaps, sem falhas; nenhuma dependência foi adicionada/atualizada e pip check não encontrou conflitos. Os 164 arquivos originais continuam intactos por SHA-256.

[checks.json](../../tests/reference/sprint4/checks.json) registra contagens/checksum do JUnit, auditoria dos arquivos e hash do wheel. O pacote final foi importado diretamente do zip fora da raiz do projeto, renderizando as sete figuras e gerando os três TXT. Após atualizar a documentação/matriz, os 14 testes do contrato de referências também passaram.

A integração Qt verifica as sete janelas/exportações com censura e escala angular; testa cross-plot sozinho e erro posterior de censura total preservando saídas anteriores. O Run padrão agora gera cinco figuras reais e quatro TXT, incluindo o EZROSE de Angles, sem alterar seleções iniciais do FIG. Arrays e Dataset de entrada permanecem íntegros.

[validation.json](../../tests/reference/sprint4/validation.json) registra três cenários: pixels sem censura; metros com censura, norte 10° e Flip X; e comprimentos repetidos. São 21 PNGs 4724×4724 a aproximadamente 600 dpi, nove TXT, parâmetros completos, arrays numéricos e hashes. As miniaturas QA derivam dos próprios pixels do exportador comum. [Reprodução de Q-05](../../tests/reference/sprint4/q05_static_reproduction.json) é explicitamente uma tradução estática Python, sem fingir execução nativa. [examples.json](../../tests/reference/sprint4/examples.json) registra cálculo/contagens/TXT dos três exemplos fornecidos válidos: IYXtest1, IYXtest2 e Souter_Blue.

Na entrada analítica de seis traços/sete segmentos, a censura corrigida exclui quatro traços de borda e retém comprimentos totais [7,5] e segmentos [3,4,5], com ângulos associados [90,0,36.86989764584402]. A emulação do fonte retém três traços de borda, exclui os internos e ainda desalinha um dos ângulos. O marcador diagonal corrigido é 37, preservado por translação, enquanto a expressão antiga daria 59 com os mesmos limites. Esses resultados e a autorização de implementação por S04-04/RF-04 estão documentados na [ADR 0005](../decisions/0005-lengths-and-censoring.md); não são equivalência do cenário defeituoso.

Exemplos visuais: [histograma de segmentos](../../tests/reference/sprint4/qa-FracPaQ2D_histosegmentlength_pixels.png), [acumulada de traços](../../tests/reference/sprint4/qa-FracPaQ2D_loglogplottracelength_pixels.png), [cross-plot após censura/escala](../../tests/reference/sprint4/qa-FracPaQ2D_crossplotsegmentlengthangle_censored_metres.png) e [acumulada de repetidos](../../tests/reference/sprint4/qa-FracPaQ2D_loglogplottracelength_repeated.png).

MATLAB/Octave continuam indisponíveis: aceite visual por regiões/SSIM e comparação com arrays nativos permanecem pendentes. As imagens do manual p. 18/19/21 são apoio documental, não goldens com os mesmos parâmetros. Q-03/Q-05/Q-08 têm implementação Python medida; Q-10 mantém a distinção entre pares brutos de Lengths e vetores corrigidos de gráficos/EZROSE. As tolerâncias congeladas não foram relaxadas.

Para reproduzir:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint4.py
.venv/bin/python scripts/source_manifest.py
```

Na GUI: Preview TXT, manter os defaults ou selecionar Lengths. Log-log libera a opção de censura conforme o callback original; cross-plot funciona sozinho. Se toda a amostra tocar as bordas, a mensagem identifica a censura e não substitui os arquivos anteriores. O restante da aplicação segue disponível conforme a matriz de paridade.
