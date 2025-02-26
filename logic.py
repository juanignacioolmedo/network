import configparser
import socket
import requests
import re

def leer_archivo_ini(ruta="C:/H2O/EXE/H2O.ini"):
    config = configparser.ConfigParser()
    
    # Leer el archivo manualmente y filtrar líneas incorrectas
    with open(ruta, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    clean_lines = []
    for line in lines:
        if "=" in line or "[" in line:  # Solo mantener líneas válidas
            clean_lines.append(line)
    
    # Parsear solo las líneas limpias
    config.read_string("".join(clean_lines))

    # Obtener el DATASOURCE original y otros valores
    datasource = config.get("ENTRADA", "DATASOURCE", fallback="")
    bd_web = config.get("ENTRADA", "BD_WEB", fallback="")
    ip_server = config.get("DESCARGAS", "IP_SERVER", fallback="")
    logo1 = config.get("General", "Logo1", fallback="").strip('"')
    logo2 = config.get("General", "Logo2", fallback="").strip('"')
    logo3 = config.get("General", "Logo3", fallback="").strip('"')
    logo4 = config.get("General", "Logo4", fallback="").strip('"')

    print(f"[DEBUG] DATASOURCE original (sin modificar): {datasource}")  # Depuración

    return {
        "datasource": datasource,
        "bd_web": bd_web,
        "ip_server": ip_server,
        "logo1": logo1,
        "logo2": logo2,
        "logo3": logo3,
        "logo4": logo4,
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

def es_ip_valida(ip):
    # Expresión regular para validar una dirección IP
    patron_ip = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    return patron_ip.match(ip) is not None

def comparar_datasource_con_ip_o_hostname(datasource, ip_privada, hostname):
    print(f"[DEBUG] Comparando DATASOURCE: {datasource} con IP: {ip_privada} y Hostname: {hostname}")  # Depuración

    if "\\" in datasource or "/" in datasource:  # Si tiene barra
        separador = "\\" if "\\" in datasource else "/"  # Detectar el tipo de barra
        partes = datasource.split(separador, 1)  # Separar en dos partes (antes y después de la barra)
        primera_parte = partes[0]
        print(f"[DEBUG] Primera parte del DATASOURCE: {primera_parte}")  # Depuración
        return primera_parte == ip_privada or primera_parte == hostname
    else:
        # Si no tiene barra, comparar directamente
        return datasource == ip_privada or datasource == hostname

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
    hostname = socket.gethostname()
    print(f"[DEBUG] Comparando DATASOURCE: {datos_ini['datasource']} con IP: {ip_privada} y Hostname: {hostname}")  # Depuración

    if not comparar_datasource_con_ip_o_hostname(datos_ini['datasource'], ip_privada, hostname):
        try:
            config_previa = obtener_configuracion_actual(datos_ini['bd_web'])
            print(f"[DEBUG] Configuración previa en la API: {config_previa}")
            
            # Conservar la parte después de la barra invertida
            if "\\" in datos_ini['datasource'] or "/" in datos_ini['datasource']:
                separador = "\\" if "\\" in datos_ini['datasource'] else "/"
                partes = datos_ini['datasource'].split(separador, 1)
                primera_parte = partes[0]
                resto = partes[1] if len(partes) > 1 else ""
                
                # Verificar si la primera parte es una IP válida
                if es_ip_valida(primera_parte):
                    nuevo_datasource = f"{ip_privada}{separador}{resto}"  # Reemplazar IP y conservar el resto
                else:
                    nuevo_datasource = f"{hostname}{separador}{resto}"  # Reemplazar hostname y conservar el resto
            else:
                # Si no tiene barra, verificar si es una IP válida
                if es_ip_valida(datos_ini['datasource']):
                    nuevo_datasource = ip_privada  # Reemplazar completamente por la IP privada
                else:
                    nuevo_datasource = hostname  # Reemplazar completamente por el hostname

            print(f"[DEBUG] Nuevo DATASOURCE a enviar a la API: {nuevo_datasource}")  # Depuración

            respuesta = actualizar_datasource_api(datos_ini['bd_web'], nuevo_datasource)
            nueva_config = obtener_configuracion_actual(datos_ini['bd_web'])
            print(f"[DEBUG] Configuración nueva en la API: {nueva_config}")
            
            return {
                "estado": "Actualizado",
                "respuesta_api": respuesta,
                "config_anterior": config_previa,
                "config_nueva": nueva_config
            }
        except Exception as e:
            return {"estado": "Error", "mensaje": str(e)}
    return {"estado": "Sin cambios", "mensaje": "Las IPs o hostnames ya coinciden"}