import requests
import time
import base64
from io import BytesIO

# Configurações
BASE_URL = "http://localhost:8081"
INSTANCE_NAME = "loja-celulares"
API_KEY = "B6D711FCDE4D4FD5936544120E713976"

headers = {
    "apikey": API_KEY,
    "Content-Type": "application/json"
}

print("=" * 50)
print("SCRIPT DE CONEXÃO EVOLUTION API")
print("=" * 50)

# 1. Verificar se a API está respondendo
print("\n1. Verificando se a API está acessível...")
try:
    response = requests.get(f"{BASE_URL}/instance/fetchInstances", headers=headers, timeout=5)
    print(f"✓ API está respondendo! Status: {response.status_code}")
except Exception as e:
    print(f"✗ Erro ao conectar na API: {e}")
    print("Verifique se os contêineres estão rodando com: docker ps")
    exit(1)

# 2. Verificar status da instância
print(f"\n2. Verificando status da instância '{INSTANCE_NAME}'...")
try:
    response = requests.get(
        f"{BASE_URL}/instance/connectionState/{INSTANCE_NAME}",
        headers=headers
    )
    status = response.json()
    print(f"Status atual: {status}")
except Exception as e:
    print(f"Erro ao verificar status: {e}")

# 3. Conectar a instância
print(f"\n3. Conectando a instância '{INSTANCE_NAME}'...")
try:
    response = requests.get(
        f"{BASE_URL}/instance/connect/{INSTANCE_NAME}",
        headers=headers
    )
    print(f"Resposta da conexão: {response.json()}")
except Exception as e:
    print(f"Erro ao conectar: {e}")

# 4. Aguardar e buscar o QR Code
print("\n4. Aguardando geração do QR Code...")
max_attempts = 10
qr_code_found = False

for attempt in range(max_attempts):
    time.sleep(3)  # Aguardar 3 segundos entre tentativas
    print(f"   Tentativa {attempt + 1}/{max_attempts}...")
    
    try:
        # Buscar QR Code via endpoint base64
        response = requests.get(
            f"{BASE_URL}/instance/qrcode/{INSTANCE_NAME}",
            headers=headers
        )
        
        data = response.json()
        
        if data.get('qrcode') or data.get('base64'):
            qr_code_found = True
            qr_data = data.get('qrcode') or data.get('base64')
            
            print("\n" + "=" * 50)
            print("✓ QR CODE GERADO COM SUCESSO!")
            print("=" * 50)
            print("\nDados do QR Code:")
            print(qr_data[:100] + "..." if len(qr_data) > 100 else qr_data)
            print("\nABRA SEU WHATSAPP E ESCANEIE O QR CODE!")
            print("WhatsApp > Aparelhos Conectados > Conectar Aparelho")
            
            # Salvar QR Code em arquivo HTML para visualização
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>QR Code WhatsApp</title>
                <style>
                    body {{
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        min-height: 100vh;
                        margin: 0;
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 20px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                        text-align: center;
                    }}
                    h1 {{
                        color: #25D366;
                        margin-bottom: 20px;
                    }}
                    img {{
                        max-width: 300px;
                        height: auto;
                        border: 5px solid #25D366;
                        border-radius: 10px;
                        padding: 10px;
                        background: white;
                    }}
                    .instructions {{
                        margin-top: 20px;
                        color: #666;
                        line-height: 1.6;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📱 Conecte seu WhatsApp</h1>
                    <img src="{qr_data}" alt="QR Code WhatsApp">
                    <div class="instructions">
                        <p><strong>Como conectar:</strong></p>
                        <ol style="text-align: left; display: inline-block;">
                            <li>Abra o WhatsApp no seu celular</li>
                            <li>Toque em "Aparelhos Conectados"</li>
                            <li>Toque em "Conectar Aparelho"</li>
                            <li>Escaneie este QR Code</li>
                        </ol>
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open("qrcode_whatsapp.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print("\n✓ QR Code salvo em 'qrcode_whatsapp.html'. Abra este arquivo em seu navegador.")
            break # Sai do loop se o QR code for encontrado

    except Exception as e:
        print(f"   ✗ Erro na tentativa {attempt + 1}: {e}")

if not qr_code_found:
    print("\n" + "=" * 50)
    print("✗ Não foi possível obter o QR Code após várias tentativas.")
    print("=" * 50)
    print("Por favor, verifique os logs do contêiner 'evolution_api' para mais detalhes:")
    print("docker logs evolution_api --tail 50")