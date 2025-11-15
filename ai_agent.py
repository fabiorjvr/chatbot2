from dotenv import load_dotenv
load_dotenv()

import os
import json
try:
    from rag.gemini_fs import GeminiFileSearchManager
except Exception:
    from rag.file_search_rest import GeminiFileSearchREST as GeminiFileSearchManager
import sys
import re
from datetime import datetime
from groq import Groq

class AIAgent:
    def __init__(self):
        self.file_search = GeminiFileSearchManager()
        self.conversation_histories = {}
        groq_key = os.environ.get("GROQ_API_KEY")
        self.groq = Groq(api_key=groq_key) if groq_key else None
        self.groq_model = "llama-3.1-70b-versatile"
        self.system_prompt = f"""
Você é Renato Tanner, vendedor especialista da PHONES PARAGUAY, atendendo via WhatsApp.

Estilo:
- Postura profissional, direta e cordial.
- Emojis apenas quando agregarem (no máximo 1 por parágrafo).
- Se fugir do tema, use uma risada breve (rs) e retome ao assunto.

Guardrails técnicos (NUNCA violar):
- Responder sobre câmeras, NFC, Dual SIM/eSIM, desempenho e bateria com base técnica real.
- Usar o RAG da Gemini (File Search) como principal fonte técnica.
- Se não houver informação, dizer claramente que não há dado e sugerir confirmar.

Data: {datetime.now().strftime('%d/%m/%Y')}.
"""
        try:
            print("\n--- INICIALIZANDO FILE SEARCH ---", file=sys.stderr)
            store_name = self.file_search.ensure_store(display_name="celulares-fichas-tecnicas")
            pdf_path = os.path.abspath("celularrag.pdf")
            if os.path.exists(pdf_path):
                print(f"📄 Encontrado: {pdf_path}", file=sys.stderr)
                self.file_search.upload_file(pdf_path, "celularrag.pdf")
            else:
                print(f"⚠️  Arquivo 'celularrag.pdf' não encontrado no diretório.", file=sys.stderr)
            print("--- FILE SEARCH PRONTO ---\n", file=sys.stderr)
        except Exception as e:
            print(f"🚨 CRÍTICO: Falha ao inicializar o File Search (RAG): {e}", file=sys.stderr)
            # A aplicação pode continuar, mas o RAG não funcionará.
            pass

    def _get_tools_definitions(self) -> list:
        return []

    def _extract_model_name(self, user_message: str) -> str:
        message_lower = user_message.lower()
        message_clean = re.sub(r'[^\w\s]', '', message_lower)
        model_map = {
            "iphone 15 pro max": "iPhone 15 Pro Max",
            "iphone 15 pro": "iPhone 15 Pro",
            "iphone 15": "iPhone 15 Pro",
            "moto g54": "Motorola Moto G54",
            "motorola g54": "Motorola Moto G54",
            "a54": "Samsung Galaxy A54",
            "galaxy a54": "Samsung Galaxy A54",
            "s24 ultra": "Samsung Galaxy S24 Ultra",
            "galaxy s24 ultra": "Samsung Galaxy S24 Ultra",
            "xiaomi 13t": "Xiaomi 13T",
            "13t": "Xiaomi 13T",
            "redmi note 13": "Xiaomi Redmi Note 13",
            "note 13": "Xiaomi Redmi Note 13",
        }
        for alias, full_name in model_map.items():
            if alias in message_clean:
                return full_name
        return None

    def _extract_name_question(self, user_message: str) -> bool:
        """Detecta se a mensagem está perguntando sobre o nome do vendedor."""
        name_patterns = [
            'qual seu nome', 'como você se chama', 'seu nome é', 'como se chama',
            'quem é você', 'qual é seu nome', 'me diga seu nome', 'posso saber seu nome'
        ]
        return any(pattern in user_message.lower() for pattern in name_patterns)

    def _extract_greeting_or_wellbeing(self, user_message: str) -> dict:
        """Detecta cumprimentos e perguntas sobre bem-estar."""
        greetings = ['oi', 'olá', 'opa', 'e aí', 'bom dia', 'boa tarde', 'boa noite']
        wellbeing = ['como você está', 'como vai', 'tudo bem com você', 'tudo certo', 'tudo bem']
        
        message_lower = user_message.lower()
        
        if any(g in message_lower for g in greetings):
            return {'tipo': 'cumprimento'}
        elif any(w in message_lower for w in wellbeing):
            return {'tipo': 'bem_estar'}
        return {'tipo': 'conversa_geral'}

    def _extract_intent(self, message_lower: str) -> dict:
        if any(p in message_lower for p in ['foto', 'imagem', 'mostre', 'ver o', 'quero ver']):
            return {'tipo': 'pedido_foto'}
        palavras_tecnicas = [
            'processador','ram','memória','armazenamento','câmera','bateria','tela','display','preço','valor','ficha técnica','comparar','diferença','melhor'
        ]
        if any(p in message_lower for p in palavras_tecnicas):
            return {'tipo': 'pergunta_tecnica'}
        if any(p in message_lower for p in ['nfc','pagamento por aproximação','aproximação','google pay','apple pay','samsung pay']):
            return {'tipo': 'pergunta_nfc'}
        if any(p in message_lower for p in ['dois chips','2 chips','dual sim','e-sim','esim']):
            return {'tipo': 'pergunta_dual_sim'}
        if any(p in message_lower for p in ['vendido','vendas','mais vendeu','vendeu mais','campeão','líder','top','receita','faturamento']):
            return {'tipo': 'pergunta_vendas'}
        return {'tipo': 'conversa_geral'}

    def _handle_greeting_response(self) -> dict:
        """Retorna resposta para cumprimentos."""
        import random
        greetings = [
            "Oi! Sou Renato Tanner da PHONES PARAGUAY. Como posso te ajudar hoje?",
            "Olá! Aqui é Renato, consultor de smartphones da PHONES PARAGUAY. Vamos achar o modelo ideal para você.",
            "Opa! Renato Tanner da PHONES PARAGUAY. Qual modelo você procura?"
        ]
        return {"tipo": "texto", "conteudo": random.choice(greetings)}

    def _handle_wellbeing_response(self) -> dict:
        """Retorna resposta para perguntas sobre bem-estar."""
        import random
        responses = [
            "Tudo certo por aqui. Vamos focar no seu objetivo: qual modelo te interessa?",
            "Estou bem, obrigado. Me fala como pretende usar o aparelho e eu te indico com precisão.",
            "Tranquilo. Qual seu orçamento e prioridade (câmera, desempenho, bateria)?"
        ]
        return {"tipo": "texto", "conteudo": random.choice(responses)}

    def _handle_name_question_response(self) -> dict:
        """Retorna resposta quando perguntam sobre o nome."""
        return {"tipo": "texto", "conteudo": "Meu nome é Renato Tanner. Sou especialista em smartphones na PHONES PARAGUAY há 8 anos. Como posso te ajudar hoje?"}

    def _handle_photo_request(self, model_name: str) -> list:
        """Retorna fotos do produto solicitado."""
        if not model_name:
            return [{"tipo": "texto", "conteudo": "Para qual modelo você gostaria de ver a foto? Temos iPhones, Samsungs e Xiaomis! 📱"}]
        
        # Lista de produtos com fotos disponíveis
        available_photos = {
            'iphone 15 pro': 'product_images/iPhone 15 Pro Natural titanium.png',
            'iphone 15': 'product_images/iPhone 15 Pro Natural titanium.png',
            'samsung galaxy a54': 'product_images/samsung_galaxy_a54.png',
            'galaxy a54': 'product_images/samsung_galaxy_a54.png',
            'xiaomi 13t': 'product_images/xiaomi_13t.png',
            'redmi note 13': 'product_images/redmi_note_13.png'
        }
        
        # Verificar se temos foto local para este modelo
        model_key = model_name.lower()
        if model_key in available_photos:
            local_image_path = os.path.abspath(available_photos[model_key])
            if os.path.exists(local_image_path):
                return [{"tipo": "fotos", "fotos": [local_image_path], "legenda": f"📱 {model_name} - Disponível na PHONES PARAGUAY"}]
        
        return [{"tipo": "texto", "conteudo": f"Não encontrei uma imagem para {model_name}, mas posso te dar todas as especificações técnicas! 📋"}]

    def process_message(self, user_id: str, user_message: str) -> dict:
        if user_id not in self.conversation_histories:
            self.conversation_histories[user_id] = [{"role": "system", "content": self.system_prompt}]
        self.conversation_histories[user_id].append({"role": "user", "content": user_message})
        try:
            
            # Verificar se é pergunta sobre o nome
            if self._extract_name_question(user_message):
                response_action = self._handle_name_question_response()
                return response_action
            
            # Verificar cumprimentos e bem-estar
            greeting_intent = self._extract_greeting_or_wellbeing(user_message)
            if greeting_intent.get('tipo') == 'cumprimento':
                response_action = self._handle_greeting_response()
                return response_action
            elif greeting_intent.get('tipo') == 'bem_estar':
                response_action = self._handle_wellbeing_response()
                return response_action
            
            intent = self._extract_intent(user_message.lower())
            if intent.get('tipo') == 'pedido_foto':
                actions = self._handle_photo_request(self._extract_model_name(user_message))
                response_action = actions[0] if actions else {"tipo": "texto", "conteudo": "Não encontrei imagem."}
                try:
                    self.db_tools.save_conversation_message(user_id, "assistant", "[fotos]" if response_action.get('tipo') != 'texto' else response_action.get('conteudo',''), datetime.now())
                except Exception:
                    pass
                return response_action
            if intent.get('tipo') in ['pergunta_nfc','pergunta_dual_sim']:
                model = self._extract_model_name(user_message)
                content = self._answer_features_with_rag(model, intent.get('tipo'))
                return content
            # Perguntas técnicas e gerais vão para o RAG da Gemini
            if intent.get('tipo') in ['pergunta_tecnica', 'pergunta_nfc', 'pergunta_dual_sim']:
                model = self._extract_model_name(user_message)
                content = self._answer_features_with_rag(model, intent.get('tipo'))
                return content
            texto = self.file_search.query(user_message) or "Me diga o modelo e sua prioridade (câmera, desempenho, bateria) que eu te oriento."
            return {"tipo": "texto", "conteudo": texto}
        except Exception as e:
            if self.groq:
                try:
                    msgs = self.conversation_histories.get(user_id, []) + [{"role": "user", "content": user_message}]
                    comp = self.groq.chat.completions.create(messages=msgs, model=self.groq_model, max_tokens=512)
                    txt = comp.choices[0].message.content
                    return {"tipo": "texto", "conteudo": txt}
                except Exception:
                    pass
            return {"tipo": "texto", "conteudo": "Desculpe, estou com um problema técnico. Tente novamente em alguns instantes."}

    def _format_response(self, tool_name: str, data: list) -> list[dict]:
        """Formata respostas técnicas com apresentação clara e moderada."""
        actions = []
        if not data or (isinstance(data, list) and len(data) > 0 and "erro" in data[0]):
            erro_msg = data[0].get('erro', 'Dados não encontrados') if data else 'Dados não encontrados'
            actions.append({"tipo": "texto", "conteudo": f"{erro_msg}"})
            return actions
        try:
            if tool_name == "get_smartphone_details_and_photos":
                if not data:
                    actions.append({"tipo": "texto", "conteudo": "Não encontrei detalhes para o modelo solicitado."})
                    return actions
                p = data[0]
                texto_resposta = f"{p.get('modelo','Modelo')} ({p.get('fabricante','Fabricante')})\n"
                texto_resposta += f"Disponível na PHONES PARAGUAY\n\n"
                
                specs = p.get('especificacoes_tecnicas', {})
                if specs:
                    texto_resposta += "ESPECIFICAÇÕES TÉCNICAS:\n"
                    if 'processador' in specs: texto_resposta += f"- Processador: {specs['processador']}\n"
                    if 'ram' in specs: texto_resposta += f"- RAM: {specs['ram']}\n"
                    if 'armazenamento' in specs: texto_resposta += f"- Armazenamento: {specs['armazenamento']}\n"
                    if 'camera_principal' in specs: texto_resposta += f"- Câmera: {specs['camera_principal']}\n"
                    if 'bateria' in specs: texto_resposta += f"- Bateria: {specs['bateria']}\n"
                    if 'tela' in specs: texto_resposta += f"- Tela: {specs['tela']}\n"
                
                info_geral = p.get('info_geral', {})
                if info_geral and 'preco' in info_geral:
                    texto_resposta += f"\nPREÇO: R$ {info_geral['preco']}\n"
                
                pontos_fortes = p.get('pontos_fortes', [])
                if pontos_fortes:
                    texto_resposta += f"\nPONTOS FORTES:\n" + "\n".join([f"- {pf}" for pf in pontos_fortes[:3]])
                
                texto_resposta += f"\n\nQuer saber mais? Pergunte sobre fotos, comparações ou disponibilidade."
                
                actions.append({"tipo": "texto", "conteudo": texto_resposta.strip()})
                if p.get('fotos'):
                    actions.append({"tipo": "fotos", "fotos": p['fotos'], "legenda": f"Fotos do {p.get('modelo','celular')} - PHONES PARAGUAY"})
                return actions
            elif tool_name == "get_top_sold_products":
                if len(data) == 1:
                    p = data[0]
                    texto = f"🏆 *PRODUTO MAIS VENDIDO:*\n\n📱 {p['modelo']} ({p['fabricante']})\n📦 {p['unidades_vendidas']:,} unidades\n💰 R$ {p['receita_total']:,.2f}"
                else:
                    linhas = ["🏆 *TOP PRODUTOS MAIS VENDIDOS:*"]
                    for i, p in enumerate(data[:3], 1):
                        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
                        linhas.append(f"\n{emoji} *{p['modelo']}* ({p['fabricante']})*")
                        linhas.append(f"   📦 {p['unidades_vendidas']:,} | 💰 R$ {p['receita_total']:,.2f}")
                    texto = "\n".join(linhas)
                actions.append({"tipo": "texto", "conteudo": texto})
                return actions
            elif tool_name == "get_monthly_revenue":
                d = data[0]
                texto = f"RECEITA DO PERÍODO:\n\nTotal: R$ {d['receita_total']:,.2f}\nUnidades: {d['total_unidades']:,}"
                actions.append({"tipo": "texto", "conteudo": texto})
                return actions
            elif tool_name == "get_product_sales":
                if data:
                    p = data[0]
                    texto = f"Vendas de {p.get('modelo','Produto')}: {p.get('unidades_vendidas',0)} unidades, R$ {p.get('receita',0):,.2f}."
                    actions.append({"tipo": "texto", "conteudo": texto})
                return actions
            actions.append({"tipo": "texto", "conteudo": json.dumps(data, ensure_ascii=False)})
            return actions
        except Exception as e:
            actions.append({"tipo": "texto", "conteudo": f"Erro ao formatar: {e}"})
            return actions

    def _ensure_base_docs(self):
        return None

    def _answer_features_with_rag(self, model_name: str, tipo: str) -> dict:
        if not model_name:
            complemento = "NFC" if tipo == 'pergunta_nfc' else "Dual SIM/eSIM"
            return {"tipo": "texto", "conteudo": f"Qual modelo você quer confirmar {complemento}?"}
        pergunta = ""
        if tipo == 'pergunta_nfc':
            pergunta = f"{model_name} possui NFC?"
        elif tipo == 'pergunta_dual_sim':
            pergunta = f"{model_name} possui Dual SIM ou eSIM?"
        else:
            pergunta = f"Especificações sobre {model_name}"
        try:
            texto = self.file_search.query(pergunta)
            texto = texto or f"Sem resposta técnica para {model_name}."
            return {"tipo": "texto", "conteudo": texto}
        except Exception:
            return {"tipo": "texto", "conteudo": f"Sem base técnica carregada para {model_name}."}

def main():
    if len(sys.argv) < 3:
        print(json.dumps({'tipo': 'erro', 'conteudo': 'Parâmetros: user_id mensagem'}))
        sys.exit(1)
    agent = AIAgent()
    response = agent.process_message(sys.argv[1], sys.argv[2])
    print(json.dumps(response, ensure_ascii=False))

if __name__ == "__main__":
    main()