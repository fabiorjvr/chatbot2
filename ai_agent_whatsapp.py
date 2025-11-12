# -*- coding: utf-8 -*-
import sys
import psycopg2
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def conectar_banco():
    """Conecta ao PostgreSQL"""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def consultar_banco(query):
    """Executa query no banco"""
    conn = conectar_banco()
    cur = conn.cursor()
    cur.execute(query)
    resultado = cur.fetchall()
    cur.close()
    conn.close()
    return resultado

def processar_pergunta(pergunta):
    """
    Processa pergunta com a API Groq
    """
    if not os.environ.get("GROQ_API_KEY"):
        return "Erro: A chave da API Groq não foi configurada."

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente de vendas de smartphones. Responda de forma CURTA (máximo 2 linhas para WhatsApp)"
                },
                {
                    "role": "user",
                    "content": pergunta,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
        )
        
        content = chat_completion.choices[0].message.content
        if content:
            return content.strip()

        return "Não consegui processar sua pergunta no momento."

    except Exception as e:
        return f"Ocorreu um erro inesperado: {e}"

def main():
    if len(sys.argv) < 2:
        print("Erro: pergunta não fornecida")
        return
    
    pergunta = sys.argv[1]
    resposta = processar_pergunta(pergunta)
    
    # ENVIAR RESPOSTA PARA NODE.JS
    print(resposta)

if __name__ == "__main__":
    main()