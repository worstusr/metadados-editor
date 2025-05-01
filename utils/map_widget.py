import folium
from streamlit_folium import st_folium
from typing import Tuple, Optional, Dict, Any
import streamlit as st


class InteractiveMap:
    def __init__(
            self,
            default_location: Tuple[float, float] = (-14.2350, -51.9253),
            zoom: int = 4,
            marker_color: str = 'red',
            marker_icon: str = 'info-sign'
    ):
        """
        Inicializa o mapa interativo com configurações personalizáveis

        Args:
            default_location: Tupla (lat, lng) para a posição inicial
            zoom: Nível de zoom inicial (1-18)
            marker_color: Cor do marcador (blue, green, red, orange, etc.)
            marker_icon: Ícone do marcador (ver opções em: https://fontawesome.com/icons)
        """
        self.default_location = default_location
        self.zoom = zoom
        self.marker_color = marker_color
        self.marker_icon = marker_icon
        self.marker = None
        self.map = None
        self.last_position = default_location

    def create_map(self) -> folium.Map:
        """Cria um mapa Folium com marcador arrastável e múltiplas camadas"""
        try:
            # Cria mapa com configurações otimizadas
            self.map = folium.Map(
                location=self.default_location,
                zoom_start=self.zoom,
                tiles='openstreetmap',
                control_scale=True,
                prefer_canvas=True  # Melhora performance com muitos marcadores
            )

            # Adiciona marcador arrastável
            self.marker = folium.Marker(
                location=self.default_location,
                draggable=True,
                popup="Arraste para ajustar a localização",
                icon=folium.Icon(color=self.marker_color, icon=self.marker_icon, prefix='fa')
            )
            self.marker.add_to(self.map)

            # Adiciona camadas base
            tile_layers = {
                'OpenStreetMap': {
                    'tiles': 'openstreetmap',
                    'attr': '© OpenStreetMap contributors'
                },
                'Stamen Terrain': {
                    'tiles': 'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
                    'attr': 'Map tiles by Stamen Design, under CC BY 3.0. Data by OSM'
                },
                'Satélite': {
                    'tiles': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                    'attr': 'Tiles © Esri'
                }
            }

            for name, config in tile_layers.items():
                folium.TileLayer(
                    tiles=config['tiles'],
                    attr=config['attr'],
                    name=name
                ).add_to(self.map)

            # Adiciona controle de camadas e minimapa
            folium.LayerControl(position='topright').add_to(self.map)
            folium.plugins.MiniMap().add_to(self.map)

            # Adiciona controle de tela cheia
            folium.plugins.Fullscreen(
                position='topright',
                title='Expandir mapa',
                title_cancel='Sair do modo tela cheia',
                force_separate_button=True
            ).add_to(self.map)

            return self.map

        except Exception as e:
            st.error(f"Erro ao criar mapa: {str(e)}")
            return None

    def display(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Exibe o mapa no Streamlit e retorna as coordenadas selecionadas

        Returns:
            Tuple (latitude, longitude) ou (None, None) se nenhuma seleção foi feita
        """
        try:
            if not self.map:
                self.create_map()

            if not self.map:
                return None, None

            # Configuração do componente no Streamlit
            map_data = st_folium(
                self.map,
                height=500,
                width='100%',  # Layout responsivo
                returned_objects=[
                    "last_active_drawing",
                    "last_clicked",
                    "bounds",
                    "zoom"
                ],
                key="interactive_map"
            )

            # Verifica se o marcador foi movido
            if map_data.get("last_active_drawing"):
                coords = map_data["last_active_drawing"]["geometry"]["coordinates"]
                self.last_position = (coords[1], coords[0])  # (lat, lng)
                return self.last_position

            # Verifica se houve clique no mapa
            if map_data.get("last_clicked"):
                self.last_position = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
                return self.last_position

            return None, None

        except Exception as e:
            st.error(f"Erro ao exibir mapa: {str(e)}")
            return None, None

    def get_last_position(self) -> Tuple[float, float]:
        """Retorna a última posição conhecida do marcador"""
        return self.last_position

    def add_circle_marker(
            self,
            location: Tuple[float, float],
            radius: int = 50,
            color: str = 'blue',
            fill: bool = True
    ) -> None:
        """Adiciona um marcador circular ao mapa"""
        if self.map:
            folium.CircleMarker(
                location=location,
                radius=radius,
                color=color,
                fill=fill,
                fill_color=color
            ).add_to(self.map)
