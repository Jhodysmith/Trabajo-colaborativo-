from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'clave_super_secreta_techstore'  # Cambiar en producción

# --------------------- Base de datos ---------------------
def get_db():
    conn = sqlite3.connect('techstore.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio INTEGER NOT NULL,
            stock INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            imagen_icono TEXT  -- guardar nombre de icono o ruta de imagen
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS carrito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )''')
        # Insertar productos de ejemplo si no existen
        cursor = conn.execute("SELECT COUNT(*) FROM productos")
        if cursor.fetchone()[0] == 0:
            productos_ejemplo = [
                ('UltraBook Pro X1', 'Intel Core i7, 16GB RAM, SSD 512GB, pantalla 14" 4K, batería 12h.', 3999900, 10, 'portatiles', 'fas fa-laptop'),
                ('Gaming Stryker G7', 'Ryzen 7, RTX 4060, 32GB RAM, SSD 1TB, RGB mecánico.', 5499900, 5, 'portatiles', 'fas fa-laptop-code'),
                ('EcoBook Lite', 'Intel Core i5, 8GB RAM, SSD 256GB, liviano y eficiente.', 2299900, 15, 'portatiles', 'fas fa-charging-station'),
                ('WorkStation Z', 'Intel Xeon, 64GB RAM, SSD 2TB, para diseño y edición.', 8999900, 3, 'portatiles', 'fas fa-laptop'),
                ('Chromebook Spin', 'Pantalla táctil 360°, 4GB RAM, 64GB eMMC, ideal estudiantes.', 1199900, 20, 'portatiles', 'fas fa-laptop'),
                ('Phantom X3 Pro', 'Pantalla AMOLED 120Hz, 256GB, cámara 108MP, 5G.', 2999900, 8, 'smartphones', 'fas fa-mobile-alt'),
                ('Nova Flash', '6.7", 8GB RAM, 128GB, triple cámara, carga rápida 65W.', 1799900, 12, 'smartphones', 'fas fa-mobile-alt'),
                ('Rugged Max', 'Resistente al agua y golpes, batería 6000mAh.', 1499900, 6, 'smartphones', 'fas fa-mobile-alt'),
                ('Foldable Flex', 'Pantalla plegable 7.6", Snapdragon 8 Gen 2, 12GB RAM.', 4499900, 4, 'smartphones', 'fas fa-mobile-alt'),
                ('EcoPhone Zero', 'Materiales reciclados, 5G, batería 5000mAh, Android puro.', 1299900, 7, 'smartphones', 'fas fa-mobile-alt'),
                ('SoundBass ANC', 'Audífonos over-ear con cancelación activa de ruido, 40h batería.', 459900, 20, 'audio', 'fas fa-headphones'),
                ('AirPro Inalámbricos', 'Estuche de carga, calidad de sonido premium, Bluetooth 5.3.', 189900, 30, 'audio', 'fas fa-headphones'),
                ('Speaker Boom 360', 'Parlante portátil Bluetooth, IPX7, luces LED, 20W.', 299900, 15, 'audio', 'fas fa-volume-up'),
                ('Gaming Headset 7.1', 'Sonido envolvente, micrófono flexible, almohadillas de espuma.', 279900, 10, 'audio', 'fas fa-headphones'),
                ('Micrófono Podcast USB', 'Grabación profesional, cancelación de ruido, compatible con PC.', 159900, 12, 'audio', 'fas fa-microphone-alt'),
                ('Teclado Mecánico RGB', 'Switches azules, iluminación RGB, resistente a derrames.', 249900, 25, 'accesorios', 'fas fa-keyboard'),
                ('Mouse Gamer Pro', '16000 DPI, 8 botones, RGB, cable paracord.', 129900, 18, 'accesorios', 'fas fa-mouse'),
                ('Power Bank 20000mAh', 'Carga rápida USB-C, doble salida, LED indicador.', 89900, 40, 'accesorios', 'fas fa-battery-full'),
                ('Cargador GaN 65W', 'Carga rápida para laptop, celular y tablet, compacto.', 79900, 50, 'accesorios', 'fas fa-plug'),
                ('Smartwatch Sport', 'Monitoreo de ritmo cardíaco, GPS, resistente al agua.', 399900, 10, 'accesorios', 'fas fa-smartwatch'),
            ]
            for p in productos_ejemplo:
                conn.execute("INSERT INTO productos (nombre, descripcion, precio, stock, categoria, imagen_icono) VALUES (?,?,?,?,?,?)", p)
        conn.commit()

# Llamar a init_db al inicio (se crea la base si no existe)
init_db()

# --------------------- Decorador de login requerido ---------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------- Rutas ---------------------
@app.route('/')
def index():
    # Obtener todos los productos para mostrar en el catálogo
    conn = get_db()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template('index.html', productos=productos, session=session)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']

        error = None
        if not nombre:
            error = 'El nombre es obligatorio.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            error = 'Correo electrónico no válido.'
        elif len(password) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres.'
        elif password != confirm:
            error = 'Las contraseñas no coinciden.'

        if error:
            flash(error, 'danger')
        else:
            conn = get_db()
            existing = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
            if existing:
                flash('El correo ya está registrado. Inicia sesión.', 'danger')
            else:
                hashed = generate_password_hash(password)
                conn.execute("INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)", (nombre, email, hashed))
                conn.commit()
                conn.close()
                flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('login'))
            conn.close()
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_nombre'] = user['nombre']
            flash(f'Bienvenido {user["nombre"]}', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('index'))

@app.route('/producto/<int:producto_id>')
def producto_detalle(producto_id):
    conn = get_db()
    producto = conn.execute("SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    conn.close()
    if not producto:
        flash('Producto no encontrado', 'danger')
        return redirect(url_for('index'))
    return render_template('producto_detalle.html', producto=producto, session=session)

@app.route('/buscar')
def buscar():
    query = request.args.get('q', '').strip()
    precio_min = request.args.get('precio_min', type=int)
    precio_max = request.args.get('precio_max', type=int)
    solo_stock = request.args.get('stock', 'false') == 'true'

    conn = get_db()
    sql = "SELECT * FROM productos WHERE 1=1"
    params = []
    if query:
        sql += " AND nombre LIKE ?"
        params.append(f'%{query}%')
    if precio_min is not None:
        sql += " AND precio >= ?"
        params.append(precio_min)
    if precio_max is not None:
        sql += " AND precio <= ?"
        params.append(precio_max)
    if solo_stock:
        sql += " AND stock > 0"
    
    productos = conn.execute(sql, params).fetchall()
    conn.close()
    # Devolvemos parcial o redirigimos a index con resultados
    return render_template('index.html', productos=productos, busqueda=query, session=session)

@app.route('/agregar_carrito', methods=['POST'])
@login_required
def agregar_carrito():
    producto_id = int(request.form['producto_id'])
    cantidad = int(request.form['cantidad'])
    usuario_id = session['user_id']
    
    conn = get_db()
    producto = conn.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if not producto:
        flash('Producto no existe', 'danger')
        return redirect(url_for('index'))
    
    if cantidad <= 0:
        flash('Cantidad inválida', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    if cantidad > producto['stock']:
        flash(f'Solo hay {producto["stock"]} unidades disponibles.', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # Verificar si ya existe en carrito para sumar
    existing = conn.execute("SELECT id, cantidad FROM carrito WHERE usuario_id = ? AND producto_id = ?", (usuario_id, producto_id)).fetchone()
    if existing:
        nueva_cantidad = existing['cantidad'] + cantidad
        if nueva_cantidad > producto['stock']:
            flash(f'No puedes agregar más de {producto["stock"]} unidades en total.', 'danger')
        else:
            conn.execute("UPDATE carrito SET cantidad = ? WHERE id = ?", (nueva_cantidad, existing['id']))
            conn.commit()
            flash('Producto actualizado en el carrito.', 'success')
    else:
        conn.execute("INSERT INTO carrito (usuario_id, producto_id, cantidad) VALUES (?,?,?)", (usuario_id, producto_id, cantidad))
        conn.commit()
        flash('Producto agregado al carrito.', 'success')
    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route('/carrito')
@login_required
def ver_carrito():
    usuario_id = session['user_id']
    conn = get_db()
    items = conn.execute('''
        SELECT c.id as carrito_id, p.id as producto_id, p.nombre, p.precio, c.cantidad, p.stock, (p.precio * c.cantidad) as subtotal
        FROM carrito c
        JOIN productos p ON c.producto_id = p.id
        WHERE c.usuario_id = ?
    ''', (usuario_id,)).fetchall()
    total = sum(item['subtotal'] for item in items)
    conn.close()
    return render_template('carrito.html', items=items, total=total)

@app.route('/eliminar_carrito/<int:carrito_id>')
@login_required
def eliminar_carrito(carrito_id):
    conn = get_db()
    conn.execute("DELETE FROM carrito WHERE id = ? AND usuario_id = ?", (carrito_id, session['user_id']))
    conn.commit()
    conn.close()
    flash('Producto eliminado del carrito.', 'success')
    return redirect(url_for('ver_carrito'))

@app.route('/actualizar_carrito', methods=['POST'])
@login_required
def actualizar_carrito():
    carrito_id = int(request.form['carrito_id'])
    cantidad = int(request.form['cantidad'])
    usuario_id = session['user_id']
    conn = get_db()
    # Obtener stock del producto
    item = conn.execute('''
        SELECT p.stock, c.producto_id FROM carrito c
        JOIN productos p ON c.producto_id = p.id
        WHERE c.id = ? AND c.usuario_id = ?
    ''', (carrito_id, usuario_id)).fetchone()
    if item and cantidad > 0:
        if cantidad > item['stock']:
            flash(f'Solo hay {item["stock"]} unidades disponibles.', 'danger')
        else:
            conn.execute("UPDATE carrito SET cantidad = ? WHERE id = ?", (cantidad, carrito_id))
            conn.commit()
            flash('Cantidad actualizada.', 'success')
    elif cantidad <= 0:
        conn.execute("DELETE FROM carrito WHERE id = ?", (carrito_id,))
        conn.commit()
        flash('Producto eliminado.', 'success')
    conn.close()
    return redirect(url_for('ver_carrito'))

# --------------------- Ejecutar ---------------------
if __name__ == '__main__':
    app.run(debug=False, port=5001)  # Usamos debug=False para evitar problemas de recarga