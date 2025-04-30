import streamlit as st
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
from utils.exif import ExifTool
from utils.map_widget import InteractiveMap
import pandas as pd


class ExifEditor:
    def __init__(self):
        self.exif = ExifTool()
        self.map = InteractiveMap()

        # Presets de equipamentos
        self.camera_presets = {
            'Canon': ['EOS 5D Mark IV', 'EOS R5', 'EOS 80D', 'PowerShot G7 X'],
            'Nikon': ['D850', 'Z7 II', 'D3500', 'Coolpix P1000'],
            'Sony': ['α7R IV', 'α6400', 'RX100 VII'],
            'Fujifilm': ['X-T4', 'X100V', 'GFX 100S'],
            'Smartphone': ['iPhone 15 Pro', 'Samsung Galaxy S23', 'Google Pixel 7']
        }

        self.lens_presets = {
            'Canon': ['EF 24-70mm f/2.8L', 'EF 70-200mm f/2.8L', 'RF 50mm f/1.2L'],
            'Nikon': ['24-70mm f/2.8G ED', '70-200mm f/2.8E FL ED', '50mm f/1.8G'],
            'Sony': ['FE 24-70mm f/2.8 GM', 'FE 70-200mm f/2.8 GM OSS'],
            'Fujifilm': ['XF 16-55mm f/2.8 R LM WR', 'XF 56mm f/1.2 R']
        }

        self.initialize_session()
        self.load_styles()

    @staticmethod
    def initialize_session():
        """Inicializa o estado da sessão"""
        session_defaults = {
            'image_path': None,
            'metadata': {},
            'make': '',
            'model': '',
            'lens': '',
            'modified': False
        }
        for key, value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def load_styles():
        """Carrega os estilos CSS"""
        css_file = Path(__file__).parent / "static" / "style.css"
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    def file_uploader(self):
        """Componente de upload de arquivo"""
        with st.expander("📤 Upload de Imagem", expanded=True):
            uploaded_file = st.file_uploader(
                "Arraste sua imagem aqui",
                type=["jpg", "jpeg", "png", "dng", "cr2", "nef"],
                accept_multiple_files=False
            )

            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    tmp.write(uploaded_file.read())
                    st.session_state.image_path = tmp.name
                    st.session_state.metadata = self.exif.read_metadata(tmp.name)
                    self.extract_initial_values()
                    st.session_state.modified = False

                cols = st.columns([1, 3])
                with cols[0]:
                    st.image(
                        Image.open(st.session_state.image_path),
                        caption="Imagem carregada",
                        use_container_width=True
                    )
                with cols[1]:
                    st.dataframe(pd.DataFrame.from_dict(st.session_state.metadata, orient='index'), height=300)

    def extract_initial_values(self):
        """Extrai valores iniciais dos metadados"""
        meta = st.session_state.metadata
        st.session_state.make = meta.get('Make', '')
        st.session_state.model = meta.get('Model', '')
        st.session_state.lens = meta.get('LensModel', meta.get('LensInfo', ''))

    def metadata_editor(self):
        """Editor principal de metadados"""
        if not st.session_state.get('image_path'):
            return

        with st.expander("✏️ Editor de Metadados", expanded=True):
            tab1, tab2 = st.tabs(["📷 Dados Técnicos", "©️ Direitos Autorais"])

            with tab1:
                self.technical_metadata()
            with tab2:
                self.copyright_metadata()

    def technical_metadata(self):
        """Componente de metadados técnicos"""
        cols = st.columns(3)

        with cols[0]:
            st.subheader("Fabricante/Modelo")
            make = st.selectbox(
                "Fabricante",
                options=[''] + list(self.camera_presets.keys()),
                index=self.get_preset_index(list(self.camera_presets.keys()), st.session_state.make),
                key='make_select'
            )

            if make:
                model_options = [''] + self.camera_presets[make]
                model = st.selectbox(
                    "Modelo",
                    options=model_options,
                    index=self.get_preset_index(model_options, st.session_state.model),
                    key='model_select'
                )

                if model:
                    self.exif.write_metadata(st.session_state.image_path, {
                        'Make': make,
                        'Model': model
                    })
                    st.session_state.modified = True

        with cols[1]:
            st.subheader("Lente")
            lens = st.selectbox(
                "Modelo da Lente",
                options=[''] + self.lens_presets.get(make, []),
                index=self.get_preset_index(self.lens_presets.get(make, []), st.session_state.lens),
                key='lens_select'
            )

            if lens:
                self.exif.write_metadata(st.session_state.image_path, {
                    'LensModel': lens,
                    'LensInfo': lens
                })
                st.session_state.modified = True

        with cols[2]:
            st.subheader("Configurações")
            aperture = st.selectbox(
                "Abertura (f/)",
                options=[''] + [f"f/{x}" for x in [1.2, 1.4, 1.8, 2.0, 2.8, 3.5, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0]],
                index=0,
                key='aperture_select'
            )

            if aperture and aperture != '':
                self.exif.write_metadata(st.session_state.image_path, {
                    'ApertureValue': aperture.replace('f/', ''),
                    'FNumber': aperture.replace('f/', '')
                })
                st.session_state.modified = True

            shutter = st.selectbox(
                "Velocidade do Obturador",
                options=[''] + [f"1/{x}" for x in [8000, 4000, 2000, 1000, 500, 250, 125, 60, 30, 15, 8, 4, 2]] + ["1",
                                                                                                                   "2",
                                                                                                                   "4",
                                                                                                                   "8",
                                                                                                                   "15",
                                                                                                                   "30"],
                index=0,
                key='shutter_select'
            )

            if shutter and shutter != '':
                self.exif.write_metadata(st.session_state.image_path, {
                    'ShutterSpeedValue': shutter,
                    'ExposureTime': shutter
                })
                st.session_state.modified = True

    @staticmethod
    def get_preset_index(options: list, current_value: str) -> int:
        """Retorna o índice para seleção em dropdowns"""
        try:
            return options.index(current_value) + 1  # +1 por causa do item vazio
        except ValueError:
            return 0

    def copyright_metadata(self):
        """Editor de metadados de copyright"""
        author = st.text_input("Autor", key='author_input')
        copyright_info = st.text_input("Direitos Autorais", key='copyright_input')
        description = st.text_area("Descrição", key='description_input')

        if author or copyright_info or description:
            tags = {}
            if author:
                tags['Artist'] = author
                tags['Author'] = author
            if copyright_info:
                tags['Copyright'] = copyright_info
            if description:
                tags['ImageDescription'] = description
                tags['Description'] = description

            self.exif.write_metadata(st.session_state.image_path, tags)
            st.session_state.modified = True

    def geo_tagging(self):
        """Componente de geolocalização"""
        if not st.session_state.get('image_path'):
            return

        with st.expander("🌍 Georreferenciamento", expanded=True):
            lat, lon = self.map.display()

            if lat and lon:
                self.exif.write_metadata(st.session_state.image_path, {
                    'GPSLatitude': str(abs(lat)),
                    'GPSLatitudeRef': 'S' if lat < 0 else 'N',
                    'GPSLongitude': str(abs(lon)),
                    'GPSLongitudeRef': 'W' if lon < 0 else 'E'
                })
                st.success(f"📍 Coordenadas gravadas: {lat:.6f}, {lon:.6f}")
                st.session_state.modified = True

    def download_section(self):
        """Seção de download da imagem editada"""
        if not st.session_state.get('image_path') or not st.session_state.modified:
            return

        st.divider()
        with st.expander("💾 Download da Imagem Modificada", expanded=True):
            st.write("Clique abaixo para baixar a imagem com todos os metadados atualizados:")

            with open(st.session_state.image_path, "rb") as f:
                st.download_button(
                    label="⬇️ Baixar Imagem",
                    data=f,
                    file_name="imagem_editada.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                    key='download_btn'
                )

    def run(self):
        """Fluxo principal da aplicação"""
        self.file_uploader()
        self.metadata_editor()
        self.geo_tagging()
        self.download_section()


if __name__ == "__main__":
    st.set_page_config(page_title="Professional EXIF Editor", layout="wide")
    editor = ExifEditor()
    editor.run()