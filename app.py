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
