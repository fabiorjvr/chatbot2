import json
import logging
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json

from rag.vector_store import VectorStoreManager
from smartphones_data import smartphones

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Estabelece a conexão com o banco de dados PostgreSQL."""
    db_url = os.getenv("DATABASE_URL")
    if "?schema=" in db_url:
        db_url = db_url.split("?schema=")[0]
    return psycopg2.connect(db_url)

def clean_databases():
    """Limpa as tabelas no PostgreSQL e a coleção no ChromaDB."""
    # Limpar PostgreSQL
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            logging.info("Limpando tabelas do PostgreSQL...")
            cur.execute("DELETE FROM fotos;")
            cur.execute("DELETE FROM vendas_smartphones;")
            cur.execute("DELETE FROM smartphones;")
            conn.commit()
            logging.info("Tabelas do PostgreSQL limpas com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao limpar PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()

    # Limpar ChromaDB
    try:
        logging.info("Limpando coleção do ChromaDB...")
        vs_manager = VectorStoreManager()
        vs_manager.client.delete_collection(name=vs_manager.collection.name)
        logging.info("Coleção do ChromaDB limpa com sucesso.")
    except Exception as e:
        logging.warning(f"Aviso ao limpar ChromaDB (pode não existir ainda): {e}")

def insert_postgres_data(conn, smartphone):
    """Insere os dados de um smartphone no PostgreSQL."""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO smartphones (modelo, fabricante, info_geral, especificacoes_tecnicas, performance_score, categoria, segmento) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (smartphone['modelo'], smartphone['fabricante'], Json(smartphone['info_geral']), Json(smartphone['especificacoes_tecnicas']), smartphone['especificacoes_tecnicas'].get('performance_score', 0), smartphone['especificacoes_tecnicas'].get('categoria', 'N/A'), smartphone['especificacoes_tecnicas'].get('segmento', 'N/A'))
        )
        smartphone_id = cur.fetchone()[0]

        for url in smartphone['fotos_reais']:
            cur.execute("INSERT INTO fotos (smartphone_id, url_imagem) VALUES (%s, %s)", (smartphone_id, url))

def create_document_for_chroma(smartphone):
    """Cria um documento de texto formatado para o ChromaDB."""
    # Usa .get() para evitar erros se as chaves não existirem
    pontos_fortes_str = ", ".join(smartphone.get('pontos_fortes', []))
    pontos_fracos_str = ", ".join(smartphone.get('pontos_fracos', []))
    recomendado_para_str = ", ".join(smartphone.get('recomendado_para', []))
    comparacao_mercado_str = json.dumps(smartphone.get('comparacao_mercado', {}), indent=2, ensure_ascii=False)

    # Formata o documento de texto
    document = (
        f"Modelo: {smartphone.get('modelo', 'N/A')}\n"
        f"Fabricante: {smartphone.get('fabricante', 'N/A')}\n"
        f"\n--- Especificações Técnicas ---\n{json.dumps(smartphone.get('especificacoes_tecnicas', {}), indent=2, ensure_ascii=False)}\n"
        f"\n--- Análise ---\n"
        f"Pontos Fortes: {pontos_fortes_str}\n"
        f"Pontos Fracos: {pontos_fracos_str}\n"
        f"Recomendado Para: {recomendado_para_str}\n"
        f"Comparação de Mercado: {comparacao_mercado_str}"
    )
    return document

def setup_database():
    """Lê os dados dos smartphones, limpa e insere as informações no PostgreSQL e ChromaDB."""
    clean_databases()
    conn = get_db_connection()
    vs_manager = VectorStoreManager()
    
    try:
        # Inserir dados no PostgreSQL
        for smartphone in smartphones:
            logging.info(f"Inserindo dados do {smartphone['modelo']} no PostgreSQL...")
            insert_postgres_data(conn, smartphone)
        conn.commit()
        logging.info("Dados inseridos no PostgreSQL com sucesso.")

        # Inserir dados no ChromaDB
        documents_to_add = []
        metadatas_to_add = []
        ids_to_add = []
        for i, smartphone in enumerate(smartphones):
            logging.info(f"Preparando documento do {smartphone['modelo']} para o ChromaDB...")
            document = create_document_for_chroma(smartphone)
            documents_to_add.append(document)
            metadatas_to_add.append({'modelo': smartphone['modelo'], 'fabricante': smartphone['fabricante']})
            ids_to_add.append(f"doc_{i}")
        
        vs_manager.add_documents(documents_to_add, metadatas_to_add)
        logging.info("Documentos inseridos no ChromaDB com sucesso.")

    except Exception as e:
        conn.rollback()
        logging.error(f"Erro durante o setup do banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database()