from datetime import date

from flask import Flask, flash, redirect, render_template, request, url_for

from domain import CATEGORIAS, Calificacion, Cliente, Habitacion, Hotel, SistemaReservas, cargar_datos_iniciales

app = Flask(__name__)
app.secret_key = "clave-secreta-del-taller"

sistema = SistemaReservas()
cargar_datos_iniciales(sistema)


def parsear_fecha(texto):
    if not texto:
        return None
    return date.fromisoformat(texto)


@app.route("/")
def index():
    return render_template("index.html", hoteles=sistema.hoteles)


@app.route("/hoteles/<int:indice>/estado", methods=["POST"])
def cambiar_estado_hotel(indice):
    hotel = sistema.hoteles[indice]
    hotel.activo = not hotel.activo  # R5: activar o desactivar el hotel
    flash(f"{hotel.nombre} ahora está {'activo' if hotel.activo else 'inactivo'}", "ok")
    return redirect(url_for("index"))


@app.route("/hoteles/<int:indice_hotel>/habitaciones/<int:indice_hab>/estado", methods=["POST"])
def cambiar_estado_habitacion(indice_hotel, indice_hab):
    habitacion = sistema.hoteles[indice_hotel].habitaciones[indice_hab]
    habitacion.activa = not habitacion.activa  # R7: activar o desactivar la habitación
    flash(f"{habitacion.tipo} ahora está {'activa' if habitacion.activa else 'inactiva'}", "ok")
    return redirect(url_for("index"))


@app.route("/registrar-hotel", methods=["GET", "POST"])
def registrar_hotel():
    if request.method == "POST":
        hotel = Hotel(
            request.form["nombre"], request.form["direccion"], request.form["telefono"], request.form["correo"],
            request.form["ubicacion"], request.form["servicios"], request.form.get("fotos", ""),
            request.form.get("servicios_adicionales", ""), request.form["condicion_pago"],
            int(request.form["dias_anticipacion"]), int(request.form["penalidad_cancelacion"]),
        )
        sistema.hoteles.append(hotel)  # R1: registro del hotel
        flash("Hotel registrado", "ok")
        return redirect(url_for("index"))
    return render_template("registrar_hotel.html")


@app.route("/registrar-habitacion", methods=["GET", "POST"])
def registrar_habitacion():
    if request.method == "POST":
        hotel = sistema.hoteles[int(request.form["hotel"])]
        habitacion = Habitacion(
            request.form["tipo"], request.form["descripcion"], int(request.form["precio"]),
            request.form["servicios"], int(request.form["capacidad"]), request.form.get("fotos", ""),
            int(request.form.get("recargo_por_persona") or 0), request.form["categoria"],
        )
        hotel.agregar_habitacion(habitacion)  # R6: registro de la habitación
        flash("Habitación registrada", "ok")
        return redirect(url_for("index"))
    return render_template("registrar_habitacion.html", hoteles=sistema.hoteles, categorias=CATEGORIAS)


@app.route("/registrar-cliente", methods=["GET", "POST"])
def registrar_cliente():
    if request.method == "POST":
        cliente = Cliente(request.form["nombre"], request.form["telefono"], request.form["correo"], request.form["direccion"])
        sistema.clientes.append(cliente)  # R13: registro del cliente
        flash("Cliente registrado", "ok")
        return redirect(url_for("index"))
    return render_template("registrar_cliente.html")


@app.route("/buscar")
def buscar():
    entrada = parsear_fecha(request.args.get("entrada", ""))
    salida = parsear_fecha(request.args.get("salida", ""))
    ubicacion = request.args.get("ubicacion", "")
    calificacion = int(request.args.get("calificacion") or 0)
    precio = int(request.args.get("precio") or 0)
    categoria = request.args.get("categoria", "")
    resultados = None
    if request.args:
        if entrada and not salida:
            flash("Si eliges fecha de entrada, también debes elegir fecha de salida", "error")
        elif entrada and salida and salida <= entrada:
            flash("La salida debe ser posterior a la entrada", "error")
        else:
            resultados = sistema.buscar_habitaciones(entrada, salida, ubicacion, calificacion, precio, categoria)
    return render_template(
        "buscar.html", resultados=resultados, categorias=CATEGORIAS,
        fecha_ref=entrada or date.today(), sistema=sistema, valores=request.args,
    )


if __name__ == "__main__":
    app.run(debug=True)
