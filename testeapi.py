import requests

# URL da API para conectar a instância e obter o QR Code
url = "http://localhost:8081/instance/connect/loja-celulares"

# Headers com a apikey
headers = {
    "apikey": "66094555-C08E-4744-BBA4-5592B853DC97"
}

# Faz a requisição GET
response = requests.get(url, headers=headers)

# Imprime a resposta da API
print(response.json())
