import os
import random
import sqlite3
import subprocess 
import psutil 
from time import sleep
import re
from app.socketio import socketio  

 
class AlertService: 
    definiciones_smart = {
    "Raw_Read_Error_Rate": "Tasa de errores de lectura en bruto, indica cuántos errores de lectura se han producido.",
    "Power_On_Hours": "Horas totales que el disco ha estado encendido.",
    "Power_Cycle_Count": "Número de veces que el disco ha sido encendido y apagado.",
    "Unknown_Attribute": "Atributo desconocido, no se puede determinar su función específica.",
    "Write_Protect_Mode": "Indica si el disco está protegido contra escritura.",
    "SATA_Phy_Error_Count": "Número de errores en la interfaz SATA.",
    "Bad_Block_Rate": "Tasa de bloques defectuosos en el disco.",
    "Bad_Blk_Ct_Lat/Erl": "Conteo de bloques defectuosos latentes o erróneos.",
    "Erase_Fail_Count": "Número de fallos durante el proceso de borrado.",
    "MaxAvgErase_Ct": "Conteo máximo promedio de borrados.",
    "Program_Fail_Count": "Número de fallos durante el proceso de programación.",
    "Reported_Uncorrect": "Número de errores reportados que no se pudieron corregir.",
    "Unsafe_Shutdown_Count": "Número de apagados no seguros que han ocurrido.",
    "Temperature_Celsius": "Temperatura actual del disco en grados Celsius.",
    "Reallocated_Event_Count": "Número de eventos en los que se han reasignado bloques defectuosos.",
    "SATA_CRC_Error_Count": "Conteo de errores CRC en la interfaz SATA.",
    "CRC_Error_Count": "Conteo de errores CRC generales.",
    "SSD_Life_Left": "Porcentaje de vida restante del SSD.",
    "Flash_Writes_GiB": "Total de escrituras en el flash del SSD en GiB.",
    "Lifetime_Writes_GiB": "Total de escrituras de vida del disco en GiB.",
    "Lifetime_Reads_GiB": "Total de lecturas de vida del disco en GiB.",
    "Average_Erase_Count": "Conteo promedio de borrados.",
    "Max_Erase_Count": "Conteo máximo de borrados.",
    "Total_Erase_Count": "Conteo total de borrados realizados."
    }

    definiciones_smart_usb = [
        "Vendor: Generic - Esto indica el fabricante del dispositivo. En este caso, 'Generic' significa que es un dispositivo de marca genérica o no reconocida.",
        "Product: Flash Disk - Se refiere al tipo de producto, que es una unidad de almacenamiento portátil USB.",
        "Revision: 8.07 - Muestra la versión o revisión del firmware del dispositivo.",
        "Compliance: SPC-2 - Indica que el dispositivo cumple con la especificación SPC-2 (SCSI Primary Commands), lo que define cómo el dispositivo se comunica con el sistema.",
        "User Capacity: 8,053,063,680 bytes [8.05 GB] - Indica la capacidad total de almacenamiento del dispositivo, en este caso 8 GB.",
        "Logical block size: 512 bytes - Define el tamaño de los bloques lógicos en los que se organiza el almacenamiento del dispositivo. Un tamaño típico es 512 bytes.",
        "Device type: disk - Especifica que el dispositivo es de tipo 'disk', lo que significa que es un dispositivo de almacenamiento.",
        "Local Time is: Sun Sep 22 19:38:15 2024 HPS - Muestra la hora local en que se realizó el análisis del dispositivo.",
        "SMART support is: Available - device has SMART capability. - Indica que el dispositivo tiene soporte para SMART (Self-Monitoring, Analysis, and Reporting Technology), una tecnología que monitorea la salud del dispositivo.",
        "SMART support is: Enabled - Esto significa que el soporte SMART está habilitado, lo que permite al dispositivo reportar su estado de salud.",
        "Temperature Warning: Disabled or Not Supported - Indica que no hay advertencias de temperatura o que el dispositivo no admite monitoreo de temperatura."
    ]
    
    name_disk=""

    def monitor_storage(self,alert_model):
        while True: 
                global name_disk
                diskNew= alert_model.get_disk()
                name_disk=diskNew
                if len(diskNew) <= 0:
                    print("error")
                elif(diskNew[0]!="/dev/sdb"): 
                    self.disk(alert_model)
                else:
                    self.usb(alert_model)
                sleep(20)
                
        
    def disk(self,alert_model):
        disk_usage = psutil.disk_usage('/')
        disk_io_counters = psutil.disk_io_counters()

        # Errores de lectura y escritura detectados automáticamente
        read_errs = getattr(disk_io_counters, 'read_errs', 0)
        write_errs = getattr(disk_io_counters, 'write_errs', 0)
        disk_errors = read_errs + write_errs  
 
        disk_usage_alert = f"El uso del disco ha alcanzado {disk_usage.percent}%."
        disk_error_alert = f"Se detectaron {disk_errors} errores en el disco."
 
  
        if disk_errors > 0:
            alert_model.add_alert(disk_error_alert)

            # Guardar los errores detectados automáticamente en la BD
        self.monitor_smart_disk(alert_model, disk_usage, disk_errors, disk_usage_alert)
  

    def monitor_smart_disk(self, alert_model, disk_usage, disk_errors, disk_usage_alert):
        try:
            global name_disk
            smart_data = subprocess.check_output(
                [r'C:\Program Files\Smartmontools\bin\smartctl.exe', '-A', '-d', 'ata', name_disk[0]],
                encoding='UTF-8',
                stderr=subprocess.STDOUT
            )

            alertas = []
            definiciones_alertas = []

            cont = 0
            contErrors = 0
            for line in smart_data.splitlines():
                cont += 1
                if cont > 7 and line.strip(): 
                    parts = line.split()
                    atributo = parts[1]  # Nombre del atributo
                    value = parts[3]
                    worst_value = parts[4]
                    raw_value = parts[-1]
 
                    if atributo in self.definiciones_smart:
                        descripcion_atributo = self.definiciones_smart[atributo]
                    else:
                        descripcion_atributo = "Descripción no disponible."
 
                    if atributo == "Temperature_Celsius": 
                        if len(parts) >= 12 and '(' in parts[10]: 
                            current_temp = parts[9].strip()  
                            # Extraer la parte de min/maxTasa
                            min_max_str = ' '.join(parts[10:]).strip() 
                            min_max_str = min_max_str.replace(')', '') 
                            try:
                                min_temp, max_temp = min_max_str.split()[1].split('/') 
                                detalles_atributo = (f"Valor Actual: {current_temp}°C, Mínimo: {min_temp}°C, Máximo: {max_temp}°C")
                            except ValueError:
                                detalles_atributo = "No se pudo extraer correctamente los valores mínimo y máximo."
                        else:
                            detalles_atributo = "Datos de temperatura no disponibles o formato incorrecto."
                    else:
                        # Para otros atributos estándar
                        detalles_atributo = (f"Valor Actual: {value}, Peor Valor: {worst_value}, Valor Crudo: {raw_value}")


                    # Concatenar la alerta con la descripción del atributo
                    estado = self.verificar_estado_smart_disk(line, f"{atributo}: {descripcion_atributo} - {detalles_atributo}")
                    definiciones_alertas.append(f"{atributo}: {descripcion_atributo} - Estado: {estado} - {detalles_atributo}")

                    # Añadir alerta completa
                    mensaje_alerta = f"{line} - Estado: {estado}"
                    alertas.append(mensaje_alerta)

                    if estado == "Crítico":
                        contErrors += 1
 
                    if disk_usage.percent > 60:
                        alert_model.add_alert(disk_usage_alert)

            total_errors = self.get_total_errors()

            # Calcular la tasa de detección automática de errores
            if total_errors> 0:
                detection_rate = (contErrors / total_errors) * 100
                detection_rate_alert = f"Tasa de detección automática: {detection_rate:.2f}%."
                alert_model.add_alert(detection_rate_alert)
            else:
                alert_model.add_alert("No se detectaron errores totales.")

            sleep(0.5)

            sleep(2)

            @socketio.on('connect')
            def handle_connect():
                print("Cliente conectado")
                alertasDisk = alert_model.get_all_alerts()
                socketio.emit('new_alert', {"alerts": definiciones_alertas, "definitions": definiciones_alertas, "disk": alertasDisk})

        except FileNotFoundError:
            alert_model.add_alert("Error: 'smartctl' no está instalado.")
        except subprocess.CalledProcessError as e:
            alert_model.add_alert(f"Error al ejecutar 'smartctl': {e.output}")
        except Exception as e:
            alert_model.add_alert(f"Error desconocido: {str(e)}")


    def usb(self,alert_model):
        try:   
                # Obtenemos uso del disco USB usando psutil
                disk_partitions = psutil.disk_partitions()
                usb_mount_point = None
                for partition in disk_partitions:
                    if 'D:\\' in partition.device:
                        usb_mount_point = partition.mountpoint
                        break

                if usb_mount_point:
                    disk_usage = psutil.disk_usage(usb_mount_point)
                    disk_usage_percent = disk_usage.percent

                    # Alertas basadas en el uso del disco
                    disk_usage_alert = f"El uso del disco USB ha alcanzado {disk_usage_percent}%."
                    existing_disk_alert = next((alert for alert in alert_model.alerts if "El uso del disco USB ha alcanzado" in alert), None)
                    
                    if disk_usage_percent > 15:
                        alert_model.add_alert(disk_usage_alert)
                    else:
                        if existing_disk_alert:
                            alert_model.remove_alert(existing_disk_alert)

                    self.monitor_smart_usb(alert_model) 

                else:
                    print("USB no encontrado")

                

        except subprocess.CalledProcessError as e: 
            error_message = "Error: El disco USB ha sufrido un error o ha sido retirado." 
            alert_model.add_alert(error_message)


    def monitor_smart_usb(self,alert_model):
        try:
            global name_disk
            smart_data = subprocess.check_output(
                [r'C:\Program Files\Smartmontools\bin\smartctl.exe', '-i', '-d', 'scsi', name_disk[0]],
                encoding='UTF-8',
                stderr=subprocess.STDOUT
            )

            alertas = []
            definiciones_alertas = []

            cont = 0

            # Alertas basadas en la funcion SMART
            for line in smart_data.splitlines():
                cont += 1
                if cont > 4 and line.strip():
                    estado = self.verificar_estado_smart_usb(line)
                    atributo = line.split()[1] 
                    mensaje_alerta = f"{line}"
    
                    if(cont<12):
                        definiciones_alertas.append(f"{atributo}: {self.definiciones_smart_usb[cont-1]} - Estado: {estado}") 
    
                    sleep(0.5)
            sleep(2)
            @socketio.on('connect')
            def handle_connect():
                print("Cliente conectado")
                alertasDisk = alert_model.get_all_alerts()
                socketio.emit('new_alert', {"alerts": definiciones_alertas, "definitions": definiciones_alertas, "disk": alertasDisk})

        except FileNotFoundError:
            alert_model.add_alert("Error: 'smartctl' no está instalado.")
        except subprocess.CalledProcessError as e:
            alert_model.add_alert(f"Error al ejecutar 'smartctl': {e.output}")

            @socketio.on('connect')
            def handle_error():
                socketio.emit('new_alert', {"alerts": None, "definitions": None, "disk": None})
        except Exception as e:
            alert_model.add_alert(f"Error desconocido: {str(e)}")


    def verificar_estado_smart_disk(self,line, detalle): 
        partes = line.split()
        
        valor_actual = int(partes[3])
        valor_umbral = int(partes[4]) 
        if valor_actual >= valor_umbral:
            return "Buen estado"  
        else:
            self.save_alerts_errors(detalle)
            return "Crítico" 


    def verificar_estado_smart_usb(self,line): 
        return "Buen estado" 
    
    def save_alerts_errors(self, line): 
        db_path = os.path.join(os.getcwd(), 'alerts_errors.db')

        if os.path.exists(db_path):
            print("La base de datos ya existe. No es necesario crearla de nuevo.")
        else: 
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errores (
                    id_campo INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL
                )
            ''')

            conn.commit()
            conn.close()
            
            print("Base de datos y tabla 'errores' creadas correctamente.")
         
        first_value = line.split()[0]  # Extraer la primera palabra de 'line'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
         
        cursor.execute("SELECT * FROM errores WHERE nombre LIKE ?", (f'%{first_value}%',))
        result = cursor.fetchone()

        if result: 
            cursor.execute("UPDATE errores SET nombre = ? WHERE id_campo = ?", (line, result[0]))
            print(f"El valor '{first_value}' ya existía. Se ha actualizado con la nueva línea completa.")
        else: 
            cursor.execute("INSERT INTO errores (nombre) VALUES (?)", (line,)) 
            print(f"Valor '{line}' guardado en la tabla 'errores' correctamente.")
        
        conn.commit()
        conn.close()



    def get_alerts_errors(self): 
        db_path = os.path.join(os.getcwd(), 'alerts_errors.db')
 
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
 
        cursor.execute('SELECT nombre FROM errores')
        nombres = cursor.fetchall()  # Esto devuelve una lista de tuplas
 
        conn.close()
 
        return [nombre[0] for nombre in nombres]
 
    def get_total_errors(self): 
        conn = sqlite3.connect('alerts_errors.db')
        cursor = conn.cursor()
 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS errores (
                id_campo INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT 
            );
        ''')  
        cursor.execute('SELECT COUNT(nombre) FROM errores')
        total_errors = cursor.fetchone()[0]
 
        if total_errors is None:
            total_errors = 0

        conn.commit()  
        conn.close()

        return total_errors

    def get_errors_list(self):
        errores_disco = [
        "Raw_Read_Error_Rate: Tasa de errores de lectura en bruto.",
        "Power_On_Hours: Horas totales que el disco ha estado encendido.",
        "Power_Cycle_Count: Número de veces que el disco ha sido encendido y apagado.",
        "Write_Protect_Mode: Indica si el disco está protegido contra escritura.",
        "SATA_Phy_Error_Count: Número de errores en la interfaz SATA.",
        "Bad_Block_Rate: Tasa de bloques defectuosos en el disco.",
        "Reported_Uncorrect: Número de errores reportados que no se pudieron corregir.",
        "Unsafe_Shutdown_Count: Número de apagados no seguros que han ocurrido.",
        "Temperature_Celsius: Temperatura actual del disco.",
        "Reallocated_Event_Count: Número de eventos en los que se han reasignado bloques defectuosos."
        ]
        
        return errores_disco
    
    def check_identified_errors(self): 
        errores_disco = self.get_errors_list()
        errores_bd = self.get_alerts_errors()
 
        resultado = []

        for error in errores_disco: 
            error_clave = error.split(':')[0]

            # Verificar si el error está en la base de datos
            if any(error_clave in bd_error for bd_error in errores_bd):
                resultado.append({'detectado': True})
            else:
                resultado.append({'detectado': False})

        return resultado