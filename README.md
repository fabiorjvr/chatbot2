# Assistente de Vendas de Celulares para WhatsApp

## 📖 Descrição

Este projeto consiste em um chatbot avançado para WhatsApp, projetado para atuar como um assistente de vendas especializado em smartphones. O agente de IA é capaz de entender e processar uma variedade de perguntas dos usuários, desde consultas técnicas sobre especificações de produtos até comparações entre modelos e perguntas relacionadas a vendas e finanças.

O sistema utiliza uma arquitetura robusta que combina bancos de dados relacionais e vetoriais, um poderoso modelo de linguagem e uma integração direta com o WhatsApp para oferecer respostas rápidas, precisas e contextualmente relevantes.

## 🛠️ Arquitetura e Tecnologias

O projeto é construído sobre uma pilha de tecnologias modernas para garantir eficiência, escalabilidade e inteligência.

- **Linguagem de Backend:** Python
- **Servidor Web:** Flask
- **Banco de Dados Relacional:** PostgreSQL
- **Banco de Dados Vetorial:** ChromaDB
- **Modelo de Linguagem (LLM):** Groq com `llama-3.1-70b-versatile`
- **Conexão WhatsApp:** WPPConnect-JS
- **Gerenciamento de Ambiente:** Node.js (para o conector do WhatsApp)

## 🗂️ Estrutura de Arquivos e Pastas Essenciais

Abaixo estão os arquivos e diretórios mais importantes para o funcionamento do sistema:

- `ai_agent.py`: O cérebro do projeto. Contém a classe `AIAgent`, responsável por processar as mensagens, orquestrar a chamada de ferramentas e rotear as perguntas para o fluxo de processamento correto (técnico, vendas, RAG, etc.).
- `tools.py`: Define o conjunto de ferramentas que o agente pode utilizar para interagir com o banco de dados PostgreSQL. Cada ferramenta corresponde a uma consulta SQL específica (ex: `get_top_products`, `get_product_sales`).
- `app.py`: Um servidor web minimalista criado com Flask. Ele expõe um endpoint `/webhook` que recebe as mensagens do WhatsApp (encaminhadas pelo `wppconnect_qrcode.js`), as passa para o `AIAgent` e retorna a resposta.
- `wppconnect_qrcode.js`: Script Node.js que utiliza a biblioteca `@wppconnect-team/wppconnect` para conectar-se ao WhatsApp. Ele gera o QR code para autenticação, escuta as mensagens recebidas e as envia para o webhook do `app.py`.
- `rag/vector_store.py`: Gerencia o banco de dados vetorial ChromaDB. É responsável por criar, carregar e realizar buscas de similaridade nos documentos de texto, sendo a base para o fluxo de RAG (Retrieval-Augmented Generation).
- `data/chroma_db/`: Diretório onde o ChromaDB armazena seus dados de forma persistente.
- `setup_database.py`: Script de inicialização para o PostgreSQL. Ele cria as tabelas necessárias (`smartphones`, `sales`, etc.) e as popula com os dados iniciais.
- `setup_chromadb.py`: Script de inicialização para o ChromaDB. Ele lê os arquivos de texto (como manuais de vendas) e os insere no banco de dados vetorial.
- `.env`: Arquivo de configuração para armazenar variáveis de ambiente sensíveis, como a chave da API da Groq e a URL de conexão com o banco de dados PostgreSQL.
- `README.md`: Este arquivo de documentação.

## 🗄️ Bancos de Dados Utilizados

- **PostgreSQL**: Armazena todos os dados estruturados do projeto. Isso inclui as especificações técnicas detalhadas de cada smartphone (processador, tela, bateria, etc.), informações de estoque, preços e todos os registros de vendas. O `AIAgent` acessa esses dados através das funções definidas em `tools.py`.
- **ChromaDB**: Funciona como a base de conhecimento para perguntas abertas, subjetivas ou que não podem ser respondidas apenas com dados estruturados. Ele armazena informações não estruturadas (documentos de texto) em formato de vetores, permitindo que o agente realize buscas por similaridade semântica para encontrar os contextos mais relevantes e gerar respostas ricas (fluxo RAG).

## 🧠 Modelo de Linguagem

Utilizamos o modelo `llama-3.1-70b-versatile` disponibilizado através da plataforma da **Groq**. A escolha se deu pela sua alta capacidade de processamento de linguagem natural, excelente habilidade para seguir instruções e utilizar ferramentas (tool-use), e, principalmente, pela sua incrível velocidade de inferência, o que é crucial para uma experiência de conversação fluida em tempo real no WhatsApp.

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento.

1.  **Configurar o Ambiente de Desenvolvimento:**
    - Crie e ative um ambiente virtual Python:
      ```bash
      python -m venv .venv
      # No Windows
      .\.venv\Scripts\activate
      # No Linux/macOS
      source .venv/bin/activate
      ```
    - Instale as dependências Python:
      ```bash
      pip install -r requirements.txt
      ```
    - Instale as dependências Node.js:
      ```bash
      npm install
      ```

2.  **Configurar Variáveis de Ambiente:**
    - Crie um arquivo chamado `.env` na raiz do projeto.
    - Adicione as seguintes variáveis, substituindo pelos seus valores:
      ```
      GROQ_API_KEY="SUA_CHAVE_API_GROQ"
      DATABASE_URL="postgresql://usuario:senha@host:porta/nome_do_banco"
      ```

3.  **Inicializar os Bancos de Dados:**
    - Execute o script para configurar e popular o PostgreSQL:
      ```bash
      python setup_database.py
      ```
    - Execute o script para configurar e popular o ChromaDB:
      ```bash
      python setup_chromadb.py
      ```

4.  **Iniciar os Serviços:**
    - Em um terminal, inicie o servidor Flask que hospeda o agente:
      ```bash
      python app.py
      ```
    - Em um segundo terminal, inicie o conector do WhatsApp:
      ```bash
      node wppconnect_qrcode.js
      ```

5.  **Conectar ao WhatsApp:**
    - O terminal executando `node wppconnect_qrcode.js` exibirá um QR code.
    - Abra o WhatsApp em seu celular, vá em **Configurações > Aparelhos conectados > Conectar um aparelho** e escaneie o QR code.
    - Aguarde a mensagem de "CONECTADO COM SUCESSO!" no terminal.

A partir deste momento, o chatbot estará ativo e pronto para receber mensagens no número de WhatsApp conectado.

---

### Desenvolvido por Fábio Rosestolato Ferreira
 
---
 
## Atualizações e Melhorias – 14/11/2025
 
- Correção crítica no `wppconnect_qrcode.js` (removidos escapes inválidos `=\u003e` e `\u0026\u0026`).
- Logs aprimorados para grupos, menções e fluxo de mensagens no conector WhatsApp.
- Ajuste no `/health` do Flask para status consistente e métricas funcionais.
- Integração e validação ponta a ponta: mensagens e respostas visíveis nos terminais.
- Guardrails técnicos no `ai_agent.py`: respostas realistas, moderadas e baseadas em dados.
- Preparação para RAG técnico com documentos base (NFC, Dual SIM/eSIM, câmeras) nos principais modelos.
- Suporte a execução contínua com PM2 (`wpp` e `flask`) e reinício automático.
- Caminho de envio de imagens ajustado no conector para compatibilidade com arquivos locais.