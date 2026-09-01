"use client";

import { useEffect, useState } from "react";
import { Activity, ArrowUpRight, Check, ChevronRight, CircleDot, Code2, Eye, FileText, GitBranch, Layers3, Pause, Play, Radio, ShieldCheck, Sparkles, TestTube2, Users, Workflow, Zap } from "lucide-react";

const agents = [
  { id: "architect", name: "Architect", state: "complete", icon: Layers3, angle: -145 },
  { id: "design", name: "Design", state: "complete", icon: Sparkles, angle: -65 },
  { id: "worker", name: "Worker", state: "active", icon: Code2, angle: 10 },
  { id: "qa", name: "QA", state: "queued", icon: TestTube2, angle: 72 },
  { id: "review", name: "Review", state: "queued", icon: Eye, angle: 145 },
];
const phases = ["Intake", "Architecture", "Plan review", "Implement", "Verify", "QA", "Final review", "Complete"];
const gates = [
  { name: "Architecture", detail: "Boundaries approved", status: "pass", icon: Layers3 },
  { name: "Static analysis", detail: "No critical findings", status: "pass", icon: ShieldCheck },
  { name: "Unit tests", detail: "184 of 236 complete", status: "active", icon: TestTube2 },
  { name: "Application build", detail: "Waiting for tests", status: "queued", icon: Code2 },
];
const timeline = [
  { time: "14:26", title: "Requirements mapped", body: "18 acceptance criteria linked to delivery evidence.", status: "done" },
  { time: "14:28", title: "Architecture created", body: "Boundaries, data flow and rollback strategy documented.", status: "done", file: "architecture.md" },
  { time: "14:31", title: "Independent review approved", body: "No coupling, tenancy or data-integrity blockers found.", status: "done", file: "review.md" },
  { time: "14:32", title: "Implementation in progress", body: "Worker owns the production diff while reviewers remain isolated.", status: "active" },
  { time: "NEXT", title: "Verification and QA", body: "Deterministic gates run before independent acceptance validation.", status: "queued" },
];
const activity = [
  { agent: "Worker", action: "is implementing the approved architecture", time: "now", tone: "active" },
  { agent: "Orchestrator", action: "handed the bounded plan to Worker", time: "1m", tone: "neutral" },
  { agent: "Design Reviewer", action: "approved responsive and failure states", time: "3m", tone: "done" },
  { agent: "Architecture Reviewer", action: "approved boundaries and data integrity", time: "4m", tone: "done" },
];

