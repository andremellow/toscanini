"use client";

import { useMemo, useState } from "react";
import { Activity, AlertTriangle, ArrowRight, Check, Clock3, Code2, Eye, FileSearch, GitBranch, Layers3, Radio, ShieldAlert, TestTube2, Users } from "lucide-react";

const roles = [
  { id: "architect", label: "Architect", starts: 1, findings: 0, icon: Layers3 },
  { id: "architecture", label: "Architecture Review (legacy)", starts: 7, findings: 4, icon: GitBranch },
  { id: "specification", label: "Specification Review", starts: 1, findings: 0, icon: FileSearch },
  { id: "worker", label: "Worker", starts: 9, findings: 0, icon: Code2 },
  { id: "code", label: "Code Review", starts: 8, findings: 2, icon: Eye },
  { id: "tests", label: "Test Analyst", starts: 9, findings: 9, icon: TestTube2 },
  { id: "qa", label: "Executable QA", starts: 4, findings: 3, icon: Radio },
  { id: "design", label: "Design Review", starts: 2, findings: 3, icon: Activity },
];
const phases = [
  { label: "Plan & contract", minutes: 22, tone: "plan" },
  { label: "Build & first review", minutes: 43, tone: "build" },
  { label: "QA & remediation", minutes: 44, tone: "repair" },
  { label: "Final review", minutes: 13, tone: "final" },
];
const moments = [
  { at: "00m", round: "R1", from: "Toscanini", to: "Architecture + Design", title: "Planning review begins", detail: "Three architecture findings; design approved.", kind: "review" },
  { at: "21m", round: "R3", from: "Toscanini", to: "Worker", title: "Implementation starts", detail: "Approved specification and architecture become the worker contract.", kind: "build" },
  { at: "42m", round: "R3", from: "Code + Tests", to: "Worker", title: "Eight findings consolidated", detail: "One source defect and seven test gaps returned together.", kind: "finding" },
  { at: "62m", round: "R5", from: "QA", to: "Worker", title: "Browser QA finds media failure", detail: "Real UI validation blocks; remaining authority checks are interrupted.", kind: "qa" },
  { at: "71m", round: "R6–R8", from: "Reviewers", to: "Worker", title: "Client remediation fragments", detail: "Three correction passes and repeated backend verification for narrow client deltas.", kind: "finding" },
  { at: "84m", round: "R8", from: "API QA", to: "Worker", title: "Missing-file grant discovered", detail: "A partial API run finds a defect already visible in the earlier browser sequence.", kind: "qa" },
  { at: "96m", round: "R9–R10", from: "Tests", to: "Worker", title: "Fixture passes for wrong reason", detail: "Negative authorization test lacked a usable positive control.", kind: "finding" },
  { at: "102m", round: "R9", from: "Architecture", to: "Worker", title: "Late MIME compatibility finding", detail: "Architecture result arrives after the previous correction already completed.", kind: "late" },
  { at: "117m", round: "R12", from: "API QA", to: "Final Code Review", title: "Partial QA recorded as pass", detail: "Bounded API evidence becomes the latest QA state while full visual QA remains blocked.", kind: "risk" },
  { at: "122m", round: "R12", from: "Toscanini", to: "Delivery", title: "Completion remains blocked", detail: "Source converged; final UI and design evidence did not.", kind: "blocked" },
];
const problems = [
  ["Gate identity", "Approvals were stored by role, without immutable scope or implementation checkpoint."],
  ["Partial QA overwrite", "A bounded API pass replaced the latest state of a broader blocked browser QA."],
  ["Mode contradiction", "Directed QA was told to confirm a fix and simultaneously reject fix-confirmation context."],
  ["Fragmented checkpoint", "Architecture feedback arrived after another remediation batch had already started."],
  ["Budget distortion", "The old gate treated the highest round number as the number of remediation batches."],
];

