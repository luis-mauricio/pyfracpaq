# S16-09 — Entrega em cinco pontos

Data: 16/11/2026. Versão dos fontes: **0.9.0rc1**. O usuário determinou concluir **um ponto por vez e parar**, aguardando autorização para o próximo. **Os cinco pontos estão concluídos. S16-09 encerrada após a conferência do commit df9f512 e do ZIP real publicado pelo usuário.** [Estado verificável](../../tests/reference/sprint16/delivery/status.json).

- [X] 1. Revisão final da interface no macOS.
- [X] 2. Conferência das exportações da versão final.
- [X] 3. Consolidação de versão e documentação da entrega.
- [X] 4. Preparação e validação do código para clone/download.
- [X] 5. Disponibilização do código no GitHub — publicação e ajustes finais enviados pelo usuário; commit df9f512 e ZIP remoto conferidos.

## Ponto 1 — concluído

Foram revisadas a janela inicial, Preview e as seis abas Maps/Lengths/Angles/Fluid flow/Wavelets/Graphs. O aplicativo Cocoa nativo foi executado com uma cópia do SD11A em caminho com espaços e extensão TXT maiúscula. O Preview apresentou 445 traços, 1076 segmentos e 1521 nós. Fontes, rótulos, logo, rodapé em linha única, navegação sem moldura, estados de entrada e os tamanhos das janelas foram conferidos.

As 48 capturas principais cobrem oito estados em seis contextos: 100%, 125%, 150%, 200%, janela mínima 1000×591 e Cocoa nativo com DPR 2. **Nenhum corte de texto foi identificado** pelos critérios de encaixe. A revisão visual das capturas não encontrou defeito pendente. A largura inicial nativa foi medida incluindo a moldura: 1710 pixels lógicos, igual à área útil; o redimensionamento permanece livre.

Os sete controles nativos adicionais passaram: abertura com largura total; Cancel/Open no seletor real do macOS; leitura de caminho com espaços/acentos e TXT maiúsculo; mensagem de erro em texto simples com retorno ao campo; recuperação com entrada válida e Run habilitado; invalidação do Preview ao editar a entrada; diálogo Wavelets em 520×320, 400×260 e 650×400, com validação/Cancel; e encerramento por Exit. A contagem de sete agrupa esses cenários no manifesto. O seletor e Exit foram operados por Computer Use no processo `org.python.python`; os demais fluxos foram exercitados pelo roteiro Qt sobre widgets Cocoa reais. Há dez capturas adicionais desses fluxos/diálogos. As mensagens de erro foram provocadas deliberadamente com um arquivo ausente e uma lista inválida de Wavelets; não representam falhas inesperadas.

**81 testes GUI passaram em 185,51 segundos**, incluindo estados/dependências, Preview, validação, integração das abas, cancelamento, janelas, barras de cores e entrypoints. Esses testes usam saídas temporárias para verificar os fluxos da interface; isso não corresponde à auditoria final dos arquivos do ponto 2. O roteiro nativo desta revisão não executou Run nem exportou produtos analíticos.

Não foi necessário corrigir o produto nesta rodada. Corrigiu-se a ferramenta de captura: agora o primeiro show aplica a abertura com largura total e, depois, o roteiro aplica explicitamente --width/--height para conferir os tamanhos solicitados. A ferramenta também aceita --input e identifica corretamente a plataforma Cocoa/offscreen. Uma primeira tentativa de controlar o seletor Cocoa por temporizadores e uma asserção incorreta do texto inicial foram corrigidas no roteiro; o seletor foi então verificado pela interface real. Essas falhas do roteiro não foram contabilizadas como aprovações nem como defeitos do programa.

[Resumo com hashes](../../tests/reference/sprint16/delivery/point-1/summary.json), [galeria nativa](../../tests/reference/sprint16/delivery/point-1/index.html), [capturas das oito telas](../../tests/reference/sprint16/delivery/point-1/native/manifest.json), [diálogos e fluxos](../../tests/reference/sprint16/delivery/point-1/dialogs/manifest.json) e [testes GUI](../../tests/reference/sprint16/delivery/point-1/gui-checks.xml).

