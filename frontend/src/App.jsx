import { useState, useEffect, useCallback, useRef } from "react";
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
const GEO_HEADERS = { "User-Agent": "GramSetu-Enterprise-App/2.0" };

// Dynamic Forward Geocoding: Searches nationwide without state restrictions
async function fetchCoordsFromAddress({ village, block, district, state }) {
  const queries = [
    // Priority 1: Full granular hierarchy
    [village, block, district, state, "India"].filter(Boolean).join(", "),
    // Priority 2: Village + District
    [village, district, state, "India"].filter(Boolean).join(", "),
    // Priority 3: Block/Taluk + District
    [block, district, state, "India"].filter(Boolean).join(", "),
    // Priority 4: District wide fallback
    [district, state, "India"].filter(Boolean).join(", ")
  ];

  for (const query of queries) {
    if (!query.replace("India", "").trim()) continue;
    try {
      const res = await fetch(
        `${NOMINATIM_BASE}/search?format=json&q=${encodeURIComponent(query)}&limit=1&addressdetails=1`,
        { headers: GEO_HEADERS }
      );
      const data = await res.json();
      if (data && data.length > 0) {
        const addr = data[0].address || {};
        return {
          lat: parseFloat(data[0].lat),
          lon: parseFloat(data[0].lon),
          displayName: data[0].display_name,
          state: addr.state || "",
          district: addr.state_district || addr.district || "",
          block: addr.county || addr.subdistrict || "",
          village: addr.village || addr.hamlet || addr.town || addr.city || ""
        };
      }
    } catch (err) {
      console.warn(`Query attempt failed for "${query}":`, err);
    }
  }

  return null;
}

