# Origem e validação

Extração em 27/10/2026 de `orbitzone/orbitz-widgets-for-gnome`, commit de origem `a0bcb0302405d176aa3be5118a5b211caf90d1fd`. Foram copiados apenas os fontes próprios do app YouTube, ícone, traduções YouTube e testes dirigidos. Nenhuma chave real, configuração de usuário, credencial ou arquivo pessoal foi copiado.

A versão independente usa aplicação/schema/i18n próprios, API key e cache em `orbitz-youtube-desktop`, caminho web local dentro de `app/` e launcher Flatpak sem o GNOME Shell. O app registra o esquema GSettings próprio. O runtime GNOME 49 fornece WebKitGTK 4.1; o código extraído foi atualizado da API introspectiva WebKit2 4.0 para 4.1, requerendo confirmação por CI.

Escopo: Linux x86_64/Flatpak/X11 ou XWayland; sem Windows/macOS, Flathub, importação automática de configurações/chave ou instalação da versão ativa do Orbitz. Não garante remoção de anúncios: Data API retorna resultados/IDs; player incorporado é servido pelo YouTube. Evidências de testes e build serão acrescentadas após execução no CI. Visual real, portais e reprodução com conta/quota própria não serão inferidos do build.

## Validação local pré-publicação (27/10/2026)

19 testes Python e quatro testes JavaScript passaram; `py_compile`, `desktop-file-validate`, `appstreamcli validate --no-net`, parse do manifesto Flatpak e `git diff --check` passaram. Esses testes usam dados sintéticos e não consultam YouTube/Google. O primeiro build Flatpak apontou que o SVG não era quadrado; o desenho foi centralizado numa tela 36×36. O [CI final 40608208765](https://github.com/orbitzone/orbitz-youtube-desktop/actions/runs/40608208765) passou após a autenticação por token dos bridges, validou importação de WebKitGTK 4.1 e gerou o bundle x86_64. SHA-256 de `orbitz-youtube-desktop-x86_64.flatpak`: `917e785eeea8ea0a1b2dc02447b19c715ab8128702f4977888cbe01668b29de1`; a cópia publicada foi baixada e conferida com `SHA256SUMS`. Execução gráfica em distribuições distintas e reprodução com chave/conta reais dependem de validação manual posterior.