Os 164 originais e os oito resultados preexistentes foram conferidos por hash e preservados. As evidências da S16-04 permanecem históricas e intactas. Windows/Linux continuam para testes posteriores pelo usuário.

## Ponto 2 — concluído

Os renderizadores e exportadores atuais foram executados sobre os resultados SD11A já homologados. Antes de carregar o cache local, foram conferidos o hash do próprio cache, o TXT original e todos os módulos científicos de analysis/domain/geometry/io. Isso evita repetir os cálculos demorados de MLE/Wavelets nesta auditoria de arquivos. As 30 rotas produziram 51 figuras únicas; Hough e SVG multicolorido completaram os **53 modelos PNG** do catálogo.

Todas as 53 exportações atuais têm **4724×4724 pixels, 600 dpi e identificação PyFracPaQ 0.9.0rc1**. Os pixels RGB são exatamente iguais aos das referências finais aprovadas na S16-04, incluindo marcadores geométricos, títulos e barras. A identificação Software atualizada altera o hash do arquivo em relação à referência histórica, sem alterar sua imagem. As cópias PNG desta conferência ficam em diretório temporário; o manifesto permanente guarda seus hashes de arquivo/RGB, metadados e hashes das referências aprovadas, evitando duplicar 53 imagens idênticas no repositório.

Os nove TXT principais, o BMP fixo dos blocos e o PNG fixo da rasterização Wavelets são **idênticos byte a byte** às referências finais. Conferiram-se também a conversão SVG simples e as duas tabelas por cor, o theta auxiliar sem tag e o TIFF de pré-processamento (pixels idênticos à referência). Com esses auxiliares, os **14 modelos de dados** do contrato estão cobertos. O painel auxiliar de pré-processamento também foi gerado pelo comando real; ele conserva sua saída própria, separada dos PNG analíticos de 600 dpi.

Tags vazias e com espaços/acentos foram exercitadas em caminhos com espaços/acentos. Onze arquivos principais foram deliberadamente substituídos por conteúdo antigo e recuperados pelos exportadores reais, com hashes idênticos aos iniciais e preservação de um arquivo alheio. As tabelas SVG também foram substituídas e recuperadas sem mudar o SVG de entrada. As saídas com nomes fixos continuam sem tag, conforme o contrato. Não ficaram arquivos temporários de gravação.

Duas execuções novas do registry, sem cache, conferiram a entrada sem escala e com dois pixels por metro: os valores TXT e rótulos dos histogramas passam corretamente de pixels para metres, com comprimentos divididos por dois. **282 testes direcionados passaram**, sem falhas, erros ou skips: contratos de execução, Lengths, Angles, amostragem circular, conectividade, estabilidade, SVG, blocos, utilitários e barras de cores, incluindo preservação de arquivos anteriores quando a gravação falha. Não foi necessário alterar código produtivo.

O roteiro de auditoria foi corrigido para expandir o parâmetro de escala `{a}=32` do catálogo. A primeira passagem já havia exportado e conferido os 53 PNGs; a passagem concluída reutilizou esses arquivos e voltou a conferir seus pixels/metadados antes de concluir os dados. Essa correção do roteiro não representa defeito do programa. Os dois registros de execução permanecem junto às evidências.

[Resumo e hashes](../../tests/reference/sprint16/delivery/point-2/summary.json), [282 testes](../../tests/reference/sprint16/delivery/point-2/export-checks.xml), [arquivos de dados](../../tests/reference/sprint16/delivery/point-2/data) e [roteiro](../../scripts/review_s1609_exports.py). Originais e evidências da S16-04 preservados. Windows/Linux permanecem para testes posteriores do usuário.

## Ponto 3 — concluído

