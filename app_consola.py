from datetime import date

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from domain import CATEGORIAS, Calificacion, Cliente, Habitacion, Hotel, SistemaReservas, cargar_datos_iniciales

console = Console()

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
