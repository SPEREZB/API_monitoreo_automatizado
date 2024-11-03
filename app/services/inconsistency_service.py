import os
import sqlite3

class InconsistencyService:
    def __init__(self, directory_path='C:\\Users\\user\\Desktop\\U', db_path='alerts_errors.db'):
        """
        Inicializa el servicio con la ruta del directorio y la ruta de la base de datos.
        """
        self.directory_path = directory_path
        self.db_path = db_path
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
             
            if not os.path.isfile(file_path):
                inconsistencias[filename] = "No es un archivo válido."
                continue
            
            if os.path.getsize(file_path) == 0:
                inconsistencias[filename] = "El archivo está vacío."
            else:
                # Verificar paridad del archivo
                if not self.verificar_paridad(file_path):
                    inconsistencias[filename] = "El archivo está dañado o tiene errores de paridad."
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

    def resolve_inconsistencies(self):
        """
        Intenta resolver las inconsistencias en cada archivo en la ruta especificada.
        """
        for filename in os.listdir(self.directory_path):
            file_path = os.path.join(self.directory_path, filename)
            
            if not os.path.isfile(file_path):
                print(f"{filename}: No es un archivo válido.")
                continue
            
            if os.path.getsize(file_path) == 0:
                # Renombrar archivos vacíos 
                new_file_path = os.path.join(self.directory_path, f"EMPTY_{filename}")
                os.rename(file_path, new_file_path)
                print(f"Renombrado: {filename} a {new_file_path}")

            elif not self.verificar_paridad(file_path):
                # Manejo de archivos dañados 
                damaged_dir = os.path.join(self.directory_path, "damaged_files")
                os.makedirs(damaged_dir, exist_ok=True)
                os.rename(file_path, os.path.join(damaged_dir, filename))
                print(f"Movido: {filename} a {damaged_dir}")

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