A identificação foi consolidada como **PyFracPaQ 0.9.0rc1**, pré-versão de **November 2026**, contato **luismauricio@me.com**, mantendo o número já aprovado pelo usuário. Runtime, metadados do projeto, rodapé e documentação concordam. FracPaQ **2.8** permanece identificado como referência MATLAB de David Healy e colaboradores.

As [notas da versão](../releases/0.9.0rc1.md) reúnem recursos, diferenças científicas Q-05/11/12/14/15/17/20, correções geométricas Q-07/08, convenções preservadas Q-10/cores por comprimento, aceites visuais e limites da entrega. Os cinco títulos, duas vistas Hough, 16 detalhes e propagação autorizada dos marcadores têm links para as evidências originais. Métricas e aceites históricos permanecem intactos; não se declara igualdade com resultados científicos corrigidos do legado.

README, changelog, manual, instalação, registro Q, matriz e relatórios de estado agora separam o histórico 0.1.0rc1 dos fontes 0.9.0rc1 e dos pacotes ainda não gerados. O guia fornece os comandos atuais de desenvolvimento e identifica os comandos offline do novo wheel como dependentes do ponto 4. Os resultados anteriores de instalação limpa/offline não foram atribuídos ao futuro pacote. As contagens da suíte completa e dos testes direcionados permanecem separadas. Windows/Linux continuam reservados ao usuário.

Foram conferidos os links locais da documentação consolidada e a consistência da versão/data/contato, incluindo dois testes existentes de identidade da interface e recursos/procedência. Nenhum algoritmo científico, figura aprovada ou pacote em dist/ foi alterado. [Resumo verificável](../../tests/reference/sprint16/delivery/point-3/summary.json) e [testes](../../tests/reference/sprint16/delivery/point-3/identity-checks.xml).

## Ponto 4 — concluído pelo código

O fluxo validado é código por clone/download, sem instalar o pacote PyFracPaQ. requirements.txt já existia, teve os pins preservados e recebeu a instrução de uso. requirements-dev.txt permanece separado e opcional. O README foi reduzido ao fluxo de preparação/uso; o conteúdo técnico anterior foi conservado em docs/development.md, e notas voltadas ao usuário estão em docs/release-notes.md. A descoberta automática de pytest no VS Code foi desativada para não exigir ferramentas de desenvolvimento no uso normal.

Os aproximadamente 760 MiB de testes/evidências foram preservados no repositório completo. .gitattributes/export-ignore os exclui do ZIP de uso, junto com scripts internos, relatórios e planejamento. O candidato foi exportado por git archive em um repositório temporário, copiando os arquivos atuais rastreados/não ignorados; não houve commit, modificação do índice ou acesso ao remoto da cópia do usuário. O ZIP tem cerca de 572 KiB e 190 arquivos, com programa, recursos, requirements.txt, exemplos, duas configurações de execução VS Code, manual/notas e licenças. Todos os arquivos do programa e recursos coincidem com os fontes. Nenhum arquivo excede o limite de 100 MiB na seleção preparada para o repositório; segredos, ambientes, caches, builds, originais MATLAB e saídas da raiz não entram. O Download ZIP efetivamente servido pelo GitHub será conferido no ponto 5, após publicação autorizada.

**Dois ambientes foram preparados:** venv CPython 3.13.18 e ambiente conda gerado pelo Miniforge, Python 3.13.13, ambos macOS arm64. Instalaram-se somente as dependências de requirements.txt, com --no-index e wheels locais de versões fixadas. Nenhum relatório de pip contém instalação de PyFracPaQ; pip check passou. O cache de wheels é apenas um recurso interno do teste, não uma exigência ou artefato da distribuição pelo código. O ambiente conda foi preparado por especificação explícita de pacotes locais; não se afirma ter testado o download/solver de conda pela internet.

