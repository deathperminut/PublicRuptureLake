import numpy as np
import requests

# (Copio todo el contenido del archivo modelos.py original)
R_vals = np.array([0.0, 0.25, 0.5, 0.75, 1.0])

# Diccionario de coeficientes A para cada material y R conocido
coef_A = {
    "Acero": {
        1.0: lambda d, L: (8e-5 * d**2 - 0.0126 * d + 0.938) * L**(-0.0006 * d + 0.5011),
        0.75: lambda d, L: (8e-5 * d**2 - 0.0087 * d + 0.9977) * L**(-0.0016 * d + 0.4976),
        0.5: lambda d, L: (-2e-10*d**2 + 7e-8*d - 5e-6)*L**2 + (4e-6*d**2 - 6e-4*d + 0.0288)*L + (0.0002*d**2 - 0.024*d + 7.4625),
        0.25: lambda d, L: (1e-6*d**2 - 0.0002*d + 0.0104)*L + (6e-5*d**2 - 0.0085*d + 26.344),
        0.0: lambda d, L: 0
    },
    "Polietileno": {
        1.0: lambda d, L: (1e-6*d**2 - 0.0019*d + 0.5947) * L**(-5e-6*d**2 + 4e-5*d + 0.4769),
        0.75: lambda d, L: (3e-5*d**2 - 0.0023*d + 0.8083) * L**(-1e-5*d**2 + 3e-6*d + 0.4343),
        0.5: lambda d, L: (-2e-12*d**2 + 2e-8*d - 2e-6)*L**2 + (-1e-7*d**2 - 8e-5*d + 0.0131)*L + (7e-6*d**2 - 0.0035*d + 6.8071),
        0.25: lambda d, L: (-4e-10*d**2 + 4e-8*d - 8e-7)*L**2 + (3e-8*d**2 - 4e-5*d + 0.0047)*L + (1e-6*d**2 - 0.0002*d + 26.041),
        0.0: lambda d, L: 0
    }
}

# Cálculo de coeficiente A dado un R puntual
def calcular_A(d_tube, longitud, R, material):
    if longitud <= 50:
        if material == "Acero":
            if R == 1.0:
                A = (-1.42655e-7 * d_tube**2 + 2.15052e-5 * d_tube - 0.000932527) * longitud**2 + \
                    (1.83867e-5 * d_tube**2 - 0.00286611 * d_tube + 0.14095) * longitud + \
                    (2.24415e-5 * d_tube**2 - 0.00319416 * d_tube + 1.74606)
                return A
            elif R == 0.75:
                A = (-9e-8 * d_tube**2 + 1e-5 * d_tube - 0.0005) * longitud**2 + \
                    (1.4522e-5 * d_tube**2 - 0.002207 * d_tube + 0.101461) * longitud + \
                    (6.3602e-6 * d_tube**2 - 0.000863 * d_tube + 2.92214)
                return A
        elif material == "Polietileno":
            if R == 1.0:
                A = (0.00000285152 * d_tube - 0.000335116) * longitud**2 + \
                    (-0.000440495 * d_tube + 0.0622487) * longitud + \
                    (-0.000314108 * d_tube + 1.6562)
                return A
            elif R == 0.75:
                A = (0.000001 * d_tube - 0.0001) * longitud**2 + \
                    (0.000309778 * d_tube + 0.0405944) * longitud + \
                    (-0.0000549869 * d_tube + 2.89734)
                return A

    return coef_A[material][R](d_tube, longitud)

# Interpolación de alpha según material y L para un R puntual
def alpha(L, R, material):
    if material == "Acero":
        if R == 1.0 and L > 1600:
            return 0.518123 * L**(-0.999574)
        elif R == 0.75 and L > 1400:
            return 0.522976 * L**(-0.999541)
        elif R == 0.5 and L > 900:
            return 0.517503 * L**(-0.999412)
        elif R == 0.25 and L > 1400:
            return 0.229286 * L**(-0.999637)
    elif material == "Polietileno":
        if R in [1.0, 0.75] and L > 1400:
            return 0.517845 * L**(-0.999502)
        elif R == 0.5 and L > 1200:
            return 0.517845 * L**(-0.999502)
        elif R == 0.25 and L > 1400:
            return 0.159491 * L**(-0.999617)
    return None