export default function Home() {
  const [selectedRole, setSelectedRole] = useState("worker");
  const [filter, setFilter] = useState("all");
  const selected = roles.find((role) => role.id === selectedRole) ?? roles[0];
  const visibleMoments = useMemo(() => filter === "all" ? moments : moments.filter((moment) => moment.kind === filter), [filter]);
  const maxStarts = Math.max(...roles.map((role) => role.starts));
  const SelectedIcon = selected.icon;
  return <main className="forensics-shell">
    <header className="topbar">
      <div className="identity"><span className="monogram">T</span><div><small>TOSCANINI</small><strong>Execution Forensics</strong></div></div>
      <div className="run-name"><small>RUN</small><strong>public-draft-preview-20260905</strong></div>
      <span className="blocked-state"><ShieldAlert size={16}/> Delivery blocked</span>
    </header>
    <section className="headline">
      <div><small>EXECUTION DIAGNOSTIC</small><h1>Quality improved. Convergence failed.</h1><p>The implementation stabilized, but review identity, QA scope and remediation sequencing allowed the workflow to keep circling.</p></div>
      <div className="score-ring"><svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="48"/><circle className="score-fill" cx="60" cy="60" r="48"/></svg><span><strong>3</strong><small>/ 10 efficiency</small></span></div>
    </section>
    <section className="metric-strip">
      <div><Clock3/><strong>2h 02m</strong><span>recorded runtime</span></div><div><Users/><strong>41</strong><span>agent activations</span></div><div><Code2/><strong>8</strong><span>worker corrections</span></div><div><AlertTriangle/><strong>21</strong><span>total findings</span></div><div><Check/><strong>17</strong><span>resolved findings</span></div>
    </section>
    <section className="time-allocation panel">
      <div className="section-title"><div><small>TIME ALLOCATION</small><h2>Where the 122 minutes went</h2></div><span>Estimated from recorded lifecycle events</span></div>
      <div className="phase-track">{phases.map((phase) => <div key={phase.label} className={`phase ${phase.tone}`} style={{flex: phase.minutes}}><strong>{phase.minutes}m</strong><span>{phase.label}</span></div>)}</div><div className="axis"><span>00:00</span><span>00:30</span><span>01:00</span><span>01:30</span><span>02:02</span></div>
    </section>
    <section className="analysis-grid">
      <article className="panel network-panel"><div className="section-title"><div><small>COMMUNICATION LOAD</small><h2>Agent handoffs</h2></div><span>Click a role</span></div><div className="network-body">
        <div className="role-bars">{roles.map((role) => { const Icon = role.icon; return <button key={role.id} className={selectedRole === role.id ? "role-row selected" : "role-row"} onClick={() => setSelectedRole(role.id)}><span className="role-icon"><Icon size={15}/></span><span className="role-label">{role.label}</span><span className="role-meter"><i style={{width: `${(role.starts/maxStarts)*100}%`}}/></span><strong>{role.starts}</strong></button>; })}</div>
        <div className="role-focus"><span className="pulse-orbit"><SelectedIcon size={25}/></span><small>SELECTED ROLE</small><h3>{selected.label}</h3><div><span><strong>{selected.starts}</strong> activations</span><span><strong>{selected.findings}</strong> findings</span></div><p>{selected.id === "worker" ? "One implementation plus eight correction passes—the clearest signal that findings did not converge into complete batches." : `${selected.label} repeatedly exchanged evidence with Toscanini across the execution.`}</p></div>
      </div></article>
      <article className="panel fault-panel"><div className="section-title"><div><small>CONTROL FAILURES</small><h2>Why it kept looping</h2></div><span>5 systemic issues</span></div><div className="problem-list">{problems.map(([title, detail], index) => <div key={title}><span>{String(index+1).padStart(2,"0")}</span><p><strong>{title}</strong>{detail}</p></div>)}</div></article>
    </section>
    <section className="panel timeline-panel"><div className="section-title timeline-title"><div><small>COMMUNICATION TIMELINE</small><h2>What moved between agents</h2></div><div className="filters">{["all","finding","qa","late","risk"].map((value)=><button key={value} className={filter===value?"active":""} onClick={()=>setFilter(value)}>{value}</button>)}</div></div><div className="timeline-list">{visibleMoments.map((moment,index)=><article className={`moment ${moment.kind}`} key={`${moment.at}-${moment.title}`}><div className="moment-time"><strong>{moment.at}</strong><span>{moment.round}</span></div><div className="moment-route"><span>{moment.from}</span><ArrowRight size={15}/><span>{moment.to}</span></div><div className="moment-copy"><strong>{moment.title}</strong><p>{moment.detail}</p></div><span className="moment-index">{String(index+1).padStart(2,"0")}</span></article>)}</div></section>
    <section className="decision-grid"><article className="panel conclusion"><small>EARLIEST AVOIDABLE DIVERGENCE</small><h2>The first checkpoint approved tests without executable client coverage, real contention proof or representative media fixtures.</h2></article><article className="panel correction"><small>NEW CONTROL MODEL</small><div><span>Freeze scope</span><ArrowRight/><span>One complete review batch</span><ArrowRight/><span>Directed fixes</span><ArrowRight/><span>Architecture conformance, when applicable</span></div><p>Directed corrections retain the original independent evidence and verify only the affected findings.</p></article></section>
    <footer><span>Source: Toscanini execution diagnostic · 88 telemetry events</span><span>CLI 0.5.0 · Project 0.4.0</span></footer>
  </main>;
}
