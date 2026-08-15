import type { Tarefa } from "../../types/api";
import { statusClass } from "../../lib/status";
import "./ProjectsTable.css";

interface ProjectsTableProps {
  tarefas: Tarefa[];
}

function formatPrazo(prazo: string | null): string {
  if (!prazo) return "—";
  const [year, month, day] = prazo.split("-");
  return `${day}/${month}/${year}`;
}

export default function ProjectsTable({ tarefas }: ProjectsTableProps) {
  if (tarefas.length === 0) {
    return (
      <div className="card table-card">
        <p className="projects-table-empty">Nenhuma tarefa encontrada.</p>
      </div>
    );
  }

  return (
    <div className="card table-card">
      <div className="table-scroll">
        <table className="projects-table">
          <thead>
            <tr>
              <th>Projeto</th>
              <th>Tarefa</th>
              <th>Status</th>
              <th>Responsável</th>
              <th>Prazo</th>
            </tr>
          </thead>
          <tbody>
            {tarefas.map((tarefa) => (
              <tr key={tarefa.linha_planilha}>
                <td>{tarefa.projeto}</td>
                <td>{tarefa.nome}</td>
                <td>
                  <span className={`status-badge ${statusClass(tarefa.status)}`}>
                    {tarefa.status}
                  </span>
                </td>
                <td>{tarefa.responsavel}</td>
                <td className="tabular-nums">{formatPrazo(tarefa.prazo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
