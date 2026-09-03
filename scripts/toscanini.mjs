#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { emitKeypressEvents } from "node:readline";
import { createInterface } from "node:readline/promises";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const workflow = resolve(root, "scripts", "workflow.py");
const builtInAdapters = ["laravel", "spec-kit", "terminal-ui"];
const builtInAgents = [
  "architect",
  "architecture-reviewer",
  "code-reviewer",
  "design-agent",
  "design-reviewer",
  "qa",
  "test-expert",
];

function usage() {
  console.log(`Toscanini

Usage:
  toscanini init [--yes] [--target PATH]
  toscanini adapter add <name> [--target PATH] [--dry-run]
  toscanini adapter remove <name> [--target PATH] [--dry-run]
  toscanini adapter list [--target PATH]
  toscanini agent enable <name> [--target PATH] [--dry-run]
  toscanini agent disable <name> [--target PATH] [--dry-run]
  toscanini agent list [--target PATH]
  toscanini agent select [--target PATH] [--dry-run]
  toscanini ui [--target PATH]
  toscanini inspect [--target PATH]
  toscanini doctor [--target PATH]
  toscanini update [--target PATH] [--dry-run]

Built-in adapters: ${builtInAdapters.join(", ")}
Built-in agents: ${builtInAgents.join(", ")}

The target defaults to the current directory.`);
}

function parse(argv) {
  const positional = [];
  const options = { target: ".", dryRun: false, yes: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--target") options.target = argv[++index];
    else if (value === "--dry-run") options.dryRun = true;
    else if (value === "--yes" || value === "-y") options.yes = true;
    else if (value === "--help" || value === "-h") options.help = true;
    else if (value.startsWith("-")) throw new Error(`Unknown option: ${value}`);
    else positional.push(value);
  }
  if (!options.target) throw new Error("--target requires a path");
  return { positional, options: { ...options, target: resolve(options.target) } };
}

function python(operation, target, extra = [], capture = false) {
  const result = spawnSync("python3", [workflow, operation, "--target", target, ...extra], {
    encoding: "utf8",
    stdio: capture ? ["ignore", "pipe", "pipe"] : "inherit",
  });
  if (result.error) throw result.error;
  if (capture && result.status !== 0) throw new Error(result.stderr || result.stdout || `${operation} failed`);
  return result;
}

function inspect(target) {
  return JSON.parse(python("inspect", target, [], true).stdout);
}

function manifest(target) {
  const path = resolve(target, ".toscanini", "manifest.json");
  if (!existsSync(path)) return null;
  return JSON.parse(readFileSync(path, "utf8"));
}

function configuration(target) {
  const installed = manifest(target);
  if (!installed) throw new Error(`Toscanini is not installed in ${target}. Run 'toscanini init' first.`);
  const current = installed.configuration ?? {};
  return {
    adapters: [...(current.adapters ?? [])],
    agents: [...(current.agents ?? builtInAgents)],
    extensions: [...(current.extensions ?? [])],
  };
}

function installationArgs(config, dryRun = false) {
  const args = [];
  for (const adapter of config.adapters) args.push("--with-adapter", adapter);
  for (const agent of builtInAgents) {
    if (!config.agents.includes(agent)) args.push("--without-agent", agent);
  }
  for (const extension of config.extensions) args.push("--extension", extension);
  if (dryRun) args.push("--dry-run");
  return args;
}

const ansi = {
  reset: "\x1b[0m",
  bold: "\x1b[1m",
  dim: "\x1b[2m",
  cyan: "\x1b[38;5;51m",
  teal: "\x1b[38;5;43m",
  blue: "\x1b[38;5;39m",
  green: "\x1b[38;5;84m",
  amber: "\x1b[38;5;220m",
  slate: "\x1b[38;5;67m",
};

function paint(value, color) {
  return process.env.NO_COLOR ? value : `${color}${value}${ansi.reset}`;
}

