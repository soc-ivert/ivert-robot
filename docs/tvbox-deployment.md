# 🚀 TV BOX Deployment

Este documento detalha o processo de preparar um TV Box Armbian para rodar o sistema do Robô de forma automática, sem precisar de intervenção manual toda vez que o TV Box for ligado.

A configuração de rede (mDNS/Avahi) é detalhada em `docs/network-setup.md`. Assume-se que tal configuração já foi executada.

Será adotado `systemd` como mecanismo de inicialização automática e recuperação de falhas, em vez de scripts.

## Pré-requisitos

- TV Box com Armbian instalado e com acesso SSH ou terminal local.
- Configuração de rede (mDNS) já realizada conforme `docs/network-setup.md`
> Este guia usa `/home/<usuario>/robot` como caminho de exemplo. Substitua `<usuario>` pelo nome do usuário real do sistema em cada comando.

### Variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto com o seguinte conteúdo, substituindo os valores de exemplo:

```dotenv
# Servidor
HOST=0.0.0.0
PORT=8484

# Autenticação
TABLET_ACCESS_TOKEN=<gere-um-token-seguro-aleatorio>

# IA - Gemini
GEMINI_API_KEY=<sua-chave-de-api-do-gemini>
```

| Variável | Descrição |
|---|---|
| `HOST` | Interface de rede onde o servidor escuta. |
| `PORT` | Porta do servidor HTTPS. |
| `TABLET_ACCESS_TOKEN` | Token de autenticação exigido nas requisições/WebSocket do tablet. |
| `GEMINI_API_KEY` | Chave de API do Gemini usada pelo Agent. |

> **Nota:** existe suporte planejado para migrar para o Google Cloud (Vertex AI) via `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` e `GOOGLE_GENAI_USE_ENTERPRISE`, pendente de configuração de faturamento no GCP. Essas variáveis substituirão `GEMINI_API_KEY` quando ativadas, veja `.env.example`.

## Passo a passo

### 1. Atualizar o sistema

```bash
sudo apt update && sudo apt upgrade -y
```
Atualiza a lista de pacotes disponíveis e aplica atualizações pendentes.

### 2. Instalar dependências de sistema (compilação das bibliotecas de visão computacional)

Essas bibliotecas são necessárias **antes** do `pip install`, porque pacotes como `dlib` compilam código C/C++ nativo durante a instalação.

```bash
sudo apt install -y build-essential cmake python3.11-dev
```
- `build-essential`: conjunto de compiladores e ferramentas (gcc, make, etc.) necessário para compilar extensões nativas em C/C++.
- `cmake`: sistema de build usado pelo processo de compilação do `dlib`.
- `python3.11-dev`: cabeçalhos de desenvolvimento do Python 3.11, necessários para compilar extensões que se conectam ao interpretador Python (bindings C/Python).

```bash
sudo apt install -y libopenblas-dev liblapack-dev libx11-dev
```
- `libopenblas-dev` e `liblapack-dev`: bibliotecas de álgebra linear otimizada, usadas por `numpy` e `dlib` para acelerar operações matriciais (essenciais no processamento de reconhecimento facial).
- `libx11-dev`: cabeçalhos de desenvolvimento do X11, exigidos pelo processo de build do `dlib` mesmo em ambientes sem interface gráfica.

### 3. Instalar Python 3.11 e o módulo de ambiente virtual

```bash
sudo apt install -y python3.11 python3.11-venv
```


Se o pacote `python3.11` não estiver disponível nos repositórios padrão do Armbian (isso pode variar conforme a versão base do Debian), verifique com `apt-cache policy python3.11` antes de seguir. Como você já validou esse processo em ambiente real, isso serve como checagem preventiva para replicações futuras.

### 4. Copiar o projeto para o TV Box

```bash
git clone https://github.com/codevinni/robot.git /home/<usuario>/robot
cd /home/<usuario>/robot
```


### 5. Criar o ambiente virtual

```bash
python3.11 -m venv venv
source venv/bin/activate
```


### 6. Instalar as dependências do projeto

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Atenção em dispositivos ARM com pouca memória:** a compilação do `dlib` é pesada e pode falhar silenciosamente por falta de RAM em TV Boxes com pouca memória. Se a instalação travar ou falhar sem erro claro, veja a seção de Troubleshooting sobre criação de swap temporário.

### 7. Gerar o certificado HTTPS autoassinado

Execute na raiz do projeto:

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 3650 -nodes \
  -subj "/CN=tvbox.local(ou nome do domínio local)" \
  -addext "subjectAltName=DNS:tvbox.local,DNS:localhost,IP:127.0.0.1"
```
Esse comando irá gerar `key.pem` e `cert.pem`.

> **Validade do certificado:** o comando usa `-days 3650`, ou seja, o certificado expira em 10 anos. Como é um projeto para rodar na rede local, não há problemas. Passado esse prazo, o HTTPS para de funcionar sem aviso prévio. Caso isso ocorra, basta gerar novamente.



### 9. Configurar o serviço systemd da aplicação

```bash
sudo nano /etc/systemd/system/robot.service
```

Conteúdo do arquivo:

```ini
[Unit]
Description=Sistema do robo receptionista
After=network-online.target avahi-daemon.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/<usuario>/robot
ExecStart=/home/<usuario>/robot/venv/bin/python main.py
Restart=on-failure
RestartSec=5
User=<usuario>

[Install]
WantedBy=multi-user.target
```

- `Description`: texto identificador exibido em `systemctl status` e nos logs.
- `WorkingDirectory`: define a pasta de trabalho do processo. Fundamental para que caminhos relativos no código resolvam corretamente.
- `ExecStart=/home/vinicius/robo-ivert/venv/bin/python main.py`: chama o Python de dentro do venv.
- `Restart=on-failure`: reinicia o processo automaticamente se ele encerrar com erro.


Aplicar e habilitar:

```bash
sudo systemctl daemon-reload
```
Recarrega as definições do systemd.

```bash
sudo systemctl enable robo-ivert
```
Habilita o início automático a cada boot.

```bash
sudo systemctl start robo-ivert
```
Inicia o serviço agora, sem precisar reiniciar o TV Box para testar.

```bash
sudo systemctl status robo-ivert
```
Veja se o estado é `active (running)`.

```bash
journalctl -u robo-ivert -f
```
Acompanha os logs em tempo real.


## Validação

**No próprio TV Box:**
```bash
curl -k https://localhost:8484
```
Deve retornar uma resposta do servidor.

**A partir do tablet:**
```
https://tvbox.local:8484
```
Deve carregar a interface.


## Swap

Criando swap temporário (para compilação do `dlib` em dispositivos com pouca RAM):

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```
Cria um arquivo de 2GB usado como memória virtual extra durante a compilação. Depois de instalar as dependências com sucesso, esse swap pode ser mantido (recomendado, como rede de segurança) ou removido com `sudo swapoff /swapfile && sudo rm /swapfile`, conforme a memória real disponível no dispositivo.

Para tornar o swap permanente entre reboots (recomendado manter, já que ajuda também em picos de uso do reconhecimento facial em produção):
```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```


## Notas

- O aviso de "conexão não segura" do navegador ao acessar via HTTPS autoassinado é esperado e não indica um problema de configuração — apenas que não existe uma autoridade certificadora reconhecida validando o certificado.

---