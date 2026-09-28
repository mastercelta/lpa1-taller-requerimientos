from datetime import date

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

# Simplificación: la temporada de una reserva se calcula con la fecha de entrada y se aplica a toda la estancia.

console = Console()

CATEGORIAS = ["silver", "gold", "platinum"]


class Calificacion:
    def __init__(self, cliente, puntuacion, comentario):
        self.cliente = cliente
        self.puntuacion = puntuacion
        self.comentario = comentario


class Cliente:
    def __init__(self, nombre, telefono, correo, direccion):  # R13: datos del cliente
        self.nombre = nombre
        self.telefono = telefono
        self.correo = correo
        self.direccion = direccion


class Reserva:
    def __init__(self, cliente, habitacion, fecha_entrada, fecha_salida, personas, total):
        self.cliente = cliente
        self.habitacion = habitacion
        self.fecha_entrada = fecha_entrada
        self.fecha_salida = fecha_salida
        self.personas = personas
        self.total = total
        self.calificada = False
        self.estado = "confirmada"  # R17: una reserva puede cancelarse


class Habitacion:
    def __init__(self, tipo, descripcion, precio, servicios, capacidad, fotos="", recargo_por_persona=0, categoria="silver"):  # R6: datos de la habitación, R2: fotos
        self.tipo = tipo
        self.descripcion = descripcion
        self.precio = precio
        self.servicios = servicios
        self.capacidad = capacidad
        self.fotos = fotos
        self.recargo_por_persona = recargo_por_persona
        self.categoria = categoria  # silver, gold o platinum
        self.activa = True  # R7: estado de la habitación
        self.hotel = None
        self.reservas = []
        self.calificaciones = []

    def esta_disponible(self, fecha_entrada, fecha_salida):
        for reserva in self.reservas:  # R12: calendario de fechas reservadas
            if reserva.estado == "confirmada" and fecha_entrada < reserva.fecha_salida and fecha_salida > reserva.fecha_entrada:
                return False
        return True

    def calcular_precio_por_noche(self, personas, fecha, sistema):
        precio = self.precio + max(0, personas - 1) * self.recargo_por_persona  # R9: recargo por persona adicional
        ajuste = self.hotel.obtener_ajuste_temporada(fecha, sistema)  # R10, R11: ajuste según temporada
        return round(precio * (1 + ajuste / 100))

    def calcular_total(self, fecha_entrada, fecha_salida, personas, sistema):
        # La temporada se calcula con la fecha de entrada y se aplica a toda la estancia
        noches = (fecha_salida - fecha_entrada).days
        return self.calcular_precio_por_noche(personas, fecha_entrada, sistema) * noches

    def calificacion_promedio(self):
        if not self.calificaciones:
            return None
        return sum(c.puntuacion for c in self.calificaciones) / len(self.calificaciones)  # R19: promedio de la habitación


class Hotel:
    def __init__(self, nombre, direccion, telefono, correo, ubicacion, servicios, fotos="",
                 servicios_adicionales="", condicion_pago="", dias_anticipacion=0, penalidad_cancelacion=0):
        # R1: datos del hotel, R2: servicios y fotos, R3: servicios adicionales, R4: pago y cancelación
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.correo = correo
        self.ubicacion = ubicacion
        self.servicios = servicios
        self.fotos = fotos
        self.servicios_adicionales = servicios_adicionales
        self.condicion_pago = condicion_pago
        self.dias_anticipacion = dias_anticipacion
        self.penalidad_cancelacion = penalidad_cancelacion
        self.activo = True  # R5: estado del hotel
        self.habitaciones = []
        self.ofertas = []  # R3: ofertas por temporada
        self.calendario_temporadas = []  # R11: calendario propio de temporadas

    def agregar_habitacion(self, habitacion):
        habitacion.hotel = self
        self.habitaciones.append(habitacion)

    def calificacion_promedio(self):
        puntuaciones = [c.puntuacion for h in self.habitaciones for c in h.calificaciones]
        if not puntuaciones:
            return None
        return sum(puntuaciones) / len(puntuaciones)  # R19: calificación general del hotel

    def obtener_ajuste_temporada(self, fecha, sistema):
        for temporada in self.calendario_temporadas:  # R11: el calendario propio manda sobre el regional
            if temporada["inicio"] <= fecha <= temporada["fin"]:
                return temporada["ajuste"]
        for temporada in sistema.calendario_regional:  # R11: calendario regional de temporadas
            if temporada["inicio"] <= fecha <= temporada["fin"]:
                return temporada["ajuste"]
        return 0

    def calcular_reembolso(self, monto, fecha_entrada, fecha_cancelacion):
        dias_restantes = (fecha_entrada - fecha_cancelacion).days
        if dias_restantes >= self.dias_anticipacion:  # R17: reembolso según la política de cancelación
            return monto
        return round(monto * (1 - self.penalidad_cancelacion / 100))


