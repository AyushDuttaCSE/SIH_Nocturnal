import { useState, useEffect, useCallback } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LanguageProvider, useLanguage } from "./context/LanguageContext";
import FinancialCalculatorWidget from "./components/FinancialCalculatorWidget";
import InteractiveMap from "./components/InteractiveMap";
import AdvisoryReportView from "./components/AdvisoryReportView";
import DprPdfGenerator from "./components/DprPdfGenerator";
import { competitorsDensity, generateFeasibility } from "./api/client";

const queryClient = new QueryClient();

const CATEGORIES = [
  { code: "DAIRY", label: "Dairy / Milk products" },
  { code: "GROCERY", label: "Grocery / General store" },
  { code: "TAILOR", label: "Tailoring / Boutique" },
  { code: "POULTRY", label: "Poultry farming" },
  { code: "BAKERY", label: "Bakery / Snacks" },
  { code: "HANDICRAFT", label: "Handicraft / Weaving" },
  { code: "SALON", label: "Salon / Beauty parlour" },
  { code: "ELECTRONICS", label: "Mobile & electronics repair" },
  { code: "HARDWARE", label: "Hardware / Building materials" },
];

const NOMINATIM_BASE = "https://nominatim.openstreetmap.org";
const GEO_HEADERS = { "User-Agent": "GramSetu-App/1.0" };

// Forward Geocoding: Converts Village/Block/District into exact coordinates
async function fetchCoordsFromAddress({ village, block, district }) {
  // Strategy 1: Specific pinpoint query
  const specificQuery = [village, block, district, "West Bengal", "India"].filter(Boolean).join(", ");
  try {
    const res = await fetch(
      `${NOMINATIM_BASE}/search?format=json&q=${encodeURIComponent(specificQuery)}&limit=1`,
      { headers: GEO_HEADERS }
    );
    const data = await res.json();
    if (data && data.length > 0) {
      return {
        lat: parseFloat(data[0].lat),
        lon: parseFloat(data[0].lon),
        displayName: data[0].display_name
      };
    }
  } catch (err) {
    console.error("Village forward geocode failed:", err);
  }

  // Strategy 2: Fallback to Sub-District / District level
  if (district || block) {
    const fallbackQuery = [block || district, district, "West Bengal", "India"].filter(Boolean).join(", ");
    try {
      const res = await fetch(
        `${NOMINATIM_BASE}/search?format=json&q=${encodeURIComponent(fallbackQuery)}&limit=1`,
        { headers: GEO_HEADERS }
      );
      const data = await res.json();
      if (data && data.length > 0) {
        return {
          lat: parseFloat(data[0].lat),
          lon: parseFloat(data[0].lon),
          displayName: data[0].display_name
        };
      }
    } catch (e) {
      console.error("District fallback geocode failed:", e);
    }
  }

  return null;
}

// Reverse Geocoding: Converts GPS lat/lon into readable administrative names
async function fetchAddressFromCoords(lat, lon) {
  try {
    const res = await fetch(
      `${NOMINATIM_BASE}/reverse?format=json&lat=${lat}&lon=${lon}&zoom=14&addressdetails=1`,
      { headers: GEO_HEADERS }
    );
    const data = await res.json();
    const addr = data.address || {};

    return {
      village: addr.village || addr.hamlet || addr.suburb || addr.town || addr.city || "",
      block: addr.county || addr.subdistrict || "",
      district: addr.state_district || addr.district || addr.city || "",
      displayName: data.display_name || ""
    };
  } catch (err) {
    console.error("Reverse geocoding failed:", err);
    return null;
  }
}

