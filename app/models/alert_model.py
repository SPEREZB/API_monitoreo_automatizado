from app.socketio import socketio


class AlertModel:
    def __init__(self):
        self.alerts = []
        self.disk= []
        self.all_disk= []
        self.disk_removed=[]

    def add_alert(self, message):
        """Añadir una alerta a la lista de alertas."""

        if(len(self.alerts)==0 and 'El uso del disco ha alcanzado' in message):
            self.alerts.append(message)
        else:
            if(len(self.alerts)==1 and 'Tasa de detección automática:' in message):
                self.alerts.append(message) 
        if(len(self.alerts)>2):
            self.alerts.clear() 

    def replace_alert(self, old_alert, new_alert):
        """Reemplazar una alerta existente con una nueva."""
        if old_alert in self.alerts: 
            index = self.alerts.index(old_alert) 
            self.alerts[index] = new_alert

    def remove_alert(self, alert):
        """Eliminar una alerta específica si existe en el modelo."""
        if alert in self.alerts:
            self.alerts.remove(alert)

    def clear_alerts(self):
        """Limpiar la lista de alertas."""
        self.alerts.clear()

    def get_all_alerts(self):
        """Devuelve la lista de alertas."""
        return self.alerts

    def length(self):
        """Devolver la longitud de la lista de alertas."""
        return len(self.alerts)
    
    def get_disk(self):
        """Obtener disco."""
        return self.disk
    
    def get_removed_disk(self):
        """Obtener disco."""
        return self.disk_removed
    
    def remove_disk(self, selected_disk):
        """Quitar disco."""
        self.disk_removed.append(self.all_disk[selected_disk])
        return self.disk
    
    def add_disk(self, devices):
        """Añadir disco."""
        if(len(self.disk)>0):
            self.all_disk.clear()
        self.all_disk=devices
        return self.all_disk
    
    def choose_disk(self, device):
        """Escoger disco."""
        if(len(self.disk)>0):
            self.disk.clear()
        return self.disk.append(device)

    def __str__(self):
        """Devolver una sola cadena de las alertas."""
        return '\n'.join(self.alerts) if self.alerts else "No hay alertas."
