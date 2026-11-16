# 0016 — Wavelets 2D e Q-12

Data: 14/11/2026. **Decisão aprovada pelo usuário: “Aprovo a Q-12.”** A aba Wavelets está integrada ao registro padrão, sem campos novos. [Registro de aprovação](../../tests/reference/sprint14/approval.json), [comparação concreta](../../tests/reference/sprint14/candidate/q12_comparison.json) e [referências nativas](../../tests/reference/sprint14/native_provenance.json).

## Contrato preservado

Núcleos anisotrópicos Morlet de Kaye L.Powell/Roseanna M.Neupauer e Mexican Hat de Dave Healy, com rotação C=[cosθ sinθ;−sinθ cosθ], A=diag(L,1), vetor Morlet k=[0,2π] e fatores L recíprocos da lista da GUI. A GUI recebe a/L inteiros positivos; a API cwt2 permite escala/ratio positivos reais, x/y regulares e retângulos.

A convolução preserva padding (2ny−1,2nx−1), origem ceil(n/2), recorte MATLAB e espaçamento dx×dy. A média é removida da imagem, mas não da função self. Morlet usa sqrt(L)/a e retém a parte real da resposta; Mexican usa1/a, conforme os fontes, sem introduzir sqrt(L). Self é a convolução do kernel conjugado consigo mesmo, não uma autocorrelação substituta. A implementação real de FFT preserva real(g*g)=gr*gr−gi*gi, inclusive o termo imaginário da self Morlet. eta soma os quadrados da resposta real; os resíduos imaginários numéricos do Mexican ficam dentro da tolerância nativa documentada.

WC normalizado=abs((WC/a)/max(abs(WCself)))×2.5. Maximização sobre L e depois θ, mantendo o máximo numérico real. Seleção estrita WC>0.5×máximo, em ordem de pixels por colunas; graus arredondados como MATLAB, duplicados axialmente, subtraídos90 e corrigidos uma vez para valores negativos. Cada flip aplica reverseAxis; dois flips restauram os ângulos. O raster permanece igual entre flips e as imagens dos painéis são espelhadas somente na exibição. Não se aplica norte nem unidade física adicional.

## Alterações Q-12 aprovadas

O raster faz parte do algoritmo. Mantém-se 27inches×72dpi=1944×1944, branco/preto, eixos [.13,.11,.775,.815] e aspecto igual. Traços com comprimento ≥45% do maior recebem4pontos; demais recebem1. Agg usa envelope explícito dos nós e não depende da tela. No exemplo nativo, 0.247305% dos pixels diferem por rounding/antialiasing e erro médio absoluto é .360593 de255. Essa diferença foi apresentada e aceita; não se anuncia identidade entre rasters. Escala uniforme dos nós preserva o enquadramento relativo, e o resultado permanece em pixels.

A lista é parseada sem eval/str2num. Incremento deve ser inteiro divisor de180, evitando passos40/270 que falharam em chamadas reais MATLAB:badsubscript. Arrays são ny×nx; wavelet2 nativo falha em8×6 ao atribuir resposta8×6 em matriz6×8. Retângulos válidos passam no port, sem transpor os dados científicos.

Empates dentro de rtol1e−12/atol1e−14 conservam a primeira escolha de L/θ na ordem de redução, mantendo o maior WC real. Em L=1 do Mexican Hat, orientação não é fisicamente única; arredondamentos FFT alteram argmax. O caso8×8 exporta26 ângulos, dos quais8 diferem do original sob a regra estável aprovada. Morlet exporta os mesmos76 ângulos. A máscara de seleção e os mapas WC coincidem com as referências, até as tolerâncias declaradas.

Imagem toda branca produz mapa zero e seleção vazia, rosa explicativa e TXT vazio; não há ângulo inventado. Raster todo preto (max gray=0) é recusado antes de dividir por zero. Self numericamente zero ou domínio não representável gera diagnóstico. Histograma mantém20 centros, log10 apenas das contagens positivas; o limiar vermelho mantém a semântica do fonte.

## Memória, interface e arquivos

QThread calcula; figuras interativas ficam na thread gráfica. O orçamento wavelet é2GiB, separado do limite de256MiB das famílias menores, pois o padding real de1944 requer buffers FFT maiores. Estimativa inclui buffers de convolução, mapas retidos por escala e metadados. Processamento por θ/L evita o tensor global ny×nx×a×θ×L; não muda a amostragem para caber. Há progresso por combinação e verificação de interrupção entre etapas. O diálogo auxiliar fornece Cancel; a aba principal continua sem esse botão.

FracPaQ2D_wavelet_traces.png permanece visível, sem tag, em72dpi. Cada escala produz FracPaQ2Dwavelet_a{a}_{tag}.png e FracPaQ2Dwavelet_theta_a{a}_{tag}.txt em `%g`, na ordem nativa. Escrita temporária própria/substituição atômica individual, sem limpeza de arquivos alheios. O painel2×2 tem imagem, WC/thermal, rosa e histograma. Bone é verificada contra MATLAB; as duas barras verticais passam exclusivamente por colourbar compartilhada, em SubFigures locais, com altura coincidente e folga fixa25pontos nos formatos quadrado/largo/alto e na exportação.

[Comparações](../../tests/reference/sprint14/native_comparison.json): respostas/self em5×8, a=[1.5,3], θ=[0,π/6,π/2], L=[.5,1] nos dois kernels; erro máximo de coeficiente/self abaixo de5e−15. [Execuções reais de produção](../../tests/reference/sprint14/validation.json) usam o raster completo1944×1944 e o registro padrão, nos dois kernels, incluindo PNG/TXT, arrays, tempo e pico de memória. As imagens pequenas dos testes Qt são fixtures declarados e não substituem essas execuções. O original integrado foi executado para seu raster; figuras/arrays pequenos vêm da variante wavelet2 original. Nenhuma execução completa do integrado é atribuída falsamente ao MATLAB. Homologação visual integral continua na Sprint16.
