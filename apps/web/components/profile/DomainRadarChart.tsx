"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

export interface DomainScore {
  domain: string;
  label: string;
  score: number; // 0–100
  color: string;
}

interface DomainRadarChartProps {
  scores: DomainScore[];
  size?: number;
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: DomainScore }[];
}) => {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload;
  if (!item) return null;
  return (
    <div className="rounded-md border border-border bg-card px-3 py-2 text-sm shadow-sm">
      <p className="font-semibold text-foreground">{item.label}</p>
      <p className="text-muted-foreground">Score: {item.score}/100</p>
    </div>
  );
};

/**
 * DomainRadarChart
 * Renders a Recharts radar chart for the 6 ICF Human Development domains.
 * Scores are 0–100 normalised.
 */
export function DomainRadarChart({ scores, size = 320 }: DomainRadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={size}>
      <RadarChart
        data={scores}
        margin={{ top: 10, right: 20, bottom: 10, left: 20 }}
      >
        <PolarGrid stroke="hsl(var(--border))" />
        <PolarAngleAxis
          dataKey="label"
          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
          tickCount={5}
        />
        <Radar
          name="Profile"
          dataKey="score"
          stroke="hsl(var(--primary))"
          fill="hsl(var(--primary))"
          fillOpacity={0.2}
          strokeWidth={2}
          dot={{ r: 4, fill: "hsl(var(--primary))" }}
        />
        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
