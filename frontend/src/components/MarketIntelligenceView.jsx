export default function MarketIntelligenceView({ report }) {
  const ml = report?.ml_appraisal;
  if (!ml) return null;

  const market = ml.market_intelligence || {};
  const tax = market.tax_profile || {};
  const demand = market.regional_demand || {};
  const benchmarks = market.purchase_benchmarks || {};
  const spatial = ml.spatial_intelligence || {};

  return (
    <div className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm space-y-5">
      <div className="flex justify-between items-center border-b border-paper-dk pb-3">
        <div>
          <h3 className="font-display text-lg text-forest-dk">Market Demand & Regulatory Dynamics</h3>
          <p className="text-xs text-gray-500">Real-time GST compliance, purchasing margins, and demand elasticity</p>
        </div>
        <span className="text-xs font-mono font-bold bg-[#efe8d6] text-forest-dk px-2.5 py-1 rounded">
          HSN {tax.hsn_sac || "N/A"}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-paper border border-paper-dk rounded-lg p-3.5">
          <div className="text-[10px] uppercase font-bold text-gray-500">Applicable GST</div>
          <div className="font-mono text-xl font-bold text-forest-dk mt-0.5">
            {tax.gst_rate_pct}%
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {tax.composition_scheme_eligible ? `Comp. Tax: ${tax.composition_tax_rate_pct}%` : "Exempt / Non-Comp"}
          </div>
        </div>

        <div className="bg-paper border border-paper-dk rounded-lg p-3.5">
          <div className="text-[10px] uppercase font-bold text-gray-500">Regional Demand Index</div>
          <div className="font-mono text-xl font-bold text-forest-dk mt-0.5">
            {demand.demand_score} <span className="text-xs font-normal text-gray-500">/ 100</span>
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {demand.absorption_capacity} Absorption
          </div>
        </div>

        <div className="bg-paper border border-paper-dk rounded-lg p-3.5">
          <div className="text-[10px] uppercase font-bold text-gray-500">Wholesale Gross Margin</div>
          <div className="font-mono text-xl font-bold text-forest-dk mt-0.5">
            {benchmarks.avg_gross_margin_pct}%
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {benchmarks.inventory_turnover_days}-Day Inventory Cycle
          </div>
        </div>

        <div className="bg-paper border border-paper-dk rounded-lg p-3.5">
          <div className="text-[10px] uppercase font-bold text-gray-500">Cluster Pattern</div>
          <div className="font-mono text-sm font-bold text-forest-dk mt-1.5 truncate" title={spatial.clustering_pattern}>
            {spatial.clustering_pattern?.replace(/_/g, " ")}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            Nearest POI: {spatial.min_distance_km} km
          </div>
        </div>
      </div>
    </div>
  );
}