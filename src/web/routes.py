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
from functions.conect import getInstance
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
            resp.set_cookie('rol', '')
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
            resp.set_cookie('rol', result.get('rol', 'worker'))  # Rol del usuario
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

    @app.route('/VisualizarEventos', methods=['GET'])
    def visualizar_eventos():
        """Página con tabla de todos los eventos - SuperAdmin y worker pueden ver"""
        # Verificar que el usuario esté autenticado
        user_rol = request.cookies.get('rol')
        if not user_rol or user_rol not in ['SuperAdmin', 'worker']:
            return redirect('/Inicio')

        # Obtener todos los eventos
        events_cursor = getEvents()
        events_list = []

        for event in events_cursor:
            event['_id'] = str(event['_id'])  # Convertir ObjectId a string
            # Formatear datos para la tabla
            event_display = {
                '_id': event['_id'],
                'orden': event.get('orden', 'N/A'),
                'ubicacion': event.get('ubicacion', 'N/A'),
                'inicio': event.get('inicio', 'N/A'),
                'duracion_hrs': round(event.get('duracion', 0) / 3600, 2) if event.get('duracion') else 0,
                'volumen': round(event.get('volumen', 0), 2),
                'flujo': round(event.get('flujo', 0), 2),
                'presion': round(event.get('presion', 0), 2),
                'diame_tube': event.get('diame_tube', 'N/A'),
                'forma': event.get('forma', 'N/A'),
                'direccion': event.get('direccion', 'N/A'),
                'subte': event.get('subte', 'N/A'),
                'aprobado': event.get('aprobado', 'no'),
                'hora_reg': event.get('hora_reg', 'N/A')
            }
            events_list.append(event_display)

        resp = make_response(render_template('visualizar_eventos.html', events=events_list, user_rol=user_rol))
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
                'aprobado': fila['aprobado'],
                'diame_tube': fila['diame_tube'],
                'material': fila['Material'],
                'Unidades': fila['Unidades']
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
                'LongiFuga': fila.get('medida_rupt', '') if fila['forma'] == 'recta' or fila['forma'] == 'Recta' else '',
                'LongiFugaUni': fila.get('medida_uni', 'mm') if fila['forma'] == 'recta' or fila['forma'] == 'Recta' else 'mm',
                'diameEqui': fila.get('diame_equi', 'no'),
                'escape': fila.get('diame_equi', 'min')
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
        # Verificar que el usuario sea SuperAdmin
        user_rol = request.cookies.get('rol')
        if user_rol != 'SuperAdmin':
            return redirect('/Perfil')

        # Obtener el número de orden del cookie
        orden = request.cookies.get('orden')
        if not orden:
            return redirect('/Perfil')

        # Actualizar el campo aprobado en la base de datos
        client = getInstance()
        db = client["rupture"]
        filter_ = {"orden": orden}
        update = {"$set": {"aprobado": "sí"}}
        db.events.update_one(filter_, update)

        # Redirigir de vuelta al reporte
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
        """Descargar formato mejorado y más intuitivo para carga masiva"""
        # Verificar que el usuario sea SuperAdmin o worker
        user_rol = request.cookies.get('rol')
        if user_rol not in ['SuperAdmin', 'worker']:
            return redirect('/CargaMasiva')

        # Campos simplificados y en español
        columnas_formulario = [
            'Numero_Orden',
            'Latitud',
            'Longitud',
            'Presion_Tuberia',
            'Unidad_Presion',
            'Diametro_Tuberia_Pulgadas',
            'Ubicacion_Tuberia',
            'Direccion_Flujo',
            'Tipo_Ruptura',
            'Medida_Ruptura',
            'Unidad_Medida_Ruptura',
            'Usar_Diametro_Equivalente',
            'Tipo_Escape',
            'Distancia_Valvula_1_m',
            'Distancia_Valvula_2_m',
            'Año_Inicio',
            'Mes_Inicio',
            'Dia_Inicio',
            'Hora_Inicio',
            'Minuto_Inicio',
            'Año_Fin',
            'Mes_Fin',
            'Dia_Fin',
            'Hora_Fin',
            'Minuto_Fin'
        ]
        
        # Crear DataFrame con ejemplos claros
        df_formato = pd.DataFrame(columns=columnas_formulario)

        # EJEMPLO 1: Ruptura circular sin diámetros equivalentes
        ejemplo1 = {
            'Numero_Orden': 1,
            'Latitud': 4.6097,
            'Longitud': -74.0817,
            'Presion_Tuberia': 60.0,
            'Unidad_Presion': 'psig',
            'Diametro_Tuberia_Pulgadas': 4.0,
            'Ubicacion_Tuberia': 'Subterránea',
            'Direccion_Flujo': 'Unidireccional',
            'Tipo_Ruptura': 'Circular',
            'Medida_Ruptura': 25.4,
            'Unidad_Medida_Ruptura': 'mm',
            'Usar_Diametro_Equivalente': 'NO',
            'Tipo_Escape': '',
            'Distancia_Valvula_1_m': 100.0,
            'Distancia_Valvula_2_m': '',
            'Año_Inicio': 2024,
            'Mes_Inicio': 1,
            'Dia_Inicio': 15,
            'Hora_Inicio': 10,
            'Minuto_Inicio': 30,
            'Año_Fin': 2024,
            'Mes_Fin': 1,
            'Dia_Fin': 15,
            'Hora_Fin': 11,
            'Minuto_Fin': 30
        }

        # EJEMPLO 2: Ruptura recta
        ejemplo2 = {
            'Numero_Orden': 2,
            'Latitud': 4.6150,
            'Longitud': -74.0850,
            'Presion_Tuberia': 45.0,
            'Unidad_Presion': 'psig',
            'Diametro_Tuberia_Pulgadas': 2.0,
            'Ubicacion_Tuberia': 'Superficial',
            'Direccion_Flujo': 'Unidireccional',
            'Tipo_Ruptura': 'Recta',
            'Medida_Ruptura': 50.0,
            'Unidad_Medida_Ruptura': 'mm',
            'Usar_Diametro_Equivalente': 'NO',
            'Tipo_Escape': '',
            'Distancia_Valvula_1_m': 150.0,
            'Distancia_Valvula_2_m': '',
            'Año_Inicio': 2024,
            'Mes_Inicio': 2,
            'Dia_Inicio': 20,
            'Hora_Inicio': 14,
            'Minuto_Inicio': 0,
            'Año_Fin': 2024,
            'Mes_Fin': 2,
            'Dia_Fin': 20,
            'Hora_Fin': 16,
            'Minuto_Fin': 30
        }

        # EJEMPLO 3: Flujo bidireccional con diámetros equivalentes
        ejemplo3 = {
            'Numero_Orden': 3,
            'Latitud': 4.6200,
            'Longitud': -74.0900,
            'Presion_Tuberia': 75.0,
            'Unidad_Presion': 'psig',
            'Diametro_Tuberia_Pulgadas': 6.0,
            'Ubicacion_Tuberia': 'Subterránea',
            'Direccion_Flujo': 'Bidireccional',
            'Tipo_Ruptura': 'Circular',
            'Medida_Ruptura': '',
            'Unidad_Medida_Ruptura': 'mm',
            'Usar_Diametro_Equivalente': 'SI',
            'Tipo_Escape': 'Mínimo',
            'Distancia_Valvula_1_m': 200.0,
            'Distancia_Valvula_2_m': 180.0,
            'Año_Inicio': 2024,
            'Mes_Inicio': 3,
            'Dia_Inicio': 10,
            'Hora_Inicio': 8,
            'Minuto_Inicio': 0,
            'Año_Fin': 2024,
            'Mes_Fin': 3,
            'Dia_Fin': 10,
            'Hora_Fin': 12,
            'Minuto_Fin': 0
        }

        df_formato = pd.concat([
            df_formato,
            pd.DataFrame([ejemplo1]),
            pd.DataFrame([ejemplo2]),
            pd.DataFrame([ejemplo3])
        ], ignore_index=True)
        
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
        """Función auxiliar para crear el Excel con múltiples hojas mejoradas"""
        # Hoja principal con datos
        df_formato.to_excel(writer, sheet_name='Eventos', index=False)

        # Hoja de opciones válidas más clara
        opciones_data = {
            'Unidad_Presion': ['psig', 'bar', 'kPa'],
            'Ubicacion_Tuberia': ['Subterránea', 'Superficial'],
            'Direccion_Flujo': ['Unidireccional', 'Bidireccional'],
            'Tipo_Ruptura': ['Circular', 'Recta', 'Rectangular', 'Triangular', 'Total'],
            'Unidad_Medida_Ruptura': ['mm', 'in'],
            'Usar_Diametro_Equivalente': ['SI', 'NO'],
            'Tipo_Escape': ['Mínimo', 'Parcial', 'Total', '']
        }

        opciones_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in opciones_data.items()]))
        opciones_df.to_excel(writer, sheet_name='Opciones_Validas', index=False)
        
        # Hoja de diámetros de tubería comunes
        diametros_tuberia = pd.DataFrame({
            'Diametro_Pulgadas': [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0],
            'Descripcion': ['1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '3"', '4"', '6"', '8"', '10"', '12"', '16"', '20"', '24"']
        })
        diametros_tuberia.to_excel(writer, sheet_name='Diametros_Comunes', index=False)

        # Crear hoja de instrucciones mejoradas y más claras
        instrucciones = pd.DataFrame([
            ['═══════════════════════════════════════════════════════════════════'],
            ['         INSTRUCCIONES PARA CARGA MASIVA DE EVENTOS DE RUPTURA'],
            ['═══════════════════════════════════════════════════════════════════'],
            [''],
            ['┌─ PASO 1: ENTENDER EL FORMATO ─────────────────────────────────┐'],
            ['│ • Este archivo tiene 3 EJEMPLOS ya completados                 │'],
            ['│ • Ejemplo 1: Ruptura circular básica (Numero_Orden = 1)       │'],
            ['│ • Ejemplo 2: Ruptura recta (Numero_Orden = 2)                 │'],
            ['│ • Ejemplo 3: Flujo bidireccional (Numero_Orden = 3)           │'],
            ['└────────────────────────────────────────────────────────────────┘'],
            [''],
            ['┌─ PASO 2: LLENAR TUS DATOS ────────────────────────────────────┐'],
            ['│ OPCIÓN A: Elimina las 3 filas de ejemplo y agrega tus datos   │'],
            ['│ OPCIÓN B: Modifica los ejemplos con tus datos reales:         │'],
            ['│   - Cambia las coordenadas GPS a tu ubicación real            │'],
            ['│   - Modifica presión, diámetro y demás datos según tu evento  │'],
            ['│ • Usa las hojas "Opciones_Validas" y "Diametros_Comunes"      │'],
            ['└────────────────────────────────────────────────────────────────┘'],
            [''],
            ['┌─ PASO 3: SUBIR EL ARCHIVO ────────────────────────────────────┐'],
            ['│ • Guarda los cambios en Excel                                  │'],
            ['│ • Ve a la página de Carga Masiva                               │'],
            ['│ • Sube el archivo y espera los resultados                      │'],
            ['└────────────────────────────────────────────────────────────────┘'],
            [''],
            ['════════════════════ CAMPOS OBLIGATORIOS ═════════════════════════'],
            [''],
            ['📍 Numero_Orden: Número único del evento'],
            ['   ✓ Usar números enteros: 1, 2, 3, 4, 5, 10, 100, 1001, etc.'],
            ['   ✓ Puedes usar cualquier número entero positivo'],
            ['   ℹ️  Las filas con texto "EJEMPLO" o "CAMBIAR" se omitirán automáticamente'],
            [''],
            ['📍 Latitud y Longitud: Coordenadas GPS del evento'],
            ['   ✓ Usar Google Maps para obtenerlas'],
            ['   ✓ Latitud: entre -90 y 90 (ej: 4.6097)'],
            ['   ✓ Longitud: entre -180 y 180 (ej: -74.0817)'],
            [''],
            ['📍 Presion_Tuberia: Presión de operación'],
            ['   ✓ Número positivo (ej: 60, 45.5, 120)'],
            ['   ✓ Unidad_Presion: psig, bar, o kPa'],
            [''],
            ['📍 Diametro_Tuberia_Pulgadas: Tamaño nominal de la tubería'],
            ['   ✓ Ver hoja "Diametros_Comunes" para valores estándar'],
            ['   ✓ Ejemplos: 2, 4, 6, 8 (en pulgadas)'],
            [''],
            ['📍 Ubicacion_Tuberia: Dónde está instalada'],
            ['   ✓ Subterránea o Superficial'],
            [''],
            ['📍 Direccion_Flujo: Cómo fluye el gas'],
            ['   ✓ Unidireccional: una sola dirección de flujo'],
            ['   ✓ Bidireccional: flujo desde ambos lados'],
            ['   ⚠ Si es Bidireccional, llenar Distancia_Valvula_2_m'],
            [''],
            ['📍 Tipo_Ruptura: Forma de la rotura'],
            ['   ✓ Circular: agujero redondo'],
            ['   ✓ Recta: grieta lineal'],
            ['   ✓ Rectangular: rotura rectangular'],
            ['   ✓ Triangular: rotura triangular'],
            ['   ✓ Total: rotura completa de tubería'],
            [''],
            ['📍 Medida_Ruptura: Tamaño de la rotura'],
            ['   Para Circular/Rectangular/Triangular: diámetro o lado'],
            ['   Para Recta: longitud de la grieta'],
            ['   Para Total: dejar VACÍO'],
            ['   ✓ Unidad_Medida_Ruptura: mm o in'],
            [''],
            ['📍 Fechas y Horas: Cuándo inició y terminó la fuga'],
            ['   ✓ Año_Inicio, Mes_Inicio, Dia_Inicio (ej: 2024, 1, 15)'],
            ['   ✓ Hora_Inicio, Minuto_Inicio (formato 24h: ej: 14, 30)'],
            ['   ✓ Año_Fin, Mes_Fin, Dia_Fin'],
            ['   ✓ Hora_Fin, Minuto_Fin'],
            ['   ⚠ La fecha de fin debe ser posterior a la de inicio'],
            [''],
            ['══════════════════ CAMPOS OPCIONALES ══════════════════════════════'],
            [''],
            ['🔧 Usar_Diametro_Equivalente: SI o NO'],
            ['   • SI: el sistema calcula el tamaño de rotura automáticamente'],
            ['   • NO: debes especificar Medida_Ruptura manualmente'],
            ['   Si eliges SI, especifica Tipo_Escape:'],
            ['     - Mínimo: escape pequeño'],
            ['     - Parcial: escape moderado'],
            ['     - Total: escape máximo'],
            [''],
            ['🔧 Distancia_Valvula_1_m: Distancia a la válvula más cercana (metros)'],
            ['   ✓ Dejar vacío si no conoces: se usará valor por defecto'],
            [''],
            ['🔧 Distancia_Valvula_2_m: Distancia a la segunda válvula (metros)'],
            ['   ⚠ SOLO llenar si Direccion_Flujo = Bidireccional'],
            ['   ⚠ Dejar VACÍO si es Unidireccional'],
            [''],
            ['═══════════════════════ EJEMPLOS PRÁCTICOS ════════════════════════'],
            [''],
            ['EJEMPLO A: Fuga circular simple en tubería de 4"'],
            ['  Numero_Orden: 10'],
            ['  Latitud: 4.8156    Longitud: -75.6961'],
            ['  Presion_Tuberia: 60    Unidad_Presion: psig'],
            ['  Diametro_Tuberia_Pulgadas: 4'],
            ['  Ubicacion_Tuberia: Subterránea'],
            ['  Direccion_Flujo: Unidireccional'],
            ['  Tipo_Ruptura: Circular'],
            ['  Medida_Ruptura: 25.4    Unidad_Medida_Ruptura: mm'],
            ['  Usar_Diametro_Equivalente: NO'],
            ['  Distancia_Valvula_1_m: 100'],
            ['  Fecha inicio: 15/01/2024 10:30'],
            ['  Fecha fin: 15/01/2024 11:30'],
            [''],
            ['EJEMPLO B: Grieta en tubería con flujo bidireccional'],
            ['  Numero_Orden: 11'],
            ['  Tipo_Ruptura: Recta'],
            ['  Direccion_Flujo: Bidireccional'],
            ['  Medida_Ruptura: 50    Unidad_Medida_Ruptura: mm'],
            ['  Distancia_Valvula_1_m: 200'],
            ['  Distancia_Valvula_2_m: 180    ← IMPORTANTE: llenar porque es bidireccional'],
            [''],
            ['══════════════════════ CONSEJOS IMPORTANTES ═══════════════════════'],
            [''],
            ['✓ Usa punto (.) para decimales, NO coma: 4.5 en vez de 4,5'],
            ['✓ Revisa las hojas "Opciones_Validas" y "Diametros_Comunes"'],
            ['✓ Cada Numero_Orden debe ser ÚNICO (no repetir)'],
            ['✓ Usa números enteros para Numero_Orden: 1, 2, 3, 4, 5, 10, 100, 1001, etc.'],
            ['✓ Puedes ELIMINAR las 3 filas de ejemplo y agregar las tuyas'],
            ['✓ O puedes MODIFICAR los ejemplos con tus datos reales'],
            ['✓ Puedes copiar y pegar filas para crear eventos similares'],
            ['✓ Los cálculos complejos (flujo, volumen, etc.) se hacen automáticamente'],
            ['✓ Las filas con texto "EJEMPLO" o "CAMBIAR" se omiten automáticamente'],
            ['✗ NO cambiar los nombres de las columnas'],
            ['✗ NO dejar filas completamente vacías entre eventos'],
            [''],
            ['═══════════════════════════════════════════════════════════════════'],
            ['Si tienes dudas, contacta al administrador del sistema'],
            ['═══════════════════════════════════════════════════════════════════']
        ])
        instrucciones.to_excel(writer, sheet_name='📖 INSTRUCCIONES', index=False, header=False)

    def mapear_valores_español_a_sistema(valor, campo):
        """Traduce valores en español del Excel al formato del sistema"""
        mapeos = {
            'Ubicacion_Tuberia': {
                'Subterránea': 'sub',
                'Superficial': 'superficial',
                'subterranea': 'sub',
                'superficial': 'superficial'
            },
            'Direccion_Flujo': {
                'Unidireccional': 'uni',
                'Bidireccional': 'bi',
                'unidireccional': 'uni',
                'bidireccional': 'bi'
            },
            'Tipo_Ruptura': {
                'Circular': 'circ',
                'Recta': 'recta',
                'Rectangular': 'rect',
                'Triangular': 'tria',
                'Total': 'total',
                'circular': 'circ',
                'recta': 'recta',
                'rectangular': 'rect',
                'triangular': 'tria',
                'total': 'total'
            },
            'Usar_Diametro_Equivalente': {
                'SI': 'on',
                'NO': 'off',
                'Si': 'on',
                'No': 'off',
                'si': 'on',
                'no': 'off',
                'SÍ': 'on',
                'Sí': 'on',
                'sí': 'on'
            },
            'Tipo_Escape': {
                'Mínimo': 'min',
                'Parcial': 'parcial',
                'Total': 'total',
                'minimo': 'min',
                'parcial': 'parcial',
                'total': 'total',
                '': ''
            }
        }

        if campo in mapeos and str(valor) in mapeos[campo]:
            return mapeos[campo][str(valor)]
        return valor

    def validar_y_preparar_evento(form_data):
        """
        Valida y prepara un evento SIN insertarlo en la base de datos.

        Validaciones:
        - Numero_Orden: SIEMPRE obligatorio, único, y válido
        - Resto de campos: Opcionales, pero si tienen valor deben ser válidos

        Returns:
            {
                'valido': True/False,
                'skip': True/False (para filas de ejemplo),
                'evento_data': {...} si es válido,
                'error': "mensaje" si es inválido
            }
        """
        try:
            # ===== VALIDACIÓN 1: NUMERO DE ORDEN (SIEMPRE OBLIGATORIO) =====
            orden = form_data.get('Numero_Orden', '').strip() if isinstance(form_data.get('Numero_Orden', ''), str) else str(form_data.get('Numero_Orden', ''))

            # Verificar que no esté vacío
            if not orden or orden == '' or orden == 'nan':
                return {'valido': False, 'error': 'Numero_Orden es obligatorio y no puede estar vacío'}

            # Verificar que sea un número entero válido
            try:
                orden_int = int(float(orden))
                if orden_int <= 0:
                    return {'valido': False, 'error': f'Numero_Orden debe ser un número positivo (recibido: {orden})'}
                orden = str(orden_int)
            except (ValueError, TypeError):
                return {'valido': False, 'error': f'Numero_Orden debe ser un número entero (recibido: {orden})'}

            # Detectar filas de ejemplo (se omiten, no es error)
            # SOLO omitir si el texto empieza con EJEMPLO o CAMBIAR
            orden_str = str(orden).upper()
            if (orden_str.startswith('EJEMPLO') or
                orden_str.startswith('CAMBIAR')):
                return {'valido': True, 'skip': True, 'mensaje': f'Fila de ejemplo omitida: {orden}'}

            # ===== EXTRACCIÓN Y VALIDACIÓN DE CAMPOS OPCIONALES =====

            def validar_campo_texto(nombre_campo, valores_permitidos):
                """Valida campo categórico opcional"""
                valor = form_data.get(nombre_campo, '').strip() if isinstance(form_data.get(nombre_campo, ''), str) else str(form_data.get(nombre_campo, ''))
                if valor and valor != '' and valor != 'nan':
                    if valor not in valores_permitidos:
                        return {'valido': False, 'error': f'{nombre_campo} "{valor}" no es válido. Valores permitidos: {", ".join(valores_permitidos)}'}
                return {'valido': True}

            def validar_campo_numerico(nombre_campo, min_val=None, max_val=None, debe_ser_positivo=False):
                """Valida campo numérico opcional"""
                valor = form_data.get(nombre_campo, '').strip() if isinstance(form_data.get(nombre_campo, ''), str) else str(form_data.get(nombre_campo, ''))
                if valor and valor != '' and valor != 'nan':
                    try:
                        num_val = float(valor)
                        if debe_ser_positivo and num_val <= 0:
                            return {'valido': False, 'error': f'{nombre_campo} debe ser un número positivo (recibido: {valor})'}
                        if min_val is not None and num_val < min_val:
                            return {'valido': False, 'error': f'{nombre_campo} debe ser mayor o igual a {min_val} (recibido: {valor})'}
                        if max_val is not None and num_val > max_val:
                            return {'valido': False, 'error': f'{nombre_campo} debe ser menor o igual a {max_val} (recibido: {valor})'}
                    except (ValueError, TypeError):
                        return {'valido': False, 'error': f'{nombre_campo} debe ser un número (recibido: {valor})'}
                return {'valido': True}

            def validar_campo_entero(nombre_campo, min_val=None, max_val=None):
                """Valida campo entero opcional"""
                valor = form_data.get(nombre_campo, '').strip() if isinstance(form_data.get(nombre_campo, ''), str) else str(form_data.get(nombre_campo, ''))
                if valor and valor != '' and valor != 'nan':
                    try:
                        int_val = int(float(valor))
                        if min_val is not None and int_val < min_val:
                            return {'valido': False, 'error': f'{nombre_campo} debe estar entre {min_val}-{max_val} (recibido: {valor})'}
                        if max_val is not None and int_val > max_val:
                            return {'valido': False, 'error': f'{nombre_campo} debe estar entre {min_val}-{max_val} (recibido: {valor})'}
                    except (ValueError, TypeError):
                        return {'valido': False, 'error': f'{nombre_campo} debe ser un número entero (recibido: {valor})'}
                return {'valido': True}

            # Validar coordenadas GPS
            resultado = validar_campo_numerico('Latitud', min_val=-90, max_val=90)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_numerico('Longitud', min_val=-180, max_val=180)
            if not resultado['valido']:
                return resultado

            # Validar presión
            resultado = validar_campo_numerico('Presion_Tuberia', debe_ser_positivo=True)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_texto('Unidad_Presion', ['psig', 'bar', 'kPa'])
            if not resultado['valido']:
                return resultado

            # Validar diámetro
            resultado = validar_campo_numerico('Diametro_Tuberia_Pulgadas', debe_ser_positivo=True)
            if not resultado['valido']:
                return resultado

            # Validar campos categóricos
            resultado = validar_campo_texto('Ubicacion_Tuberia', ['Subterránea', 'Superficial'])
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_texto('Direccion_Flujo', ['Unidireccional', 'Bidireccional'])
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_texto('Tipo_Ruptura', ['Circular', 'Recta', 'Rectangular', 'Triangular', 'Total'])
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_texto('Unidad_Medida_Ruptura', ['mm', 'in'])
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_texto('Usar_Diametro_Equivalente', ['SI', 'NO'])
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_texto('Tipo_Escape', ['Mínimo', 'Parcial', 'Total'])
            if not resultado['valido']:
                return resultado

            # Validar medida de ruptura
            resultado = validar_campo_numerico('Medida_Ruptura', debe_ser_positivo=True)
            if not resultado['valido']:
                return resultado

            # Validar distancias
            resultado = validar_campo_numerico('Distancia_Valvula_1_m', debe_ser_positivo=True)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_numerico('Distancia_Valvula_2_m', debe_ser_positivo=True)
            if not resultado['valido']:
                return resultado

            # Validar fechas
            resultado = validar_campo_entero('Año_Inicio', min_val=1900, max_val=2100)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Mes_Inicio', min_val=1, max_val=12)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Dia_Inicio', min_val=1, max_val=31)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Hora_Inicio', min_val=0, max_val=23)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Minuto_Inicio', min_val=0, max_val=59)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Año_Fin', min_val=1900, max_val=2100)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Mes_Fin', min_val=1, max_val=12)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Dia_Fin', min_val=1, max_val=31)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Hora_Fin', min_val=0, max_val=23)
            if not resultado['valido']:
                return resultado

            resultado = validar_campo_entero('Minuto_Fin', min_val=0, max_val=59)
            if not resultado['valido']:
                return resultado

            # ===== VALIDACIÓN DE REGLAS DE NEGOCIO =====

            # Regla 1: Si Direccion_Flujo es Bidireccional, Distancia_Valvula_2_m no puede estar vacía
            direccion_raw = form_data.get('Direccion_Flujo', '').strip() if isinstance(form_data.get('Direccion_Flujo', ''), str) else str(form_data.get('Direccion_Flujo', ''))
            distancia_2 = form_data.get('Distancia_Valvula_2_m', '').strip() if isinstance(form_data.get('Distancia_Valvula_2_m', ''), str) else str(form_data.get('Distancia_Valvula_2_m', ''))

            if direccion_raw == 'Bidireccional':
                if not distancia_2 or distancia_2 == '' or distancia_2 == 'nan':
                    return {'valido': False, 'error': 'Direccion_Flujo es Bidireccional pero falta Distancia_Valvula_2_m'}

            # Regla 2: Si Tipo_Ruptura es Total, Medida_Ruptura debe estar vacía
            forma_raw = form_data.get('Tipo_Ruptura', '').strip() if isinstance(form_data.get('Tipo_Ruptura', ''), str) else str(form_data.get('Tipo_Ruptura', ''))
            medida_ruptura = form_data.get('Medida_Ruptura', '').strip() if isinstance(form_data.get('Medida_Ruptura', ''), str) else str(form_data.get('Medida_Ruptura', ''))

            if forma_raw == 'Total':
                if medida_ruptura and medida_ruptura != '' and medida_ruptura != 'nan':
                    return {'valido': False, 'error': 'Tipo_Ruptura "Total" no debe tener Medida_Ruptura. Déjalo vacío'}

            # Regla 3: Si Usar_Diametro_Equivalente es SI, Tipo_Escape no puede estar vacío
            usar_equiv_raw = form_data.get('Usar_Diametro_Equivalente', '').strip() if isinstance(form_data.get('Usar_Diametro_Equivalente', ''), str) else str(form_data.get('Usar_Diametro_Equivalente', ''))
            escape_raw = form_data.get('Tipo_Escape', '').strip() if isinstance(form_data.get('Tipo_Escape', ''), str) else str(form_data.get('Tipo_Escape', ''))

            if usar_equiv_raw == 'SI':
                if not escape_raw or escape_raw == '' or escape_raw == 'nan':
                    return {'valido': False, 'error': 'Usar_Diametro_Equivalente "SI" requiere especificar Tipo_Escape (Mínimo, Parcial o Total)'}

            # Si llegamos aquí, la validación básica pasó
            # Ahora llamamos a la función original para preparar el evento (sin insertar)
            resultado = procesar_evento_desde_excel(form_data)

            if resultado['status'] == 'exito':
                return {'valido': True, 'evento_data': resultado['evento_data']}
            elif resultado['status'] == 'skip':
                return {'valido': True, 'skip': True, 'mensaje': resultado.get('error', 'Fila omitida')}
            else:
                return {'valido': False, 'error': resultado['error']}

        except Exception as e:
            return {'valido': False, 'error': f'Error inesperado en validación: {str(e)}'}

    def procesar_evento_desde_excel(form_data):
        """Procesar un evento usando los mismos cálculos que /Resultados con nuevo formato"""
        try:
            # Extraer datos del nuevo formato en español
            orden = form_data.get('Numero_Orden', '')
            latitud = form_data.get('Latitud', '')
            longitud = form_data.get('Longitud', '')
            ubicacion = f"{latitud},{longitud}" if latitud and longitud else ''

            presionTub = form_data.get('Presion_Tuberia', '')
            presionUni = form_data.get('Unidad_Presion', 'psig')
            Tdiametro = form_data.get('Diametro_Tuberia_Pulgadas', '')

            # Mapear valores en español a códigos del sistema
            subte_raw = form_data.get('Ubicacion_Tuberia', 'Subterránea')
            subte = mapear_valores_español_a_sistema(subte_raw, 'Ubicacion_Tuberia')

            direccion_raw = form_data.get('Direccion_Flujo', 'Unidireccional')
            direccion = mapear_valores_español_a_sistema(direccion_raw, 'Direccion_Flujo')

            forma_raw = form_data.get('Tipo_Ruptura', 'Circular')
            forma = mapear_valores_español_a_sistema(forma_raw, 'Tipo_Ruptura')

            # Medida de ruptura y unidades
            Fdiametro = form_data.get('Medida_Ruptura', '')
            FdiametroUni = form_data.get('Unidad_Medida_Ruptura', 'mm')
            longitud = Fdiametro  # Para rupturas rectas, es la misma medida
            longitudUni = FdiametroUni

            # Diámetros equivalentes
            usar_diame_equiv_raw = form_data.get('Usar_Diametro_Equivalente', 'NO')
            usar_diame_equiv = mapear_valores_español_a_sistema(usar_diame_equiv_raw, 'Usar_Diametro_Equivalente')
            equi = 'on' if usar_diame_equiv == 'on' else None

            escape_raw = form_data.get('Tipo_Escape', '')
            escape = mapear_valores_español_a_sistema(escape_raw, 'Tipo_Escape')
            if not escape:
                escape = 'min'  # Valor por defecto

            # Distancias (ya en metros)
            Tlargo = form_data.get('Distancia_Valvula_1_m', '')
            TlargoUni = 'm'  # Siempre en metros en el nuevo formato
            Tlargo2 = form_data.get('Distancia_Valvula_2_m', '')
            TlargoUni2 = 'm'

            # Construir fechas desde componentes individuales
            try:
                año_inicio = int(form_data.get('Año_Inicio', 2024))
                mes_inicio = int(form_data.get('Mes_Inicio', 1))
                dia_inicio = int(form_data.get('Dia_Inicio', 1))
                hora_inicio = int(form_data.get('Hora_Inicio', 0))
                minuto_inicio = int(form_data.get('Minuto_Inicio', 0))

                año_fin = int(form_data.get('Año_Fin', 2024))
                mes_fin = int(form_data.get('Mes_Fin', 1))
                dia_fin = int(form_data.get('Dia_Fin', 1))
                hora_fin = int(form_data.get('Hora_Fin', 1))
                minuto_fin = int(form_data.get('Minuto_Fin', 0))

                tiempoInicio = f"{año_inicio:04d}-{mes_inicio:02d}-{dia_inicio:02d}T{hora_inicio:02d}:{minuto_inicio:02d}"
                tiempoFin = f"{año_fin:04d}-{mes_fin:02d}-{dia_fin:02d}T{hora_fin:02d}:{minuto_fin:02d}"
            except (ValueError, TypeError) as e:
                return {'status': 'error', 'error': f'Error en formato de fecha/hora: {str(e)}. Verifica que todos los campos de fecha sean números válidos'}

            # Validación básica: SOLO Numero_Orden es obligatorio
            # Todos los demás campos son opcionales según los nuevos requerimientos
            if not orden:
                return {'status': 'error', 'error': 'Numero_Orden es obligatorio'}

            # Validación especial para ejemplos (solo omitir filas claramente marcadas como ejemplo)
            # SOLO omitir si el texto empieza con EJEMPLO o CAMBIAR
            orden_str = str(orden).upper()
            if orden_str.startswith('EJEMPLO') or orden_str.startswith('CAMBIAR'):
                return {'status': 'skip', 'error': f'Fila de ejemplo omitida: {orden}'}
            
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

            # NO insertar en base de datos, solo retornar el objeto preparado
            return {'status': 'exito', 'evento_data': evento_data}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    @app.route('/ProcesarCargaMasiva', methods=['POST'])
    def procesar_carga_masiva():
        """Procesar carga masiva con validación en dos fases (validar todo primero, insertar después)"""
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

            # ===== FASE 1: VALIDAR TODOS LOS EVENTOS (sin insertar) =====
            eventos_validados = []
            eventos_omitidos = 0
            errores_validacion = []
            ordenes_validadas = []

            print(f"=== INICIANDO VALIDACIÓN DE {len(df)} FILAS ===")

            for index, row in df.iterrows():
                try:
                    # Saltar filas completamente vacías
                    if pd.isna(row.get('Numero_Orden')):
                        continue

                    # Simular el llenado del formulario de crear evento
                    form_data = {}
                    for col in df.columns:
                        form_data[col] = '' if pd.isna(row[col]) else str(row[col])

                    # DEBUG: Imprimir datos de la fila para diagnóstico
                    if index + 2 == 4:  # Fila 4 en Excel
                        print(f"=== DEBUG FILA 4 ===")
                        print(f"Numero_Orden: [{form_data.get('Numero_Orden')}]")
                        print(f"Latitud: [{form_data.get('Latitud')}]")
                        print(f"Longitud: [{form_data.get('Longitud')}]")
                        print(f"Latitud vacía: {form_data.get('Latitud') == ''}")
                        print(f"Longitud vacía: {form_data.get('Longitud') == ''}")

                    # Validar usando la nueva función (NO inserta)
                    resultado = validar_y_preparar_evento(form_data)

                    if resultado.get('skip'):
                        # Fila de ejemplo omitida
                        eventos_omitidos += 1
                        print(f"Fila {index + 2}: {resultado.get('mensaje', 'Omitida')}")
                    elif resultado['valido']:
                        # Evento válido, guardarlo en lista temporal
                        eventos_validados.append(resultado['evento_data'])
                        ordenes_validadas.append(resultado['evento_data']['orden'])
                        print(f"Fila {index + 2}: ✓ Válido (Orden: {resultado['evento_data']['orden']})")
                    else:
                        # Evento inválido
                        error_msg = f"Fila {index + 2} (Orden: {row.get('Numero_Orden', 'Sin orden')}): {resultado['error']}"
                        errores_validacion.append(error_msg)
                        print(f"Fila {index + 2}: ✗ ERROR - {resultado['error']}")

                except Exception as e:
                    error_msg = f"Fila {index + 2} (Orden: {row.get('Numero_Orden', 'Sin orden')}): Error inesperado - {str(e)}"
                    errores_validacion.append(error_msg)
                    print(f"Fila {index + 2}: ✗ EXCEPCIÓN - {str(e)}")

            # ===== VALIDACIÓN ADICIONAL: Órdenes duplicadas en el archivo =====
            ordenes_duplicadas_archivo = [orden for orden in ordenes_validadas if ordenes_validadas.count(orden) > 1]
            if ordenes_duplicadas_archivo:
                ordenes_unicas = list(set(ordenes_duplicadas_archivo))
                for orden in ordenes_unicas:
                    errores_validacion.append(f"ARCHIVO: Numero_Orden '{orden}' aparece duplicado en múltiples filas")

            # ===== VALIDACIÓN ADICIONAL: Órdenes que ya existen en la base de datos =====
            if ordenes_validadas:
                try:
                    from functions.conect import getDataBase
                    db = getDataBase()

                    # DEBUG: Ver qué tipos estamos buscando
                    print(f"=== DEBUG VALIDACIÓN DUPLICADOS ===")
                    print(f"Órdenes a validar (type): {[(o, type(o).__name__) for o in ordenes_validadas[:3]]}")

                    # Buscar con AMBOS tipos: string y numérico (int/float)
                    # Convertir cada orden a múltiples formatos para asegurar coincidencia
                    ordenes_busqueda = []
                    for orden in ordenes_validadas:
                        ordenes_busqueda.append(orden)  # String original
                        try:
                            # Intentar convertir a int
                            ordenes_busqueda.append(int(orden))
                        except (ValueError, TypeError):
                            pass
                        try:
                            # Intentar convertir a float
                            ordenes_busqueda.append(float(orden))
                        except (ValueError, TypeError):
                            pass

                    print(f"Órdenes a buscar (multiformato): {ordenes_busqueda[:9]}")

                    # Buscar si alguna de las órdenes validadas ya existe en la BD
                    eventos_existentes_cursor = db['events'].find(
                        {'orden': {'$in': ordenes_busqueda}},
                        {'orden': 1, '_id': 0}
                    )
                    # Convertir cursor a lista
                    ordenes_db_raw = [evento['orden'] for evento in eventos_existentes_cursor]

                    print(f"Órdenes encontradas en BD (type): {[(o, type(o).__name__) for o in ordenes_db_raw]}")

                    # Convertir todas las órdenes de BD a string para comparación
                    ordenes_db_str = [str(o) for o in ordenes_db_raw]

                    # Verificar cuáles de nuestras órdenes validadas están duplicadas
                    for orden_validada in ordenes_validadas:
                        if orden_validada in ordenes_db_str:
                            errores_validacion.append(f"BASE DE DATOS: Numero_Orden '{orden_validada}' ya existe en la base de datos")

                except Exception as e:
                    print(f"Advertencia: No se pudo verificar duplicados en BD: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # No detener el proceso por este error, solo registrarlo

            print(f"=== VALIDACIÓN COMPLETADA ===")
            print(f"Eventos validados: {len(eventos_validados)}")
            print(f"Eventos omitidos: {eventos_omitidos}")
            print(f"Errores encontrados: {len(errores_validacion)}")

            # ===== FASE 2: SI HAY ERRORES, ABORTAR (no insertar nada) =====
            if errores_validacion:
                print(f"❌ ABORTANDO: Se encontraron {len(errores_validacion)} errores. NO se insertó nada.")
                for i, error in enumerate(errores_validacion[:5], 1):
                    print(f"  Error {i}: {error}")

                return {
                    'exito': False,
                    'eventos_creados': 0,
                    'eventos_validados': len(eventos_validados),
                    'eventos_fallidos': len(errores_validacion),
                    'eventos_omitidos': eventos_omitidos,
                    'errores': errores_validacion,  # Retornar TODOS los errores
                    'mensaje': f'⚠️ Se encontraron {len(errores_validacion)} errores. NO se guardó ningún evento en la base de datos.'
                }

            # ===== FASE 3: SI TODO ES VÁLIDO, INSERTAR TODOS LOS EVENTOS =====
            print(f"✅ VALIDACIÓN EXITOSA: Insertando {len(eventos_validados)} eventos...")

            eventos_insertados = 0
            errores_insercion = []

            for evento_data in eventos_validados:
                try:
                    response = createEvent(evento_data)
                    if response.get('status') == 'Orden creada con éxito':
                        eventos_insertados += 1
                        print(f"  ✓ Insertado: {evento_data['orden']}")
                    else:
                        error_msg = f"Orden {evento_data['orden']}: {response.get('status', 'Error desconocido')}"
                        errores_insercion.append(error_msg)
                        print(f"  ✗ Error insertando {evento_data['orden']}: {response.get('status')}")
                except Exception as e:
                    error_msg = f"Orden {evento_data['orden']}: Error inesperado - {str(e)}"
                    errores_insercion.append(error_msg)
                    print(f"  ✗ Excepción insertando {evento_data['orden']}: {str(e)}")

            print(f"=== INSERCIÓN COMPLETADA ===")
            print(f"Eventos insertados: {eventos_insertados}")
            print(f"Errores de inserción: {len(errores_insercion)}")

            # Si hubo errores en la inserción (no debería pasar si la validación fue correcta)
            if errores_insercion:
                return {
                    'exito': False,
                    'eventos_creados': eventos_insertados,
                    'eventos_validados': len(eventos_validados),
                    'eventos_fallidos': len(errores_insercion),
                    'eventos_omitidos': eventos_omitidos,
                    'errores': errores_insercion,
                    'mensaje': f'⚠️ Se insertaron {eventos_insertados} eventos pero {len(errores_insercion)} fallaron durante la inserción.'
                }

            # Todo exitoso
            return {
                'exito': True,
                'eventos_creados': eventos_insertados,
                'eventos_validados': len(eventos_validados),
                'eventos_fallidos': 0,
                'eventos_omitidos': eventos_omitidos,
                'errores': [],
                'mensaje': f'✅ Todos los eventos fueron validados e insertados exitosamente ({eventos_insertados} eventos).'
            }

        except Exception as e:
            print(f"ERROR CRÍTICO: {str(e)}")
            return {'error': f'Error procesando archivo: {str(e)}'}, 500