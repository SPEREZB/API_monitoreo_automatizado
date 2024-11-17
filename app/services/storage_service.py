import stat
from app.models.storage_model import StorageModel
import threading
import time
import os
import shutil

class StorageService:
    def __init__(self):
        self.storage = StorageModel()
        self.start_auto_adjust()   
        self.excluded_extensions = ['.exe', '.dll', '.sys', '.ini', '.bat', '.chk']

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



    def liberar_space(self, ruta):
        total_deleted = 0  # Total de espacio liberado en bytes
        max_time = 10  # Tiempo máximo en segundos para cada sección

        # Ruta de caché del sistema
        cache_dirs = [
            os.path.expanduser("~/.cache"),  # Linux
            os.path.expanduser("C:\\Users\\"+ruta+"\\AppData\\Local\\Temp"),  # Windows
            os.path.expanduser("C:\\Users\\"+ruta+"\\AppData\\Roaming\\Microsoft\\Windows\\Recent")  # Archivos recientes en Windows
        ]

        # Limpiar cachés
        for cache_dir in cache_dirs:
            start_time = time.time()  # Tiempo de inicio
            if os.path.exists(cache_dir):
                print(f"Liberando espacio en: {cache_dir}")
                try:
                    for root, dirs, files in os.walk(cache_dir):
                        for file in files:
                            # Verifica si han pasado más de 10 segundos
                            if time.time() - start_time > max_time:
                                print(f"Tiempo límite excedido en {cache_dir}. Saliendo...")
                                break
                            file_path = os.path.join(root, file)
                            try:
                                # Obtener el tamaño del archivo
                                file_size = os.path.getsize(file_path)
                                # Eliminar el archivo
                                os.remove(file_path) 
                                total_deleted += file_size
                                print(f"Archivo eliminado: {file_path}, Tamaño: {file_size} bytes")
                            except (PermissionError, OSError) as e:
                                print(f"No se pudo eliminar el archivo {file_path}: {e}")
                except Exception as e:
                    print(f"Error al acceder a la carpeta {cache_dir}: {e}")

        # Limpiar papelera
        trash_dirs = [
            os.path.expanduser("~/.local/share/Trash/files"),  # Linux
            os.path.expanduser("C:\\$Recycle.Bin")  # Windows (general)
        ]

        for trash_dir in trash_dirs:
            start_time = time.time()  # Tiempo de inicio
            if os.path.exists(trash_dir):
                print(f"Liberando espacio en papelera: {trash_dir}")
                try:
                    for root, dirs, files in os.walk(trash_dir):
                        for file in files:
                            # Verifica si han pasado más de 10 segundos
                            if time.time() - start_time > max_time:
                                print(f"Tiempo límite excedido en {trash_dir}. Saliendo...")
                                break
                            file_path = os.path.join(root, file)
                            try:
                                # Obtener el tamaño del archivo
                                file_size = os.path.getsize(file_path)
                                # Eliminar el archivo
                                os.remove(file_path)
                                total_deleted += file_size
                                print(f"Archivo eliminado de la papelera: {file_path}, Tamaño: {file_size} bytes")
                                break
                            except (PermissionError, OSError) as e:
                                print(f"No se pudo eliminar el archivo {file_path}: {e}")
                        break
                except Exception as e:
                    print(f"Error al acceder a la papelera {trash_dir}: {e}")
            break

        return total_deleted
 
    def balance_disks(self, disks):
        """Balancea los archivos entre discos y dispositivos de almacenamiento.""" 
        
        # Encontrar el disco con mayor y menor porcentaje de uso
        if len(disks) < 2:
            print("Se necesitan al menos dos discos para realizar el balanceo.")
            return disks

        # Continuar hasta que no haya más diferencias significativas entre discos
        while True:
            # Ordenar los discos por porcentaje de uso (mayor a menor)
            disks.sort(key=lambda d: (self.convert_size_to_bytes(d['used']) / self.convert_size_to_bytes(d['size'])) * 100, reverse=True)
            largest_disk = disks[0]
            smallest_disk = disks[-1]

            # Obtener el porcentaje de uso actual del disco más lleno y el más vacío
            largest_percentage = (self.convert_size_to_bytes(largest_disk['used']) / self.convert_size_to_bytes(largest_disk['size'])) * 100
            smallest_percentage = (self.convert_size_to_bytes(smallest_disk['used']) / self.convert_size_to_bytes(smallest_disk['size'])) * 100

            print(f"Disco más lleno: {largest_disk['filesystem']} ({largest_percentage:.2f}% usado)")
            print(f"Disco más vacío: {smallest_disk['filesystem']} ({smallest_percentage:.2f}% usado)")

            # Si la diferencia entre los discos es menor al 1%, consideramos que están balanceados
            if largest_percentage - smallest_percentage < 1:
                print("Los discos están balanceados.")
                break

            # Calcular cuánto espacio mover para reducir la diferencia
            max_percentage = largest_percentage - 1  # Dejar un margen del 1%
            target_used_in_smallest = (max_percentage / 100) * self.convert_size_to_bytes(smallest_disk['size'])
            space_to_move = target_used_in_smallest - self.convert_size_to_bytes(smallest_disk['used'])

            if space_to_move <= 0:
                print("No hay espacio suficiente para continuar el balanceo.")
                break 

            print(f"Moviendo {space_to_move} bytes del disco {largest_disk['filesystem']} al disco {smallest_disk['filesystem']}")

            # Verificar si el disco más grande tiene suficientes archivos para mover
            if space_to_move > largest_disk['available']:
                raise ValueError("No hay suficiente espacio disponible en el disco más lleno para mover.")

            # Mover los archivos del disco más lleno al disco más vacío
            self.move_files(largest_disk['mountpoint'], smallest_disk['mountpoint'], space_to_move)

            # Actualizar los espacios usados de ambos discos
            largest_disk['used'] = f"{self.convert_bytes_to_size(self.convert_size_to_bytes(largest_disk['used']) - space_to_move)}"
            smallest_disk['used'] = f"{self.convert_bytes_to_size(self.convert_size_to_bytes(smallest_disk['used']) + space_to_move)}"

            # Actualizar los porcentajes y mostrar el estado actual
            largest_percentage = (self.convert_size_to_bytes(largest_disk['used']) / self.convert_size_to_bytes(largest_disk['size'])) * 100
            smallest_percentage = (self.convert_size_to_bytes(smallest_disk['used']) / self.convert_size_to_bytes(smallest_disk['size'])) * 100

            print(f"Nuevo porcentaje - Disco más lleno: {largest_percentage:.2f}% | Disco más vacío: {smallest_percentage:.2f}%")
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

    def is_important_file(self, file_path):
        """Verifica si el archivo es importante o sensible."""
        # Comprobar si el archivo es de sistema
        is_hidden = file_path.startswith('.') or bool(os.stat(file_path).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
        is_read_only = bool(os.stat(file_path).st_mode & stat.S_IREAD) and not bool(os.stat(file_path).st_mode & stat.S_IWRITE)

        # Comprobar extensión del archivo
        _, ext = os.path.splitext(file_path)
        if ext.lower() in self.excluded_extensions:
            return True

        return is_hidden or is_read_only

    def move_files(self, source_mountpoint, target_mountpoint, space_to_free):
        """Mueve archivos desde un disco lleno a uno con espacio hasta liberar el espacio necesario."""
        total_moved = 0
        files_moved = []
        files_to_move = []

        storage_envio = os.path.join(source_mountpoint, "Almacenamiento")
        storage_folder = os.path.join(target_mountpoint, "Almacenamiento")
        
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)

        # Recopilar archivos que no sean importantes o sensibles
        for root, dirs, files in os.walk(storage_envio):
            for file in files:
                file_path = os.path.join(root, file)

                if self.is_important_file(file_path):
                    print(f"Archivo {file} ignorado (importante o sensible).")
                    continue
                
                files_to_move.append(file_path)

        print(f"Total de archivos a considerar para mover: {len(files_to_move)}.")

        # Mover archivos hasta liberar el espacio necesario
        for file_path in files_to_move:
            file_size = os.path.getsize(file_path)

            # Si ya se movió suficiente espacio, detener el proceso
            if total_moved >= space_to_free:
                print(f"Espacio suficiente liberado: {self.convert_bytes_to_size(total_moved)} de {self.convert_bytes_to_size(space_to_free)} requerido.")
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
            print(f"Archivo {file_path} movido. Tamaño: {self.convert_bytes_to_size(file_size)}. Total movido: {self.convert_bytes_to_size(total_moved)}.")

        # Verificar si se logró liberar suficiente espacio
        if total_moved < space_to_free:
            print(f"No se pudo liberar todo el espacio requerido. Espacio liberado: {self.convert_bytes_to_size(total_moved)} de {self.convert_bytes_to_size(space_to_free)} requerido.")
        
        return files_moved