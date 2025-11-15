import os
import time
from dotenv import load_dotenv

load_dotenv()

from rag.gemini_fs import GeminiFileSearchManager

perguntas = [
    "Qual eh o nome do vendedor?",
    "Qual eh o nome da loja?",
    "Vocês fazem envio para todo Brasil?",
    "Vocês emitem nota fiscal?",
    "Vocês tem site oficial?",
    "Qual eh o melhor celular pra jogar jogos pesados?",
    "Tem algum celular na faixa de 3000 reais?",
    "Qual eh o celular mais barato?",
    "Qual eh o celular mais caro?",
    "Qual celular tem a melhor camera?",
    "Qual celular tem a maior bateria?",
    "Qual celular eh mais fino?",
    "Qual eh o celular com melhor processador?",
    "Qual celular tem 1TB de armazenamento?",
    "Quais celulares tem 5G?",
    "Qual eh a diferenca entre Motorola Edge 60 Pro e Samsung Galaxy A56?",
    "Vocês tem parcelamento?",
    "Qual eh a garantia dos aparelhos?",
    "Eu quero fazer uma reclamacao sobre um produto",
    "Qual celular voces me recomenda pra fotografo profissional?"
]

print("=" * 80)
print("TESTE DE 20 PERGUNTAS - SISTEMA RAG PHONES PARAGUAY")
print("=" * 80)
print()

fsm = GeminiFileSearchManager()
store_id = fsm.ensure_store("celulares-fichas-tecnicas")
fsm.upload_file("celularrag.pdf", "Fichas Tecnicas")

print("\n" + "=" * 80)
print("INICIANDO TESTE DE PERGUNTAS (10 segundos entre cada uma)")
print("=" * 80 + "\n")

for i, pergunta in enumerate(perguntas, 1):
    print(f"\n{'='*80}")
    print(f"PERGUNTA {i}/20:")
    print(f"{'='*80}")
    print(f"Q: {pergunta}\n")
    
    resposta = fsm.query(pergunta)
    
    print(f"A: {resposta}")
    print()
    
    if i < len(perguntas):
        print("⏳ Aguardando 10 segundos ate proxima pergunta...")
        for segundos in range(10, 0, -1):
            print(f"   {segundos}s", end="\r")
            time.sleep(1)
        print("   OK - Proxima pergunta!       ")

print("\n" + "=" * 80)
print("TESTE FINALIZADO")
print("=" * 80)
