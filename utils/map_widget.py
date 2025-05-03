import folium
from folium.plugins import MousePosition, Draw
from streamlit_folium import st_folium
import streamlit as st
from typing import Optional, Tuple


class InteractiveMap:
    def __init__(
        self,
        default_location: Tuple[float, float] = (-14.2350, -51.9253),
        zoom_start: int = 12,
        marker_color: str = 'red',
        tile_layer: str = 'OpenStreetMap'
    ):
        self.default_location = default_location
        self.zoom_start = zoom_start
        self.marker_color = marker_color
        self.tile_layer = tile_layer

    def display(self) -> Optional[Tuple[float, float]]:
        # Estado inicial da coordenada
        if "gps_coords" not in st.session_state:
            st.session_state["gps_coords"] = self.default_location

        fmap = folium.Map(
            location=st.session_state["gps_coords"],
            zoom_start=self.zoom_start,
            tiles=self.tile_layer,
            control_scale=True
        )

        # Plugin de desenho apenas para marcador
        draw = Draw(
            draw_options={
                "polyline": False,
                "polygon": False,
                "circle": False,
                "rectangle": False,
                "circlemarker": False,
                "marker": True
            },
            edit_options={"edit": False, "remove": True}
        )
        draw.add_to(fmap)

        self._add_mouse_position(fmap)

        # Renderiza mapa
        map_data = st_folium(
            fmap,
            height=400,
            use_container_width=True,
            returned_objects=["last_active_drawing"]
        )

        # Captura marcador desenhado
        drawing = map_data.get("last_active_drawing")
        if drawing and drawing["geometry"]["type"] == "Point":
            lon, lat = drawing["geometry"]["coordinates"]
            st.session_state["gps_coords"] = (lat, lon)

        # Exibe coordenadas atuais
        with st.container(border=True):
            st.markdown("### 📍 Localização Atual")
            st.write(f"**Latitude:** {st.session_state['gps_coords'][0]:.6f}")
            st.write(f"**Longitude:** {st.session_state['gps_coords'][1]:.6f}")

        return st.session_state["gps_coords"]

    @staticmethod
    def _add_mouse_position(map_obj: folium.Map) -> None:
        MousePosition(
            position="bottomright",
            separator=" | ",
            empty_string="NaN",
            num_digits=6,
            prefix="📍 Coordenadas:",
            lat_formatter="function(num) {return L.Util.formatNum(num, 6);}",
            lng_formatter="function(num) {return L.Util.formatNum(num, 6);}"
        ).add_to(map_obj)