class SistemaReservas:
    def __init__(self):
        self.hoteles = []
        self.clientes = []
        self.reservas = []
        self.calendario_regional = []  # R11: calendario regional de temporadas

    def buscar_habitaciones(self, fecha_entrada=None, fecha_salida=None, ubicacion="", calificacion_minima=0, precio_maximo=0, categoria=""):
        resultados = []
        for hotel in self.hoteles:
            if not hotel.activo:  # R8: solo hoteles activos
                continue
            if ubicacion and ubicacion.lower() not in hotel.ubicacion.lower():  # R14: criterio de ubicación
                continue
            for habitacion in hotel.habitaciones:
                if not habitacion.activa:  # R8: solo habitaciones activas
                    continue
                if fecha_entrada and not habitacion.esta_disponible(fecha_entrada, fecha_salida):  # R14: criterio de fecha
                    continue
                promedio = habitacion.calificacion_promedio()
                if calificacion_minima and (promedio is None or promedio < calificacion_minima):  # R14: criterio de calificación
                    continue
                if precio_maximo and habitacion.precio > precio_maximo:  # R14: criterio de precio
                    continue
                if categoria and habitacion.categoria != categoria:  # criterio de categoría (silver, gold, platinum)
                    continue
                resultados.append(habitacion)
        return resultados

    def reservar(self, cliente, habitacion, fecha_entrada, fecha_salida, personas):
        total = habitacion.calcular_total(fecha_entrada, fecha_salida, personas, self)
        reserva = Reserva(cliente, habitacion, fecha_entrada, fecha_salida, personas, total)
        habitacion.reservas.append(reserva)
        self.reservas.append(reserva)
        return reserva

    def cancelar(self, reserva, fecha_cancelacion):
        reembolso = reserva.habitacion.hotel.calcular_reembolso(reserva.total, reserva.fecha_entrada, fecha_cancelacion)  # R17
        reserva.estado = "cancelada"
        return reembolso


def pedir(mensaje):
    valor = ""
    while not valor.strip():
        valor = Prompt.ask(mensaje)
    return valor.strip()


def pedir_fecha(mensaje, opcional=False):
    while True:
        sufijo = ", vacío para omitir" if opcional else ""
        texto = Prompt.ask(f"{mensaje} (AAAA-MM-DD{sufijo})", default="", show_default=False).strip()
        if not texto and opcional:
            return None
        try:
            return date.fromisoformat(texto)
        except ValueError:
            console.print("[red]Fecha inválida, usa el formato AAAA-MM-DD[/red]")


def elegir(titulo, opciones):
    if not opciones:
        console.print("[red]No hay opciones disponibles[/red]")
        return None
    for numero, opcion in enumerate(opciones, 1):
        console.print(f"{numero}. {opcion}")
    numero = IntPrompt.ask(titulo, choices=[str(n) for n in range(1, len(opciones) + 1)])
    return numero - 1


def formato_calificacion(promedio):
    if promedio is None:
        return "Sin calificar"
    return f"{promedio:.1f}"