// Dynamic Reverse Geocoding: Extracts village, block, district, and state from GPS coords
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
      state: addr.state || "",
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
    village: "",
    block: "",
    district: "",
    state: "",
    category: "GROCERY",
    margin: 50000,
  });

  const [center, setCenter] = useState({ lat: 20.5937, lon: 78.9629 }); // Pan-India center default
  const [resolvedLocationName, setResolvedLocationName] = useState("");
  const [competitors, setCompetitors] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isLocating, setIsLocating] = useState(false);

  // Tracks active coordinates synchronously to prevent stale state submissions
  const activeCoordsRef = useRef(center);
  useEffect(() => {
    activeCoordsRef.current = center;
  }, [center]);

  // 1. Forward geocode with debouncing
  const updateCoordinates = useCallback(async (locationData) => {
    if (!locationData.village && !locationData.district && !locationData.block) return;
    setIsLocating(true);
    const resolved = await fetchCoordsFromAddress(locationData);
    if (resolved) {
      const newCoords = { lat: resolved.lat, lon: resolved.lon };
      setCenter(newCoords);
      activeCoordsRef.current = newCoords;
      setResolvedLocationName(resolved.displayName);
      if (resolved.state && !locationData.state) {
        setForm((prev) => ({ ...prev, state: resolved.state }));
      }
    }
    setIsLocating(false);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      updateCoordinates(form);
    }, 700);
    return () => clearTimeout(timer);
  }, [form.village, form.block, form.district, form.state, updateCoordinates]);

  // 2. Browser GPS detection
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

        const newCoords = { lat, lon };
        setCenter(newCoords);
        activeCoordsRef.current = newCoords;

        const details = await fetchAddressFromCoords(lat, lon);
        if (details) {
          setForm((prev) => ({
            ...prev,
            village: details.village || prev.village,
            block: details.block || prev.block,
            district: details.district || prev.district,
            state: details.state || prev.state,
          }));
          setResolvedLocationName(details.displayName);
        }
        setIsLocating(false);
      },
      (error) => {
        console.warn("GPS error:", error.message);
        alert("Unable to fetch your location. Please enter your location manually.");
        setIsLocating(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleStructureChange = (structure) => {
    if (structure?.margin_capital) {
      setForm((prev) => ({ ...prev, margin: structure.margin_capital }));
    }
  };

  // 3. Dynamic Submission
  const handleGenerate = async () => {
    if (!form.village && !form.district) {
      alert("Please provide at least a Village or District name.");
      return;
    }

    setLoading(true);
    try {
      // Force an immediate coordinate refresh to prevent using stale coordinates
      let targetLat = activeCoordsRef.current.lat;
      let targetLon = activeCoordsRef.current.lon;

      const directResolution = await fetchCoordsFromAddress(form);
      if (directResolution) {
        targetLat = directResolution.lat;
        targetLon = directResolution.lon;
        setCenter({ lat: targetLat, lon: targetLon });
        setResolvedLocationName(directResolution.displayName);
      }

      // 1. Fetch live competitors from OpenStreetMap Overpass
      const density = await competitorsDensity({
        latitude: targetLat,
        longitude: targetLon,
        category: form.category,
        business_type: form.category,
        radius_km: 10,
      });

      const competitorPool = density?.competitors || [];
      const competitorCount = density?.competitor_count ?? competitorPool.length;
      const saturationLevel = density?.saturation_level || "MODERATE";

      setCompetitors(competitorPool);

      // 2. Generate Mistral Feasibility Analysis
      const result = await generateFeasibility({
        village: form.village || "Local Area",
        block: form.block || form.village || "Local Block",
        district: form.district || form.state || "Local District",
        state: form.state || "",
        latitude: targetLat,
        longitude: targetLon,
        margin_capital: form.margin,
        business_category: form.category,
        category_code: form.category,
        competitor_count: competitorCount,
        saturation_level: saturationLevel,
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
        <h1 className="font-display text-2xl text-forest-dk">GramSetu (v2 Dynamic)</h1>
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
          
          <button
            type="button"
            onClick={handleFetchCurrentGPS}
            disabled={isLocating}
            className="inline-flex items-center gap-1.5 text-xs font-semibold bg-[#edf5ef] text-[#245237] border border-[#a7d3b5] px-3 py-1.5 rounded-lg hover:bg-[#d8ebd9] transition disabled:opacity-50"
          >
            <span>📍</span>
            {isLocating ? "Resolving location…" : "Use My Current Location"}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Field
            label="Village / Town"
            placeholder="e.g. Tarakeswar"
            value={form.village}
            onChange={(v) => setForm((prev) => ({ ...prev, village: v }))}
          />
          <Field
            label="Block / Taluk"
            placeholder="e.g. Tarakeswar"
            value={form.block}
            onChange={(v) => setForm((prev) => ({ ...prev, block: v }))}
          />
          <Field
            label="District"
            placeholder="e.g. Hooghly"
            value={form.district}
            onChange={(v) => setForm((prev) => ({ ...prev, district: v }))}
          />
          <Field
            label="State"
            placeholder="e.g. West Bengal"
            value={form.state}
            onChange={(v) => setForm((prev) => ({ ...prev, state: v }))}
          />
        </div>

        {resolvedLocationName ? (
          <div className="text-[11px] text-gray-600 bg-gray-50 px-3 py-2 rounded-lg border border-gray-200 truncate">
            <span className="font-bold text-gray-700">Resolved Location: </span>
            {resolvedLocationName}
          </div>
        ) : (
          <div className="text-[11px] text-gray-400 bg-gray-50 px-3 py-2 rounded-lg border border-dashed border-gray-200">
            Type any village/town and district above, or click "Use My Current Location".
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
            disabled={loading || isLocating}
            className="bg-wheat-dk hover:opacity-90 text-white font-bold px-6 py-2.5 rounded-lg transition ml-auto disabled:opacity-50"
          >
            {loading ? "Generating Feasibility Report…" : "Generate feasibility report"}
          </button>
        </div>
      </section>

      <FinancialCalculatorWidget onStructureChange={handleStructureChange} />

      <section className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-3">
          <h2 className="font-display text-lg">Hyper-local competitor map</h2>
          <span className="text-xs text-gray-500 font-mono">
            Lat: {center.lat.toFixed(4)}, Lon: {center.lon.toFixed(4)}
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

function Field({ label, value, onChange, placeholder = "" }) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-wide mb-1">{label}</label>
      <input
        className="w-full border border-paper-dk rounded-md px-3 py-2 bg-paper text-sm"
        value={value}
        placeholder={placeholder}
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