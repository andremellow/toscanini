import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";

const cli = resolve("scripts/toscanini.mjs");

function run(args, cwd) {
  return execFileSync(process.execPath, [cli, ...args], { encoding: "utf8", cwd });
}

test("init defaults to the current directory", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--yes"], target);
  const manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.equal(manifest.configuration.adapters.length, 0);
});

test("non-interactive init enables detected adapters", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  mkdirSync(resolve(target, ".specify"));
  writeFileSync(resolve(target, "artisan"), "");
  writeFileSync(resolve(target, "composer.json"), JSON.stringify({ require: { "laravel/framework": "^13.0" } }));
  run(["init", "--target", target, "--yes"]);
  const manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.deepEqual(manifest.configuration.adapters, ["laravel", "spec-kit"]);
});

test("adapters can be added and removed incrementally", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["adapter", "add", "spec-kit", "--target", target]);
  let manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.deepEqual(manifest.configuration.adapters, ["spec-kit"]);
  run(["adapter", "add", "laravel", "--target", target]);
  manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.deepEqual(manifest.configuration.adapters, ["laravel", "spec-kit"]);
  run(["adapter", "remove", "spec-kit", "--target", target]);
  manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.deepEqual(manifest.configuration.adapters, ["laravel"]);
});

test("agents can be disabled without changing adapters", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["adapter", "add", "spec-kit", "--target", target]);
  run(["agent", "disable", "design-agent", "--target", target]);
  const manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.deepEqual(manifest.configuration.adapters, ["spec-kit"]);
  assert.equal(manifest.configuration.agents.includes("design-agent"), false);
  assert.equal(manifest.configuration.agents.includes("test-expert"), true);
  run(["agent", "disable", "test-expert", "--target", target]);
  const updated = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.equal(updated.configuration.agents.includes("test-expert"), false);
});

test("agent list shows every available agent and its current state", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["agent", "disable", "qa", "--target", target]);
  const output = run(["agent", "list", "--target", target]);
  assert.match(output, /enabled\s+architect/);
  assert.match(output, /disabled\s+qa/);
  assert.match(output, /enabled\s+test-expert/);
  for (const agent of ["architect", "architecture-reviewer", "code-reviewer", "design-agent", "design-reviewer", "qa", "test-expert"]) {
    assert.match(output, new RegExp(agent));
  }
});

test("running init again preserves an installed configuration", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["adapter", "add", "spec-kit", "--target", target]);
  run(["agent", "disable", "design-agent", "--target", target]);
  run(["init", "--target", target, "--yes"]);
  const manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.deepEqual(manifest.configuration.adapters, ["spec-kit"]);
  assert.equal(manifest.configuration.agents.includes("design-agent"), false);
});

test("terminal UI is an optional adapter with a truthful snapshot", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["adapter", "add", "terminal-ui", "--target", target]);
  execFileSync("python3", [resolve(target, ".toscanini/bin/toscanini-event.py"), "--agent", "worker", "--role", "worker", "--event", "started", "--state", "active", "--summary", "Implementing the task API"], { cwd: target });
  const output = run(["ui", "--target", target]);
  assert.match(output, /COMMAND MATRIX/);
  assert.match(output, /ORCHESTRATION NETWORK/);
  assert.match(output, /Local workflow telemetry/);
  assert.match(output, /Implementing the task API/);
});
