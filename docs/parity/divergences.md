# Registro de divergências Q-01 a Q-21

Registro iniciado na S0, revisado na Sprint16 em 14/11/2026 e consolidado para 0.9.0rc1 em 16/11/2026. Os resultados nativos efetivamente executados são identificados por questão; leitura estática não é captura nativa. Correções científicas autorizadas e limitações de homologação visual permanecem explícitas. O mantenedor científico decide alterações de método; testes de integridade não substituem essa decisão.

## Procedimento de decisão

1. Abrir caso com ID, fonte/checksum, versão, entrada, configuração, unidade e prioridade. Distinguir defeito demonstrado de risco estático.
2. Reproduzir no MATLAB quando disponível e salvar saída ou erro, arrays, figura e arquivos. Comparar também com oráculo analítico independente.
3. Para integridade, validação contextual, caminhos e limpeza, implementar a correção prevista no PRD e demonstrar preservação dos resultados válidos. O PRD já autoriza essas correções técnicas; não se exige aprovação adicional para preparar ou testar o caso.
4. Se mudar fórmula, amostragem, normalização, significado angular, censura ou classificação científica, preencher resultado original/proposto, fundamento, impacto, alternativas e teste. Obter decisão explícita do mantenedor antes de promover a alteração a padrão. Não criar seletor de modo científico por conta própria.
5. Registrar autor/data/decisão, atualizar matriz e testes e preservar a referência anterior. Questão sem resultado ou decisão permanece pendente; não declarar paridade naquele item.

Cada questão registra separadamente resultado, decisão e estado. Q-15/Q-11/Q-17 foram reproduzidas no MATLAB e suas correções aprovadas explicitamente pelo usuário em 14/11/2026; Q-05/12/14/20 também têm decisões próprias registradas abaixo. **S16-04 concluída nos contextos documentados**, com aceites visuais preservados; a revisão de interface/exportações da S16-09 também terminou. As ausências de reprodução nativa específica indicadas em cada questão continuam explícitas e não foram transformadas em evidência executada. [Notas consolidadas 0.9.0rc1](../releases/0.9.0rc1.md).

## Q-01 — P1

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 2.
- Evidência estática original: Run valida vários campos de outras análises mesmo quando elas estão desmarcadas (`guiFracPaQ2D.m:1046–1159`)
- Entrada / reprodução: mixed; selecionar somente uma análise e inserir valor inválido em outra aba.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Validar somente parâmetros necessários às saídas selecionadas
- Resultado Python medido: Registro declarativo valida somente parâmetros selecionados, incluindo dependências de MLE. Testes mantêm Sigma/lambda/listas inválidos em análises desmarcadas sem bloquear a seleção pertinente; erros selecionados identificam seu campo e aba.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Correção técnica aplicada conforme S02-07 e política do PRD em 13/11/2026.
- Estado: Correção técnica integrada às30 rotas; testes de validação contextual e Run concluídos. A reprodução nativa específica deste erro continua indisponível.

## Q-02 — P1

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 1/2/6/8/14.
- Evidência estática original: Mensagens pedem inteiros, mas vários campos só testam intervalo; a/L usam `isempty(str2double(...))`, que não valida vetores; faltam verificações de limites/casos degenerados
- Entrada / reprodução: empty, incomplete, nonfinite, bad_wavelet_step; limites/listas adicionais na sprint de implementação.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Validar integralidade, finitude, listas não vazias, cortes, tolerância I→Y e intervalos coerentes
- Resultado Python medido: Validação contextual concluída para todas as famílias: finitude, integralidade, listas a/L, passo divisor de180, cortes MLE, tensões, tolerância e domínios degenerados. Casos técnicos preservam entradas válidas; decisões científicas são Q05/11/12/14/15/17/20, com autorizações individuais.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto a quantificar: valores/classes/limiares e respectivas figuras/TXT; sem aceitação de paridade até concluir comparação e decisão.
- Decisão / autor / data: Validação técnica parcial implementada nas Sprints 1/2. Decisões científicas fora da Q-15 permanecem registradas nos respectivos itens; Q-15 foi aprovada pelo usuário em 14/11/2026.
- Estado: Validações integradas/testadas; decisões científicas individualizadas abaixo. Nenhum método novo foi aprovado por esta revisão técnica.

## Q-03 — P1

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 4.
- Evidência estática original: `flag_length` não inclui `flag_crossplot` (`guiFracPaQ2D.m:1300`), apesar do manual anunciar a correção
- Entrada / reprodução: mixed; marcar somente checkbox_crossplot.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Cross-plot executar como seleção única
- Resultado Python medido: Cross-plot isolado executa LEN-06, gera FracPaQ2D_crossplotsegmentlengthangle_tag.png e os três TXT Lengths. Testes numéricos/Qt verificam uma figura, configuração e ausência de EZROSE quando Angles não é selecionado.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Correção de despacho aplicada conforme S04-05 por solicitação de execução da Sprint 4, em 13/11/2026; sem alterar cálculos válidos.
- Estado: Cross-plot isolado integrado e testado. A função Lengths original foi executada na S16; o defeito do despacho do callback permanece evidência estática, sem alegar reprodução nativa desse callback.