#Factor multiplicativo por rotura total
def factor_rotura_total(longitud, material):
    if material == "Acero":
        if longitud <= 10:
            return 4.006269643
        elif longitud <= 90:
            return 1.288833046
        elif longitud <= 600:
            return 1.044385934
        else:
            return 1.007683532
    elif material == "Polietileno":
        if longitud <= 10:
            return 4.05805243
        elif longitud <= 90:
            return 1.296293257
        elif longitud <= 600:
            return 1.045834945
        else:
            return 1.007896708
    return 1

# Función principal para calcular el caudal
def modelo_utpSuper(d_fuga, d_tube, p_tube, p_atmos, subte, direccion, forma, longitud, material, R):
    A = calcular_A(d_tube, longitud, R, material)
    if A == 0:
        return 0

    if subte == "subterranea":
        flujo = 0.55 * 0.168 * (1 + np.power((d_tube / d_tube), 4)) * d_tube**2 * (p_tube + p_atmos) / A
    else:
        flujo = 0.55 * (1 + 0.34 * np.power((d_tube / d_tube), 4)) * d_tube**2 * (p_tube + p_atmos) / A
    
    if forma == "Total":
        flujo *= factor_rotura_total(longitud, material)
        if direccion == "bi":
            flujo *= 2
    
    return flujo

# L0 según material y R
def obtener_L0(R, material):
    if material == "Acero":
        if R >= 1.0:
            return 1600
        elif R >= 0.75:
            return 1400
        elif R >= 0.5:
            return 900
        else:
            return 1400
    elif material == "Polietileno":
        if R >= 0.75:
            return 1400
        elif R >= 0.5:
            return 1200
        else:
            return 1400
    return longitud

def diametro_hidraulico(a,p,d_tube):
    formula= ((a*4)/np.pi)
    d_apa = np.sqrt(formula)
    
    if d_apa<=d_tube:
        diametro=d_apa
    else:
        diametro=d_tube
    return diametro

def calc_area(forma, diametro, alto, largo, longitud):
    area = 0
    if forma == "circ":
        area = np.pi * np.square(diametro/2)
    elif forma == "rect":
        area = alto * largo
    elif forma == "tria":
        area = alto * largo / 2
    elif forma == "recta":
        #Valor preestablecido de alto en mm
        a = 1.5
        area = longitud * a
    else:
        area = np.pi * alto * largo

    return area

def calc_peri(forma, diametro, alto, largo, longitud):
    peri = 0
    if forma == "circ":
        peri = np.pi * diametro
    elif forma == "rect":
        peri = 2 * (alto + largo)
    elif forma == "tria":
        peri = 3 * largo
    elif forma == "recta":
        #Valor preestablecido de alto en mm
        a = 1.5
        peri = 2 * (longitud + a)
    else:
        peri = 2 * np.pi * np.sqrt((np.square(alto) + np.square(largo)) / 2)

    return peri

def vol_muerto(diametro, longitud):
    vol = np.pi * np.square(diametro/2000) * longitud
    return vol

def diametro_interno(diametro):
    d_int = 0
    #Valores retornados son en mm
    if diametro == 0.5:
        d_int = 16.72
    elif diametro == 0.75:
        d_int = 21.88
    elif diametro == 1:
        d_int = 27.36
    elif diametro == 1.25:
        d_int = 34.42
    elif diametro == 1.5:
        d_int = 39.36
    elif diametro == 2:
        d_int = 49.32
    elif diametro == 2.25:
        d_int = 59.14
    elif diametro == 3:
        d_int = 73.74
    elif diametro == 4:
        d_int = 93.52
    elif diametro == 6:
        d_int = 137.72
    elif diametro == 8:
        d_int = 179.22
    elif diametro == 21:
        d_int = 18.18
    elif diametro == 26:
        d_int = 23.63
    elif diametro == 33:
        d_int = 30.2
    elif diametro == 42:
        d_int = 38.14
    elif diametro == 48:
        d_int = 43.68
    elif diametro == 60:
        d_int = 54.58
    elif diametro == 73:
        d_int = 66.07
    elif diametro == 88:
        d_int = 80.42
    elif diametro == 114:
        d_int = 103.42
    elif diametro == 168:
        d_int = 152.22
    elif diametro == 200:
        d_int = 181.22
