import configparser
import socket
import requests
import re

def leer_archivo_ini(ruta="H2O.ini"):
    config = configparser.ConfigParser()
    config.read(ruta)
    return {
        "datasource": config.get("ENTRADA", "DATASOURCE").split('/')[0],
        "bd_web": config.get("ENTRADA", "BD_WEB"),
        "ip_server": config.get("DESCARGAS", "IP_SERVER")
    }

def obtener_ip_privada():
    hostname = socket.gethostname()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def comparar_ips(ip_ini, ip_privada):
    return ip_ini == ip_privada

def actualizar_datasource_api(bd_cliente, nuevo_datasource):
    url = "http://serviceairtech.com.ar/service1.asmx/setConfiguracionIni_datasource"
    data = {
        "BDCliente": bd_cliente,
        "DataSource": nuevo_datasource
    }
    try:
        response = requests.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"[DEBUG] Respuesta del POST: {response.text}")  # Depuración
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def obtener_configuracion_actual(bd_cliente):
    url = f"http://serviceairtech.com.ar/service1.asmx/getConfiguracionIni?BDCliente={bd_cliente}"
    try:
        response = requests.get(url)
        print(f"[DEBUG] Respuesta del GET: {response.text}")  # Depuración
        return extraer_datasource(response.text)
    except Exception as e:
        return f"Error: {str(e)}"

def extraer_datasource(texto):
    # Extraer el valor de DATASOURCE usando una expresión regular
    match = re.search(r'DATASOURCE=([^;]+)', texto)
    if match:
        return match.group(1)
    return "No se pudo extraer DATASOURCE"

def actualizar_config(datos_ini, ip_privada):
    if not comparar_ips(datos_ini['datasource'], ip_privada):
        try:
            config_previa = obtener_configuracion_actual(datos_ini['bd_web'])
            print(f"[DEBUG] IP en la API antes de actualizar: {config_previa}")
            
            respuesta = actualizar_datasource_api(datos_ini['bd_web'], ip_privada)
            nueva_config = obtener_configuracion_actual(datos_ini['bd_web'])
            print(f"[DEBUG] IP en la API después de actualizar: {nueva_config}")
            
            return {
                "estado": "Actualizado",
                "respuesta_api": respuesta,
                "config_anterior": config_previa,
                "config_nueva": nueva_config
            }
        except Exception as e:
            return {"estado": "Error", "mensaje": str(e)}
    return {"estado": "Sin cambios", "mensaje": "Las IPs ya coinciden"}
