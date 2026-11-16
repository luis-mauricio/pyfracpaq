# PyFracPaQ 0.9.0rc1

November 2026 · luismauricio@me.com. Pré-versão do port Python; **FracPaQ 2.8** identifica a referência MATLAB de David Healy e colaboradores.

O programa é executado diretamente pelo código, com Python 3.13 e as bibliotecas de requirements.txt. Miniforge pode gerenciar esse ambiente. As seis abas analíticas, importação TXT/SVG/imagem e ferramentas complementares estão disponíveis. A janela usa o logo PyFracPaQ, abre com largura útil total e mantém redimensionamento livre. Barras de cores acompanham o plot com distância fixa aos rótulos; marcadores usam quadrados/círculos geométricos normais.

## Diferenças aceitas em relação à referência

As correções abaixo foram aprovadas pelo mantenedor; podem alterar resultados em relação ao comportamento do legado.

| Família | Comportamento adotado |
| --- | --- |
| Censura — Q-05 | Extremidades nas bordas reais excluem o traço inteiro, mantendo comprimentos e ângulos alinhados. |
| Conectividade — Q-11 | Proximidade entre ponta real e segmento finito; T exato é Y mesmo com tolerância zero. |
| Wavelets — Q-12 | Rasterização determinística, dimensões retangulares e desempate de orientações conforme decisão aprovada. |
| Blocos — Q-14 | Exclui componentes que tocam a borda e calibra áreas/centroides; mede regiões rasterizadas, não polígonos vetoriais. |
| MLE — Q-15 | Cortes Lower/Upper coerentes e ajuste lognormal pela cauda, usando a mesma população na busca e no ajuste. |
| Estabilidade — Q-17 | Normalização após correções angulares, cores Sf lineares e igualdade CSF consistente entre mapa e rosa. |
| Maps/Graphs — Q-20 | Contagem em segmentos finitos e normalização P20 dos perfis como m/(2πr²). |

A geometria usa o centro do traço na metade do percurso e a diagonal pelas amplitudes do domínio. Convenções angulares brutas/corrigidas têm finalidades distintas. Os mapas de comprimento conservam a convenção aceita de índices de cor lineares e barra logarítmica.

Foram aceitas pequenas diferenças visuais em cinco títulos e duas vistas Hough, sem autorização para mudar votos/picos/endpoints. Os 16 detalhes apresentados foram aprovados após a troca dos marcadores. Isso não declara identidade geral de pixels nem identidade com os resultados científicos corrigidos do legado.

## Uso e limites

Prepare as dependências antes de executar. Não são necessários MATLAB, testes, relatórios ou instalação do pacote PyFracPaQ. O ZIP de uso é reduzido; o clone completo conserva o material de desenvolvimento. Windows/Linux permanecem para testes posteriores do mantenedor.

As saídas usam o diretório corrente, e repetir uma tag substitui os mesmos nomes. A substituição é atômica por arquivo, sem transação conjunta para toda a análise. Há intermediários de nome fixo. Dados e precisões dos TXT mantêm os contratos documentados.

[Preparação](install.md) · [Manual](user-guide.md) · [Exemplos](../examples/README.md) · [Créditos](../THIRD_PARTY_NOTICES.md). O histórico detalhado de decisões e evidências permanece no repositório completo, em docs/decisions, docs/parity e tests/reference.