## Q-04 — P1

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 2/5/6.
- Evidência estática original: `imfinfo` usa texto do campo sem `selpath`, enquanto leitura usa caminho combinado; cancelamento de Browse recebe 0 mas testa `~isempty`; detecção SVG usa busca sensível a maiúsculas
- Entrada / reprodução: mixed copiado para caminho com espaços/acentos e extensão .SVG; cancelar Browse.
- Resultado original executado: **disponível** — callback real com caminho absoluto concatena cwd+path e falha ao abrir; erro preservado em sprint16/native/native_calls.json. A sessão separada com nome relativo executa Preview/seis abas e salva propriedades/capturas em native/details. Cancelamento e extensão maiúscula do legado continuam sem captura específica.
- Resultado proposto / critério a verificar: Testar arquivo fora da pasta atual, caminho completo digitado, cancelamento e extensão `.SVG`
- Resultado Python medido: Preview SVG/imagem usa caminho completo capturado, metadados da mesma origem e extensão sem distinção de caixa. Conversões ficam junto ao SVG; diagnóstico no cwd congelado. Browse cancelado não altera entrada; resultados obsoletos não publicam arquivos.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Integração de integridade concluída para os três leitores, conforme S05-07/S06-01/07 em 14/11/2026.
- Estado: Correção de paths dos três leitores testada; Browse/Cancel e caminho com espaços/acentos também verificados no desktop macOS na S16. Diferença técnica deliberada.

## Q-05 — P0

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 4.
- Evidência estática original: Censura compara Y com limites X, usa `Node(nSeg)` em vez do último nó e perde alinhamento ao filtrar comprimentos antes dos ângulos (`guiFracPaQ2Dlength.m:49–105`)
- Entrada / reprodução: polyline, negative; fixture de cada uma das quatro bordas na Sprint 4.
- Resultado original executado: **disponível** — execução real de guiFracPaQ2Dlength sobre lengths_edges.txt confirmou traços [4,4,4], segmentos [4,4,4] e ângulos exportados [90,90,0]. Captura e TXT em sprint16/native; comparação em sprint16/q05_comparison.json.
- Resultado proposto / critério a verificar: Corrigir bordas e índices; usar uma máscara comum para comprimentos/ângulos e definir o que é censurado
- Resultado Python medido: Fixture lengths_edges tem seis traços/sete segmentos. A tradução estática do fonte retém traços 1/2/3 com comprimentos [4,4,4] e ângulos desalinhados [90,90,0], enquanto a máscara correspondente daria [90,0,0]. A correção retém traços 4/5, totais [7,5] e segmentos [3,4,5] com ângulos [90,0,36.86989764584402]; exclui quatro traços/quatro segmentos. Artefato histórico q05_static_reproduction.json e ADR0005. A execução nativa posterior está registrada acima, separadamente.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto a quantificar: valores/classes/limiares e respectivas figuras/TXT; sem aceitação de paridade até concluir comparação e decisão.
- Decisão / autor / data: **aprovada explicitamente pelo usuário em14/11/2026**, mensagem “Aprovo a Q-05.” Excluir o traço inteiro se primeiro/último nó tocar qualquer borda real; máscara comum para IDs/comprimentos/ângulos. A pergunta incluiu a mudança de população de [4,4,4] para [7,5] e segmentos [3,4,5].
- Estado: Correção científica aprovada e ativa; população e associação alinhadas testadas. Não há identidade declarada com a censura defeituosa original.

## Q-06 — P0

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 6.
- Evidência estática original: Leitor de imagem não preenche `Segment.midpointX/Y` nem `Colour`; usa comprimento do primeiro traço em `endLength` dos demais (`guiFracPaQ2Dimage.m:108–122`)
- Entrada / reprodução: directional.tif, rectangular.tif; centros/cores e seis abas.
- Resultado original executado: **disponível** — guiFracPaQ2Dimage executada sobre tensor_network.tif; estrutura real em sprint16/native/details/image_reader.mat. Votos, picos e endpoints comparados exatamente em cinco rasters, incluindo Macduff/Orkney, em sprint16/hough_comparison.json.
- Resultado proposto / critério a verificar: Unificar campos de `traces` e testar todas as seis abas com imagem, inclusive nós, variograma e FROM
- Resultado Python medido: Imagens sintéticas e Macduff/Orkney compatíveis produzem traços de um segmento com centros de traço/segmento, BLUE e end_length do próprio segmento. API with_scale preserva domínio raster e reconstrói da origem. Treze figuras de famílias anteriores executadas com origem em imagem; arrays em sprint6/arrays.npz.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Construtor completo único nos três leitores, conforme PRD. Auditoria S16 corrigiu arredondamento dos bins, vizinhança de supressão e ordem dos endpoints Hough; nenhuma fórmula científica adicional.
- Estado: Campos geométricos completos e Hough nativo testados. As famílias posteriores também têm testes Run com origem em imagem; homologação dos contextos capturados concluída na S16-04, conforme os aceites documentados.