Cada ambiente executou os dois entrypoints sobre cópias do ZIP que não contêm tests/ ou scripts/. O verificador exige importação pela própria pasta e ausência de distribuição PyFracPaQ instalada. Leitura TXT/SVG/Hough, recursos/logo/rodapé, Preview, Run com Maps/Lengths/Angles, quatro PNGs 4724×4724/600 dpi e quatro TXT por execução passaram: **quatro fluxos, 32 arquivos exportados**. Connect/connect_ex/create_connection e DNS foram bloqueados no Python, com autoteste do bloqueio e zero tentativas durante as análises. As entradas e tags incluem espaços/acentos e extensão TXT maiúscula. São testes de integração Qt offscreen, não nova certificação de aparência nativa.

O VS Code nativo também selecionou o ambiente limpo, iniciou run_gui.py por Run Python File e abriu a janela correta. Preview de examples/profiles.txt mostrou dois traços/quatro segmentos/seis nós e habilitou Run; Exit funcionou e o interpretador original do workspace foi restaurado. Essa verificação usou o workspace original já confiável, cujos módulos/recursos coincidem com o ZIP. A pasta temporária do ZIP foi visualizada em Restricted Mode; nenhuma configuração de confiança/segurança foi alterada. Os dois entrypoints da cópia enxuta foram cobertos separadamente pelas execuções automatizadas.

A preparação offline inicial do conda não encontrou os pacotes no cache temporário vazio; foram usadas as cópias dos arquivos locais e uma especificação explícita. O conda também precisou de autorização para registrar o prefixo temporário em ~/.conda/environments.txt. Após essa autorização, a criação e todas as verificações finais passaram. As tentativas de preparação não são contadas como testes aprovados nem como defeitos do aplicativo.

Os artefatos instaláveis anteriores são históricos/internos e não foram usados como prova de conclusão deste fluxo. Nenhum algoritmo, referência aprovada ou original MATLAB foi alterado. Windows/Linux permanecem para testes posteriores do usuário. [Resumo](../../tests/reference/sprint16/delivery/point-4/summary.json), [conteúdo/ZIP](../../tests/reference/sprint16/delivery/point-4/source-archive.json), [Python](../../tests/reference/sprint16/delivery/point-4/native-source.json), [Miniforge](../../tests/reference/sprint16/delivery/point-4/miniforge-source.json) e [VS Code](../../tests/reference/sprint16/delivery/point-4/vscode-native.json).

## Parada após o ponto 4

A preparação/validação está concluída. **O ponto 5 não foi iniciado:** não houve commit no projeto, push, publicação ou disponibilização no GitHub. A continuação depende da autorização explícita do usuário para esse ponto.

## Reprodução do ponto 1

As capturas automatizadas usam `scripts/capture_sprint2.py --output-dir ... --width 1250 --height 739`; `QT_SCALE_FACTOR` define 1/1.25/1.5/2 e a janela mínima usa --width 1000 --height 591. Para as capturas nativas, definir `QT_QPA_PLATFORM=cocoa` e `--input` com a cópia do SD11A. A captura identifica a plataforma efetivamente usada.

`scripts/review_s1609_dialogs.py --output-dir ... --input ... --manual-picker --keep-open`, com `QT_QPA_PLATFORM=cocoa`, exige interação real para Cancel, seleção do TXT e Exit. Essa opção não simula o seletor nativo por temporizadores. O roteiro só confere a interface e grava suas capturas/manifestações. A suíte específica é `python -m pytest -q tests/gui` com `QT_QPA_PLATFORM=offscreen` e JUnit em diretório próprio.

## Reprodução do ponto 2

Executar os onze módulos registrados em `point-2/export-checks.xml` com pytest/JUnit no mesmo caminho. Com `MPLCONFIGDIR=/tmp/pyfracpaq-matplotlib` e `PYTHONPATH=.:scripts`, executar `.venv/bin/python scripts/review_s1609_exports.py`. O roteiro exige o cache local produzido por `finish_s16.compute`, com hashes válidos e os mesmos módulos científicos; não aceita caches de origem desconhecida nem altera as referências aprovadas. A opção `--png-directory` permite retomar somente as cópias PNG de uma passagem anterior desta mesma auditoria; todos os pixels, nomes, dimensões, resolução e metadados são conferidos novamente. A ausência do cache exige recalcular os resultados científicos antes de repetir esta auditoria, sem necessidade de uma nova calibração visual.

