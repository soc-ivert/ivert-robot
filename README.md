# Ivert Robot

O Ivert Robot é um agente de IA recepcionista desenvolvido para a Casa Verde (Ivert). O robô é capaz de recepcionar visitantes, fornecer informações sobre o instituto e eventos. Os visitantes são identificados através de reconhecimento facial caso estejam cadastrados, tornando possível que o robô os trate diretamente pelo nome. Caso não estejam cadastrados, o robô pode cadastrá-los durante o diálogo solicitando apenas seu nome. 

O projeto foi projetado para operar em hardware simples e em funcionamento contínuo, sendo "plug and play", distribuindo responsabilidades entre um servidor Linux em TV Box e um tablet Android como interface interativa.

<div align="center">
   <img width="50%" alt="Captura de tela 2026-09-24 154427" src="https://github.com/user-attachments/assets/5d702932-d9bb-458c-b938-93d6312fbe62" />
</div>

## Arquitetura

O sistema opera em modelo cliente-servidor na mesma rede local, comunicando-se via HTTPS (certificados autoassinados) e WebSocket bidirecional:

### 1. Servidor Backend (TV Box Armbian)
Hospeda o servidor FastAPI, contendo a lógica de negócio do robô:
- **Processamento de Visão:** Recebe frames de vídeo via WebSocket e processa detecção e extração de encodings faciais através de OpenCV e dlib.
- **Banco de Dados Local:** Armazena e busca usuários por similaridade vetorial facial em um banco SQLite.
- **Orquestração de IA:** Integra a API do Google Gemini com suporte a tool calling, permitindo ao modelo verificar quem está diante da câmera, realizar cadastros e obter eventos.
- **Sincronização de Estado:** Mantém uma máquina de estados e temporizadores de inatividade para coordenar a interação com o tablet.

### 2. Interface Interativa (Tablet Android)
Opera em modo *kiosk* dedicado utilizando o aplicativo Fully Kiosk Browser em tela cheia:
- **Câmera e Microfone:** Captura vídeo para envio contínuo de frames ao servidor.
- **Áudio e Microfone:**  Ouve perguntas através da Web Speech API e utiliza a interface nativa do Fully Kiosk para responder com reprodução de voz (TTS).
- **Expressão:** Exibe a face do robô, que reage visualmente a cada mudança de estado.

### 3. Máquina de Estados
O robô transiciona dinamicamente entre cinco estados sincronizados via WebSocket:
- **`sleeping`**: Estado de repouso. O robô monitora a câmera em segundo plano.
- **`greeting`**: Ao avistar um rosto humano, o robô desperta, aguardando ativação por voz (como "Oi robô").
- **`waiting`**: Robô ouvindo a dúvida ou solicitação do visitante.
- **`thinking`**: Momento de consulta das ferramentas e geração de resposta pelo modelo Gemini.
- **`speaking`**: Resposta falada reproduzida pelo tablet.

Se o visitante se afastar ou a conversa for interrompida, timers de inatividade retornam o robô ao estado `sleeping`.


## Funcionalidades

- **Reconhecimento Facial:** Detecção em tempo real via frames enviados pelo tablet e busca por similaridade vetorial.
- **Cadastro Conversacional de Visitantes:** Caso um visitante ainda não possua cadastro, o agente identifica o rosto humano, extrai sua codificação facial e solicita que o visitante informe seu nome, cadastranto-o.
- **Integração com Planilha de Eventos:** Consulta a programação de eventos a partir de uma planilha Google Sheets publicada em CSV, com sistema de cache local de 24 horas para garantir disponibilidade e velocidade.


## Fluxo de Configuração

Para realizar a instalação completa
, siga a documentação detalhada disponível no diretório [`docs/`](docs/):

1. **Configuração de Rede ([`docs/network-setup.md`](docs/network-setup.md))**  
   Instruções para configurar a resolução de nome via mDNS (`avahi-daemon`) no Armbian, garantindo que o TV Box responda em `tvbox.local` independentemente do IP atribuído pelo roteador.

2. **Deploy no TV Box ([`docs/tvbox-deployment.md`](docs/tvbox-deployment.md))**  
   Instalação do sistema: pacotes, dependências do projeto, geração de certificados SSL e criação do serviço `systemd` para inicialização automática no boot.

3. **Configuração do Tablet ([`docs/tablet-setup.md`](docs/tablet-setup.md))**  
   Guia de configuração do Fully Kiosk Browser no tablet Android.
