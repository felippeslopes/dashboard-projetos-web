import { useMemo } from "react";
import type { Tarefa } from "../../types/api";
import { CANONICAL_STATUS_ORDER, statusClass } from "../../lib/status";
import { formatPrazo } from "../../lib/date";
import "./KanbanBoard.css";

interface KanbanBoardProps {
  tarefas: Tarefa[];
}

const OUTROS = "Outros";
const COLUMN_ORDER = [...CANONICAL_STATUS_ORDER, OUTROS];

function columnFor(status: string): string {
  return CANONICAL_STATUS_ORDER.includes(status) ? status : OUTROS;
}

export default function KanbanBoard({ tarefas }: KanbanBoardProps) {
  const columns = useMemo(() => {
    const map = new Map<string, Tarefa[]>();
    for (const column of COLUMN_ORDER) map.set(column, []);

    for (const tarefa of tarefas) {
      map.get(columnFor(tarefa.status))!.push(tarefa);
    }

    return COLUMN_ORDER.map((column) => ({
      status: column,
      tarefas: map.get(column) ?? [],
    })).filter((column) => column.tarefas.length > 0 || column.status !== OUTROS);
  }, [tarefas]);

  if (tarefas.length === 0) {
    return (
      <div className="card table-card">
        <p className="projects-table-empty">Nenhuma tarefa encontrada.</p>
      </div>
    );
  }

  return (
    <div className="kanban-board">
      {columns.map((column) => (
        <div className="kanban-column" key={column.status}>
          <div className={`kanban-column-header ${statusClass(column.status)}`}>
            <span className="status-badge">{column.status}</span>
            <span className="kanban-column-count">{column.tarefas.length}</span>
          </div>

          <div className="kanban-column-body">
            {column.tarefas.map((tarefa) => (
              <div className="kanban-card" key={tarefa.linha_planilha}>
                <p className="kanban-card-title">{tarefa.nome}</p>
                <p className="kanban-card-meta">{tarefa.projeto}</p>
                <div className="kanban-card-footer">
                  <span>{tarefa.responsavel || "—"}</span>
                  <span className="tabular-nums">{formatPrazo(tarefa.prazo)}</span>
                </div>
              </div>
            ))}
            {column.tarefas.length === 0 && (
              <p className="kanban-column-empty">Sem tarefas</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
