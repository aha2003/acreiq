# src/inspect_data.py
from src.db import db_engine

print("--- Top 15 Most Frequent Areas ---")
areas_df = db_engine.execute_query("""
    SELECT area_name_en, COUNT(*) as count 
    FROM transactions 
    WHERE area_name_en IS NOT NULL 
    GROUP BY area_name_en 
    ORDER BY count DESC 
    LIMIT 15;
""", {})
print(areas_df)

print("\n--- Distinct Transaction Groups ---")
groups_df = db_engine.execute_query("""
    SELECT DISTINCT trans_group_en, COUNT(*) as count 
    FROM transactions 
    GROUP BY trans_group_en;
""", {})
print(groups_df)
# check area + trans_group combo directly
df = db_engine.execute_query("""
    SELECT 
        area_name_en,
        trans_group_en,
        actual_worth,
        TRY_CAST(REPLACE(CAST(actual_worth AS VARCHAR), ',', '') AS DOUBLE) AS cast_worth
    FROM transactions
    WHERE LOWER(area_name_en) = 'al thanyah fifth'
      AND LOWER(trans_group_en) = 'sales'
    LIMIT 10
""", {})
print(df)