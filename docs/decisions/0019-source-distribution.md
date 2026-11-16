# ADR 0019 — Distribuição pelo código no GitHub

Data: 16/11/2026. **Decisão explícita do usuário**, durante a execução do ponto 4 da S16-09.

O produto será distribuído como código no GitHub. O usuário obtém a pasta por clone ou download ZIP e executa o programa nessa pasta, pelo terminal ou VS Code, com Python 3.13 e as dependências. Miniforge pode fornecer o ambiente Python. Não se prevê instalador de aplicativo, wheel como entrega ao usuário, instalação do pacote PyFracPaQ no ambiente ou distribuição de um wheelhouse como requisito de uso.

A preparação do ambiente continua necessária: instalar Python e as dependências de requirements.txt. Executar `python run_gui.py` ou `python -m pyfracpaq` na raiz. O modo editável via pip é opcional para desenvolvimento e não faz parte do caminho normal de uso. VS Code utiliza o interpretador escolhido; Miniforge é uma opção para gerenciar esse ambiente.

A versão permanece 0.9.0rc1, com November 2026 e luismauricio@me.com. A referência MATLAB continua FracPaQ 2.8. O funcionamento após preparar as dependências permanece local/offline; a obtenção inicial de código e dependências pode exigir rede.

O ponto 4 é redefinido como **preparação e validação do código para clone/download**, incluindo conteúdo do repositório/ZIP, exclusões, instruções e execução em ambiente limpo sem instalar o pacote do projeto. O ponto 5 é a disponibilização do código no GitHub e registro da entrega, ainda dependente da autorização específica prevista no fluxo de um ponto por vez. Windows/Linux permanecem para os testes posteriores do usuário.

Os pacotes locais 0.1.0rc1 e os artefatos 0.9.0rc1 gerados antes desta definição são evidências técnicas internas, não a distribuição do produto. Os testes de instalação desses pacotes não concluem o novo ponto 4. Não houve publicação desses arquivos.

Os originais MATLAB, ambientes virtuais, caches, segredos, builds e saídas de análises permanecem fora do repositório conforme .gitignore. As referências MATLAB são necessárias somente para repetir testes específicos de comparação, não para executar o programa. Os relatórios anteriores permanecem históricos; esta decisão substitui o requisito de entregar pacotes instaláveis.

## Material de desenvolvimento e ZIP de uso

Em continuidade ao esclarecimento do usuário sobre testes/relatórios, o clone completo preserva testes, ferramentas e evidências para manutenção, sem dependência em tempo de execução. O ZIP de uso usa .gitattributes/export-ignore para excluir tests/, scripts/, relatórios de paridade, decisões internas e documentos de planejamento. Mantém programa, recursos, requirements.txt, exemplos, configurações de execução, manual, notas e licenças. Nenhuma evidência aprovada foi apagada. A descoberta automática de pytest no VS Code fica desativada; requirements-dev.txt é opcional no repositório completo.

A política foi conferida com o [git archive oficial](https://git-scm.com/docs/git-archive#ATTRIBUTES) em repositório temporário, sem alterar o índice ou criar commit na cópia do usuário. A conferência do ZIP remoto efetivamente oferecido pelo GitHub fica no ponto 5, após a disponibilização autorizada.

## Responsabilidade pelo envio ao GitHub

O usuário definiu explicitamente que fará o envio dos arquivos. O agente prepara e confere os arquivos e a documentação, sem commit, push ou publicação. O ponto 5 permanece aberto até a confirmação do envio e a conferência do repositório/ZIP remoto. README e manual ilustrado em LaTeX/PDF foram preparados para revisão antes desse envio.
