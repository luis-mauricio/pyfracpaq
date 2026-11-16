# Sprint 13 — Graphs: perfis ALONG e FROM

Sprint concluída: seleção, oito análises de perfil e nove figuras integradas ao Run padrão. **Extensão P20 de Q-20 aprovada explicitamente em 14/11/2026:** “Aprovo ambos Q-14 e Extensão Q-20.” GRA-06/07 estão ativas. [Contrato](../decisions/0015-along-and-from-profiles.md).

Dois cliques na prévia em cache criam ProfileLine imutável, linha/quadrados vermelhos e snapshot do Run. Seleção ausente/nula, clique fora do mapa, duplicação do segundo ponto, cancelamento e invalidação por entrada/escala são tratados. Soma zero válida é aceita. Os fluxos TXT/SVG/Hough passam sem nova importação; flips e norte preservam a linha e os valores científicos dos perfis.

ALONG mantém repetições por segmento, múltiplas interseções por traço e ordem de entrada; FROM mede distância perpendicular assinada dos centros à reta infinita. Linha reversa troca a origem/sinal corretamente. Nenhum resultado de ângulo é corrigido pelo norte/flips nessas famílias.

[Comparações](../../tests/reference/sprint13/native_comparison.json) conferem os seis perfis e o exemplo P21 com arrays de execução MATLAB. As falhas nativas sem interseções/linha nula e o efeito acoplado density→três figuras estão registrados em native_calls.json. O Run circular usa a contagem finita previamente aprovada; a normalização por área aprovada muda P20 de .1591549431 para .0795774715 em r=2,m=2. Testes Qt confirmam que P21 isolado, P20 isolado e ambos selecionados geram uma única tríade mapa/P21/P20, com a fórmula m/(2πr²). [Q-20](../../tests/reference/sprint13/candidate/q20_density_comparison.json).

[Nove figuras/QA e arrays](../../tests/reference/sprint13/candidate/validation.json) preservam os nove nomes-base, cores/legenda, títulos/limites/unidades dos seis perfis e o exportador comum _tag/600 dpi/20×20 cm. Não há TXT de Graphs nem novas barras de cores. A revisão não declara identidade de pixels entre motores. [Proveniência nativa](../../tests/reference/sprint13/native_provenance.json); [checagens finais](../../tests/reference/sprint13/checks.json).
