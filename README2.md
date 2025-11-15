# Assistente de Vendas de Celulares para WhatsApp com IA Híbrida (Gemini + Llama)

## 📖 Descrição

Este projeto consiste em um chatbot avançado para WhatsApp, projetado para atuar como um assistente de vendas especializado em smartphones. O agente de IA foi reestruturado para utilizar o **Gemini File Search** como sua principal base de conhecimento técnico, consultando um arquivo (`celularrag.pdf`) para obter especificações de produtos.

Para conversas gerais ou quando a informação não é encontrada, o sistema utiliza o modelo `llama-3.1-70b-versatile` da Groq como fallback, garantindo respostas rápidas, precisas e contextualmente relevantes em qualquer cenário.

## 🛠️ Arquitetura e Tecnologias

O projeto foi modernizado para uma arquitetura mais ágil e focada em APIs de IA de ponta.

- **Linguagem de Backend:** Python
- **Servidor Web:** Flask
- **Base de Conhecimento (RAG):** **Google Gemini File Search API**
- **Modelo de Linguagem Principal (RAG):** **Gemini 1.5 Flash**
- **Modelo de Linguagem Fallback:** Groq com `llama-3.1-70b-versatile`
- **Conexão WhatsApp:** WPPConnect-JS
- **Gerenciamento de Ambiente:** Node.js (para o conector do WhatsApp)

## 🗂️ Estrutura de Arquivos e Pastas Essenciais

Abaixo estão os arquivos e diretórios mais importantes para o funcionamento do sistema:

- `ai_agent.py`: O cérebro do projeto. Contém a classe `AIAgent`, responsável por processar as mensagens, orquestrar a chamada ao Gemini File Search e decidir quando usar o modelo de fallback da Groq.
- `rag/gemini_fs.py`: Gerencia toda a interação com a API do Gemini File Search. É responsável por criar o *File Store*, fazer o upload do arquivo `celularrag.pdf` e executar as buscas (queries) para responder às perguntas dos usuários.
- `app.py`: Servidor web minimalista com Flask. Expõe o endpoint `/webhook` que recebe as mensagens do WhatsApp (encaminhadas pelo `wppconnect_qrcode.js`), as passa para o `AIAgent` e retorna a resposta.
- `wppconnect_qrcode.js`: Script Node.js que utiliza a biblioteca `@wppconnect-team/wppconnect` para conectar-se ao WhatsApp. Ele gera o QR code, escuta as mensagens e as envia para o webhook do `app.py`.
- `celularrag.pdf`: O documento central da base de conhecimento. Contém todas as fichas técnicas e informações dos produtos que o assistente pode vender. Este arquivo é enviado para o Gemini File Search.
- `.env`: Arquivo de configuração para armazenar variáveis de ambiente, como as chaves de API do Gemini e da Groq.
- `README2.md`: Este arquivo de documentação.

## 🗄️ Base de Conhecimento (RAG com Gemini File Search)

O sistema abandonou os bancos de dados tradicionais (PostgreSQL e ChromaDB) em favor de uma arquitetura mais moderna e simplificada com o **Google Gemini File Search**.

- **Fonte de Dados Única:** Um único arquivo, `celularrag.pdf`, contém todas as informações técnicas dos produtos. Isso simplifica drasticamente a gestão e atualização dos dados.
- **Indexação Automática:** O script `rag/gemini_fs.py` faz o upload deste PDF para um *File Store* no Gemini, que automaticamente processa, indexa e otimiza o conteúdo para buscas semânticas.
- **Busca Inteligente (RAG):** Quando um usuário faz uma pergunta técnica (ex: "Qual a bateria do Galaxy S24?"), o `AIAgent` aciona o `GeminiFileSearchManager` para fazer uma query diretamente no conteúdo do PDF. O Gemini encontra os trechos mais relevantes e os utiliza para gerar uma resposta precisa, baseada exclusivamente nos dados do documento.

## 🧠 Modelo de Linguagem Híbrido

Utilizamos uma abordagem híbrida para garantir a melhor performance e versatilidade:

- **Gemini 1.5 Flash:** É o modelo principal, invocado através do File Search para todas as consultas técnicas que exigem busca de dados no `celularrag.pdf`. Sua integração nativa com o RAG garante respostas factuais e precisas.
- **Llama 3.1 70B (Groq):** Atua como um modelo de fallback para conversação geral. Se a pergunta do usuário for um cumprimento, uma dúvida não relacionada a produtos ou se o File Search não retornar uma resposta, o `AIAgent` utiliza o Llama 3.1 via Groq para gerar uma resposta rápida e fluida, mantendo a qualidade da interação.

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
    - Renomeie `.env.example` para `.env` ou crie um novo arquivo `.env`.
    - Adicione as seguintes variáveis, substituindo pelos seus valores:
      ```
      GROQ_API_KEY="SUA_CHAVE_API_GROQ"
      GEMINI_API_KEY="SUA_CHAVE_API_GEMINI"
      ```

3.  **Preparar a Base de Conhecimento:**
    - Garanta que o arquivo `celularrag.pdf` esteja presente na raiz do projeto. Este arquivo é a única fonte de dados para as especificações dos produtos.

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
    - Abra o WhatsApp em seu celular, vá em **Configurações \u003e Aparelhos conectados \u003e Conectar um aparelho** e escaneie o QR code.
    - Aguarde a mensagem de "CONECTADO COM SUCESSO!" no terminal.

A partir deste momento, o chatbot estará ativo. Na primeira execução, o `AIAgent` irá criar o *File Store* no Gemini e fazer o upload do `celularrag.pdf`, o que pode levar alguns instantes.

---

### Desenvolvido por Fábio Rosestolato Ferreira