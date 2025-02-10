import tkinter as tk
from tkinter import ttk, messagebox
import socket
from logic import leer_archivo_ini, obtener_ip_privada, comparar_ips, actualizar_datasource_api, obtener_configuracion_actual

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Scanner")
        self.geometry("600x400")
        
        # Variables de estado
        self.ip_privada = obtener_ip_privada()
        self.hostname = socket.gethostname()
        
        try:
            self.datos_ini = leer_archivo_ini()
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando INI: {str(e)}")
            self.destroy()
            return
        
        self.crear_widgets()
        self.mostrar_comparacion_ips()  # Primera comparación (con el INI)
        
    def crear_widgets(self):
        # Frame principal
        frame = ttk.Frame(self)
        frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Sección de información
        ttk.Label(frame, text="INFORMACIÓN LOCAL", font=('Arial', 12, 'bold')).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(frame, text=f"IP Actual: {self.ip_privada}").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, text=f"Hostname: {self.hostname}").grid(row=2, column=0, sticky="w")
        
        # Sección de configuración
        ttk.Label(frame, text="CONFIGURACIÓN INI", font=('Arial', 12, 'bold')).grid(row=3, column=0, sticky="w", pady=5)
        ttk.Label(frame, text=f"Datasource: {self.datos_ini['datasource']}").grid(row=4, column=0, sticky="w")
        ttk.Label(frame, text=f"BD Web: {self.datos_ini['bd_web']}").grid(row=5, column=0, sticky="w")
        
        # Botones
        ttk.Button(frame, text="Actualizar Configuración", command=self.actualizar_config).grid(row=6, column=0, pady=10)
        
        # Área de estado
        self.status_text = tk.Text(frame, height=8, width=50, state="normal")
        self.status_text.grid(row=7, column=0, pady=10)
        self.status_text.insert(tk.END, "Esperando acciones...\n")
        self.status_text.config(state="disabled")
        
    def mostrar_comparacion_ips(self, datasource_api=None):
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        
        # Comparar con la IP de la API si está disponible, de lo contrario usar el INI
        ip_a_comparar = datasource_api if datasource_api else self.datos_ini['datasource']
        resultado = "COINCIDEN" if comparar_ips(ip_a_comparar, self.ip_privada) else "NO COINCIDEN"
        color = "green" if resultado == "COINCIDEN" else "red"
        
        self.status_text.insert(tk.END, "Estado de IPs: ")
        self.status_text.insert(tk.END, resultado, color)
        self.status_text.insert(tk.END, "\n\n")
        self.status_text.config(state="disabled")
        
    def actualizar_config(self):
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "Enviando datos a la API...\n")
        self.status_text.config(state="disabled")
        self.update_idletasks()  # Forzar actualización de la interfaz
        
        # Primera comparación (con el INI)
        if not comparar_ips(self.datos_ini['datasource'], self.ip_privada):
            try:
                # Obtener configuración actual desde la API (antes de actualizar)
                print("[DEBUG] Obteniendo estado previo de la API...")
                config_previa = obtener_configuracion_actual(self.datos_ini['bd_web'])
                print(f"[DEBUG] IP en la API (antes de actualizar): {config_previa}")
                
                # Actualizar configuración
                print(f"[DEBUG] Enviando nueva IP a la API: {self.ip_privada}")
                respuesta = actualizar_datasource_api(self.datos_ini['bd_web'], self.ip_privada)
                self.status_text.config(state="normal")
                self.status_text.insert(tk.END, "Datos enviados correctamente.\n")
                self.status_text.insert(tk.END, f"Respuesta de la API: {respuesta}\n\n")
                self.status_text.config(state="disabled")
                self.update_idletasks()  # Forzar actualización de la interfaz
                
                # Obtener configuración actualizada desde la API
                print("[DEBUG] Obteniendo configuración actualizada desde la API...")
                nueva_config = obtener_configuracion_actual(self.datos_ini['bd_web'])
                print(f"[DEBUG] IP en la API (después de actualizar): {nueva_config}")
                
                self.status_text.config(state="normal")
                self.status_text.insert(tk.END, "Configuración actualizada:\n")
                self.status_text.insert(tk.END, f"{nueva_config}\n")
                self.status_text.config(state="disabled")
                
                # Segunda comparación (con la API)
                print(f"[DEBUG] Comparando IPs: Local={self.ip_privada}, API={nueva_config}")
                self.mostrar_comparacion_ips(datasource_api=nueva_config)
                
            except Exception as e:
                print(f"[DEBUG] Error: {str(e)}")
                self.status_text.config(state="normal")
                self.status_text.insert(tk.END, f"Error: {str(e)}\n")
                self.status_text.config(state="disabled")
        else:
            print("[DEBUG] Las IPs ya coinciden, no se requiere actualización.")
            self.status_text.config(state="normal")
            self.status_text.insert(tk.END, "Las IPs ya coinciden, no se requiere actualización.\n")
            self.status_text.config(state="disabled")

if __name__ == "__main__":
    app = Application()
    app.mainloop()