import { useState } from "react";

/**
 * Muestra folio con copiado al portapapeles.
 */
export default function FolioTag({ folio }) {
  const [copiado, setCopiado] = useState(false);

  async function copiar() {
    try {
      await navigator.clipboard.writeText(folio);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      setCopiado(false);
    }
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-lg border-2 border-primary bg-[#E3F2FD] px-3 py-2 font-mono text-sm text-ink">
      <span>{folio}</span>
      <button
        type="button"
        onClick={copiar}
        className="rounded p-1 text-primary hover:bg-white/60"
        title="Copiar folio"
        aria-label="Copiar folio"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path
            d="M8 7V5a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2h-2"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <rect x="4" y="7" width="12" height="14" rx="2" stroke="currentColor" strokeWidth="2" />
        </svg>
      </button>
      {copiado ? <span className="text-sm font-medium text-success">¡Copiado!</span> : null}
    </div>
  );
}