def mostrar_habitaciones(habitaciones, sistema, fecha=None, personas=1):
    fecha = fecha or date.today()
    tabla = Table(title="Habitaciones")
    for columna in ["Hotel", "Ubicación", "Tipo", "Categoría", "Precio por noche", "Capacidad", "Calificación"]:
        tabla.add_column(columna)
    for h in habitaciones:
        precio = h.calcular_precio_por_noche(personas, fecha, sistema)
        tabla.add_row(h.hotel.nombre, h.hotel.ubicacion, h.tipo, h.categoria, f"${precio}", str(h.capacidad), formato_calificacion(h.calificacion_promedio()))
    console.print(tabla)
    for h in habitaciones:  # R15: detalle de la habitación con calificación y comentarios
        console.print(f"\n[bold]{h.hotel.nombre} - {h.tipo}[/bold]")
        console.print(f"Descripción: {h.descripcion}")
        console.print(f"Servicios incluidos: {h.servicios}")
        if h.fotos:
            console.print(f"Fotos: {h.fotos}")  # R15: fotos de la habitación
        for c in h.calificaciones:
            console.print(f"  {c.cliente.nombre} ({c.puntuacion}/5): {c.comentario}")


def registrar_hotel(sistema):
    hotel = Hotel(
        pedir("Nombre"),
        pedir("Dirección"),
        pedir("Teléfono"),
        pedir("Correo electrónico"),
        pedir("Ubicación (ciudad o zona)"),
        pedir("Servicios (ej: restaurante, piscina, gimnasio)"),
        Prompt.ask("Fotos (nombres de archivo separados por coma, opcional)", default="", show_default=False),
        Prompt.ask("Servicios adicionales (ej: estacionamiento, coworking, opcional)", default="", show_default=False),
        pedir("Condición de pago (ej: anticipado, al llegar)"),
        IntPrompt.ask("Días de anticipación para cancelar sin penalidad"),
        IntPrompt.ask("Penalidad por cancelación tardía (%)"),
    )
    sistema.hoteles.append(hotel)  # R1: registro del hotel
    console.print("[green]Hotel registrado[/green]")


def registrar_habitacion(sistema):
    numero = elegir("Hotel", [h.nombre for h in sistema.hoteles])
    if numero is None:
        return
    indice_categoria = elegir("Categoría", CATEGORIAS)
    if indice_categoria is None:
        return
    habitacion = Habitacion(
        pedir("Tipo (ej: sencilla, doble, suite)"),
        pedir("Descripción"),
        IntPrompt.ask("Precio por noche"),
        pedir("Servicios incluidos"),
        IntPrompt.ask("Capacidad máxima (personas)"),
        Prompt.ask("Fotos (nombres de archivo separados por coma, opcional)", default="", show_default=False),
        IntPrompt.ask("Recargo por persona adicional (0 si no aplica)", default=0),
        CATEGORIAS[indice_categoria],
    )
    sistema.hoteles[numero].agregar_habitacion(habitacion)  # R6: registro de la habitación
    console.print("[green]Habitación registrada[/green]")


def registrar_cliente(sistema):
    cliente = Cliente(pedir("Nombre completo"), pedir("Teléfono"), pedir("Correo electrónico"), pedir("Dirección"))
    sistema.clientes.append(cliente)  # R13: registro del cliente
    console.print("[green]Cliente registrado[/green]")


def ver_hoteles(sistema):
    tabla = Table(title="Hoteles y habitaciones")
    for columna in ["Hotel", "Ubicación", "Estado", "Calificación", "Habitación", "Categoría", "Estado hab.", "Precio", "Capacidad"]:
        tabla.add_column(columna)
    for hotel in sistema.hoteles:
        estado = "activo" if hotel.activo else "inactivo"
        calificacion = formato_calificacion(hotel.calificacion_promedio())
        if not hotel.habitaciones:
            tabla.add_row(hotel.nombre, hotel.ubicacion, estado, calificacion, "-", "-", "-", "-", "-")
        for h in hotel.habitaciones:
            estado_hab = "activa" if h.activa else "inactiva"
            tabla.add_row(hotel.nombre, hotel.ubicacion, estado, calificacion, h.tipo, h.categoria, estado_hab, f"${h.precio}", str(h.capacidad))
    console.print(tabla)
    for hotel in sistema.hoteles:
        if hotel.fotos or hotel.ofertas or hotel.servicios_adicionales:
            console.print(f"\n[bold]{hotel.nombre}[/bold]")
            if hotel.fotos:
                console.print(f"Fotos: {hotel.fotos}")  # R2: fotos del hotel
            if hotel.servicios_adicionales:
                console.print(f"Servicios adicionales: {hotel.servicios_adicionales}")  # R3
            for oferta in hotel.ofertas:
                console.print(f"Oferta: {oferta}")  # R3: ofertas por temporada


