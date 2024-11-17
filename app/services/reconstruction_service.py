import io
from flask import jsonify
from zfec import filefec
import os

TOTAL_SHARDS = 8  # Total de fragmentos generados por bloque
MIN_SHARDS = 5     # Mínimo de fragmentos necesarios por bloque
BLOCK_SIZE = 4 * 1024 * 1024  # Tamaño de bloque en bytes (4 MB)

# Directorios temporales para almacenar fragmentos
ENCODED_DIR = 'encoded_files/'
DECODED_DIR = 'decoded_files/'
os.makedirs(ENCODED_DIR, exist_ok=True)
os.makedirs(DECODED_DIR, exist_ok=True)

class ReconstructionService: 
    def encode_disk(self, disk_path):
        """Codifica todo el contenido de un disco en bloques y aplica código de borrado."""
        if not os.path.exists(disk_path):
            return jsonify({"error": "Disco no encontrado."}), 404

        ruta_script = os.path.abspath(__file__) 
        services_path = os.path.dirname(ruta_script)
        app_path = os.path.dirname(services_path)
        api_path = os.path.dirname(app_path)
        
        ruta_especifica=  os.path.basename(disk_path)
        nueva_ruta = os.path.join(ENCODED_DIR, ruta_especifica)
        nueva_ruta= api_path+"/"+nueva_ruta


        if not os.path.exists(nueva_ruta):
            os.makedirs(nueva_ruta, exist_ok=True)  

         
        block_index = 0

        try:
            for root, dirs, files in os.walk(disk_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)

                    try:
                        with open(file_path, 'rb') as file:
                            while True:
                                # Lee un bloque de datos del archivo
                                block = file.read(BLOCK_SIZE)
                                if not block:
                                    break  # Sale del bucle al final del archivo

                                # Obtiene la extensión del archivo
                                file_extension = os.path.splitext(file_name)[1]  # Obtiene la extensión

                                # Construye el nombre del bloque con el nombre y extensión original del archivo
                                block_filename = f"block_{block_index}_file_{os.path.splitext(file_name)[0]}{file_extension}"
                                block_path = os.path.join(nueva_ruta, block_filename)

                                # Guarda temporalmente el bloque leído
                                try:
                                    with open(block_path, 'wb') as block_file:
                                        block_file.write(block)
                                except IOError as e:
                                    return jsonify({"error": f"Error al escribir el bloque temporal: {e}"}), 500

                                # Codifica el bloque en fragmentos
                                try: 
                                    fsize = len(block)

                                    with io.BytesIO(block) as block_io:
                                        filefec.encode_to_files(
                                            inf=block_io,       # Pasa el objeto BytesIO
                                            fsize=fsize,        # Tamaño del bloque
                                            dirname=nueva_ruta, # Directorio de salida
                                            prefix=block_filename, # Prefijo del bloque
                                            k=MIN_SHARDS,       # Mínimo de fragmentos
                                            m=TOTAL_SHARDS      # Total de fragmentos
                                        )

                                except Exception as e:
                                    print(f"Error en la codificación de fragmentos: {e}")
                                    continue 
                                finally:
                                    # Elimina el bloque temporal después de la codificación
                                    if os.path.exists(block_path):
                                        os.remove(block_path)

                                block_index += 1

                    except IOError as e:
                        print(f"Error al leer el archivo {file_name}: {e}") 
                        continue

        except Exception as e:
            print(f"Error en la lectura de archivos del disco: {e}")

        return jsonify({"message": "Contenido del disco codificado en fragmentos.", "blocks_encoded": block_index, "ruta": nueva_ruta})
 
    def decode_disk(self, output_directory): 
        ruta_script = os.path.abspath(__file__) 
        services_path = os.path.dirname(ruta_script)
        app_path = os.path.dirname(services_path)
        api_path = os.path.dirname(app_path)



        nueva_ruta = os.path.join(DECODED_DIR, output_directory)
        nueva_ruta= api_path+"/"+nueva_ruta

        ruta_de_fragmentos= os.path.join(ENCODED_DIR, output_directory)
 
        os.makedirs(nueva_ruta, exist_ok=True)

        decoded_files = {}  
        block_index = 0


        # Recorrer cada bloque hasta que no haya más bloques
        while True:
            block_filename = f"block_{block_index}"
            available_shards_paths = [
                os.path.join(ruta_de_fragmentos, f)
                for f in os.listdir(ruta_de_fragmentos)
                if f.startswith(block_filename) and f.endswith('.fec')
            ]

            if not available_shards_paths:
                break

            if len(available_shards_paths) < MIN_SHARDS:
                print(f"No se encontraron suficientes fragmentos para {block_filename}.")
                break

            # Extraer el nombre del archivo original
            original_file_name = self.extract_file_name(available_shards_paths[0])
            reconstructed_file_path = os.path.join(nueva_ruta, original_file_name)

            # Reconstruir el archivo a partir de los fragmentos
            try:
                self.reconstruct_file_from_fragments(available_shards_paths, reconstructed_file_path)
            except Exception as e:
                print(f"Error en la reconstrucción de {original_file_name}: {e}")
                continue

            decoded_files[original_file_name] = reconstructed_file_path  
            print(f"Archivo {original_file_name} reconstruido y guardado en {reconstructed_file_path}.")
            block_index += 1

        return jsonify({"message": "Decodificación completa.", "decoded_files": nueva_ruta})  


    def reconstruct_file_from_fragments(self, fragments, output_file):
        """Reconstruye un archivo a partir de sus fragmentos .FEC usando zfec.""" 
        fragments.sort()

        # Abre cada fragmento en modo lectura binaria y lo almacena en una lista
        opened_fragments = [open(fragment, 'rb') for fragment in fragments]

        try: 
            with open(output_file, 'wb') as outfile:
                filefec.decode_from_files(
                    outf=outfile,
                    infiles=opened_fragments,
                    verbose=False
                )
        finally:
            # Cierra todos los archivos de fragmentos después de la decodificación
            for fragment_file in opened_fragments:
                fragment_file.close()


    def extract_file_name(self, shard_path):
        # Extrae el nombre del archivo original a partir del nombre del fragmento
        base_name = os.path.basename(shard_path)  # Obtiene el nombre del archivo del fragmento
 
        parts = base_name.split('_file_')  # Divide en el nombre del archivo original
        if len(parts) > 1: 
            original_name_with_extension = parts[1].split('.')
            
            # Toma solo el nombre y la extensión original
            original_file_name = ".".join(original_name_with_extension[:-2])  
 
            return original_file_name 
        
        return base_name

    def get_subdirectories(self):
        try: 
            subdirs = [d for d in os.listdir(ENCODED_DIR) if os.path.isdir(os.path.join(ENCODED_DIR, d))]
            return subdirs
        except FileNotFoundError:
            return []