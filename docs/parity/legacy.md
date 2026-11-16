# Destinação de utilitários e legado — Sprint15

Todos os164 arquivos originais permanecem intactos. [Destinação por arquivo/hashes](legacy-files.json) e [contrato das APIs](../decisions/0017-complementary-tools-and-legacy.md). A tabela cobre os19 AUX, sem confundir experimentos com controles da GUI2.8.

| ID | Destinação Python / tratamento explícito |
| --- | --- |
| AUX-01 | `python -m pyfracpaq.tools preprocess`: entrada, TIFF e painel PNG explícitos; seis etapas nativas verificadas |
| AUX-02 | `python -m pyfracpaq.tools move`: colunas base1, cabeçalho contado, objetos separados e último objeto preservado |
| AUX-03 | `pyfracpaq.io.text.readtext`: modos, regex/comentário/aspas, vazios, complexos e máscaras; leitor TXT da GUI permanece estrito |
| AUX-04 | `pyfracpaq.geometry` e `io.colours`: interseções/distâncias/limites/RGB existentes reutilizados/testados |
| AUX-05 | `analysis.variogram.experimental_variogram` e `plots.variogram.variogram`: API avançada já entregue na Sprint12 |
| AUX-06 | `analysis.auxiliary.crack_tensor16`: tensor/projeção16,65536componentes por momentos simétricos; fora da GUI |
| AUX-07 | `analysis.roses.linear_rose/historical_rose`, `plots.roses`: variantes válidas; roseEqualArea2 incompleta preservada como experimento |
| AUX-08 | `analysis.palettes.cmocean`, `plots.auxiliary.apply_cmocean`:18famílias, níveis, reversão, pivô/limites e aplicação ao eixo |
| AUX-09 | newCM/testCM: experimentos de cores não lineares, hardcodes/plot exploratório preservados; nenhum controle/algoritmo padrão novo |
| AUX-10 | `plots.auxiliary`: elipse, arcos, eixos centralizados, quadro/pontos ternários; desenho de conectividade existente reutilizado |
| AUX-11 | `analysis.auxiliary.probe_plane`: API histórica com limitações de origem/contagem declaradas; sem solução de fluxo3D |
| AUX-12 | `python -m pyfracpaq.tools wavelet-dialog`:14objetos do FIG, Run/Cancel, raster explícito e TXT auxiliar sem tag |
| AUX-13 | wavelet2 dá origem ao diálogo que reutiliza raster; wavelet3/FracPaQ2Dwave_2_Morlet ficam como variantes de referência com imagem/caminhos fixos e apresentações/exportações antigas |
| AUX-14 | guiFracPaQ2Dtabbed2.2: .fig correspondente ausente; assinaturas antigas e callbacks apenas preservados, nunca entrypoint |
| AUX-15 | testImage/testmaps/testWavelet/guiWaveletTest/blocksize/logplots/tritest/testCM/plotCrackTensor/plotSouterMap/plotMohr*: demonstrações com hardcodes/assinaturas históricas, sem execução automática. A suíte pytest é independente |
| AUX-16 | [Exemplos válidos](../../examples/README.md) do projeto e auditados; exemplos completos originais preservados, restrições TXT/SVG/imagem documentadas |
| AUX-17 | [Manual local de uso/preparação](../user-guide.md) e manual2.8 original; digitalização externa, sem transformar o port em editor GIS |
| AUX-18 | README, instalação, MIT, avisos e bibliografia preservados/atualizados; documentação nativa permanece ligada ao projeto |
| AUX-19 | index.html, CSS, JS, fontes/assets e params.json preservados como site histórico. params.json não é configuração da GUI; main.js não é aplicação web; sem hospedagem requerida |

EXP-05: os BMP/JPEG/TIFF/EPS e nomes sem tag de scripts antigos permanecem contratos daqueles exemplos, não formatos selecionáveis da GUI. Exceções ativas explícitas: BMP de blocos, PNG raster wavelet, TIFF da ferramenta de preparação e TXT sem tag do diálogo wavelet auxiliar. EXP-06: salvar sessão, histórico persistente e relatório consolidado são extensões futuras, sem tarefa implícita nesta entrega.

Q-19: a interface antiga não dita assinaturas/estado; paths da GUI atual já foram corrigidos nas sprints anteriores. As ferramentas locais recebem caminhos explícitos e a Move corrige EOF/cabeçalho como integridade de dados. Nenhuma limpeza geral de TXT/BMP ou procura por nomes fixos em outras pastas foi introduzida.