# acero in
    elif diametro == 0.501:
        d_int = 15.79
    elif diametro == 0.751:
        d_int = 19.91
    elif diametro == 1.001:
        d_int = 26.64
    elif diametro == 1.251:
        d_int = 35.05
    elif diametro == 1.501:
        d_int = 40.89
    elif diametro == 2.001:
        d_int = 52.5
    elif diametro == 2.501:
        d_int = 62.07
    elif diametro == 3.001:
        d_int = 77.92
    elif diametro ==  4.001:
        d_int = 102.26
    elif diametro == 6.001:
        d_int = 154.05
    elif diametro == 8.001:
        d_int = 202.71
    elif diametro == 10.001:
        d_int = 254.5
    elif diametro == 12.001:
        d_int = 303.22
    elif diametro == 14.001:
        d_int = 330.2
    elif diametro == 16.001:
        d_int = 381.0
    elif diametro == 18.001:
        d_int = 431.8
    elif diametro == 20.001:
        d_int = 482.6

#acero milimetros
    elif diametro == 20:
        d_int = 13.6
    elif diametro == 25:
        d_int = 18.6
    elif diametro == 30:
        d_int = 22
    elif diametro == 38:
        d_int = 28
    elif diametro == 44.5:
        d_int = 34.5
    elif diametro == 51:
        d_int = 41
    elif diametro == 54:
        d_int = 44
    elif diametro == 57:
        d_int = 46.2
    elif diametro == 63.5:
        d_int = 52.7
    elif diametro == 70:
        d_int = 57.4
    elif diametro == 82.5:
        d_int = 71.3
    elif diametro == 108:
        d_int = 95.4
    elif diametro == 127:
        d_int = 112.8
    elif diametro == 133:
        d_int = 118.8
    elif diametro == 152:
        d_int = 136.4
    elif diametro == 159:
        d_int = 143
    elif diametro == 177.8:
        d_int = 161.8
    elif diametro == 244.5:
        d_int = 226.9
    elif diametro == 298.5:
      d_int = 278.5
    return d_int

def diametro_interno1(diametro):
    Material="Polietileno"
    #Valores retornados son en mm
    if diametro == 0.5:
        Material="Polietileno"
    elif diametro == 0.75:
        Material="Polietileno"
    elif diametro == 1:
        Material="Polietileno"
    elif diametro == 1.25:
        Material="Polietileno"
    elif diametro == 1.5:
        Material="Polietileno"
    elif diametro == 2:
        Material="Polietileno"
    elif diametro == 2.25:
        Material="Polietileno"
    elif diametro == 3:
        Material="Polietileno"
    elif diametro == 4:
        Material="Polietileno"
    elif diametro == 6:
        Material="Polietileno"
    elif diametro == 8:
        Material="Polietileno"
    elif diametro == 21:
        Material="Polietileno"
    elif diametro == 26:
        Material="Polietileno"
    elif diametro == 33:
        Material="Polietileno"
    elif diametro == 42:
        Material="Polietileno"
    elif diametro == 48:
        Material="Polietileno"
    elif diametro == 60:
        Material="Polietileno"
    elif diametro == 73:
        Material="Polietileno"
    elif diametro == 88:
        Material="Polietileno"
    elif diametro == 114:
        Material="Polietileno"
    elif diametro == 168:
        Material="Polietileno"
    elif diametro == 200:
        Material="Polietileno"
