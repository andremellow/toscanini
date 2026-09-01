"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, ArrowUpRight, Check, ChevronRight, CircleDot, Code2, Eye, GitBranch, Hexagon, Pause, Play, Radio, ScanLine, ShieldCheck, Sparkles, Terminal, TriangleAlert, Users, Workflow, X } from "lucide-react";

type AgentState = "working" | "complete" | "queued" | "blocked";
type Agent = { id: string; role: string; detail: string; state: AgentState; x: number; y: number };
const agents: Agent[] = [
  { id: "orchestrator", role: "Orchestrator", detail: "Routing context", state: "working", x: 50, y: 49 },
  { id: "architect", role: "Architect", detail: "Plan approved", state: "complete", x: 21, y: 21 },
  { id: "design", role: "Design Agent", detail: "UX contract", state: "complete", x: 79, y: 21 },
  { id: "worker", role: "Worker", detail: "Implementing", state: "working", x: 19, y: 78 },
  { id: "qa", role: "QA", detail: "Waiting on build", state: "queued", x: 50, y: 86 },
  { id: "reviewer", role: "Code Reviewer", detail: "Context isolated", state: "queued", x: 81, y: 78 },
];
const events = [
  { time: "14:32:18", from: "ORCHESTRATOR", to: "WORKER", text: "Architecture accepted. Begin bounded implementation.", kind: "handoff" },
  { time: "14:31:52", from: "DESIGN REVIEW", to: "ORCHESTRATOR", text: "APPROVE — responsive states are covered.", kind: "success" },
  { time: "14:30:41", from: "ARCH REVIEW", to: "ORCHESTRATOR", text: "APPROVE — no boundary violations found.", kind: "success" },
  { time: "14:28:09", from: "ARCHITECT", to: "ARCH REVIEW", text: "architecture.md ready for independent review.", kind: "artifact" },
  { time: "14:26:33", from: "ORCHESTRATOR", to: "DESIGN AGENT", text: "Map existing components and failure states.", kind: "handoff" },
];
const gates = [
  { name: "Format", status: "pass", ms: "0.8s" }, { name: "Static analysis", status: "pass", ms: "4.2s" },
  { name: "Unit + integration", status: "running", ms: "18.6s" }, { name: "Build", status: "queued", ms: "—" },
  { name: "Browser suite", status: "queued", ms: "—" },
];
function StatusDot({ state }: { state: AgentState }) { return <span className={`status-dot ${state}`} aria-label={state} />; }

