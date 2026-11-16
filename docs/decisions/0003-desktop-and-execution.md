# ADR 0003 — Janela, estado e exportação base

**Atualização S16:** S16 mantém o worker e a apresentação Matplotlib na thread principal, mas exporta um PNG por evento Qt. Busy/contexto/temporários permanecem até terminar; job_completed só então é emitido. Exit pode interromper entre PNGs. Atalho Close nas figuras. Fonte GUI Helvetica capturada, fallback explícito. ADR0018 detalha o contrato atual.

Estado: implementado na Sprint 2, em 13/11/2026. Não aprova mudanças científicas nem antecipa as análises das próximas sprints.

## Interface e referência

`python run_gui.py` e `python -m pyfracpaq` chamam a mesma aplicação Qt Widgets. A fábrica de janela mantém um único MainWindow por processo; chamadas repetidas mostram a instância existente. A barra da janela diz FracPaQ, conforme Name do FIG; o cabeçalho interno diz Fracture Pattern Quantification e a identificação preserva figure_main. Qt Fusion, paleta clara e QSS impedem o tema escuro do sistema de alterar o formulário.

resources/ui_spec.json deriva dos 142 objetos com Tag do FIG original, com checksum da origem. Os 119 controles, grupos e três áreas de eixos mantêm seus nomes; os popups aplicam os três ajustes de OpeningFcn para índice 2. A janela inclui todos os controles das seis abas. Logo e ícone são cópias exatas, com procedência e licença em resources/provenance.json, carregadas por importlib.resources; não há dependência do diretório corrente ou da pasta original para abrir a aplicação instalada. As imagens mantêm sua proporção.

As posições normalizadas dos blocos principais são aplicadas ao formulário. Position de axes_tracemap é interpretada como área de dados; a borda do canvas é expandida para acomodar ticks/rótulos. Aspecto igual pode reduzir a área efetiva de dados depois de carregar uma geometria. Os painéis são empilhados em QStackedWidget, sem mudar as escolhas ao navegar.

**Revisão visual de 14/11/2026:** substituiu os layouts que redistribuíam controles por coordenadas relativas ao pai do FIG, inclusive nas seis abas. BorderType e FontWeight antes descartados agora fazem parte do recurso instalado. Navegação sem borda, botões com larguras iguais/altura original e grupos com borda rebaixada. Insets explícitos reservam a região dos títulos; correções locais impedem que rótulos cortados no original encubram seus campos. As escolhas usam indicadores azuis com marca branca, mantendo os estados Qt e acesso pelo teclado.

O cliente de referência é 1250×739 pixels lógicos, proporção medida nas capturas fornecidas do manual; não é conversão inventada de characters do FIG. A janela abre centralizada, normal, limitada a 90% da área útil com reserva para a moldura do sistema, até esse tamanho. FontSize preserva a hierarquia original na calibração em pixels lógicos (cabeçalho 30, texto usual 12); tamanhos menores reduzem a escala, sem ampliar fontes ao maximizar. Arial tem fallback DejaVu Sans. Prévia usa o tamanho de fonte do eixo de referência, independente do DPR, e onze ticks por eixo no estado vazio.

O formulário mínimo é 1000×591; rolagem da área cliente só aparece abaixo desse tamanho, com foco capaz de alcançar todos os controles. Não há mais scroll wrappers que modifiquem as dimensões das abas. [Relatório da revisão](../parity/ui-calibration.md) e quarenta capturas registram quatro DPRs e a superfície mínima sem cortes de texto. As capturas da Sprint 2 continuam preservadas como histórico anterior a essa correção. Aparência nativa e aprovação pixel a pixel MATLAB continuam pendentes; não se declara identidade de decorações do sistema operacional.

## Estados e prévia

Inicial: Ready, nenhuma prévia, estatísticas vazias, abas/Run/flips desabilitados. Filename aceita edição; Browse admite TXT/SVG/JPG/JPEG/TIF/TIFF e preserva todo o estado no cancelamento. A detecção de extensão ignora caixa; a seleção manual de tipo é respeitada. Apenas Preview TXT está implementado; SVG e imagem produzem mensagem explícita de indisponibilidade, sem conversão implícita ou dados fabricados.

