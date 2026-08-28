import SwotMatrix from "./SwotMatrix";

export default function AdvisoryReportView({ report }) {
  if (!report) return null;
  const pricing = report.suggested_pricing_strategy || {};

  return (
    <div className="bg-white border border-paper-dk rounded-xl p-6 space-y-5">
      <div>
        <h3 className="font-display text-lg mb-1">Market reach</h3>
        <p className="text-sm leading-relaxed">{report.market_reach_summary}</p>
      </div>

      <SwotMatrix report={report} />

      <div>
        <h3 className="font-display text-lg mb-2">Suggested pricing strategy</h3>
        <div className="flex flex-wrap gap-2">
          {Object.entries(pricing).map(([tier, desc]) => (
            <span key={tier} className="bg-paper border border-paper-dk rounded-full px-3 py-1 text-xs font-semibold text-forest">
              {tier}: {desc}
            </span>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-display text-lg mb-1">Localized risks</h3>
        <ul className="list-disc pl-5 text-sm space-y-1">
          {(report.localized_risks || []).map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </div>
    </div>
  );
}
