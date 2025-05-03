import subprocess
import json
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExifTool:
    exiftool_path: str = "exiftool"

    def check_exiftool_installed(self) -> bool:
        """Verifica se o exiftool está instalado e acessível"""
        try:
            subprocess.run(
                [self.exiftool_path, "-ver"],
                capture_output=True,
                check=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def read_metadata(self, file_path: str) -> Dict[str, Any]:
        """Lê todos os metadados da imagem"""
        try:
            result = subprocess.run(
                [self.exiftool_path, "-j", "-G", "-a", "-u", "-n", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)[0]
        except subprocess.CalledProcessError as e:
            raise Exception(f"Erro ao ler metadados: {e.stderr}")
        except json.JSONDecodeError:
            raise Exception("Erro ao decodificar metadados (formato inválido)")
        except Exception as e:
            raise Exception(f"Erro inesperado ao ler metadados: {str(e)}")

    def write_metadata(self, file_path: str, tags: Dict[str, str]) -> bool:
        """Escreve metadados na imagem"""
        try:
            args = [self.exiftool_path, "-overwrite_original"]
            for tag, value in tags.items():
                args.extend([f"-{tag}={value}"])
            args.append(file_path)

            result = subprocess.run(
                args,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(result.stderr)
            return True
        except Exception as e:
            raise Exception(f"Erro ao escrever metadados: {str(e)}")

    def write_gps_metadata(self, file_path: str, lat: float, lon: float) -> bool:
        """Escreve metadados GPS com precisão adequada"""
        try:
            lat_ref = 'S' if lat < 0 else 'N'
            lon_ref = 'W' if lon < 0 else 'E'
            lat = round(abs(lat), 6)
            lon = round(abs(lon), 6)

            args = [
                self.exiftool_path,
                "-overwrite_original",
                f"-GPSLatitude={lat}",
                f"-GPSLatitudeRef={lat_ref}",
                f"-GPSLongitude={lon}",
                f"-GPSLongitudeRef={lon_ref}",
                file_path
            ]

            result = subprocess.run(
                args,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(result.stderr)
            return True
        except Exception as e:
            raise Exception(f"Erro ao gravar coordenadas GPS: {str(e)}")

    def get_supported_tags(self) -> Dict[str, str]:
        """Retorna todos os tags suportados pelo ExifTool"""
        try:
            _ = subprocess.run(
                [self.exiftool_path, "-listx"],
                capture_output=True,
                text=True,
                check=True
            )
            # Processar a saída XML para extrair as etiquetas
            # Implementação simplificada - expandir conforme necessário
            return {}
        except Exception as e:
            raise Exception(f"Erro ao obter tags suportados: {str(e)}")