function fit(value, width) {
  const plain = value.replace(/\x1b\[[0-9;]*m/g, "");
  if (plain.length <= width) return value + " ".repeat(width - plain.length);
  return plain.slice(0, Math.max(0, width - 1)) + "…";
}

function panel(title, lines, width) {
  const inner = Math.max(20, width - 2);
  const top = `╭─ ${title} ${"─".repeat(Math.max(0, inner - title.length - 2))}╮`;
  return [paint(top, ansi.slate), ...lines.map((line) => `${paint("│", ansi.slate)}${fit(` ${line}`, inner)}${paint("│", ansi.slate)}`), paint(`╰${"─".repeat(inner)}╯`, ansi.slate)];
}

function roleKey(value = "") {
  return value.replaceAll("_", "-").toLowerCase();
}

function localTelemetry(target) {
  const runtime = resolve(target, ".toscanini", "runtime");
  let state = { agents: {} };
  let events = [];
  try {
    state = JSON.parse(readFileSync(resolve(runtime, "state.json"), "utf8"));
  } catch {}
  try {
    events = readFileSync(resolve(runtime, "events.jsonl"), "utf8")
      .trim().split("\n").filter(Boolean).slice(-6).map((line) => JSON.parse(line));
  } catch {}
  return { agents: state.agents ?? {}, events };
}

function telemetryState(event) {
  const value = event?.state?.toUpperCase() || "READY";
  return value === "COMPLETED" ? "DONE" : value;
}

function terminalSnapshot(target, frame = 0) {
  const installed = manifest(target);
  if (!installed) throw new Error(`Toscanini is not installed in ${target}. Run 'toscanini init' first.`);
  const config = installed.configuration ?? { adapters: [], agents: builtInAgents, extensions: [] };
  if (!config.adapters?.includes("terminal-ui")) throw new Error("The terminal-ui adapter is disabled. Run 'toscanini adapter add terminal-ui'.");
  const detected = inspect(target);
  const width = Math.max(58, Math.min(process.stdout.columns || 92, 112));
  const orbit = ["◐", "◓", "◑", "◒"][frame % 4];
  const adapters = config.adapters.filter((item) => item !== "terminal-ui");
  const telemetry = localTelemetry(target);
  const telemetryByRole = new Map(Object.values(telemetry.agents).map((event) => [roleKey(event.role), event]));
  const activeMain = telemetryByRole.get("orchestrator");
  const agentLines = config.agents.map((agent, index) => {
    const connector = index === config.agents.length - 1 ? "└─" : "├─";
    const event = telemetryByRole.get(roleKey(agent));
    const state = event ? telemetryState(event) : "READY";
    const active = state === "ACTIVE";
    const color = active ? ansi.cyan : ["READY", "DONE"].includes(state) ? ansi.green : ansi.amber;
    return `${paint(connector, ansi.slate)} ${paint(active ? "◆" : "◇", active ? ansi.cyan : ansi.teal)} ${agent.padEnd(24)} ${paint(state, color)}`;
  });
  const extraTelemetry = Object.values(telemetry.agents).filter((event) => {
    const role = roleKey(event.role);
    return role !== "orchestrator" && !config.agents.some((agent) => roleKey(agent) === role);
  });
  for (const event of extraTelemetry) {
    const state = telemetryState(event);
    const active = state === "ACTIVE";
    agentLines.push(`${paint("└─", ansi.slate)} ${paint(active ? "◆" : "◇", active ? ansi.cyan : ansi.teal)} ${roleKey(event.role).padEnd(24)} ${paint(state, active ? ansi.cyan : ansi.green)}`);
  }
  const verify = detected.verification.canonical ?? "not configured";
  const stack = detected.packageManagers.join(" · ") || "generic";
  const output = [];
  output.push(paint(`  T O S C A N I N I   ${orbit}   COMMAND MATRIX`, ansi.cyan));
  output.push(paint(`  ${"━".repeat(Math.max(10, width - 4))}`, ansi.blue));
  output.push(...panel("SYSTEM", [
    `${paint("PROJECT", ansi.dim)}  ${basename(target)}`,
    `${paint("ROOT", ansi.dim)}     ${target}`,
    `${paint("STACK", ansi.dim)}    ${stack}`,
    `${paint("VERIFY", ansi.dim)}   ${verify === "not configured" ? paint(verify, ansi.amber) : paint(verify, ansi.green)}`,
  ], width));
  output.push(...panel("ORCHESTRATION NETWORK", [
    `${" ".repeat(8)}${paint("╭──────────────╮", ansi.cyan)}`,
    `${" ".repeat(8)}${paint("│ ORCHESTRATOR │", ansi.cyan)}  ${paint(activeMain ? telemetryState(activeMain) : "CONFIGURED", activeMain ? ansi.cyan : ansi.green)}`,
    `${" ".repeat(8)}${paint("╰──────┬───────╯", ansi.cyan)}`,
    `${" ".repeat(15)}${paint("│", ansi.slate)}`,
    ...agentLines,
  ], width));
  output.push(...panel("MODULES", [
    `${paint("CORE", ansi.cyan)}          ${paint("ENABLED", ansi.green)}`,
    `${paint("INTERFACE", ansi.dim)}     terminal-ui`,
    `${paint("ADAPTERS", ansi.dim)}      ${adapters.length ? adapters.join(" · ") : "none"}`,
    `${paint("EXTENSIONS", ansi.dim)}    ${config.extensions?.length ? config.extensions.map((item) => basename(item)).join(" · ") : "none"}`,
  ], width));
  const activity = telemetry.events.length
    ? [
        `${paint("●", ansi.green)} Local workflow telemetry`,
        ...telemetry.events.map((event) => {
          const time = event.timestamp?.slice(11, 19) || "--:--:--";
          return `${paint(time, ansi.dim)} ${paint(roleKey(event.role), ansi.cyan)} · ${event.summary}`;
        }),
      ]
    : [
        `${paint("○", ansi.amber)} Configuration view`,
        `${paint("INFO", ansi.dim)} Waiting for an instrumented Toscanini task…`,
      ];
  output.push(...panel("ACTIVITY LINK", activity, width));
  output.push(paint("  [q] exit   [r] refresh   Toscanini", ansi.dim));
  return output.join("\n");
}

async function ui(target) {
  if (!process.stdout.isTTY) {
    console.log(terminalSnapshot(target));
    return;
  }
  let frame = 0;
  const draw = () => {
    process.stdout.write(`\x1b[2J\x1b[H${terminalSnapshot(target, frame++)}\n`);
  };
  draw();
  process.stdin.setRawMode?.(true);
  process.stdin.resume();
  process.stdin.setEncoding("utf8");
  const timer = setInterval(draw, 700);
  await new Promise((done) => {
    process.stdin.on("data", (key) => {
      if (key === "q" || key === "Q" || key === "\u0003") done();
      if (key === "r" || key === "R") draw();
    });
  });
  clearInterval(timer);
  process.stdin.setRawMode?.(false);
  process.stdin.pause();
  process.stdout.write("\x1b[2J\x1b[H");
}

async function confirm(rl, question, defaultValue) {
  const suffix = defaultValue ? " [Y/n] " : " [y/N] ";
  const answer = (await rl.question(question + suffix)).trim().toLowerCase();
  if (!answer) return defaultValue;
  return answer === "y" || answer === "yes";
}

async function checklist(title, choices, enabled) {
  if (!process.stdin.isTTY || !process.stdout.isTTY || !process.stdin.setRawMode) {
    throw new Error("Interactive selection requires a terminal. Use 'agent enable' or 'agent disable' in non-interactive environments.");
  }
  const selected = new Set(enabled);
  let cursor = 0;
  const render = () => {
    const rows = choices.map((choice, index) => {
      const pointer = index === cursor ? paint("›", ansi.cyan) : " ";
      const mark = selected.has(choice) ? paint("[✓]", ansi.green) : paint("[ ]", ansi.dim);
      return `  ${pointer} ${mark} ${choice}`;
    });
    process.stdout.write(`\x1b[2J\x1b[H${paint(title, ansi.bold)}\n\n${rows.join("\n")}\n\n${paint("↑/↓ move   space toggle   a all   enter confirm   q cancel", ansi.dim)}\n`);
  };
  emitKeypressEvents(process.stdin);
  process.stdin.setRawMode(true);
  process.stdin.resume();
  render();
  return new Promise((resolveSelection, rejectSelection) => {
    const finish = (value, error) => {
      process.stdin.off("keypress", onKey);
      process.stdin.setRawMode(false);
      process.stdin.pause();
      process.stdout.write("\x1b[2J\x1b[H");
      if (error) rejectSelection(error);
      else resolveSelection(value);
    };
    const onKey = (_input, key) => {
      if (key.ctrl && key.name === "c") return finish(null, new Error("Selection cancelled."));
      if (key.name === "up") cursor = (cursor - 1 + choices.length) % choices.length;
      else if (key.name === "down") cursor = (cursor + 1) % choices.length;
      else if (key.name === "space") selected.has(choices[cursor]) ? selected.delete(choices[cursor]) : selected.add(choices[cursor]);
      else if (key.name === "a") selected.size === choices.length ? selected.clear() : choices.forEach((choice) => selected.add(choice));
      else if (key.name === "return") return finish(choices.filter((choice) => selected.has(choice)));
      else if (key.name === "q" || key.name === "escape") return finish([...enabled]);
      render();
    };
    process.stdin.on("keypress", onKey);
  });
}

async function init(target, options) {
  const detected = inspect(target);
  const installed = manifest(target)?.configuration;
  const adapters = [...(installed?.adapters ?? [])];
  const agents = [...(installed?.agents ?? builtInAgents)];
  const extensions = [...(installed?.extensions ?? [])];
  console.log(`\nToscanini setup\nTarget: ${target}`);
  console.log(`Detected: ${[
    detected.laravel.detected ? `Laravel ${detected.laravel.framework ?? ""}`.trim() : null,
    detected.specKit ? "Spec Kit" : null,
    ...detected.packageManagers,
  ].filter(Boolean).join(", ") || "generic repository"}\n`);

  if (options.yes || !process.stdin.isTTY) {
    if (detected.laravel.detected && !adapters.includes("laravel")) adapters.push("laravel");
    if (detected.specKit && !adapters.includes("spec-kit")) adapters.push("spec-kit");
  } else {
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    try {
      const laravel = await confirm(rl, "Enable the Laravel adapter?", adapters.includes("laravel") || detected.laravel.detected);
      const specKit = await confirm(rl, "Enable the Spec Kit adapter?", adapters.includes("spec-kit") || detected.specKit);
      const terminalUi = await confirm(rl, "Enable the terminal command center?", adapters.includes("terminal-ui"));
      adapters.splice(0, adapters.length, ...[...(laravel ? ["laravel"] : []), ...(specKit ? ["spec-kit"] : []), ...(terminalUi ? ["terminal-ui"] : [])]);
    } finally {
      rl.close();
    }
    const selectedAgents = await checklist("Choose specialist agents", builtInAgents, agents);
    agents.splice(0, agents.length, ...selectedAgents);
  }

  const config = { adapters: [...new Set(adapters)].sort(), agents, extensions };
  if (!options.yes && process.stdin.isTTY) {
    console.log("\nPlanned changes:");
    const preview = python("install", target, installationArgs(config, true), true);
    console.log(preview.stdout.trim());
    const rl = createInterface({ input: process.stdin, output: process.stdout });
    try {
      if (!(await confirm(rl, "Apply this configuration?", true))) return;
    } finally {
      rl.close();
    }
  }
  const extra = installationArgs(config, options.dryRun);
  const result = python("install", target, extra);
  if (result.status !== 0) process.exitCode = result.status;
}

function reconfigure(target, type, action, name, dryRun) {
  const config = configuration(target);
  if (type === "adapter") {
    if (!builtInAdapters.includes(name)) throw new Error(`Unknown adapter: ${name}`);
    const selected = new Set(config.adapters);
    action === "add" ? selected.add(name) : selected.delete(name);
    config.adapters = [...selected].sort();
  } else {
    if (!builtInAgents.includes(name)) throw new Error(`Unknown agent: ${name}`);
    const selected = new Set(config.agents);
    action === "enable" ? selected.add(name) : selected.delete(name);
    config.agents = builtInAgents.filter((agent) => selected.has(agent));
  }
  const result = python("install", target, installationArgs(config, dryRun));
  if (result.status !== 0) process.exitCode = result.status;
}

async function selectAgents(target, dryRun) {
  const config = configuration(target);
  config.agents = await checklist("Choose specialist agents", builtInAgents, config.agents);
  const result = python("install", target, installationArgs(config, dryRun));
  if (result.status !== 0) process.exitCode = result.status;
}

async function main() {
  const { positional, options } = parse(process.argv.slice(2));
  if (options.help || positional.length === 0) return usage();
  const [command, action, name] = positional;
  if (command === "init") return init(options.target, options);
  if (command === "ui") return ui(options.target);
  if (command === "inspect" || command === "doctor" || command === "update") {
    const extra = options.dryRun ? ["--dry-run"] : [];
    const result = python(command, options.target, extra);
    if (result.status !== 0) process.exitCode = result.status;
    return;
  }
  if (command === "adapter" && action === "list") {
    const current = manifest(options.target)?.configuration?.adapters ?? [];
    for (const adapter of builtInAdapters) console.log(`${current.includes(adapter) ? "enabled " : "disabled"}  ${adapter}`);
    return;
  }
  if (command === "agent" && action === "list") {
    const current = new Set(configuration(options.target).agents);
    for (const agent of builtInAgents) console.log(`${current.has(agent) ? "enabled " : "disabled"}  ${agent}`);
    return;
  }
  if (command === "agent" && action === "select") return selectAgents(options.target, options.dryRun);
  if (command === "adapter" && ["add", "remove"].includes(action) && name) return reconfigure(options.target, command, action, name, options.dryRun);
  if (command === "agent" && ["enable", "disable"].includes(action) && name) return reconfigure(options.target, command, action, name, options.dryRun);
  throw new Error(`Invalid command: ${positional.join(" ")}`);
}

main().catch((error) => {
  console.error(`toscanini: ${error.message}`);
  process.exitCode = 1;
});
