# Importación de módulos necesarios
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

# Inicialización de la aplicación Flask
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Clave secreta para manejar sesiones y seguridad
Bootstrap(app)  # Integración de Bootstrap con Flask

# Configuración de conexión a la base de datos MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'desarrollo_web',
}

# Función para obtener la conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Ruta principal (Inicio)
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('productos'))  # Redirige a productos si ya está logueado
    return render_template('index.html')  # Página de bienvenida

# Ruta para inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Recibe datos del formulario
        username = request.form['username']
        password = request.form['password']
        
        # Verifica usuario en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Verifica contraseña con hash
        if user and check_password_hash(user['password'], password):
            # Almacena datos del usuario en la sesión
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('productos'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')


# Ruta para registro de nuevos usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Recoge datos del formulario
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Encripta contraseña
        email = request.form['email']
        
        # Inserta nuevo usuario en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)',
                           (username, password, email))
            conn.commit()
            flash('Registro exitoso. Por favor inicia sesión.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('El nombre de usuario o correo ya existe', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()  # Limpia la sesión
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))

# Ruta para mostrar lista de productos (CRUD - Read)
@app.route('/productos')
def productos():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Requiere estar logueado
    
    # Obtiene los productos del usuario actual
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM productos WHERE user_id = %s', (session['user_id'],))
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('productos.html', productos=productos)

# Ruta para agregar un producto (CRUD - Create)
@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Requiere sesión activa
    
    if request.method == 'POST':
        # Recoge los datos del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        cantidad = int(request.form['cantidad'])
        user_id = session['user_id']
        
        # Inserta producto en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO productos (nombre, descripcion, precio, cantidad, user_id) VALUES (%s, %s, %s, %s, %s)',
                       (nombre, descripcion, precio, cantidad, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Producto agregado correctamente', 'success')
        return redirect(url_for('productos'))
    
    return render_template('agregar_producto.html')

# Ruta para editar un producto (CRUD - Update)
@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Consulta producto por ID y usuario
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM productos WHERE id = %s AND user_id = %s', (id, session['user_id']))
    producto = cursor.fetchone()
    
    if request.method == 'POST':
        # Actualiza los datos del producto
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        cantidad = int(request.form['cantidad'])
        
        cursor.execute('UPDATE productos SET nombre = %s, descripcion = %s, precio = %s, cantidad = %s WHERE id = %s',
                       (nombre, descripcion, precio, cantidad, id))
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('productos'))
    
    cursor.close()
    conn.close()
    
    # Si no se encuentra el producto
    if producto is None:
        flash('Producto no encontrado', 'danger')
        return redirect(url_for('productos'))
    
    return render_template('editar_producto.html', producto=producto)

# Ruta para eliminar un producto (CRUD - Delete)
@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Elimina producto si pertenece al usuario
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM productos WHERE id = %s AND user_id = %s', (id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Producto eliminado correctamente', 'success')
    return redirect(url_for('productos'))

# Ruta para ver los detalles de un producto
@app.route('/producto/<int:id>')
def ver_producto(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Requiere sesión activa
    
    # Consulta el producto por ID y usuario
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM productos WHERE id = %s AND user_id = %s', (id, session['user_id']))
    producto = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if producto is None:
        flash('Producto no encontrado', 'danger')
        return redirect(url_for('productos'))
    
    return render_template('ver_producto.html', producto=producto)


# Punto de entrada principal de la aplicación
if __name__ == '__main__':
    app.run(debug=True)
