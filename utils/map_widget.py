import folium
from streamlit_folium import st_folium
from typing import Tuple, Optional


class InteractiveMap:
    def __init__(self, default_location: Tuple[float, float] = (-14.2350, -51.9253), zoom: int = 4):
        self.default_location = default_location
        self.zoom = zoom
        self.marker = None
        self.map = None

    def create_map(self) -> folium.Map:
        """Cria um mapa Folium com marcador arrastável"""
        self.map = folium.Map(location=self.default_location, zoom_start=self.zoom)

        # Adiciona marcador arrastável
        self.marker = folium.Marker(
            location=self.default_location,
            draggable=True,
            popup="Arraste para ajustar a localização",
            icon=folium.Icon(color='red', icon='info-sign')
        )
        self.marker.add_to(self.map)

        # Adiciona camadas com atribuições
        folium.TileLayer(
            'openstreetmap',
            attr='© OpenStreetMap contributors'
        ).add_to(self.map)

        folium.TileLayer(
            'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
            name='Stamen Terrain',
            attr='Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
        ).add_to(self.map)

        folium.LayerControl().add_to(self.map)

        return self.map

    def display(self) -> Tuple[Optional[float], Optional[float]]:
        """Exibe o mapa no Streamlit e retorna coordenadas"""
        self.create_map()

        map_data = st_folium(
            self.map,
            height=500,
            width=700,
            returned_objects=["last_active_drawing"],
            key="interactive_map"
        )

        if map_data and map_data.get("last_active_drawing"):
            lat = map_data["last_active_drawing"]["geometry"]["coordinates"][1]
            lng = map_data["last_active_drawing"]["geometry"]["coordinates"][0]
            return lat, lng

        return None, None
