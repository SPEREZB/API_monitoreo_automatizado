import datetime
import io
import os
import sqlite3
from PIL import Image, UnidentifiedImageError
from app.services.reconstruction_service import ReconstructionService

class InconsistencyService:
    def __init__(self, directory_path='C:\\Users\\user\\Desktop\\U', db_path='alerts_errors.db'):
        """
        Inicializa el servicio con la ruta del directorio y la ruta de la base de datos.
        """
        self.directory_path = directory_path
        self.db_path = db_path
        self.reconstructionService= ReconstructionService()
        self.crear_tabla()  

    def crear_tabla(self):
        """
        Crea la tabla Parity si no existe.
        """ 
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Parity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    parity TEXT NOT NULL
                )
            ''')
            conn.commit()
            print("Tabla 'Parity' creada o ya existe.") 

    def analyze_inconsistencies(self):
        inconsistencias = []
        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)

            if os.path.isdir(file_path):
                estado = "Carpeta"
                detalles = "El elemento es una carpeta, no un archivo."
            elif not os.path.isfile(file_path):
                estado = "No es un archivo válido."
                detalles = "El elemento no es un archivo estándar."
            elif os.path.getsize(file_path) == 0:
                estado = "El archivo está vacío."
                detalles = "El archivo no contiene datos."
            else:
                estado, detalles = self.verificar_paridad(file_path)
                if estado is True:
                    estado = "Archivo válido"

            inconsistencias.append({
                "id": len(inconsistencias) + 1,
                "nombre": filename,
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "estado": estado,
                "detalles": detalles
            })

        return inconsistencias


    def verificar_paridad(self, file_path):
        """
        Verifica la integridad del archivo utilizando un algoritmo de paridad.
        Retorna una tupla (estado, detalle). El estado puede ser True para válido,
        o "Inconsistente" con una descripción del problema en caso contrario.
        """
        try:
            with open(file_path, 'rb') as file:
                data = file.read()
                paridad_calculada = self.calcular_paridad(data)

                # Obtener la paridad esperada de la base de datos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT parity FROM Parity WHERE filename = ?', (os.path.basename(file_path),))
                    result = cursor.fetchone()

                    if result is None:
                        # No hay paridad registrada: registrar y considerar válido
                        self.add_file(file_path)
                        return True, "Paridad registrada automáticamente, archivo considerado válido."

                    paridad_esperada = result[0]
                    if paridad_calculada != paridad_esperada:
                        # Paridad no coincide
                        return "Inconsistente", f"La paridad calculada ({paridad_calculada}) no coincide con la esperada ({paridad_esperada})."

                # Si todo está bien
                return True, "La paridad fue la esperada"
        except Exception as e:
            return "Inconsistente", f"Error al procesar el archivo: {e}"


    def calcular_paridad(self, data):
        """
        Calcula la paridad de los datos (par o impar).
        Retorna 'par' o 'impar'.
        """
        num_bits = sum(bin(byte).count('1') for byte in data)   
        return 'par' if num_bits % 2 == 0 else 'impar'
    

    def add_file(self, file_path):
        """
        Agrega o actualiza un archivo en el registro de paridad.
        """
        if os.path.isfile(file_path):
            paridad = self.calcular_paridad(open(file_path, 'rb').read())
            nuevo_registro = (os.path.basename(file_path), paridad)
 
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO Parity (filename, parity) VALUES (?, ?)', nuevo_registro)
                conn.commit()
                print(f"Paridad registrada para {file_path}: {paridad}")

    def get_parity_for_name(self, path):
        """
        Consulta la base de datos para obtener la paridad de todos los archivos en la ruta especificada.
        Retorna una lista de diccionarios con los datos formateados para cada archivo.
        """
        try:
            # Obtener todos los archivos en la ruta proporcionada
            archivos = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
             
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                 
                datos_formateados = []

                for archivo in archivos: 
                    cursor.execute('SELECT filename, parity FROM Parity WHERE filename = ?', (archivo,))
                    result = cursor.fetchone()
                    
                    if result is None:
                        # Si no se encuentra el archivo en la base de datos, agregamos un registro con un mensaje de error
                        datos_formateados.append({
                            "id": len(datos_formateados) + 1, 
                            "nombre": archivo,
                            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "estado": "No encontrado",
                            "detalles": "Archivo no encontrado en la base de datos."
                        })
                    else:
                        # Si se encuentra el archivo, agregamos los datos formateados
                        datos_formateados.append({
                            "id": len(datos_formateados) + 1,  
                            "nombre": result[0],
                            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "estado": "Archivo válido" if result[1] == "par" else "Inconsistente",
                            "detalles": result[1]
                        })
 
            return datos_formateados
        except Exception as e:
            return None, f"Error al consultar la base de datos: {e}"









    def update_parity(self, file_path):
        """
        Actualiza la paridad del archivo en la base de datos después de una reparación.
        """
        with open(file_path, 'rb') as file:
            data = file.read()
            nueva_paridad = self.calcular_paridad(data)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE Parity SET parity = ? WHERE filename = ?', (nueva_paridad, os.path.basename(file_path)))
            conn.commit()

    def resolve_inconsistencies(self):
        """
        Intenta resolver las inconsistencias en cada archivo en la ruta especificada.
        """
        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)
            
            if not os.path.isfile(file_path):
                print(f"{filename}: No es un archivo válido (Pueden ser carpetas).")
                continue
            
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension in ['.txt', '.log', '.csv', '.backup', '.dat']:
                # Reparación para archivos de texto
                self.repair_text_file(file_path)
                self.update_parity(file_path)
            elif file_extension in ['.jpg', '.jpeg', '.png']:
                # Reparación para archivos de imagen
                self.repair_image_file(file_path)
                self.update_parity(file_path)
            else:
                print(f"{filename}: Tipo de archivo no soportado para reparación.")


    def repair_text_file(self, file_path):
        """
        Intenta reparar un archivo de texto.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.readlines()

            # Eliminar líneas vacías y caracteres no imprimibles
            repaired_content = [line for line in content if line.strip()]

            # Guardar archivo reparado
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(repaired_content)

            print(f"{file_path}: Reparación de archivo de texto completada.")
        
        except Exception as e:
            print(f"{file_path}: Error al intentar reparar el archivo de texto. {e}")

    def repair_image_file(self, file_path):
        """
        Intenta reparar un archivo de imagen.
        """
        try:
            # Intentar abrir la imagen
            with Image.open(file_path) as img:
                img.verify()  # Verificar si la imagen es legible
 
            with Image.open(file_path) as img:
                img.save(file_path)  # Guardar imagen en el mismo path para reemplazar el archivo original
            
            print(f"{file_path}: Reparación de imagen completada y reemplazada en la misma ruta.")

        except UnidentifiedImageError:
            print(f"{file_path}: Error - no se puede identificar el archivo como una imagen válida.")
             
            try:
                with open(file_path, 'rb') as f: 
                    img_data = f.read()
                    repaired_image = Image.open(io.BytesIO(img_data))  # Cargar la imagen desde los bytes
                    repaired_image.save(file_path, format='PNG')  # Guardar como PNG para intentar repararla
                    print(f"{file_path}: Imagen reparada y guardada como PNG.")
            except Exception as e:
                print(f"{file_path}: No se pudo reparar la imagen. Error: {e}")
        
        except Exception as e:
            print(f"{file_path}: Error al intentar reparar la imagen. {e}")

    def get_inconsistencias(self):
        """
        Obtiene todas las inconsistencias registradas en la base de datos.
        Retorna un diccionario con el nombre del archivo como clave y el estado de paridad como valor.
        """
        inconsistencias = {}
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT filename, parity FROM Parity')
            rows = cursor.fetchall()
            
            for filename, parity in rows: 
                inconsistencias[filename] = parity
        
        return inconsistencias