## Q-07 — P0

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 1.
- Evidência estática original: Leitores podem manter nós repetidos enquanto contam segmentos de outra forma; `euclideanLength` usa X no lugar do Y final (`guiFracPaQ2Dlist.m:86–115,167–168`; também em `readTraces`)
- Entrada / reprodução: duplicate, degenerate, polyline.
- Resultado original executado: **disponível** — guiFracPaQ2Dlist sobre directional.txt salva euclideanLength=0 para (0,0)→(0,8), em sprint16/native/geometry_arrays.mat; a distância correta é8. O caso de duplicatas continua com oráculo analítico, sem nova captura nativa atribuída.
- Resultado proposto / critério a verificar: Normalizar nós sem perder pares, conferir comprimentos e rejeitar traços sem segmento
- Resultado Python medido: Implementado em domain/construction.py, models.py e io/nodes.py. duplicate produz 3 nós/2 segmentos com comprimentos [3,4], total 7 e centro (4,2.5); IDs mantêm índices originais. A polilinha de (1,2) a (4,6) tem euclidiana 5, enquanto a expressão defeituosa do fonte daria sqrt(13) (derivação estática, não execução). Traços degenerados reais são rejeitados com linha; relatório em tests/reference/sprint1/numerical.json.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Correção de integridade aplicada sob autorização explícita de S01-03/04 e da política do PRD, em 13/11/2026; não houve nova decisão científica.
- Estado: Normalização, identidade e construção completas nos três leitores; correção de distância confirmada por captura real e testes analíticos.

**Complemento SD11A,15/11/2026:** o leitor original também desloca incorretamente para cima a metade do caminho em segmentos verticais descendentes. Nas linhas389/397 do arquivo indicado pelo usuário, os centros nativos têm Y=772,7301571943/690,65; o Python já calcula754,6698428057/644,75, conforme S01-04. Na linha397, o centro original fica fora do segmento. A diferença propaga-se ao perfil FROM de traços, com erro máximo45,9pixels. Nenhuma geometria Python foi alterada nesta rodada; trata-se de evidência adicional do contrato de integridade existente. [Caso e resultados nativos](sd11a.md).

## Q-08 — P1

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 1/4.
- Evidência estática original: Máximos iniciais em 0 em `getMapLimits`/leitor principal falham para mapas inteiramente negativos; comprimento máximo possível usa `sqrt(xMax²+yMax²)`, sem subtrair mínimos
- Entrada / reprodução: negative, mixed; transladar domínio.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Conferir domínio transladado, coordenadas negativas e diagonal a partir das amplitudes
- Resultado Python medido: Bounds preserva os limites reais; negative tem área 12 e diagonal 5. Na Sprint 4, Lengths aplica ceil(hypot(amplitudes)): fixture [10,30]×[20,50] produz diagonal 36.05551275463989 e marcador 37, versus 59 da fórmula antiga com os mesmos limites reais (derivação). Translação e escala testadas; curvas e marcador continuam visíveis para polilinhas que excedem a diagonal.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Correção geométrica S01-05 integrada aos gráficos conforme S04-03 em 13/11/2026. Ceil do fonte preservado; amostragem/convenção angular não alteradas.
- Estado: Correção técnica de amplitudes/limites integrada/testada. Caso nativo negativo específico permanece indisponível; não se confunde derivação estática com execução MATLAB.

## Q-09 — P0

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 5.
- Evidência estática original: Conversor SVG é textual e sensível à ordem/forma de atributos; não aplica transformações gerais; limpeza de TXT vazios busca `*_converted.txt` em toda a pasta atual (`convertSVG2txt_colour2.m:369–376`)
- Entrada / reprodução: simple.svg, multicolour.svg; atributos/transformações e TXT alheio sentinela na Sprint 5.
- Resultado original executado: **disponível** — conversor original executado em simple.svg e multicolour.svg, em sprint16/native/exports. As chamadas terminam sem exceção, mas geram nós com NaN e omitem elementos/grupos do fixture; sucesso do callback não prova geometria válida. Comparação em sprint16/svg-comparison.json.
- Resultado proposto / critério a verificar: Limitar limpeza aos arquivos criados naquela conversão e definir parser/subconjunto SVG seguro e verificável
- Resultado Python medido: XML estruturado define subconjunto M/L, line/polyline; comandos/transformações/CSS/polygon fora do contrato rejeitam o documento antes de publicar. Tabelas/cores vêm de lista explícita, nunca glob de limpeza/importação. Testes preservam arquivos alheios/vazios/cores antigas e resultados obsoletos; ADR 0006.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto a quantificar: valores/classes/limiares e respectivas figuras/TXT; sem aceitação de paridade até concluir comparação e decisão.
- Decisão / autor / data: Política de subconjunto e correções de integridade solicitadas em S05-01/02/07 aplicadas em 14/11/2026; sem aproximação científica de curvas ou modos adicionais.
- Estado: Subconjunto XML e integridade de escrita/limpeza concluídos e testados; captura nativa confirma saída inválida do parser textual no fixture. O port preserva os elementos aceitos sem aproximar curvas ou transformações.

