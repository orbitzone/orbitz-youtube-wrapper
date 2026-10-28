# YouTube Wrapper

### YouTube, em uma janela só. E um pequeno alien para fazer companhia.

Pesquise vídeos, Shorts, transmissões ao vivo e podcasts, leia comentários e assista pelo player oficial do YouTube. Quando não houver vídeo na tela, o Orbitz Runner espera por você: um jogo arcade espacial com um ET, obstáculos, tiros automáticos e recorde local.

**Leve, direto e independente do GNOME Shell.** Feito por Felipe Santiago / orbitzone como projeto comunitário, sem afiliação com Google ou YouTube.

> A versão atual é uma prévia para Linux x86_64. Ela ainda não está no Flathub e não recebe atualizações automáticas.

## O que você encontra

- **Busca do YouTube:** vídeos, comentários e recomendações recentes em português. Busca e comentários usam sua própria chave da YouTube Data API v3.
- **Shorts e lives:** filtros dedicados para encontrar vídeos curtos e transmissões ao vivo ativas.
- **Podcasts:** busca orientada a episódios de podcast.
- **Player oficial:** reproduza vídeos incorporados, use tela cheia e copie o link do vídeo selecionado.
- **Orbitz Runner:** um mini game que começa só quando você aperta Espaço ou clica. Pule obstáculos, veja os cactos explodirem e tente superar seu recorde.
- **Português e inglês:** escolha Português (Brasil) ou English (United States) nas configurações.
- **Seus dados no seu computador:** chave, preferências, cache e recorde ficam no perfil local do aplicativo; não há sincronização nem telemetria própria.

## Instalar no Linux

O pacote disponível é um Flatpak x86_64. É necessário usar X11 ou uma sessão Wayland com XWayland, além de conexão à internet para os serviços do YouTube. O aplicativo usa o runtime GNOME 49 e não exige uma versão específica do GNOME Shell.

1. Instale o [Flatpak para sua distribuição](https://flatpak.org/setup/).
2. Baixe o arquivo `orbitz-youtube-desktop-x86_64.flatpak` na [prévia v0.1.0](https://github.com/orbitzone/orbitz-youtube-wrapper/releases/tag/v0.1.0). O nome do arquivo foi mantido desde a publicação inicial.
3. No terminal, entre na pasta do download e instale:

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user ./orbitz-youtube-desktop-x86_64.flatpak
flatpak run io.orbitz.YouTubeDesktop
```

Depois, você também pode abrir **YouTube Wrapper** pelo menu de aplicativos. Para atualizar, instale uma versão mais recente quando ela for publicada. O arquivo `SHA256SUMS` da release permite conferir a integridade do download.

## Começar a usar

Abra **Configurações** e cole uma chave pessoal da YouTube Data API v3 para habilitar buscas e comentários. A página de [credenciais do Google Cloud](https://console.cloud.google.com/apis/credentials) permite criar a chave; o projeto também precisa ter a YouTube Data API v3 habilitada e quota disponível.

A chave é guardada localmente no diretório privado do aplicativo, com permissão restrita. O app também consegue ler uma chave salva por uma instalação anterior do Orbitz YouTube Desktop; ao salvar uma nova, ela fica no local atual do aplicativo. Não compartilhe arquivos de configuração que contenham sua chave.

Para assistir a um vídeo sem configurar a API, cole um link do YouTube na busca. Você também pode iniciar o Orbitz Runner na tela inicial usando **Espaço** ou clicando na área do jogo.

## Como funcionam os filtros

O YouTube não disponibiliza um filtro oficial de pesquisa para todas essas categorias. Por isso, alguns resultados são aproximações:

- **Shorts:** usa o filtro oficial de vídeos com menos de quatro minutos. Isso pode incluir vídeos que não são classificados pelo YouTube como Shorts.
- **Ao vivo:** procura transmissões que estejam ativas.
- **Podcasts:** acrescenta o termo “podcast” à busca; os resultados podem incluir outros tipos de vídeo.

As recomendações iniciais mostram vídeos recentes em português. Uma consulta digitada só é enviada quando você inicia a busca. Os limites de uso e a quota seguem as regras do Google Cloud para a sua chave.

## Sobre o player e os vídeos

A YouTube Data API encontra vídeos e fornece seus identificadores. A reprodução acontece no player incorporado oficial, carregado pelo YouTube. Anúncios, disponibilidade, restrições, autenticação e reprodução são controlados pelo YouTube e pelos responsáveis pelos vídeos. A chave da API não remove anúncios nem dá acesso ao arquivo de vídeo.

## Privacidade e permissões

O aplicativo não envia telemetria própria nem sincroniza seus dados. Consultas e links são enviados ao YouTube/Google quando você usa esses serviços; a chave configurada é enviada à API oficial nas solicitações de busca e comentários. Cache, idioma, chave e recorde do jogo são armazenados localmente no perfil Flatpak do aplicativo.

O pacote solicita rede, X11 e áudio para reproduzir vídeos, sem acesso geral aos seus arquivos pessoais. Em Wayland, é necessário XWayland. A posição da janela, tela cheia, áudio e abertura de links externos também dependem do ambiente Linux instalado.

## Compilar a partir do código

Para gerar e instalar uma versão Flatpak localmente, instale Flatpak, `flatpak-builder`, Node.js e configure o remoto Flathub:

```sh
flatpak-builder --user --install-deps-from=flathub --assumeyes --repo=repo build-dir packaging/io.orbitz.YouTubeDesktop.json
flatpak build-bundle repo orbitz-youtube-wrapper-x86_64.flatpak io.orbitz.YouTubeDesktop --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo
```

Para executar diretamente numa sessão X11/XWayland, são necessários Python 3, GTK 3, WebKitGTK 4.1, PyGObject, SQLite e Node.js:

```sh
python3 app/youtube-wrapper.py
```

Os testes são executados sem chave real e sem chamadas à API:

```sh
make test
```

Consulte [origem e validação](docs/validation.md) para conhecer o histórico do pacote e as verificações disponíveis.

## Licença e independência

O projeto é distribuído sob a licença [GPL-3.0](LICENSE). YouTube e Google são marcas de seus respectivos titulares. Este aplicativo comunitário não é produzido, aprovado nem mantido pelo Google.
