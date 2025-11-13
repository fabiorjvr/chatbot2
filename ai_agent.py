# -*- coding: utf-8 -*-
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
import os
import json
from tools import DatabaseTools
from rag.vector_store import VectorStoreManager
import sys
import inspect
import re

class AIAgent:
    """
    Agente de IA profissional que SEMPRE usa dados do banco antes de responder.
    """

    def __init__(self):
        self.db_tools = DatabaseTools()
        self.vector_store = VectorStoreManager()
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("A chave da API Groq não foi encontrada. Verifique o arquivo .env e a variável GROQ_API_KEY.")
        
        self.client = Groq(api_key=groq_api_key)
        
        # MUDANÇA CRÍTICA 1: Usar modelo 70B em vez de 8B
        self.model_name = "llama-3.3-70b-versatile"  # Modelo MUITO melhor e ainda gratuito
        
        self.tools = self._get_tools_definitions()
        self.system_prompt = self._build_system_prompt()
        
        # Lista de modelos válidos (cache)
        self.modelos_validos = [
            "iPhone 15 Pro Max",
            "Motorola Moto G54",
            "Samsung Galaxy A54",
            "Samsung Galaxy S24 Ultra",
            "Xiaomi 13T",
            "Xiaomi Redmi Note 13"
        ]

    def _get_tools_definitions(self) -> list:
        """
        Gera as definições das ferramentas de forma SIMPLIFICADA.
        MUDANÇA CRÍTICA 2: Reduzir número de ferramentas para evitar confusão do modelo.
        """
        tool_definitions = []
        
        # APENAS as ferramentas ESSENCIAIS
        ferramentas_essenciais = [
            'get_smartphone_details_and_photos',
            'get_top_sold_products',
            'get_monthly_revenue',
            'get_product_sales'
        ]
        
        for name, func in inspect.getmembers(self.db_tools, inspect.isfunction):
            if name.startswith("_") or name not in ferramentas_essenciais:
                continue

            docstring = inspect.getdoc(func)
            if not docstring:
                continue

            # Extrair descrição
            description_match = re.match(r"^(.*?)\n", docstring, re.DOTALL)
            description = description_match.group(1).strip() if description_match else "Sem descrição."
            
            # MUDANÇA CRÍTICA 3: Descrições ULTRA específicas
            if name == "get_smartphone_details_and_photos":
                description = """
FERRAMENTA OBRIGATÓRIA para QUALQUER pergunta sobre especificações técnicas de smartphones.
Use esta ferramenta quando o usuário perguntar sobre:
- Processador, RAM, memória, armazenamento
- Câmera, bateria, tela, display
- Preço, valor, custo
- Características, especificações, detalhes técnicos
- Comparação entre dois modelos específicos
Exemplos de perguntas que EXIGEM esta ferramenta:
- "Qual o processador do Xiaomi 13T?"
- "Quanto custa o iPhone 15 Pro Max?"
- "Qual a diferença entre Samsung A54 e Xiaomi 13T?"
"""
            elif name == "get_top_sold_products":
                description = "Retorna os produtos MAIS VENDIDOS. Use quando perguntarem sobre 'mais vendido', 'campeão de vendas', 'líder', 'top vendas'."
            elif name == "get_monthly_revenue":
                description = "Retorna o FATURAMENTO TOTAL de um mês/ano. Use quando perguntarem sobre 'receita', 'faturamento', 'quanto vendeu em dinheiro'."
            elif name == "get_product_sales":
                description = "Retorna as VENDAS de UM produto específico. Use quando perguntarem 'quantos [modelo] foram vendidos?', 'vendas do [modelo]'."

            param_docs = dict(re.findall(r"-\s+([a-zA-Z_]+)\s+\([^)]+\):\s+(.*)", docstring))
            sig = inspect.signature(func)
            parameters = sig.parameters
            
            tool_params = {
                "type": "object",
                "properties": {},
                "required": [],
            }

            for param_name, param in parameters.items():
                if param_name == 'self':
                    continue
                
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"

                tool_params["properties"][param_name] = {
                    "type": param_type,
                    "description": param_docs.get(param_name, ""),
                }

                if param.default is inspect.Parameter.empty:
                    tool_params["required"].append(param_name)
            
            tool_definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": tool_params,
                },
            })
            
        return tool_definitions

    def _build_system_prompt(self) -> str:
        """
        MUDANÇA CRÍTICA 4: System prompt CURTO, DIRETO e IMPERATIVO.
        """
        return f'''Você é Fabio, especialista em vendas de smartphones.

DATA ATUAL: 12 de Novembro de 2025.

MODELOS DISPONÍVEIS EM ESTOQUE (MEMORIZE):
1. iPhone 15 Pro Max (Apple)
2. Motorola Moto G54 (Motorola)
3. Samsung Galaxy A54 (Samsung)
4. Samsung Galaxy S24 Ultra (Samsung)
5. Xiaomi 13T (Xiaomi)
6. Xiaomi Redmi Note 13 (Xiaomi)

REGRA ABSOLUTA DE OURO (NUNCA QUEBRE):

Se a pergunta menciona QUALQUER informação técnica (processador, RAM, câmera, bateria, preço, especificações), você DEVE:
1. Chamar get_smartphone_details_and_photos com o nome EXATO do modelo
2. ESPERAR o resultado da ferramenta
3. Responder APENAS com os dados retornados

NUNCA invente dados técnicos. Se você não chamou a ferramenta, você NÃO SABE a resposta.

EXEMPLOS OBRIGATÓRIOS:

❌ ERRADO:
User: "Qual o processador do Xiaomi 13T?"
Você: "O Xiaomi 13T tem processador MediaTek Dimensity 8200..."

✅ CORRETO:
User: "Qual o processador do Xiaomi 13T?"
Você: [CHAMA get_smartphone_details_and_photos(modelo="Xiaomi 13T")]
[ESPERA resultado]
Você: "Segundo nossos dados, o Xiaomi 13T possui [dado real do banco]"

NORMALIZAÇÃO DE NOMES:
- "Redmi Note 13" = "Xiaomi Redmi Note 13"
- "Galaxy A54" = "Samsung Galaxy A54"
- "iPhone 15 Pro Max" = "iPhone 15 Pro Max"
- "S24 Ultra" = "Samsung Galaxy S24 Ultra"
- "Moto G54" = "Motorola Moto G54"

Se o usuário perguntar sobre um modelo que NÃO está na lista, ofereça uma alternativa da mesma marca ou similar.

Seja amigável, mas SEMPRE baseie suas respostas em DADOS REAIS das ferramentas.'''

    def _format_response(self, tool_name: str, data: list) -> str:
        """Formata os dados em resposta amigável."""
        if not data or (isinstance(data, list) and len(data) > 0 and "erro" in data[0]):
            erro_msg = data[0].get('erro', 'Dados não encontrados') if data else 'Dados não encontrados'
            return f"❌ {erro_msg}"

        try:
            if tool_name == "get_smartphone_details_and_photos":
                if not data:
                    return "❌ Não encontrei detalhes para o modelo solicitado."
                
                p = data[0]
                resposta = f"📱 *{p.get('modelo', 'Modelo')}* ({p.get('fabricante', 'Fabricante')})\n\n"
                
                specs = p.get('especificacoes_tecnicas', {})
                if specs:
                    resposta += "*Especificações Técnicas:*\n"
                    if 'processador' in specs:
                        resposta += f"🔧 Processador: {specs['processador']}\n"
                    if 'ram' in specs:
                        resposta += f"💾 RAM: {specs['ram']}\n"
                    if 'armazenamento' in specs:
                        resposta += f"💿 Armazenamento: {specs['armazenamento']}\n"
                    if 'camera_principal' in specs:
                        resposta += f"📸 Câmera: {specs['camera_principal']}\n"
                    if 'bateria' in specs:
                        resposta += f"🔋 Bateria: {specs['bateria']}\n"
                    if 'tela' in specs:
                        resposta += f"📺 Tela: {specs['tela']}\n"
                    resposta += "\n"
                
                info_geral = p.get('info_geral', {})
                if info_geral and 'preco' in info_geral:
                    resposta += f"💰 *Preço: R$ {info_geral['preco']}*\n\n"
                
                pontos_fortes = p.get('pontos_fortes', [])
                if pontos_fortes:
                    resposta += "*✅ Pontos Fortes:*\n"
                    for ponto in pontos_fortes[:3]:
                        resposta += f"  • {ponto}\n"
                    resposta += "\n"
                
                fotos = p.get('fotos', [])
                if fotos:
                    resposta += "*📸 Fotos:*\n"
                    for foto in fotos[:2]:
                        resposta += f"{foto}\n"
                
                return resposta

            elif tool_name == "get_top_sold_products":
                if len(data) == 1:
                    p = data[0]
                    return f"🏆 *Produto Mais Vendido:*\n\n📱 {p['modelo']} ({p['fabricante']})\n📦 {p['unidades_vendidas']:,} unidades\n💰 R$ {p['receita_total']:,.2f}"
                else:
                    lines = ["🏆 *Top Produtos Mais Vendidos:*\n"]
                    for i, p in enumerate(data[:5], 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º"
                        lines.append(f"{emoji} *{p['modelo']}* ({p['fabricante']})")
                        lines.append(f"   📦 {p['unidades_vendidas']:,} unidades | 💰 R$ {p['receita_total']:,.2f}\n")
                    return "\n".join(lines)

            elif tool_name == "get_monthly_revenue":
                d = data[0]
                return f"💰 *Receita do Período:*\n\n💵 Total: R$ {d['receita_total']:,.2f}\n📦 Unidades: {d['total_unidades']:,}"

            elif tool_name == "get_product_sales":
                if data:
                    p = data[0]
                    return f"📊 *Vendas de {p.get('modelo', 'Produto')}: {p.get('unidades_vendidas', 0)} unidades, gerando R$ {p.get('receita', 0):,.2f}."
            
            return f"Resultado de {tool_name}: {json.dumps(data, indent=2, ensure_ascii=False)}"

        except Exception as e:
            return f"🐞 Erro ao formatar resposta: {e}"

    def _normalize_model_name(self, text: str) -> str:
        """Normaliza o nome de um modelo de smartphone a partir de um texto."""
        text_lower = text.lower()
        
        # Mapeamento de apelidos para nomes completos
        model_map = {
            "redmi note 13": "Xiaomi Redmi Note 13",
            "galaxy a54": "Samsung Galaxy A54",
            "iphone 15 pro max": "iPhone 15 Pro Max",
            "s24 ultra": "Samsung Galaxy S24 Ultra",
            "moto g54": "Motorola Moto G54",
            "xiaomi 13t": "Xiaomi 13T"
        }

        for alias, full_name in model_map.items():
            if alias in text_lower:
                return full_name
        
        # Se não encontrar um apelido, tenta encontrar o nome completo
        for model in self.modelos_validos:
            if model.lower() in text_lower:
                return model
                
        return None

    def _find_mentioned_models(self, text: str) -> list:
        """Encontra todos os modelos de smartphones válidos mencionados em um texto."""
        mentioned = set()
        text_lower = text.lower()
        
        # Mapeamento de apelidos para nomes completos
        model_map = {
            "redmi note 13": "Xiaomi Redmi Note 13",
            "galaxy a54": "Samsung Galaxy A54",
            "iphone 15 pro max": "iPhone 15 Pro Max",
            "s24 ultra": "Samsung Galaxy S24 Ultra",
            "moto g54": "Motorola Moto G54",
            "xiaomi 13t": "Xiaomi 13T"
        }

        # Verifica apelidos primeiro
        for alias, full_name in model_map.items():
            if alias in text_lower:
                mentioned.add(full_name)
        
        # Verifica nomes completos (para garantir que não perca nada)
        for model in self.modelos_validos:
            if model.lower() in text_lower:
                mentioned.add(model)
                
        return list(mentioned)

    def process_message(self, user_message: str) -> str:
        """
        MUDANÇA CRÍTICA 5: Lógica de roteamento DETERMINÍSTICA.
        A IA só é usada quando estritamente necessário.
        """
        user_message_lower = user_message.lower()
        
        # Palavras-chave que indicam uma pergunta técnica
        palavras_tecnicas = [
            'processador', 'ram', 'memória', 'armazenamento', 'câmera', 'bateria', 
            'tela', 'display', 'preço', 'valor', 'custo', 'característica', 
            'especificação', 'detalhe', 'ficha técnica', 'comparar', 'vs', 'x', 
            'diferença', 'melhor', 'pior'
        ]
        
        pergunta_tecnica = any(palavra in user_message_lower for palavra in palavras_tecnicas)
        modelos_mencionados = self._find_mentioned_models(user_message)

        # FLUXO 1: Pergunta técnica com modelo(s) claro(s)
        if pergunta_tecnica and modelos_mencionados:
            # FLUXO 1.1: Comparação entre DOIS ou mais modelos
            if len(modelos_mencionados) >= 2:
                print(f"🔍 FLUXO DETERMINÍSTICO: Comparação entre {', '.join(modelos_mencionados)}", file=sys.stderr)
                
                dados_completos = []
                for modelo in modelos_mencionados:
                    dados = self.db_tools.get_smartphone_details_and_photos(modelo)
                    if dados:
                        # Formata os dados brutos para um texto mais limpo
                        texto_formatado = self._format_response('get_smartphone_details_and_photos', dados)
                        dados_completos.append(texto_formatado)
                
                if not dados_completos:
                    return "😕 Não consegui encontrar dados para os modelos solicitados. Pode tentar outros?"

                dados_formatados = '\n---\n'.join(dados_completos)
                prompt_comparacao = f"""O usuário pediu para comparar: "{user_message}"

Dados dos produtos:

---
{dados_formatados}
---

Sua tarefa: Crie uma tabela comparativa em markdown ou uma lista clara comparando os pontos principais (câmera, processador, preço, etc.) dos produtos. Seja objetivo e use apenas os dados fornecidos."""

                comparacao = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Você é um especialista que cria comparações claras de produtos."},
                        {"role": "user", "content": prompt_comparacao}
                    ],
                    model=self.model_name,
                    temperature=0.1,
                    max_tokens=1024
                )
                return comparacao.choices[0].message.content

            # FLUXO 1.2: Pergunta sobre UM modelo
            else:
                modelo_mencionado = modelos_mencionados[0]
                print(f"✅ FLUXO DETERMINÍSTICO: Pergunta técnica sobre {modelo_mencionado}", file=sys.stderr)
                
                try:
                    # Executar ferramenta DIRETAMENTE
                    dados = self.db_tools.get_smartphone_details_and_photos(modelo_mencionado)
                    
                    if dados and len(dados) > 0:
                        resposta_formatada = self._format_response('get_smartphone_details_and_photos', dados)
                        
                        # Agora usar IA apenas para HUMANIZAR a resposta
                        prompt_humanizar = f"""O usuário perguntou: "{user_message}"

Dados reais do banco de dados:
{resposta_formatada}

Sua tarefa: Responda de forma AMIGÁVEL e CONVERSACIONAL usando APENAS os dados acima. Não invente nada. Seja breve (máximo 5 linhas)."""

                        humanizacao = self.client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": "Você é um vendedor amigável. Use APENAS os dados fornecidos."},
                                {"role": "user", "content": prompt_humanizar}
                            ],
                            model=self.model_name,
                            temperature=0.3,
                            max_tokens=300
                        )
                        
                        return humanizacao.choices[0].message.content
                    
                    else:
                        return f"😕 Desculpe, não encontrei dados sobre o {modelo_mencionado} em nosso sistema. Posso te ajudar com outro modelo?"
                        
                except Exception as e:
                    print(f"🐞 Erro no fluxo determinístico: {e}", file=sys.stderr)
                    return f"🐞 Ocorreu um erro ao buscar dados: {e}"
        
        # FLUXO 2: Pergunta técnica SEM modelo claro - Usar IA com tools
        elif pergunta_tecnica:
            print("⚠️ FLUXO IA COM TOOLS: Pergunta técnica sem modelo claro", file=sys.stderr)
            return self._process_with_tools(user_message)
        
        # FLUXO 3: Pergunta sobre vendas ou finanças
        elif any(palavra in user_message_lower for palavra in ['vendido', 'vendas', 'mais vendeu', 'campeão', 'líder', 'top', 'receita', 'faturamento', 'arrecadação']):
            print("📊 FLUXO VENDAS/FINANÇAS", file=sys.stderr)
            return self._process_with_tools(user_message)
        
        # FLUXO 4: Pergunta genérica/subjetiva - Usar RAG
        else:
            print("💬 FLUXO RAG: Pergunta genérica", file=sys.stderr)
            return self._process_with_rag(user_message)

    def _process_with_tools(self, user_message: str) -> str:
        """
        MUDANÇA CRÍTICA 4: Forçar o uso de RAG se a IA não escolher uma ferramenta.
        """
        print("🤖 Usando IA para escolher a melhor ferramenta...", file=sys.stderr)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                tools=self.tools,
                tool_choice="auto",
                temperature=0.1, # MUDANÇA CRÍTICA 2: Temperatura baixa para consistência
                max_tokens=1024
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                return self._execute_tool_calls(tool_calls)
            else:
                # MUDANÇA CRÍTICA 4: Fallback para RAG
                print("⚠️ IA não acionou ferramenta. Acionando RAG como fallback.", file=sys.stderr)
                return self._process_with_rag(user_message)

        except Exception as e:
            print(f"🐞 Erro ao processar com ferramentas: {e}", file=sys.stderr)
            return f"🐞 Desculpe, ocorreu um erro ao tentar usar minhas ferramentas: {e}"

    def _execute_tool_calls(self, tool_calls: list) -> str:
        """Executa as chamadas de ferramentas."""
        available_tools = {
            func_name: getattr(self.db_tools, func_name) 
            for func_name in dir(self.db_tools) 
            if callable(getattr(self.db_tools, func_name)) and not func_name.startswith("_")
        }
        
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                print(f"🔧 Executando: {function_name}({tool_call.function.arguments})", file=sys.stderr)
                
                if function_name not in available_tools:
                    return f"❌ Erro: Ferramenta '{function_name}' não encontrada."

                function_to_call = available_tools[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)

                return self._format_response(function_name, function_response)

            except Exception as e:
                print(f"🐞 Erro ao executar ferramenta: {e}", file=sys.stderr)
                return f"❌ Erro ao executar {function_name}: {e}"

    def _process_with_rag(self, user_message: str) -> str:
        """Processa usando RAG para perguntas subjetivas."""
        try:
            search_results = self.vector_store.search(user_message, n_results=2)
            context_docs = search_results.get('documents', [[]])[0]
            
            if not context_docs:
                # Sem contexto RAG, resposta genérica
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": f"Você é Fabio, vendedor de smartphones. Modelos disponíveis: {', '.join(self.modelos_validos)}. Seja breve e amigável."},
                        {"role": "user", "content": user_message}
                    ],
                    model=self.model_name,
                    temperature=0.7,
                    max_tokens=300
                )
                return response.choices[0].message.content
            
            context_str = "\n- ".join(context_docs)
            rag_prompt = f'''Contexto de documentos:
- {context_str}

Modelos disponíveis: {', '.join(self.modelos_validos)}

Pergunta: {user_message}

Responda de forma amigável e útil, mas se mencionar qualquer especificação técnica, deixe claro que são informações gerais e que você pode buscar dados precisos se o cliente quiser.'''

            final_response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você é um vendedor prestativo."},
                    {"role": "user", "content": rag_prompt}
                ],
                model=self.model_name,
                temperature=0.7,
                max_tokens=512
            )
            return final_response.choices[0].message.content

        except Exception as e:
            print(f"🐞 Erro no RAG: {e}", file=sys.stderr)
            return "Desculpe, tive um problema ao processar sua pergunta. Pode reformular?"


def main():
    try:
        if len(sys.argv) < 2:
            print("Erro: Pergunta não fornecida.", file=sys.stderr)
            sys.exit(1)

        question = sys.argv[1]
        agent = AIAgent()
        response = agent.process_message(question)
        print(response)

    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()