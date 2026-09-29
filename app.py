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


@app.route("/reservar", methods=["GET", "POST"])
def reservar():
    disponibles = None
    if request.method == "POST" and request.form.get("paso") == "buscar":
        cliente = sistema.clientes[int(request.form["cliente"])]
        entrada = parsear_fecha(request.form["entrada"])
        salida = parsear_fecha(request.form["salida"])
        personas = int(request.form["personas"])
        if salida <= entrada:
            flash("La salida debe ser posterior a la entrada", "error")
        else:
            disponibles = [h for h in sistema.buscar_habitaciones(entrada, salida) if h.capacidad >= personas]  # R9: la capacidad no se puede exceder
            if not disponibles:
                flash("No hay habitaciones disponibles para esas fechas y personas", "error")
            return render_template(
                "reservar.html", clientes=sistema.clientes, disponibles=disponibles, sistema=sistema,
                cliente_idx=request.form["cliente"], entrada=entrada, salida=salida, personas=personas,
            )
    if request.method == "POST" and request.form.get("paso") == "confirmar":
        cliente = sistema.clientes[int(request.form["cliente"])]
        entrada = parsear_fecha(request.form["entrada"])
        salida = parsear_fecha(request.form["salida"])
        personas = int(request.form["personas"])
        hotel_idx, hab_idx = request.form["habitacion"].split(":")
        habitacion = sistema.hoteles[int(hotel_idx)].habitaciones[int(hab_idx)]
        sistema.reservar(cliente, habitacion, entrada, salida, personas)  # R16: la reserva se formaliza al confirmar el pago
        flash("Reserva confirmada", "ok")
        return redirect(url_for("mis_reservas", cliente=cliente.nombre))
    return render_template("reservar.html", clientes=sistema.clientes, disponibles=None, sistema=sistema)


@app.route("/mis-reservas")
def mis_reservas():
    nombre_cliente = request.args.get("cliente", "")
    reservas = [r for r in sistema.reservas if r.cliente.nombre == nombre_cliente] if nombre_cliente else []
    hoy = date.today()
    return render_template("mis_reservas.html", clientes=sistema.clientes, nombre_cliente=nombre_cliente, reservas=reservas, hoy=hoy)


@app.route("/reservas/<int:id_reserva>/cancelar", methods=["POST"])
def cancelar(id_reserva):
    reserva = next(r for r in sistema.reservas if r.id == id_reserva)
    reembolso = sistema.cancelar(reserva, date.today())  # R17: cancelar y calcular el reembolso
    flash(f"Reserva cancelada. Reembolso: ${reembolso}", "ok")
    return redirect(url_for("mis_reservas", cliente=reserva.cliente.nombre))


@app.route("/reservas/<int:id_reserva>/calificar", methods=["POST"])
def calificar(id_reserva):
    reserva = next(r for r in sistema.reservas if r.id == id_reserva)
    puntuacion = int(request.form["puntuacion"])
    comentario = request.form["comentario"]
    reserva.habitacion.calificaciones.append(Calificacion(reserva.cliente, puntuacion, comentario))  # R18: calificación y comentario
    reserva.calificada = True
    flash("Gracias por tu calificación", "ok")
    return redirect(url_for("mis_reservas", cliente=reserva.cliente.nombre))


@app.route("/ofertas-temporadas")
def ofertas_temporadas():
    return render_template("ofertas_temporadas.html", sistema=sistema)


@app.route("/hoteles/<int:indice>/ofertas", methods=["POST"])
def agregar_oferta(indice):
    hotel = sistema.hoteles[indice]
    hotel.ofertas.append(request.form["descripcion"])  # R3: ofertas por temporada
    flash("Oferta agregada", "ok")
    return redirect(url_for("ofertas_temporadas"))


@app.route("/hoteles/<int:indice>/temporadas", methods=["POST"])
def agregar_temporada_hotel(indice):
    hotel = sistema.hoteles[indice]
    hotel.calendario_temporadas.append({
        "nombre": request.form["nombre"],
        "inicio": parsear_fecha(request.form["inicio"]),
        "fin": parsear_fecha(request.form["fin"]),
        "ajuste": int(request.form["ajuste"]),
    })  # R11: calendario propio de temporadas
    flash("Temporada agregada al hotel", "ok")
    return redirect(url_for("ofertas_temporadas"))


@app.route("/temporadas-regionales", methods=["POST"])
def agregar_temporada_regional():
    sistema.calendario_regional.append({
        "nombre": request.form["nombre"],
        "inicio": parsear_fecha(request.form["inicio"]),
        "fin": parsear_fecha(request.form["fin"]),
        "ajuste": int(request.form["ajuste"]),
    })  # R11: calendario regional de temporadas
    flash("Temporada regional agregada", "ok")
    return redirect(url_for("ofertas_temporadas"))


@app.route("/hoteles/<int:indice_hotel>/habitaciones/<int:indice_hab>")
def detalle_habitacion(indice_hotel, indice_hab):
    habitacion = sistema.hoteles[indice_hotel].habitaciones[indice_hab]
    return render_template("detalle_habitacion.html", h=habitacion)  # R15: detalle con calificación y comentarios


if __name__ == "__main__":
    app.run(debug=True)
