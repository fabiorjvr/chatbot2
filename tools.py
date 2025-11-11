# -*- coding: utf-8 -*-
import psycopg2
import os
from datetime import date
from dotenv import load_dotenv

load_dotenv(encoding='latin-1')

def get_db_connection():
    """Estabelece a conexão com o banco de dados PostgreSQL."""
    return psycopg2.connect(os.getenv("DATABASE_URL"))

class DatabaseTools:
    """
    Classe que gerencia as consultas ao banco de dados de vendas de smartphones.
    """
    
    def __init__(self):
        self.conn = self.conectar_banco()

    def conectar_banco(self):
        """
        Estabelece conexão com o banco de dados PostgreSQL.
        """
        try:
            return get_db_connection()
        except Exception as e:
            print(f"❌ ERRO DE CONEXÃO: {repr(e)}")
            return None

    def executar_query(self, query: str, params: tuple = None) -> list:
        """
        Executa uma query no banco de dados de forma segura.
        """
        if self.conn is None:
            return [{"erro": "Sem conexão com o banco de dados."}]
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                
                if cur.description:
                    colunas = [desc[0] for desc in cur.description]
                    return [dict(zip(colunas, row)) for row in cur.fetchall()]
                else:
                    self.conn.commit()
                    return [{"status": "sucesso", "linhas_afetadas": cur.rowcount}]

        except Exception as e:
            self.conn.rollback()
            return [{"erro": f"Erro ao executar query: {e}"}]

    def fechar_conexao(self):
        if self.conn:
            self.conn.close()

    def get_top_products(self, limit: int = 1, month: int = None, year: int = None) -> list:
        """Retorna os N produtos mais vendidos, opcionalmente filtrando por mês/ano."""
        params = []
        query = """
            SELECT 
                modelo, 
                fabricante,
                SUM(unidades_vendidas) as unidades_vendidas, 
                SUM(receita) as receita_total
            FROM vendas_smartphones
        """
        
        where_clauses = []
        if month and year:
            where_clauses.append("mes = %s AND ano = %s")
            params.extend([month, year])
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += """
            GROUP BY modelo, fabricante
            ORDER BY unidades_vendidas DESC
            LIMIT %s;
        """
        params.append(limit)
        
        return self.executar_query(query, tuple(params))

    def get_monthly_revenue(self, month: int, year: int) -> list:
        """Retorna a receita total e o total de unidades vendidas de um mês/ano."""
        query = """
            SELECT 
                SUM(receita) as receita_total,
                SUM(unidades_vendidas) as total_unidades
            FROM vendas_smartphones
            WHERE mes = %s AND ano = %s;
        """
        return self.executar_query(query, (month, year))

    def get_product_sales_by_month(self, month: int, year: int) -> list:
        """Retorna todos os produtos vendidos em um mês/ano, ordenados por unidades vendidas."""
        query = """
            SELECT 
                modelo, 
                fabricante,
                unidades_vendidas, 
                receita
            FROM vendas_smartphones
            WHERE mes = %s AND ano = %s
            ORDER BY unidades_vendidas DESC;
        """
        return self.executar_query(query, (month, year))

    def get_product_sales(self, produto: str, month: int, year: int) -> list:
        """Retorna as vendas de um produto específico em um mês/ano."""
        query = """
            SELECT 
                modelo, 
                fabricante,
                unidades_vendidas, 
                receita
            FROM vendas_smartphones
            WHERE lower(modelo) LIKE %s AND mes = %s AND ano = %s;
        """
        return self.executar_query(query, (f"%{produto.lower()}%", month, year))

    def get_comparison_by_manufacturer(self, year: int, month: int = None) -> list:
        """Retorna o total de vendas por fabricante, opcionalmente filtrando por mês/ano."""
        params = []
        query = """
            SELECT 
                fabricante, 
                SUM(unidades_vendidas) as total_unidades,
                SUM(receita) as receita_total
            FROM vendas_smartphones
        """
        
        where_clauses = ["ano = %s"]
        params.append(year)
        
        if month:
            where_clauses.append("mes = %s")
            params.append(month)
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += """
            GROUP BY fabricante
            ORDER BY total_unidades DESC;
        """
        
        return self.executar_query(query, tuple(params))

    def get_average_monthly_sales(self, year: int) -> list:
        """Calcula a média de receita e unidades vendidas por mês em um ano."""
        query = """
            WITH vendas_mensais AS (
                SELECT 
                    mes,
                    SUM(receita) as receita_mensal,
                    SUM(unidades_vendidas) as unidades_mensais
                FROM vendas_smartphones
                WHERE ano = %s
                GROUP BY mes
            )
            SELECT 
                AVG(receita_mensal) as media_receita,
                AVG(unidades_mensais) as media_unidades
            FROM vendas_mensais;
        """
        return self.executar_query(query, (year,))

    def get_best_selling_month(self, year: int) -> list:
        """Retorna o mês com a maior receita de vendas em um ano."""
        query = """
            SELECT 
                CASE mes
                    WHEN 1 THEN 'Janeiro'
                    WHEN 2 THEN 'Fevereiro'
                    WHEN 3 THEN 'Março'
                    WHEN 4 THEN 'Abril'
                    WHEN 5 THEN 'Maio'
                    WHEN 6 THEN 'Junho'
                    WHEN 7 THEN 'Julho'
                    WHEN 8 THEN 'Agosto'
                    WHEN 9 THEN 'Setembro'
                    WHEN 10 THEN 'Outubro'
                    WHEN 11 THEN 'Novembro'
                    WHEN 12 THEN 'Dezembro'
                END as mes_nome,
                SUM(receita) as receita_total,
                SUM(unidades_vendidas) as total_unidades
            FROM vendas_smartphones
            WHERE ano = %s
            GROUP BY mes
            ORDER BY receita_total DESC
            LIMIT 1;
        """
        return self.executar_query(query, (year,))

    def get_least_sold_products(self, year: int, limit: int = 1) -> list:
        """Retorna os N produtos menos vendidos de um ano, com base na receita total."""
        query = """
            SELECT 
                modelo, 
                fabricante,
                SUM(unidades_vendidas) as unidades_vendidas, 
                SUM(receita) as receita_total
            FROM vendas_smartphones
            WHERE ano = %s
            GROUP BY modelo, fabricante
            ORDER BY receita_total ASC
            LIMIT %s;
        """
        return self.executar_query(query, (year, limit))

    def get_multiple_product_sales(self, products: list, year: int) -> list:
        """Retorna as vendas de múltiplos produtos em um ano."""
        if not products:
            return []

        # Cria os placeholders para a cláusula IN
        placeholders = ', '.join(['%s'] * len(products))
        
        query = f"""
            SELECT 
                modelo, 
                fabricante,
                SUM(unidades_vendidas) as unidades_vendidas, 
                SUM(receita) as receita_total
            FROM vendas_smartphones
            WHERE lower(modelo) IN ({placeholders}) AND ano = %s
            GROUP BY modelo, fabricante
            ORDER BY receita_total DESC;
        """
        
        # Prepara os parâmetros: produtos em minúsculas e o ano
        params = [p.lower() for p in products] + [year]
        return self.executar_query(query, tuple(params))