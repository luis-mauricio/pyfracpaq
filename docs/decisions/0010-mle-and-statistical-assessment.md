# ADR 0010 — MLE, cortes e avaliação estatística (Q-15)

14/11/2026. Estado: **Q-15 aprovada e implementação ativada no Run padrão**. Após a reprodução concreta e a revisão das propostas, o usuário declarou: **“Aprovo as Q-15 e a Q-11.”** A aprovação autoriza os cortes coerentes e a busca lognormal por cauda descritos abaixo. LEN-07 está associado a compute_lengths/render_mle no registro padrão. O registro temporário de revisão foi removido; há um único comportamento científico, sem novo modo/controle na GUI.

## Reprodução nativa e diferença proposta

MATLAB **24.2.0.3212159 / R2024b Update 9** foi executado em processo batch separado, com preferências em /tmp e figuras invisíveis. Os fontes FracPaQ não foram editados. O script `capture_native_s89.m` salva os dados em tests/reference/sprint8/native e usa x=[1,2,3,4,6,10,18,40], rng(77,'twister') e cores azuis. Os PNGs MLE nativos foram impressos a 150 dpi para inspeção; não são referências de exportação GUI a 600 dpi nem aprovação de SSIM.

Sem cortes, a referência retorna PL alpha=1.7778106756553362/xmin=2, exponencial lambda=.10526315789473684/xmin=1, lognormal mu=1.7314562005725183/sigma=1.1236141500905636/xmin=1. Os parâmetros do port coincidem nesse exemplo, dentro do contrato de tolerância.

Com os argumentos nativos uc=10 e lc=20, a janela de busca inicial é [1,2,3,4,6,10]. PL volta à entrada inteira no ajuste final e mantém [2,3,4,6,10,18,40]; exponencial mantém [1,2,3,4,6,10]; lognormal volta à amostra inteira e mantém mu/sigma inalterados. A busca lognormal nativa usa a mesma amostra em todos os candidatos e compara CDF crescente com frequência complementar decrescente. Os retornos de seis/sete posições também não correspondem aos cinco/seis nomes do chamador GUI. O `y` retornado por PL/exp já foi reduzido pelo laço ao último port; usá-lo nos marcadores concentra ambas as linhas no máximo.

O port usa Lower cut-off para remover ceil(n×lower/100) menores e Upper cut-off para remover ceil(n×upper/100) maiores, após ordenação estável. Para esse mesmo exemplo, lower=20/upper=10 mantém [3,4,6,10,18]. A mesma seleção vale para busca, ajuste final e linhas de corte. Lognormal recalcula a cauda de cada xmin e compara frequências complementares no mesmo sentido. Essa mudança de resultados foi **aprovada explicitamente em Q-15 pelo usuário em 14/11/2026**. [Comparação](../../tests/reference/sprint8/candidate/q15_comparison.json) contém parâmetros, caudas e distâncias propostas junto aos resultados nativos.

## Equações e validação

Busca em valores únicos crescentes, com pelo menos duas observações e dois valores distintos por cauda. Empates de distância usam o menor xmin. PL: alpha=1+n/sum(log(z/xmin)); exponencial: lambda=1/mean(z−xmin); lognormal: média e desvio populacional dos logs. A correção finita opcional da API PL aplica alpha×(n−1)/n+1/n depois da busca, como no fonte; não há controle novo na GUI.

O ajuste lognormal continua sendo o método de momentos/MLE normal dos logs da cauda selecionada, conforme as equações fornecidas; não foi substituído por otimização de uma lognormal condicionalmente truncada nem por `.fit()` do SciPy. A busca proposta corrige a seleção e o sentido das curvas, sem apresentar outro estimador como se fosse o original. As curvas estimadas conservam as fórmulas Plot*, inclusive a escala pela frequência observada no xmin. O desenho observado usa valores únicos como no fonte; ajuste e K-S mantêm todas as repetições.

Valores zero, negativos, não finitos, amostra com menos de dois valores distintos, cortes que esgotam a amostra e parâmetros não representáveis são recusados antes dos TXT da família. Não se adiciona jitter nem epsilon a denominadores. Censura continua usando a máscara comum da Sprint 4. Unidades: alpha/sigma invariantes, xmin escala linearmente, lambda inversamente e mu pela translação do log da escala.

## K-S e Monte Carlo

Cada modelo conserva **2500** comparações de duas amostras, hipótese bilateral e p-valor assintótico, sem escolha `auto`. D compara os dois degraus empíricos com inclusão de empates. O p usa a série de Kolmogorov de 101 termos com n efetivo e correção sqrt(n)+.12+.11/sqrt(n), conferida contra o MATLAB instalado. Rejeição: p≤alpha. PL mantém alpha=.1; exponencial/lognormal .05. A segunda taxa conta p>.05 em todos os modelos. Ambas são resultados desse procedimento, **não probabilidades posteriores do modelo**. A [documentação MathWorks](https://www.mathworks.com/help/stats/kstest2.html) descreve o p assintótico e a decisão por significância.

`shared_ks_inputs.mat` contém 2500 vetores/modelo em unidades padronizadas: Exp(1) para PL/exponencial e N(0,1) para lognormal. Transformações monotônicas evitam overflow sem alterar o teste de duas amostras. Os mesmos vetores foram passados ao kstest2 nativo; **7500 distâncias D coincidem exatamente, p difere no máximo 2.22e−16 e todas as decisões coincidem**. Arquivos MAT de saída, comparação JSON e versões foram preservados. Isso não implica identidade de RNG entre bibliotecas.

Gerador local PCG64; API aceita seed e vetores compartilhados. Sem seed, a GUI usa entropia local e registra a seed raiz; seis substreams independentes cobrem os três modelos de cada população. Não modifica np.random global. Resultados incluem seed, parâmetros, caudas, perfis, vetores D/p, rejeições e taxas, com arrays somente para leitura. Vinte repetições independentes verificam variação Monte Carlo. Caudas pequenas geram aviso sobre a aproximação assintótica, sem chamar não rejeição de prova de distribuição.

## Integração e figuras

LengthResult carrega MleResult opcional. `compute_lengths` calcula todas as seleções Lengths uma vez por Run e só exporta os três TXT após o sucesso de todos os ajustes. LEN-07 usa o mesmo cache; o registro padrão habilita a associação, mantendo a dependência de Log-log. Run da GUI padrão com Log-log+MLE gera dez PNGs (quatro log-log e seis ajustes) e três TXT, sem duplicar cálculos/arquivos. Interrupção é consultada na busca, simulações e antes da exportação; renderização permanece na thread principal.

Seis nomes originais, cores do conjunto, curvas :s/−., cortes vermelhos tracejados, legenda superior direita e parâmetros gregos em caixa branca. PL log/log, exponencial linear/log, lognormal log/linear. Retângulo do plot .13/.11/.775/.815 e caixa com topo .325 reproduzem a composição default observada na referência; unidades e população vêm do Dataset. Autoscaling/ticks ainda dependem de homologação visual nativa. Exportação comum 20×20 cm/600 dpi. [Figuras e arrays](../../tests/reference/sprint8/candidate/validation.json). Não há novas barras nestas figuras.

## Decisão e limite de aceite

A aprovação explícita do usuário encerra a decisão Q-15 e S08-08. A GUI padrão executa o algoritmo documentado, e os testes de Run usam MainWindow sem injeção de registro alternativo. A Sprint 8 está implementada e validada; permanece pendente a homologação visual integral das figuras MATLAB, que não é inferida da aprovação da correção científica.
