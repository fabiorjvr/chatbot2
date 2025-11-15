import os

codigo = ''''''import os
import time
from google import genai
from google.genai import types

class GeminiFileSearchManager:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY nao definida!")
        self.client = genai.Client(api_key=api_key)
        self.store_name = None
    
    def ensure_store(self, display_name="default-store"):
        try:
            stores = self.client.file_search_stores.list()
            if stores and hasattr(stores, "file_search_stores") and len(stores.file_search_stores) \u003e 0:
                self.store_name = stores.file_search_stores[0].name
                print(f"OK Store: {self.store_name}")
                return self.store_name
        except Exception as e:
            print(f"Aviso: {e}")
        
        try:
            print(f"Criando store: {display_name}")
            store = self.client.file_search_stores.create(config={"display_name": display_name})
            self.store_name = store.name
            print(f"OK Store criada: {self.store_name}")
            return self.store_name
        except Exception as e:
            print(f"Erro: {e}")
            raise
    
    def upload_file(self, file_path, display_name=None):
        if not self.store_name:
            raise ValueError("Store nao inicializada!")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")
        display_name = display_name or os.path.basename(file_path)
        try:
            print(f"Upload: {file_path}")
            operation_name = self.client.file_search_stores.upload_to_file_search_store(file=file_path, file_search_store_name=self.store_name, config={"display_name": display_name})
            print(f"Operacao: {operation_name}")
            print("Aguardando...")
            for i in range(60):
                operation = self.client.operations.get(operation_name)
                if operation.done:
                    print("OK Indexado!")
                    return self.store_name
                print(f"  Processando... ({i+1}/60)")
                time.sleep(2)
            return self.store_name
        except Exception as e:
            print(f"Erro: {e}")
            raise
    
    def query(self, pergunta):
        if not self.store_name:
            raise ValueError("Store nao inicializada!")
        try:
            print(f"Consultando: {pergunta[:50]}")
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=pergunta, config=types.GenerateContentConfig(tools=[types.Tool(file_search=types.FileSearchTool(file_search_store_names=[self.store_name]))]))
            return response.text
        except Exception as e:
            print(f"Erro: {e}")
            return "Erro"
''''''

os.makedirs('rag', exist_ok=True)
with open('rag/gemini_fs.py', 'w', encoding='utf-8') as f:
    f.write(codigo)
print('✅ Arquivo criado: rag/gemini_fs.py')