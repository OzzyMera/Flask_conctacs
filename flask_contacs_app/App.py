import pymysql
pymysql.install_as_MySQLdb()
import random
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'contrasenia'
app.config['MYSQL_DB'] = 'flaskcontacts'
mysql = MySQL(app)

# Secret Key for Flash Messages
app.secret_key = 'mysecretkey'

# Home Route
@app.route('/')
def Index():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM usuarios''')
    usuarios = cur.fetchall()
    cur.execute('''SELECT * FROM productos''')
    productos = cur.fetchall()
    cur.execute('''SELECT facturas.id, usuarios.nombre, productos.nombre, detalles_factura.cantidad, facturas.fecha
                FROM facturas
                JOIN usuarios ON facturas.usuario_id = usuarios.id
                JOIN detalles_factura ON facturas.id = detalles_factura.factura_id
                JOIN productos ON detalles_factura.producto_id = productos.id''')

    facturas = cur.fetchall()
    return render_template('index.html', usuarios=usuarios, productos=productos, facturas=facturas)

# Add Usuario
@app.route('/add_usuario', methods=['POST'])
def add_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (nombre, email, telefono) VALUES (%s, %s, %s)', (nombre, email, telefono))
        mysql.connection.commit()
        flash('Usuario agregado correctamente')
        return redirect(url_for('Index'))

# Edit Usuario
@app.route('/edit_usuario/<id>')
def get_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE id = %s', [id])
    usuario = cur.fetchone()
    return render_template('edit_usuario.html', usuario=usuario)

@app.route('/update_usuario/<id>', methods=['POST'])
def update_usuario(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        cur = mysql.connection.cursor()
        cur.execute('UPDATE usuarios SET nombre = %s, email = %s, telefono = %s WHERE id = %s', (nombre, email, telefono, id))
        mysql.connection.commit()
        flash('Usuario actualizado correctamente')
        return redirect(url_for('Index'))

# Delete Usuario
@app.route('/delete_usuario/<id>')
def delete_usuario(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM usuarios WHERE id = %s', [id])
        mysql.connection.commit()
        flash('Usuario eliminado correctamente')
    except pymysql.err.IntegrityError:
        flash('No se puede eliminar el usuario porque está referenciado en una factura')
    return redirect(url_for('Index'))

@app.route('/add_producto', methods=['POST'])
def add_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        cantidad_disponible = request.form['cantidad_disponible']

        codigo = str(random.randint(10000000, 99999999))  # Código de 8 dígitos

        cur = mysql.connection.cursor()
        # Verificar si el producto ya existe
        cur.execute('SELECT * FROM productos WHERE nombre = %s', [nombre])
        existing_product = cur.fetchone()
        if existing_product:
            # Si el producto ya existe, actualizar la cantidad disponible
            cur.execute('UPDATE productos SET cantidad_disponible = %s WHERE id = %s', (cantidad_disponible, existing_product[0]))
        else:
            # Si el producto no existe, agregarlo a la base de datos
            cur.execute('INSERT INTO productos (nombre, descripcion, precio, codigo, cantidad_disponible) VALUES (%s, %s, %s, %s, %s)', 
                        (nombre, descripcion, precio, codigo, cantidad_disponible))
        mysql.connection.commit()
        flash('Producto agregado satisfactoriamente')
        return redirect(url_for('Index'))


# Edit Producto
@app.route('/edit_producto/<id>')
def get_producto(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id = %s', [id])
    producto = cur.fetchone()
    return render_template('edit_producto.html', producto=producto)

@app.route('/update_producto/<id>', methods=['POST'])
def update_producto(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        cantidad_disponible= request.form['cantidad_disponible']
        cur = mysql.connection.cursor()
        cur.execute('UPDATE productos SET nombre = %s, descripcion = %s, precio = %s, cantidad_disponible= %s WHERE id = %s', (nombre, descripcion, precio, cantidad_disponible, id))
        mysql.connection.commit()
        flash('Producto actualizado correctamente')
        return redirect(url_for('Index'))

# Delete Producto
@app.route('/delete_producto/<id>')
def delete_producto(id):
    try:
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM productos WHERE id = %s', [id])
        mysql.connection.commit()
        flash('Producto eliminado correctamente')
    except pymysql.err.IntegrityError:
        flash('No se puede eliminar el producto porque está referenciado en una factura')
    return redirect(url_for('Index'))

# Add Factura
@app.route('/add_factura', methods=['POST'])
def add_factura():
    if request.method == 'POST':
        usuario_id = request.form['usuario_id']
        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')
        fecha = request.form['fecha']

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO facturas (usuario_id, fecha) VALUES (%s, %s)', (usuario_id, fecha))
        factura_id = cur.lastrowid

        for producto_id, cantidad in zip(producto_ids, cantidades):
            cur.execute('SELECT precio FROM productos WHERE id = %s', [producto_id])
            precio_unitario = cur.fetchone()[0]
            precio_total = int(cantidad) * precio_unitario
            # Actualizar la cantidad disponible del producto
            cur.execute('UPDATE productos SET cantidad_disponible = cantidad_disponible - %s WHERE id = %s', (cantidad, producto_id))
            cur.execute('INSERT INTO detalles_factura (factura_id, producto_id, cantidad, precio_unitario, precio_total) VALUES (%s, %s, %s, %s, %s)',
                        (factura_id, producto_id, cantidad, precio_unitario, precio_total))

        mysql.connection.commit()
        flash('Factura agregada correctamente')
        return redirect(url_for('Index'))


# Edit Factura
@app.route('/edit_factura/<id>')
def get_factura(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT facturas.id, detalles_factura.producto_id, detalles_factura.cantidad, facturas.fecha FROM facturas JOIN detalles_factura ON facturas.id = detalles_factura.factura_id WHERE facturas.id = %s', [id])
    factura = cur.fetchone()

    cur.execute('SELECT * FROM usuarios')
    usuarios = cur.fetchall()

    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()



    return render_template('edit_factura.html', factura=factura, usuarios=usuarios, productos=productos)


@app.route('/update_factura/<id>', methods=['POST'])
def update_factura(id):
    if request.method == 'POST':
        usuario_id = request.form['usuario_id']
        producto_id = request.form['producto_id']  # Aquí obtén el producto_id
        cantidad = request.form['cantidad']
        fecha = request.form['fecha']
        cur = mysql.connection.cursor()

        # Actualizar la cantidad en la tabla detalles_factura
        cur.execute('UPDATE detalles_factura SET cantidad = %s WHERE factura_id = %s AND producto_id = %s', (cantidad, id, producto_id))

        # Actualizar la factura en la tabla facturas
        cur.execute('UPDATE facturas SET usuario_id = %s, fecha = %s WHERE id = %s', (usuario_id, fecha, id))

        mysql.connection.commit()
        flash('Factura actualizada correctamente')
        return redirect(url_for('Index'))


# Delete Factura
@app.route('/delete_factura/<id>')
def delete_factura(id):
    cur = mysql.connection.cursor()

    # Eliminar los registros relacionados en detalles_factura
    cur.execute('DELETE FROM detalles_factura WHERE factura_id = %s', [id])

    # Luego, eliminar la factura
    cur.execute('DELETE FROM facturas WHERE id = %s', [id])

    mysql.connection.commit()
    flash('Factura eliminada correctamente')
    return redirect(url_for('Index'))


# Print Factura
@app.route('/print_factura/<id>')
def print_factura(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT facturas.id, usuarios.nombre, facturas.fecha FROM facturas JOIN usuarios ON facturas.usuario_id = usuarios.id WHERE facturas.id = %s', [id])
    factura = cur.fetchone()
    cur.execute('SELECT productos.nombre, detalles_factura.cantidad, detalles_factura.precio_unitario, detalles_factura.precio_total FROM detalles_factura JOIN productos ON detalles_factura.producto_id = productos.id WHERE detalles_factura.factura_id = %s', [id])
    detalles = cur.fetchall()

    total = sum([detalle[3] for detalle in detalles])

    return render_template('print_factura.html', factura=factura, detalles=detalles, total=total)

#Search
@app.route('/search', methods=['GET'])
def search():
    term = request.args.get('term')
    category = request.args.get('category')

    cur = mysql.connection.cursor()
    if category == 'usuarios':
        cur.execute('SELECT * FROM usuarios WHERE nombre LIKE %s', ['%' + term + '%'])
    elif category == 'productos':
        cur.execute('SELECT * FROM productos WHERE codigo LIKE %s', ['%' + term + '%'])
    elif category == 'facturas':
        cur.execute('''SELECT facturas.id, usuarios.nombre, productos.nombre, detalles_factura.cantidad, facturas.fecha
                       FROM facturas
                       JOIN usuarios ON facturas.usuario_id = usuarios.id
                       JOIN detalles_factura ON facturas.id = detalles_factura.factura_id
                       JOIN productos ON detalles_factura.producto_id = productos.id
                       WHERE facturas.id LIKE %s''', ['%' + term + '%'])
    results = cur.fetchall()

    if not results:
        flash('No se encontraron resultados', 'danger')
        return redirect(url_for('Index'))

    return render_template('search_results.html', results=results, category=category)





if __name__ == '__main__':
    app.run(port=3000, debug=True)