## Q-10 — P1

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 3/4.
- Evidência estática original: Correção de norte é subtraída e arredondada, embora o manual diga adicionada; normalização angular não usa módulo completo; TXT ângulo/comprimento e `segmentdata` usam ângulo original
- Entrada / reprodução: matlab_round, angles_flip_00/10/01/11; norte ±360 e TXT bruto/corrigido.
- Resultado original executado: **disponível** — doubleAngles/reverseAxis originais executados com norte−360/0/12.5/360 e ângulos [0,.5,30,90,179.5]; vetores em sprint16/native/angular_conventions.mat. TXT Lengths/EZROSE reais preservam suas convenções distintas.
- Resultado proposto / critério a verificar: Fixar convenção angular única e documentar/exportar dados corrigidos de forma consistente
- Resultado Python medido: **Sprint 3:** doubleAngles/reverseAxis preservados sem módulo completo. Norte −360 e direção 30 dão [390,570]; hist inclui caudas, rosa exclui e console avisa. Empates −0,5/179,5 de strike preservam índices adjacentes. EZROSE contém vetor corrigido; convenções de Lengths/segmentdata permanecem distintas conforme o fonte. Testes e ADR0004; a auditoria S16 confirmou a preservação da convenção, sem promover unificação. Na Sprint 4, cross-plot usa os ângulos corrigidos/duplicados/invertidos e o TXT de pares mantém ângulos brutos, com a mesma máscara de censura dos comprimentos (ADR 0005).
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto a quantificar: valores/classes/limiares e respectivas figuras/TXT; sem aceitação de paridade até concluir comparação e decisão.
- Decisão / autor / data: Auditoria S16 preserva a convenção do fonte conforme política de paridade já autorizada no PRD: subtrair norte, arredondar, duplicar, wrap único e flips; pares/segmentdata brutos e EZROSE corrigido. Não promover a unificação sugerida sem nova decisão científica; ela fica fora desta entrega.
- Estado: Convenções preservadas e comparadas com execução nativa. Unificação não implementada nem requisito para reproduzir o fonte; limites de norte e avisos documentados.

## Q-11 — P0

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 9.
- Evidência estática original: Manual descreve snap I→Y para undershoot/overshoot; código depende de interseções existentes e tem criação de novos Y comentada (`getConnectivity.m:135–168`); há referências a `xint`/`XU` sem garantia de inicialização
- Entrada / reprodução: isolated, tee, cross, no_crossing, undershoot, overshoot.
- Resultado original executado: **disponível** — MATLAB R2024b Update 9 executado. Tee com tolerância 0: I=3/Y=0/X=1; tee .2: I=3/Y=1/X=0; cross: I=4/Y=0/X=1; overshoot .2: I=3/Y=1/X=0; kink-cross: I=4/Y=1/X=0. Isolated falha por XU indefinido e undershoot falha por xint indefinido. Entrada/script e resultados em tests/reference/sprint9/native/native_topology.json.
- Resultado proposto / critério a verificar: Implementar ou delimitar o snap; testar rede sem cruzamentos, só I, só X, só Y, duplicatas e junções próximas
- Resultado Python medido: Implementado e testado por API e Run no registro padrão, após aprovação explícita do usuário. Interseções exatas, pontas reais, proximidade finita, deduplicação, bordas e classes vazias; tee_zero passa a I=3/Y=1/X=0, undershoot a I=3/Y=1/X=0 e kink-cross a I=4/Y=0/X=1. Mapas/ternário/TXT preparados.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto medido: parâmetros/caudas ou classes/contagens e figuras/TXT conforme a comparação concreta vinculada à ADR. Diferença deliberada aprovada; não se declara igualdade com os resultados científicos alterados do legado.
- Decisão / autor / data: **aprovada pelo usuário em 14/11/2026**, pela mensagem “Aprovo as Q-15 e a Q-11.” Proximidade euclidiana inclusiva de ponta real a segmento finito de outro traço, undershoot com Y inferido, vértices internos não são pontas e T exato com tolerância zero é Y. Comportamento aprovado ativado no registro padrão, sem criar modo científico alternativo.
- Estado: correção científica aprovada, implementada e ativa na GUI padrão; testes e referência nativa documentados. Revisão visual concluída nos contextos documentados da S16-04, sem declaração de identidade com os resultados defeituosos do legado.

## Q-12 — P1

