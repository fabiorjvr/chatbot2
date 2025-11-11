# -*- coding: utf-8 -*- 
import google.generativeai as genai 
import os 
import json 
from tools import DatabaseTools 

class AIAgent: 
    """ 
    Agente de IA que interpreta perguntas e consulta o banco de dados. 
    """ 

    def __init__(self): 
        genai.configure(api_key=os.getenv("GEMINI_API_KEY")) 
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
        self.db_tools = DatabaseTools() 
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str: 
        return ''' 
Você é um assistente de vendas de smartphones. Analise a pergunta do usuário e retorne APENAS um JSON válido (sem formatação markdown) indicando qual ferramenta usar. 

**FERRAMENTAS DISPONÍVEIS:** 

1. `get_top_products(month: int, year: int, limit: int)` 
   - Retorna os N produtos MAIS vendidos de um mês/ano 
   - Use para: "qual celular vendeu mais", "top 3 produtos", "mais vendido" 
   - limit: 1 para "mais vendido", 3 para "top 3", 5 para "top 5" 

2. `get_monthly_revenue(month: int, year: int)` 
   - Retorna a RECEITA TOTAL de um mês/ano 
   - Use para: "qual foi a receita", "faturamento", "valor de vendas" 

3. `get_product_sales_by_month(month: int, year: int)` 
   - Retorna TODOS os produtos vendidos em um mês/ano 
   - Use para: \"quanto vendeu de cada aparelho\", \"vendas por produto\", \"lista de vendas\" 

4. `get_product_sales(produto: str, month: int, year: int)` 
   - Retorna vendas de UM produto específico 
   - Use para: "quanto vendeu o iPhone 15", "vendas do Galaxy S24" 

5. `get_comparison_by_manufacturer(month: int, year: int)` 
   - Retorna vendas por FABRICANTE (Apple, Samsung, etc) 
   - Use para: "comparar marcas", "qual marca vendeu mais" 

6. `get_average_monthly_sales(year: int)`
   - Retorna a MÉDIA de faturamento e unidades vendidas por mês em um ano.
   - Use para: "qual a média de vendas", "média mensal de faturamento"

7. `get_best_selling_month(year: int)`
   - Retorna o MÊS com MAIOR faturamento em um ano.
   - Use para: "qual mês vendeu mais", "melhor mês de vendas"

8. `get_least_sold_products(year: int, limit: int)`
   - Retorna os N produtos MENOS vendidos de um ano.
   - Use para: "qual celular vendeu menos", "piores produtos em vendas"
   - limit: 1 para "menos vendido", 3 para "top 3 piores", 5 para "top 5 piores"

9. `get_multiple_product_sales(products: list, year: int)`
   - Retorna as vendas de MÚLTIPLOS produtos em um ano.
   - Use para: "compare as vendas do iPhone 15 e Galaxy S24"

**REGRAS IMPORTANTES:** 
- Sempre extraia MÊS e ANO da pergunta 
- Se não mencionar ano, use 2024 
- Para "mais vendido" use limit=1 
- Para "top 3" use limit=3, "top 5" use limit=5 
- Meses: janeiro=1, fevereiro=2, ..., dezembro=12 
- Se a pergunta contiver "e" ou "vs" para comparar produtos, extraia todos os nomes e use a ferramenta `get_multiple_product_sales`.

**FORMATO DE RESPOSTA (apenas JSON, sem ```json):** 

Exemplo 1: 
Pergunta: "qual celular vendeu mais em junho de 2024?" 
Resposta: 
{ 
  "tool": "get_top_products", 
  "params": {"month": 6, "year": 2024, "limit": 1} 
} 

Exemplo 2: 
Pergunta: "qual foi valor de vendas de outubro de 2024?" 
Resposta: 
{ 
  "tool": "get_monthly_revenue", 
  "params": {"month": 10, "year": 2024} 
} 

Exemplo 3: 
Pergunta: \"quanto vendeu de cada aparelho em fevereiro de 2025?\" 
Resposta: 
{ 
  "tool": \"get_product_sales_by_month\", 
  "params": {\"month\": 2, \"year\": 2025} 
} 

Exemplo 4: 
Pergunta: "top 3 celulares que venderam mais em maio de 2025" 
Resposta: 
{ 
  "tool": "get_top_products", 
  "params": {"month": 5, "year": 2025, "limit": 3} 
} 

Exemplo 5: 
Pergunta: "quanto vendeu o iPhone 15 em março?" 
Resposta: 
{ 
  "tool": "get_product_sales", 
  "params": {"produto": "iPhone 15", "month": 3, "year": 2024} 
} 

Exemplo 6:
Pergunta: "compare as vendas do iPhone 15 Pro Max e do Samsung Galaxy S24 Ultra em 2024"
Resposta:
{
  "tool": "get_multiple_product_sales",
  "params": {"products": ["iPhone 15 Pro Max", "Samsung Galaxy S24 Ultra"], "year": 2024}
}
''' 

    def _format_response(self, tool_name: str, data: list) -> str: 
        """Formata os dados em resposta amigável.""" 
        if not data or ("erro" in data[0]):
            return f"❌ Não encontrei dados para essa consulta. Detalhe: {data[0].get('erro')}"

        try: 
            if tool_name == "get_top_products": 
                if len(data) == 1: 
                    p = data[0] 
                    return f"📱 O produto mais vendido foi:\n\n🏆 {p['modelo']} ({p['fabricante']})\n   {p['unidades_vendidas']:,} unidades vendidas\n   💰 R$ {p['receita_total']:,.2f}" 
                else: 
                    lines = ["📊 Ranking dos produtos mais vendidos:\n"] 
                    for i, p in enumerate(data, 1): 
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º" 
                        lines.append(f"{emoji} {p['modelo']} ({p['fabricante']})") 
                        lines.append(f"   📦 {p['unidades_vendidas']:,} unidades") 
                        lines.append(f"   💰 R$ {p['receita_total']:,.2f}\n") 
                    return "\n".join(lines) 

            elif tool_name == "get_monthly_revenue": 
                d = data[0] 
                return f"💰 **Receita Total:** R$ {d['receita_total']:,.2f}\n📦 **Total de Unidades:** {d['total_unidades']:,}" 

            elif tool_name == "get_product_sales_by_month": 
                lines = ["📊 **Vendas do mês**:\n"]
                if len(data) > 10:
                    lines = [f"📊 **Vendas do mês** (mostrando top 10 de {len(data)} produtos):\n"]
                    data_to_show = data[:10]
                else:
                    data_to_show = data
                for p in data_to_show:
                    lines.append(f"📱 {p['modelo']} ({p['fabricante']})")
                    lines.append(f"   📦 {p['unidades_vendidas']:,} unidades")
                    lines.append(f"   💰 R$ {p['receita']:,.2f}\n")
                return "\n".join(lines)

            elif tool_name == "get_product_sales":
                if data:
                    p = data[0]
                    return f"📱 Vendas de {p['modelo']} ({p['fabricante']}):\n\n   📦 {p['unidades_vendidas']:,} unidades vendidas\n   💰 R$ {p['receita']:,.2f}"
                else:
                    return "❌ Não encontrei dados para esse produto."

            elif tool_name == "get_comparison_by_manufacturer":
                lines = ["📊 **Comparativo por Fabricante**:\n"]
                for fab in data:
                    lines.append(f"🏢 **{fab['fabricante']}**")
                    lines.append(f"   📦 Total de Unidades: {fab['total_unidades']:,}")
                    lines.append(f"   💰 Receita Total: R$ {fab['receita_total']:,.2f}\n")
                return "\n".join(lines)

            elif tool_name == "get_average_monthly_sales":
                d = data[0]
                return f"📊 **Média Mensal de Vendas**:\n\n   💰 Faturamento Médio: R$ {d['media_receita']:,.2f}\n   📦 Unidades Médias: {d['media_unidades']:,}"

            elif tool_name == "get_best_selling_month":
                d = data[0]
                return f"🏆 **Melhor Mês de Vendas**:\n\n   🗓️ Mês: {d['mes_nome']}\n   💰 Faturamento: R$ {d['receita_total']:,.2f}\n   📦 Unidades Vendidas: {d['total_unidades']:,}"

            elif tool_name == "get_least_sold_products":
                if len(data) == 1:
                    p = data[0]
                    return f"📉 O produto menos vendido foi:\n\n   {p['modelo']} ({p['fabricante']})\n   {p['unidades_vendidas']:,} unidades vendidas\n   💰 R$ {p['receita_total']:,.2f}"
                else:
                    lines = ["📉 Ranking dos produtos menos vendidos:\n"]
                    for i, p in enumerate(data, 1):
                        lines.append(f"{i}º {p['modelo']} ({p['fabricante']})")
                        lines.append(f"   📦 {p['unidades_vendidas']:,} unidades")
                        lines.append(f"   💰 R$ {p['receita_total']:,.2f}\n")
                    return "\n".join(lines)

            elif tool_name == "get_multiple_product_sales":
                lines = ["📊 **Comparativo de Vendas**:\n"]
                for p in data:
                    lines.append(f"📱 {p['modelo']} ({p['fabricante']})")
                    lines.append(f"   📦 {p['unidades_vendidas']:,} unidades vendidas")
                    lines.append(f"   💰 R$ {p['receita_total']:,.2f}\n")
                return "\n".join(lines)

        except (KeyError, IndexError) as e:
            return f"😕 Desculpe, não consegui formatar a resposta. Detalhe do erro: {e}"
        except Exception as e:
            return f"🐞 Ocorreu um erro inesperado ao formatar a resposta: {e}"

    def process_message(self, user_message: str) -> str:
        """
        Processa a mensagem do usuário, chama a IA e executa a ferramenta.
        """
        prompt = f'{self.system_prompt}\n\n--- PERGUNTA DO USUÁRIO ---\n{user_message}'

        try:
            # 1. Chamar o Gemini
            response = self.model.generate_content(prompt)
            
            # Limpa a resposta para extrair apenas o JSON
            cleaned_response = response.text.strip()
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("Nenhum JSON válido encontrado na resposta da IA.")
            
            json_str = cleaned_response[json_start:json_end]

            # 2. Fazer o parse da resposta JSON
            tool_call = json.loads(json_str)
            tool_name = tool_call.get('tool')
            tool_params = tool_call.get('params', {})

            if not tool_name:
                return "❌ A IA não especificou uma ferramenta para usar."

            # 3. Executar a ferramenta
            if hasattr(self.db_tools, tool_name):
                tool_function = getattr(self.db_tools, tool_name)
                result = tool_function(**tool_params)
            else:
                return f"❌ Ferramenta '{tool_name}' não encontrada."

            # 4. Formatar a resposta
            return self._format_response(tool_name, result)

        except json.JSONDecodeError:
            return f"❌ Erro: A resposta da IA não é um JSON válido.\nResposta recebida:\n{cleaned_response}"
        except Exception as e:
            return f"🐞 Ocorreu um erro geral no processamento: {e}"