# Orbitz YouTube Desktop

Um mini app independente para pesquisar vídeos, Shorts e transmissões ao vivo, consultar comentários e reproduzir vídeos do YouTube numa janela compacta. Busca e comentários usam uma chave própria da YouTube Data API v3, salva localmente; links de vídeo podem abrir diretamente sem chave. A aplicação usa o player incorporado oficial do YouTube para a reprodução.

Desenvolvido por **Felipe Santiago / orbitzone** e extraído do [Orbitz Widgets for GNOME](https://github.com/orbitzone/orbitz-widgets-for-gnome), sob GPL-3.0. É um projeto comunitário sem afiliação com Google ou YouTube.

Busca e reprodução são partes separadas: a [YouTube Data API retorna detalhes e IDs dos vídeos](https://developers.google.com/youtube/data/reference/rest/v3/search/list); para reproduzir, o app carrega esse ID no [player incorporado oficial](https://developers.google.com/youtube/player_parameters). Portanto, o vídeo pode exibir anúncios definidos pelo YouTube e pelo canal. Uma chave própria da API não remove anúncios nem fornece o arquivo de vídeo.

## Instalação Linux com Flatpak

Pacote x86_64 para distribuições Linux com Flatpak e X11 ou sessão Wayland com XWayland. Requer conexão à internet para usar APIs/players do YouTube. Não depende de versão do GNOME Shell; runtime e arquitetura delimitam a compatibilidade. Não promete suporte a todas as distribuições.

1. [Instale Flatpak para sua distribuição](https://flatpak.org/setup/).
2. Baixe o `.flatpak` da prévia em [Releases](https://github.com/orbitzone/orbitz-youtube-desktop/releases). Até a publicação da primeira prévia, use o artefato verde em [Actions](https://github.com/orbitzone/orbitz-youtube-desktop/actions).
3. No diretório do download:

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user ./orbitz-youtube-desktop-x86_64.flatpak
flatpak run io.orbitz.YouTubeDesktop
```

O ícone também aparece no menu. Para fechar, feche a janela. Não há início automático. Atualizações exigem instalar novo pacote; ainda não há canal Flathub/atualização automática.

## Configurar e usar

- Abra Configurações e informe uma chave pessoal da YouTube Data API v3 para busca/comentários. A chave fica em `~/.var/app/io.orbitz.YouTubeDesktop/config/orbitz-youtube-desktop/youtube.json` com permissão privada. Não compartilhe o pacote com credenciais. Consulte limites de quota do seu projeto no Google Cloud.
- URLs diretas do YouTube podem ser coladas na busca sem chave. O filtro Shorts usa vídeos de menos de quatro minutos como aproximação; não garante a classificação Shorts. O filtro Live procura transmissões ativas.
- Preferências e cache ficam dentro do diretório Flatpak do app. Nenhuma chave/configuração do Orbitz Widgets é importada automaticamente.
- Para inglês nesta prévia: `flatpak run --env=ORBITZ_LOCALE=en-US io.orbitz.YouTubeDesktop`.

## Compatibilidade e privacidade

O mini app usa GTK 3, WebKitGTK 4.1, X11 e conectividade de rede. Sessões Wayland precisam de XWayland; Wayland sem XWayland não é suportado. Janela centralizada, tela cheia, reprodução incorporada e aplicações padrão variam entre gerenciadores/portais. A compatibilidade visual em GNOME/KDE/Xfce reais ainda requer teste.

O Flatpak precisa de rede para falar com Google/YouTube e acesso X11 para a interface atual. Não recebe acesso geral à pasta pessoal. URLs e consultas seguem para os servidores do YouTube; a chave de API é enviada à API oficial pelo próprio aplicativo. Não há telemetria nem sincronização própria. Revisar termos/quotas da Google API e a política do YouTube antes de usar.

## Compilar

Instale `flatpak-builder`, Flatpak, Node.js e o remoto Flathub. Na raiz:

```sh
flatpak-builder --user --install-deps-from=flathub --assumeyes --repo=repo build-dir packaging/io.orbitz.YouTubeDesktop.json
flatpak build-bundle repo orbitz-youtube-desktop-x86_64.flatpak io.orbitz.YouTubeDesktop --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo
```

Desenvolvimento nativo: Python 3, GTK 3, WebKitGTK 4.1, PyGObject, SQLite e Node.js. Execute `python3 app/youtube-widget.py` numa sessão X11/XWayland. `make test` usa mocks/fixtures e testes de interface sem chamar APIs reais. Nunca coloque chave real em testes. Veja [origem e validação](docs/validation.md).
