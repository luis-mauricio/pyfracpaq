# Sprint 9 — Conectividade I-Y-X

Concluída em 14/11/2026: oito tarefas implementadas e verificadas. **O usuário aprovou Q-15 e Q-11: “Aprovo as Q-15 e a Q-11.”** Conectividade está ativa no registro padrão/Run. As mudanças científicas em undershoot, tolerância zero e vértices internos foram aprovadas explicitamente; a homologação visual integral do legado permanece independente.

| Tarefa | Implementação e evidência |
| --- | --- |
| S09-01 | Interseções finitas somente entre traços diferentes, classificação por pontas reais/interiores e provenance por IDs. |
| S09-02 | Undershoot/overshoot reproduzidos no MATLAB e no candidato; limite euclidiano inclusivo e projeção finita testados. **Decisão Q-11 aprovada explicitamente pelo usuário.** |
| S09-03 | Deduplicação exata com todos os vínculos, prioridade X em eventos coincidentes e exclusão apenas de I nas quatro bordas. |
| S09-04 | Ternário Y:X:I, linhas CL=2/3.57 e tratamento explícito de total zero. |
| S09-05 | Traços pretos, I azul/Y verde/X vermelho, legenda por classes existentes e contagens no título. |
| S09-06 | Heatmaps hist3 X+Y/I, bins pela razão de aspecto, escala comum e classes vazias válidas. |
| S09-07 | TXT I/X/Y, tag inclusive vazia, substituição atômica e console antes/depois da limpeza. |
| S09-08 | Redes isoladas, T/X, duplicatas, vértices, pontas próximas, classes ausentes/total zero, bordas, escala e interrupção verificados. |

[ADR 0011](../decisions/0011-connectivity-iyx.md) explicita a regra proposta, limitações de classificação por eventos, sobreposições e política de bordas. [Comparação Q-11](../../tests/reference/sprint9/candidate/q11_comparison.json) contém os sete casos idênticos executados no MATLAB original, inclusive erros reais de variáveis indefinidas. [Procedência nativa](../../tests/reference/sprint9/native_provenance.json). Não se atribuem ao original contagens corrigidas.

O núcleo preserva Dataset e registra a posição original/projeção de cada Y inferido. Varredura de bounding boxes e árvores espaciais evitam armazenamento quadrático; orçamento de memória e interrupção cooperativa são explícitos. Heatmaps reproduzem hist3 para classes não vazias, inclusive intervalos constantes; classes vazias usam o domínio em uma grade de zeros. Os dois mapas têm o mesmo máximo.

[Artefatos verificados](../../tests/reference/sprint9/candidate/validation.json): TXT, SVG multicolorido, imagem/Hough e rede fechada de total zero; dezesseis PNGs 20×20 cm/600 dpi, quatro TXT, miniaturas revisadas, arrays I/Y/X e grades. Testes Qt com MainWindow e o registro padrão exercitam Run com SVG e imagem. As barras passam pela fábrica comum e preservam comprimento do plot e folga de 25 pontos até os rótulos em janelas quadradas, largas e pequenas.

**490 testes passaram**, sendo 57 novos sobre a baseline de 433. As 973 advertências são deprecações do backend Qt/Matplotlib. Os testes das duas sprints, regressões, integridade dos 164 fontes e pacote estão registrados em [checks.json](../../tests/reference/sprint9/checks.json). Há quinze PNGs nativos dos casos em que getConnectivity termina; a função nativa não gera o ternário por si. Não se declara homologação SSIM ou correspondência de todos os ticks/paletas.

Reprodução: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint89.py`. Nenhum seletor científico ou dependência foi adicionado. O registro padrão executa a regra aprovada em Q-11. O registro temporário de revisão foi removido; os testes de Run validam a integração de produção.
