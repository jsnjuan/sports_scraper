"use client";

import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Bar, Doughnut, Scatter, Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
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

const getGradientColor = (
  gender: "male" | "female",
  value: number // 0 to 100
): string => {
  const baseColors = {
    male: { r: 59, g: 130, b: 246 }, // Blue
    female: { r: 236, g: 72, b: 153 }, // Pink
  };

  const color = baseColors[gender];
  const alpha = 0.75;
  const percentage = Math.min(100, Math.max(0, value)) / 100;

  // Linear interpolation: White (255,255,255) to Target Color
  const r = Math.round(255 - (255 - color.r) * percentage);
  const g = Math.round(255 - (255 - color.g) * percentage);
  const b = Math.round(255 - (255 - color.b) * percentage);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

const getSequentialColor = (index: number, total: number) => {
  if (total <= 1) return CHART_COLORS.indigo;
  const ratio = index / (total - 1);
  const h = 230 + ratio * 100; // Gradient from blue-ish to pink-ish
  return `hsla(${h}, 70%, 60%, 0.8)`;
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
  const [activeTab, setActiveTab] = useState<"overview" | "events">("overview");
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<string>("");
  const [data, setData] = useState<any>(null);
  const [overviewData, setOverviewData] = useState<any>(null);
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
    if (activeTab === "events" && selectedEvent) {
      setLoading(true);
      const [slug, dist] = selectedEvent.split("|");
      fetch(`/api/stats?event_slug=${slug}&distance=${encodeURIComponent(dist)}`)
        .then((res) => res.json())
        .then((json) => {
          setData(json);
        })
        .catch((err) => console.error("Error fetching stats:", err))
        .finally(() => setLoading(false));
    } else if (activeTab === "overview" && !overviewData) {
      setLoading(true);
      fetch("/api/overview")
        .then((res) => res.json())
        .then((json) => {
          setOverviewData(json);
        })
        .catch((err) => console.error("Error fetching overview:", err))
        .finally(() => setLoading(false));
    }
  }, [selectedEvent, activeTab]);

  // ── Chart data builders ────────────────────────────────────────────────────

  const buildPyramidData = (dist: string) => {
    const d = overviewData?.[dist];
    if (!d) return null;

    return {
      labels: d.labels,
      datasets: [
        {
          label: "Male",
          data: d.male.map((v: number) => -v), // Negative for left side
          backgroundColor: CHART_COLORS.indigo,
          borderColor: CHART_COLORS.indigoBorder,
          borderWidth: 1,
          borderRadius: { topLeft: 4, bottomLeft: 4 },
        },
        {
          label: "Female",
          data: d.female,
          backgroundColor: CHART_COLORS.pink,
          borderColor: CHART_COLORS.pinkBorder,
          borderWidth: 1,
          borderRadius: { topRight: 4, bottomRight: 4 },
        },
      ],
    };
  };

  const buildComparisonData = (dist: string) => {
    const d = overviewData?.[dist];
    if (!d || !d.races?.length) return null;

    const allLabels = d.labels;
    const datasets: any[] = [];

    d.races.forEach((race: any, idx: number) => {
      const percentage = d.races.length > 1 ? (idx / (d.races.length - 1)) * 100 : 100;
      const maleColor = getGradientColor("male", 30 + (percentage * 0.7)); // Range 30-100 to avoid too much white
      const femaleColor = getGradientColor("female", 30 + (percentage * 0.7));
      const raceName = race.event_slug.replace(/_/g, " ");

      // Male series (Positive Y)
      datasets.push({
        label: `${raceName} (Male)`,
        data: allLabels.map((label: string) => {
          const min = label.replace("m", "");
          return race.male_counts[min] || 0;
        }),
        borderColor: maleColor,
        backgroundColor: "transparent",
        borderWidth: 1.5,
        pointRadius: 0,
        pointHitRadius: 10,
        hoverBorderWidth: 3,
        tension: 0.4,
      });

      // Female series (Negative Y)
      datasets.push({
        label: `${raceName} (Female)`,
        data: allLabels.map((label: string) => {
          const min = label.replace("m", "");
          return -(race.female_counts[min] || 0);
        }),
        borderColor: femaleColor,
        backgroundColor: "transparent",
        borderWidth: 1.5,
        pointRadius: 0,
        pointHitRadius: 10,
        hoverBorderWidth: 3,
        tension: 0.4,
      });
    });

    return {
      labels: allLabels,
      datasets,
    };
  };

  const buildOverviewScatterData = () => {
    if (!overviewData) return null;

    const datasets: any[] = [];
    const distShapes: Record<string, any> = {
      "3K": "circle",
      "5K": "triangle",
      "10K": "rect",
      "21K": "rectRot", // Diamond shape for better visibility
    };

    ["3K", "5K", "10K", "21K"].forEach((dist) => {
      const d = overviewData[dist];
      if (!d?.scatter?.length) return;

      // Male Dataset
      datasets.push({
        label: `${dist} Male`,
        data: d.scatter
          .filter((p: any) => p.gender === "M")
          .map((p: any) => ({ x: p.age, y: p.pace })),
        backgroundColor: CHART_COLORS.indigo,
        pointStyle: distShapes[dist],
        pointRadius: 6, // Increased size
        pointHoverRadius: 9,
      });

      // Female Dataset
      datasets.push({
        label: `${dist} Female`,
        data: d.scatter
          .filter((p: any) => p.gender === "F")
          .map((p: any) => ({ x: p.age, y: p.pace })),
        backgroundColor: CHART_COLORS.pink,
        pointStyle: distShapes[dist],
        pointRadius: 6, // Increased size
        pointHoverRadius: 9,
      });
    });

    return { datasets };
  };

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
    fullWidth,
  }: {
    title: string;
    children: React.ReactNode;
    badge?: string;
    fullWidth?: boolean;
  }) => (
    <div className={`bg-neutral-900/60 p-6 rounded-2xl border border-neutral-800 shadow-xl backdrop-blur-sm flex flex-col gap-4 ${fullWidth ? "md:col-span-2" : ""}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-neutral-200">{title}</h2>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-neutral-800 text-neutral-400 border border-neutral-700">
            {badge}
          </span>
        )}
      </div>
      <div className="h-72">{children}</div>
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
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 pb-6 border-b border-neutral-800/80 gap-6">
          <div className="flex flex-col gap-4">
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
                Race Insights
              </h1>
              <p className="text-neutral-500 mt-1 text-sm">
                Advanced analytics from cross-event race results.
              </p>
            </div>

            {/* Tab Switcher */}
            <div className="flex bg-neutral-900/80 p-1 rounded-xl border border-neutral-800 w-fit">
              <button
                onClick={() => setActiveTab("overview")}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === "overview"
                    ? "bg-indigo-600 text-white shadow-lg"
                    : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                Global Overview
              </button>
              <button
                onClick={() => setActiveTab("events")}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === "events"
                    ? "bg-indigo-600 text-white shadow-lg"
                    : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                Event Analytics
              </button>
            </div>
          </div>

          {activeTab === "events" && (
            <div className="flex flex-col items-start sm:items-end gap-1 animate-in fade-in slide-in-from-right-4 duration-500">
              <label className="text-xs text-neutral-500 mb-0.5 uppercase tracking-wider">
                Select Event
              </label>
              <select
                className="bg-neutral-900 border border-neutral-700 text-white text-sm px-3 py-2 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer min-w-[240px] shadow-inner"
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
          )}
        </header>

        {/* Body */}
        {loading ? (
          <div className="flex h-96 items-center justify-center">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
              <p className="text-neutral-500 animate-pulse text-lg font-medium">
                Processing Data…
              </p>
            </div>
          </div>
        ) : activeTab === "events" ? (
          /* Events Tab Content */
          !data ? (
             <div className="flex h-64 items-center justify-center">
               <p className="text-neutral-600">Select an event to view analytics.</p>
             </div>
          ) : data.error ? (
            <div className="flex h-64 items-center justify-center">
              <p className="text-red-500">{data.error}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in zoom-in-95 duration-500">
              <ChartCard
                title="Finish Time Distribution"
                badge={`${data.finish_records.length} finishers`}
              >
                {histogramData ? (
                  <Bar data={histogramData} options={CHART_OPTS_BASE as any} />
                ) : (
                  <NoData msg="No finish time data available." />
                )}
              </ChartCard>

              <ChartCard
                title="Age Demographics"
                badge={`${data.age_records.length} runners`}
              >
                {ageData ? (
                  <Bar data={ageData} options={CHART_OPTS_BASE as any} />
                ) : (
                  <NoData msg="Age data not available for this event." />
                )}
              </ChartCard>

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
                      },
                    }}
                  />
                ) : (
                  <NoData msg="No gender data available." />
                )}
              </ChartCard>

              <ChartCard title="Pace vs Age">
                {scatterData ? (
                  <Scatter
                    data={scatterData}
                    options={{
                      ...(CHART_OPTS_BASE as any),
                      scales: {
                        x: {
                          ...CHART_OPTS_BASE.scales.x,
                          title: { display: true, text: "Age (years)", color: "#6b7280", font: { size: 11 } },
                        },
                        y: {
                          ...CHART_OPTS_BASE.scales.y,
                          title: { display: true, text: "Pace (min / km)", color: "#6b7280", font: { size: 11 } },
                        },
                      },
                    }}
                  />
                ) : (
                  <NoData msg="Age or pace data not available." />
                )}
              </ChartCard>
            </div>
          )
        ) : (
          /* Overview Tab Content */
          <div className="flex flex-col gap-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* 1. All Finish Times (Race Comparison) */}
            <section className="flex flex-col gap-8">
              <div>
                <h2 className="text-2xl font-bold text-neutral-200 mb-2">Race Comparisons</h2>
                <p className="text-neutral-500 text-sm max-w-2xl">
                  Vertical reflected line plots (Male up, Female down). X-axis shows minutes; Y-axis shows participant volume.
                  Scale is symmetric to allow absolute comparison between genders.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-8">
                {["3K", "5K", "10K", "21K"].map((dist) => {
                  const comparisonData = buildComparisonData(dist);
                  if (!comparisonData) return null;
                  
                  // Calculate symmetric max for absolute comparison
                  const d = overviewData[dist];
                  let maxVal = 0;
                  d.races.forEach((r: any) => {
                    const mMax = Math.max(...(Object.values(r.male_counts) as number[]), 0);
                    const fMax = Math.max(...(Object.values(r.female_counts) as number[]), 0);
                    maxVal = Math.max(maxVal, mMax, fMax);
                  });

                  return (
                    <ChartCard 
                      key={`comp-${dist}`} 
                      title={`${dist} Event Comparison (Vertical Reflection)`} 
                      badge={`${d.races.length} races`}
                      fullWidth
                    >
                      <Line
                        data={comparisonData}
                        options={{
                          ...CHART_OPTS_BASE,
                          indexAxis: "x",
                          interaction: {
                            mode: "nearest",
                            intersect: false,
                          },
                          plugins: {
                            ...CHART_OPTS_BASE.plugins,
                            legend: { display: false },
                            tooltip: {
                              ...CHART_OPTS_BASE.plugins.tooltip,
                              callbacks: {
                                label: (context: any) => {
                                  const val = Math.abs(context.parsed.y);
                                  return `${context.dataset.label}: ${val} runners`;
                                },
                              },
                            },
                          },
                          scales: {
                            ...CHART_OPTS_BASE.scales,
                            x: { ...CHART_OPTS_BASE.scales.x, title: { display: true, text: "Minutes", color: "#4b5563", font: { size: 10 } } },
                            y: { 
                              ...CHART_OPTS_BASE.scales.y, 
                              min: -maxVal,
                              max: maxVal,
                              ticks: { 
                                ...CHART_OPTS_BASE.scales.y.ticks,
                                callback: (v: any) => Math.abs(v) 
                              },
                              title: { display: true, text: "Count", color: "#4b5563", font: { size: 10 } } 
                            },
                          },
                        }}
                      />
                    </ChartCard>
                  );
                })}
              </div>
            </section>

            {/* 2. Performance Pyramid */}
            <section className="flex flex-col gap-8 pt-8 border-t border-neutral-800/50">
              <div>
                <h2 className="text-2xl font-bold text-neutral-200 mb-2">Performance Pyramid</h2>
                <p className="text-neutral-500 text-sm max-w-2xl">
                  Horizontal reflected bars comparing gender distributions. 
                  Scale is symmetric to allow absolute comparison between genders.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {["3K", "5K", "10K", "21K"].map((dist) => {
                  const pyramidData = buildPyramidData(dist);
                  if (!pyramidData) return null;
                  const d = overviewData[dist];
                  const stats = d.stats;
                  
                  // Calculate symmetric max
                  const maxVal = Math.max(...d.male, ...d.female, 0);
                  
                  return (
                    <div key={dist} className="flex flex-col gap-4">
                      <ChartCard 
                        title={`${dist} Finish Distribution`} 
                        badge={`${d.total_participants} runners`}
                      >
                        <Bar
                          data={pyramidData}
                          options={{
                            indexAxis: "y",
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                              x: {
                                min: -maxVal,
                                max: maxVal,
                                ticks: {
                                  color: "#6b7280",
                                  callback: (value: any) => Math.abs(value),
                                },
                                grid: { color: "rgba(255,255,255,0.04)" },
                              },
                              y: {
                                ticks: { color: "#6b7280" },
                                grid: { display: false },
                              },
                            },
                            plugins: {
                              legend: { display: true, position: "top", labels: { color: "#9ca3af", boxWidth: 10 } },
                              tooltip: {
                                callbacks: {
                                  label: (context: any) => {
                                    const label = context.dataset.label || "";
                                    const value = Math.abs(context.parsed.x);
                                    return `${label}: ${value} participants`;
                                  },
                                },
                              },
                            },
                          }}
                        />
                      </ChartCard>

                      {/* Facts Card */}
                      <div className="bg-neutral-900/40 border border-neutral-800/60 p-5 rounded-2xl flex flex-col gap-4">
                        <h4 className="text-xs font-bold text-neutral-500 uppercase tracking-widest">Key Facts · {dist}</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex flex-col">
                            <span className="text-xs text-neutral-500">Fastest (M/F)</span>
                            <span className="text-lg font-mono text-indigo-400">
                              {stats.fastest_male}m <span className="text-neutral-700 mx-1">/</span> <span className="text-pink-400">{stats.fastest_female}m</span>
                            </span>
                          </div>
                          <div className="flex flex-col">
                            <span className="text-xs text-neutral-500">Median (M/F)</span>
                            <span className="text-lg font-mono text-indigo-400">
                              {stats.median_male}m <span className="text-neutral-700 mx-1">/</span> <span className="text-pink-400">{stats.median_female}m</span>
                            </span>
                          </div>
                        </div>
                        {stats.median_male && stats.median_female && (
                          <p className="text-sm text-neutral-400 italic">
                            The gender performance gap is approximately {Math.abs(stats.median_male - stats.median_female)} minutes at the median level.
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* 3. Global Performance Trends (Scatter) */}
            <section className="flex flex-col gap-8 pt-8 border-t border-neutral-800/50">
              <div>
                <h2 className="text-2xl font-bold text-neutral-200 mb-2">Global Performance Trends</h2>
                <p className="text-neutral-500 text-sm max-w-2xl">
                  Aggregated pace vs age across all distances. 
                  Identify performance correlations between different age groups and race lengths.
                </p>
              </div>
              <ChartCard title="Pace vs Age (All Distances)" fullWidth>
                {overviewData ? (
                  <Scatter
                    data={buildOverviewScatterData() as any}
                    options={{
                      ...CHART_OPTS_BASE,
                      plugins: {
                        ...CHART_OPTS_BASE.plugins,
                        legend: { 
                          display: true, 
                          position: "bottom",
                          labels: { color: "#9ca3af", usePointStyle: true, padding: 20 }
                        },
                      },
                      scales: {
                        x: {
                          ...CHART_OPTS_BASE.scales.x,
                          title: { display: true, text: "Age (years)", color: "#6b7280" },
                        },
                        y: {
                          ...CHART_OPTS_BASE.scales.y,
                          title: { display: true, text: "Pace (min/km)", color: "#6b7280" },
                        },
                      },
                    }}
                  />
                ) : (
                  <NoData msg="No scatter data available." />
                )}
              </ChartCard>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