- Tipo: misto; validação técnica e decisão científica do raster/desempate wavelet.
- Sprint responsável: 14.
- Resultado original executado: **disponível** — MATLAB R2024b Update 9. Coeficientes/self/eta dos dois kernels em imagem 5×8 e figuras/TXT reais da variante wavelet2 em 8×8; raster integrado real 1944×1944. Chamadas com passo 40/270 falham MATLAB:badsubscript; imagem 8×6 falha MATLAB:subsassigndimmismatch. Captura em scripts/capture_native_s1415.m e tests/reference/sprint14/native.
- Resultado Python medido: erro máximo dos coeficientes/self abaixo de 5e−15 sobre a mesma entrada; Morlet em 8×8 exporta exatamente os 76 ângulos nativos. Raster candidato mantém 27 inches/72 dpi, margens e regra 45%/linhas 4/1 ponto; difere em 0.247305% dos pixels, erro absoluto médio .36059 de 255, devido ao motor/rounding/limites. Não se afirma identidade de rasters.
- Proposta: validar listas positivas inteiras sem eval e incremento inteiro divisor de 180; usar ny×nx para retângulos, preservar pixels/ausência de norte e tratar população vazia. Raster determinístico Agg com envelope dos nós e margens originais; aceitar explicitamente sua diferença da impressão MATLAB. Para empates de WC dentro de rtol=1e−12/atol=1e−14, escolher primeiro L e depois primeiro theta, mantendo o maior coeficiente real. Em Mexican/L=1, theta é fisicamente indeterminado e arredondamentos FFT mudam escolhas discretas; referência e proposta estão quantificadas no JSON.
- Entrada, fundamento e impacto: tests/reference/sprint14/candidate/q12_comparison.json; alteração do raster pode mudar coeficientes, limiar, rosa e TXT; desempate pode mudar theta/L sem mudar WC fora da precisão declarada. A máscara estrita WC>0.5×máximo permanece.
- Decisão / autor / data: **aprovada explicitamente pelo usuário em14/11/2026: “Aprovo a Q-12.”** Raster, amostragem axial, correção ny×nx e desempate conforme proposta registrada; a aprovação é própria desta família, independente de Q-14.
- Estado: implementado e ativo no Run padrão, com referências nativas preservadas e diferenças aprovadas explícitas. Dois casos completos1944×1944, Qt e barras responsivas verificados; revisão dos contextos capturados concluída na S16-04, com diferenças e aceites explícitos.

## Q-13 — P1

- Tipo: validação/integridade operacional; não altera valores de perfis válidos.
- Sprint responsável: 13.
- Evidência original: guiFracPaQ2D.m:1177 rejeita seleção pela soma das coordenadas; guiFracPaQ2Dgraphs usa xInt sem inicialização quando não há interseções.
- Entrada / reprodução: mesma rede da captura, linha horizontal sem interseções em y=10 e linha de comprimento zero; linha válida (-6,0)→(6,0), cuja soma é zero.
- Resultado original executado: **disponível** — chamadas reais de guiFracPaQ2Dgraphs falham com MATLAB:UndefinedFunction / “Unrecognized function or variable 'xInt'” para ausência de interseções e comprimento zero. A rejeição pela soma pertence ao callback da GUI e foi inspecionada estaticamente, não simulada como uma chamada nativa. [Registro](../../tests/reference/sprint13/native/native_calls.json).
- Resultado Python medido: ProfileLine exige dois pontos finitos distintos; seleção ausente identifica Select end points antes de exportar. Soma zero é válida. ALONG sem interseções retorna vetores vazios e figuras com mensagem; FROM continua usando a reta suporte infinita. Seis perfis válidos coincidem com os arrays nativos até 1e−12.
- Fundamento: requisitos GRA-01/02 e Q-13; validação geométrica, sem tolerância espacial nova e sem inventar observações.
- Impacto: corrige seleção/estado/ausência de dados; valores científicos de casos válidos preservados. Preview Hough permanece em cache; nenhuma tentativa de lê-lo como TXT.
- Decisão / autor / data: implementação técnica prevista no PRD, 14/11/2026; não depende das decisões científicas Q-14/P20.
- Estado: implementado e testado no Run, com eventos do canvas, cancelamento, invalidação e snapshot imutável.

## Q-14 — P1

