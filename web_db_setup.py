# web_db_setup.py
import sqlite3
import json
from datetime import datetime

def setup_web_database():
    """Настройка базы данных для веб-приложения"""
    conn = sqlite3.connect('iphones_catalog.db')
    cursor = conn.cursor()
    
    # Добавляем дополнительные поля для веб-отображения
    try:
        cursor.execute('ALTER TABLE iphones_catalog ADD COLUMN display_order INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE iphones_catalog ADD COLUMN is_featured BOOLEAN DEFAULT 0')
        cursor.execute('ALTER TABLE iphones_catalog ADD COLUMN category TEXT DEFAULT "iPhone"')
    except:
        print("Поля уже существуют")
    
    # Обновляем порядок отображения (новые товары первыми)
    cursor.execute('''
        UPDATE iphones_catalog 
        SET display_order = rowid, 
            is_featured = CASE WHEN price > 80000 THEN 1 ELSE 0 END,
            category = CASE 
                WHEN model LIKE '%Pro Max%' THEN 'iPhone Pro Max' 
                WHEN model LIKE '%Pro%' THEN 'iPhone Pro'
                WHEN model LIKE '%Plus%' THEN 'iPhone Plus'
                WHEN model LIKE '%Б/У%' THEN 'iPhone Б/У'
                ELSE 'iPhone'
            END
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных настроена для веб-отображения")

def export_sample_data():
    """Экспорт образца данных для проверки"""
    conn = sqlite3.connect('iphones_catalog.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT product_id, model, price, current_color, current_memory, image_url, category
        FROM iphones_catalog 
        ORDER BY price DESC 
        LIMIT 10
    ''')
    
    products = []
    for row in cursor.fetchall():
        product = {
            'id': row[0],
            'model': row[1],
            'price': f"{row[2]:,} руб.".replace(',', ' '),
            'color': row[3],
            'memory': row[4],
            'image': row[5],
            'category': row[6]
        }
        products.append(product)
    
    with open('sample_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print("✅ Образец данных экспортирован в sample_products.json")
    conn.close()

if __name__ == "__main__":
    setup_web_database()
    export_sample_data()