export default function Home() {
  const [paused, setPaused] = useState(false);
  const [selected, setSelected] = useState("worker");
  const [seconds, setSeconds] = useState(773);
  useEffect(() => { if (paused) return; const id = setInterval(() => setSeconds((v) => v + 1), 1000); return () => clearInterval(id); }, [paused]);
  const clock = `${String(Math.floor(seconds / 60)).padStart(2,"0")}:${String(seconds % 60).padStart(2,"0")}`;
  return <main className="shell">
    <div className="ambient ambient-a"/><div className="ambient ambient-b"/><div className="noise"/>
    <header className="header">
      <div className="brand"><span className="brand-orb"><Workflow size={20}/></span><div><small>POWER DEV WORKFLOW</small><strong>Mission Control</strong></div></div>
      <div className="mission-title"><span>ACTIVE MISSION</span><strong>Spec 024 · Multi-agent delivery system</strong></div>
      <div className="header-actions"><span className="live"><Radio size={13}/> LIVE PREVIEW</span><span className="elapsed"><small>ELAPSED</small>{clock}</span><button onClick={() => setPaused(!paused)} aria-label={paused ? "Resume timeline" : "Pause timeline"}>{paused ? <Play size={16}/> : <Pause size={16}/>}</button></div>
    </header>

    <nav className="workflow-rail" aria-label="Workflow progress">{phases.map((phase,index)=><div className={`workflow-step ${index<3?"done":index===3?"current":""}`} key={phase}><span>{index<3?<Check size={11}/>:index+1}</span><div><small>{String(index+1).padStart(2,"0")}</small><strong>{phase}</strong></div></div>)}</nav>

    <section className="dashboard">
      <aside className="left-stack">
        <article className="glass progress-card"><div className="card-title"><div><small>MISSION PROGRESS</small><h2>Delivery pulse</h2></div><Zap size={18}/></div><div className="progress-dial"><svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="50"/><circle className="fill" cx="60" cy="60" r="50"/></svg><div><strong>42<small>%</small></strong><span>ON TRACK</span></div></div><div className="progress-stats"><span><small>PHASE</small><strong>04 / 08</strong></span><span><small>RISK</small><strong>LOW</strong></span><span><small>BLOCKERS</small><strong>0</strong></span></div></article>
        <article className="glass gates-card"><div className="card-title"><div><small>QUALITY SYSTEM</small><h2>Verification gates</h2></div><ShieldCheck size={18}/></div><div className="gates">{gates.map((gate)=><div className={`gate ${gate.status}`} key={gate.name}><span className="gate-orb"><gate.icon size={16}/></span><div><strong>{gate.name}</strong><small>{gate.detail}</small></div><span className="gate-state">{gate.status}</span></div>)}</div></article>
      </aside>

      <article className="glass core-card">
        <div className="card-title core-heading"><div><small>AGENT NETWORK</small><h2>Execution intelligence</h2></div><span><i/> 2 ACTIVE · 2 QUEUED</span></div>
        <div className="hologram">
          <div className="orbit orbit-1"/><div className="orbit orbit-2"/><div className="orbit orbit-3"/><div className="orbit orbit-4"/>
          <div className="sweep"/><div className="core-glow"/><div className="core"><span className="core-ring"/><Workflow size={34}/><strong>ORCHESTRATOR</strong><small>Routing context</small></div>
          {agents.map((agent)=>{const radians=agent.angle*Math.PI/180;const x=50+40*Math.cos(radians);const y=50+40*Math.sin(radians);const Icon=agent.icon;return <button key={agent.id} className={`agent ${agent.state} ${selected===agent.id?"selected":""}`} style={{left:`${x}%`,top:`${y}%`}} onClick={()=>setSelected(agent.id)}><span><Icon size={18}/></span><strong>{agent.name}</strong><small>{agent.state}</small></button>})}
          <svg className="neural-lines" viewBox="0 0 100 100" preserveAspectRatio="none">{agents.map((agent)=>{const r=agent.angle*Math.PI/180;return <line key={agent.id} x1="50" y1="50" x2={50+40*Math.cos(r)} y2={50+40*Math.sin(r)}/>})}</svg>
          <div className="holo-caption"><span>SELECTED</span><strong>{agents.find(a=>a.id===selected)?.name}</strong><small>Independent context · production scope protected</small></div>
        </div>
      </article>

      <aside className="right-stack">
        <article className="glass brief-card"><div className="card-title"><div><small>MISSION BRIEF</small><h2>Current state</h2></div><GitBranch size={18}/></div><div className="brief-metrics"><div><strong>18<small>/18</small></strong><span>Criteria mapped</span></div><div><strong>14</strong><span>Files in scope</span></div><div><strong>06</strong><span>Isolated contexts</span></div></div><div className="risk"><ShieldCheck size={18}/><div><small>RISK POSTURE</small><strong>Controlled</strong></div><span>NO BLOCKERS</span></div></article>
        <article className="glass activity-card"><div className="card-title"><div><small>LIVE ACTIVITY</small><h2>Who is doing what</h2></div><Activity size={18}/></div><div className="activities">{activity.map((item,index)=><div className="activity-item" key={index}><span className={`activity-dot ${item.tone}`}/><p><strong>{item.agent}</strong> {item.action}</p><time>{item.time}</time></div>)}</div><button className="view-log">View complete activity log <ChevronRight size={14}/></button></article>
      </aside>
    </section>

    <section className="glass timeline-card"><div className="timeline-heading"><div><small>MISSION TIMELINE</small><h2>Continuous delivery record</h2></div><span>Updates appear here as agents complete work</span></div><div className="timeline">{timeline.map((item,index)=><div className={`timeline-item ${item.status}`} key={item.time}><div className="timeline-marker"><span>{item.status==="done"?<Check size={12}/>:item.status==="active"?<CircleDot size={12}/>:index+1}</span></div><time>{item.time}</time><strong>{item.title}</strong><p>{item.body}</p>{item.file&&<button><FileText size={13}/>{item.file}<ArrowUpRight size={12}/></button>}</div>)}</div></section>
    <footer><span><i/> APP SERVER CONTRACT READY</span><span>POWER DEV WORKFLOW · v0.1.0</span><span><Users size={13}/> 6 SPECIALIST CONTEXTS</span></footer>
  </main>;
}