- Tipo: científico; aprovação necessária antes de alterar os resultados de blocos.
- Sprint responsável: 12.
- Entrada / reprodução: dois retângulos fechados 40×40 em (10,10)..(50,50) e (70,30)..(110,70), além de casos aninhados e oblíquos; escala 10 pixels/metre.
- Resultado original executado: **disponível** — MATLAB R2024b Update 9, guiFracPaQ2Dlength original, BMP e três figuras por caso. Sem escala: BMP 100×60, áreas [2721,1368,1368], incluindo o exterior; centroides desenhados [(60.50349,39.49614),(31.5,29.5),(89.5,49.5)]. Com escala 10: BMP 10×6, áreas [5,2,6,2], ainda contagens de pixels. Fonte e matrizes em tests/reference/sprint12/native. A geometria de impressão depende também do arredondamento da figura em pixels de tela.
- Resultado proposto / critério: raster determinístico do envelope completo dos traços a 300 dpi/.5 ponto, fixo nas coordenadas originais sem escala; componentes brancos com conectividade 8, excluindo os que tocam a borda. Converter áreas/centroides pelo tamanho real de pixel e pela escala, com centros de pixel corretos. Continua sendo rasterização, não poligonização vetorial.
- Resultado Python medido: no Run padrão aprovado, duas áreas [1444,1444] pixels e centros [(30,30),(90,50)]; com escala 10, mesmo BMP 100×60 e áreas [14.44,14.44] metres². Diferenças incluem a política de exterior, raster/viewport e transformação de coordenadas. Registro em tests/reference/sprint12/candidate/q14_comparison.json.
- Fundamento: medir somente blocos fechados e preservar a mesma amostragem ao mudar a unidade; explicitar área branca rasterizada após a espessura dos traços.
- Impacto: contagem, áreas, centroides e figuras mudam deliberadamente; casos constantes/vazios passam a produzir saída completa controlada.
- Decisão / autor / data: **aprovada pelo usuário em 14/11/2026**, na mensagem “Aprovo ambos Q-14 e Extensão Q-20.” Escopo: raster determinístico fixo nas coordenadas originais, exclusão de componentes que tocam a borda e calibração de áreas/centroides; sem equiparar áreas rasterizadas às áreas vetoriais.
- Estado: Q-14 aprovada e integrada ao Run padrão; Block size graphs gera as três figuras, BMP visível e três TXT de Lengths. Referências nativas preservadas e diferenças de raster/população/calibração declaradas.

## Q-15 — P1

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 8.
- Evidência estática original: Chamadas MLE em `guiFracPaQ2Dlength` não alinham todos os nomes de retorno às assinaturas; cortes usam índices com semântica a revisar; lognormal busca xmin sem truncar a amostra no laço (`fittingLognormal.m:89–107`)
- Entrada / reprodução: histogram_centres; vetores MLE compartilhados/cortes na Sprint 8.
- Resultado original executado: **disponível** — MATLAB R2024b Update 9 executado com x=[1,2,3,4,6,10,18,40], sem cortes e com uc=10/lc=20. A lei de potência devolve a mesma cauda incluindo 18/40 após a busca cortada; lognormal devolve os mesmos mu/sigma, ignorando esses cortes no ajuste final. Resultados em tests/reference/sprint8/native/native_fits.json; 7500 comparações K-S com vetores compartilhados também conferidas.
- Resultado proposto / critério a verificar: Validar algoritmos, sentido dos cortes, retorno de todos os parâmetros, repetidos/zeros e tamanho mínimo de amostra
- Resultado Python medido: Implementado e testado por API e Run no registro padrão, após aprovação explícita do usuário. Uma seleção de cortes para busca e ajuste final, busca lognormal por cauda/CDF complementar consistente; 2500 testes/modelo, alpha .1/.05 preservados. D nativo idêntico nos 7500 vetores; maior erro de p=2.22e-16 e decisões idênticas. Seis figuras e cache Lengths preparados.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto medido: parâmetros/caudas ou classes/contagens e figuras/TXT conforme a comparação concreta vinculada à ADR. Diferença deliberada aprovada; não se declara igualdade com os resultados científicos alterados do legado.
- Decisão / autor / data: **aprovada pelo usuário em 14/11/2026**, pela mensagem “Aprovo as Q-15 e a Q-11.” Lower remove os menores, Upper os maiores, mesma seleção na busca/ajuste final e lognormal por cauda com frequências complementares no mesmo sentido. Comportamento aprovado ativado no registro padrão, sem criar modo científico alternativo.
- Estado: correção científica aprovada, implementada e ativa na GUI padrão; testes e referência nativa documentados. Revisão visual concluída nos contextos documentados da S16-04, sem declaração de identidade com os resultados defeituosos do legado.

## Q-16 — P1

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 2/12/14/16.
- Evidência estática original: Imagens intermediárias de blocos/wavelets têm nomes fixos; arquivos finais abrem em modo de escrita e podem sobrescrever resultados
- Entrada / reprodução: mixed; mesma tag e tags diferentes; destinos isolados.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Definir política de nomes por execução e temporários isolados; conferir execuções sucessivas
- Resultado Python medido: PNG/TXT/conversões são preparados em temporários próprios e substituídos por os.replace. BMP de blocos e raster wavelet preservam nomes fixos visíveis. Mesma tag substitui; tags distintas coexistem. Falhas de staging e limpeza restrita testadas; substituições de vários arquivos não formam uma transação conjunta.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Correção técnica conforme EXP03/04 e S16-03; nomes/gatilhos legados preservados, nenhuma limpeza por glob. Não adicionar nomes científicos alternativos.
- Estado: Integridade de exportação implementada/testada; limitação de atomicidade por arquivo explicitada na documentação.

