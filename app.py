# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'


class iPhoneCatalog:
    def __init__(self, db_path='iphones_catalog.db'):
        self.db_path = db_path
    
    def get_all_products(self, category=None, sort_by='price_desc', search=None):
        """Получение всех товаров с фильтрацией"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Базовый запрос
        query = '''
            SELECT ic.*, 
                   GROUP_CONCAT(DISTINCT icc.color_name) as all_colors,
                   GROUP_CONCAT(DISTINCT icm.memory_size) as all_memory
            FROM iphones_catalog ic
            LEFT JOIN iphone_catalog_colors icc ON ic.product_id = icc.product_id
            LEFT JOIN iphone_catalog_memory icm ON ic.product_id = icm.product_id
        '''
        
        conditions = []
        params = []
        
        # Фильтр по категории
        if category and category != 'all':
            conditions.append("ic.category = ?")
            params.append(category)
        
        # Поиск
        if search:
            conditions.append("(ic.model LIKE ? OR ic.current_color LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Группировка
        query += " GROUP BY ic.product_id"
        
        # Сортировка
        if sort_by == 'price_asc':
            query += " ORDER BY ic.price ASC"
        elif sort_by == 'price_desc':
            query += " ORDER BY ic.price DESC"
        elif sort_by == 'name':
            query += " ORDER BY ic.model ASC"
        else:
            query += " ORDER BY ic.display_order ASC"
        
        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]
        
        # Форматируем данные для отображения
        for product in products:
            product['formatted_price'] = f"{product['price']:,} руб.".replace(',', ' ')
            product['short_model'] = product['model'][:30] + '...' if len(product['model']) > 30 else product['model']
            
            # Обрабатываем цвета и память
            if product['all_colors']:
                product['colors_list'] = product['all_colors'].split(',')
            else:
                product['colors_list'] = [product['current_color']] if product['current_color'] else []
            
            if product['all_memory']:
                product['memory_list'] = product['all_memory'].split(',')
            else:
                product['memory_list'] = [product['current_memory']] if product['current_memory'] else []
        
        conn.close()
        return products
    
    def get_categories(self):
        """Получение списка категорий"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM iphones_catalog 
            GROUP BY category 
            ORDER BY count DESC
        ''')
        
        categories = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
        conn.close()
        return categories
    
    def get_featured_products(self, limit=6):
        """Получение рекомендуемых товаров"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM iphones_catalog 
            WHERE is_featured = 1 
            ORDER BY price DESC 
            LIMIT ?
        ''', (limit,))
        
        products = [dict(row) for row in cursor.fetchall()]
        for product in products:
            product['formatted_price'] = f"{product['price']:,} руб.".replace(',', ' ')
        
        conn.close()
        return products
    
    def get_product_by_id(self, product_id):
        """Получение товара по ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ic.*, 
                   GROUP_CONCAT(DISTINCT icc.color_name) as all_colors,
                   GROUP_CONCAT(DISTINCT icm.memory_size) as all_memory
            FROM iphones_catalog ic
            LEFT JOIN iphone_catalog_colors icc ON ic.product_id = icc.product_id
            LEFT JOIN iphone_catalog_memory icm ON ic.product_id = icm.product_id
            WHERE ic.product_id = ?
            GROUP BY ic.product_id
        ''', (product_id,))
        
        product = cursor.fetchone()
        if product:
            product = dict(product)
            product['formatted_price'] = f"{product['price']:,} руб.".replace(',', ' ')
            
            if product['all_colors']:
                product['colors_list'] = product['all_colors'].split(',')
            else:
                product['colors_list'] = []
            
            if product['all_memory']:
                product['memory_list'] = product['all_memory'].split(',')
            else:
                product['memory_list'] = []
        
        conn.close()
        return product

# Инициализация каталога
catalog = iPhoneCatalog()



@app.route('/')
def index():
    """Главная страница"""
    featured_products = catalog.get_featured_products(6)
    categories = catalog.get_categories()
    
    return render_template('index.html', 
                         featured_products=featured_products,
                         categories=categories,
                         total_products=len(catalog.get_all_products()))

@app.route('/catalog')
def catalog_page():
    """Страница каталога"""
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'price_desc')
    search = request.args.get('search', '')
    
    products = catalog.get_all_products(category, sort_by, search)
    categories = catalog.get_categories()
    
    return render_template('catalog.html',
                         products=products,
                         categories=categories,
                         current_category=category,
                         current_sort=sort_by,
                         search_query=search,
                         total_products=len(products))

@app.route('/product/<product_id>')
def product_detail(product_id):
    """Страница товара"""
    product = catalog.get_product_by_id(product_id)
    if not product:
        return "Товар не найден", 404
    
    # Похожие товары
    similar_products = catalog.get_all_products(category=product['category'])[:4]
    
    return render_template('product.html',
                         product=product,
                         similar_products=similar_products)

@app.route('/api/products')
def api_products():
    """API для получения товаров (для AJAX)"""
    category = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'price_desc')
    search = request.args.get('search', '')
    
    products = catalog.get_all_products(category, sort_by, search)
    return jsonify(products)

@app.route('/api/categories')
def api_categories():
    """API для получения категорий"""
    categories = catalog.get_categories()
    return jsonify(categories)

@app.route('/cart')
def cart():
    """Страница корзины"""
    if 'cart' not in session:
        session['cart'] = {}
    
    cart_products = []
    total_price = 0
    
    for product_id, quantity in session['cart'].items():
        product = catalog.get_product_by_id(product_id)
        if product:
            product['quantity'] = quantity
            product['total_price'] = product['price'] * quantity
            cart_products.append(product)
            total_price += product['total_price']
            
    return render_template('cart.html', cart_products=cart_products, total_price=total_price, catalog=catalog, total_products=len(catalog.get_all_products()))

@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    """Добавление товара в корзину"""
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    cart[product_id] = cart.get(product_id, 0) + 1
    session['cart'] = cart
    
    flash('Товар добавлен в корзину!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    """Удаление товара из корзины"""
    if 'cart' in session and product_id in session['cart']:
        session['cart'].pop(product_id)
        flash('Товар удален из корзины!', 'info')
    return redirect(url_for('cart'))

@app.route('/clear_cart')
def clear_cart():
    """Очистка корзины"""
    session.pop('cart', None)
    flash('Корзина очищена!', 'info')
    return redirect(url_for('cart'))

@app.context_processor
def inject_cart_count():
    """Доступное количество товаров в корзине во всех шаблонах"""
    cart_count = 0
    if 'cart' in session:
        cart_count = sum(session['cart'].values())
    return dict(cart_count=cart_count)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
