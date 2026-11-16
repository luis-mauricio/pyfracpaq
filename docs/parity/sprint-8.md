# Sprint 8 — MLE e avaliação estatística

Concluída em 14/11/2026: oito tarefas implementadas e verificadas. **O usuário aprovou Q-15 e Q-11: “Aprovo as Q-15 e a Q-11.”** MLE está ativado no registro padrão e no Run, com cortes coerentes e busca lognormal por cauda. A aprovação da correção não equivale à homologação numérica/visual geral de todo o legado.

| Tarefa | Implementação e evidência |
| --- | --- |
| S08-01 | Lei de potência, busca discreta de xmin e correção finita opcional na API. |
| S08-02 | Exponencial deslocada por xmin, estimação de lambda e busca do limiar. |
| S08-03 | Lognormal sobre logs de cada cauda candidata; reprodução nativa do defeito de truncamento e comparação registrada. |
| S08-04 | Seleção única após cortes percentuais, validação de positivos/finitude/valores distintos e tamanho restante. Sentido Lower/Upper aprovado em Q-15. |
| S08-05 | K-S bilateral assintótico, alpha=.1/.05, 2500 comparações por modelo, RNG local e referência nativa com vetores idênticos. |
| S08-06 | Seis figuras, nomes originais, escalas log/log, linear/log e log/linear; curvas, cortes, legenda e caixa de parâmetros. |
| S08-07 | Retornos estruturados e imutáveis, parâmetros e seed no console; percentuais descritos como taxas de testes, sem interpretação posterior. |
| S08-08 | Testes analíticos/sintéticos, zeros/repetidos, reprodutibilidade e variação Monte Carlo executados; **decisão Q-15 aprovada explicitamente pelo usuário**. |

[ADR 0010](../decisions/0010-mle-and-statistical-assessment.md) apresenta equações, estimador lognormal efetivo, políticas, fonte e impacto. [Q-15](divergences.md#q-15--p1) e [comparação concreta](../../tests/reference/sprint8/candidate/q15_comparison.json) registram os resultados nativos e a proposta. Não há seletor novo de modo científico: a implementação aprovada usa o registro padrão. O registro temporário de revisão foi removido, e os testes Qt instanciam MainWindow diretamente.

O MATLAB R2024b Update 9 executou os ajustes originais sem cortes/com cortes e o kstest2 com **7500 vetores compartilhados**: D idêntico, erro máximo de p=2.22e−16, todas as decisões idênticas. [Comparação K-S](../../tests/reference/sprint8/native_ks_comparison.json), [resultados nativos](../../tests/reference/sprint8/native/native_fits.json) e [procedência](../../tests/reference/sprint8/native_provenance.json). Seis PNGs nativos a 150 dpi servem à inspeção; não substituem goldens da GUI/exportação a 600 dpi.

[Artefatos verificados](../../tests/reference/sprint8/candidate/validation.json): seis PNGs 20×20 cm/600 dpi, miniaturas revisadas, três TXT de Lengths, arrays de caudas/perfis/D/p e parâmetros com seed 20261114. O fluxo Qt padrão gera também os quatro log-log, totalizando dez figuras sem duplicar o cálculo Lengths. Erros e interrupção impedem a exportação da família. As novas figuras MLE não têm barras de cores.

**490 testes passaram**, sendo 57 novos sobre a baseline de 433. As 973 advertências são deprecações do backend Qt/Matplotlib. Os testes das duas sprints, regressões e pacote estão registrados em [checks.json](../../tests/reference/sprint8/checks.json). A validação completa usa cópia isolada dos 164 arquivos da baseline: oito resultados MATLAB que já estavam na pasta original do usuário foram preservados, sem alterar o verificador estrito.

Reprodução das figuras: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint89.py`. As referências nativas já estão salvas; recapturá-las exige MATLAB e Statistics and Machine Learning Toolbox. Nenhuma dependência foi acrescentada.
