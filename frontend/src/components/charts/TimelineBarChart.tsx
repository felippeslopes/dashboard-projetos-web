import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PeriodoBreakdown } from "../../types/api";
import { useTheme } from "../../contexts/ThemeContext";

interface TimelineBarChartProps {
  data: PeriodoBreakdown[];
}

const COLORS = {
  light: { bar: "#4a3aa7", axis: "#5b6360", grid: "#dde3e0" },
  dark: { bar: "#9085e9", axis: "#a9b3b0", grid: "#2c3436" },
};

export default function TimelineBarChart({ data }: TimelineBarChartProps) {
  const { theme } = useTheme();
  const colors = COLORS[theme];

  return (
    <div className="card chart-card">
      <h2>Tarefas por prazo (mês)</h2>
      {data.length === 0 ? (
        <p className="chart-empty">Nenhuma tarefa com prazo preenchido.</p>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid vertical={false} stroke={colors.grid} />
            <XAxis
              dataKey="periodo"
              tick={{ fill: colors.axis, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: colors.axis, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={28}
            />
            <Tooltip
              formatter={(value) => [String(value), "Tarefas"]}
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--rule)",
                borderRadius: "8px",
                fontSize: "0.85rem",
                color: "var(--ink)",
              }}
              itemStyle={{ color: "var(--ink)" }}
              cursor={{ fill: "var(--paper)" }}
            />
            <Bar dataKey="total" fill={colors.bar} radius={[4, 4, 0, 0]} barSize={28} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
