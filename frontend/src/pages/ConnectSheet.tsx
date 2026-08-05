import { useEffect, useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../services/api";
import type { ConfigStatusResponse } from "../types/api";

type Status = "loading" | "form" | "already-connected" | "error";

export default function ConnectSheet() {
  const [status, setStatus] = useState<Status>("loading");
  const [serviceAccountEmail, setServiceAccountEmail] = useState("");
  const [sheetUrl, setSheetUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      try {
        const response = await api.get("/config");
        if (!response.ok) {
          throw new Error("Não foi possível carregar as informações de conexão.");
        }
        const data: ConfigStatusResponse = await response.json();
        if (cancelled) return;

        setServiceAccountEmail(data.service_account_email);
        setStatus(data.config ? "already-connected" : "form");
      } catch (err) {
        if (cancelled) return;
        setLoadError(err instanceof Error ? err.message : "Erro inesperado.");
        setStatus("error");
      }
    }

    loadStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);

    try {
      const response = await api.post("/config", { sheet_url: sheetUrl });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Não foi possível conectar a planilha.");
      }

      setStatus("already-connected");
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro inesperado.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCopyEmail() {
    await navigator.clipboard.writeText(serviceAccountEmail);
  }

  if (status === "loading") {
    return <div>Carregando...</div>;
  }

  if (status === "already-connected") {
    return <Navigate to="/dashboard" replace />;
  }

  if (status === "error") {
    return <div role="alert">{loadError}</div>;
  }

  return (
    <div>
      <h1>Conectar Planilha</h1>

      <ol>
        <li>Abra sua planilha do Google Sheets</li>
        <li>
          Clique em &quot;Compartilhar&quot; e adicione o e-mail abaixo com
          permissão de leitor:
          <div>
            <code>{serviceAccountEmail}</code>
            <button type="button" onClick={handleCopyEmail}>
              Copiar
            </button>
          </div>
        </li>
        <li>Cole abaixo o link da planilha compartilhada</li>
      </ol>

      <form onSubmit={handleSubmit}>
        <input
          type="url"
          placeholder="https://docs.google.com/spreadsheets/d/..."
          value={sheetUrl}
          onChange={(event) => setSheetUrl(event.target.value)}
          required
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "Conectando..." : "Conectar"}
        </button>
      </form>

      {formError && <p role="alert">{formError}</p>}
    </div>
  );
}