## Q-17 — P1

- Tipo: misto/científico; decisão necessária antes de alterar o padrão de estabilidade.
- Sprint responsável: 3/11.
- Evidência estática original: Ts/Sf normalizam antes da correção de norte/flips/azimute; Sf arredonda antes de multiplicar por 100, reduzindo cores; mapa CSF usa ≥, rosa usa >. Comprimentos mantêm índice linear com barra logarítmica desde a Sprint 3.
- Entrada / reprodução: duas fraturas ortogonais (0°/90°), sigma1=100, sigma2=50, azimute=30°, C0=2, Pf=10, mu=.6. MATLAB R2024b Update 9, script scripts/capture_native_s1011.m; casos degenerados e quatro famílias também executados.
- Resultado original executado: **disponível** — sn=[62.5,87.5], tau=[21.650635094610966,21.650635094610966], Tsmax preliminar=0 e TsNorm=Inf. A chamada real guiFracPaQ2Dtracemap falha com MATLAB:badsubscript. Sf=[19.748941508981723,44.74894150898172], mas escala preliminar=[43.333333333333336,93.33333333333333] e ambos os índices=1. No caso de igualdade (sigma1=sigma2=100, mu=C0=Pf=0), mapa classifica CSF e rosa não. Arrays MAT, 18 PNGs e native_calls.json em tests/reference/sprint11/native.
- Resultado proposto / critério a verificar: normalizar pelos valores dos segmentos já corrigidos; mesma escala nos mapas/rosas, índices saturados, mapeamento Sf linear e critério CSF ≥ nos dois. Recusar apenas combinações indefinidas mu=0/Sf e sigma1=sigma2/Td, validar compressão positiva ordenada; constantes têm normalização zero sem alterar as grandezas. Preservar a convenção legada de cores por comprimento já documentada.
- Resultado Python medido: núcleo implementado e integrado ao Run padrão, TsNorm=[1,.7142857142857143], faixa Sf=[19.748941508981723,44.74894150898172], índices Sf=[1,100]; igualdade CSF em mapa e todos os 36 centros de bins. Comparação em tests/reference/sprint11/q17_comparison.json; mapas, rosas, Mohr e segmentdata ativos na GUI padrão. O registro candidato anterior à aprovação está preservado na subpasta candidate.
- Fundamento: eliminar divisão por zero e incoerência de normalização/cor/classe; mudança de resultado científico depende da aprovação do usuário exigida pelo PRD.
- Impacto medido: valores normalizados, cores/legendas e classificação no limite mudam; fórmulas físicas sn/tau/Ts/Td/Sf e arquivo segmentdata são preservados. Mapas de comprimento conservam o comportamento da referência com a divergência de legenda explícita.
- Decisão / autor / data: **aprovada explicitamente pelo usuário em 14/11/2026**, pela mensagem “Aprovo a correção Q-17.” A pergunta incluía a correção de estabilidade/igualdade/validação e a preservação da convenção legada de cores por comprimento. ADR 0013 registra o algoritmo único promovido a padrão.
- Estado: correção científica aprovada, implementada, testada e ativa no Run padrão. Comprimentos preservam a convenção legada aceita. Comparações de dados, paletas, arquivos e calibração visual registradas; revisão visual concluída nos contextos documentados da S16-04, preservando as diferenças aceitas.

## Q-18 — P2

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 2/16.
- Evidência estática original: Mensagem final fala em `.tif`, mas `guiPrint.m:35–36` grava PNG; comentários preservam antigas alternativas TIFF/JPEG
- Entrada / reprodução: qualquer figura via guiPrint; conferir PNG e mensagem.
- Resultado original executado: **disponível** — guiPrint executado nas capturas S8–S16 gera PNG600dpi; fonte dos callbacks ainda contém mensagens TIFF. As capturas não são reclassificadas como teste de cada mensagem de console legado.
- Resultado proposto / critério a verificar: Mensagens e documentação refletirem o formato efetivamente exportado
- Resultado Python medido: Exportador da base grava PNG com mensagem Saved/Replaced PNG no console. Testes inspecionam formato, nome, tamanho e DPI do PNG real. Nenhuma mensagem de conclusão da base promete TIFF.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Apresentação técnica alinhada a guiPrint, conforme S02-09 em 13/11/2026.
- Estado: Auditoria das rotas e exportadores concluída: PNG/TXT/BMP indicados corretamente, sem promessa de TIFF nos resultados da GUI. TIFF restrito à ferramenta explícita de preparação.