## Ponto 5 — preparação local dos documentos

O usuário assumiu o envio ao GitHub e pediu revisão do README e manual em LaTeX antes do push. O README recebeu apresentação, visão das seis abas, início rápido, Miniforge/VS Code, exemplo SD11A, créditos e links. O manual em docs/manual contém LaTeX, capítulos, figuras e PDF compilado com XeLaTeX: 73 páginas, 51 figuras numeradas, todos os 30 recursos analíticos, entradas/unidades, ferramentas, saídas e teoria/fórmulas conferidas no código. SD11A.txt foi copiado sem alterações para examples, com checksum/procedência e atribuição MIT.

A revisão incluiu referências internas, cobertura dos recursos, teste de procedência dos exemplos e renderização das 73 páginas. As métricas/evidências científicas anteriores continuam intactas; figuras usadas no manual são cópias para documentação. O manual inclui instruções para XeLaTeX no TeXStudio e não adiciona dependências à execução do programa.

**O ponto 5 continua aberto:** não houve commit, push ou publicação. Aguarda-se a revisão/envio pelo usuário e o link para conferir o repositório/Download ZIP real. A documentação adicional aumenta o tamanho do candidato em relação aos cerca de 572 KiB históricos do ponto 4; esse tamanho anterior não descreve o ZIP com o manual.

## Documentação bilíngue — 16/11/2026

Por solicitação do usuário, README e índice dos manuais estão em inglês. O manual está disponível em pt-BR (73 páginas) e inglês britânico (71 páginas), com os mesmos 30 recursos, 51 figuras numeradas e 27 blocos de equações. Os rótulos dos controles foram conferidos no catálogo da interface e no registry; a prosa inglesa usa colour, centre e normalisation. Títulos bibliográficos e nomes reais de arquivos/comandos preservam sua grafia original.

As duas versões compartilham estilo e 52 imagens, sem duplicar os recursos científicos. PDFs recompilados com XeLaTeX, sem caixas excedidas, glifos ausentes ou referências indefinidas; todas as 144 páginas foram renderizadas e revisadas visualmente. Os links locais e a inclusão de PDFs, capítulos, estilo e imagens no novo candidato ZIP foram conferidos. Evidências anteriores são históricas e mantêm seus hashes originais; a atualização está em [bilingual-documentation-checks.json](../../tests/reference/sprint16/delivery/point-5/bilingual-documentation-checks.json). Nenhum código científico ou referência aceita foi alterado.

O envio ao GitHub continua a cargo do usuário. Não houve commit/push/publicação; S16-09.5 permanece aberta até o envio e a conferência remota.

## Documentos aprovados e organização local — 16/11/2026

O usuário aprovou o README e os dois manuais. A pendência de revisão desses documentos foi concluída no PRD; envio ao GitHub e conferência remota continuam pendentes. Também foram aprovados e executados os movimentos de PRD/inventário para docs/planning e de 14 saídas locais para outputs/previous-runs. Links e ferramentas afetadas foram ajustados, sem modificar os documentos aprovados, código produtivo ou referências científicas. [Organização e revisão das pastas](repository-organisation.md).

## Ajustes após a publicação — 16/11/2026