export default function Home() {
  const [paused, setPaused] = useState(false); const [selected, setSelected] = useState("orchestrator");
  const [clock, setClock] = useState("00:12:48"); const [demo, setDemo] = useState(true);
  useEffect(() => { if (paused) return; const started = Date.now() - 768_000; const interval = setInterval(() => { const seconds = Math.floor((Date.now() - started) / 1000); setClock(`${String(Math.floor(seconds / 3600)).padStart(2, "0")}:${String(Math.floor((seconds % 3600) / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`); }, 1000); return () => clearInterval(interval); }, [paused]);
  const selectedAgent = useMemo(() => agents.find((agent) => agent.id === selected)!, [selected]);
  return <main className="command-center">
    <div className="scanlines" aria-hidden="true" />
    <header className="topbar">
      <div className="brand-lockup"><div className="brand-mark"><Hexagon size={25} strokeWidth={1.4} /><Sparkles size={11} /></div><div><p className="eyebrow">POWER DEV</p><h1>WORKFLOW COMMAND</h1></div></div>
      <div className="mission"><span className="mission-label">ACTIVE MISSION</span><strong>Spec 024 · Multi-agent delivery system</strong><span className="mission-meta">MEDIUM WORKFLOW <i /> PHASE 04 / 08</span></div>
      <div className="top-actions"><button className={`telemetry ${demo ? "demo" : "live"}`} onClick={() => setDemo(!demo)}><Radio size={14} /> {demo ? "DEMO TELEMETRY" : "LIVE CONTRACT"}</button><span className="runtime"><small>ELAPSED</small>{clock}</span><button className="icon-button" onClick={() => setPaused(!paused)} aria-label={paused ? "Resume timeline" : "Pause timeline"}>{paused ? <Play size={17} /> : <Pause size={17} />}</button></div>
    </header>
    <section className="phase-rail" aria-label="Workflow phases">{["INTAKE", "ARCHITECTURE", "PLAN REVIEW", "IMPLEMENT", "VERIFY", "QA", "FINAL REVIEW", "COMPLETE"].map((phase, index) => <div className={`phase ${index < 3 ? "done" : index === 3 ? "active" : ""}`} key={phase}><span>{index < 3 ? <Check size={12} /> : String(index + 1).padStart(2, "0")}</span><div><small>PHASE {String(index + 1).padStart(2, "0")}</small><strong>{phase}</strong></div></div>)}</section>
    <div className="workspace-grid">
      <section className="panel topology-panel"><div className="panel-heading"><div><span className="section-code">01 / TOPOLOGY</span><h2>Agent Network</h2></div><div className="legend"><span><i className="working" /> ACTIVE</span><span><i className="complete" /> DONE</span><span><i className="queued" /> QUEUED</span></div></div>
        <div className="topology"><svg className="connections" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{agents.slice(1).map((agent) => <line key={agent.id} x1="50" y1="49" x2={agent.x} y2={agent.y} />)}<path className="pulse-path" d="M50 49 L19 78" /></svg><div className="radar-ring ring-one" /><div className="radar-ring ring-two" />
          {agents.map((agent) => <button key={agent.id} className={`agent-node ${agent.state} ${selected === agent.id ? "selected" : ""}`} style={{ left: `${agent.x}%`, top: `${agent.y}%` }} onClick={() => setSelected(agent.id)}><span className="node-icon">{agent.id === "orchestrator" ? <Workflow size={21} /> : agent.id === "worker" ? <Code2 size={19} /> : agent.id === "qa" ? <ShieldCheck size={19} /> : <Eye size={19} />}</span><span className="node-copy"><strong>{agent.role}</strong><small><StatusDot state={agent.state} />{agent.detail}</small></span></button>)}
          <div className="selection-card"><span>SELECTED NODE</span><strong>{selectedAgent.role}</strong><small>{selectedAgent.detail} · {selectedAgent.state.toUpperCase()}</small></div></div></section>
      <section className="panel event-panel"><div className="panel-heading"><div><span className="section-code">02 / SIGNAL</span><h2>Communication Stream</h2></div><Activity size={18} className="cyan" /></div><div className="event-stream">{events.map((event, index) => <button className="event" key={`${event.time}-${index}`}><span className="event-time">{event.time}</span><span className={`event-glyph ${event.kind}`}>{event.kind === "success" ? <Check size={13} /> : event.kind === "artifact" ? <Terminal size={13} /> : <ArrowUpRight size={13} />}</span><span className="event-content"><strong>{event.from} <ChevronRight size={11} /> {event.to}</strong><small>{event.text}</small></span></button>)}</div><button className="stream-action"><ScanLine size={15} /> INSPECT FULL EVENT LOG <ChevronRight size={14} /></button></section>
      <section className="panel gate-panel"><div className="panel-heading"><div><span className="section-code">03 / INTEGRITY</span><h2>Verification Gates</h2></div><span className="score">42%</span></div><div className="gate-progress"><span /></div><div className="gate-list">{gates.map((gate) => <div className="gate" key={gate.name}><span className={`gate-icon ${gate.status}`}>{gate.status === "pass" ? <Check size={13} /> : gate.status === "running" ? <CircleDot size={13} /> : <span />}</span><strong>{gate.name}</strong><small>{gate.status.toUpperCase()}</small><time>{gate.ms}</time></div>)}</div></section>
      <section className="panel intel-panel"><div className="panel-heading"><div><span className="section-code">04 / INTELLIGENCE</span><h2>Mission Brief</h2></div><GitBranch size={18} className="cyan" /></div><div className="metric-grid"><div><span>ACCEPTANCE</span><strong>18<small>/18</small></strong><em>Mapped</em></div><div><span>FINDINGS</span><strong>02</strong><em>Non-blocking</em></div><div><span>FILES</span><strong>14</strong><em>Changed</em></div><div><span>CONTEXTS</span><strong>06</strong><em>Independent</em></div></div><div className="risk-row"><ShieldCheck size={18} /><div><small>RISK POSTURE</small><strong>Controlled</strong></div><span>NO BLOCKERS</span></div><div className="finding-row"><TriangleAlert size={17} /><p><strong>2 review notes</strong> queued for final consolidation</p><button aria-label="Dismiss"><X size={14} /></button></div></section>
    </div>
    <footer><span><i className={demo ? "amber-dot" : "green-dot"} /> {demo ? "REPRESENTATIVE EVENT DATA" : "APP SERVER CONTRACT READY"}</span><span>POWER DEV WORKFLOW <b>v0.1.0</b></span><span><Users size={13} /> 2 ACTIVE · 2 COMPLETE · 2 QUEUED</span></footer>
  </main>;
}
