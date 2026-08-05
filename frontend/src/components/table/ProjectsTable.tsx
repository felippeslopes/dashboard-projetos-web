import type { Tarefa } from "../../types/api";

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
    return <p>Nenhuma tarefa encontrada.</p>;
  }

  return (
    <table>
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
            <td>{tarefa.status}</td>
            <td>{tarefa.responsavel}</td>
            <td>{formatPrazo(tarefa.prazo)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
