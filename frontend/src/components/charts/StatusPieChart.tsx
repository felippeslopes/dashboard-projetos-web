import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { StatusBreakdown } from "../../types/api";

interface StatusPieChartProps {
  data: StatusBreakdown[];
}

const COLORS: Record<string, string> = {
  Planejado: "#8884d8",
  "Em andamento": "#3b82f6",
  Concluído: "#22c55e",
  Atrasado: "#f97316",
  Cancelado: "#6b7280",
  Outros: "#a3a3a3",
};

export default function StatusPieChart({ data }: StatusPieChartProps) {
  if (data.length === 0) {
    return <p>Sem dados suficientes para o gráfico de status.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          dataKey="quantidade"
          nameKey="status"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label={({ name, value }) => `${name}: ${value}`}
        >
          {data.map((entry) => (
            <Cell key={entry.status} fill={COLORS[entry.status] ?? "#a3a3a3"} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