# acero in
    elif diametro == 0.501:
        Material="Acero"
    elif diametro == 0.751:
        Material="Acero"
    elif diametro == 1.001:
        Material="Acero"
    elif diametro == 1.251:
        Material="Acero"
    elif diametro == 1.501:
        Material="Acero"
    elif diametro == 2.001:
        Material="Acero"
    elif diametro == 2.501:
        Material="Acero"
    elif diametro == 3.001:
        Material="Acero"
    elif diametro ==  4.001:
        Material="Acero"
    elif diametro == 6.001:
        Material="Acero"
    elif diametro == 8.001:
        Material="Acero"
    elif diametro == 10.001:
        Material="Acero"
    elif diametro == 12.001:
        Material="Acero"
    elif diametro == 14.001:
        Material="Acero"
    elif diametro == 16.001:
        Material="Acero"
    elif diametro == 18.001:
        Material="Acero"
    elif diametro == 20.001:
        Material="Acero"

#acero milimetros
    elif diametro == 20:
        Material="Acero"
    elif diametro == 25:
        Material="Acero"
    elif diametro == 30:
        Material="Acero"
    elif diametro == 38:
        Material="Acero"
    elif diametro == 44.5:
        Material="Acero"
    elif diametro == 51:
        Material="Acero"
    elif diametro == 54:
        Material="Acero"
    elif diametro == 57:
        Material="Acero"
    elif diametro == 63.5:
        Material="Acero"
    elif diametro == 70:
        Material="Acero"
    elif diametro == 82.5:
        Material="Acero"
    elif diametro == 108:
        Material="Acero"
    elif diametro == 127:
        Material="Acero"
    elif diametro == 133:
        Material="Acero"
    elif diametro == 152:
        Material="Acero"
    elif diametro == 159:
        Material="Acero"
    elif diametro == 177.8:
        Material="Acero"
    elif diametro == 244.5:
        Material="Acero"
    elif diametro == 298.5:
        Material="Acero"
    return Material

def diametro_interno2(diametro):
    d_int = 0
    Material="Polietileno"
    Unidades="in"
    #Valores retornados son en mm
    if diametro == 0.5:
        Material="Polietileno"
        Unidades="in"
    elif diametro == 0.75:
        Material="Polietileno"
        Unidades="in"
    elif diametro == 1:
        d_int = 27.36
        Material="Polietileno"
        Unidades="in"
    elif diametro == 1.25:
        d_int = 34.42
        Material="Polietileno"
        Unidades="in"
    elif diametro == 1.5:
        d_int = 39.36
        Material="Polietileno"
        Unidades="in"
    elif diametro == 2:
        d_int = 49.32
        Material="Polietileno"
        Unidades="in"
    elif diametro == 2.25:
        d_int = 59.14
        Material="Polietileno"
        Unidades="in"
    elif diametro == 3:
        d_int = 73.74
        Material="Polietileno"
        Unidades="in"
    elif diametro == 4:
        d_int = 93.52
        Material="Polietileno"
        Unidades="in"
    elif diametro == 6:
        d_int = 137.72
        Material="Polietileno"
        Unidades="in"
    elif diametro == 8:
        d_int = 179.22
        Material="Polietileno"
        Unidades="in"
    elif diametro == 21:
        d_int = 18.18
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 26:
        d_int = 23.63
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 33:
        d_int = 30.2
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 42:
        d_int = 38.14
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 48:
        d_int = 43.68
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 60:
        d_int = 54.58
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 73:
        d_int = 66.07
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 88:
        d_int = 80.42
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 114:
        d_int = 103.42
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 168:
        d_int = 152.22
        Material="Polietileno"
        Unidades="mm"
    elif diametro == 200:
        d_int = 181.22
        Material="Polietileno"
        Unidades="mm"
