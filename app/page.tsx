"use client";

import {
  Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import {
  ArrowRight, BarChart3, BookOpen, Building2, ChevronDown, Download,
  Globe2, Info, Search, TrendingUp, Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import pilotData from "./pilot-data.json";

type AnnualRecord = {
  releaseYear: number; metricYear: number; name: string; nameKey: string;
  institution: string; country: string; field: string; subfield: string;
  rank: number | null; rankNoSelf: number | null; subfieldRank: number | null;
  subfieldRankNoSelf: number | null; citations: number | null; hIndex: number | null;
  hmIndex: number | null; papers: number | null; cScore: number | null;
  cScoreNoSelf: number | null; selfCitationPercent: number | null;
  firstYear: number | null; lastYear: number | null;
};

type Scientist = {
  id: string; name: string; institution: string; country: string; field: string;
  subfield: string; appearances: number; history: AnnualRecord[];
};

const data = pilotData as typeof pilotData & {
  scientists: Scientist[];
  rankingsByYear: Record<string, AnnualRecord[]>;
};

function number(value: number | null | undefined, digits = 0) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);
}

function shortNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}m`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
  return number(value);
}

const tooltipStyle = {
  border: "1px solid #dce8e5", borderRadius: 12,
  boxShadow: "0 12px 30px rgba(30, 71, 66, .08)", fontSize: 12,
};

export default function Home() {
  const [selectedYear, setSelectedYear] = useState(2026);
  const [yearMenuOpen, setYearMenuOpen] = useState(false);
  const [excludeSelf, setExcludeSelf] = useState(true);
  const [scientistQuery, setScientistQuery] = useState("");
  const [rankingQuery, setRankingQuery] = useState("");
  const defaultScientist = data.scientists.find((item) => item.name.includes("Wang, Zhong Lin")) ?? data.scientists[0];
  const [selectedScientistId, setSelectedScientistId] = useState(defaultScientist.id);

  const selectedRelease = data.releases.find((release) => release.releaseYear === selectedYear)!;
  const releaseIndex = data.releases.findIndex((release) => release.releaseYear === selectedYear);
  const previousRelease = data.releases[releaseIndex - 1];
  const annualGrowth = previousRelease
    ? ((selectedRelease.totalRecords - previousRelease.totalRecords) / previousRelease.totalRecords) * 100
    : null;
  const selectedScientist = data.scientists.find((scientist) => scientist.id === selectedScientistId)!;
  const selectedScientistRecord = selectedScientist.history.find((item) => item.releaseYear === selectedYear)
    ?? selectedScientist.history[selectedScientist.history.length - 1];

  const scientistMatches = useMemo(() => {
    const query = scientistQuery.toLowerCase().trim();
    if (!query) return data.scientists.slice(0, 6);
    return data.scientists.filter((item) =>
      `${item.name} ${item.institution} ${item.field}`.toLowerCase().includes(query),
    ).slice(0, 6);
  }, [scientistQuery]);

  const rankTrend = selectedScientist.history.map((item) => ({
    year: item.releaseYear,
    rank: excludeSelf ? item.rankNoSelf : item.rank,
    subfieldRank: excludeSelf ? item.subfieldRankNoSelf : item.subfieldRank,
  }));

  const rankings = useMemo(() => {
    const query = rankingQuery.toLowerCase().trim();
    return data.rankingsByYear[String(selectedYear)].filter((item) =>
      `${item.name} ${item.institution} ${item.country} ${item.field}`.toLowerCase().includes(query),
    ).slice(0, 12);
  }, [rankingQuery, selectedYear]);

  const selectScientist = (scientist: Scientist) => {
    setSelectedScientistId(scientist.id);
    setScientistQuery(scientist.name);
  };

  const downloadScientistCsv = () => {
    const headers = ["release_year", "metric_year", "global_rank", "subfield_rank", "citations", "h_index", "hm_index", "institution"];
    const rows = selectedScientist.history.map((item) => [
      item.releaseYear, item.metricYear,
      excludeSelf ? item.rankNoSelf : item.rank,
      excludeSelf ? item.subfieldRankNoSelf : item.subfieldRank,
      item.citations, item.hIndex, item.hmIndex,
      `"${item.institution.replaceAll('"', '""')}"`,
    ]);
    const blob = new Blob([[headers, ...rows].map((row) => row.join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedScientist.id}-pilot-trend.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="site-shell">
      <header className="topbar">
        <a className="brand" href="#overview" aria-label="Scientist Trends home">
          <span className="brand-mark"><BarChart3 size={20} /></span>
          <span><strong>Scientist Trends</strong><small>Annual citation impact explorer</small></span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#overview">Overview</a><a href="#scientists">Scientists</a>
          <a href="#institutions">Institutions</a><a href="#rankings">Rankings</a>
          <a href="#methodology">Methodology</a>
        </nav>
        <div className="year-picker-wrap">
          <button className="year-picker" onClick={() => setYearMenuOpen((open) => !open)} aria-expanded={yearMenuOpen}>
            <span><small>Release</small>{selectedYear}</span><ChevronDown size={16} />
          </button>
          {yearMenuOpen && <div className="year-menu">
            {data.meta.releaseYears.map((year) => <button key={year} className={year === selectedYear ? "active" : ""} onClick={() => { setSelectedYear(year); setYearMenuOpen(false); }}>
              <span>{year} release</span><small>Metrics through {year - 1}</small>
            </button>)}
          </div>}
        </div>
      </header>

      <main>
        <section className="hero" id="overview">
          <div className="hero-copy">
            <div className="eyebrow"><span /> Pilot study · career-long dataset</div>
            <h1>Explore how scientific impact changes over time.</h1>
            <p>Search scientists, follow rank trajectories, and compare the institutions, countries, and fields represented in each annual release.</p>
            <div className="hero-actions">
              <a className="primary-button" href="#scientists">Find a scientist <ArrowRight size={17} /></a>
              <a className="text-button" href="#methodology">How rankings work</a>
            </div>
          </div>
          <div className="hero-panel">
            <div className="hero-panel-head">
              <div><small>Published records</small><strong>{number(selectedRelease.totalRecords)}</strong></div>
              <span className="soft-badge">{selectedYear} release</span>
            </div>
            <ResponsiveContainer width="100%" height={190}>
              <AreaChart data={data.releases} margin={{ top: 16, right: 4, left: 4, bottom: 0 }}>
                <defs><linearGradient id="recordsFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#42a893" stopOpacity={0.28} /><stop offset="100%" stopColor="#42a893" stopOpacity={0.02} /></linearGradient></defs>
                <CartesianGrid vertical={false} stroke="#e7efed" />
                <XAxis dataKey="releaseYear" axisLine={false} tickLine={false} tick={{ fill: "#72827f", fontSize: 11 }} />
                <YAxis hide domain={[90000, 250000]} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value) => [number(Number(value)), "Records"]} />
                <Area type="monotone" dataKey="totalRecords" stroke="#287d6d" strokeWidth={2.5} fill="url(#recordsFill)" />
              </AreaChart>
            </ResponsiveContainer>
            <div className="hero-panel-foot"><span><TrendingUp size={15} /> {annualGrowth ? `${annualGrowth.toFixed(1)}% from prior release` : "First release shown"}</span><span>Metrics through {selectedRelease.metricYear}</span></div>
          </div>
        </section>

        <section className="pilot-note"><Info size={18} /><p><strong>This is a visual pilot.</strong> Scientist profiles and breakdowns use a 5,000-record sample from each release. Published record totals come from the complete source tables.</p></section>

        <section className="metrics-grid" aria-label="Release overview">
          <MetricCard icon={<Users size={18} />} label="Listed scientists" value={shortNumber(selectedRelease.totalRecords)} note={`Career metrics through ${selectedRelease.metricYear}`} />
          <MetricCard icon={<Building2 size={18} />} label="Leading institution in sample" value={selectedRelease.topInstitutions[0]?.name ?? "—"} note={`${number(selectedRelease.topInstitutions[0]?.count)} of 5,000 sampled records`} compact />
          <MetricCard icon={<Globe2 size={18} />} label="Leading country in sample" value={selectedRelease.topCountries[0]?.name ?? "—"} note={`${number(selectedRelease.topCountries[0]?.count)} sampled records`} />
          <MetricCard icon={<BookOpen size={18} />} label="Leading field in sample" value={selectedRelease.topFields[0]?.name ?? "—"} note={`${number(selectedRelease.topFields[0]?.count)} sampled records`} compact />
        </section>

        <section className="section" id="scientists">
          <SectionHeading eyebrow="Scientist explorer" title="Follow an individual trajectory" text="Search the pilot cohort and view the same indicators across annual releases." />
          <div className="scientist-grid">
            <div className="profile-card">
              <label className="search-label" htmlFor="scientist-search">Search scientist</label>
              <div className="search-box"><Search size={18} /><input id="scientist-search" value={scientistQuery} onChange={(event) => setScientistQuery(event.target.value)} placeholder="Name, institution, or field" /></div>
              <div className="search-results" aria-label="Scientist search results">
                {scientistMatches.map((scientist) => <button key={scientist.id} className={scientist.id === selectedScientistId ? "selected" : ""} onClick={() => selectScientist(scientist)}>
                  <span className="initials">{initials(scientist.name)}</span><span><strong>{scientist.name}</strong><small>{scientist.institution}</small></span>
                </button>)}
              </div>
              <div className="profile-summary"><span className="initials large">{initials(selectedScientist.name)}</span><div><h3>{selectedScientist.name}</h3><p>{selectedScientistRecord.institution}</p></div></div>
              <dl className="profile-details">
                <div><dt>Country</dt><dd>{selectedScientistRecord.country}</dd></div><div><dt>Primary field</dt><dd>{selectedScientistRecord.field}</dd></div>
                <div><dt>Subfield</dt><dd>{selectedScientistRecord.subfield}</dd></div><div><dt>Releases linked</dt><dd>{selectedScientist.appearances} of 8</dd></div>
              </dl>
            </div>

            <div className="chart-card rank-card">
              <div className="card-heading"><div><small>Global rank trend</small><h3>{selectedScientist.name}</h3></div><div className="segmented" aria-label="Self citation setting"><button className={excludeSelf ? "active" : ""} onClick={() => setExcludeSelf(true)}>Excluding self-citations</button><button className={!excludeSelf ? "active" : ""} onClick={() => setExcludeSelf(false)}>All citations</button></div></div>
              <div className="rank-highlight">
                <div><small>{selectedYear} global rank</small><strong>#{number(excludeSelf ? selectedScientistRecord.rankNoSelf : selectedScientistRecord.rank)}</strong></div>
                <div><small>Subfield rank</small><strong>#{number(excludeSelf ? selectedScientistRecord.subfieldRankNoSelf : selectedScientistRecord.subfieldRank)}</strong></div>
                <div><small>Citations</small><strong>{shortNumber(selectedScientistRecord.citations)}</strong></div><div><small>h-index</small><strong>{number(selectedScientistRecord.hIndex)}</strong></div>
              </div>
              <div className="chart-wrap"><ResponsiveContainer width="100%" height={300}><LineChart data={rankTrend} margin={{ top: 18, right: 14, left: 2, bottom: 4 }}>
                <CartesianGrid vertical={false} stroke="#e7efed" /><XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: "#71817e", fontSize: 12 }} />
                <YAxis reversed domain={[1, "dataMax"]} axisLine={false} tickLine={false} width={46} tick={{ fill: "#71817e", fontSize: 11 }} tickFormatter={(value) => `#${number(value)}`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [`#${number(Number(value))}`, name === "rank" ? "Global rank" : "Subfield rank"]} />
                <Line type="monotone" dataKey="rank" name="rank" stroke="#267b6b" strokeWidth={3} dot={{ r: 4, fill: "#267b6b", strokeWidth: 2, stroke: "white" }} connectNulls={false} />
                <Line type="monotone" dataKey="subfieldRank" name="subfieldRank" stroke="#7991c9" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3, fill: "#7991c9", strokeWidth: 2, stroke: "white" }} connectNulls={false} />
              </LineChart></ResponsiveContainer></div>
              <div className="legend"><span><i className="teal" /> Global rank</span><span><i className="blue" /> Subfield rank</span><small>Higher position is plotted toward the top.</small></div>
            </div>
          </div>

          <div className="table-card annual-table">
            <div className="card-heading"><div><small>Annual detail</small><h3>Release history</h3></div><button className="quiet-button" onClick={downloadScientistCsv}><Download size={15} /> Export sample</button></div>
            <div className="table-scroll"><table><thead><tr><th>Release</th><th>Global rank</th><th>Subfield rank</th><th>Citations</th><th>h-index</th><th>hm-index</th><th>Institution</th></tr></thead><tbody>
              {selectedScientist.history.map((item) => <tr key={item.releaseYear}><td><strong>{item.releaseYear}</strong><small>through {item.metricYear}</small></td><td>#{number(excludeSelf ? item.rankNoSelf : item.rank)}</td><td>{(excludeSelf ? item.subfieldRankNoSelf : item.subfieldRank) ? `#${number(excludeSelf ? item.subfieldRankNoSelf : item.subfieldRank)}` : "—"}</td><td>{number(item.citations)}</td><td>{number(item.hIndex)}</td><td>{number(item.hmIndex, 1)}</td><td>{item.institution}</td></tr>)}
            </tbody></table></div>
          </div>
        </section>

        <section className="section" id="institutions">
          <SectionHeading eyebrow="Institutions and countries" title={`Where sampled scientists were affiliated in ${selectedYear}`} text="These counts describe affiliations in the selected release. They are not institutional performance rankings." />
          <div className="two-column">
            <BreakdownCard icon={<Building2 size={19} />} title="Institutions" subtitle="Top affiliations in the 5,000-record sample" items={selectedRelease.topInstitutions} color="teal" />
            <BreakdownCard icon={<Globe2 size={19} />} title="Countries" subtitle="Country associated with most recent institution" items={selectedRelease.topCountries} color="blue" />
          </div>
        </section>

        <section className="section" id="rankings">
          <SectionHeading eyebrow="Annual ranking" title={`${selectedYear} pilot ranking table`} text={`Career-long indicators through ${selectedRelease.metricYear}. Search the first 60 records included in this pilot.`} />
          <div className="table-card rankings-card">
            <div className="ranking-tools"><div className="search-box"><Search size={17} /><input value={rankingQuery} onChange={(event) => setRankingQuery(event.target.value)} placeholder="Search name, institution, country, or field" /></div><div className="data-chip">Career-long</div><div className="data-chip">{excludeSelf ? "Self-citations excluded" : "All citations"}</div></div>
            <div className="table-scroll"><table><thead><tr><th>Rank</th><th>Scientist</th><th>Institution</th><th>Country</th><th>Field</th><th>Citations</th><th>h-index</th><th>c-score</th></tr></thead><tbody>
              {rankings.map((item) => <tr key={`${item.nameKey}-${item.releaseYear}`}><td><span className="rank-pill">#{number(excludeSelf ? item.rankNoSelf : item.rank)}</span></td><td><strong>{item.name}</strong><small>{item.subfield}</small></td><td>{item.institution}</td><td>{item.country}</td><td>{item.field}</td><td>{number(item.citations)}</td><td>{number(item.hIndex)}</td><td>{number(excludeSelf ? item.cScoreNoSelf : item.cScore, 2)}</td></tr>)}
            </tbody></table></div>
          </div>
        </section>

        <section className="methodology" id="methodology">
          <div><div className="eyebrow light"><span /> Read the data carefully</div><h2>Rankings provide one view of citation impact.</h2><p>The underlying database uses a composite citation indicator and field-adjusted inclusion criteria. It should not be interpreted as a complete assessment of scientific quality or institutional performance.</p></div>
          <div className="method-cards">
            <article><span>01</span><h3>Release year</h3><p>The selector begins in 2019, when the dataset was first published. Each release summarizes metrics through an earlier calendar year.</p></article>
            <article><span>02</span><h3>Inclusion</h3><p>Scientists are included through the top 100,000 composite scores or the top 2% within their primary subfield.</p></article>
            <article><span>03</span><h3>Pilot limits</h3><p>This preview uses sampled records and conservative exact-name links. The production pipeline will normalize identities and institutions across all records.</p></article>
          </div>
        </section>
      </main>

      <footer><div className="brand footer-brand"><span className="brand-mark"><BarChart3 size={18} /></span><span><strong>Scientist Trends</strong><small>Pilot interface</small></span></div><p>Built from the annual science-wide citation indicator datasets. Source attribution and full methodology will accompany the production release.</p><a href="#overview">Back to top ↑</a></footer>
    </div>
  );
}

function initials(name: string) { return name.split(/[ ,]+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join(""); }

function MetricCard({ icon, label, value, note, compact = false }: { icon: React.ReactNode; label: string; value: string; note: string; compact?: boolean }) {
  return <article className="metric-card"><span className="metric-icon">{icon}</span><small>{label}</small><strong className={compact ? "compact" : ""}>{value}</strong><p>{note}</p></article>;
}

function SectionHeading({ eyebrow, title, text }: { eyebrow: string; title: string; text: string }) {
  return <div className="section-heading"><div><span>{eyebrow}</span><h2>{title}</h2></div><p>{text}</p></div>;
}

function BreakdownCard({ icon, title, subtitle, items, color }: { icon: React.ReactNode; title: string; subtitle: string; items: { name: string; count: number }[]; color: "teal" | "blue" }) {
  const maximum = items[0]?.count || 1;
  return <article className="breakdown-card"><div className="card-heading"><div className="breakdown-title"><span className={`metric-icon ${color}`}>{icon}</span><div><h3>{title}</h3><small>{subtitle}</small></div></div><span className="sample-label">Sample view</span></div><div className="bars">{items.slice(0, 7).map((item, index) => <div className="bar-row" key={item.name}><span className="bar-rank">{String(index + 1).padStart(2, "0")}</span><div><div className="bar-label"><strong>{item.name}</strong><span>{number(item.count)}</span></div><div className="bar-track"><i className={color} style={{ width: `${Math.max(5, (item.count / maximum) * 100)}%` }} /></div></div></div>)}</div></article>;
}
