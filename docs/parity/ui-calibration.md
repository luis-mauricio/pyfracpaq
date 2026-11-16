# Revisão da fidelidade da interface

**Atualização de 16/11/2026:** o usuário solicitou abertura com a largura da tela. A janela agora ocupa toda a largura útil do monitor, incluindo bordas nativas, com altura limitada e centralização vertical. Continua sendo uma janela normal redimensionável. Essa solicitação substitui a regra anterior de margem horizontal/limite de 1250 na abertura, documentada no histórico abaixo. [Verificação Qt](../../tests/reference/interface-identity/startup-width.json).

14/11/2026, após relato do usuário sobre borda na navegação, tamanhos dos botões, largura da janela e outras diferenças. A implementação anterior preservava os blocos principais, mas redistribuía seus controles internos com layouts Qt e descartava propriedades visuais do FIG. Isso não atendia à fidelidade solicitada.

Foram conferidos o FIG extraído, os callbacks de abertura e as capturas originais do manual nas páginas 5/6. Os 164 arquivos MATLAB permanecem intactos. A revisão atua na apresentação; não modifica cálculos, seleções padrão ou formatos dos resultados científicos.

| Diferença encontrada | Correção |
| --- | --- |
| Moldura em torno de Maps/Lengths/Angles/Fluid flow/Wavelets/Graphs | BorderType=none agora preservado no recurso e aplicado ao grupo. |
| Botões de navegação baixos e largura determinada pelo layout/texto | Coordenadas relativas originais, larguras iguais, espaços e altura do FIG. Na referência 1250×739: seis botões de 71×50, sem desvio nos retângulos relativos. |
| Janela com largura fixa 1366 e formulário mínimo muito grande | Abertura normal centralizada, até 1250×739, limitada pela área útil do monitor com margem. Em uma área 1366×768: aproximadamente 1120×662. |
| Grupos internos redistribuídos nas seis abas | Árvore e posições originais restauradas. Em Maps, mapas por cor ficam no alto à direita e estabilidade abaixo das opções de traços. Lengths mantém cortes/MLE à esquerda e cross-plot/blocos à direita. |
| Grupos com linha plana genérica e títulos invadidos por controles | Bordas rebaixadas claras e insets explícitos para o título. |
| Todos os controles herdando a mesma fonte, cabeçalho reduzido | Hierarquia FontSize/FontWeight do FIG, cabeçalho em negrito, calibração em pixels lógicos e redução proporcional em janelas menores. |
| Números alinhados à esquerda sem observar a referência | HorizontalAlignment original aplicado a campos e rótulos. |
| Indicadores cinza do Fusion | Marcadores azuis com marca branca para checkbox/radio, mantendo foco e estados habilitado/desabilitado. |
| Título da barra diferente do FIG | FracPaQ na barra; Fracture Pattern Quantification permanece no cabeçalho interno. |
| Rótulos da própria referência excedendo campos/bordas | Ajustes locais de largura/altura preservam texto completo; títulos longos ajustam a fonte, sem reposicionar a família inteira. |
| Fonte da prévia e quantidade de ticks vazios diferentes | FontSize do eixo convertido para pixels lógicos independentemente do DPR; onze ticks nos eixos vazios, como na captura inicial fornecida. |

[Antes da correção (Python)](../../tests/reference/ui-calibration/before-maps.png), [Maps corrigido](../../tests/reference/ui-calibration/dpi-100/maps.png) e [estado inicial atual](../../tests/reference/ui-calibration/dpi-100/initial.png). Os diretórios dpi-100/125/150/200 contêm oito estados cada, incluindo as seis abas; minimum contém os mesmos oito estados a 1000×591. São **40 capturas atuais**, sem violações de ajuste do texto, e duas capturas Python anteriores para comparação. Manifests registram hashes, geometria de navegação, posição dos blocos e dimensões de abertura detectadas no monitor offscreen. As capturas históricas da Sprint 2 não foram sobrescritas.

Oito novos testes de regressão verificam metadados contra o FIG, ausência da linha inferior da moldura, igualdade/retângulos dos seis botões, dimensões iniciais para três monitores, uso real da área disponível, árvore/posição dos grupos, alinhamento e ausência de sobreposição de rótulos com seus campos. A suíte completa passou com **384 testes**. [validation.json](../../tests/reference/ui-calibration/validation.json) registra auditoria dos arquivos e preservação dos originais.

A referência do manual é documental; MATLAB indisponível impede comparar capturas controladas ou aprovar identidade pixel a pixel. Decorações da janela, fonte de fallback e renderização nativa variam entre sistemas. A correção preserva geometria/estados verificáveis e documenta os poucos ajustes necessários para não reproduzir cortes do original.

Reprodução de uma escala: `QT_SCALE_FACTOR=1.25 .venv/bin/python scripts/capture_sprint2.py --output-dir /tmp/pyfracpaq-ui-125`. O script usa por padrão 1250×739; --width/--height permitem conferir superfícies menores sem mudar a regra de abertura do programa.

## Atualização S16

MATLAB R2024b foi executado e capturou oito estados por print e propriedades reais, em sprint16/native/details. A conversão de characters produz1702×739 neste Mac; não comparar esse raster ao1250×739 do requisito como se fossem a mesma área cliente. A GUI Python passou a usar Helvetica da referência, fallback explícito;32 novas capturas em sprint16/gui verificam quatro DPRs, sem cortes de texto. Uma sessão desktop real abriu pelo VS Code, usou Browse/Cancel/caminho acentuado, percorreu abas e gerou cinco PNG/quatro TXT. O contrato de abertura limitada ao monitor/navegação sem moldura foi mantido. Isso não homologa posição/tamanho em2px contra screenshots diferentes, nem substitui a revisão visual integral ainda aberta. Windows/Linux foram adiados pelo usuário.
