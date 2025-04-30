import subprocess
import json
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ExifTool:
    exiftool_path: str = "exiftool"

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
        except Exception as e:
            raise Exception(f"Erro ao ler metadados: {str(e)}")

    def write_metadata(self, file_path: str, tags: Dict[str, str]):
        """Escreve metadados na imagem"""
        try:
            args = [self.exiftool_path]
            for tag, value in tags.items():
                args.extend([f"-{tag}={value}"])
            args.append(file_path)

            subprocess.run(args, check=True)
        except Exception as e:
            raise Exception(f"Erro ao escrever metadados: {str(e)}")

    def get_supported_tags(self) -> Dict[str, str]:
        """Retorna todos os tags suportados pelo ExifTool"""
        result = subprocess.run(
            [self.exiftool_path, "-listx"],
            capture_output=True,
            text=True
        )
        # Processar a saída XML para extrair as tags
        # Implementação simplificada - expandir conforme necessário
        return {}
