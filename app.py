from datetime import date

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

# No implementados: R3, R4, R10, R11, R17. Las fotos de R2, R6 y R15 no se manejan en consola.

console = Console()


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
    def __init__(self, cliente, habitacion, fecha_entrada, fecha_salida, personas):
        self.cliente = cliente
        self.habitacion = habitacion
        self.fecha_entrada = fecha_entrada
        self.fecha_salida = fecha_salida
        self.personas = personas
        self.total = habitacion.calcular_total(fecha_entrada, fecha_salida)
        self.calificada = False


class Habitacion:
    def __init__(self, tipo, descripcion, precio, servicios, capacidad):  # R6: datos de la habitación
        self.tipo = tipo
        self.descripcion = descripcion
        self.precio = precio
        self.servicios = servicios
        self.capacidad = capacidad
        self.activa = True  # R7: estado de la habitación
        self.hotel = None
        self.reservas = []
        self.calificaciones = []

    def esta_disponible(self, fecha_entrada, fecha_salida):
        for reserva in self.reservas:  # R12: calendario de fechas reservadas
            if fecha_entrada < reserva.fecha_salida and fecha_salida > reserva.fecha_entrada:
                return False
        return True

    def calcular_total(self, fecha_entrada, fecha_salida):
        return (fecha_salida - fecha_entrada).days * self.precio

    def calificacion_promedio(self):
        if not self.calificaciones:
            return None
        return sum(c.puntuacion for c in self.calificaciones) / len(self.calificaciones)  # R19: promedio de la habitación


class Hotel:
    def __init__(self, nombre, direccion, telefono, correo, ubicacion, servicios):  # R1: datos del hotel, R2: servicios
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.correo = correo
        self.ubicacion = ubicacion
        self.servicios = servicios
        self.activo = True  # R5: estado del hotel
        self.habitaciones = []

    def agregar_habitacion(self, habitacion):
        habitacion.hotel = self
        self.habitaciones.append(habitacion)

    def calificacion_promedio(self):
        puntuaciones = [c.puntuacion for h in self.habitaciones for c in h.calificaciones]
        if not puntuaciones:
            return None
        return sum(puntuaciones) / len(puntuaciones)  # R19: calificación general del hotel


class SistemaReservas:
    def __init__(self):
        self.hoteles = []
        self.clientes = []
        self.reservas = []

    def buscar_habitaciones(self, fecha_entrada=None, fecha_salida=None, ubicacion="", calificacion_minima=0, precio_maximo=0):
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
                resultados.append(habitacion)
        return resultados

    def reservar(self, cliente, habitacion, fecha_entrada, fecha_salida, personas):
        reserva = Reserva(cliente, habitacion, fecha_entrada, fecha_salida, personas)
        habitacion.reservas.append(reserva)
        self.reservas.append(reserva)
        return reserva


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


def mostrar_habitaciones(habitaciones):
    tabla = Table(title="Habitaciones")
    for columna in ["Hotel", "Ubicación", "Tipo", "Precio por noche", "Capacidad", "Calificación"]:
        tabla.add_column(columna)
    for h in habitaciones:
        tabla.add_row(h.hotel.nombre, h.hotel.ubicacion, h.tipo, f"${h.precio}", str(h.capacidad), formato_calificacion(h.calificacion_promedio()))
    console.print(tabla)
    for h in habitaciones:  # R15: detalle de la habitación con calificación y comentarios
        console.print(f"\n[bold]{h.hotel.nombre} - {h.tipo}[/bold]")
        console.print(f"Descripción: {h.descripcion}")
        console.print(f"Servicios incluidos: {h.servicios}")
        for c in h.calificaciones:
            console.print(f"  {c.cliente.nombre} ({c.puntuacion}/5): {c.comentario}")
