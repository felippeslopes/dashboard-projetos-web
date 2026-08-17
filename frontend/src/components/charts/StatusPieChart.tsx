import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { PieLabelRenderProps } from "recharts";
import type { StatusBreakdown } from "../../types/api";
import { STATUS_CHART_COLORS } from "../../lib/status";
import { useTheme } from "../../contexts/ThemeContext";
import "./StatusPieChart.css";

interface StatusPieChartProps {
  data: StatusBreakdown[];
}

const RADIAN = Math.PI / 180;

function renderSliceLabel(props: PieLabelRenderProps) {
  const cx = Number(props.cx) || 0;
  const cy = Number(props.cy) || 0;
  const midAngle = props.midAngle ?? 0;
  const outerRadius = Number(props.outerRadius) || 0;
  const percent = props.percent ?? 0;
  const value = Number(props.value) || 0;
  const name = String(props.name ?? "");
  const radius = outerRadius + 18;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  const anchor = x > cx ? "start" : "end";

  return (
    <text x={x} y={y} textAnchor={anchor} className="pie-label">
      <tspan x={x} dy="-1em" className="pie-label-name">
        {name}
      </tspan>
      <tspan x={x} dy="1.15em" className="pie-label-count">
        {value} tarefa{value === 1 ? "" : "s"}
      </tspan>
      <tspan x={x} dy="1.15em" className="pie-label-percent">
        {Math.round(percent * 100)}%
      </tspan>
    </text>
  );
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
        <div className="pie-chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 24, right: 56, bottom: 24, left: 56 }}>
              <Pie
                data={data}
                dataKey="quantidade"
                nameKey="status"
                cx="50%"
                cy="50%"
                innerRadius="58%"
                outerRadius="82%"
                paddingAngle={2}
                stroke="var(--surface)"
                strokeWidth={2}
                label={renderSliceLabel}
                labelLine={false}
                isAnimationActive={false}
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
        </div>
      )}
    </div>
  );
}
