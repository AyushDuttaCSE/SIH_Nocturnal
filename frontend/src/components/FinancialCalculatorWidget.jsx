import { useState, useMemo } from "react";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { structureLoan } from "../api/client";
import { useQuery } from "@tanstack/react-query";

const COLORS = ["#D4A62A", "#1F4D3C"];

export default function FinancialCalculatorWidget({ onStructureChange }) {
  const [margin, setMargin] = useState(100000);

  const { data: loan, isFetching } = useQuery({
    queryKey: ["structure-loan", margin],
    queryFn: () => structureLoan(margin),
    onSuccess: (d) => onStructureChange?.(d),
  });

  const pieData = useMemo(
    () => loan ? [
      { name: "Your margin (10%)", value: Number(loan.margin_capital) },
      { name: "Bank loan (90%)", value: Number(loan.loan_amount) },
    ] : [],
    [loan]
  );

  return (
    <div className="bg-white border border-paper-dk rounded-xl p-6">
      <label className="block text-xs font-semibold uppercase tracking-wide text-forest-dk mb-2">
        Available margin capital — ₹{margin.toLocaleString("en-IN")}
      </label>
      <input
        type="range" min={5000} max={500000} step={1000} value={margin}
        onChange={(e) => setMargin(Number(e.target.value))}
        className="w-full accent-wheat-dk"
      />

      {loan && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-5">
            <Stat label="Project cost" value={`₹${Number(loan.total_project_cost).toLocaleString("en-IN")}`} />
            <Stat label="Loan amount" value={`₹${Number(loan.loan_amount).toLocaleString("en-IN")}`} />
            <Stat label="Interest rate" value={`${loan.interest_rate_pa}% p.a.`} />
            <Stat label="Tenure" value={`${loan.tenure_years} yrs`} />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mt-6">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>

            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={loan.amortization_schedule}>
                <XAxis dataKey="quarter" tickFormatter={(q) => `Q${q}`} fontSize={10} />
                <YAxis fontSize={10} />
                <Tooltip />
                <Legend />
                <Bar dataKey="principal" stackId="a" fill="#1F4D3C" name="Principal" />
                <Bar dataKey="interest" stackId="a" fill="#D4A62A" name="Interest" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
      {isFetching && <p className="text-xs text-soil mt-2">Recalculating…</p>}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-paper border border-paper-dk rounded-lg p-3">
      <div className="text-[11px] uppercase tracking-wide text-soil/70 font-semibold">{label}</div>
      <div className="font-mono text-lg font-bold text-forest-dk mt-1">{value}</div>
    </div>
  );
}