O usuário publicou o commit **2bb3355dada72c916d599888a29db395d3ad0982** em [luis-mauricio/pyfracpaq](https://github.com/luis-mauricio/pyfracpaq). O ZIP real do GitHub foi baixado e conferido: 262 arquivos, 48.972.573 bytes (46,7 MiB), todos os blobs idênticos ao commit. Aplicação, dependências declaradas, exemplos, duas versões do manual e licenças presentes; testes, scripts, planejamento, relatórios, ambientes e saídas locais ausentes. [Auditoria da publicação inicial](../../tests/reference/sprint16/delivery/point-5/published-zip-checks.json).

O usuário aceitou manter .vscode com suas três configurações compartilhadas. launch.json/settings.json acompanham o ZIP; tasks.json permanece no clone para testes. Não houve alteração dessas configurações ou das regras de exclusão.

As correções locais autorizadas substituem o link indisponível da licença original pelo LICENSE distribuído e os oito links de manutenção por URLs do GitHub. Créditos, atribuições e licenças locais continuam disponíveis offline; a consulta dos relatórios externos requer rede. Os oito destinos técnicos foram verificados no GitHub.

capture_native_ks_hist.m e capture_native_s89.m agora usam fileparts/mfilename para localizar o projeto, sem caminho fixo do computador. Os corpos numéricos continuam byte a byte iguais aos da captura histórica. Os manifestos/arquivos das Sprints 8/9 permanecem históricos e intactos: seus hashes identificam os scripts daquela execução, recuperáveis pelo commit 2bb3355. O novo registro separa esses hashes dos scripts atuais; nenhuma captura científica foi refeita ou substituída.

As verificações locais e hashes estão em [post-publication-checks.json](../../tests/reference/sprint16/delivery/point-5/post-publication-checks.json). O README e os manuais aprovados permanecem intactos. Não houve commit/push do agente. O envio desta correção pertence ao usuário; a S16-09 permanece sem X até a conferência remota final da versão ajustada. Windows/Linux continuam reservados aos testes posteriores do usuário.

**Resultado dos ajustes locais:** verificação real dos dois trechos de localização no MATLAB R2024b, em cópia temporária com espaços/acentos e diretório de trabalho diferente; nenhum cálculo científico executado. Candidato ZIP atualizado com 262 arquivos: somente THIRD_PARTY_NOTICES.md difere entre seus arquivos de uso e os do ZIP publicado. Foram conferidos 46 links locais sem destinos ausentes e oito links técnicos no GitHub. README, manuais, configurações VS Code, 53 figuras aceitas, implementação científica, 164 originais e oito saídas conhecidas da referência permanecem íntegros. Pronto para o commit/push do usuário.

## Encerramento da S16-09 — 16/11/2026

O usuário informou o segundo push. A branch main do GitHub foi conferida antes e depois da validação e aponta para **df9f512bb3c0e3e3404344997f5d6b1941d25b49**, com a correção dos créditos e a portabilidade dos dois scripts MATLAB. A comparação dos três arquivos pela API confirma os blobs do commit. Nenhum commit/push foi feito pelo agente.

O ZIP real desse commit foi baixado e validado: **262 arquivos**, todos com conteúdo correspondente ao commit publicado, CRC íntegro e exclusões corretas. Foram conferidos **46 links locais sem destinos ausentes**, oito destinos técnicos no mesmo commit e os dois scripts idênticos aos validados no MATLAB. README aprovado, PDFs, fontes LaTeX e configurações VS Code preservados. Entre os arquivos de uso, somente THIRD_PARTY_NOTICES.md difere da publicação inicial; os ajustes nos scripts e registros de manutenção acompanham o clone completo.

[Evidências finais](../../tests/reference/sprint16/delivery/point-5/final-publication-checks.json) e [estado de entrega](../../tests/reference/sprint16/delivery/status.json) registram a conclusão dos pontos 1–5. **S16-09 e S16-09.5 marcadas com X no PRD.** Os registros anteriores desta página e os relatórios anteriores conservam os estados e hashes históricos. Windows/Linux permanecem reservados ao usuário, conforme a definição de escopo; nenhuma nova execução da suíte completa ou comparação científica é atribuída a esta verificação de publicação.

O código validado está em [luis-mauricio/pyfracpaq](https://github.com/luis-mauricio/pyfracpaq); [ZIP do commit verificado](https://github.com/luis-mauricio/pyfracpaq/archive/df9f512bb3c0e3e3404344997f5d6b1941d25b49.zip). O registro local de encerramento altera somente documentação/evidências excluídas do ZIP, sem modificar o programa entregue.
