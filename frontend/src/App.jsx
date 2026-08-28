import { useState } from "react";
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

function Wizard() {
  const { language, setLanguage, listen } = useLanguage();
  const [form, setForm] = useState({
    village: "Bishnupur", block: "Bishnupur-I", district: "Bankura",
    lat: 23.0708, lon: 87.3167, category: "GROCERY", margin: 100000,
  });
  const [center, setCenter] = useState({ lat: 23.0708, lon: 87.3167 });
  const [competitors, setCompetitors] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const density = await competitorsDensity({
        latitude: center.lat, longitude: center.lon,
        category_code: form.category, radius_km: 10,
      });
      setCompetitors(density.competitors || []);

      const result = await generateFeasibility({
        village_name: form.village, block_name: form.block, district_name: form.district,
        center_lat: center.lat, center_lng: center.lon,
        margin_capital: form.margin, category_code: form.category, language,
      });
      setReport(result);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-5 py-10 space-y-6 font-body">
      <header className="flex justify-between items-center">
        <h1 className="font-display text-2xl text-forest-dk">GramSetu</h1>
        <select value={language} onChange={(e) => setLanguage(e.target.value)} className="border border-paper-dk rounded-md px-2 py-1 text-sm">
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
          <option value="bn">বাংলা</option>
          <option value="mr">मराठी</option>
          <option value="ta">தமிழ்</option>
          <option value="te">తెలుగు</option>
        </select>
      </header>

      <section className="bg-white border border-paper-dk rounded-xl p-6 space-y-4">
        <h2 className="font-display text-lg">Business enquiry</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <Field label="Village" value={form.village} onChange={(v) => setForm({ ...form, village: v })} />
          <Field label="Block" value={form.block} onChange={(v) => setForm({ ...form, block: v })} />
          <Field label="District" value={form.district} onChange={(v) => setForm({ ...form, district: v })} />
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide mb-1">Category</label>
          <select
            className="w-full border border-paper-dk rounded-md px-3 py-2 bg-paper"
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
          >
            {CATEGORIES.map((c) => <option key={c.code} value={c.code}>{c.label}</option>)}
          </select>
        </div>
        <button
          type="button"
          onClick={() => listen((text) => setForm({ ...form, village: text }))}
          className="text-xs border border-paper-dk rounded-full px-3 py-1"
        >
          🎙 Speak village name
        </button>
        <button onClick={handleGenerate} disabled={loading} className="bg-wheat-dk text-white font-bold px-5 py-3 rounded-lg">
          {loading ? "Generating…" : "Generate feasibility report"}
        </button>
      </section>

      <FinancialCalculatorWidget onStructureChange={() => {}} />

      <section className="bg-white border border-paper-dk rounded-xl p-6">
        <h2 className="font-display text-lg mb-3">Hyper-local competitor map</h2>
        <InteractiveMap center={center} competitors={competitors} />
      </section>

      {report && (
        <>
          <AdvisoryReportView report={report} />
          <section className="bg-white border border-paper-dk rounded-xl p-6">
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