# acero in
    elif diametro == 0.501:
        d_int = 15.79
        Material="Acero"
        Unidades="in"
    elif diametro == 0.751:
        d_int = 19.91
        Material="Acero"
        Unidades="in"
    elif diametro == 1.001:
        d_int = 26.64
        Material="Acero"
        Unidades="in"
    elif diametro == 1.251:
        d_int = 35.05
        Material="Acero"
        Unidades="in"
    elif diametro == 1.501:
        d_int = 40.89
        Material="Acero"
        Unidades="in"
    elif diametro == 2.001:
        d_int = 52.5
        Material="Acero"
        Unidades="in"
    elif diametro == 2.501:
        d_int = 62.07
        Material="Acero"
        Unidades="in"
    elif diametro == 3.001:
        d_int = 77.92
        Material="Acero"
        Unidades="in"
    elif diametro ==  4.001:
        d_int = 102.26
        Material="Acero"
        Unidades="in"
    elif diametro == 6.001:
        d_int = 154.05
        Material="Acero"
        Unidades="in"
    elif diametro == 8.001:
        d_int = 202.71
        Material="Acero"
        Unidades="in"
    elif diametro == 10.001:
        d_int = 254.5
        Material="Acero"
        Unidades="in"
    elif diametro == 12.001:
        d_int = 303.22
        Material="Acero"
        Unidades="in"
    elif diametro == 14.001:
        Material="Acero"
        Unidades="in"
    elif diametro == 16.001:
        Material="Acero"
        Unidades="in"
    elif diametro == 18.001:
        Material="Acero"
        Unidades="in"
    elif diametro == 20.001:
        Material="Acero"
        Unidades="in"

#acero milimetros
    elif diametro == 20:
        Material="Acero"
        Unidades="mm"
    elif diametro == 25:
        Material="Acero"
        Unidades="mm"
    elif diametro == 30:
        Material="Acero"
        Unidades="mm"
    elif diametro == 38:
        Material="Acero"
        Unidades="mm"
    elif diametro == 44.5:
        Material="Acero"
        Unidades="mm"
    elif diametro == 51:
        Material="Acero"
        Unidades="mm"
    elif diametro == 54:
        Material="Acero"
        Unidades="mm"
    elif diametro == 57:
        Material="Acero"
        Unidades="mm"
    elif diametro == 63.5:
        Material="Acero"
        Unidades="mm"
    elif diametro == 70:
        Material="Acero"
        Unidades="mm"
    elif diametro == 82.5:
        Material="Acero"
        Unidades="mm"
    elif diametro == 108:
        Material="Acero"
        Unidades="mm"
    elif diametro == 127:
        Material="Acero"
        Unidades="mm"
    elif diametro == 133:
        Material="Acero"
        Unidades="mm"
    elif diametro == 152:
        Material="Acero"
        Unidades="mm"
    elif diametro == 159:
        Material="Acero"
        Unidades="mm"
    elif diametro == 177.8:
        Material="Acero"
        Unidades="mm"
    elif diametro == 244.5:
        Material="Acero"
        Unidades="mm"
    elif diametro == 298.5:
        Material="Acero"
        Unidades="mm"
    return Unidades

def diametro_equi(diametro, escape):
    equi = 0
    if escape == "min":
        if diametro == 0.75:
            equi = 0.225
        elif diametro == 1 or diametro == 26:
            equi = 0.3
        elif diametro == 1.25 or diametro == 33:
            equi = 0.375
        elif diametro == 1.5 or diametro == 42:
            equi = 0.45
        elif diametro == 2 or diametro == 48:
            equi = 0.6
        elif diametro == 2.25 or diametro == 60:
            equi = 0.675
        elif diametro == 3 or diametro == 73:
            equi = 0.9
        elif diametro == 88: #3.5
            equi = 1.05
        elif diametro == 4:
            equi = 1.2
        elif diametro == 114: #4.5
            equi = 1.35
        elif diametro == 6:
            equi = 1.8
        elif diametro == 168: #6.5
            equi = 1.95
    elif escape == "parcial":
        if diametro == 0.75:
            equi = 0.525
        elif diametro == 1 or diametro == 26:
            equi = 0.7
        elif diametro == 1.25 or diametro == 33:
            equi = 0.875
        elif diametro == 1.5 or diametro == 42:
            equi = 1.05
        elif diametro == 2 or diametro == 48:
            equi = 1.4
        elif diametro == 2.25 or diametro == 60:
            equi = 1.575
        elif diametro == 3 or diametro == 73:
            equi = 2.1
        elif diametro == 88: #3.5
            equi = 2.45
        elif diametro == 4:
            equi = 2.8
        elif diametro == 114: #4.5
            equi = 3.15
        elif diametro == 6:
            equi = 4.2
        elif diametro == 168: #6.5
            equi = 4.55
    else:
        if diametro < 26:
            equi = diametro
        else:
            if diametro == 26:
                equi = 1
            elif diametro == 33:
                equi = 1.25
            elif diametro == 42:
                equi = 1.5
            elif diametro == 48:
                equi = 2
            elif  diametro == 60:
                equi = 2.25
            elif diametro == 73:
                equi = 3
            elif diametro == 88: #3.5
                equi = 3.5
            elif diametro == 114: #4.5
                equi = 4.5
            elif diametro == 168: #6.5
                equi = 6.5

    return equi

