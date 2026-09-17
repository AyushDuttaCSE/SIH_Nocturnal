import React, { useState, useEffect } from 'react';
import { fetchNearbyBanks } from '../api/geo';

export default function NearbyBanksWidget({ pincode, lat, lon }) {
  const [banks, setBanks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadBanks() {
      if (!pincode && (!lat || !lon)) return;

      setLoading(true);
      setError(null);

      try {
        const data = await fetchNearbyBanks(pincode, lat, lon);
        if (data && data.banks) {
          setBanks(data.banks);
        } else {
          setBanks([]);
        }
      } catch (err) {
        setError("Failed to load nearby banks.");
      } finally {
        setLoading(false);
      }
    }

    loadBanks();
  }, [pincode, lat, lon]);

  if (!pincode && (!lat || !lon)) return null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mt-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
        </svg>
        Institutional Infrastructure (Nearby Banks)
      </h3>

      {loading ? (
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </div>
      ) : error ? (
        <p className="text-red-500 text-sm">{error}</p>
      ) : banks.length === 0 ? (
        <p className="text-gray-500 text-sm">No banks found for PIN {pincode}.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bank Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Branch</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Distance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {banks.slice(0, 5).map((bank) => (
                <tr key={bank.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{bank.bank_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{bank.branch_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {bank.distance_km ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800">
                        {bank.distance_km} km
                      </span>
                    ) : (
                      "Unknown"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {banks.length > 5 && (
            <p className="text-xs text-gray-400 mt-3 text-right">
              Showing top 5 nearest out of {banks.length} branches.
            </p>
          )}
        </div>
      )}
    </div>
  );
}