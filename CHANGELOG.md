# Alterações do port

## 0.9.0rc1 — pré-versão nos fontes, 16/11/2026

README em inglês e manual ilustrado em duas versões, pt-BR e inglês britânico, com fontes LaTeX e PDFs compilados. Ambas cobrem os mesmos 30 recursos, fórmulas e 51 figuras; a terminologia inglesa acompanha a aplicação (colour, centre, normalisation).

**Ponto 4 pelo código:** requirements.txt preservado com pins e instrução de uso; README simplificado, documentação técnica preservada em docs/development.md e ZIP de uso sem testes/relatórios por export-ignore. Cópia enxuta executada sem instalar o projeto em ambientes CPython 3.13.18 e Miniforge Python 3.13.13; dois entrypoints por ambiente, Preview/Run e 32 saídas conferidos. Abertura/Preview nativos pelo VS Code também conferidos. Nenhuma publicação realizada.

**Definição de distribuição pelo usuário:** código no GitHub para clone/download ZIP e execução pela pasta, com Python, VS Code ou ambiente Miniforge. Sem instalador/wheel como entrega ao usuário e sem instalar o pacote do projeto. O ponto 4 foi redefinido para validar esse fluxo e continua aberto. Artefatos de empacotamento descritos abaixo são internos, anteriores a essa definição. [ADR 0019](docs/decisions/0019-source-distribution.md).

S16-04 concluída nos contextos documentados: comparações numéricas/semânticas por família, aceite dos cinco títulos e duas vistas Hough e aprovação dos 16 detalhes após substituir os marcadores por quadrados/círculos normais do Matplotlib. As métricas brutas e diferenças científicas autorizadas permanecem explícitas. O ajuste EZROSE mantém a ordenação estável dos zeros assinados; Hough coincide nos cinco casos numéricos capturados. [Notas da versão e diferenças aceitas](docs/releases/0.9.0rc1.md).

A janela inicia com toda a largura útil da tela, incluindo bordas nativas, mantendo altura limitada, centralização vertical e redimensionamento livre. Logo PyFracPaQ fornecido pelo usuário, ampliado aproximadamente 12% sem deformação; rodapé com versão 0.9.0rc1, November 2026 e luismauricio@me.com em uma linha. Barras de cores preservam alinhamento e distância fixa aos rótulos no redimensionamento e na exportação.

S16-09.1: interface macOS revisada em 48 capturas principais e dez adicionais, com sete controles nativos e 81 testes GUI aprovados. S16-09.2: 53 PNGs com RGB idêntico às referências finais, identificação 0.9.0rc1, 11 arquivos principais idênticos byte a byte e 282 testes direcionados aprovados; tags, unidades, conversões e substituição conferidas. S16-09.3: versão e documentação consolidadas. A última suíte completa registrada tem 726 testes; os resultados direcionados posteriores são contabilizados separadamente.

**Histórico técnico anterior à definição de distribuição:** wheel, sdist e ZIP completo de fontes 0.9.0rc1 em dist/0.9.0rc1/, com hashes e validação registrados separadamente. A disponibilização é o ponto 5 e permanece pendente. Os artefatos 0.1.0rc1 em dist/ continuam históricos e não contêm estas alterações. Windows/Linux permanecem para seus testes posteriores.

## Em desenvolvimento —15/11/2026

Comparação real com SD11A.txt indicado pelo usuário:51 figuras pareadas e81 confrontos de arrays/curvas, com diferenças científicas aprovadas e pendências visuais explícitas. Execução integrada da função principal Wavelets no MATLAB e conferência adicional do núcleo sobre pixels nativos. EZROSE agora preserva a ordem dos empates de zeros assinados, produzindo o TXT idêntico ao original. Suíte completa:686 testes passaram. [Relatório](docs/parity/sd11a.md). Os pacotes0.1.0rc1 da entrega anterior continuam congelados; esta alteração no código-fonte ainda não está nesses pacotes.

## 0.1.0rc1 — candidato local,14/11/2026

Sprints0–15 integradas e auditoria S16 com referências nativas dos53 nomes de figuras/14 tipos de dados. Hough corrigido para igualdade exata de votos/picos/endpoints em cinco casos. Q05 aprovada explicitamente; Q10 mantém as convenções originais. GUI Helvetica/fallback, calibração de histogramas/títulos/ticks e barras de strike; contrato responsivo das barras preservado. Apresentação por eventos Qt e fechamento padrão das figuras. Entrega com wheel, instalação limpa offline, configurações VS Code, medições e evidências.

Naquela entrega, a homologação visual S16-04 e a revisão/publicação S16-09 ainda estavam abertas. Q05/11/12/14/15/17/20 registravam diferenças científicas autorizadas, detalhadas nas ADRs. O encerramento posterior da S16-04 e as mudanças atuais pertencem aos fontes 0.9.0rc1 descritos acima. FracPaQ2.8 identifica sempre a referência MATLAB, não a versão do port. Windows/Linux foram adiados pelo usuário.
