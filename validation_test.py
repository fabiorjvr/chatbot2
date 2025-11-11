import os
from dotenv import load_dotenv
from tools import DatabaseTools

load_dotenv()

def run_tests():
    db_tools = DatabaseTools()

    # Test 1: Count records
    record_count = db_tools.executar_query("SELECT COUNT(*) as count FROM vendas_smartphones")[0]['count']
    print(f"Test 1: Record count: {record_count} (Expected: 248)")
    assert record_count == 248

    # Test 2: List manufacturers
    manufacturers_rows = db_tools.executar_query("SELECT DISTINCT fabricante FROM vendas_smartphones")
    manufacturers = [row['fabricante'] for row in manufacturers_rows]
    print(f"Test 2: Manufacturers: {manufacturers} (Expected: ['Xiaomi', 'Samsung', 'Apple', 'Motorola'])")
    assert set(manufacturers) == set(['Xiaomi', 'Samsung', 'Apple', 'Motorola'])

    # Test 3: Total revenue
    total_revenue = db_tools.executar_query("SELECT SUM(receita) as sum FROM vendas_smartphones")[0]['sum']
    print(f"Test 3: Total revenue: {total_revenue}")

    # Test 4: Top 3 models by units sold
    # 4. Top 3 modelos mais vendidos (unidades)
    top_models = db_tools.get_top_products(limit=3)
    print(f"\n✅ 4. Top 3 modelos: {top_models}")
    assert len(top_models) == 3, "Erro: O número de modelos retornados é diferente de 3."

    # 5. Receita da Apple em 2024
    apple_revenue_2024 = db_tools.get_comparison_by_manufacturer(year=2024)
    #filter for apple
    for item in apple_revenue_2024:
        if item['fabricante'] == 'Apple':
            print(f"Test 5: Apple revenue in 2024: {item}")


if __name__ == "__main__":
    run_tests()