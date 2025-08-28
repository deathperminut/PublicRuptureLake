import os
import io
import datetime
import numpy as np
import shutil
from io import BytesIO
import requests
from functools import wraps

from flask import Flask, request, send_file, render_template, make_response, redirect, url_for

from functions.users import loginUserV2, createUser, getUsers, updateUserState, updateUserPassword, getUserById
from functions.events import createEvent, updateEvent, getSpecificEvent, getEvents
from functions.modelos import *
import pandas as pd
import numpy as np

def init_web_routes(app):
    """Inicializar rutas web"""
    
    @app.route('/')
    def home():
        if request.cookies.get("ingreso") == "true":
            return redirect("/Perfil")
        return redirect("/Inicio")

    @app.route('/Inicio', methods=['POST', 'GET'])
    def salir():
        if request.method == "POST":
            resp = make_response(render_template('index.html', mostrar="true"))
        else:
            resp = make_response(render_template('index.html', mostrar="false"))
        
        if request.cookies.get("ingreso") == "true":
            resp.set_cookie('ingreso', 'false')
            resp.set_cookie('email', '')
            resp.set_cookie('nombre1', '')
            resp.set_cookie('nombre2', '')
            resp.set_cookie('empresa', '')
            resp.set_cookie('tipo_user', '')
        return resp

    @app.route('/Ingresar', methods=['POST'])
    def iniciar():
        identification = request.form.get('identification')
        password = request.form.get('password')
        
        object_ = {
            "identification": identification,
            "password": password
        }
        
        result = loginUserV2(object_)
        
        if result['status'] == 'Registro éxitoso':
            resp = make_response(redirect("/Perfil"))
            resp.set_cookie('ingreso', 'true')
            resp.set_cookie('email', result['email'])
            resp.set_cookie('nombre1', result['first_name'])
            resp.set_cookie('nombre2', result['last_name'])
            resp.set_cookie('empresa', 'Efigas S.A')
            resp.set_cookie('tipo_user', 'worker')  # Mantener para compatibilidad
            resp.set_cookie('rol', result.get('rol', 'worker'))  # Nuevo: rol del usuario
            return resp
        else:
            # Error en login - redirigir a inicio sin mensaje
            resp = make_response(redirect("/Inicio", code=307))
            return resp

    @app.route('/Perfil')
    def perfil():
        resp = make_response(render_template('principal.html'))
        resp.set_cookie('nuevo', '')
        return resp

    @app.route('/Registrarse', methods=['GET'])
    def nuevo_usuario():
        resp = make_response(render_template('crear_usuario.html', existe="false"))
        return resp

    @app.route('/Registrar', methods=['POST'])
    def guardar_usuario():
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        identification = request.form.get("identification")
        password = request.form.get("password")
        
        object_ = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "identification": identification,
            "password": password,
            "state": True,
            "rol": "worker"
        }
        
        response = createUser(object_)
        
        if response['status'] == 'Usuario creado con éxito':
            return redirect(url_for('salir'))
        else:
            # Error en registro - redirigir a registro sin mensaje
            return redirect(url_for('nuevo_usuario'))


    @app.route('/NuevoEvento', methods=['POST'])
    def nuevo():
        resp = make_response(render_template('evento.html'))
        resp.set_cookie('guardado', 'false')
        return resp

    @app.route('/CargarBuscar', methods=['POST', 'GET'])
    def cargarBuscar():
        resp = make_response(redirect('/BuscarEvento'))
        resp.set_cookie('orden', '')
        return resp

    @app.route('/BuscarEvento', methods=['POST', 'GET'])
    def renderBuscar():
        resp = make_response(render_template('buscar.html'))
        return resp

    @app.route('/Buscar', methods=['POST'])
    def buscar():
        orden = request.form.get('orden')
        objeto_ = {'orden': orden}
        
        result = getSpecificEvent(objeto_)
        
        if result['status'] == 'Si hay elemento':
            resp = make_response(redirect('/Reporte', code=307))
            resp.set_cookie('orden', orden)
            return resp
        else:
            resp = make_response(redirect('/BuscarEvento'))
            resp.set_cookie('orden', '-1')
            return resp

    @app.route('/Reporte', methods=['POST'])
    def reporte():
        orden = request.cookies.get("orden")
        objeto_ = {'orden': orden}
        
        response = getSpecificEvent(objeto_)
        
        if response['status'] == 'Si hay elemento':
            fila = response['data'][0]
            
            # Procesar fecha de reporte (hora_reg)
            fecha_reg = datetime.datetime.strptime(fila['hora_reg'], '%Y-%m-%d %H:%M')
            
            # Procesar fecha de inicio
            fecha_inicio = datetime.datetime.strptime(fila['inicio'], '%Y-%m-%d %H:%M')
            
            # Procesar ubicación
            ubicacion_coords = fila['ubicacion'].split(',')
            latitud = float(ubicacion_coords[0])
            longitud = float(ubicacion_coords[1])
            
            # Procesar duración
            duracion_segundos = fila['duracion']
            horas = int(duracion_segundos // 3600)
            minutos = int((duracion_segundos % 3600) // 60)
            
            # Preparar datos para template
            template_data = {
                'orden': fila['orden'],
                'dia_reg': fecha_reg.day,
                'mes_reg': fecha_reg.month, 
                'año_reg': fecha_reg.year,
                'dia_inicio': fecha_inicio.day,
                'mes_inicio': fecha_inicio.month,
                'año_inicio': fecha_inicio.year,
                'latitud': latitud,
                'longitud': longitud,
                'volumen': round(fila['volumen'], 2),
                'Volumenfugado': round(fila['volumen_fuga'], 2),
                'vol_muerto': round(fila['volumen_muerto'], 2),
                'presion_atmos': round(fila['presion_atmos'], 2),
                'flujo': round(fila['flujo'], 2),
                'horas': horas,
                'minutos': minutos,
                'area': round(fila['area'], 2),
                'direccion': "Unidireccional" if fila['direccion'] == "uni" else "Bidireccional",
                'forma': fila['forma'].title(),
                'presion_tube': round(fila['presion'], 2),
                'Tlargo': fila['dist_tube'],
                'TlargoUni': fila['dist_tube_uni'],
                'Subte': "Subterráneo" if fila['subte'] == "sub" else "Aéreo",
                'aprobado': fila['aprobado']
            }
            
            resp = make_response(render_template('reporte.html', **template_data))
            return resp
        else:
            resp = make_response(redirect('/BuscarEvento'))
            resp.set_cookie('orden', '-1')
            return resp

    @app.route('/Descargar', methods=['POST'])
    def downloadFile():
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return redirect('/BuscarEvento')
            
        response = getEvents()
        data = list(response)
        
        # Convertir ObjectIds a strings
        for item in data:
            item['_id'] = str(item['_id'])
        
        df = pd.DataFrame(data)
        buffer = BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Datos')
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='datos.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # Rutas adicionales que faltan
    @app.route('/Resultados', methods=['POST'])
    def resultados():
        # Se obtienen todas las entradas (lógica exacta de rl.py)
        orden = request.form.get('orden')
        ubicacion = request.form.get('ubicacion')
        presionTub = request.form.get('presion')
        presionUni = request.form.get('presionUni')
        subte = request.form.get('subte')
        equi = request.form.get('diameEqui')
        escape = request.form.get('escape')
        direccion = request.form.get("Flujo")
        forma = request.form.get('Forma')
        Fdiametro = request.form.get('DiameFuga')
        longitud = request.form.get('LongiFuga')
        Alto = request.form.get('Altofuga')
        FdiametroUni = request.form.get('DiameFugaUni')
        longitudUni = request.form.get('LongiFugaUni')
        AltoUni = request.form.get('AltofugaUni')
        Tlargo = request.form.get("DistTube")
        TlargoUni = request.form.get("DistTubeUni")
        Tlargo2 = request.form.get("DistTube2")
        TlargoUni2 = request.form.get("DistTubeUni2")
        Tdiametro = request.form.get('DiameTube')
        tiempoInicio = request.form.get('tiempoInicio')
        tiempoFin = request.form.get('tiempoFin')
        
        try:
            # Se castean los valores porque a numpy no le gusta usar cadenas
            presionTub = float(presionTub)
            Fdiametro = float(Fdiametro) if Fdiametro != "" else 0
            Tlargo = float(Tlargo) if Tlargo != "" else 0
            Tlargo2 = float(Tlargo2) if Tlargo2 != "" else 0
            longitud = float(longitud) if longitud != "" else 0
            Tdiametro = float(Tdiametro)
            
            # Aplicar los diametros equivalentes
            if equi == 'on':
                Fuga_diame = convertir("in", "mm", diametro_equi(Tdiametro, escape))
            else:
                Fuga_diame = convertir(FdiametroUni, "mm", Fdiametro)
            
            # Convertir a mm y m para que concuerden las unidades de diametro  
            diametro_int = diametro_interno(Tdiametro)
            material = diametro_interno1(Tdiametro)
            Unidades = diametro_interno2(Tdiametro)
            Tlargo = convertir(TlargoUni, "m", Tlargo)
            Tlargo2 = convertir(TlargoUni2, "m", Tlargo2)
            longitud = convertir(longitudUni, "mm", longitud)
            
            TubeLargo = Tlargo + Tlargo2
            
            # Separar los componentes de la ubicacion
            lati = float(ubicacion.split(",")[0])
            longi = float(ubicacion.split(",")[1])
            
            # Convertir a bar para que concuerden las unidades de presion
            presionTub = convertir(presionUni, "bar", presionTub)
            
            # Traer presion atmos para obtener presion total
            presionAtmos = presion_atmos(elevacion(lati, longi))
            
            # Se calcula la duracion de la fuga
            tiempoInicio = datetime.datetime(int(tiempoInicio[0:4]), int(tiempoInicio[5:7]), int(tiempoInicio[8:10]), int(tiempoInicio[11:13]), int(tiempoInicio[14:16]), 0, 0)
            tiempoFin = datetime.datetime(int(tiempoFin[0:4]), int(tiempoFin[5:7]), int(tiempoFin[8:10]), int(tiempoFin[11:13]), int(tiempoFin[14:16]), 0, 0)
            duracion = tiempoFin - tiempoInicio
            duracion = duracion.total_seconds()
            horas = int(duracion // 3600)
            horasQ = duracion % 3600
            minutos = int(horasQ // 60)
            duracion2 = duracion / 3600
            
            # Si la ruptura es total se calculan los valores de una ruptura circular con el diametro de la tubería
            if forma == "total":
                Fuga_diame = diametro_int
                area = calc_area("circ", Fuga_diame, 0, 0, 0)
                perimetro = calc_peri("circ", Fuga_diame, 0, 0, 0)
            # Si la ruptura es recta se calcula el diametro hidraulico
            elif forma == "recta":
                if equi == 'on':
                    area = calc_area("circ", Fuga_diame, 0, 0, 0)
                    perimetro = calc_peri("circ", Fuga_diame, 0, 0, 0)
                else:
                    area = calc_area("recta", 0, 0, 0, longitud)
                    perimetro = calc_peri("recta", 0, 0, 0, longitud)
                    Fuga_diame = diametro_hidraulico(area, perimetro, diametro_int)
            else:
                area = calc_area(forma, Fuga_diame, 0, 0, longitud)
                perimetro = calc_peri(forma, Fuga_diame, 0, 0, longitud)
            
            if forma == "rect" or forma == "recta":
                coef_flujo = 0.9
            elif forma == "tria":
                coef_flujo = 0.95
            else:
                coef_flujo = 1
            
            if forma == "recta":
                forma = "Recta"
                medida = longitud
                medidaUni = longitudUni
            elif forma == "total":
                forma = "Total"
                medida = ""
                medidaUni = ""
            else:
                forma = "Circular"
                medida = Fdiametro
                medidaUni = FdiametroUni
            
            # NUEVO METODO DE CALCULO DEL FLUJO (copiado exacto de rl.py)
            R_vals = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
            R_real = 1.0 if forma == "Total" else Fuga_diame / diametro_int
            Q_vals = []
            
            if diametro_int > 76.2:
                d1 = 50.8
                d2 = 76.2
                Q1_vals = []
                Q2_vals = []
                for R in R_vals:
                    R_actual = 1.0 if forma == "Total" else R
                    Q1_iter = []
                    Q2_iter = []

                    for d_tube_i, Q_iter in zip([d1, d2], [Q1_iter, Q2_iter]):
                        L0 = obtener_L0(R_actual, material)
                        if TubeLargo <= L0:
                            Q0 = modelo_utpSuper(Fuga_diame, d_tube_i, presionTub, presionAtmos, subte, direccion, forma, TubeLargo, material, R_actual)
                            Q_iter.append(Q0)
                        else:
                            Q0 = modelo_utpSuper(Fuga_diame, d_tube_i, presionTub, presionAtmos, subte, direccion, forma, L0, material, R_actual)
                            Q_iter.append(Q0)
                            for L in range(L0 + 1, int(TubeLargo) + 1):
                                a = alpha(L, R_actual, material)
                                Qi = Q_iter[-1] if a is None else Q_iter[-1] * (1 - a)
                                Q_iter.append(Qi)

                    Q1_vals.append(Q1_iter[-1])
                    Q2_vals.append(Q2_iter[-1])

                Q1_interp = np.interp(R_real, R_vals, Q1_vals)
                Q2_interp = np.interp(R_real, R_vals, Q2_vals)
                Q_extrap = Q1_interp + (Q2_interp - Q1_interp) * ((diametro_int - d1) / (d2 - d1))
                flujo = Q_extrap
            else:
                for R in R_vals:
                    R_actual = 1.0 if forma == "Total" else R
                    Q_iter = []
                    L0 = obtener_L0(R_actual, material)

                    if TubeLargo <= L0:
                        Q0 = modelo_utpSuper(Fuga_diame, diametro_int, presionTub, presionAtmos, subte, direccion, forma, TubeLargo, material, R_actual)
                        Q_iter.append(Q0)
                    else:
                        Q0 = modelo_utpSuper(Fuga_diame, diametro_int, presionTub, presionAtmos, subte, direccion, forma, L0, material, R_actual)
                        Q_iter.append(Q0)
                        for L in range(L0 + 1, int(TubeLargo) + 1):
                            a = alpha(L, R_actual, material)
                            Qi = Q_iter[-1] if a is None else Q_iter[-1] * (1 - a)
                            Q_iter.append(Qi)

                    Q_vals.append(Q_iter[-1])

                Q_final = np.interp(R_real, R_vals, Q_vals)
                flujo = Q_final
            
            # Se calcula el flujo y volumen total perdido
            vol_muerto_calc = vol_muerto(diametro_int, TubeLargo)
            Volumenfugado = (flujo * duracion2)
            volumen = Volumenfugado + vol_muerto_calc
            TubeLargo = convertir("m", TlargoUni, TubeLargo)
            
            # Crear objeto para la base de datos
            evento_data = {
                'orden': orden,
                'ubicacion': ubicacion,
                'presion': convertir("bar", "psig", presionTub),
                'subte': subte,
                'dist_tube': Tlargo,
                'dist_tube_uni': TlargoUni,
                'dist_tube2': Tlargo2,
                'dist_tube_uni2': TlargoUni2,
                'diame_tube': Tdiametro,
                'Material': material,
                'Unidades': Unidades,
                'direccion': direccion,
                'forma': forma,
                'medida_rupt': medida,
                'medida_uni': medidaUni,
                'area': area,
                'flujo': float(flujo),
                'volumen': float(volumen),
                'inicio': tiempoInicio.strftime('%Y-%m-%d %H:%M'),
                'duracion': duracion,
                'hora_reg': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                'presion_atmos': float(presionAtmos),
                'volumen_fuga': float(Volumenfugado),
                'volumen_muerto': float(vol_muerto_calc),
                'diame_equi': escape if equi == "on" else 'no',
                'aprobado': 'no'
            }
            
            # Guardar en base de datos
            response = createEvent(evento_data)
            
            if response.get('status') == 'Orden creada con éxito':
                # Renderizar resultados con todos los datos calculados (exacto como rl.py)
                hoy = datetime.datetime.now()
                vol_muerto2 = float(vol_muerto_calc)
                resp = make_response(render_template('resultados.html', 
                    Unidades=Unidades,
                    material=material,
                    Tdiametro=round(Tdiametro, 2),
                    Volumenfugado=round(Volumenfugado, 2),
                    vol_muerto=round(vol_muerto2, 2),
                    Subte=subte,
                    Tlargo=TubeLargo,
                    TlargoUni=TlargoUni,
                    orden=orden,
                    area=round(area, 2),
                    flujo=round(flujo, 2),
                    volumen=round(volumen, 2),
                    horas=horas,
                    minutos=minutos,
                    longitud=round(longi, 4),
                    latitud=lati,
                    año_reg=hoy.year,
                    mes_reg=hoy.month,
                    dia_reg=hoy.day,
                    año_inicio=tiempoInicio.year,
                    mes_inicio=tiempoInicio.month,
                    dia_inicio=tiempoInicio.day,
                    direccion="Unidireccional" if direccion == "uni" else "Bidireccional",
                    presion_tube=round(convertir("bar", "psig", presionTub), 2),
                    presion_atmos=round(convertir("bar", "psig", presionAtmos), 2),
                    forma=forma
                ))
                resp.set_cookie('guardado', 'true')
                return resp
            else:
                # Error al guardar
                resp = make_response(redirect('/NuevoEvento', code=307))
                return resp
                
        except Exception as e:
            print(f"Error procesando evento: {e}")
            resp = make_response(redirect('/NuevoEvento', code=307))
            return resp

    @app.route('/Editado', methods=['POST'])
    def editado():
        # Procesar datos del formulario de edición (misma lógica que /Resultados)
        orden = request.form.get('orden')
        ubicacion = request.form.get('ubicacion')
        presionTub = request.form.get('presion')
        presionUni = request.form.get('presionUni')
        subte = request.form.get('subte')
        equi = request.form.get('diameEqui')
        escape = request.form.get('escape')
        direccion = request.form.get("Flujo")
        forma = request.form.get('Forma')
        Fdiametro = request.form.get('DiameFuga')
        longitud = request.form.get('LongiFuga')
        Alto = request.form.get('Altofuga')
        FdiametroUni = request.form.get('DiameFugaUni')
        longitudUni = request.form.get('LongiFugaUni')
        AltoUni = request.form.get('AltofugaUni')
        Tlargo = request.form.get("DistTube")
        TlargoUni = request.form.get("DistTubeUni")
        Tlargo2 = request.form.get("DistTube2")
        TlargoUni2 = request.form.get("DistTubeUni2")
        Tdiametro = request.form.get('DiameTube')
        tiempoInicio = request.form.get('tiempoInicio')
        tiempoFin = request.form.get('tiempoFin')
        
        try:
            # Procesar datos igual que en /Resultados
            presionTub = float(presionTub)
            Fdiametro = float(Fdiametro) if Fdiametro != "" else 0
            Tlargo = float(Tlargo) if Tlargo != "" else 0
            Tlargo2 = float(Tlargo2) if Tlargo2 != "" else 0
            longitud = float(longitud) if longitud != "" else 0
            Tdiametro = float(Tdiametro)
            
            # Aplicar los diametros equivalentes
            if equi == 'on':
                Fuga_diame = convertir("in", "mm", diametro_equi(Tdiametro, escape))
            else:
                Fuga_diame = convertir(FdiametroUni, "mm", Fdiametro)
            
            # Convertir a mm y m para que concuerden las unidades
            diametro_int = diametro_interno(Tdiametro)
            material = diametro_interno1(Tdiametro)
            Unidades = diametro_interno2(Tdiametro)
            Tlargo = convertir(TlargoUni, "m", Tlargo)
            Tlargo2 = convertir(TlargoUni2, "m", Tlargo2)
            longitud = convertir(longitudUni, "mm", longitud)
            
            TubeLargo = Tlargo + Tlargo2
            
            # Separar los componentes de la ubicacion
            lati = float(ubicacion.split(",")[0])
            longi = float(ubicacion.split(",")[1])
            
            # Convertir a bar para que concuerden las unidades de presion
            presionTub = convertir(presionUni, "bar", presionTub)
            
            # Traer presion atmos
            presionAtmos = presion_atmos(elevacion(lati, longi))
            
            # Calcular duracion
            tiempoInicio = datetime.datetime(int(tiempoInicio[0:4]), int(tiempoInicio[5:7]), int(tiempoInicio[8:10]), int(tiempoInicio[11:13]), int(tiempoInicio[14:16]), 0, 0)
            tiempoFin = datetime.datetime(int(tiempoFin[0:4]), int(tiempoFin[5:7]), int(tiempoFin[8:10]), int(tiempoFin[11:13]), int(tiempoFin[14:16]), 0, 0)
            duracion = tiempoFin - tiempoInicio
            duracion = duracion.total_seconds()
            duracion2 = duracion / 3600
            
            # Calcular horas y minutos para duración
            horas = int(duracion // 3600)
            horasQ = duracion % 3600
            minutos = int(horasQ // 60)
            
            # Si la ruptura es total se calculan los valores de una ruptura circular con el diametro de la tubería
            if forma == "total":
                Fuga_diame = diametro_int
                area = calc_area("circ", Fuga_diame, 0, 0, 0)
                perimetro = calc_peri("circ", Fuga_diame, 0, 0, 0)
            # Si la ruptura es recta se calcula el diametro hidraulico
            elif forma == "recta":
                if equi == 'on':
                    area = calc_area("circ", Fuga_diame, 0, 0, 0)
                    perimetro = calc_peri("circ", Fuga_diame, 0, 0, 0)
                else:
                    area = calc_area("recta", 0, 0, 0, longitud)
                    perimetro = calc_peri("recta", 0, 0, 0, longitud)
                    Fuga_diame = diametro_hidraulico(area, perimetro, diametro_int)
            else:
                area = calc_area(forma, Fuga_diame, 0, 0, longitud)
                perimetro = calc_peri(forma, Fuga_diame, 0, 0, longitud)
            
            if forma == "rect" or forma == "recta":
                coef_flujo = 0.9
            elif forma == "tria":
                coef_flujo = 0.95
            else:
                coef_flujo = 1
            
            if forma == "recta":
                forma = "Recta"
                medida = longitud
                medidaUni = longitudUni
            elif forma == "total":
                forma = "Total"
                medida = ""
                medidaUni = ""
            else:
                forma = "Circular"
                medida = Fdiametro
                medidaUni = FdiametroUni
            
            # Calcular flujo usando el mismo método que /Resultados
            R_vals = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
            R_real = 1.0 if forma == "Total" else Fuga_diame / diametro_int
            Q_vals = []
            
            if diametro_int > 76.2:
                d1 = 50.8
                d2 = 76.2
                Q1_vals = []
                Q2_vals = []
                for R in R_vals:
                    R_actual = 1.0 if forma == "Total" else R
                    Q1_iter = []
                    Q2_iter = []

                    for d_tube_i, Q_iter in zip([d1, d2], [Q1_iter, Q2_iter]):
                        L0 = obtener_L0(R_actual, material)
                        if TubeLargo <= L0:
                            Q0 = modelo_utpSuper(Fuga_diame, d_tube_i, presionTub, presionAtmos, subte, direccion, forma, TubeLargo, material, R_actual)
                            Q_iter.append(Q0)
                        else:
                            Q0 = modelo_utpSuper(Fuga_diame, d_tube_i, presionTub, presionAtmos, subte, direccion, forma, L0, material, R_actual)
                            Q_iter.append(Q0)
                            for L in range(L0 + 1, int(TubeLargo) + 1):
                                a = alpha(L, R_actual, material)
                                Qi = Q_iter[-1] if a is None else Q_iter[-1] * (1 - a)
                                Q_iter.append(Qi)

                    Q1_vals.append(Q1_iter[-1])
                    Q2_vals.append(Q2_iter[-1])

                Q1_interp = np.interp(R_real, R_vals, Q1_vals)
                Q2_interp = np.interp(R_real, R_vals, Q2_vals)
                Q_extrap = Q1_interp + (Q2_interp - Q1_interp) * ((diametro_int - d1) / (d2 - d1))
                flujo = Q_extrap
            else:
                for R in R_vals:
                    R_actual = 1.0 if forma == "Total" else R
                    Q_iter = []
                    L0 = obtener_L0(R_actual, material)

                    if TubeLargo <= L0:
                        Q0 = modelo_utpSuper(Fuga_diame, diametro_int, presionTub, presionAtmos, subte, direccion, forma, TubeLargo, material, R_actual)
                        Q_iter.append(Q0)
                    else:
                        Q0 = modelo_utpSuper(Fuga_diame, diametro_int, presionTub, presionAtmos, subte, direccion, forma, L0, material, R_actual)
                        Q_iter.append(Q0)
                        for L in range(L0 + 1, int(TubeLargo) + 1):
                            a = alpha(L, R_actual, material)
                            Qi = Q_iter[-1] if a is None else Q_iter[-1] * (1 - a)
                            Q_iter.append(Qi)

                    Q_vals.append(Q_iter[-1])

                Q_final = np.interp(R_real, R_vals, Q_vals)
                flujo = Q_final
            
            # Calcular volumenes
            vol_muerto_calc = vol_muerto(diametro_int, TubeLargo)
            Volumenfugado = (flujo * duracion2)
            volumen = Volumenfugado + vol_muerto_calc
            TubeLargo = convertir("m", TlargoUni, TubeLargo)
            
            # Preparar datos para actualización
            evento_data = {
                'orden': orden,
                'ubicacion': ubicacion,
                'presion': convertir("bar", "psig", presionTub),
                'subte': subte,
                'dist_tube': Tlargo,
                'dist_tube_uni': TlargoUni,
                'dist_tube2': Tlargo2,
                'dist_tube_uni2': TlargoUni2,
                'diame_tube': Tdiametro,
                'Material': material,
                'Unidades': Unidades,
                'direccion': direccion,
                'forma': forma,
                'medida_rupt': medida,
                'medida_uni': medidaUni,
                'area': area,
                'flujo': float(flujo),
                'volumen': float(volumen),
                'inicio': tiempoInicio.strftime('%Y-%m-%d %H:%M'),
                'duracion': duracion,
                'hora_reg': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                'presion_atmos': float(presionAtmos),
                'volumen_fuga': float(Volumenfugado),
                'volumen_muerto': float(vol_muerto_calc),
                'diame_equi': escape if equi == "on" else 'no',
                'aprobado': 'no'  # Reset approval status when edited
            }
            
            # Actualizar en base de datos
            response = updateEvent(evento_data)
            
            # Redirigir a reporte con cookie actualizado
            resp = make_response(redirect('/Reporte', code=307))
            resp.set_cookie('orden', orden)
            return resp
            
        except Exception as e:
            print(f"Error actualizando evento: {e}")
            # En caso de error, redirigir al formulario de edición
            resp = make_response(redirect('/Editar', code=307))
            return resp

    @app.route('/Editar', methods=['POST'])
    def editar():
        # Obtener la orden del cookie o del form
        orden = request.cookies.get("orden")
        if not orden:
            orden = request.form.get('orden')
        
        objeto_ = {'orden': orden}
        response = getSpecificEvent(objeto_)
        
        if response['status'] == 'Si hay elemento':
            fila = response['data'][0]
            
            # Procesar datos para el formulario de edición
            fecha_inicio = datetime.datetime.strptime(fila['inicio'], '%Y-%m-%d %H:%M')
            tiempoInicio_str = fecha_inicio.strftime('%Y-%m-%dT%H:%M')
            
            # Calcular tiempo fin basado en duración
            duracion_segundos = fila['duracion'] 
            fecha_fin = fecha_inicio + datetime.timedelta(seconds=duracion_segundos)
            tiempoFin_str = fecha_fin.strftime('%Y-%m-%dT%H:%M')
            
            # Preparar datos para el formulario
            form_data = {
                'orden': fila['orden'],
                'ubicacion': fila['ubicacion'],
                'tiempoInicio': tiempoInicio_str,
                'tiempoFin': tiempoFin_str,
                'presion': fila['presion'],
                'presionUni': 'psig',  # Asumir unidades por defecto
                'DiameTube': fila['diame_tube'],
                'DistTube': fila['dist_tube'],
                'DistTubeUni': fila['dist_tube_uni'],
                'DistTube2': float(fila.get('dist_tube2', 1)) if fila.get('dist_tube2') else 1,
                'DistTubeUni2': fila.get('dist_tube_uni2', 'm') if fila.get('dist_tube_uni2') else 'm',
                'subte': fila['subte'],
                'Flujo': fila['direccion'],
                'Forma': fila['forma'],
                'DiameFuga': fila.get('medida_rupt', ''),
                'DiameFugaUni': fila.get('medida_uni', 'mm'),
                'LongiFuga': fila.get('medida_rupt', '') if fila['forma'] == 'recta' else '',
                'LongiFugaUni': fila.get('medida_uni', 'mm') if fila['forma'] == 'recta' else 'mm',
                'diameEqui': 'checked' if fila.get('diame_equi', 'no') == 'sí' else '',
                'escape': '1'  # Valor por defecto
            }
            
            resp = make_response(render_template('editar.html', **form_data))
            return resp
        else:
            # Si no se encuentra el evento, redirigir a buscar
            resp = make_response(redirect('/BuscarEvento'))
            return resp

    @app.route('/Aprobar', methods=['POST'])
    def aprobar():
        # Esta ruta aprueba un evento
        resp = make_response(redirect('/Reporte', code=307))
        return resp

    @app.route('/RegistrarseAdmin', methods=['POST'])
    def registrarse_admin():
        # Esta ruta carga el formulario de registro de admin
        resp = make_response(render_template('crear_admin.html', existe="false"))
        return resp

    @app.route('/RegistrarAdmin', methods=['POST'])
    def registrar_admin():
        # Esta ruta procesa el registro de admin
        resp = make_response(render_template('creado_admin.html'))
        return resp

    # ===== RUTAS DE ADMINISTRACIÓN (SOLO SUPERADMIN) =====
    
    @app.route('/Administracion')
    def administracion():
        """Página de administración de usuarios - Solo SuperAdmin"""
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return redirect('/Principal')
            
        # Obtener todos los usuarios
        users_cursor = getUsers()
        users_list = []
        for user in users_cursor:
            user['_id'] = str(user['_id'])  # Convertir ObjectId a string
            users_list.append(user)
        
        resp = make_response(render_template('administracion.html', users=users_list))
        return resp

    @app.route('/ToggleUserState', methods=['POST'])
    def toggle_user_state():
        """Habilitar/Deshabilitar usuario - Solo SuperAdmin"""
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return {'status': 'error', 'message': 'No autorizado'}, 403
            
        user_id = request.form.get('user_id')
        current_state = request.form.get('current_state') == 'True'  # Convertir string a boolean
        new_state = not current_state  # Invertir el estado
        
        try:
            updateUserState(user_id, new_state)
            return redirect('/Administracion')
        except Exception as e:
            print(f"Error actualizando estado: {e}")
            return redirect('/Administracion')

    @app.route('/ChangeUserPassword', methods=['POST'])
    def change_user_password():
        """Cambiar contraseña de usuario - Solo SuperAdmin"""
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return {'status': 'error', 'message': 'No autorizado'}, 403
            
        user_id = request.form.get('user_id')
        new_password = request.form.get('new_password')
        
        try:
            updateUserPassword(user_id, new_password)
            return redirect('/Administracion')
        except Exception as e:
            print(f"Error cambiando contraseña: {e}")
            return redirect('/Administracion')

    # ===== RUTAS DE CARGA MASIVA (SOLO SUPERADMIN) =====
    
    @app.route('/DescargarFormato', methods=['POST'])
    def descargar_formato():
        """Descargar formato base para carga masiva - Solo SuperAdmin"""
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return redirect('/BuscarEvento')
        
        # Crear un DataFrame con las columnas necesarias (sin _id de MongoDB)
        columnas_formato = [
            'orden', 'ubicacion', 'presion', 'subte', 'dist_tube', 'dist_tube_uni',
            'dist_tube2', 'dist_tube_uni2', 'diame_tube', 'Material', 'Unidades',
            'direccion', 'forma', 'medida_rupt', 'medida_uni', 'area', 'flujo',
            'volumen', 'inicio', 'duracion', 'hora_reg', 'presion_atmos',
            'volumen_fuga', 'volumen_muerto', 'diame_equi', 'aprobado'
        ]
        
        # Crear DataFrame vacío con las columnas
        df_formato = pd.DataFrame(columns=columnas_formato)
        
        # Agregar una fila de ejemplo
        ejemplo = {
            'orden': 'EJEMPLO-001',
            'ubicacion': '4.6097,-74.0817',
            'presion': 60.0,
            'subte': 'sub',
            'dist_tube': 100.0,
            'dist_tube_uni': 'm',
            'dist_tube2': 0.0,
            'dist_tube_uni2': 'm',
            'diame_tube': 4.0,
            'Material': 'Acero',
            'Unidades': 'in',
            'direccion': 'uni',
            'forma': 'circ',
            'medida_rupt': 25.4,
            'medida_uni': 'mm',
            'area': 506.7,
            'flujo': 15.5,
            'volumen': 2.5,
            'inicio': '2024-01-15 10:30',
            'duracion': 3600,
            'hora_reg': '2024-01-15 11:00',
            'presion_atmos': 14.2,
            'volumen_fuga': 1.8,
            'volumen_muerto': 0.7,
            'diame_equi': 'no',
            'aprobado': 'no'
        }
        df_formato = pd.concat([df_formato, pd.DataFrame([ejemplo])], ignore_index=True)
        
        buffer = BytesIO()
        df_formato.to_excel(buffer, index=False, sheet_name='Formato_Eventos')
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='formato_carga_masiva_eventos.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    @app.route('/CargarMasivo', methods=['POST'])
    def cargar_masivo():
        """Cargar eventos masivamente desde Excel - Solo SuperAdmin"""
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return redirect('/BuscarEvento')
        
        if 'archivo' not in request.files:
            return redirect('/BuscarEvento')
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            return redirect('/BuscarEvento')
        
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo)
            
            eventos_creados = 0
            eventos_fallidos = 0
            
            for index, row in df.iterrows():
                try:
                    # Convertir la fila a diccionario
                    evento_data = row.to_dict()
                    
                    # Validar que tenga los campos obligatorios
                    if pd.isna(evento_data.get('orden')) or evento_data.get('orden') == 'EJEMPLO-001':
                        continue  # Saltar filas vacías o de ejemplo
                    
                    # Convertir tipos de datos
                    evento_data = {k: (None if pd.isna(v) else v) for k, v in evento_data.items()}
                    
                    # Crear el evento
                    response = createEvent(evento_data)
                    if response.get('status') == 'Orden creada con éxito':
                        eventos_creados += 1
                    else:
                        eventos_fallidos += 1
                        print(f"Error creando evento {evento_data.get('orden')}: {response}")
                        
                except Exception as e:
                    eventos_fallidos += 1
                    print(f"Error procesando fila {index}: {e}")
            
            print(f"Carga masiva completada: {eventos_creados} creados, {eventos_fallidos} fallidos")
            return redirect('/BuscarEvento')
            
        except Exception as e:
            print(f"Error en carga masiva: {e}")
            return redirect('/BuscarEvento')

    # ===== NUEVA PÁGINA DE CARGA MASIVA DEDICADA =====
    
    @app.route('/CargaMasiva')
    def carga_masiva():
        """Página dedicada para carga masiva - SuperAdmin y worker"""
        # Verificar que el usuario sea SuperAdmin o worker
        user_rol = request.cookies.get('rol')
        if user_rol not in ['SuperAdmin', 'worker']:
            return redirect('/Perfil')
            
        resp = make_response(render_template('carga_masiva.html'))
        return resp

    @app.route('/DescargarFormatoSimple', methods=['POST'])
    def descargar_formato_simple():
        """Descargar formato simplificado basado en formulario de crear evento"""
        # Verificar que el usuario sea SuperAdmin o worker
        user_rol = request.cookies.get('rol')
        if user_rol not in ['SuperAdmin', 'worker']:
            return redirect('/CargaMasiva')
        
        # Campos que el usuario llena en el formulario (sin cálculos)
        columnas_formulario = [
            'orden',
            'ubicacion', 
            'presion',
            'presionUni',
            'subte',
            'diameEqui',
            'escape',
            'Flujo',
            'Forma', 
            'DiameFuga',
            'DiameFugaUni',
            'LongiFuga',
            'LongiFugaUni',
            'DistTube',
            'DistTubeUni', 
            'DistTube2',
            'DistTubeUni2',
            'DiameTube',
            'tiempoInicio',
            'tiempoFin'
        ]
        
        # Crear DataFrame con ejemplo
        df_formato = pd.DataFrame(columns=columnas_formulario)
        
        # Agregar fila de ejemplo con datos realistas del formulario  
        ejemplo = {
            'orden': 'CAMBIAR_POR_TU_ORDEN_001',
            'ubicacion': '4.6097,-74.0817',
            'presion': 60.0,
            'presionUni': 'psig',
            'subte': 'sub',
            'diameEqui': 'off',
            'escape': 1,
            'Flujo': 'uni', 
            'Forma': 'circ',
            'DiameFuga': 25.4,
            'DiameFugaUni': 'mm',
            'LongiFuga': '',
            'LongiFugaUni': 'mm',
            'DistTube': 100.0,
            'DistTubeUni': 'm',
            'DistTube2': '',
            'DistTubeUni2': 'm',
            'DiameTube': 4.0,
            'tiempoInicio': '2024-01-15T10:30',
            'tiempoFin': '2024-01-15T11:30'
        }
        df_formato = pd.concat([df_formato, pd.DataFrame([ejemplo])], ignore_index=True)
        
        # Crear archivo Excel con múltiples hojas
        buffer = io.BytesIO()
        try:
            # Intentar usar xlsxwriter para mejor funcionalidad
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                crear_excel_completo(writer, df_formato)
        except ImportError:
            # Fallback a openpyxl si xlsxwriter no está disponible
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                crear_excel_completo(writer, df_formato)
        
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name='formato_carga_masiva_simplificado.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def crear_excel_completo(writer, df_formato):
        """Función auxiliar para crear el Excel con múltiples hojas"""
        # Hoja principal con datos
        df_formato.to_excel(writer, sheet_name='Eventos', index=False)
        
        # Crear hoja de opciones válidas
        opciones_data = {
            'presionUni_opciones': ['psig', 'bar', 'kPa'],
            'subte_opciones': ['sub', 'superficial'],
            'Flujo_opciones': ['uni', 'bi'],
            'Forma_opciones': ['circ', 'rect', 'tria', 'recta', 'total'],
            'diameEqui_opciones': ['on', 'off'],
            'DiameFugaUni_opciones': ['mm', 'in'],
            'LongiFugaUni_opciones': ['mm', 'in'],
            'DistTubeUni_opciones': ['m', 'ft'],
            'DistTubeUni2_opciones': ['m', 'ft']
        }
        
        # Crear hoja de opciones válidas
        opciones_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in opciones_data.items()]))
        opciones_df.to_excel(writer, sheet_name='Opciones_Validas', index=False)
        
        # Hoja de diámetros de tubería comunes
        diametros_tuberia = pd.DataFrame({
            'DiameTube_comunes': [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0],
            'Descripcion': ['1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '3"', '4"', '6"', '8"', '10"', '12"', '16"', '20"', '24"']
        })
        diametros_tuberia.to_excel(writer, sheet_name='Diametros_Tuberia', index=False)
        
        # Crear hoja de instrucciones mejoradas
        instrucciones = pd.DataFrame([
            ['INSTRUCCIONES PARA CARGA MASIVA DE EVENTOS'],
            [''],
            ['PASO A PASO:'],
            ['1. IMPORTANTE: Cambia "CAMBIAR_POR_TU_ORDEN_001" por un código único'],
            ['2. Llena tus datos usando las opciones válidas de las otras hojas'],
            ['3. Guarda el archivo y súbelo en la página web'],
            [''],
            ['CAMPOS OBLIGATORIOS:'],
            ['- orden: Número único (ej: EV-2024-001, RUPTURA-001, etc)'],
            ['- ubicacion: Lat,Lng (ej: 4.6097,-74.0817) - usar Google Maps'],
            ['- presion: Número (ej: 60, 45.5, 120)'],
            ['- presionUni: Ver hoja "Opciones_Validas" (psig, bar, kPa)'],
            ['- subte: Ver hoja "Opciones_Validas" (sub o superficial)'],
            ['- Flujo: Ver hoja "Opciones_Validas" (uni o bi)'],
            ['- Forma: Ver hoja "Opciones_Validas" (circ, rect, tria, recta, total)'],
            ['- DiameTube: Ver hoja "Diametros_Tuberia" para valores comunes'],
            ['- tiempoInicio: YYYY-MM-DDTHH:MM (ej: 2024-01-15T10:30)'],
            ['- tiempoFin: YYYY-MM-DDTHH:MM (ej: 2024-01-15T11:30)'],
            [''],
            ['CAMPOS SEGÚN TIPO DE RUPTURA:'],
            ['- Si Forma = circ: llenar DiameFuga y DiameFugaUni'],
            ['- Si Forma = recta: llenar LongiFuga y LongiFugaUni'],
            ['- Si Forma = rect/tria: llenar DiameFuga como el lado/radio'],
            ['- Si Forma = total: dejar DiameFuga vacío'],
            [''],
            ['CAMPOS OPCIONALES:'],
            ['- diameEqui: "on" para usar diámetro equivalente, "off" para no usar'],
            ['- escape: Número (1-5) para cálculo de diámetro equivalente'],
            ['- DistTube: Distancia a primera válvula (número)'],
            ['- DistTube2: Distancia a segunda válvula (solo si Flujo=bi)'],
            ['- DistTubeUni/DistTubeUni2: Ver opciones (m o ft)'],
            [''],
            ['EJEMPLOS DE DATOS VÁLIDOS:'],
            ['presionUni: psig, bar, kPa'],
            ['subte: sub, superficial'],
            ['Flujo: uni, bi'],
            ['Forma: circ, rect, tria, recta, total'],
            ['diameEqui: on, off'],
            [''],
            ['NOTAS IMPORTANTES:'],
            ['- Usar punto (.) como separador decimal, no coma'],
            ['- Coordenadas con punto como decimal: 4.6097,-74.0817'],
            ['- Fechas en formato ISO: 2024-01-15T10:30'],
            ['- Eliminar SIEMPRE la fila de ejemplo antes de subir'],
            ['- Los cálculos complejos se harán automáticamente']
        ])
        instrucciones.to_excel(writer, sheet_name='Instrucciones', index=False, header=False)

    def procesar_evento_desde_excel(form_data):
        """Procesar un evento usando los mismos cálculos que /Resultados"""
        try:
            # Extraer datos del diccionario (simulando request.form.get)
            orden = form_data.get('orden', '')
            ubicacion = form_data.get('ubicacion', '') 
            presionTub = form_data.get('presion', '')
            presionUni = form_data.get('presionUni', 'psig')
            subte = form_data.get('subte', 'sub')
            equi = 'on' if form_data.get('diameEqui', '').lower() == 'on' else None
            escape = form_data.get('escape', '1')
            direccion = form_data.get('Flujo', 'uni')
            forma = form_data.get('Forma', 'circ')
            Fdiametro = form_data.get('DiameFuga', '')
            longitud = form_data.get('LongiFuga', '')
            FdiametroUni = form_data.get('DiameFugaUni', 'mm')
            longitudUni = form_data.get('LongiFugaUni', 'mm')
            Tlargo = form_data.get('DistTube', '')
            TlargoUni = form_data.get('DistTubeUni', 'm')
            Tlargo2 = form_data.get('DistTube2', '')
            TlargoUni2 = form_data.get('DistTubeUni2', 'm')
            Tdiametro = form_data.get('DiameTube', '')
            tiempoInicio = form_data.get('tiempoInicio', '')
            tiempoFin = form_data.get('tiempoFin', '')
            
            # Validaciones básicas más detalladas
            campos_vacios = []
            if not orden: campos_vacios.append('orden')
            if not ubicacion: campos_vacios.append('ubicacion')
            if not presionTub: campos_vacios.append('presion')
            if not Tdiametro: campos_vacios.append('DiameTube')
            if not tiempoInicio: campos_vacios.append('tiempoInicio')
            if not tiempoFin: campos_vacios.append('tiempoFin')
            
            if campos_vacios:
                return {'status': 'error', 'error': f'Campos obligatorios faltantes: {", ".join(campos_vacios)}'}
                
            # Validación especial para ejemplo
            if orden.upper().startswith('EJEMPLO') or orden.upper().startswith('CAMBIAR'):
                return {'status': 'error', 'error': 'Debes cambiar la orden de ejemplo por un valor único (ej: EV-2024-001, RUPTURA-001)'}
            
            # Conversiones de tipos (misma lógica que /Resultados)
            presionTub = float(presionTub)
            Fdiametro = float(Fdiametro) if Fdiametro != "" else 0
            Tlargo = float(Tlargo) if Tlargo != "" else 0
            Tlargo2 = float(Tlargo2) if Tlargo2 != "" else 0
            longitud = float(longitud) if longitud != "" else 0
            Tdiametro = float(Tdiametro)
            
            # Aplicar los diametros equivalentes
            if equi == 'on':
                Fuga_diame = convertir("in", "mm", diametro_equi(Tdiametro, escape))
            else:
                Fuga_diame = convertir(FdiametroUni, "mm", Fdiametro)
            
            # Convertir a mm y m para que concuerden las unidades
            diametro_int = diametro_interno(Tdiametro)
            material = diametro_interno1(Tdiametro)
            Unidades = diametro_interno2(Tdiametro)
            Tlargo = convertir(TlargoUni, "m", Tlargo)
            Tlargo2 = convertir(TlargoUni2, "m", Tlargo2)
            longitud = convertir(longitudUni, "mm", longitud)
            
            TubeLargo = Tlargo + Tlargo2
            
            # Separar los componentes de la ubicacion
            lati = float(ubicacion.split(",")[0])
            longi = float(ubicacion.split(",")[1])
            
            # Convertir a bar para que concuerden las unidades de presion
            presionTub = convertir(presionUni, "bar", presionTub)
            
            # Traer presion atmos
            presionAtmos = presion_atmos(elevacion(lati, longi))
            
            # Procesar fechas
            tiempoInicio = datetime.datetime.fromisoformat(tiempoInicio.replace('T', ' '))
            tiempoFin = datetime.datetime.fromisoformat(tiempoFin.replace('T', ' '))
            duracion = tiempoFin - tiempoInicio
            duracion = duracion.total_seconds()
            horas = int(duracion // 3600)
            horasQ = duracion % 3600
            minutos = int(horasQ // 60)
            duracion2 = duracion / 3600
            
            # Cálculos de ruptura (misma lógica que /Resultados)
            if forma == "total":
                Fuga_diame = diametro_int
                area = calc_area("circ", Fuga_diame, 0, 0, 0)
                perimetro = calc_peri("circ", Fuga_diame, 0, 0, 0)
            elif forma == "recta":
                if equi == 'on':
                    area = calc_area("circ", Fuga_diame, 0, 0, 0)
                    perimetro = calc_peri("circ", Fuga_diame, 0, 0, 0)
                else:
                    area = calc_area("recta", 0, 0, 0, longitud)
                    perimetro = calc_peri("recta", 0, 0, 0, longitud)
                    Fuga_diame = diametro_hidraulico(area, perimetro, diametro_int)
            else:
                area = calc_area(forma, Fuga_diame, 0, 0, longitud)
                perimetro = calc_peri(forma, Fuga_diame, 0, 0, longitud)
            
            if forma == "rect" or forma == "recta":
                coef_flujo = 0.9
            elif forma == "tria":
                coef_flujo = 0.95
            else:
                coef_flujo = 1
            
            if forma == "recta":
                forma = "Recta"
                medida = longitud
                medidaUni = longitudUni
            elif forma == "total":
                forma = "Total"
                medida = ""
                medidaUni = ""
            else:
                forma = "Circular"
                medida = Fdiametro
                medidaUni = FdiametroUni
            
            # NUEVO METODO DE CALCULO DEL FLUJO (igual que /Resultados)
            R_vals = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
            R_real = 1.0 if forma == "Total" else Fuga_diame / diametro_int
            Q_vals = []
            
            if diametro_int > 76.2:
                d1 = 50.8
                d2 = 76.2
                Q1_vals = []
                Q2_vals = []
                for R in R_vals:
                    R_actual = 1.0 if forma == "Total" else R
                    Q1_iter = []
                    Q2_iter = []

                    for d_tube_i, Q_iter in zip([d1, d2], [Q1_iter, Q2_iter]):
                        L0 = obtener_L0(R_actual, material)
                        if TubeLargo <= L0:
                            Q0 = modelo_utpSuper(Fuga_diame, d_tube_i, presionTub, presionAtmos, subte, direccion, forma, TubeLargo, material, R_actual)
                            Q_iter.append(Q0)
                        else:
                            Q0 = modelo_utpSuper(Fuga_diame, d_tube_i, presionTub, presionAtmos, subte, direccion, forma, L0, material, R_actual)
                            Q_iter.append(Q0)
                            for L in range(L0 + 1, int(TubeLargo) + 1):
                                a = alpha(L, R_actual, material)
                                Qi = Q_iter[-1] if a is None else Q_iter[-1] * (1 - a)
                                Q_iter.append(Qi)

                    Q1_vals.append(Q1_iter[-1])
                    Q2_vals.append(Q2_iter[-1])

                Q1_interp = np.interp(R_real, R_vals, Q1_vals)
                Q2_interp = np.interp(R_real, R_vals, Q2_vals)
                Q_extrap = Q1_interp + (Q2_interp - Q1_interp) * ((diametro_int - d1) / (d2 - d1))
                flujo = Q_extrap
            else:
                for R in R_vals:
                    R_actual = 1.0 if forma == "Total" else R
                    Q_iter = []
                    L0 = obtener_L0(R_actual, material)

                    if TubeLargo <= L0:
                        Q0 = modelo_utpSuper(Fuga_diame, diametro_int, presionTub, presionAtmos, subte, direccion, forma, TubeLargo, material, R_actual)
                        Q_iter.append(Q0)
                    else:
                        Q0 = modelo_utpSuper(Fuga_diame, diametro_int, presionTub, presionAtmos, subte, direccion, forma, L0, material, R_actual)
                        Q_iter.append(Q0)
                        for L in range(L0 + 1, int(TubeLargo) + 1):
                            a = alpha(L, R_actual, material)
                            Qi = Q_iter[-1] if a is None else Q_iter[-1] * (1 - a)
                            Q_iter.append(Qi)

                    Q_vals.append(Q_iter[-1])

                Q_final = np.interp(R_real, R_vals, Q_vals)
                flujo = Q_final
            
            # Calcular volumenes
            vol_muerto_calc = vol_muerto(diametro_int, TubeLargo)
            Volumenfugado = (flujo * duracion2)
            volumen = Volumenfugado + vol_muerto_calc
            TubeLargo = convertir("m", TlargoUni, TubeLargo)
            
            # Crear objeto para la base de datos
            evento_data = {
                'orden': orden,
                'ubicacion': ubicacion,
                'presion': convertir("bar", "psig", presionTub),
                'subte': subte,
                'dist_tube': Tlargo,
                'dist_tube_uni': TlargoUni,
                'dist_tube2': Tlargo2,
                'dist_tube_uni2': TlargoUni2,
                'diame_tube': Tdiametro,
                'Material': material,
                'Unidades': Unidades,
                'direccion': direccion,
                'forma': forma,
                'medida_rupt': medida,
                'medida_uni': medidaUni,
                'area': area,
                'flujo': float(flujo),
                'volumen': float(volumen),
                'inicio': tiempoInicio.strftime('%Y-%m-%d %H:%M'),
                'duracion': duracion,
                'hora_reg': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
                'presion_atmos': float(presionAtmos),
                'volumen_fuga': float(Volumenfugado),
                'volumen_muerto': float(vol_muerto_calc),
                'diame_equi': escape if equi == "on" else 'no',
                'aprobado': 'no'
            }
            
            # Guardar en base de datos
            response = createEvent(evento_data)
            
            if response.get('status') == 'Orden creada con éxito':
                return {'status': 'exito'}
            else:
                # Manejar específicamente el error de orden duplicada
                error_msg = response.get('status', 'Error desconocido')
                if 'éxiste una orden registrada' in error_msg:
                    error_msg = f'La orden "{orden}" ya existe. Usa un número único diferente'
                return {'status': 'error', 'error': error_msg}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/ProcesarCargaMasiva', methods=['POST'])
    def procesar_carga_masiva():
        """Procesar carga masiva usando lógica del formulario"""
        # Verificar que el usuario sea SuperAdmin o worker
        user_rol = request.cookies.get('rol')
        if user_rol not in ['SuperAdmin', 'worker']:
            return {'error': 'No autorizado'}, 403
        
        if 'archivo' not in request.files:
            return {'error': 'No se encontró archivo'}, 400
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            return {'error': 'Archivo vacío'}, 400
        
        try:
            # Leer el archivo Excel
            df = pd.read_excel(archivo, sheet_name='Eventos')
            
            eventos_creados = 0
            eventos_fallidos = 0
            errores = []
            
            for index, row in df.iterrows():
                try:
                    # Saltar filas vacías o de ejemplo
                    if pd.isna(row.get('orden')) or row.get('orden') in ['EJEMPLO-001', 'EV-2024-001']:
                        continue
                    
                    # Simular el llenado del formulario de crear evento
                    form_data = {}
                    for col in df.columns:
                        form_data[col] = '' if pd.isna(row[col]) else str(row[col])
                    
                    # Procesar usando la misma lógica que /Resultados
                    resultado = procesar_evento_desde_excel(form_data)
                    
                    if resultado['status'] == 'exito':
                        eventos_creados += 1
                    else:
                        eventos_fallidos += 1
                        errores.append(f"Fila {index + 2}: {resultado['error']}")
                        
                except Exception as e:
                    eventos_fallidos += 1
                    errores.append(f"Fila {index + 2}: {str(e)}")
            
            # Log para debugging
            print(f"Carga masiva completada: {eventos_creados} creados, {eventos_fallidos} fallidos")
            for error in errores[:5]:  # Mostrar primeros 5 errores en consola
                print(f"Error: {error}")
                
            return {
                'eventos_creados': eventos_creados,
                'eventos_fallidos': eventos_fallidos,
                'errores': errores[:10]  # Limitar a 10 errores para no sobrecargar
            }
            
        except Exception as e:
            return {'error': f'Error procesando archivo: {str(e)}'}, 500