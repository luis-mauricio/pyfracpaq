# Contrato de aceite numérico, visual e de arquivos

Baseline S0, versão 1. Alterações exigem nova versão, justificativa e evidência; nunca aumentar tolerância apenas para aprovar teste. O contrato está definido; a comparação MATLAB continua pendente.

## Grandezas e tolerâncias

Usar float64. Comparar forma, ordem, unidade, finitude e máscara de valores antes de aplicar `abs(a-b) <= atol + rtol*abs(b)` elemento a elemento. NaN só é aceito em posições explicitamente previstas; não usar equal_nan para ocultar falha. Grandezas discretas, máscaras e índices exigem igualdade exata.

Seja L a maior amplitude espacial positiva do domínio na unidade corrente; domínio de área zero deve ser identificado antes de análises que dividam por área. Seja A a área, F0 a soma de l²/A, T o maior módulo das tensões e K* a soma de abertura³×comprimento/A dividida por 12 e multiplicada por λ. Os fatores absolutos abaixo têm a unidade da grandeza comparada.

| Família | rtol | atol / regra |
| --- | --- | --- |
| Coordenadas, comprimentos, centros e distâncias | 1e-10 | 1e-12×max(1,L), na unidade corrente |
| Área | 1e-10 | 1e-12×max(1,L²), na unidade corrente ao quadrado |
| Ângulos, em graus | 1e-10 | 1e-12×360; distância circular só para valores equivalentes, preservando o vetor exportado |
| P21 | 1e-10 | 1e-12/L; contagens e ordem dos círculos exatas |
| P20 | 1e-10 | 1e-12/L²; contagens exatas |
| F0/F2/F4/F8, autovalores e projeções | 1e-8 | 1e-12×max(1,abs(F0)) |
| P e K / autovalores | 1e-8 | Para K: 1e-12×abs(K*); para P: 1e-12×sum(abertura³×comprimento/A). Caso escala zero: atol=0. Não usar atol de 1e-12 absoluto que esconda permeabilidade pequena. |
| Tensões / Sf | 1e-8 | 1e-12×max(1,T), em MPa; Ts/Td adimensionais: atol=1e-12 |
| Ajustes determinísticos | 1e-8 | Expoentes, μ e σ: 1e-12×max(1,abs(referência)); xmin usa unidade de comprimento; taxa exponencial usa 1e-12/L |
| K-S com os mesmos vetores | 1e-8 para D e p | atol=1e-12; decisões de rejeição e significância exatas |
| CWT normalizada, por escala | 1e-6 | 1e-8; comparar também energia eta, resposta self, raster e coeficientes intermediários com escala declarada no registro |

As metas iniciais por família ficam congeladas neste contrato. A captura real deve confirmar escala/unidade e registrar os valores dimensionais efetivamente utilizados. Um desvio além da meta abre investigação/Q; não redefine o limite automaticamente. Ótimos CWT, escolha de L/θ, limiar de 50%, ordem de empates, bins e classes I/Y/X são exatos e avaliados separadamente. Valores em fronteiras não podem ser aceitos só porque o erro contínuo é pequeno.

MLE usa 2500 comparações sintéticas por modelo. Mesma seed entre bibliotecas não é oráculo: salvar vetores compartilhados e método/hipótese/significância de K-S. Sem esses vetores, executar 20 repetições independentes documentadas, comparar D/ajustes e proporções com intervalos binomiais de Wilson de 95% e erro amostral; registrar resultado estatístico separadamente. Essa alternativa não certifica igualdade de RNG nem resolve as assinaturas/cortes de Q-15. A escolha estatística final precisa da referência experimental.

## Interface e imagens

Mesmo texto, grupo, efeito, default e estado; posição/tamanho até dois pixels lógicos na resolução definida na ADR 0001. Escalas 100/125/150/200% não podem gerar cortes ou sobreposições. Comparar área cliente, removendo somente a decoração nativa documentada. Não redimensionar screenshots arbitrariamente para aumentar similaridade.

Para figuras: verificar primeiro os arrays, unidades, rótulos, limites, linhas, cores, legendas, ticks, posição das barras e polaridade. Só depois comparar regiões sem sobreposição: área de dados, título/textos, legenda e barra de cor. Exigir SSIM ≥0,98 em **cada região comparável**, data_range explícito e imagem RGB na mesma dimensão. Guardar a diferença e revisar visualmente. Texto deve ser semanticamente idêntico mesmo que SSIM passe; um gráfico vazio não pode passar por similaridade do fundo.

Não usar máscara de antialiasing inicialmente. Se necessária, registrar pixels afetados, motivo, limite de deslocamento e comparação antes/depois; nunca excluir toda uma curva, texto, legenda ou região de dados. Não usar tight_layout, bbox_inches=tight ou recortes que escondam margens diferentes. A dimensão de PNG de guiPrint ainda é pendente: 600 dpi e 20×20 cm são conhecidos pelo fonte; aproximadamente 4724 px não é dimensão observada. DPI no metadata pode sofrer quantização PNG e deve ser conferido contra arquivo real.

Raster wavelet a 72 dpi e BMP de blocos a 300 dpi são entradas do algoritmo. Comparar tamanho, orientação, traços, margens e pixels antes dos coeficientes/áreas. Imagens do manual não contêm arrays, parâmetros completos, métricas de tela ou PNG original: são apoio documental, sem aprovação de SSIM de release.

Observação de 14/11/2026, sem alterar as tolerâncias: os PNGs nativos das Sprints 10/11, produzidos por guiPrint no MATLAB R2024b Update 9, confirmaram **4724×4724** e metadata **599.9988 dpi** para 20×20 cm/600 dpi. Procedência e dimensões individuais constam nos manifestos dessas sprints. A comparação integral de regiões continua pendente; a captura de um subconjunto não certifica os 53 tipos do catálogo inicial.

## Arquivos e rastreabilidade

Usar [capture_catalog.json](../../tests/reference/capture_catalog.json) e RF-09/RF-14: nome/capitalização, tag, quantidade, diretório, esquema, separador, precisão, cabeçalhos, ordem e gatilho exatos. Comparar valores antes e depois da formatação. Preservar os acoplamentos P21/P20 e EZROSE. Substituição segura da mesma tag e limpeza restrita a temporários próprios são requisitos de integridade.

Cada evidência deve ligar ID, checksum de entrada/fonte, configuração completa congelada, versões, unidade, resultado bruto, imagem/arquivo e resultado de comparação. Os estados independentes são: funcional, numérico, visual e arquivos. Um teste de referência da Sprint 0 valida os artefatos de preparação; não significa análise do produto implementada.