function Wizard() {
  const { language, setLanguage, listen } = useLanguage();
  const [form, setForm] = useState({
    village: "Bishnupur",
    block: "Bishnupur-I",
    district: "Bankura",
    category: "GROCERY",
    margin: 100000,
  });

  const [center, setCenter] = useState({ lat: 23.0708, lon: 87.3167 });
  const [resolvedLocationName, setResolvedLocationName] = useState("Bishnupur, Bankura, West Bengal, India");
  const [competitors, setCompetitors] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);

  // 1. Forward geocode whenever village/block/district changes
  const updateCoordinates = useCallback(async (locationData) => {
    if (!locationData.village && !locationData.district) return;
    setIsLocating(true);
    const resolved = await fetchCoordsFromAddress(locationData);
    if (resolved) {
      setCenter({ lat: resolved.lat, lon: resolved.lon });
      setResolvedLocationName(resolved.displayName);
    }
    setIsLocating(false);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      updateCoordinates(form);
    }, 600);
    return () => clearTimeout(timer);
  }, [form.village, form.block, form.district, updateCoordinates]);

  // 2. Reverse geocode when fetching current browser GPS
  const handleFetchCurrentGPS = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        setCenter({ lat, lon });

        const details = await fetchAddressFromCoords(lat, lon);
        if (details) {
          setForm((prev) => ({
            ...prev,
            village: details.village || prev.village,
            block: details.block || prev.block,
            district: details.district || prev.district,
          }));
          setResolvedLocationName(details.displayName);
        }
        setIsLocating(false);
      },
      (error) => {
        console.warn("GPS error:", error.message);
        alert("Unable to fetch your location. Please check browser location permissions.");
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Sync margin when slider moves in FinancialCalculatorWidget
  const handleStructureChange = (structure) => {
    if (structure?.margin_capital) {
      setForm((prev) => ({ ...prev, margin: structure.margin_capital }));
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const density = await competitorsDensity({
        latitude: center.lat,
        longitude: center.lon,
        category: form.category,
        business_type: form.category,
        radius_km: 10,
      });
      setCompetitors(density?.competitors || []);

      const result = await generateFeasibility({
        village: form.village,
        block: form.block,
        district: form.district,
        village_name: form.village,
        block_name: form.block,
        district_name: form.district,
        latitude: center.lat,
        longitude: center.lon,
        center_lat: center.lat,
        center_lng: center.lon,
        margin_capital: form.margin,
        business_category: form.category,
        category_code: form.category,
        competitor_count: density?.competitor_count || density?.competitors?.length || 0,
        saturation_level: density?.saturation_level || "MODERATE",
        language,
      });

      setReport(result?.report || result);
    } catch (e) {
      alert(e.response?.data?.message || e.message || "Failed to generate report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-5 py-10 space-y-6 font-body">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="font-display text-2xl text-forest-dk">GramSetu</h1>
          <p className="text-xs text-gray-500">Rural Credit & Enterprise Feasibility Terminal</p>
        </div>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="border border-paper-dk rounded-md px-2 py-1 text-sm bg-white"
        >
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
          <option value="bn">বাংলা</option>
          <option value="mr">मराठी</option>
          <option value="ta">தமிழ்</option>
          <option value="te">తెలుగు</option>
        </select>
      </header>

      <section className="bg-white border border-paper-dk rounded-xl p-6 space-y-4 shadow-sm">
        <div className="flex justify-between items-center">
          <h2 className="font-display text-lg">Business enquiry</h2>
          
          {/* GPS Auto-Detect Button */}
          <button
            type="button"
            onClick={handleFetchCurrentGPS}
            disabled={isLocating}
            className="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#edf5ef] text-[#245237] border border-[#a7d3b5] px-3 py-1.5 rounded-lg hover:bg-[#d8ebd9] transition disabled:opacity-50"
          >
            <span>📍</span>
            {isLocating ? "Locating on map…" : "Use My Current Location"}
          </button>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <Field
            label="Village"
            value={form.village}
            onChange={(v) => setForm((prev) => ({ ...prev, village: v }))}
          />
          <Field
            label="Block"
            value={form.block}
            onChange={(v) => setForm((prev) => ({ ...prev, block: v }))}
          />
          <Field
            label="District"
            value={form.district}
            onChange={(v) => setForm((prev) => ({ ...prev, district: v }))}
          />
        </div>

        {/* Live Resolved Address Line */}
        {resolvedLocationName && (
          <div className="text-[11px] text-gray-600 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 truncate">
            <span className="font-bold text-gray-700">OSM Target: </span>
            {resolvedLocationName}
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide mb-1">Category</label>
          <select
            className="w-full border border-paper-dk rounded-md px-3 py-2 bg-paper"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            {CATEGORIES.map((c) => (
              <option key={c.code} value={c.code}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-1">
          <button
            type="button"
            onClick={() =>
              listen((text) => {
                setForm((prev) => ({ ...prev, village: text }));
              })
            }
            className="text-xs border border-paper-dk hover:bg-gray-50 rounded-full px-4 py-2 transition"
          >
            🎙 Speak village name
          </button>

          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="bg-wheat-dk hover:opacity-90 text-white font-bold px-6 py-2.5 rounded-lg transition ml-auto disabled:opacity-50"
          >
            {loading ? "Generating Real Feasibility…" : "Generate feasibility report"}
          </button>
        </div>
      </section>

      {/* Synchronizes the margin capital slider with calculators.py */}
      <FinancialCalculatorWidget onStructureChange={handleStructureChange} />

      <section className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-3">
          <h2 className="font-display text-lg">Hyper-local competitor map</h2>
          <span className="text-xs text-gray-500 font-mono">
            GPS: {center.lat.toFixed(4)}, {center.lon.toFixed(4)}
          </span>
        </div>
        <InteractiveMap center={center} competitors={competitors} />
      </section>

      {report && (
        <>
          <AdvisoryReportView report={report} />
          <section className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm">
            <h2 className="font-display text-lg mb-3">Bank-ready DPR</h2>
            <DprPdfGenerator report={report} />
          </section>
        </>
      )}
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-wide mb-1">{label}</label>
      <input
        className="w-full border border-paper-dk rounded-md px-3 py-2 bg-paper"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <Wizard />
      </LanguageProvider>
    </QueryClientProvider>
  );
}