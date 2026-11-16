# Sprint14 — Wavelets2D

Sprint concluída com Morlet/Mexican Hat no registro padrão. **Q-12 aprovada pelo usuário: “Aprovo a Q-12.”** [Decisão](../decisions/0016-wavelets-and-q12.md), [aprovação](../../tests/reference/sprint14/approval.json), [comparações](../../tests/reference/sprint14/native_comparison.json) e [execuções completas](../../tests/reference/sprint14/validation.json).

Controles originais e parser seguro de listas/recíprocos L, incremento divisor de180, raster1944×1944/72dpi com regra45%, kernels/FFT/self/eta, maximização e seleção estrita50% implementados. Quadros2×2, TXT por escala, flips, progresso e nomes originais estão integrados ao Run. Barras verticais usam o helper compartilhado com mesma altura do plot e25pontos de folga ao redimensionar/exportar.

Chamadas reais MATLAB confirmam falhas com passo40/270 e imagem retangular; respostas/core/self em5×8 e painéis8×8 foram capturados nos dois kernels. Coeficientes/self conferem dentro de5e−15, mapas GUI dentro de3e−16. Morlet exporta76 ângulos iguais; a regra de empate aprovada muda8 dos26 ângulos Mexican isotrópicos. O raster candidato difere em0.247305% dos pixels do integrado MATLAB, diferença medida e aceita. Nenhum desses candidatos é apresentado como resultado nativo idêntico.

Os dois casos de produção usam o raster/FFT completos e o registro padrão, com uma escala32, L=2 e passo90. Guardam PNGs4724×4724/600dpi, raster visível, TXT, arrays, tempos e pico do processo. Não são substituídos por mocks pequenos de Qt. Memória estimada por escala/orientação, orçamento2GiB e Cancel somente no diálogo auxiliar. [Procedência](../../tests/reference/sprint14/native_provenance.json); [checagens finais](../../tests/reference/sprint14/checks.json). Homologação integral/multiplataforma fica na Sprint16.
