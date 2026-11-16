# Referência original e padrões a preservar

Referência: FracPaQ 2.8 / 2.8.0, março de 2021. README, manual e OpeningFcn confirmam essa identificação; GUIDE registra alteração em 17/03/2021. O commit de origem e a release MATLAB que gravou o FIG não foram fornecidos. Não atribuir um commit presumido.

[source_manifest.json](../../tests/reference/source_manifest.json) registra tamanho e SHA-256 dos 164 arquivos, incluindo subpastas. `python scripts/source_manifest.py` compara conteúdo e conjunto de caminhos, detectando alteração, remoção e acréscimo. O comando --create recusa substituir um baseline. Nenhum arquivo de fracpaq-matlab foi editado ou usado como destino de saída. O .gitignore original já exclui essa pasta: preservar o original e o manifesto juntos ao reproduzir os testes; o manifesto não substitui os arquivos originais.

[source_catalog.json](../../tests/reference/source_catalog.json) cobre os 82 .m: assinaturas, candidatos a chamadas locais, instruções de exportação e checksum. É índice estático, não execução nem parser completo de MATLAB. Arquivos antigos em Latin-1 são decodificados explicitamente, sem alterar bytes originais.

| Camada encontrada | Padrão / consequência para o port |
| --- | --- |
| GUIDE 2.8 | guiFracPaQ2D.m e FIG são a referência principal; singleton, callbacks e estado em handles. Não usar a interface 2.2 como entrypoint. |
| Inicialização | OpeningFcn muda três popups para índice 2, move cinco painéis à posição de Maps, esconde os seis painéis e habilita Filename. Logo/ícone são carregados do diretório corrente no original. No port, usar recursos do pacote. |
| Entradas | TXT tabulado via readtext; SVG passa por conversão e arquivos por cor; imagem gera linhas Hough de um segmento. Não há contrato uniforme completo entre os leitores: Q-06/07. |
| Geometria | Segmentos sequenciais, comprimento acumulado e centro a meio caminho; ângulo bruto por atan(dx/dy), ajustado ao intervalo axial. Não confundir centro com média dos vértices. |
| Despacho | Run coleta opções de todas as abas, não só da visível. Há validação indevida de campos desmarcados e cross-plot fora do flag Lengths: Q-01/03. |
| Mapas / perfis | Execução acoplada P21/P20: preservar os dois TXT em Maps e os dois gráficos em Graphs. Q-20 impede assumir contagem correta de secantes horizontais/verticais. FROM mantém distância com sinal. |
| Ângulos | doubleAngles subtrai norte, usa round MATLAB e duplica direções; cada flip chama reverseAxis. TXT com ângulos brutos não devem ser silenciosamente substituídos por corrigidos: Q-10. |
| Tensores | Comprimentos ao quadrado, polos e área em F; abertura ao cubo em P/K. Crack tensor está em Fluid flow e aciona a rotina que também grava EZROSE. |
| Estatística | Portar equações MLE e 2500 comparações; K-S MATLAB/SciPy e RNG exigem vetores compartilhados. Não trocar por .fit() genérico. Q-15 permanece aberta. |
| Blocos / wavelets | O raster integra o método. Blocos usa BMP 300 dpi; wavelet usa PNG 72 dpi e espessura pela regra de 45%. Morlet/Mexican Hat 2D anisotrópicos não equivalem a wavelets 1D. |
| Figuras | Funções MATLAB misturam cálculo, desenho e gravação; separar os três no Python mantendo os mesmos arrays. guiPrint impõe 20×20 cm e 600 dpi; dimensão real em pixels ainda precisa de PNG original. |
| Integridade | Corrigir limpeza ampla, paths e índices conforme PRD; mudanças científicas de Q-10/11/12/14/15/17/20 exigem decisão registrada antes de mudar o padrão. |

O inventário detalha também site, manual, 41 TXT, 14 SVG, 15 imagens e dois FIG. A matriz mantém todos os IDs e a destinação AUX. O conjunto inspecionado não fornece licença individual adicional para cada fotografia; a atribuição inicial é a do pacote, sem inventar autores de campo.
