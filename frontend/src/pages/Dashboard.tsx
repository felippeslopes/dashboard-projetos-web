import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../services/api";
import type { DashboardResponse } from "../types/api";
import ProjectStatCard from "../components/cards/ProjectStatCard";
import ProjectsTable from "../components/table/ProjectsTable";
import StatusPieChart from "../components/charts/StatusPieChart";
import LogoutButton from "../components/LogoutButton";

type Status = "loading" | "ready" | "no-sheet" | "error";

export default function Dashboard() {
  const [status, setStatus] = useState<Status>("loading");
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        const response = await api.get("/dashboard");

        if (response.status === 404) {
          if (!cancelled) setStatus("no-sheet");
          return;
        }

        const body = await response.json();

        if (!response.ok) {
          throw new Error(body.detail ?? "Não foi possível carregar o dashboard.");
        }

        if (cancelled) return;
        setData(body as DashboardResponse);
        setStatus("ready");
      } catch (err) {
        if (cancelled) return;
        setErrorMessage(err instanceof Error ? err.message : "Erro inesperado.");
        setStatus("error");
      }
    }

    loadDashboard();
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "loading") {
    return <div>Carregando...</div>;
  }

  if (status === "no-sheet") {
    return <Navigate to="/connect-sheet" replace />;
  }

  if (status === "error") {
    return <div role="alert">{errorMessage}</div>;
  }

  if (!data) {
    return null;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Dashboard</h1>
        <LogoutButton />
      </div>

      {data.planilha_truncada && (
        <p role="alert">
          A planilha tem mais linhas do que o limite processado — só as
          primeiras 2000 linhas de dados foram consideradas.
        </p>
      )}

      {data.avisos.length > 0 && (
        <ul>
          {data.avisos.map((aviso) => (
            <li key={aviso}>{aviso}</li>
          ))}
        </ul>
      )}

      <div>
        <ProjectStatCard label="Total de Tarefas" value={data.cards.total_tarefas} />
        <ProjectStatCard label="Em Andamento" value={data.cards.em_andamento} />
        <ProjectStatCard label="Concluídas" value={data.cards.concluidas} />
        <ProjectStatCard label="Atrasadas" value={data.cards.atrasadas} />
        <ProjectStatCard
          label="Taxa de Conclusão"
          value={`${data.cards.taxa_conclusao}%`}
        />
      </div>

      <StatusPieChart data={data.grafico_status} />

      <ProjectsTable tarefas={data.tarefas} />
    </div>
  );
}
