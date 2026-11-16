# Referências obtidas e captura ainda necessária

## Material disponível

- SHA-256 dos 164 arquivos originais e catálogo estático dos 82 fontes MATLAB.
- Extração integral dos dois FIG: 154 objetos principais e 14 auxiliares.
- 103 imagens de apoio do manual, com página, nome, dimensão e hash em [manual/manifest.json](../../tests/reference/manual/manifest.json); texto das 39 páginas em text.txt.
- Páginas 4, 5, 13–16 e 28 renderizadas a 144 dpi para contexto. Poppler não está instalado no host; a renderização usa QtPdf já fornecido por PySide6. Dez imagens excedem o limite individual de buffer do pypdf; a razão e a página estão no manifesto e as páginas correspondentes foram renderizadas.

A imagem page-05-image-00.png é a janela inicial; page-06-image-00.png é a prévia. As demais incluem mapas, histogramas, rosas, MLE, topologia, tensores e Graphs. Todas vêm do manual fornecido, sem execução do código nesta máquina. Elas **não são PNGs originais de exportação nem goldens numéricos**.

## Pendências explícitas

[capture_catalog.json](../../tests/reference/capture_catalog.json) lista oito estados de tela e 53 nomes-base de figuras obrigatórias (wavelet é por escala), além dos dados/intermediários de RF-09. Todos estão pendentes de captura controlada com MATLAB. Não há instalação MATLAB/Octave encontrada no PATH; nem aprovação visual/numerical simulada. Figuras experimentais, como a rosa linear desativada, não entram nessa contagem GUI.

S00-05 fica concluída como **obtenção das referências documentais disponíveis e registro das indisponíveis**, conforme a própria tarefa prevê. A paridade continua pendente em todos os itens pertinentes. Capturar as referências originais é necessário antes do aceite de cada família e da auditoria final.

## Execução em máquina com MATLAB

1. Transportar a distribuição original e verificar o manifesto; nunca rodar capturas dentro da pasta original. Criar diretório de saída exclusivo e adicionar a pasta original ao path. A GUI original usa o diretório corrente para logo/ícone: copiar esses dois JPEG para o diretório de captura, com hashes registrados, sem modificar o fonte.
2. Registrar MATLAB release, toolboxes, SO, CPU/RAM, área cliente, resolução, escala do SO, ScreenPixelsPerInch, fontes efetivas e opções do renderer. Usar Arial e o alvo da ADR 0001 ou registrar diferença e recalibrar o ambiente.
3. Abrir guiFracPaQ2D. Salvar janela inicial sem reescalar. Para o fixture mixed.txt, salvar configuração, Preview, estatísticas e as seis abas. Capturar também grupos ativados/desativados e o diálogo auxiliar Run/Cancel. Capturas por getframe requerem janela visível e desktop sem oclusão.
4. Para cada família do catálogo, executar apenas as opções pertinentes com entrada e tag explícitas. Copiar para o registro os valores de todos os controles, escala, norte/flips e linha de Graphs. Usar diretório exclusivo por cenário, pois o original pode sobrescrever arquivos e seu conversor SVG limpa TXT na pasta corrente.
5. Salvar figuras em FIG e PNG pelo guiPrint original. Guardar arrays que alimentam o desenho e resultados em MAT e TXT com unidade e esquema. Nas funções sem retorno, usar breakpoint no ponto de desenho e salvar variáveis locais relevantes; registrar a linha e o checksum, sem editar o fonte para criar resultados diferentes.
6. Em Hough guardar imagem após complemento/clean, theta/rho/H, limiar, picos, supressão, endpoints e ordem. Em MLE guardar amostra antes/depois de cortes, xmin, parâmetros, D/p e todos os vetores sintéticos compartilhados. Em conectividade guardar interseções, classes antes/depois da limpeza e grade. Em CWT guardar raster, kernels, FFT/padding, eta, resposta self, coeficientes por a/L/θ, ótimos e máscara de 50%.
7. Repetir com escala, norte/flips, inputs reais válidos, imagem retangular e casos Q relevantes. Caso o original falhe, registrar erro/stack, input e ponto da falha; nunca substituir falha por valor inventado. Casos analíticos permanecem oráculos independentes.
8. Adicionar uma entrada de procedência por captura: ID, input/checksum, opções, ambiente, data, operador, fontes/checksums, arquivos, formatos, tolerância e estado de revisão. Só então atualizar os campos nulos e o estado de cada comparação, preservando o histórico.

## Reprodução das extrações locais

```bash
.venv/bin/python scripts/source_manifest.py
.venv/bin/python scripts/extract_fig_reference.py --output-dir /tmp/pyfracpaq-fig-review
.venv/bin/python scripts/extract_manual_reference.py --output-dir /tmp/pyfracpaq-manual-review
```

Os extratores não executam callbacks e não escrevem na distribuição original. Os JSONs de FIG podem ser comparados integralmente com a baseline; renderização PDF pode variar com a versão QtPdf, por isso há pins, hashes e revisão visual. Para leitura MAT usamos [SciPy loadmat](https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.loadmat.html); para renderização auxiliar usamos [QPdfDocument](https://doc.qt.io/qtforpython-6/PySide6/QtPdf/QPdfDocument.html).