def cambiar_estado_hotel(sistema):
    numero = elegir("Hotel", [f"{h.nombre} ({'activo' if h.activo else 'inactivo'})" for h in sistema.hoteles])
    if numero is None:
        return
    hotel = sistema.hoteles[numero]
    hotel.activo = not hotel.activo  # R5: activar o desactivar el hotel
    console.print(f"{hotel.nombre} ahora está {'activo' if hotel.activo else 'inactivo'}")


def cambiar_estado_habitacion(sistema):
    numero = elegir("Hotel", [h.nombre for h in sistema.hoteles])
    if numero is None:
        return
    hotel = sistema.hoteles[numero]
    numero = elegir("Habitación", [f"{h.tipo} ({'activa' if h.activa else 'inactiva'})" for h in hotel.habitaciones])
    if numero is None:
        return
    habitacion = hotel.habitaciones[numero]
    habitacion.activa = not habitacion.activa  # R7: activar o desactivar la habitación
    console.print(f"{habitacion.tipo} ahora está {'activa' if habitacion.activa else 'inactiva'}")


def agregar_oferta(sistema):
    numero = elegir("Hotel", [h.nombre for h in sistema.hoteles])
    if numero is None:
        return
    hotel = sistema.hoteles[numero]
    hotel.ofertas.append(pedir("Descripción de la oferta (ej: 20% de descuento en temporada baja)"))  # R3
    console.print("[green]Oferta agregada[/green]")


def agregar_temporada_hotel(sistema):
    numero = elegir("Hotel", [h.nombre for h in sistema.hoteles])
    if numero is None:
        return
    hotel = sistema.hoteles[numero]
    nombre = pedir("Nombre de la temporada (ej: temporada alta)")
    inicio = pedir_fecha("Fecha de inicio")
    fin = pedir_fecha("Fecha de fin")
    ajuste = IntPrompt.ask("Ajuste sobre el precio, en % (positivo sube, negativo baja)")
    hotel.calendario_temporadas.append({"nombre": nombre, "inicio": inicio, "fin": fin, "ajuste": ajuste})  # R11: calendario propio
    console.print("[green]Temporada agregada al hotel[/green]")


def agregar_temporada_regional(sistema):
    nombre = pedir("Nombre de la temporada (ej: vacaciones de mitad de año)")
    inicio = pedir_fecha("Fecha de inicio")
    fin = pedir_fecha("Fecha de fin")
    ajuste = IntPrompt.ask("Ajuste sobre el precio, en % (positivo sube, negativo baja)")
    sistema.calendario_regional.append({"nombre": nombre, "inicio": inicio, "fin": fin, "ajuste": ajuste})  # R11: calendario regional
    console.print("[green]Temporada regional agregada[/green]")


def ver_ofertas_y_temporadas(sistema):
    if sistema.calendario_regional:
        tabla = Table(title="Temporadas regionales")
        for columna in ["Temporada", "Inicio", "Fin", "Ajuste"]:
            tabla.add_column(columna)
        for t in sistema.calendario_regional:
            tabla.add_row(t["nombre"], str(t["inicio"]), str(t["fin"]), f"{t['ajuste']}%")
        console.print(tabla)
    else:
        console.print("[yellow]No hay temporadas regionales registradas[/yellow]")

    for hotel in sistema.hoteles:
        if not hotel.ofertas and not hotel.calendario_temporadas:
            continue
        console.print(f"\n[bold]{hotel.nombre}[/bold]")
        if hotel.ofertas:
            for oferta in hotel.ofertas:
                console.print(f"  Oferta: {oferta}")
        if hotel.calendario_temporadas:
            tabla = Table(title=f"Temporadas de {hotel.nombre}")
            for columna in ["Temporada", "Inicio", "Fin", "Ajuste"]:
                tabla.add_column(columna)
            for t in hotel.calendario_temporadas:
                tabla.add_row(t["nombre"], str(t["inicio"]), str(t["fin"]), f"{t['ajuste']}%")
            console.print(tabla)


