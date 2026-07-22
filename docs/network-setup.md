# 🌐 Configuração de Rede — Resolução de Nome via mDNS (Avahi)


O sistema do Robô roda em um TV Box (Armbian) que atua como servidor, enquanto um tablet Android se comunica com ele via rede local para servir a interface (face do robô, WebSocket, etc.). Para que o tablet saiba onde encontrar o servidor, é necessário algum mecanismo de descoberta de endereço.

O requisito principal do projeto é que o sistema seja **plug and play**: depois de instalado, ele deve continuar funcionando apenas ligando o TV Box e o tablet, sem intervenção.

### Por que não usar IP fixo simples

A abordagem mais simples seria fixar o IP do TV Box manualmente no código. O problema é que, sem uma reserva de IP feita no roteador, o DHCP pode atribuir um IP diferente ao TV Box a qualquer momento.

### Por que não usar reserva de IP por MAC no roteador

Essa seria a solução ideal em conjunto com um nome de rede, pois garante que o IP nunca mude. **Não foi possível usá-la neste projeto porque não há acesso administrativo ao roteador do local.** Essa alternativa fica documentada aqui para referência.

### mDNS

Diante dessa limitação, a solução escolhida foi o **mDNS (Multicast DNS)**, implementado no Linux através do `avahi-daemon`. Ele permite que o TV Box anuncie a si mesmo na rede local sob um nome fixo, resolvido automaticamente por qualquer dispositivo compatível, mesmo que o IP interno do TV Box mude.

**Importante:** mDNS funciona *apenas dentro da rede local*. Nesse projeto isso não é uma limitação real, pois tablet e TV Box estão sempre na mesma rede física.



## Passo a passo

### 1. Atualizar repositórios e instalar o Avahi

```bash
sudo apt update
```
Atualiza a lista de pacotes disponíveis, garantindo a instalação da versão mais recente.

```bash
sudo apt install avahi-daemon avahi-utils -y
```
- `avahi-daemon`: serviço que implementa mDNS/DNS-SD no Linux (implementação livre do protocolo Bonjour da Apple).
- `avahi-utils`: ferramentas de linha de comando (`avahi-browse`, `avahi-resolve`) usadas para validar a resolução de nomes sem depender do tablet.

### 2. Verificar/definir o hostname do sistema

```bash
hostnamectl
```
Mostra o hostname atual do sistema. É esse nome que o Avahi publica na rede como `<hostname>.local`.

Se necessário, defina um nome específico:

```bash
sudo hostnamectl set-hostname tvbox
```
Altera o hostname de forma persistente. O Avahi lê esse valor ao iniciar e passa a anunciar `tvbox.local` na rede.

### 3. Habilitar e iniciar o serviço

```bash
sudo systemctl enable avahi-daemon
```
Cria os links simbólicos necessários para que o systemd inicie o serviço automaticamente em todo boot futuro.

```bash
sudo systemctl start avahi-daemon
```
Inicia o serviço imediatamente, sem precisar reiniciar o sistema.

```bash
sudo systemctl status avahi-daemon
```
Para verificar o estado atual do serviço. Deve aparecer `active (running)`.

### 4. Proteger contra inicialização antes da rede estar pronta

Esse passo evita que o Avahi tente iniciar antes da interface de rede estar de fato ativa.

```bash
sudo systemctl edit avahi-daemon
```
Adicione:

```ini
[Unit]
After=network-online.target
Wants=network-online.target

[Service]
Restart=on-failure
RestartSec=5
```

- `After=network-online.target`: só inicia o Avahi depois que a rede estiver oficialmente online (não apenas depois que a interface exista).
- `Wants=network-online.target`: reforça essa dependência, garantindo que o alvo de rede seja ativado.
- `Restart=on-failure`: reinicia o serviço automaticamente caso o processo caia por qualquer motivo (crash, sinal inesperado).
- `RestartSec=5`: aguarda 5 segundos entre tentativas de restart, evitando um loop agressivo.


### 5. Confirmar que o `network-online.target` realmente espera a rede

O passo anterior só é eficaz se existir um serviço que define, de fato, quando a rede está "online". Verifique qual gerenciador de rede está ativo no sistema:

```bash
systemctl status systemd-networkd
```
ou

```bash
systemctl status NetworkManager
```

Um dos dois estará `active`. Em seguida, habilite o serviço de espera correspondente:

Se for `systemd-networkd`:
```bash
sudo systemctl enable systemd-networkd-wait-online.service
```

Se for `NetworkManager`:
```bash
sudo systemctl enable NetworkManager-wait-online.service
```

### 6. Aplicar as mudanças

```bash
sudo systemctl daemon-reload
sudo systemctl restart avahi-daemon
```
Recarrega as definições e reinicia o Avahi.


## Validação

### No próprio TV Box

```bash
avahi-resolve --name tvbox.local
```
Pergunta ao Avahi local qual IP corresponde a `tvbox.local`. Deve retornar o IP atual da interface de rede.

```bash
hostname -I
```
Mostra o(s) IP(s) reais atribuídos às interfaces de rede. Deve corresponder ao resultado do comando anterior.

### A partir de outro dispositivo na rede

De outro computador na mesma rede:
```bash
ping tvbox.local
```