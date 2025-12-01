# 🤖 Bot de Vagas: Telegram + Indeed Scraper

Este projeto é uma automação inteligente que monitora vagas de emprego no site **Indeed** e envia alertas instantâneos para um grupo ou tópico específico no **Telegram**.

O sistema utiliza **Selenium** para navegação e raspagem de dados (incluindo salário e localização) e a API oficial do Telegram para o envio das notificações.

## 📋 Pré-requisitos

Antes de configurar o projeto em uma nova máquina (Windows), certifique-se de ter instalado:

1.  **Python 3.8+**: [Baixar Python](https://www.python.org/downloads/) (Marque a opção *"Add Python to PATH"* na instalação).
2.  **Google Chrome**: O navegador deve estar instalado para o Selenium funcionar.
3.  **Git**: (Opcional) Para clonar o repositório.

## 🚀 Instalação e Configuração (Passo a Passo)

Abra o **PowerShell** na pasta do projeto e siga as instruções abaixo.

### 1. Criar e Ativar Ambiente Virtual
Recomendado para isolar as dependências do projeto.

```powershell
# Cria a pasta .venv (Execute apenas na primeira vez)
python -m venv .venv

# Ativa o ambiente virtual
.\.venv\Scripts\Activate.ps1
```

### 2. 📦 Instalar Dependências

Este passo é fundamental. Ele instalará o selenium, beautifulsoup4 e a biblioteca do telegram.

```
pip install -r requirements.txt
```

### 3. ⚙️ Configurando as Credenciais

Crie um arquivo chamado config.py na raiz do projeto (caso não exista). Este arquivo contém dados sensíveis e não deve ser compartilhado.

Conteúdo do ```config.py```:

```# config.py

# Token fornecido pelo @BotFather
BOT_TOKEN = "SEU_TOKEN_DO_TELEGRAM_AQUI"

# ID do Grupo (Geralmente começa com -100)
CHAT_ID = -100123456789

# ID do Tópico (message_thread_id). Use None se for um chat simples.
TOPIC_ID = 2
```

## ▶️ Como Executar

**🧪 Modo de Teste (Apenas Scraper)**

Use este comando para verificar se o robô está conseguindo "ler" o Indeed corretamente (título, empresa, local e salário) sem enviar nada para o Telegram.

```
python scraping.py
```

**🤖 Modo Bot (Produção)**

Inicia o bot. Ele fará uma varredura imediatamente e depois repetirá o processo automaticamente a cada 1 hora.

```
python bot.py
```

### 📂 Estrutura do Projeto

- bot.py: O "cérebro" da operação. Gerencia o agendamento e o envio de mensagens.
- scraping.py: O "braço operário". Abre o Chrome invisível e coleta os dados.
- config.py: Arquivo de configuração (Senhas/Tokens).
- jks_enviados.txt: "Memória" do bot. Guarda os IDs das vagas já enviadas para evitar duplicidade.
- requirements.txt: Lista de bibliotecas necessárias.

### 🛠️ Solução de Problemas Comuns

**1. O Bot roda, mas não envia mensagem no Telegram**

Provavelmente é uma configuração de privacidade.

- Vá no @BotFather no Telegram.
- Digite /mybots > Selecione seu Bot > Bot Settings.
- Vá em Group Privacy e clique em Turn off.
- Remova o bot do grupo e adicione novamente.

**2. Erro de "ChromeDriver" ou Navegador**

O Selenium precisa que o Driver seja compatível com seu Chrome.

- Se der erro, tente atualizar o Selenium: ```pip install --upgrade selenium```

**3. Vagas repetidas**

Se quiser que o bot reenvie todas as vagas (como se fosse a primeira vez), apague o arquivo ```jks_enviados.txt.```

---

Developed with 💙 using Python.