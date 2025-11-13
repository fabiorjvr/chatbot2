# Regras Operacionais do Agente de IA - Assistente de Vendas

## 1. Mandato Principal

Meu objetivo principal é atuar como um assistente de vendas de celulares, operando via WhatsApp. Devo interpretar as perguntas dos usuários, utilizar as ferramentas e os bancos de dados à minha disposição para fornecer respostas precisas, contextuais e bem formatadas, simulando um vendedor especialista.

## 2. Arquitetura e Tecnologias

- **Linguagem Principal:** Python
- **Servidor Web:** Flask (`app.py`) para intermediar a comunicação.
- **Conexão WhatsApp:** WPPConnect-JS (`wppconnect_qrcode.js`) rodando em Node.js.
- **Modelo de IA:** Groq com `llama-3.1-70b-versatile`.
- **Banco de Dados Relacional:** PostgreSQL para dados estruturados (produtos, vendas, especificações).
- **Banco de Dados Vetorial:** ChromaDB para dados não estruturados (manuais, descrições, etc.), suportando o fluxo RAG.
- **Gerenciamento de Ambiente:** Arquivo `.env` para chaves de API e URLs de banco de dados.

## 3. Fluxo de Comunicação

1.  O usuário envia uma mensagem no WhatsApp.
2.  O script `wppconnect_qrcode.js` (Node.js) captura a mensagem.
3.  `wppconnect_qrcode.js` envia a mensagem via requisição HTTP POST para o endpoint `/webhook` do servidor Flask (`app.py`).
4.  O `app.py` recebe a requisição e chama o método `process_message` da classe `AIAgent` (definida em `ai_agent.py`).
5.  O `AIAgent` processa a mensagem, decide o fluxo a ser seguido (uso de ferramentas, RAG ou resposta direta) e gera uma resposta.
6.  O `app.py` retorna a resposta gerada para o `wppconnect_qrcode.js`.
7.  O `wppconnect_qrcode.js` envia a resposta final de volta para o usuário no WhatsApp.

## 4. Motor de Raciocínio e Decisão (`ai_agent.py`)

Ao receber uma mensagem, sigo uma hierarquia de processamento:

- **Análise de Intenção:** Utilizo o modelo `llama-3.1-70b-versatile` para analisar a pergunta e determinar a intenção do usuário.
- **Seleção de Ferramenta (Fluxo de Vendas/Finanças):** Se a pergunta for sobre dados estruturados (ex: "qual o mais vendido?", "preço do iPhone 15"), minha primeira prioridade é selecionar a ferramenta apropriada definida em `tools.py` para consultar o PostgreSQL.
- **Fallback para RAG (Fluxo Técnico/Subjetivo):** Se o modelo de IA não conseguir selecionar uma ferramenta (porque a pergunta é subjetiva, como "qual tem a melhor câmera?" ou muito genérica), o sistema deve acionar o **fallback para o fluxo RAG**. Nesse caso, a pergunta é usada para buscar documentos relevantes no ChromaDB (`vector_store.py`) e a resposta é gerada com base nesses documentos.
- **Formatação da Resposta:** Todas as saídas, sejam de ferramentas ou do RAG, devem ser processadas para criar uma resposta em linguagem natural, bem formatada e amigável, antes de serem enviadas ao usuário.

## 5. Conjunto de Ferramentas (`tools.py`)

Para interagir com o banco de dados PostgreSQL, devo usar exclusivamente o conjunto de funções (ferramentas) definido em `tools.py`. Cada ferramenta é projetada para uma consulta específica e otimizada.

- `get_db_connection`: Estabelece a conexão com o banco de dados.
- `get_top_products`: Busca os produtos mais vendidos.
- `get_monthly_revenue`: Calcula a receita total para um mês/ano.
- `get_product_sales`: Busca dados de vendas para um produto específico.
- `get_comparison_by_manufacturer`: Compara vendas por fabricante.
- E outras ferramentas conforme definidas no arquivo.

**Regra Crítica:** Nunca devo construir consultas SQL dinamicamente. Devo sempre usar as ferramentas predefinidas.

## 6. Gerenciamento de Arquivos e Limpeza

- **Backup:** Arquivos de texto com logs, anotações ou dados brutos úteis devem ser movidos para a pasta `backup_info`.
- **Redundância:** Arquivos de teste (`teste_*.py`), backups (`*_backup.py`) e versões antigas de scripts devem ser removidos para manter o projeto limpo.
- **Documentação:** O `README.md` deve ser mantido atualizado com a arquitetura, tecnologias e instruções de execução. Este arquivo (`project_rules.md`) serve como meu guia de operações interno.

## 7. Procedimento de Execução

Para colocar o sistema em operação, devo seguir os seguintes passos:

1.  **Verificar Ambiente:** Garantir que todas as dependências (`requirements.txt` e `package.json`) estão instaladas e que o arquivo `.env` está configurado corretamente.
2.  **Iniciar Servidor Flask:** Em um terminal, executar `python app.py`.
3.  **Iniciar Conector WhatsApp:** Em um segundo terminal, executar `node wppconnect_qrcode.js`.
4.  **Autenticação:** Escanear o QR code gerado pelo `wppconnect_qrcode.js` com o app do WhatsApp.
5.  **Monitoramento:** Acompanhar os logs de ambos os terminais para garantir que a comunicação está fluindo corretamente.

## 8. Commits e Versionamento (Git)

Ao receber uma solicitação para salvar o progresso:

1.  **Adicionar Arquivos:** Usar `git add .` para adicionar todas as novas modificações.
2.  **Criar Commit:** Usar `git commit -m "Mensagem descritiva"` para criar um commit com uma mensagem clara sobre as alterações realizadas.
3.  **Enviar para o Repositório:** Usar `git push` para enviar as alterações para o repositório remoto no GitHub.