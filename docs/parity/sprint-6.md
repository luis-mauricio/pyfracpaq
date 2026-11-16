# Sprint 6 — Imagens e transformada de Hough

Concluída em 14/11/2026: nove tarefas S06 implementadas, preservando o contrato geométrico e os controles existentes. [ADR 0007](../decisions/0007-images-and-hough.md) registra equações, escolhas determinísticas, limites e pendências de paridade.

| Tarefa | Evidência |
| --- | --- |
| S06-01 | JPEG/TIFF grayscale 8 bits, metadados completos no console; rejeição de RGB/RGBA, palette, 1/16 bits e múltiplos frames sem conversão silenciosa. |
| S06-02 | Complemento lógico de todos os pixels não brancos e clean de oito vizinhos, inclusive bordas. |
| S06-03 | Acumulador determinístico, theta −90:0.5:89.5, rho por diagonal/passo 1 e ceil do limiar; oráculo escalar confere todos os votos de um caso pequeno. |
| S06-04 | Picos com desempate estável, supressão/costura rho-theta, recuperação dos pixels votantes, lacunas e mínimo; políticas de fronteira explícitas e comparação toolbox ainda pendente. |
| S06-05 | Dataset completo, azul, um segmento por traço, centros e end_length próprios; domínio raster preservado e escala idempotente; Q-06. |
| S06-06 | Figura Houghstuff de quatro painéis, três malhas completas e planos de limiar; exportação comum no Preview. |
| S06-07 | Invalidação por parâmetros/tipo/escala; configuração/tag/diretório congelados; nova prévia e origem/base de coordenadas verificadas. |
| S06-08 | Arrays/picos/endpoints/estatísticas salvos para directional, rectangular, MacduffBinary e Orkney1aBinary; variantes RGBA originais recusadas. Conferência analítica/documental; MATLAB indisponível. |
| S06-09 | Treze figuras de Maps/Lengths/Angles executadas com origem em imagem; teste dos campos geométricos e dos TXT/exportações. Famílias ainda não implementadas mantêm indisponibilidade explícita. |

Validação conjunta: **319 testes passaram**, incluindo 67 casos novos das duas sprints. [validation.json](../../tests/reference/sprint6/validation.json) contém quatro diagnósticos e treze PNGs analíticos a 4724×4724/600 dpi, quatro TXT, arrays completos, parâmetros e hashes. Os 164 arquivos de referência continuam intactos. Nenhuma dependência foi modificada.

[checks.json](../../tests/reference/sprint6/checks.json) registra checksum do JUnit, auditoria das exportações e hash do wheel. A leitura de imagem, extração de traços e renderização de quatro painéis foram verificadas diretamente do pacote zip fora do projeto.

| Imagem | H | max(H) / limiar | Picos / traços Python |
| --- | --- | --- | --- |
| directional | 89×360 | 24 / 8 | 7 / 7 |
| rectangular | 107×360 | 40 / 14 | 3 / 3 |
| MacduffBinary | 723×360 | 126 / 42 | 355 / 1507 |
| Orkney1aBinary | 1447×360 | 364 / 121 | 29 / 169 |

Parâmetros padrão: 1000 picos, fator .33, FillGap 5, MinLength 3. As contagens são medições deste port, **não observações de execução MATLAB**. [Macduff](../../tests/reference/sprint6/qa-FracPaQ2D_Houghstuff_Macduff.png) e [Orkney](../../tests/reference/sprint6/qa-FracPaQ2D_Houghstuff_Orkney.png) ilustram a malha completa, sem decimação ou substituição por perfil máximo. A revisão corrigiu rótulos/ticks dos eixos colapsados e tornou os planos de limiar visíveis.

Testes Qt verificam Preview da imagem, janela diagnóstica, Run padrão (cinco figuras adicionais), mudança de escala e parâmetros, campo de erro pertinente, rejeição de metadados e diagnóstico sem linhas. Não há Dataset/Run fictício quando nenhuma linha é extraída. Os cálculos não importam Qt; desenho/exportação ficam na thread principal.

Q-06 tem correção de integridade medida e Q-01/02/04/21 têm validação/estado do fluxo de imagem. Defaults não foram substituídos. Aceite nativo ainda requer comparar arredondamento de rho, empates, supressão e associação/ordem dos endpoints, além das tabelas RGB nominais reconstruídas e SSIM de figuras. MATLAB/Octave indisponíveis nesta sessão impedem essa homologação; as tolerâncias da Sprint 0 não foram relaxadas.

Reprodução: `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib .venv/bin/python scripts/validate_sprint56.py` e `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`.