def buscar(sistema):
    entrada = pedir_fecha("Fecha de entrada", opcional=True)
    salida = None
    if entrada:
        salida = pedir_fecha("Fecha de salida")
        if salida <= entrada:
            console.print("[red]La salida debe ser posterior a la entrada[/red]")
            return
    ubicacion = Prompt.ask("Ubicación (vacío para omitir)", default="", show_default=False)
    calificacion = IntPrompt.ask("Calificación mínima de 1 a 5 (0 para omitir)", default=0)
    precio = IntPrompt.ask("Precio máximo por noche (0 para omitir)", default=0)
    categoria = Prompt.ask("Categoría (silver, gold, platinum; vacío para omitir)", default="", show_default=False)
    resultados = sistema.buscar_habitaciones(entrada, salida, ubicacion, calificacion, precio, categoria)
    if not resultados:
        console.print("[yellow]No se encontraron habitaciones[/yellow]")
        return
    mostrar_habitaciones(resultados, sistema, entrada)


def reservar(sistema):
    numero = elegir("Cliente", [c.nombre for c in sistema.clientes])
    if numero is None:
        return
    cliente = sistema.clientes[numero]
    entrada = pedir_fecha("Fecha de entrada")
    salida = pedir_fecha("Fecha de salida")
    if salida <= entrada:
        console.print("[red]La salida debe ser posterior a la entrada[/red]")
        return
    personas = IntPrompt.ask("Cantidad de personas")
    disponibles = [h for h in sistema.buscar_habitaciones(entrada, salida) if h.capacidad >= personas]  # R9: la capacidad no se puede exceder
    numero = elegir(
        "Habitación",
        [f"{h.hotel.nombre} - {h.tipo} (${h.calcular_precio_por_noche(personas, entrada, sistema)} por noche, capacidad {h.capacidad})" for h in disponibles],
    )
    if numero is None:
        return
    habitacion = disponibles[numero]
    console.print(f"Total a pagar: ${habitacion.calcular_total(entrada, salida, personas, sistema)}")
    if Confirm.ask("¿Confirmas el pago?"):  # R16: la reserva se formaliza al confirmar el pago
        sistema.reservar(cliente, habitacion, entrada, salida, personas)
        console.print("[green]Reserva confirmada[/green]")
    else:
        console.print("[yellow]Pago no confirmado, no se hizo la reserva[/yellow]")


def cancelar_reserva(sistema):
    numero = elegir("Cliente", [c.nombre for c in sistema.clientes])
    if numero is None:
        return
    cliente = sistema.clientes[numero]
    activas = [r for r in sistema.reservas if r.cliente is cliente and r.estado == "confirmada"]
    if not activas:
        console.print("[yellow]No tienes reservas activas[/yellow]")
        return
    numero = elegir("Reserva a cancelar", [f"{r.habitacion.hotel.nombre} - {r.habitacion.tipo} ({r.fecha_entrada} a {r.fecha_salida}), total ${r.total}" for r in activas])
    if numero is None:
        return
    reserva = activas[numero]
    if not Confirm.ask("¿Confirmas la cancelación?"):
        return
    reembolso = sistema.cancelar(reserva, date.today())  # R17: cancelar y calcular el reembolso
    console.print(f"[green]Reserva cancelada. Reembolso: ${reembolso}[/green]")


