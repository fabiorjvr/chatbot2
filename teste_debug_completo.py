import os, time, json, requests, itertools, textwrap

BASE_URL = os.getenv("BASE_URL", "http://localhost:8081")
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "loja-celulares")
API_KEY = os.getenv("AUTHENTICATION_API_KEY", "B6D711FCDE4D4FD5936544120E713976")

# Versões candidatas do WhatsApp Web (ordem do mais “alto/recente” para alternativas)
PHONE_VERSIONS = [
    "2.3000.1023341282",
    "2.3000.6",
    "2.2407.1",
    "2.2409.2",
    "2.2410.5",
]

# Número E.164 é obrigatório em versões novas da API
E164_NUMBER = os.getenv("WA_NUMBER", "5511999999999")  # ajuste se quiser

HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

def section(t): 
    print("\n" + "="*70 + f"\n{t}\n" + "="*70)

def req(method, endpoint, desc="", json_data=None, timeout=15):
    print(f"\n→ {desc}")
    url = f"{BASE_URL}{endpoint}"
    print(f"  URL: {url}")
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, timeout=timeout)
        elif method == "POST":
            r = requests.post(url, headers=HEADERS, json=json_data, timeout=timeout)
        elif method == "DELETE":
            r = requests.delete(url, headers=HEADERS, timeout=timeout)
        else:
            raise ValueError("method inválido")
        print(f"  Status: {r.status_code}")
        try:
            data = r.json()
            print("  Resposta:", json.dumps(data, ensure_ascii=False, indent=2)[:700])
            return r.status_code, data
        except:
            print("  Resposta (texto):", r.text[:700])
            return r.status_code, None
    except Exception as e:
        print(f"  ✗ ERRO: {e}")
        return 0, None

def delete_instance_if_exists():
    status, data = req("GET", f"/instance/connectionState/{INSTANCE_NAME}", "Checando instância existente")
    if status == 200 and data and data.get("instance"):
        req("DELETE", f"/instance/delete/{INSTANCE_NAME}", f"Deletando '{INSTANCE_NAME}'")

def create_instance():
    payload = {
        "instanceName": INSTANCE_NAME,
        "integration": "WHATSAPP-BAILEYS",
        "qrcode": True,
        "number": E164_NUMBER,
        "token": ""
    }
    return req("POST", "/instance/create", "Criando nova instância", payload)

def connect_instance():
    return req("GET", f"/instance/connect/{INSTANCE_NAME}", "Solicitando conexão")

def try_qr(endpoints, attempts=15, sleep_s=3):
    print(f"\nTentando obter QR/Código de pareamento ({attempts} tentativas, {sleep_s}s cada)")
    for attempt in range(1, attempts+1):
        print(f"\n→ Tentativa {attempt}/{attempts}")
        time.sleep(sleep_s)
        for ep in endpoints:
            st, data = req("GET", ep, f"Buscando em {ep}", timeout=10)
            if not data: 
                continue
            qr = data.get("qrcode") or data.get("base64")
            pairing = data.get("pairingCode")
            state = data.get("state")
            if pairing:
                print("\n🎉 Código de pareamento:", pairing)
                return ("PAIRING", pairing)
            if qr:
                save_qr_html(qr)
                return ("QR", qr)
            if state:
                print(f"  Estado atual: {state}")
    return ("NONE", None)

def save_qr_html(qr_data):
    html = f"""<!DOCTYPE html>
<html><head><meta charset=\"utf-8\"><title>QR - {INSTANCE_NAME}</title>
<style>body{{display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:sans-serif;background:#f3f5f7}}
.box{{background:#fff;padding:40px;border-radius:18px;box-shadow:0 12px 50px rgba(0,0,0,.15);text-align:center}}
img{{max-width:320px}}</style></head>
<body><div class=\"box\">
<h2>Conecte seu WhatsApp</h2><p>Escaneie abaixo:</p>
<img src=\"{qr_data}\" alt=\"QR WhatsApp\"/></div></body></html>"""
    path = r"c:\Users\fabio\Desktop\chatbot whatsapp\qrcode_whatsapp.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n✓ QR salvo em: {path}\nAbra no navegador e escaneie agora.")

def set_phone_version_in_env(ver):
    # Atualiza variável no container via .env (você já reinicia via compose)
    print(f"\n↻ Ajustando CONFIG_SESSION_PHONE_VERSION para: {ver}")

def main():
    section("TESTE COMPLETO - CICLO ÚNICO")
    endpoints = [
        f"/instance/qrcode/{INSTANCE_NAME}",
        f"/instance/qr/{INSTANCE_NAME}",
        f"/instance/connectionState/{INSTANCE_NAME}",
    ]

    # Assumimos que a versão correta já está no .env e os contentores estão a ser executados
    current_version = os.getenv("CONFIG_SESSION_PHONE_VERSION", "N/A")
    print(f"\n===== A EXECUTAR CICLO DE TESTE PARA PHONE_VERSION={current_version} =====")

    delete_instance_if_exists()
    create_instance()
    time.sleep(3)
    connect_instance()
    kind, value = try_qr(endpoints, attempts=15, sleep_s=3)

    if kind in ("QR","PAIRING"):
        print(f"\n✅ Sucesso! Tipo: {kind}")
        if kind == "PAIRING":
            print(f"   Código: {value}")
        return

    print("\n✗ Sem QR ou código de emparelhamento neste ciclo.")
    print("Sugestões: Tentar a próxima versão da lista, verificar os logs do docker.")

if __name__ == "__main__":
    main()