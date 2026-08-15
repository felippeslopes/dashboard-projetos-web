import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { StatusBreakdown } from "../../types/api";
import { STATUS_CHART_COLORS } from "../../lib/status";
import { useTheme } from "../../contexts/ThemeContext";
import "./StatusPieChart.css";

interface StatusPieChartProps {
  data: StatusBreakdown[];
}

export default function StatusPieChart({ data }: StatusPieChartProps) {
  const { theme } = useTheme();
  const colors = STATUS_CHART_COLORS[theme];

  return (
    <div className="card chart-card">
      <h2>Tarefas por status</h2>
      {data.length === 0 ? (
        <p className="chart-empty">Sem dados suficientes para o gráfico de status.</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={data}
                dataKey="quantidade"
                nameKey="status"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={2}
                stroke="var(--surface)"
                strokeWidth={2}
              >
                {data.map((entry) => (
                  <Cell
                    key={entry.status}
                    fill={colors[entry.status] ?? colors.Outros}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--rule)",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  color: "var(--ink)",
                }}
                itemStyle={{ color: "var(--ink)" }}
              />
            </PieChart>
          </ResponsiveContainer>
          <ul className="chart-legend">
            {data.map((entry) => (
              <li key={entry.status}>
                <span
                  className="chart-legend-swatch"
                  style={{ background: colors[entry.status] ?? colors.Outros }}
                />
                {entry.status}: {entry.quantidade}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