def calificar(sistema):
    numero = elegir("Cliente", [c.nombre for c in sistema.clientes])
    if numero is None:
        return
    cliente = sistema.clientes[numero]
    hoy = date.today()
    pendientes = [r for r in sistema.reservas if r.cliente is cliente and r.estado == "confirmada" and r.fecha_salida <= hoy and not r.calificada]  # R18: solo estancias ya terminadas
    if not pendientes:
        console.print("[yellow]No tienes estancias terminadas para calificar[/yellow]")
        return
    numero = elegir("Estancia a calificar", [f"{r.habitacion.hotel.nombre} - {r.habitacion.tipo} ({r.fecha_entrada} a {r.fecha_salida})" for r in pendientes])
    reserva = pendientes[numero]
    puntuacion = IntPrompt.ask("Puntuación", choices=["1", "2", "3", "4", "5"])
    comentario = pedir("Comentario")
    reserva.habitacion.calificaciones.append(Calificacion(cliente, puntuacion, comentario))  # R18: calificación y comentario
    reserva.calificada = True
    console.print("[green]Gracias por tu calificación[/green]")


def cargar_datos_iniciales(sistema):
    sol = Hotel(
        "Hotel Sol Caribe", "Calle 1 # 2-3", "3001112222", "sol@hotel.com", "Cartagena", "restaurante, piscina",
        "fachada.jpg, piscina.jpg", "estacionamiento", "50% anticipado, 50% al llegar", 3, 30,
    )
    sol.agregar_habitacion(Habitacion("Sencilla", "Cama sencilla con vista al mar", 120000, "wifi, desayuno", 1, "sencilla.jpg", 0, "silver"))
    sol.agregar_habitacion(Habitacion("Doble", "Dos camas dobles", 200000, "wifi, desayuno, aire acondicionado", 4, "doble.jpg", 30000, "gold"))
    sol.ofertas.append("20% de descuento en temporada baja")
    sol.calendario_temporadas.append({"nombre": "temporada alta", "inicio": date(2026, 12, 15), "fin": date(2027, 1, 15), "ajuste": 25})
    andino = Hotel(
        "Hotel Andino", "Carrera 4 # 5-6", "3003334444", "andino@hotel.com", "Medellín", "gimnasio, coworking",
        "", "coworking", "pago al llegar", 1, 50,
    )
    andino.agregar_habitacion(Habitacion("Suite", "Suite con sala privada", 350000, "wifi, minibar, jacuzzi", 3, "", 40000, "platinum"))
    sistema.hoteles.extend([sol, andino])
    sistema.calendario_regional.append({"nombre": "vacaciones de fin de año", "inicio": date(2026, 12, 20), "fin": date(2027, 1, 10), "ajuste": 15})
    ana = Cliente("Ana Pérez", "3005556666", "ana@correo.com", "Calle 7 # 8-9")
    sistema.clientes.append(ana)
    sistema.reservar(ana, sol.habitaciones[0], date(2026, 1, 10), date(2026, 1, 12), 1)


def main():
    sistema = SistemaReservas()
    cargar_datos_iniciales(sistema)
    opciones = {
        "1": ("Registrar hotel", registrar_hotel),
        "2": ("Registrar habitación", registrar_habitacion),
        "3": ("Registrar cliente", registrar_cliente),
        "4": ("Ver hoteles y habitaciones", ver_hoteles),
        "5": ("Activar o desactivar un hotel", cambiar_estado_hotel),
        "6": ("Activar o desactivar una habitación", cambiar_estado_habitacion),
        "7": ("Buscar habitaciones", buscar),
        "8": ("Reservar", reservar),
        "9": ("Calificar una estancia", calificar),
        "10": ("Agregar oferta a un hotel", agregar_oferta),
        "11": ("Agregar temporada a un hotel", agregar_temporada_hotel),
        "12": ("Agregar temporada regional", agregar_temporada_regional),
        "13": ("Cancelar una reserva", cancelar_reserva),
        "14": ("Ver ofertas y temporadas", ver_ofertas_y_temporadas),
    }
    while True:
        console.print("\n[bold]Sistema de reservas[/bold]")
        for clave, (texto, _) in opciones.items():
            console.print(f"{clave}. {texto}")
        console.print("0. Salir")
        opcion = Prompt.ask("Opción", choices=[*opciones, "0"])
        if opcion == "0":
            break
        opciones[opcion][1](sistema)


if __name__ == "__main__":
    main()
