import streamlit as st
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
from utils.exif import ExifTool
from utils.map_widget import InteractiveMap
import pandas as pd
import os


class ExifEditor:
    def __init__(self):
        self.exif = ExifTool()
        self.map = InteractiveMap(marker_color='blue', marker_icon='camera')

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
            'modified': False,
            'author': '',
            'copyright': '',
            'description': ''
        }
        for key, value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def load_styles():
        """Carrega os estilos CSS"""
        try:
            css_file = Path(__file__).parent / "static" / "style.css"
            if css_file.exists():
                with open(css_file) as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
            else:
                st.warning("Arquivo CSS não encontrado. O aplicativo será exibido sem estilos personalizados.")
        except Exception as e:
            st.warning(f"Erro ao carregar estilos CSS: {str(e)}")

    def file_uploader(self):
        """Componente de upload de arquivo"""
        with st.expander("📤 Upload de Imagem", expanded=True):
            uploaded_file = st.file_uploader(
                "Arraste sua imagem aqui",
                type=["jpg", "jpeg", "png", "dng", "cr2", "nef"],
                accept_multiple_files=False,
                key="file_uploader"
            )

            if uploaded_file is not None:
                try:
                    # Cria arquivo temporário com extensão apropriada
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                        tmp.write(uploaded_file.read())
                        st.session_state.image_path = tmp.name

                        # Lê metadados
                        metadata = self.exif.read_metadata(tmp.name)

                        # Converte valores para string e filtra metadados inválidos
                        st.session_state.metadata = {
                            k: str(v) for k, v in metadata.items()
                            if v is not None and str(v).strip() != ''
                        }

                        self.extract_initial_values()
                        st.session_state.modified = False

                    # Exibe a imagem e metadados
                    cols = st.columns([1, 3])
                    with cols[0]:
                        try:
                            st.image(
                                Image.open(st.session_state.image_path),
                                caption="Imagem carregada",
                                use_container_width=True  # Esta é a versão atualizada do parâmetro
                            )
                        except Exception as e:
                            st.error(f"Erro ao exibir imagem: {str(e)}")

                    with cols[1]:
                        if st.session_state.metadata:
                            # Cria DataFrame com os metadados
                            df = pd.DataFrame.from_dict(
                                st.session_state.metadata,
                                orient='index',
                                columns=['Valor']
                            )
                            st.dataframe(
                                df,
                                height=min(300, len(df) * 35 + 3),  # Altura dinâmica
                                use_container_width=True
                            )
                        else:
                            st.warning("Nenhum metadado encontrado na imagem.")

                except Exception as e:
                    st.error(f"Erro ao processar imagem: {str(e)}")
                    if 'image_path' in st.session_state and st.session_state.image_path:
                        try:
                            os.unlink(st.session_state.image_path)
                        except:
                            pass
                    st.session_state.image_path = None

    def extract_initial_values(self):
        """Extrai valores iniciais dos metadados"""
        meta = st.session_state.metadata
        st.session_state.make = meta.get('Make', '')
        st.session_state.model = meta.get('Model', '')
        st.session_state.lens = meta.get('LensModel', meta.get('LensInfo', ''))
        st.session_state.author = meta.get('Artist', meta.get('Author', ''))
        st.session_state.copyright = meta.get('Copyright', '')
        st.session_state.description = meta.get('ImageDescription', meta.get('Description', ''))

    def metadata_editor(self):
        """Editor principal de metadados"""
        if not st.session_state.get('image_path'):
            return st.warning("Por favor, carregue uma imagem primeiro.")

        with st.expander("✏️ Editor de Metadados", expanded=True):
            tab1, tab2 = st.tabs(["📷 Dados Técnicos", "©️ Direitos Autorais"])

            with tab1:
                success_tech = self.technical_metadata()
                if success_tech:
                    st.success("Metadados técnicos atualizados com sucesso!")

            with tab2:
                success_copyright = self.copyright_metadata()
                if success_copyright:
                    st.success("Metadados de direitos autorais atualizados com sucesso!")

    def technical_metadata(self) -> bool:
        """Componente de metadados técnicos"""
        success = False
        cols = st.columns(3)

        with cols[0]:
            st.subheader("Fabricante/Modelo")
            make = st.selectbox(
                "Fabricante",
                options=[''] + list(self.camera_presets.keys()),
                index=self.get_preset_index(list(self.camera_presets.keys()), st.session_state.make),
                key='make_select'
            )

            model = ''
            if make:
                model_options = [''] + self.camera_presets[make]
                model = st.selectbox(
                    "Modelo",
                    options=model_options,
                    index=self.get_preset_index(model_options, st.session_state.model),
                    key='model_select'
                )

        with cols[1]:
            st.subheader("Lente")
            lens = st.selectbox(
                "Modelo da Lente",
                options=[''] + self.lens_presets.get(make, []),
                index=self.get_preset_index(self.lens_presets.get(make, []), st.session_state.lens),
                key='lens_select'
            )

        with cols[2]:
            st.subheader("Configurações")
            aperture = st.selectbox(
                "Abertura (f/)",
                options=[''] + [f"f/{x}" for x in [1.2, 1.4, 1.8, 2.0, 2.8, 3.5, 4.0, 5.6, 8.0, 11.0, 16.0, 22.0]],
                index=0,
                key='aperture_select'
            )

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

        # Aplica as alterações
        tags = {}
        if make and model:
            tags.update({'Make': make, 'Model': model})
        if lens:
            tags.update({'LensModel': lens, 'LensInfo': lens})
        if aperture and aperture != '':
            tags.update({
                'ApertureValue': aperture.replace('f/', ''),
                'FNumber': aperture.replace('f/', '')
            })
        if shutter and shutter != '':
            tags.update({
                'ShutterSpeedValue': shutter,
                'ExposureTime': shutter
            })

        if tags:
            try:
                if self.exif.write_metadata(st.session_state.image_path, tags):
                    st.session_state.modified = True
                    success = True
                    # Atualiza a sessão com os novos valores
                    if 'Make' in tags:
                        st.session_state.make = tags['Make']
                    if 'Model' in tags:
                        st.session_state.model = tags['Model']
                    if 'LensModel' in tags:
                        st.session_state.lens = tags['LensModel']
            except Exception as e:
                st.error(f"Erro ao atualizar metadados técnicos: {str(e)}")

        return success

    @staticmethod
    def get_preset_index(options: list, current_value: str) -> int:
        """Retorna o índice para seleção em dropdowns"""
        try:
            return options.index(current_value) + 1  # +1 por causa do item vazio
        except ValueError:
            return 0

    def copyright_metadata(self) -> bool:
        """Editor de metadados de copyright"""
        success = False
        author = st.text_input("Autor", value=st.session_state.author, key='author_input')
        copyright_info = st.text_input("Direitos Autorais", value=st.session_state.copyright, key='copyright_input')
        description = st.text_area("Descrição", value=st.session_state.description, key='description_input')

        if st.button("Aplicar Alterações", key='apply_copyright'):
            tags = {}
            if author:
                tags.update({'Artist': author, 'Author': author})
            if copyright_info:
                tags.update({'Copyright': copyright_info})
            if description:
                tags.update({'ImageDescription': description, 'Description': description})

            if tags:
                try:
                    if self.exif.write_metadata(st.session_state.image_path, tags):
                        st.session_state.modified = True
                        success = True
                        # Atualiza a sessão
                        st.session_state.author = author
                        st.session_state.copyright = copyright_info
                        st.session_state.description = description
                except Exception as e:
                    st.error(f"Erro ao atualizar metadados de copyright: {str(e)}")

        return success

    def geo_tagging(self):
        """Componente de geolocalização"""
        if not st.session_state.get('image_path'):
            return st.warning("Por favor, carregue uma imagem primeiro.")

        with st.expander("🌍 Georreferenciamento", expanded=True):
            st.info("Arraste o marcador para a localização desejada ou clique no mapa para posicioná-lo")
            lat, lon = self.map.display()

            if lat is not None and lon is not None:
                if st.button("Salvar Localização", key='save_location'):
                    try:
                        if self.exif.write_gps_metadata(st.session_state.image_path, lat, lon):
                            st.success(f"📍 Coordenadas gravadas com sucesso: {lat:.6f}, {lon:.6f}")
                            st.session_state.modified = True
                        else:
                            st.error("Falha ao gravar coordenadas na imagem")
                    except Exception as e:
                        st.error(f"Erro ao gravar coordenadas: {str(e)}")

    def download_section(self):
        """Seção de download da imagem editada"""
        if not st.session_state.get('image_path'):
            return

        if st.session_state.modified:
            st.divider()
            with st.expander("💾 Download da Imagem Modificada", expanded=True):
                st.write("Clique abaixo para baixar a imagem com todos os metadados atualizados:")

                # Criamos um container para melhor organização
                with st.container():
                    cols = st.columns([1, 2, 1])  # Centraliza o botão

                    with cols[1]:  # Coluna do meio
                        try:
                            with open(st.session_state.image_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Baixar Imagem",
                                    data=f,
                                    file_name=f"edited_{os.path.basename(st.session_state.image_path)}",
                                    mime="image/jpeg",
                                    use_container_width=True,  # Garante que o botão use a largura da coluna
                                    key='download_btn'
                                )
                        except Exception as e:
                            st.error(f"Erro ao preparar arquivo para download: {str(e)}")

    def cleanup(self):
        """Limpeza de recursos temporários"""
        if st.session_state.get('image_path'):
            try:
                os.unlink(st.session_state.image_path)
            except:
                pass

    def run(self):
        """Fluxo principal da aplicação"""
        if not self.exif.check_exiftool_installed():
            st.error("""
                **ExifTool não está instalado ou não foi encontrado.**  
                Por favor, instale o ExifTool no seu sistema e certifique-se que está no PATH.
                Visite [exiftool.org](https://exiftool.org/) para instruções de instalação.
            """)
            return

        try:
            self.file_uploader()
            self.metadata_editor()
            self.geo_tagging()
            self.download_section()
        finally:
            self.cleanup()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Professional EXIF Editor",
        layout="wide",
        page_icon="📷",
        initial_sidebar_state="expanded"
    )

    st.title("📷 Professional EXIF Editor")
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h3>Edite os metadados EXIF das suas imagens fotográficas</h3>
        </div>
    """, unsafe_allow_html=True)

    editor = ExifEditor()
    editor.run()
