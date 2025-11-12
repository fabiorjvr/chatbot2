# Chatbot WhatsApp com IA - Análise de Vendas

Este projeto implementa um chatbot para WhatsApp capaz de realizar análises de dados de vendas de uma loja de celulares, respondendo a perguntas em linguagem natural. O bot se conecta a um banco de dados PostgreSQL, utiliza um modelo de linguagem de ponta para interpretar as perguntas e retorna respostas formatadas e claras diretamente no chat.

## Funcionalidades

O chatbot pode responder a uma variedade de perguntas sobre o desempenho de vendas, incluindo:

- **Produtos mais vendidos:** Quais são os produtos com maior receita?
- **Receita mensal:** Qual foi a receita total em um determinado mês e ano?
- **Vendas por produto:** Quantas unidades de um produto específico foram vendidas?
- **Comparativo por fabricante:** Qual fabricante vendeu mais?
- **Média de vendas:** Qual a média de receita e unidades vendidas por mês?
- **Melhor mês de vendas:** Qual foi o mês com maior faturamento?
- **Produtos menos vendidos:** Quais são os produtos com menor receita?
- **Comparativo de múltiplos produtos:** Compare as vendas de vários produtos.

## Arquitetura e Tecnologias

O projeto foi construído com uma arquitetura modular e utiliza as seguintes tecnologias:

- **Linguagem de Programação:** Python
- **Conexão com WhatsApp:** WPPConnect (Node.js)
- **Inteligência Artificial:**
    - **Modelo:** Llama 3.1 (llama-3.1-8b-instant)
    - **API:** Groq
- **Banco de Dados:** PostgreSQL
- **Gerenciamento de Ambiente:** `python-dotenv` para carregar variáveis de ambiente a partir de um arquivo `.env`.

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
.
├── .gitignore
├── API.txt
├── README.md
├── ai_agent.py
├── ai_agent_whatsapp.py
├── requirements.txt
├── tools.py
└── wppconnect_qrcode.js
```

- **`wppconnect_qrcode.js`**: Script Node.js responsável pela conexão com o WhatsApp. Ele gera um QR Code para autenticação e atua como a ponte entre o WhatsApp e o bot.
- **`ai_agent_whatsapp.py`**: O coração do bot. Este script recebe as mensagens do WhatsApp, as processa e envia para o agente de IA.
- **`ai_agent.py`**: Contém a lógica do agente de IA. Ele utiliza a API da Groq para se comunicar com o modelo Llama 3.1, seleciona a ferramenta de análise de dados apropriada e retorna a resposta.
- **`tools.py`**: Um conjunto de funções (ferramentas) que realizam consultas específicas no banco de dados para obter os dados de vendas.
- **`requirements.txt`**: Lista de todas as dependências Python necessárias para o projeto.
- **`API.txt`**: Arquivo de texto contendo as chaves de API e credenciais do banco de dados (este arquivo não deve ser versionado em um repositório público).
- **`README.md`**: Este arquivo.

## Configuração e Instalação

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

### Pré-requisitos

- [Node.js](https://nodejs.org/) (versão 16 ou superior)
- [Python](https://www.python.org/) (versão 3.9 ou superior)
- Um banco de dados PostgreSQL populado com os dados de vendas.

### 1. Clone o Repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd chatbot-whatsapp-ia
```

### 2. Instale as Dependências

**Dependências Node.js:**

```bash
npm install
```

**Dependências Python:**

```bash
pip install -r requirements.txt
```

### 3. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto e adicione as seguintes variáveis:

```
GROQ_API_KEY="sua_chave_de_api_da_groq"
DATABASE_URL="postgresql://usuario:senha@host:porta/nome_do_banco"
```

- **`GROQ_API_KEY`**: Sua chave de API da [Groq](https://groq.com/).
- **`DATABASE_URL`**: A URL de conexão com o seu banco de dados PostgreSQL.

### 4. Execute o Bot

**Passo 1: Inicie a conexão com o WhatsApp**

Em um terminal, execute o seguinte comando:

```bash
node wppconnect_qrcode.js
```

Um QR Code será exibido no terminal. Escaneie-o com o aplicativo do WhatsApp no celular associado ao número **+55 11 91502-2668**.

**Passo 2: Inicie o agente de IA**

Em outro terminal, execute o script principal do bot:

```bash
python ai_agent_whatsapp.py
```

O bot estará pronto para receber mensagens e responder às suas perguntas.

## Modelo de IA

O bot utiliza o modelo de linguagem **Llama 3.1 (llama-3.1-8b-instant)**, acessado através da API da **Groq**. Este modelo foi escolhido por sua alta velocidade e capacidade de processar linguagem natural com precisão, permitindo que o bot entenda as perguntas dos usuários e selecione a ferramenta de análise de dados correta para gerar a resposta.

## Desenvolvido por

Fábio Rosestolato Ferreira