import { useEffect, useState } from "react";
import "./ColdStartLoader.css";

const SWITCH_AFTER_MS = 3000;
const PROGRESS_DURATION_MS = 50000;

interface ColdStartLoaderProps {
  label?: string;
}

export default function ColdStartLoader({ label = "Carregando..." }: ColdStartLoaderProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const id = setInterval(() => setElapsed(Date.now() - start), 200);
    return () => clearInterval(id);
  }, []);

  if (elapsed < SWITCH_AFTER_MS) {
    return (
      <div className="page-loading">
        <span className="spinner" aria-hidden="true" />
        {label}
      </div>
    );
  }

  const progressElapsed = elapsed - SWITCH_AFTER_MS;
  const percent = Math.min(100, (progressElapsed / PROGRESS_DURATION_MS) * 100);
  const stalled = percent >= 100;

  return (
    <div className="cold-start-loader">
      <p className="cold-start-message">
        O servidor estava inativo e está iniciando — isso pode levar até 1
        minuto na primeira vez.
      </p>
      <div className="cold-start-track">
        <div
          className={`cold-start-bar ${stalled ? "cold-start-bar--pulsing" : ""}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
