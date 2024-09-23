import subprocess 
import psutil 
from time import sleep
import re
from app.socketio import socketio 
 
 

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

def monitor_storage(alert_model):
    while True: 
            global name_disk
            diskNew= alert_model.get_disk()
            name_disk=diskNew
            if len(diskNew) <= 0:
                print("error")
            elif(diskNew[0]!="/dev/sdb"): 
                disk(alert_model)
            else:
                usb(alert_model)
        
def disk(alert_model):
        disk_usage = psutil.disk_usage('/')
        disk_io_counters = psutil.disk_io_counters()
        read_errs = getattr(disk_io_counters, 'read_errs', 0)
        write_errs = getattr(disk_io_counters, 'write_errs', 0)
        disk_errors = read_errs + write_errs

        disk_usage_alert = f"El uso del disco ha alcanzado {disk_usage.percent}%."
        disk_error_alert = f"Se detectaron {disk_errors} errores en el disco."

        existing_disk_alert = next((alert for alert in alert_model.alerts if "El uso del disco ha alcanzado" in alert), None)
        if disk_usage.percent > 60:
            alert_model.add_alert(disk_usage_alert)
 
        if disk_errors > 0:
            alert_model.add_alert(disk_error_alert)

        monitor_smart_disk(alert_model) 


def monitor_smart_disk(alert_model):
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
        for line in smart_data.splitlines():
            cont += 1
            if cont > 7 and line.strip():
                estado = verificar_estado_smart_disk(line)
                atributo = line.split()[1]
                mensaje_alerta = f"{line} - Estado: {estado}"

             
                definiciones_alertas.append(f"{atributo}: {definiciones_smart[atributo]} - Estado: {estado}")

                alertas.append(mensaje_alerta)
                sleep(1)

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


def usb(alert_model):
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

                monitor_smart_usb(alert_model) 

            else:
                print("USB no encontrado")

    except subprocess.CalledProcessError as e: 
        error_message = "Error: El disco USB ha sufrido un error o ha sido retirado." 
        alert_model.add_alert(error_message)

        


def monitor_smart_usb(alert_model):
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
                estado = verificar_estado_smart_usb(line)
                atributo = line.split()[1] 
                mensaje_alerta = f"{line}"
 
                if(cont<12):
                    definiciones_alertas.append(f"{atributo}: {definiciones_smart_usb[cont-1]} - Estado: {estado}") 
 
                sleep(1)

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

  
 

def verificar_estado_smart_disk(line): 
    partes = line.split()
    
    valor_actual = int(partes[3])
    valor_umbral = int(partes[4])
 
    if valor_actual >= valor_umbral:
        return "Buen estado"  
    else:
        return "Crítico" 
    


def verificar_estado_smart_usb(line): 
    return "Buen estado" 