Preview captura caminho absoluto, tipo, escala, extração e stamp (mtime_ns/tamanho). O worker lê pelo leitor da Sprint 1. A thread principal desenha a geometria, mostra exatamente as sete estatísticas, calcula a tolerância inicial I→Y e libera Maps/abas/Run/flips. Domínios lineares recebem apenas uma pequena margem de visualização no eixo sem amplitude, mantendo limites/área originais no Dataset e nas estatísticas.

Editar arquivo, tipo, escala ou qualquer parâmetro de extração invalida imediatamente a prévia e seus resultados de tela. Cada carga carrega uma revisão; uma conclusão antiga não pode restaurar dados obsoletos. Run verifica novamente a assinatura e o stamp do arquivo, cobrindo alteração externa ou mudança de pasta com Filename relativo. Norte, tag e opções analíticas não alteram a geometria de entrada; flips são flags de visualização e não reescrevem arrays.

## Execução e disponibilidade

AnalysisConfig, InputConfig e RunContext são dataclasses congeladas, sem Qt. O snapshot inclui opções e parâmetros das seis abas, seleção efetiva, tag, flips, fonte, pasta de saída e temporários exclusivos. Os campos da interface são desabilitados durante o trabalho, preservando Exit. A configuração já capturada não muda mesmo se um campo for alterado programaticamente.

O registro declarativo associa cada checkbox de análise ao ID, parâmetros necessários, dependências e callbacks de cálculo/renderização. Só os parâmetros das saídas selecionadas são validados; MLE não é selecionada sem seu pai Log-log. Validação de listas não executa expressões. Os limites ainda dependentes de decisões científicas permanecem nas respectivas Q; não se mudou a amostragem wavelet nem o significado angular nesta sprint.

**Nenhuma família analítica do Run foi implementada na Sprint 2.** Entradas pendentes têm compute=None e recusam Run com os nomes das saídas indisponíveis, antes de criar arquivos ou temporários. Não há função vazia, resultado demonstrativo ou mensagem de sucesso para essas seleções. Para executar cálculos novos, as próximas sprints ligarão callbacks reais ao mesmo registro. Os testes da infraestrutura injetam operações reais sobre o Dataset (como comprimento total e desenho dos traços) para verificar snapshot, thread e exportação; isso não torna MAP-01 implementada como análise selecionável do produto.

QObject em QThread executa leitura/cálculo; sinais levam progresso, resultado e erro à janela. Progresso de leitura é indeterminado enquanto a duração é desconhecida. Desenho interativo e renderização/exportação das figuras são feitos na thread principal. Exceções identificam análise/campo, deixam traceback no console e restauram estado. A mensagem abre a aba do campo relevante e o foco volta para ele depois de fechar o diálogo.

Exit fecha as figuras e mensagens pertencentes à janela. Durante trabalho, solicita interrupção e espera cooperativamente a operação corrente terminar, sem terminate e sem bloquear o loop Qt. Não fecha outros widgets/processos, terminal ou VS Code. A aba principal não ganha botão Cancel. Uma função científica futura precisa observar a callback de interrupção entre etapas; código externo bloqueado não pode ser abortado à força com segurança.

## Figuras e arquivos

FigureWindow oferece canvas QtAgg e toolbar normal de zoom/pan/restauração/salvamento. A exportação automática usa exclusivamente export_png: basename + '_' + tag + '.png', diretório corrente congelado, 20×20 cm e 600 dpi. Tag vazia preserva o sufixo '_' do fonte; separadores de caminho, controles e caracteres reservados são recusados sem reescrever o texto.

A exportação bloqueia bbox_inches=tight herdado de rcParams, não inclui moldura/toolbar e restaura o tamanho da figura de tela. Grava primeiro um PNG temporário próprio na pasta de destino e usa os.replace; falha preserva o arquivo anterior e limpa somente esse temporário. A substituição da mesma tag é registrada no console, sem confirmação adicional no fluxo. Nomes/base são fornecidos pelo registro das futuras análises; nenhum catálogo de figuras é gerado incondicionalmente.

Neste backend, 20 cm a 600 dpi produziu 4724×4724 pixels, com metadata PNG quantizada em aproximadamente 600 dpi. Essa é uma observação Python, não dimensão original MATLAB já confirmada. Estilo completo, tabelas RGB e demais TXT/intermediários seguem nas sprints de cada família.
