class StorageModel:
    def __init__(self):
        self.capacity = 100  
        self.used_space = 20  
        self.devices = [
            {'id': 1, 'capacity': 50, 'used_space': 40},
            {'id': 2, 'capacity': 50, 'used_space': 10},
        ]

    def adjust_capacity(self, demand):
        """Ajusta la capacidad de almacenamiento según la demanda."""
        if demand > self.capacity:
            self.capacity += demand - self.used_space  # Aumenta la capacidad
        elif demand < self.used_space * 0.5:
            self.capacity -= (self.used_space - demand)  # Reduce la capacidad
        return self.capacity

    def get_total_used_space(self):
        """Obtiene el total de espacio utilizado en todos los dispositivos."""
        return sum([device['used_space'] for device in self.devices])

    def get_storage_status(self):
        """Devuelve el estado actual de los dispositivos de almacenamiento."""
        return {
            'capacity': self.capacity,
            'used_space': self.get_total_used_space(),
            'devices': self.devices
        }
