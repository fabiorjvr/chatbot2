import os
import time
from google import genai
from google.genai import types

class GeminiFileSearchManager:
    def __init__(self, store_name: str | None = None):
        self.client = genai.Client()
        self.store_name = store_name or os.environ.get("GEMINI_FILE_SEARCH_STORE_NAME")

    def ensure_store(self, display_name: str = "phones-whatsapp") -> str:
        if not self.store_name:
            store = self.client.file_search_stores.create(config={"display_name": display_name})
            self.store_name = store.name
        return self.store_name

    def upload_file(self, file_path: str, display_name: str | None = None) -> None:
        op = self.client.file_search_stores.upload_to_file_search_store(
            file=file_path,
            file_search_store_name=self.store_name,
            config={"display_name": display_name or os.path.basename(file_path)}
        )
        while not op.done:
            time.sleep(2)
            op = self.client.operations.get(op)

    def query(self, text: str) -> str:
        cfg = types.GenerateContentConfig(
            tools=[{"file_search": {"file_search_store_names": [self.store_name]}}]
        )
        resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config=cfg
        )
        return getattr(resp, "text", "") or ""

    def export_postgres_to_file(self, db_tools, out_path: str) -> str:
        rows = db_tools.executar_query(
            "SELECT modelo, fabricante, especificacoes_tecnicas, info_geral FROM smartphones;"
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for r in rows or []:
                modelo = r.get("modelo") or ""
                fabricante = r.get("fabricante") or ""
                specs = r.get("especificacoes_tecnicas") or {}
                info = r.get("info_geral") or {}
                linha = {
                    "modelo": modelo,
                    "fabricante": fabricante,
                    "especificacoes_tecnicas": specs,
                    "info_geral": info,
                }
                f.write(json_dumps(linha) + "\n")
        return out_path

def json_dumps(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)
