export default function StrategicDecisionsCard({ report }) {
  const ml = report?.ml_appraisal;
  if (!ml || !ml.strategic_decisions) return null;

  const { immediate_actions, risk_warnings, growth_levers } = ml.strategic_decisions;

  return (
    <div className="bg-white border border-paper-dk rounded-xl p-6 shadow-sm space-y-5">
      <div>
        <h3 className="font-display text-lg text-forest-dk">Predictive Strategic Advisory</h3>
        <p className="text-xs text-gray-500">Machine learning derived business operations & risk mitigation levers</p>
      </div>

      {/* Immediate Actions */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold uppercase text-forest-dk tracking-wider">Priority Operational Actions</h4>
        <div className="grid gap-2">
          {immediate_actions?.map((act, idx) => (
            <div key={idx} className="bg-paper border-l-4 border-forest-dk border-paper-dk rounded-r-lg p-3 text-xs">
              <span className="font-bold text-gray-800 block text-xs">{act.title}</span>
              <p className="text-gray-600 mt-0.5 leading-relaxed">{act.detail}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Warnings & Risk Controls */}
      {risk_warnings?.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase text-amber-800 tracking-wider">Risk Controls & Mitigations</h4>
          <div className="grid gap-2">
            {risk_warnings.map((warn, idx) => (
              <div key={idx} className="bg-amber-50/60 border-l-4 border-amber-600 border border-amber-200 rounded-r-lg p-3 text-xs">
                <span className="font-bold text-amber-900 block text-xs">{warn.title}</span>
                <p className="text-amber-800 mt-0.5 leading-relaxed">{warn.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Growth Levers */}
      {growth_levers?.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase text-forest tracking-wider">Growth & Market Expansion Levers</h4>
          <div className="grid gap-2">
            {growth_levers.map((lever, idx) => (
              <div key={idx} className="bg-[#edf5ef] border-l-4 border-forest border border-[#a7d3b5] rounded-r-lg p-3 text-xs">
                <span className="font-bold text-forest-dk block text-xs">{lever.title}</span>
                <p className="text-gray-700 mt-0.5 leading-relaxed">{lever.detail}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}