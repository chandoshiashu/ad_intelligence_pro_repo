
"use client";

import { useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BrainCircuit,
  Check,
  ChevronDown,
  CircleHelp,
  Command,
  Download,
  Eye,
  FileSearch,
  Globe,
  LayoutDashboard,
  Lightbulb,
  Menu,
  MessageSquareText,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  X,
  Zap,
} from "lucide-react";

type NavItem = {
  label: string;
  icon: typeof LayoutDashboard;
};

const navItems: NavItem[] = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Competitor Analysis", icon: Target },
  { label: "Ad Explorer", icon: FileSearch },
  { label: "Creative Intelligence", icon: BrainCircuit },
  { label: "Opportunities", icon: Lightbulb },
];

const performance = [
  { month: "May", value: 34 },
  { month: "Jun", value: 47 },
  { month: "Jul", value: 41 },
  { month: "Aug", value: 62 },
  { month: "Sep", value: 54 },
  { month: "Oct", value: 77 },
  { month: "Nov", value: 69 },
  { month: "Dec", value: 88 },
];

const creatives = [
  {
    brand: "Zomato",
    initials: "Z",
    color: "#E94B55",
    type: "Offer-led",
    headline: "Your next favourite meal is waiting.",
    description:
      "Discount-first messaging with urgency and a direct purchase CTA.",
    tags: ["Discounts", "Urgency", "Food"],
    strength: "Strong offer emphasis",
  },
  {
    brand: "Swiggy",
    initials: "S",
    color: "#F4A340",
    type: "Convenience-led",
    headline: "Good food. Delivered to your door.",
    description:
      "Convenience and everyday use cases are central to the message.",
    tags: ["Convenience", "Lifestyle", "Delivery"],
    strength: "Everyday positioning",
  },
  {
    brand: "Blinkit",
    initials: "B",
    color: "#E7D83F",
    type: "Speed-led",
    headline: "Everything you need, right now.",
    description:
      "Fast fulfillment and immediate availability drive the proposition.",
    tags: ["Speed", "Convenience", "Essentials"],
    strength: "Speed positioning",
  },
];

const themes = [
  { name: "Discounts & offers", value: 82, color: "#FF7138" },
  { name: "Convenience", value: 67, color: "#F4AB77" },
  { name: "Lifestyle & emotion", value: 51, color: "#A98BFF" },
  { name: "Speed & delivery", value: 43, color: "#55D6A5" },
  { name: "Product discovery", value: 29, color: "#6EA8FE" },
];

