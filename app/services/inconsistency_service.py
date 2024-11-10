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
        """
        Analiza cada archivo en la ruta especificada para encontrar inconsistencias.
        Retorna un diccionario con el reporte de inconsistencias.
        """
        inconsistencias = {}
        
        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)

            if os.path.isdir(file_path):
                inconsistencias[filename] = "Es una carpeta"
                continue
             
            if not os.path.isfile(file_path):
                inconsistencias[filename] = "No es un archivo válido."
                continue
            
            if os.path.getsize(file_path) == 0:
                inconsistencias[filename] = "El archivo está vacío."
            else:
                # Verificar paridad del archivo
                if not self.verificar_paridad(file_path):
                    inconsistencias[filename] = "Inconsistente"
                else:
                    inconsistencias[filename] = "Archivo válido."

        return inconsistencias

    def verificar_paridad(self, file_path):
        """
        Verifica la integridad del archivo utilizando un algoritmo de paridad.
        Retorna True si el archivo es válido, False en caso contrario.
        """
        try:
            with open(file_path, 'rb') as file: 
                data = file.read() 
                paridad = self.calcular_paridad(data)

                # Obtener la paridad esperada de la base de datos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT parity FROM Parity WHERE filename = ?', (os.path.basename(file_path),))
                    result = cursor.fetchone()

                    # Si no hay paridad esperada, agregar un nuevo registro de paridad
                    if result is None:
                        self.add_file(file_path)
                        return True   

                    return paridad == result[0]
        except Exception as e:
            print(f"Error al verificar el archivo {file_path}: {e}")
            return False

    def calcular_paridad(self, data):
        """
        Calcula la paridad de los datos (par o impar).
        Retorna 'par' o 'impar'.
        """
        num_bits = sum(bin(byte).count('1') for byte in data)   
        return 'par' if num_bits % 2 == 0 else 'impar'
    
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
