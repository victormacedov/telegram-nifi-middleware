import requests
import subprocess
import json

from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NIFI_URL  = os.getenv("NIFI_URL", "http://localhost:9090/contentListener")

def get_last_message():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()

    if not data["ok"] or not data["result"]:
        print("Nenhuma mensagem encontrada.")
        return None

    # Pega a última mensagem
    last_update = data["result"][-1]
    message = last_update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    return {"text": text, "chat_id": chat_id}

def parse_message(text):
    """
    Espera o padrão: Nome;CPF_ou_CNPJ;"mensagem"
    Ex: João Silva;123.456.789-09;"Quero suporte técnico"
    """
    parts = text.split(";")
    if len(parts) < 3:
        print("Formato inválido. Use: Nome;CPF_ou_CNPJ;\"mensagem\"")
        return None

    nome = parts[0].strip()
    documento = parts[1].strip()
    demanda = parts[2].strip().strip('"')

    return {"nome": nome, "documento": documento, "demanda": demanda}

def send_to_nifi(payload):
    """Envia os dados para o NiFi via curl (HTTPS, ignorando certificado autoassinado)"""
    body = json.dumps(payload)

    curl_command = [
        "curl", "-s", "-k",          # -k ignora certificado autoassinado
        "-X", "POST", NIFI_URL,
        "-H", "Content-Type: application/json",
        "-d", body
    ]

    print(f"Enviando para o NiFi: {body}")
    result = subprocess.run(curl_command, capture_output=True, text=True)

    if result.returncode == 0:
        print("Dados enviados com sucesso ao NiFi!")
    else:
        print(f"Erro ao enviar: {result.stderr}")

def main():
    msg = get_last_message()
    if not msg:
        return

    print(f"Última mensagem recebida: {msg['text']}")

    parsed = parse_message(msg["text"])
    if not parsed:
        return

    # Inclui o chat_id do remetente no payload (opcional, para uso futuro)
    parsed["chat_id_remetente"] = msg["chat_id"]

    send_to_nifi(parsed)

if __name__ == "__main__":
    main()
