from app.models.storage_model import StorageModel
import threading
import time
import os
import shutil

class StorageService:
    def __init__(self):
        self.storage = StorageModel()
        self.start_auto_adjust()   

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

    def balance_disks(self, disks):
        """Balancea los archivos entre discos y dispositivos de almacenamiento."""
        cont = 0
        for disk in disks:
            cont += 1
            used_percentage = (self.convert_size_to_bytes(disk['used']) / self.convert_size_to_bytes(disk['size'])) * 100

            if used_percentage > 9 and cont == 2:
                        # Calcular la mitad del espacio utilizado para mover
                        space_to_free = self.convert_size_to_bytes(disk['used']) // 2

                        # Encontrar otro disco con suficiente espacio disponible
                        target_disk = next(
                            (d for d in disks if d['available'] >= space_to_free and d['filesystem'] != disk['filesystem']),
                            None
                        )

                        if target_disk:
                            # Mover archivos del disco lleno al disco con espacio
                            self.move_files(disk['mountpoint'], target_disk['mountpoint'], space_to_free)

                            # Actualizar espacio utilizado en ambos discos
                            disk['used'] = f"{self.convert_bytes_to_size(self.convert_size_to_bytes(disk['used']) - space_to_free)}"
                            target_disk['used'] = f"{self.convert_bytes_to_size(self.convert_size_to_bytes(target_disk['used']) + space_to_free)}"

                            print(f"Moviendo {space_to_free} bytes de {disk['filesystem']} a {target_disk['filesystem']}")
                        else:
                            raise ValueError('No hay discos con suficiente espacio disponible.')

        return disks

    def convert_size_to_bytes(self, size_str):
        """Convierte un tamaño en formato GB/MB/etc a bytes."""
        size, unit = size_str.split()
        size = float(size)
        unit = unit.upper()

        if 'GB' in unit:
            return int(size * (1024 ** 3))
        elif 'MB' in unit:
            return int(size * (1024 ** 2))
        elif 'KB' in unit:
            return int(size * 1024)
        elif 'B' in unit:
            return int(size)
        else:
            raise ValueError("Unidad de tamaño desconocida")

    def convert_bytes_to_size(self, bytes_value):
        """Convierte bytes a formato legible GB/MB/etc."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024

    def move_files(self, source_mountpoint, target_mountpoint, space_to_free):
        """Mueve archivos de un disco lleno a uno con espacio."""
        total_moved = 0
        files_moved = []

        storage_folder = os.path.join(target_mountpoint, "Almacenamiento")
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)

        for root, dirs, files in os.walk(source_mountpoint):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)

                # Excluir archivos .CHK
                if file.lower().endswith('.chk'):
                    print(f"Archivo {file} ignorado.")
                    continue

                # Si ya se movió suficiente espacio, detener el proceso
                if total_moved >= space_to_free:
                    return files_moved

                # Crear la ruta de destino en la carpeta Almacenamiento
                target_path = os.path.join(storage_folder, os.path.basename(file_path))

                # Crear directorio si no existe
                target_dir = os.path.dirname(target_path)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Mover el archivo
                shutil.move(file_path, target_path)
                files_moved.append(file_path)

                total_moved += file_size

        return files_moved