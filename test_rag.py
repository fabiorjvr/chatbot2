import os 
from dotenv import load_dotenv 
load_dotenv() 
 
from rag.gemini_fs import GeminiFileSearchManager 
 
fsm = GeminiFileSearchManager() 
store_id = fsm.ensure_store("celulares-fichas-tecnicas") 
fsm.upload_file("celularrag.pdf", "Fichas Técnicas") 
 
# Testa uma pergunta 
resposta = fsm.query("Quais aparelhos você tem disponível?") 
print(resposta)