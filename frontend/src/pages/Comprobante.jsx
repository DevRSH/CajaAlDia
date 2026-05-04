import { useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getComprobanteUrl } from "../services/api.js";

export default function Comprobante() {
  const { id } = useParams();
  const navigate = useNavigate();
  const iframeRef = useRef(null);
  const url = id ? getComprobanteUrl(id) : "";

  function imprimir() {
    try {
      const w = iframeRef.current?.contentWindow;
      if (w) {
        w.focus();
        w.print();
        return;
      }
    } catch {
      /* continúa abajo */
    }
    window.print();
  }

  return (
    <div className="min-h-screen bg-bg p-4">
      <div className="no-print mx-auto flex max-w-3xl flex-wrap gap-3 py-4">
        <button
          type="button"
          onClick={imprimir}
          className="rounded-lg bg-primary px-4 py-2 font-medium text-white"
        >
          Imprimir
        </button>
        <button
          type="button"
          onClick={() => navigate("/")}
          className="rounded-lg border border-muted/40 bg-surface px-4 py-2 font-medium text-ink"
        >
          Volver al dashboard
        </button>
      </div>
      <iframe
        ref={iframeRef}
        title="Comprobante"
        src={url}
        className="mx-auto block min-h-[80vh] w-full max-w-3xl rounded-lg border border-primary/25 bg-white shadow-lg"
      />
    </div>
  );
}
