# 📱 Configuração do Tablet — Fully Kiosk Browser

Este documento detalha o processo de configuração do tablet Android para operar como a interface interativa (face do robô, áudio, câmera e microfone) do sistema.

Para que o robô funcione de forma autônoma e em modo *kiosk* (tela cheia permanente, sem barras de navegação e com recuperação automática em caso de queda de rede ou erro de carregamento), é utilizado o **Fully Kiosk Browser**.

A configuração de rede e o deployment no TV Box são detalhados em `docs/network-setup.md` e `docs/tvbox-deployment.md`. Assume-se que tais etapas já foram executadas.

### Por que o Fully Kiosk Browser

Nos testes com navegadores padrão e soluções de WebView convencionais no Android, o suporte à API nativa de síntese de voz (`SpeechSynthesis`) apresentou falhas ou inconsistências de execução em segundo plano. O Fully Kiosk resolve essa limitação disponibilizando uma **JavaScript Interface nativa** (objeto `fully.*`), permitindo executar e controlar o áudio e a síntese de voz diretamente no hardware do tablet com confiabilidade.

Além disso, o aplicativo provê controle de modo kiosk (bloqueio de barras de navegação, tela sempre ativa e supressão de diálogos repetitivos de permissão).

### Licença e Limitações

O Fully Kiosk Browser disponibiliza suas funcionalidades gratuitamente, porém com algumas limitações e com a exibição de uma marca d'água (*watermark*). No momento atual do projeto, a versão gratuita atende plenamente aos requisitos operacionais.

Alternativas como **PWA** (*Progressive Web App*) e **TWA** (*Trusted Web Activity*) serão exploradas no futuro para empacotamento nativo.

## Pré-requisitos

- Tablet Android conectado à mesma rede Wi-Fi que o TV Box.
- Servidor do TV Box em execução e mDNS configurado conforme `docs/network-setup.md`.
- Token de acesso configurado no `.env` do TV Box (`TABLET_ACCESS_TOKEN`).

> A URL de acesso padrão tem o formato:  
> `https://tvbox.local:8484?token=<TABLET_ACCESS_TOKEN>`  
> *(Substitua `<TABLET_ACCESS_TOKEN>` pelo valor configurado no `.env` do servidor)*.

Existem duas formas de realizar a configuração: importando o arquivo de configurações pré-definido ou fazendo o passo a passo manual. Para ambos os métodos:
- O **primeiro passo** é sempre baixar o Fully Kiosk Browser no tablet.
- O **último passo** é configurar a página de erro personalizada (opcional, disponível em `fully/error.html`).

## Passo inicial comum: Baixar o Fully Kiosk Browser

No tablet Android, baixe e instale o **Fully Kiosk Browser & Launcher** (via Google Play Store ou diretamente do site oficial). Abra o aplicativo e conceda as permissões iniciais solicitadas pelo Android.

## Opção 1: Importar configurações pré-definidas (Mais rápido)

1. Baixe ou copie os arquivos da pasta `fully/` do projeto para o armazenamento do tablet:
   - `fully/fully-settings.json`
   - `fully/error.html`
2. No Fully Kiosk Browser, abra o menu lateral deslizando a partir da borda esquerda.
3. Acesse **Settings** -> **Other Settings** -> **Import Settings**.
4. Selecione o arquivo `fully-settings.json`.
5. Ajuste a URL inicial com o seu token:
   - **Settings** -> **Web Browsing** -> **Start URL**:  
     `https://tvbox.local:8484?token=<TABLET_ACCESS_TOKEN>`
6. Execute o [Passo final: Página de erro personalizada](#passo-final-página-de-erro-personalizada-opcional).

## Opção 2: Configuração manual passo a passo

### 1. Configuração na tela inicial (ao abrir pela primeira vez)

Na tela inicial exibida na primeira abertura do app:
- **Start URL:** defina a URL com o token de parâmetro (`https://tvbox.local:8484?token=<TABLET_ACCESS_TOKEN>`).
- Habilite a opção de modo fullscreen (**Fullscreen Mode**).
- Deixe desabilitadas as opções **Show Action Bar** e **Show Address Bar**.
- Selecione **Start using Fully**.

### 2. Configurações avançadas (painel lateral)

Abra o painel lateral deslizando da borda esquerda para a direita e acerte as seguintes seções em **Settings**:

#### Advanced Web Settings
- **Ignore SSL Errors:** `Habilitado` (necessário para aceitar o certificado autoassinado gerado no TV Box).
- **Enable JavaScript Interface:** `Habilitado` (permite ao código web acionar o TTS e áudio nativo do tablet).
  > Ao voltar para a tela inicial, será solicitada permissão para usar a interface JavaScript. Clique em **OK** e aceite as permissões subsequentes.
- **Enable User Interactions:** `Desativado` (impede cliques e toques acidentais na tela, preservando a interface do robô).

#### Web Content Settings
- **Enable Microphone Access:** `Habilitado`.
- **Enable Webcam Access:** `Habilitado`.
  > Ao voltar para a página inicial, o Fully pedirá para conceder permissão para ambos. Clique em **OK** e aceite as permissões durante o uso do app.

#### Web Auto Reload
- **Auto Reload after Page Error:** defina para `5` a `10` segundos (ou o valor desejado para re-tentativas de conexão caso o servidor esteja indisponível).
- **Auto Reload on Screen On:** `Habilitado` (recarrega a página ao ligar a tela).
- **Auto Reload on Network Reconnect:** `Habilitado` (recarrega automaticamente assim que a conexão de rede for restabelecida).

## Passo final: Página de erro personalizada (Opcional)

Para exibir uma interface informativa e elegante quando o servidor estiver fora do ar ou reiniciando:

1. Certifique-se de que o arquivo `fully/error.html` está no tablet.
2. Abra o menu lateral -> **Settings** -> **Web Content Settings**.
3. Em **Custom Error URL**, escolha **Pick a file** e selecione o arquivo `error.html`.

## Validação

**Na tela do tablet:**
1. A interface deve abrir em tela cheia, sem barra de endereços ou botões de navegação.
2. Não devem aparecer avisos bloqueantes de certificado SSL.
3. As permissões de microfone e câmera não devem ser solicitadas novamente após a concessão inicial.
4. O áudio e as falas do robô devem ser executados sem falhas via interface JavaScript.
5. Ao simular uma queda de conexão (ex.: desligar o Wi-Fi ou reiniciar o serviço no TV Box), o tablet deve tentar recarregar automaticamente dentro do tempo configurado.

---
