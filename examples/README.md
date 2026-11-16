# Exemplos locais válidos

Todos estes arquivos foram construídos pelo projeto, sob MIT. [Procedência/hashes](provenance.json). Não são resultados atribuídos ao MATLAB nem cópias de fotografias sem licença individual.

| Arquivo | Uso |
| --- | --- |
| rectangles.txt | Duas fraturas fechadas de 40×40; blocos, variograma, Maps e perfis. O bloco rasterizado branco mede 1444 pixels² após a espessura da linha, não 1600 pixels² vetoriais |
| profiles.txt | Traço dobrado e segmento vertical; linha sugerida (-5.5,0)→(5.5,0) para ALONG/FROM/círculos |
| colours.svg | Polyline/line sem transformação, dois strokes hexadecimais; conversão ao lado do SVG e TXT por cor |
| network.tif | Imagem grayscale uint8; Preview/Hough e análises subsequentes |
| move_objects.dat | Dois objetos com cabeçalho de uma linha e último objeto sem linha vazia final; usar a ferramenta Move com --skip-header 1 |

Ver [manual local](../docs/user-guide.md) para instalação, limites do SVG, preparação de fotografias, escala, wavelets e utilitários. Os exemplos originais completos permanecem em fracpaq-matlab; alguns requerem preparação antes de importar. Seus SVGs foram auditados na Sprint5 e nenhum arquivo original foi corrigido silenciosamente.
