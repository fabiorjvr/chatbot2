from flask import Flask, request, jsonify
from ai_agent import AIAgent

app = Flask(__name__)
agent = AIAgent()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    user_message = data['message']
    
    # Processa a mensagem usando o agente de IA
    response_message = agent.process_message(user_message)
    
    return jsonify({'response': response_message})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)