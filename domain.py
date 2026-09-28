from datetime import date

# Simplificación: la temporada de una reserva se calcula con la fecha de entrada y se aplica a toda la estancia.

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
    def __init__(self, id_reserva, cliente, habitacion, fecha_entrada, fecha_salida, personas, total):
        self.id = id_reserva
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
        reserva = Reserva(len(self.reservas) + 1, cliente, habitacion, fecha_entrada, fecha_salida, personas, total)
        habitacion.reservas.append(reserva)
        self.reservas.append(reserva)
        return reserva

    def cancelar(self, reserva, fecha_cancelacion):
        reembolso = reserva.habitacion.hotel.calcular_reembolso(reserva.total, reserva.fecha_entrada, fecha_cancelacion)  # R17
        reserva.estado = "cancelada"
        return reembolso


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
