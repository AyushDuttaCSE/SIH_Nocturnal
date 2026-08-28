import { MapContainer, TileLayer, Circle, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function InteractiveMap({ center, competitors = [] }) {
  if (!center) return null;
  const position = [center.lat, center.lon];

  return (
    <MapContainer center={position} zoom={12} style={{ height: 380, borderRadius: 10 }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Circle center={position} radius={5000} pathOptions={{ color: "#3d7a4d", fillOpacity: 0.05 }} />
      <Circle center={position} radius={10000} pathOptions={{ color: "#b5602c", fillOpacity: 0.03 }} />
      <CircleMarker center={position} radius={7} pathOptions={{ color: "#3A7CA5", fillColor: "#3A7CA5", fillOpacity: 1 }}>
        <Popup>Your proposed location</Popup>
      </CircleMarker>
      {competitors.map((c, i) => (
        <CircleMarker
          key={c.osm_id ?? i}
          center={[c.lat, c.lon]}
          radius={5}
          pathOptions={{ color: "#a13a3a", fillColor: "#a13a3a", fillOpacity: 0.8 }}
        >
          <Popup>{c.name} · {c.distance_km} km away</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
