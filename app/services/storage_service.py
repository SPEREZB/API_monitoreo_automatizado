from app.models.storage_model import StorageModel
import threading
import time

class StorageService:
    def __init__(self):
        self.storage = StorageModel()
        self.start_auto_adjust()  # Inicia el ajuste automático en un hilo

    def get_storage_info(self): 
        return {
            'capacity': self.storage.capacity,
            'used_space': self.storage.get_total_used_space(),
            'available_space': self.storage.capacity - self.storage.get_total_used_space(),
            'devices': self.storage.devices
        }

    def adjust_storage(self, demand): 
        new_capacity = self.storage.adjust_capacity(demand)
        return {
            'capacity': new_capacity,
            'used_space': self.storage.get_total_used_space(),
            'available_space': new_capacity - self.storage.get_total_used_space()
        }

    def auto_adjust_storage(self): 
        while True:
            if self.storage.get_total_used_space() >= self.storage.capacity * 0.8:
                print("Capacidad ajustada automáticamente (escalado hacia arriba).")
                self.storage.capacity += 20
            elif self.storage.get_total_used_space() <= self.storage.capacity * 0.3:
                print("Capacidad ajustada automáticamente (escalado hacia abajo).")
                self.storage.capacity -= 10
            time.sleep(5) 

    def start_auto_adjust(self): 
        adjust_thread = threading.Thread(target=self.auto_adjust_storage)
        adjust_thread.daemon = True
        adjust_thread.start()

    def balance_storage(self, demand):
        """
        Balancea el almacenamiento entre los dispositivos y ajusta según la demanda.
        """
        if demand + self.storage.get_total_used_space() > self.storage.capacity:
            raise ValueError('No hay suficiente capacidad total para la demanda.')

        # Redistribuir datos si es necesario
        self.redistribute_load()

        # Agregar nuevos datos según la demanda
        self.add_data(demand)
 
        return self.storage.get_storage_status()

    def redistribute_load(self):
        """Redistribuye la carga entre los dispositivos de almacenamiento."""
        for device in self.storage.devices: 
            if device['used_space'] / device['capacity'] > 0.9:
                self.move_data_from_device(device)

    def move_data_from_device(self, device):
        """Mueve datos desde un dispositivo lleno a otro con más espacio."""
        data_to_move = device['used_space'] - int(0.9 * device['capacity'])

        for target_device in self.storage.devices:
            if target_device != device and target_device['used_space'] < target_device['capacity']:
                available_space = target_device['capacity'] - target_device['used_space']
                
                move_amount = min(data_to_move, available_space)
                device['used_space'] -= move_amount
                target_device['used_space'] += move_amount
                data_to_move -= move_amount
                
                if data_to_move <= 0:
                    break

    def add_data(self, demand):
        """Añadir datos según la demanda al dispositivo con más espacio disponible."""
        for device in sorted(self.storage.devices, key=lambda d: d['capacity'] - d['used_space'], reverse=True):
            available_space = device['capacity'] - device['used_space']
            
            if demand <= available_space:
                device['used_space'] += demand
                break