def presion_atmos(altura):
    valor = 0
    #Presion nivel del mar 14.7 psi
    P_0 = 14.7
    #Temperatura nivel del mar 15 K
    T_0 = 288.15
    #Taza de lapso de temperatura (idk) K/m
    L = 0.00976
    #Cosntante presion calor J/(kg*K)
    C = 1004.68506
    #Gravedad m/s^2
    G = 9.80665
    #Masa molar aire kg/mol
    M = 0.02896968
    #Constante de gas universal J/(mol*K)
    R_0 = 8.314462618

    valor= P_0 * np.float_power(np.e,-G*altura/(R_0/M*T_0))*0.0689476

    return valor

def elevacion(latitud, longitud):
    valor = 0
    api = "https://api.open-elevation.com/api/v1/lookup?locations=" + str(latitud) + "," + str(longitud)
    try:
        #Respuesta es un json que se decodifica como dict
        respuesta = requests.get(api).json()
        #Dentro del dict hay una llave results con array de un elemento con otro dict adentro
        valor = respuesta.get('results')[0].get('elevation')
    except:
        valor = 0
    return valor

def convertir(origen, objetivo, valor):
    conv = valor
    #Distancia
    if origen == "mm":
        if objetivo == "m":
            conv = valor/1000
        elif objetivo == "in":
            conv = valor/25.4
        elif objetivo == "ft":
            conv = valor/304.8
        elif objetivo == "mm":
            conv = valor
    elif origen == "ft":
        if objetivo == "m":
            conv = valor/3.281
        elif objetivo == "in":
            conv = valor/12
        elif objetivo == "mm":
            conv = valor*304.8
        elif objetivo == "ft":
            conv = valor
    elif origen == "in":
        if objetivo == "mm":
            conv = valor*25.4
        elif objetivo == "m":
            conv = valor/39.37
        elif objetivo == "ft":
            conv = valor*12
        elif objetivo == "in":
            conv = valor
    elif origen == "m":
        if objetivo == "mm":
            conv = valor*1000
        elif objetivo == "in":
            conv = valor*39.37
        elif objetivo == "ft":
            conv = valor*3.281
        elif objetivo == "m":
            conv = valor
    #Presion
    elif origen == "psig":
        if objetivo == "bar":
            conv = valor/14.504
        elif objetivo == "pascal":
            conv = valor/6894.76
        elif objetivo == "psig":
            conv = valor
    elif origen == "bar":
        if objetivo == "psig":
            conv = valor*14.504
        elif objetivo == "pascal":
            conv = valor*100000
        elif objetivo == "bar":
            conv = valor
    elif origen == "pascal":
        if objetivo == "psig":
            conv = valor*6894.76
        elif objetivo == "bar":
            conv = valor/100000
        elif objetivo == "pascal":
            conv = valor
    #Temperatura
    if origen == "c":
        if objetivo == "f":
            conv = (valor*9/5) + 32
    return conv