## Q-19 — P2

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 5/15.
- Evidência estática original: Há scripts com assinaturas antigas, nome de função diferente do arquivo e recursos externos ausentes; exemplos em vírgulas convivem com leitor GUI tabulado
- Entrada / reprodução: examples.json; souter_all_colour24378D.txt em vírgulas; catálogo de legado.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Classificar legado, parametrizar utilitários e disponibilizar exemplos válidos; ver apêndice
- Resultado Python medido: Os19AUX e164 arquivos têm destinação em docs/parity/legacy.md e legacy-files.json. Ferramentas preprocess/Move, diálogo wavelet e APIs válidas entregues/testados; variantes incompletas, GUI2.2 semFIG e site histórico preservados. Exemplos preparados explícitos, sem modificar originais.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Destinação técnica concluída na Sprint15 e auditada na S16; scripts históricos não viram entrypoint nem recurso obrigatório.
- Estado: Destinação concluída; limitações dos exemplos/experimentos documentadas, sem simular recursos científicos ausentes.

## Q-20 — P1

- Tipo: misto/científico; avaliar impacto e obter decisão antes de alterar padrão.
- Sprint responsável: 7/13.
- Evidência estática original: Estimativas circulares usam teste de secante com condição adicional de mudança de sinal em X **e** Y (`guiFracPaQ2Dpattern.m:226–239`; repetido em Graphs)
- Entrada / reprodução: circle_horizontal_0/7, circle_vertical_0/7, circle_oblique_0/7, circle_tangent, circle_internal_0/7.
- Resultado original executado: **disponível** para Graphs na Sprint 13 — nove figuras/arrays e chamada apenas density com três figuras, em tests/reference/sprint13/native. Capturas nativas específicas da bateria de predicados Maps continuam pendentes; a reprodução estática anterior não foi reclassificada como nativa.
- Resultado proposto / critério a verificar: Validar contagem para linhas horizontais, verticais, oblíquas, tangentes e círculos transladados
- Resultado Python medido: Contagem finita implementada/testada. Horizontal (−2,0)→(2,0), r=1: n=2/P21=.5, contra n=0/P21=0 na tradução estática do fonte. Tangente: n=1; extremos estritamente internos para m. Translações, linhas verticais/oblíquas, bordas e reversões verificadas. [Reprodução estática](../../tests/reference/sprint7/q20_static_reproduction.json), sem execução MATLAB.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; há possibilidade de alterar resultado científico.
- Impacto a quantificar: valores/classes/limiares e respectivas figuras/TXT; sem aceitação de paridade até concluir comparação e decisão.
- Decisão / autor / data: Usuário, 14/11/2026: **“Corrigir a contagem geométrica”**, após exemplo concreto e escolha entre correção e preservação do predicado legado. Critérios completos na [ADR 0008](../decisions/0008-circular-sampling.md).
- Estado: Contagem finita Maps/Graphs e normalização P20 aprovadas e ativas. S16 acrescenta chamada Maps original real e TXT/capturas; resultados defeituosos permanecem preservados, sem declarar identidade com o método corrigido.

**Extensão identificada na Sprint 13 — P20:** a chamada real de guiFracPaQ2Dgraphs usa m/(2πr), enquanto Maps usa m/(2πr²). Para r=2 e m=[0,2,0], Graphs retorna [0,.1591549431,0]; a proposta dimensionalmente consistente é [0,.0795774715,0]. Dados e comparação em tests/reference/sprint13/candidate/q20_density_comparison.json. A aprovação anterior cobre a contagem geométrica. **A extensão de normalização foi aprovada explicitamente pelo usuário em 14/11/2026: “Aprovo ambos Q-14 e Extensão Q-20.”** P20=m/(2πr²) está ativo no Run de Graphs, preservando a contagem finita autorizada; selecionar P21 e/ou P20 gera mapa e ambos os perfis uma única vez.

## Q-21 — P1

- Tipo: integridade, validação, apresentação ou destinação técnica conforme PRD.
- Sprint responsável: 2/6.
- Evidência estática original: Preview aplica escala, mas Run relê o campo sem reconstruir necessariamente a geometria; mudança posterior pode gerar rótulos incompatíveis
- Entrada / reprodução: scaled, mixed, rectangular_cwt; alterar escala/parâmetro após Preview.
- Resultado original executado: **indisponível**; capturar valor/arquivo ou falha, sem inferir execução da leitura do fonte.
- Resultado proposto / critério a verificar: Invalidar/refazer prévia quando escala, arquivo ou parâmetros de extração mudarem
- Resultado Python medido: Preview é invalidado por arquivo/tipo/escala/Hough. Revisão descarta resultado assíncrono obsoleto; Run compara configuração e stamp do arquivo. Testes mudam escala durante leitura e arquivo externamente; nenhum resultado antigo libera Run.
- Fundamento: PRD, política de fidelidade, RF relacionado e caso analítico; a correção deve preservar os resultados de entradas válidas.
- Impacto a quantificar: fluxo, integridade, consistência de dados e arquivos; medir ausência de regressão nas análises relacionadas.
- Decisão / autor / data: Correção de integridade prevista em S02-08 aplicada em 13/11/2026.
- Estado: Invalidação integrada para TXT/SVG/Hough, escala e perfil; resultados obsoletos impedidos de publicar. Testes de revisão/stamp e seis abas concluídos.