export default function Home() {
  const [active, setActive] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [company, setCompany] = useState("Zomato");
  const [competitor, setCompetitor] = useState("Swiggy");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [apiResult, setApiResult] = useState<unknown>(null);

  async function analyzeCompetitors() {
    if (!company.trim() || !competitor.trim()) {
      setNotice("Enter both company names to start an analysis.");
      return;
    }

    setLoading(true);
    setNotice("");
    setApiResult(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company: company.trim(),
          competitor: competitor.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : `Analysis request failed (${response.status}).`
        );
      }

      setApiResult(data);
      setNotice("Analysis completed. The API response is shown below.");
    } catch (error) {
      setNotice(
        error instanceof Error
          ? `Could not complete analysis: ${error.message}`
          : "Could not connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  const filteredCreatives = creatives.filter((ad) =>
    `${ad.brand} ${ad.headline} ${ad.type} ${ad.tags.join(" ")}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  return (
    <main className="min-h-screen bg-[#101114] text-[#F4F2EF]">
      <style jsx global>{`
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          background: #101114;
        }

        button,
        input {
          font: inherit;
        }

        button {
          cursor: pointer;
        }

        .panel {
          background: #17181d;
          border: 1px solid #292a31;
          border-radius: 16px;
        }

        .muted {
          color: #92939d;
        }

        .eyebrow {
          font-size: 11px;
          letter-spacing: 1.3px;
          font-weight: 700;
          text-transform: uppercase;
          color: #92939d;
        }

        .nav-link {
          display: flex;
          align-items: center;
          gap: 11px;
          width: 100%;
          padding: 11px 12px;
          border-radius: 9px;
          color: #92939d;
          text-align: left;
          font-size: 13px;
          transition: background 150ms, color 150ms;
        }

        .nav-link:hover {
          background: #222329;
          color: #f4f2ef;
        }

        .nav-link.active {
          color: #ff9a70;
          background: #302019;
        }

        .primary-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          border-radius: 9px;
          background: #ff7138;
          padding: 11px 15px;
          color: #15110f;
          font-size: 12px;
          font-weight: 800;
          transition: background 150ms, transform 150ms;
        }

        .primary-btn:hover {
          background: #ff8b5b;
          transform: translateY(-1px);
        }

        .field {
          width: 100%;
          min-width: 0;
          border: 1px solid #35363e;
          border-radius: 9px;
          background: #101114;
          padding: 11px 12px;
          color: #f4f2ef;
          outline: none;
          font-size: 13px;
        }

        .field:focus {
          border-color: #ff7138;
          box-shadow: 0 0 0 3px #ff71381b;
        }

        .section-title {
          font-size: 14px;
          font-weight: 700;
          letter-spacing: -0.2px;
        }

        .metric-value {
          font-size: clamp(23px, 2vw, 30px);
          font-weight: 750;
          letter-spacing: -1px;
          line-height: 1.2;
        }

        .chart-bar {
          transition: opacity 150ms;
        }

        .chart-bar:hover {
          opacity: 0.72;
        }

        @media (max-width: 767px) {
          .mobile-sidebar {
            position: fixed;
            inset: 0 auto 0 0;
            z-index: 50;
            width: 260px;
            background: #141519;
            box-shadow: 20px 0 70px #0008;
          }
        }
      `}</style>

      <div className="flex min-h-screen">
        {sidebarOpen && (
          <button
            aria-label="Close navigation"
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/60 md:hidden"
          />
        )}

        {/* SIDEBAR */}
        <aside
          className={`${
            sidebarOpen ? "mobile-sidebar block" : "hidden"
          } w-[248px] shrink-0 border-r border-[#292a31] bg-[#141519] p-5 md:sticky md:top-0 md:flex md:h-screen md:flex-col`}
        >
          <div className="mb-10 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#FF7138] text-[#15110f]">
                <Activity size={22} strokeWidth={2.5} />
              </div>
              <div>
                <div className="text-[15px] font-extrabold tracking-tight">
                  ad<span className="text-[#FF7138]">intelligence</span>
                </div>
                <div className="mt-1 text-[10px] tracking-[1.5px] text-[#92939D]">
                  COMPETITIVE INTEL
                </div>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-[#92939D] md:hidden"
              aria-label="Close menu"
            >
              <X size={18} />
            </button>
          </div>

          <div className="mb-3 px-3 eyebrow">Workspace</div>
          <div className="mb-8 space-y-1">
            {navItems.map(({ label, icon: Icon }) => (
              <button
                key={label}
                onClick={() => {
                  setActive(label);
                  setSidebarOpen(false);
                }}
                className={`nav-link ${active === label ? "active" : ""}`}
              >
                <Icon size={17} />
                <span>{label}</span>
                {label === "Opportunities" && (
                  <span className="ml-auto rounded-md bg-[#FF7138] px-1.5 py-0.5 text-[10px] font-bold text-[#15110f]">
                    3
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="mb-3 px-3 eyebrow">Manage</div>
          <div className="space-y-1">
            <button
              onClick={() => setActive("Data Sources")}
              className={`nav-link ${active === "Data Sources" ? "active" : ""}`}
            >
              <Globe size={17} />
              Data Sources
            </button>
            <button
              onClick={() => setActive("Settings")}
              className={`nav-link ${active === "Settings" ? "active" : ""}`}
            >
              <Settings2 size={17} />
              Settings
            </button>
          </div>

          <div className="mt-auto">
            <div className="mb-5 rounded-xl border border-[#393029] bg-[#211a17] p-4">
              <div className="mb-3 flex items-center gap-2 text-[#FFAB78]">
                <Sparkles size={17} />
                <span className="text-xs font-bold">Intelligence Pro</span>
              </div>
              <p className="mb-4 text-xs leading-5 text-[#B4ADA8]">
                Turn competitor ad activity into your next strategic advantage.
              </p>
              <button
                onClick={() => setActive("Opportunities")}
                className="flex items-center gap-2 text-xs font-bold text-[#FFAB78]"
              >
                Explore insights <ArrowRight size={14} />
              </button>
            </div>

            <div className="flex items-center gap-3 border-t border-[#292a31] pt-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#34343d] text-sm font-bold">
                A
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-xs font-semibold">Workspace</div>
                <div className="mt-1 text-[10px] text-[#92939D]">
                  Local development
                </div>
              </div>
              <ChevronDown size={15} className="text-[#92939D]" />
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <section className="min-w-0 flex-1">
          {/* TOP BAR */}
          <header className="sticky top-0 z-30 flex h-[68px] items-center justify-between border-b border-[#292a31] bg-[#101114]/95 px-4 backdrop-blur-xl sm:px-7">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="text-[#92939D] md:hidden"
                aria-label="Open navigation"
              >
                <Menu size={21} />
              </button>
              <div className="hidden items-center gap-2 text-xs text-[#92939D] sm:flex">
                <span>Workspace</span>
                <span>/</span>
                <span className="text-[#F4F2EF]">{active}</span>
              </div>
              <div className="text-sm font-semibold sm:hidden">{active}</div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-lg border border-[#292a31] bg-[#17181d] px-3 py-2 sm:flex">
                <Command size={14} className="text-[#92939D]" />
                <span className="text-xs text-[#92939D]">
                  Competitive workspace
                </span>
              </div>
              <button
                aria-label="Help"
                className="hidden text-[#92939D] hover:text-white sm:block"
              >
                <CircleHelp size={18} />
              </button>
              <button
                aria-label="Notifications"
                className="relative text-[#92939D] hover:text-white"
              >
                <Bell size={18} />
                <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-[#FF7138]" />
              </button>
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#574032] bg-[#302019] text-xs font-bold text-[#FFAB78]">
                A
              </div>
            </div>
          </header>

          <div className="mx-auto max-w-[1600px] p-4 sm:p-7">
            {/* HEADING */}
            <div className="mb-7 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
              <div>
                <div className="mb-3 flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#55D6A5]" />
                  <span className="eyebrow">Market intelligence workspace</span>
                </div>
                <h1 className="text-2xl font-bold tracking-tight sm:text-[32px]">
                  See what your competitors <span className="text-[#FF7138]">are doing.</span>
                </h1>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-[#92939D]">
                  Explore ad creatives, decode messaging strategies, and
                  discover potential opportunities your competitors may be
                  overlooking.
                </p>
              </div>
              <button
                onClick={() =>
                  document
                    .getElementById("analysis-form")
                    ?.scrollIntoView({ behavior: "smooth", block: "center" })
                }
                className="primary-btn self-start lg:self-auto"
              >
                <Plus size={16} /> New analysis
              </button>
            </div>

            {/* ANALYSIS FORM */}
            <div id="analysis-form" className="panel mb-7 p-5 sm:p-6">
              <div className="mb-5 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#302019] text-[#FF7138]">
                  <Zap size={20} />
                </div>
                <div>
                  <h2 className="text-sm font-bold">Start a competitor analysis</h2>
                  <p className="mt-1 text-xs text-[#92939D]">
                    Compare brands using your connected analysis API.
                  </p>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr_auto] md:items-end">
                <label className="block">
                  <span className="mb-2 block text-xs font-semibold text-[#C7C5C9]">
                    Your company
                  </span>
                  <input
                    className="field"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="e.g. Zomato"
                  />
                </label>

                <div className="hidden pb-3 text-[#92939D] md:block">
                  <ArrowRight size={18} />
                </div>

                <label className="block">
                  <span className="mb-2 block text-xs font-semibold text-[#C7C5C9]">
                    Competitor
                  </span>
                  <input
                    className="field"
                    value={competitor}
                    onChange={(e) => setCompetitor(e.target.value)}
                    placeholder="e.g. Swiggy"
                  />
                </label>

                <button
                  onClick={analyzeCompetitors}
                  disabled={loading}
                  className="primary-btn min-h-[42px] disabled:cursor-wait disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <Activity size={15} className="animate-pulse" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      Analyze <ArrowRight size={15} />
                    </>
                  )}
                </button>
              </div>

              {notice && (
                <div
                  role="status"
                  className={`mt-4 rounded-lg border p-3 text-xs leading-5 ${
                    notice.startsWith("Analysis completed")
                      ? "border-[#55D6A5]/30 bg-[#55D6A5]/5 text-[#80E7BB]"
                      : "border-[#FF7138]/30 bg-[#FF7138]/5 text-[#FFAB78]"
                  }`}
                >
                  {notice}
                </div>
              )}

              {apiResult !== null && (
                <div className="mt-4">
                  <div className="mb-2 text-xs font-bold">Backend response</div>
                  <pre className="max-h-80 overflow-auto rounded-lg border border-[#292a31] bg-[#101114] p-4 text-xs leading-5 text-[#C7C5C9]">
                    {JSON.stringify(apiResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>

            {/* DEMO DATA NOTICE */}
            <div className="mb-5 flex items-start gap-3 rounded-xl border border-[#4a3c2b] bg-[#211b16] p-4">
              <Eye size={17} className="mt-0.5 shrink-0 text-[#F4C56A]" />
              <div>
                <div className="text-xs font-bold text-[#F4C56A]">
                  Dashboard preview · illustrative data
                </div>
                <p className="mt-1 text-xs leading-5 text-[#B8AEA1]">
                  Charts and metrics below are sample UI data, not live ad spend,
                  CTR, conversions, or measured campaign performance. Run an
                  analysis above to see the actual response from your backend.
                </p>
              </div>
            </div>

            {/* METRICS */}
            <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                {
                  title: "Ads in preview",
                  value: "1,284",
                  change: "Sample dataset",
                  icon: Eye,
                  color: "#FF7138",
                  up: true,
                },
                {
                  title: "Creative themes",
                  value: "18",
                  change: "Illustrative count",
                  icon: BrainCircuit,
                  color: "#A98BFF",
                  up: true,
                },
                {
                  title: "Brands tracked",
                  value: "12",
                  change: "Demo workspace",
                  icon: Target,
                  color: "#55D6A5",
                  up: true,
                },
                {
                  title: "Potential opportunities",
                  value: "06",
                  change: "Hypotheses to validate",
                  icon: Lightbulb,
                  color: "#F4C56A",
                  up: false,
                },
              ].map((metric) => {
                const Icon = metric.icon;
                return (
                  <div key={metric.title} className="panel p-5">
                    <div className="mb-5 flex items-center justify-between">
                      <span className="text-xs text-[#92939D]">{metric.title}</span>
                      <div
                        className="flex h-9 w-9 items-center justify-center rounded-lg"
                        style={{
                          background: `${metric.color}18`,
                          color: metric.color,
                        }}
                      >
                        <Icon size={18} />
                      </div>
                    </div>
                    <div className="metric-value">{metric.value}</div>
                    <div className="mt-3 flex items-center gap-1.5 text-[11px] text-[#92939D]">
                      {metric.up ? (
                        <ArrowUpRight size={14} style={{ color: metric.color }} />
                      ) : (
                        <ArrowDownRight size={14} style={{ color: metric.color }} />
                      )}
                      {metric.change}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* CHARTS */}
            <div className="mb-7 grid gap-5 xl:grid-cols-[1.5fr_1fr]">
              <div className="panel p-5 sm:p-6">
                <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="section-title">Creative activity overview</h2>
                    <p className="mt-1.5 text-xs text-[#92939D]">
                      Illustrative index of observed creative activity
                    </p>
                  </div>
                  <button
                    onClick={() => setActive("Competitor Analysis")}
                    className="flex items-center gap-2 rounded-lg border border-[#35363e] px-3 py-2 text-xs text-[#C7C5C9] hover:bg-[#222329]"
                  >
                    View analysis <ArrowRight size={14} />
                  </button>
                </div>

                <div className="mb-5 flex items-center gap-4 text-[11px] text-[#92939D]">
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-[#FF7138]" />
                    Brand A
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-[#A98BFF]" />
                    Brand B
                  </span>
                </div>

                <div className="relative h-[230px]">
                  <div className="absolute inset-0 flex flex-col justify-between">
                    {[100, 75, 50, 25, 0].map((n) => (
                      <div key={n} className="flex items-center gap-3">
                        <span className="w-5 text-[10px] text-[#777883]">
                          {n}
                        </span>
                        <div className="h-px flex-1 border-t border-dashed border-[#303139]" />
                      </div>
                    ))}
                  </div>

                  <div className="absolute inset-y-0 left-9 right-1 flex items-end justify-around gap-2">
                    {performance.map((item, i) => (
                      <div
                        key={item.month}
                        className="flex h-full flex-1 flex-col items-center justify-end gap-2"
                      >
                        <div className="flex h-[200px] w-full items-end justify-center gap-1">
                          <div
                            className="chart-bar w-[35%] max-w-[22px] rounded-t-[4px] bg-[#FF7138]"
                            style={{ height: `${item.value}%` }}
                            title={`Brand A illustrative index: ${item.value}`}
                          />
                          <div
                            className="chart-bar w-[35%] max-w-[22px] rounded-t-[4px] bg-[#A98BFF]"
                            style={{
                              height: `${Math.max(
                                10,
                                item.value * 0.7 + (i % 3) * 9
                              )}%`,
                            }}
                            title="Brand B illustrative index"
                          />
                        </div>
                        <span className="text-[10px] text-[#92939D]">
                          {item.month}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-5 border-t border-[#292a31] pt-4 text-[11px] leading-5 text-[#777883]">
                  The index is invented for layout demonstration and does not
                  represent actual ad counts or performance.
                </div>
              </div>

              <div className="panel p-5 sm:p-6">
                <div className="mb-6">
                  <h2 className="section-title">Creative theme distribution</h2>
                  <p className="mt-1.5 text-xs text-[#92939D]">
                    Example breakdown of messaging themes
                  </p>
                </div>

                <div className="mb-6 flex items-center gap-5">
                  <div className="relative flex h-[120px] w-[120px] shrink-0 items-center justify-center rounded-full"
                    style={{
                      background:
                        "conic-gradient(#FF7138 0 28%, #F4AB77 28% 49%, #A98BFF 49% 67%, #55D6A5 67% 82%, #6EA8FE 82% 100%)",
                    }}
                  >
                    <div className="flex h-[78px] w-[78px] flex-col items-center justify-center rounded-full bg-[#17181d]">
                      <BrainCircuit size={19} className="text-[#FF7138]" />
                      <span className="mt-1 text-[10px] text-[#92939D]">Themes</span>
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">05</div>
                    <div className="mt-1 text-xs text-[#92939D]">
                      Example categories
                    </div>
                    <div className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-[#252029] px-2 py-1 text-[10px] text-[#C6B4FF]">
                      <Sparkles size={12} /> NLP concept
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {themes.map((theme) => (
                    <div key={theme.name}>
                      <div className="mb-2 flex items-center justify-between gap-3">
                        <span className="text-xs text-[#C7C5C9]">
                          {theme.name}
                        </span>
                        <span className="text-[11px] text-[#92939D]">
                          {theme.value}%
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-[#2A2B32]">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${theme.value}%`,
                            background: theme.color,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-5 text-[10px] leading-5 text-[#777883]">
                  Example percentages only; real theme shares require actual
                  collected ads and a defined counting method.
                </p>
              </div>
            </div>

            {/* CREATIVE EXPLORER */}
            <div className="panel mb-7 p-5 sm:p-6">
              <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <div>
                  <h2 className="section-title">Creative intelligence</h2>
                  <p className="mt-1.5 text-xs text-[#92939D]">
                    Example messaging patterns for familiar brands
                  </p>
                </div>
                <div className="relative w-full sm:w-[250px]">
                  <Search
                    size={15}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-[#777883]"
                  />
                  <input
                    className="field pl-9"
                    placeholder="Search sample creatives..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid gap-4 lg:grid-cols-3">
                {filteredCreatives.map((ad) => (
                  <article
                    key={ad.brand}
                    className="overflow-hidden rounded-xl border border-[#303139] bg-[#131418]"
                  >
                    <div
                      className="flex h-[115px] items-center justify-between p-5"
                      style={{
                        background: `linear-gradient(135deg, ${ad.color}22, #17181d 85%)`,
                      }}
                    >
                      <div
                        className="flex h-12 w-12 items-center justify-center rounded-2xl text-xl font-black text-[#101114]"
                        style={{ background: ad.color }}
                      >
                        {ad.initials}
                      </div>
                      <span className="rounded-md border border-white/10 bg-black/20 px-2.5 py-1 text-[10px] text-[#D6D3D1]">
                        {ad.type}
                      </span>
                    </div>

                    <div className="p-4">
                      <div className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[#92939D]">
                        {ad.brand} · Example creative
                      </div>
                      <h3 className="min-h-[44px] text-sm font-bold leading-6">
                        {ad.headline}
                      </h3>
                      <p className="mt-2 min-h-[60px] text-xs leading-5 text-[#92939D]">
                        {ad.description}
                      </p>
                      <div className="my-4 flex flex-wrap gap-1.5">
                        {ad.tags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded-md border border-[#34353D] px-2 py-1 text-[10px] text-[#B7B7C1]"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                      <div className="flex items-center gap-2 border-t border-[#292a31] pt-3 text-xs text-[#FFAB78]">
                        <MessageSquareText size={14} />
                        {ad.strength}
                      </div>
                    </div>
                  </article>
                ))}

                {filteredCreatives.length === 0 && (
                  <div className="py-8 text-sm text-[#92939D] lg:col-span-3">
                    No sample creatives match that search.
                  </div>
                )}
              </div>
              <p className="mt-4 text-[10px] leading-5 text-[#777883]">
                These are illustrative messaging examples, not verified copies
                of current live ads or measured competitor performance.
              </p>
            </div>

            {/* OPPORTUNITIES */}
            <div className="mb-7 grid gap-5 lg:grid-cols-[1.2fr_1fr]">
              <div className="panel p-5 sm:p-6">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <div>
                    <h2 className="section-title">Potential blind spots</h2>
                    <p className="mt-1.5 text-xs text-[#92939D]">
                      Strategic hypotheses to investigate
                    </p>
                  </div>
                  <Lightbulb size={20} className="text-[#F4C56A]" />
                </div>

                {[
                  {
                    title: "Build trust-led creative",
                    text: "Test testimonials, transparent pricing, or product-quality messaging alongside offer-led ads.",
                    tag: "Creative experiment",
                  },
                  {
                    title: "Test distinct audience needs",
                    text: "Compare messaging for first-time customers with messaging for repeat customers.",
                    tag: "Audience hypothesis",
                  },
                  {
                    title: "Explore a different format",
                    text: "Test a product demonstration or creator-style video against a static promotional creative.",
                    tag: "Format experiment",
                  },
                ].map((item, index) => (
                  <div
                    key={item.title}
                    className="flex gap-3 border-t border-[#292a31] py-4 first:border-0 first:pt-0 last:pb-0"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#29231A] text-xs font-bold text-[#F4C56A]">
                      0{index + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-xs font-bold">{item.title}</h3>
                      <p className="mt-1.5 text-xs leading-5 text-[#92939D]">
                        {item.text}
                      </p>
                      <span className="mt-2 inline-block rounded-md bg-[#24252B] px-2 py-1 text-[10px] text-[#B8B8C2]">
                        {item.tag}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="panel p-5 sm:p-6">
                <div className="mb-5 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#242039] text-[#B9A3FF]">
                    <BrainCircuit size={20} />
                  </div>
                  <div>
                    <h2 className="section-title">AI strategy assistant</h2>
                    <p className="mt-1 text-xs text-[#92939D]">
                      Example recommendations
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-[#393044] bg-[#201C29] p-4">
                  <div className="mb-3 flex items-center gap-2 text-xs font-bold text-[#C9B8FF]">
                    <Sparkles size={15} /> Suggested experiment
                  </div>
                  <p className="text-sm font-semibold leading-6">
                    Pair a clear product benefit with a specific customer
                    situation.
                  </p>
                  <p className="mt-3 text-xs leading-5 text-[#B3ADBF]">
                    Create two variations with the same offer but different
                    hooks. Compare qualified engagement and conversions using
                    your own campaign analytics.
                  </p>
                  <div className="mt-4 flex items-center gap-2 text-[10px] text-[#92939D]">
                    <ShieldCheck size={13} />
                    Hypothesis, not a proven performance prediction
                  </div>
                </div>

                <button
                  onClick={() => setActive("Creative Intelligence")}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-[#35363e] py-3 text-xs font-semibold hover:bg-[#222329]"
                >
                  Explore creative intelligence <ArrowRight size={14} />
                </button>
              </div>
            </div>

            {/* FOOTER */}
            <footer className="flex flex-col justify-between gap-3 border-t border-[#292a31] py-5 text-[11px] text-[#777883] sm:flex-row sm:items-center">
              <div className="flex items-center gap-2">
                <Activity size={14} className="text-[#FF7138]" />
                <span>Ad Intelligence</span>
                <span>·</span>
                <span>Competitive insights workspace</span>
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#55D6A5]" />
                  Frontend running
                </span>
                <span>Illustrative dashboard data</span>
              </div>
            </footer>
          </div>
        </section>
      </div>
    </main>
  );
}
