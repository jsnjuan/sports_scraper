"use client";

import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Bar, Doughnut, Scatter } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const CHART_COLORS = {
  indigo: "rgba(99, 102, 241, 0.75)",
  indigoBorder: "rgba(99, 102, 241, 1)",
  pink: "rgba(236, 72, 153, 0.75)",
  pinkBorder: "rgba(236, 72, 153, 1)",
  blue: "rgba(59, 130, 246, 0.75)",
  purple: "rgba(168, 85, 247, 0.75)",
  emerald: "rgba(16, 185, 129, 0.55)",
};

const CHART_OPTS_BASE = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: "rgba(15,15,20,0.92)",
      titleColor: "#e5e7eb",
      bodyColor: "#9ca3af",
      borderColor: "rgba(99,102,241,0.4)",
      borderWidth: 1,
    },
  },
  scales: {
    x: {
      ticks: { color: "#6b7280" },
      grid: { color: "rgba(255,255,255,0.04)" },
    },
    y: {
      ticks: { color: "#6b7280" },
      grid: { color: "rgba(255,255,255,0.04)" },
    },
  },
};

export default function Home() {
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<string>("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/events")
      .then((res) => res.json())
      .then((json) => {
        setEvents(json);
        if (json.length > 0) {
          setSelectedEvent(`${json[0].event_slug}|${json[0].distance}`);
        }
      });
  }, []);

  useEffect(() => {
    if (!selectedEvent) return;
    setLoading(true);
    const [slug, dist] = selectedEvent.split("|");
    fetch(`/api/stats?event_slug=${slug}&distance=${encodeURIComponent(dist)}`)
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      });
  }, [selectedEvent]);

  // ── Chart data builders ────────────────────────────────────────────────────

  const histogramData = (() => {
    if (!data?.finish_records?.length) return null;
    const buckets: Record<string, number> = {};
    data.finish_records.forEach((r: any) => {
      const mins = Math.floor(r.finish_time_seconds / 300) * 5;
      const label = `${mins}m`;
      buckets[label] = (buckets[label] || 0) + 1;
    });
    const sorted = Object.entries(buckets).sort(
      (a, b) => parseInt(a[0]) - parseInt(b[0])
    );
    return {
      labels: sorted.map(([k]) => k),
      datasets: [
        {
          label: "Runners",
          data: sorted.map(([, v]) => v),
          backgroundColor: CHART_COLORS.indigo,
          borderColor: CHART_COLORS.indigoBorder,
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    };
  })();

  const ageData = (() => {
    if (!data?.age_records?.length) return null;
    const buckets: Record<string, number> = {};
    data.age_records.forEach((r: any) => {
      const group = `${Math.floor(r.age / 5) * 5}s`;
      buckets[group] = (buckets[group] || 0) + 1;
    });
    const sorted = Object.entries(buckets).sort(
      (a, b) => parseInt(a[0]) - parseInt(b[0])
    );
    return {
      labels: sorted.map(([k]) => k),
      datasets: [
        {
          label: "Runners",
          data: sorted.map(([, v]) => v),
          backgroundColor: CHART_COLORS.pink,
          borderColor: CHART_COLORS.pinkBorder,
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    };
  })();

  const genderData = (() => {
    if (!data?.gender_counts) return null;
    const labels = Object.keys(data.gender_counts);
    const values = Object.values(data.gender_counts) as number[];
    if (!labels.length) return null;
    return {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: [CHART_COLORS.blue, CHART_COLORS.pink, CHART_COLORS.purple],
          borderWidth: 0,
          hoverOffset: 6,
        },
      ],
    };
  })();

  const scatterData = (() => {
    if (!data?.scatter_records?.length) return null;
    return {
      datasets: [
        {
          label: "Runners",
          data: data.scatter_records.map((r: any) => ({
            x: r.age,
            y: parseFloat((r.pace_seconds / 60).toFixed(2)),
          })),
          backgroundColor: CHART_COLORS.emerald,
          pointRadius: 3,
          pointHoverRadius: 5,
        },
      ],
    };
  })();

  // ── Helpers ────────────────────────────────────────────────────────────────

  const ChartCard = ({
    title,
    children,
    badge,
  }: {
    title: string;
    children: React.ReactNode;
    badge?: string;
  }) => (
    <div className="bg-neutral-900/60 p-6 rounded-2xl border border-neutral-800 shadow-xl backdrop-blur-sm flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-neutral-200">{title}</h2>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-800 text-neutral-400 border border-neutral-700">
            {badge}
          </span>
        )}
      </div>
      <div className="h-60">{children}</div>
    </div>
  );

  const NoData = ({ msg }: { msg: string }) => (
    <div className="h-full flex items-center justify-center">
      <p className="text-neutral-600 text-sm">{msg}</p>
    </div>
  );

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <main
      className="min-h-screen text-white p-8 font-sans"
      style={{
        background:
          "radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.12) 0%, transparent 70%), #0a0a0f",
      }}
    >
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 pb-6 border-b border-neutral-800/80 gap-4">
          <div>
            <h1
              className="text-3xl sm:text-4xl font-extrabold tracking-tight"
              style={{
                background:
                  "linear-gradient(135deg, #818cf8 0%, #a78bfa 40%, #f472b6 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Race Analytics
            </h1>
            <p className="text-neutral-500 mt-1 text-sm">
              Visual distributions from your scraped race results.
            </p>
          </div>
          <div className="flex flex-col items-start sm:items-end gap-1">
            <label className="text-xs text-neutral-500 mb-0.5 uppercase tracking-wider">
              Select Event
            </label>
            <select
              className="bg-neutral-900 border border-neutral-700 text-white text-sm px-3 py-2 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer min-w-[240px]"
              value={selectedEvent}
              onChange={(e) => setSelectedEvent(e.target.value)}
            >
              {events.map((e, idx) => (
                <option key={idx} value={`${e.event_slug}|${e.distance}`}>
                  {e.event_slug.replace(/_/g, " ")} · {e.distance}
                </option>
              ))}
            </select>
          </div>
        </header>

        {/* Body */}
        {!data && !loading ? (
          <div className="flex h-64 items-center justify-center">
            <p className="text-neutral-600">Select an event above.</p>
          </div>
        ) : loading ? (
          <div className="flex h-64 items-center justify-center">
            <p className="text-neutral-500 animate-pulse text-lg">
              Loading Analytics…
            </p>
          </div>
        ) : data?.error ? (
          <div className="flex h-64 items-center justify-center">
            <p className="text-red-500">{data.error}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 1. Finish Time Histogram */}
            <ChartCard
              title="Finish Time Distribution"
              badge={histogramData ? `${data.finish_records.length} finishers` : undefined}
            >
              {histogramData ? (
                <Bar data={histogramData} options={CHART_OPTS_BASE as any} />
              ) : (
                <NoData msg="No finish time data available." />
              )}
            </ChartCard>

            {/* 2. Age Demographics */}
            <ChartCard
              title="Age Demographics"
              badge={ageData ? `${data.age_records.length} runners` : undefined}
            >
              {ageData ? (
                <Bar data={ageData} options={CHART_OPTS_BASE as any} />
              ) : (
                <NoData msg="Age data not available for this event." />
              )}
            </ChartCard>

            {/* 3. Gender Split */}
            <ChartCard title="Gender Split">
              {genderData ? (
                <Doughnut
                  data={genderData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: true,
                        position: "bottom",
                        labels: { color: "#9ca3af", boxWidth: 12, padding: 16 },
                      },
                      tooltip: {
                        backgroundColor: "rgba(15,15,20,0.92)",
                        titleColor: "#e5e7eb",
                        bodyColor: "#9ca3af",
                      },
                    },
                  }}
                />
              ) : (
                <NoData msg="No gender data available." />
              )}
            </ChartCard>

            {/* 4. Pace vs Age Scatter */}
            <ChartCard title="Pace vs Age">
              {scatterData ? (
                <Scatter
                  data={scatterData}
                  options={{
                    ...(CHART_OPTS_BASE as any),
                    scales: {
                      x: {
                        ...CHART_OPTS_BASE.scales.x,
                        title: {
                          display: true,
                          text: "Age (years)",
                          color: "#6b7280",
                          font: { size: 11 },
                        },
                      },
                      y: {
                        ...CHART_OPTS_BASE.scales.y,
                        title: {
                          display: true,
                          text: "Pace (min / km)",
                          color: "#6b7280",
                          font: { size: 11 },
                        },
                      },
                    },
                  }}
                />
              ) : (
                <NoData msg="Age or pace data not available for this event." />
              )}
            </ChartCard>
          </div>
        )}
      </div>
    </main>
  );
}
