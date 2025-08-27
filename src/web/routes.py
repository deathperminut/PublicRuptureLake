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
import pandas as pd

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
            fila = response['info']
            # Procesar datos del evento para mostrar en template
            # (código simplificado - necesitarás adaptar la lógica completa de rl.py)
            resp = make_response(render_template('reporte.html', **fila))
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
        # Procesar los datos del formulario de evento
        orden = request.form.get('orden')
        ubicacion = request.form.get('ubicacion')
        presion = request.form.get('presion', '0')
        presion_uni = request.form.get('presionUni', 'psig')
        subte = request.form.get('subte', 'no')
        diame_tube = request.form.get('DiameTube', '0')
        flujo = request.form.get('Flujo', 'uni')
        forma = request.form.get('Forma', 'circ')
        tiempo_inicio = request.form.get('tiempoInicio')
        tiempo_fin = request.form.get('tiempoFin')
        dist_tube = request.form.get('DistTube', '0')
        dist_tube_uni = request.form.get('DistTubeUni', 'm')
        dist_tube2 = request.form.get('DistTube2', '0')
        dist_tube_uni2 = request.form.get('DistTubeUni2', 'm')
        
        try:
            # Crear objeto para la base de datos
            evento_data = {
                'orden': orden,
                'ubicacion': ubicacion,
                'presion': float(presion) if presion else 0,
                'presion_uni': presion_uni,
                'subte': subte,
                'dist_tube': float(dist_tube) if dist_tube else 0,
                'dist_tube_uni': dist_tube_uni,
                'dist_tube2': float(dist_tube2) if dist_tube2 else 0,
                'dist_tube_uni2': dist_tube_uni2,
                'diame_tube': float(diame_tube) if diame_tube else 0,
                'direccion': flujo,
                'forma': forma,
                'inicio': tiempo_inicio,
                'fin': tiempo_fin,
                # Campos calculados básicos
                'area': 0.0,
                'flujo': 0.0,
                'volumen': 0.0,
                'volumen_muerto': 0.0,
                'volumen_fuga': 0.0,
                'aprobado': 'no',
                'Material': 'Acero',
                'Unidades': 'in',
                'medida_rupt': '',
                'medida_uni': '',
                'presion_atmos': 1.0,
                'diame_equi': 'no',
                'duracion': 0,
                'hora_reg': datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            }
            
            # Guardar en base de datos
            response = createEvent(evento_data)
            
            if response.get('status') == 'Orden creada con éxito':
                # Renderizar resultados con los datos
                resp = make_response(render_template('resultados.html', 
                    orden=orden,
                    ubicacion=ubicacion,
                    presion_tube=presion,
                    forma=forma,
                    flujo=0.0,
                    volumen=0.0,
                    area=0.0,
                    horas=0,
                    minutos=0,
                    año_reg=datetime.datetime.now().year,
                    mes_reg=datetime.datetime.now().month,
                    dia_reg=datetime.datetime.now().day
                ))
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
        # Esta ruta maneja la actualización de eventos
        resp = make_response(redirect('/Reporte', code=307))
        return resp

    @app.route('/Editar', methods=['POST'])
    def editar():
        # Esta ruta carga el formulario de edición
        resp = make_response(render_template('editar.html'))
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