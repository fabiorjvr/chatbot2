import subprocess
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import sys
import requests # Importa a biblioteca requests
from ai_agent import AIAgent

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Instancia o agente de IA uma única vez
try:
    print("⏳ Inicializando AIAgent...", file=sys.stderr)
    agent = AIAgent()
    print("✅ Agente de IA inicializado com sucesso.", file=sys.stderr)
except Exception as e:
    print(f"🚨 CRÍTICO: Falha ao inicializar o AIAgent: {e.__class__.__name__}: {e}", file=sys.stderr)
    agent = None

# Obtém a URL do servidor Node.js a partir das variáveis de ambiente
wpp_server_url = os.getenv("WPP_SERVER_URL", "http://localhost:3000")
print(f"ℹ️  URL do servidor WPPConnect: {wpp_server_url}", file=sys.stderr)


def send_response_to_node(payload):
    """Envia a resposta processada para o servidor Node.js."""
    headers = {'Content-Type': 'application/json'}
    from datetime import datetime
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        # O endpoint no Node.js que vai receber a resposta
        node_endpoint = f"{wpp_server_url}/process-response"
        response = requests.post(node_endpoint, json=payload, headers=headers)
        response.raise_for_status()
        print(f"[{ts}] ✅ Resposta enviada ao Node.js: tipo={payload.get('tipo')} destino={payload.get('recipient_phone')}", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"[{ts}] 🚨 Erro ao enviar resposta para o Node.js: {e}", file=sys.stderr)


@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe mensagens do WhatsApp via webhook do WPPConnect (Node.js)."""
    try:
        if not agent:
            print("🚨 Agente não inicializado. Abortando requisição.", file=sys.stderr)
            return jsonify({"status": "error", "message": "Agente de IA não está pronto."}), 503

        data = request.json or {}
        from datetime import datetime
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{ts}] --- Nova Mensagem Recebida ---", file=sys.stderr)

        # Processar informações do grupo
        message_body = data.get('body', '')
        sender_id = data.get('from')
        is_group_msg = bool(data.get('isGroupMsg', False))
        author = data.get('author', sender_id)
        is_bot_mentioned = bool(data.get('isBotMentioned', False))

        if is_group_msg:
            print(f"[{ts}] 📋 GRUPO: {sender_id}", file=sys.stderr)
            print(f"[{ts}] 👤 AUTOR: {author}", file=sys.stderr)
            print(f"[{ts}] 🔔 BOT MENCIONADO: {is_bot_mentioned}", file=sys.stderr)

        actual_sender = author if is_group_msg else sender_id

        if not sender_id or not message_body:
            print("ID do remetente ou corpo da mensagem ausente.", file=sys.stderr)
            return jsonify({"status": "error", "message": "Dados ausentes"}), 400

        print(f"[{ts}] De: {actual_sender}", file=sys.stderr)
        print(f"[{ts}] Mensagem: {message_body}", file=sys.stderr)

        if data.get('media_base64') and str(data.get('mimetype','')).startswith('image'):
            try:
                texto_ocr = perform_ocr(data['media_base64'])
                print(f"[{ts}] 🧾 OCR: {texto_ocr[:200]}", file=sys.stderr)
                ocr_payload = {
                    "tipo": "texto",
                    "conteudo": f"OCR: {texto_ocr}",
                    "recipient_phone": sender_id,
                    "is_group_msg": is_group_msg
                }
                send_response_to_node(ocr_payload)
            except Exception as e:
                print(f"[{ts}] ⚠️ Falha no OCR: {e}", file=sys.stderr)

        if is_group_msg:
            print(f"[{ts}] Tipo: Mensagem de Grupo", file=sys.stderr)

        # Processar com agente
        try:
            response_action = agent.process_message(actual_sender, message_body)
        except Exception as inner_e:
            print(f"[{ts}] ⚠️ Erro no agente: {inner_e}", file=sys.stderr)
            response_action = {"tipo": "texto", "conteudo": "Tive um erro ao entender sua mensagem. Pode repetir?"}

        if response_action:
            response_action['recipient_phone'] = sender_id
            response_action['is_group_msg'] = is_group_msg
            try:
                send_response_to_node(response_action)
            except Exception as e:
                print(f"⚠️ Falha ao encaminhar ao Node.js: {e}", file=sys.stderr)

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"🚨 Erro inesperado geral no webhook: {e}", file=sys.stderr)
        return jsonify({"status": "ok"})

def perform_ocr(data_uri: str) -> str:
    import base64
    import re
    import io
    from PIL import Image
    try:
        header, b64 = data_uri.split(',', 1)
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes))
        # Tesseract
        try:
            import pytesseract
            text = pytesseract.image_to_string(img, lang='por')
            return text.strip()
        except Exception:
            # Fallback simples
            return "[OCR indisponível no servidor]"
    except Exception as e:
        return f"Falha ao decodificar imagem: {e}"

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "ok"})

@app.route('/health', methods=['GET'])
def health_check():
    from datetime import datetime
    status = {
        "status": "healthy" if agent else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "flask": "ok",
            "ai_agent": "ok" if agent else "error"
        }
    }
    return jsonify(status), (200 if agent else 503)

@app.route('/metrics', methods=['GET'])
def metrics():
    from datetime import datetime
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "ai_agent_status": "active" if agent else "inactive",
        "whatsapp_integration": "configured" if os.getenv("WPP_SERVER_URL") else "not_configured"
    })

@app.route('/test_rag', methods=['GET'])
def test_rag():
    try:
        q = request.args.get('q', 'Qual celular tem 1TB de armazenamento?')
        if not agent:
            return jsonify({"error": "agent not initialized"}), 503
        text = agent.file_search.query(q)
        return jsonify({"query": q, "text": text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando servidor Flask...")
    finally:
        pass