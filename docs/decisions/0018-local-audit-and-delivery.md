# ADR0018 — Auditoria de paridade e candidato local

Data:14/11/2026. Estado: adotada para a auditoria S16; **homologação visual integral aberta**. Versão do port:0.1.0rc1; referência científica/interface: FracPaQ2.8. Este documento atualiza os estados históricos das ADR0001/0003/0004/0005/0007 sem transformar medições antigas em capturas nativas.

## Referência efetivamente executada

MATLAB R2024b Update9, macOS arm64, em processos batch separados da sessão interativa. `capture_native_s16*.m` executa somente fontes fornecidos/toolboxes e grava fora da distribuição original. Os164 fontes/assets originais e os oito resultados preexistentes do usuário continuam intactos. O manifesto estrito permanece exigindo exatamente164 arquivos; a suíte roda numa cópia isolada dessa baseline.

As capturas agora incluem todos os53 nomes de figuras e14 tipos de dados/intermediários. Disponibilidade no catálogo significa que há um arquivo real ligado ao contexto; não significa que os arrays ou pixels passaram. Exemplos SVG nativos terminam sem exceção, mas contêm NaN/elementos omitidos; são evidência da Q09, não uma geometria que o Python deva imitar. MLE, blocos, estabilidade, conectividade e wavelets conservam as diferenças científicas autorizadas e suas referências anteriores.

## Correções desta auditoria

Hough passa a quantizar a coordenada positiva do bin, depois de somar o offset de rho, com seno/cosseno em radianos. Arredondar rho assinado antes do offset deslocava votos de meio bin. A vizinhança padrão é `2*ceil(size(H)/100)+1`, não apenas o próximo ímpar de `size(H)/50`. Endpoints são ordenados pelo eixo de maior extensão em ordem crescente, com desempate pelo outro eixo. A associação de pixels em houghlines usa a coordenada de bin com offset/base1. Essas correções produzem igualdade exata de binário, acumulador, theta, rho, limiar, picos e endpoints ordenados em cinco rasters, incluindo MacduffBinary/Orkney1aBinary. Os artefatos antigos da S6 permanecem históricos; os atuais estão em sprint16.

Q05 recebeu aprovação explícita do usuário nesta auditoria: “Aprovo a Q-05.” O MATLAB real confirmou a mudança de população descrita na pergunta: traços[4,4,4] no legado versus[7,5] no port; segmentos[3,4,5] e ângulos alinhados. Preservar o critério de extremidades e máscara única já implementado; nenhum seletor científico novo. Q10 preserva exatamente as convenções do fonte, incluindo wrap único e TXT bruto distinto do EZROSE corrigido; uma futura unificação continua exigindo decisão científica.

A GUI usa Helvetica, identificada nos controles da captura nativa; fallback explícito Arial/DejaVu Sans se ausente. Os plots continuam usando Arial, também aplicada nas chamadas MATLAB comparáveis. A janela mantém a proporção1250×739 e abertura limitada ao monitor pedidas pelo usuário/PRD. O batch MATLAB abre1702×739 neste Mac por conversão das unidades characters; esse tamanho não substitui o requisito de abertura do port nem serve para declarar uma comparação de screenshots com tolerância de2px.

Histogramas/Lengths e mapas básicos recebem os retângulos nativos, os histogramas recebem ticks/formatação/grade mais próximos da referência, os títulos básicos descem2,5pt e barras de strike usam ticks de20°; rosas de estabilidade reservam8pt para separar o título da anotação de azimute vertical. A geometria e a distância fixa das barras exigidas pelo usuário/AGENTS permanecem sob o helper compartilhado. Essas alterações não mudam dados, bins, paletas ou normalizações.

## Eventos, arquivos e entrega

O cálculo continua no worker. A apresentação/exportação passa a avançar um PNG por evento Qt, mantendo Run desabilitado e o contexto/temporários vivos até a última saída. Exit pode interromper a sequência entre PNGs; cada PNG iniciado termina atomicamente. Não usar processEvents reentrante nem desenhar Matplotlib no worker. O sinal job_completed só é emitido após apresentação/limpeza. As figuras aceitam o atalho padrão Close, sem novo controle visual.

Mesma tag substitui o mesmo nome; tags diferentes coexistem; intermediários fixos de blocos/wavelets permanecem visíveis. A substituição é atômica por arquivo, sem promessa de transação conjunta entre vários arquivos. Falhas de staging preservam arquivos anteriores; falhas durante uma sequência de replaces podem deixar gerações diferentes e são reportadas. Não limpar arquivos do usuário por glob.

O wheel0.1.0rc1 é candidato **local**, acompanhado dos pins, avisos, hashes e wheelhouse macOS arm64. A instalação limpa usa CPython3.13, sem acesso ao índice; os dois entrypoints foram executados fora da árvore fonte com conexões/DNS impedidos. O VS Code foi usado de fato, além das configurações entregues. Windows/Linux foram retirados desta execução por instrução explícita do usuário; não são plataformas certificadas.

## Critérios que continuam impedindo homologação

O SSIM continua ≥0,98 por região comparável, com semântica/arrays corretos. A comparação exploratória preserva RGB, dimensões4724×4724, data_range255, diferenças e regiões fixas, sem máscaras, redimensionamento ou aumento de tolerância. Há falhas reais em títulos, ticks, margens, rosas e áreas com barras. A disponibilidade dos53 arquivos e a passagem da suíte não fecham esse critério. A revisão por contexto de todas as famílias, regiões independentes de textos/legendas/barras e os ajustes restantes continuam necessários para uma release homologada.
