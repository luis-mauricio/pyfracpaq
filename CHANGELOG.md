# Alterações do port

## Em desenvolvimento —15/11/2026

Comparação real com SD11A.txt indicado pelo usuário:51 figuras pareadas e81 confrontos de arrays/curvas, com diferenças científicas aprovadas e pendências visuais explícitas. Execução integrada da função principal Wavelets no MATLAB e conferência adicional do núcleo sobre pixels nativos. EZROSE agora preserva a ordem dos empates de zeros assinados, produzindo o TXT idêntico ao original. Suíte completa:686 testes passaram. [Relatório](docs/parity/sd11a.md). Os pacotes0.1.0rc1 da entrega anterior continuam congelados; esta alteração no código-fonte ainda não está nesses pacotes.

## 0.1.0rc1 — candidato local,14/11/2026

Sprints0–15 integradas e auditoria S16 com referências nativas dos53 nomes de figuras/14 tipos de dados. Hough corrigido para igualdade exata de votos/picos/endpoints em cinco casos. Q05 aprovada explicitamente; Q10 mantém as convenções originais. GUI Helvetica/fallback, calibração de histogramas/títulos/ticks e barras de strike; contrato responsivo das barras preservado. Apresentação por eventos Qt e fechamento padrão das figuras. Entrega com wheel, instalação limpa offline, configurações VS Code, medições e evidências.

Esta versão do port não é FracPaQ2.8:2.8 identifica a referência MATLAB. Q05/11/12/14/15/17/20 têm diferenças científicas autorizadas, detalhadas nas ADRs. A homologação visual integral continua aberta, com métricas abaixo do limite em contextos documentados. Windows/Linux foram adiados pelo usuário. Não se publica uma versão estável com declaração de identidade geral.
