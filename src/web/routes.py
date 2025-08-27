import os
import io
import datetime
import numpy as np
import shutil
from io import BytesIO
import requests
from functools import wraps

from flask import Flask, request, send_file, render_template, make_response, redirect, url_for

from functions.users import loginUserV2, createUser
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
            resp.set_cookie('tipo_user', 'worker')
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