# Sprint 11 — Estabilidade de fraturas e Mohr

Concluída em 14/11/2026 com **aprovação explícita de Q-17 pelo usuário: “Aprovo a correção Q-17.”** [ADR 0013](../decisions/0013-fracture-stability-and-mohr.md) e [comparação Q-17](../../tests/reference/sprint11/q17_comparison.json) registram a reprodução e a regra ativa no Run padrão.

| Tarefa | Evidência |
| --- | --- |
| S11-01 | Parâmetros compartilhados/contextuais, tensões compressivas ordenadas e erros nos campos antes das exportações. |
| S11-02 | sn/tau e Mohr total/efetivo com reta de resistência, limites e legenda; sem acrescentar pontos omitidos no fonte. |
| S11-03 | Ts/TsNorm por tensões corrigidas, mapa/rosa e segmentdata com esquema/ângulos brutos nativos. |
| S11-04 | Td/mapa/rosa; tensões iguais recusadas somente para essa seleção. |
| S11-05 | Sf/mapa/rosa em MPa, escala comum e cores lineares; μ=0 recusado somente para Sf, faixa constante válida. |
| S11-06 | CSF binário inclusivo ≥ no mapa/rosa, igualdade/nextafter conferidos. |
| S11-07 | Bin fixo 10°, frequência/raios, σ1 vermelha, textos e jet nativo; barras responsivas nas oito figuras. |
| S11-08 | Falhas reproduzidas em chamadas MATLAB reais e expressões intermediárias; Q-17 corrigida com aprovação, comprimento legado preservado por decisão explícita. |
| S11-09 | Norte/flips, orientações conhecidas, cache, nomes/gatilhos e Run com TXT/SVG/Hough verificados. |

[Procedência nativa](../../tests/reference/sprint11/native_provenance.json): quatro famílias, erros por normalizador zero/μ=0/tensões iguais, igualdade CSF, jet(19/100/256), dezoito PNGs e layouts genuínos. Ts/Sf e CSF nos casos alterados são diferenças científicas aprovadas; os valores físicos válidos sn/tau/Ts/Td/Sf continuam comparados com as equações nativas.

[Artefatos](../../tests/reference/sprint11/validation.json): quarenta PNGs 4724×4724/600 dpi e miniaturas, quatro segmentdata, arrays e parâmetros. Incluem TXT/SVG/Hough, entrada das capturas e campo constante. Cada execução conjunta gera nove figuras de estabilidade (um Mohr + oito mapas/rosas); a entrada SVG acrescenta uma figura multicolorida. Selecionar somente Sf constante gera Mohr/mapa/rosa e nenhum TXT.

As quatro famílias passam pelo helper compartilhado de barras; testes verificam alinhamento, folga de 25 pontos e restauração em formatos quadrado/largo/pequeno, com flips. [checks.json](../../tests/reference/sprint11/checks.json) registra a regressão completa, pacote e auditoria de arquivos. Fontes/ticks/composição foram comparados e calibrados; homologação visual integral por regiões/SSIM e multiplataforma continua na auditoria final.

**558 testes passaram**, com 68 novos sobre a baseline de 490. As 1631 advertências são deprecações do backend Qt/Matplotlib. Pacote verificado fora da raiz, com onze PNGs 600 dpi e ambos os TXT acoplados.

Reprodução: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint1011.py`. Não houve nova dependência ou controle científico na GUI.
