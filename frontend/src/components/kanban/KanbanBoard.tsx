import { useMemo, useState, type DragEvent } from "react";
import type { Tarefa } from "../../types/api";
import { CANONICAL_STATUS_ORDER, statusClass } from "../../lib/status";
import { formatPrazo } from "../../lib/date";
import "./KanbanBoard.css";

interface KanbanBoardProps {
  tarefas: Tarefa[];
  onStatusChange?: (tarefa: Tarefa, novoStatus: string) => void;
}

const OUTROS = "Outros";
const COLUMN_ORDER = [...CANONICAL_STATUS_ORDER, OUTROS];

function columnFor(status: string): string {
  return CANONICAL_STATUS_ORDER.includes(status) ? status : OUTROS;
}

export default function KanbanBoard({ tarefas, onStatusChange }: KanbanBoardProps) {
  const [draggingRow, setDraggingRow] = useState<number | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);

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

  const tarefasByRow = useMemo(() => {
    const map = new Map<number, Tarefa>();
    for (const tarefa of tarefas) map.set(tarefa.linha_planilha, tarefa);
    return map;
  }, [tarefas]);

  const draggable = Boolean(onStatusChange);

  function handleDragStart(event: DragEvent<HTMLDivElement>, tarefa: Tarefa) {
    event.dataTransfer.setData("text/plain", String(tarefa.linha_planilha));
    event.dataTransfer.effectAllowed = "move";
    setDraggingRow(tarefa.linha_planilha);
  }

  function handleDragEnd() {
    setDraggingRow(null);
    setDragOverColumn(null);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>, columnStatus: string) {
    event.preventDefault();
    setDragOverColumn(null);
    if (columnStatus === OUTROS) return;

    const linha = Number(event.dataTransfer.getData("text/plain"));
    const tarefa = tarefasByRow.get(linha);
    if (!tarefa || columnFor(tarefa.status) === columnStatus) return;

    onStatusChange?.(tarefa, columnStatus);
  }

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
        <div
          className={`kanban-column ${
            dragOverColumn === column.status ? "kanban-column--drag-over" : ""
          }`}
          key={column.status}
          onDragOver={(event) => {
            if (column.status === OUTROS) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            setDragOverColumn(column.status);
          }}
          onDragLeave={() =>
            setDragOverColumn((current) => (current === column.status ? null : current))
          }
          onDrop={(event) => handleDrop(event, column.status)}
        >
          <div className={`kanban-column-header ${statusClass(column.status)}`}>
            <span className="status-badge">{column.status}</span>
            <span className="kanban-column-count">{column.tarefas.length}</span>
          </div>

          <div className="kanban-column-body">
            {column.tarefas.map((tarefa) => (
              <div
                className={`kanban-card ${
                  draggingRow === tarefa.linha_planilha ? "kanban-card--dragging" : ""
                }`}
                key={tarefa.linha_planilha}
                draggable={draggable}
                onDragStart={(event) => handleDragStart(event, tarefa)}
                onDragEnd={handleDragEnd}
              >
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
