# ADR 0006 — SVG linear e conjuntos por cor

Data: 14/11/2026. Escopo: S05-01 a S05-08. Implementação Python verificada; comparação com execução MATLAB permanece pendente. A pasta original é somente referência e não recebeu gravações durante a validação.

## Subconjunto e integridade (Q-09)

io/svg.py usa XML estruturado com defusedxml, aceitando raiz SVG 1.1, grupos, line, polyline e path com **um M absoluto seguido por L absolutos ou pares implícitos**. Notação científica, sinais, namespaces SVG, quebras de linha e ordem arbitrária de atributos são tratados sem eval. Coordenadas devem ser finitas e unitless. version ausente assume o subconjunto 1.1; outras versões são recusadas.

Rejeição atômica do documento para comandos relativos, curvas, H/V/Z, múltiplos subpaths, polygon, transformações (inclusive grupos), viewports aninhados, referências use, geometria oculta/transparente, seletores CSS/classes e efeitos de clipping/máscara/filtro. Não aproximar curvas, fechar polígonos nem descartar traços incompatíveis silenciosamente. Metadata/title/desc, defs e imagens de fundo não são traços e não são carregados como geometrias; nenhuma referência externa é buscada. Declaração DOCTYPE histórica sem entidades é admitida, mas entidades/recursos externos são proibidos pelo parser. Limite de arquivo: 32 MiB.

Root width/height/viewBox não convertem unidades nem aplicam escala de navegador: são mantidas as coordenadas numéricas de usuário, como no conversor fornecido. Scaling da GUI é a única conversão pixels/metre. O port não anuncia suporte SVG geral.

Stroke admite #RGB/#RRGGBB, caixa indiferente, além de black/white. Ausência de stroke recebe preto, como no conversor. Atributos e style inline/de grupo são herdados; style inline vence o atributo. Outras sintaxes de cor precisam de preparação explícita. Normalização gera seis dígitos maiúsculos e RGB float64/255.

read_svg prepara SvgImport sem escrever; convert_svg prepara e publica. A GUI lê/calcula no worker e só publica TXT após conferir revisão e stamp da entrada. Resultado obsoleto não substitui arquivo convertido. Todo o conteúdo e a geometria são validados antes de criar temporários. A lista de alvos vem do próprio resultado, nunca de glob de diretório: arquivos antigos de cores não presentes e arquivos alheios, inclusive vazios, não são importados nem apagados. Todos os temporários próprios são escritos antes de substituir os alvos; cada replace é atômico, sem promessa de transação entre arquivos.

## Ordem, precisão e nomes

Grupos por hexadecimal ordenado; dentro de cada grupo, paths, polylines e lines em suas ordens de origem. Essa é a organização do fonte, não uma ordenação espacial. SvgElement retém tipo, índice documental, id, cor e pontos. O Dataset recebe IDs globais contíguos e source_line relativa ao TXT do grupo.

Uma cor: `nome_converted.txt`; várias: `nome_colourHHHHHH_converted.txt`. Destino sempre junto ao SVG, preservando nomes com espaços/pontos e extensão .SVG indiferente à caixa. Sem tag da execução ou cabeçalhos. Coordenadas `%12.8f`, TAB, CRLF; paths/polylines conservam o TAB final e lines seguem a regra de última linha do conversor. O Dataset é construído a partir dos valores **já quantizados para oito casas**, como converter e reler. Duplicatas consecutivas são normalizadas com diagnóstico; traço inteiro degenerado, inclusive por perda de precisão na conversão, rejeita o documento antes de escrever.

## Cores na aplicação

read_txt passa a reconhecer `_colourHHHHHH[_converted].txt` no final do nome, inclusive caixa mista; nome de cor inválido é erro. Cor fornecida explicitamente pela API continua tendo precedência. O padrão de TXT comum é azul, o padrão GUI do FracPaQ; TraceInput da API geométrica mantém seu default preto. Não se convertem arquivos em vírgulas automaticamente.

Prévia usa cores por traço e estatísticas/limites agregados. Os renderizadores deixam de impor azul a TXT de cor, incluindo mapa básico, Lengths, histograma angular e rosa sem Colour by strike. Paletas por comprimento/strike continuam as da análise. A cor global dos gráficos agregados é a do primeiro grupo, como no despacho legado; não há execução automática separada de todas as análises por cor. Para uma análise individual, carregar o TXT de cor correspondente e fazer novo Preview.

MAP-03 é acoplado à família de mapas básicos: quando há várias cores e pelo menos um desses mapas selecionado, gerar uma única figura `FracPaQ2D_tracemap_multicolour_{tag}.png`, com todas as cores, limites, unidades e flips. Não foi acrescentado checkbox. A figura aparece após o mapa básico se selecionado, ou antes do primeiro mapa por grandeza quando este inicia a família, como no fonte. Lengths/Angles sozinhos não disparam esse mapa extra. Linhas ficam acima da moldura para preservar traços exatamente nas bordas; nós/centros ficam acima das linhas.

## Referências e preparação de exemplos (Q-19)

Os fixtures simple.svg/multicolour.svg produzem dois traços/três segmentos/cinco nós; o segundo gera arquivos 0000FF e FF0000. O teste de recarga individual verifica cor vermelha em mapa, histograma e rosa. Sentinelas, staging com falha, revisão obsoleta, entidades XML, atributos reordenados, expoentes e geometrias não suportadas são exercitados.

original_svg_audit.json registra os 14 SVG fornecidos sem modificá-los: arquivos Tile/ThinSection/blocksizetest contêm curvas, comandos relativos, fechamentos ou paths sem segmento; left/rightside contêm CSS/classes; map1/map7 incluem polygon; map1_edit/map7_edit contêm traços inteiramente degenerados. Essas entradas precisam de edição explícita para o subconjunto. Isso é mais estrito que o legado que podia saltar elementos e prosseguir sem um conjunto íntegro.

Somente para evidência foi preparada uma **cópia** de map1_edit, removendo três traços inteiramente degenerados: 2120 traços/4356 segmentos, com checksum original/preparado no relatório. A cópia e sua proveniência estão em tests/reference/sprint5/inputs; nenhuma remoção automática foi introduzida no leitor. IYXtest1/2 e Souter_Blue continuam TXT válidos; map1_edit_converted/map7_edit_converted têm três/dois traços degenerados. souter_all_colour24378D.txt é separado por vírgulas e requer cópia preparada com TAB antes de usar o leitor GUI. Nenhum desses originais foi corrigido em lugar.

Evidências: testes numéricos/Qt/artistas, 18 PNGs, três TXT convertidos e oito TXT analíticos, arrays/cores, parâmetros e hashes em tests/reference/sprint5. Não são goldens MATLAB nem aceite visual por SSIM; capturas nativas continuam pendentes. Não houve relaxamento de tolerâncias ou introdução de modos científicos.
