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
