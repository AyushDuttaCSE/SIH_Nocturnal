import { useRef } from "react";

/* Loads html2pdf.js from CDN on demand — keeps it out of the main bundle. */
function loadHtml2Pdf() {
  return new Promise((resolve, reject) => {
    if (window.html2pdf) return resolve(window.html2pdf);
    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js";
    script.onload = () => resolve(window.html2pdf);
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

export default function DprPdfGenerator({ report }) {
  const printRef = useRef(null);

  const handleDownload = async () => {
    const html2pdf = await loadHtml2Pdf();
    html2pdf().from(printRef.current).save(`DPR_${report.village_name}_${report.id}.pdf`);
  };

  if (!report) return null;

  return (
    <div>
      <div ref={printRef} className="bg-paper border border-paper-dk rounded-lg p-5 text-sm whitespace-pre-line leading-relaxed">
        {report.dpr_ready_summary}
      </div>
      <button onClick={handleDownload} className="mt-3 border border-paper-dk rounded-lg px-4 py-2 text-sm font-semibold text-forest">
        Download DPR (.pdf)
      </button>
    </div>
  );
}
