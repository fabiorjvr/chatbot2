import os
import time
import json
import requests

BASE = "https://generativelanguage.googleapis.com"

class GeminiFileSearchREST:
    def __init__(self, api_key: str | None = None, store_name: str | None = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.store_name = store_name

    def _url(self, path: str) -> str:
        return f"{BASE}{path}?key={self.api_key}"

    def ensure_store(self, display_name: str = "phones-whatsapp") -> str:
        if self.store_name:
            return self.store_name
        # List
        r = requests.get(self._url("/v1beta/fileSearchStores"))
        if r.ok:
            data = r.json()
            for s in data.get("fileSearchStores", []):
                if s.get("displayName") == display_name:
                    self.store_name = s.get("name")
                    return self.store_name
        # Create
        payload = {"displayName": display_name}
        rc = requests.post(self._url("/v1beta/fileSearchStores"), json=payload)
        rc.raise_for_status()
        self.store_name = rc.json().get("name")
        return self.store_name

    def upload_file(self, file_path: str, display_name: str | None = None) -> None:
        files = {"file": open(file_path, "rb")}
        config = {"displayName": display_name or os.path.basename(file_path)}
        # Upload to store (media endpoint)
        url = self._url(f"/upload/v1beta/{self.store_name}:uploadToFileSearchStore")
        ru = requests.post(url, files=files, data={"config": json.dumps(config)})
        ru.raise_for_status()
        op = ru.json()
        name = op.get("name")
        # Poll operation
        while True:
            ro = requests.get(self._url(f"/v1beta/{name}"))
            ro.raise_for_status()
            j = ro.json()
            if j.get("done"):
                break
            time.sleep(2)

    def query(self, text: str) -> str:
        tools = [{
            "file_search": {
                "file_search_store_names": [self.store_name]
            }
        }]
        body = {
            "model": "models/gemini-2.5-flash",
            "contents": text,
            "tools": tools
        }
        rg = requests.post(self._url("/v1beta/models/gemini-2.5-flash:generateContent"), json=body)
        if not rg.ok:
            return ""
        data = rg.json()
        # Try common response shapes
        if isinstance(data, dict):
            # google-genai SDK returns resp.text; REST returns candidates
            cand = data.get("candidates", [])
            if cand:
                parts = cand[0].get("content", {}).get("parts", [])
                if parts and isinstance(parts[0], dict):
                    return parts[0].get("text", "") or ""
        return ""