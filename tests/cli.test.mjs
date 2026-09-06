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

test("version reports the CLI and project installation state", () => {
  assert.equal(run(["--version"]).trim(), "0.7.0");

  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  assert.match(run(["version", "--target", target]), /Project: not installed[\s\S]*Status: Toscanini is not installed/);

  run(["init", "--target", target, "--yes"]);
  const manifestPath = resolve(target, ".toscanini/manifest.json");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  manifest.version = "0.5.0";
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + "\n");

  assert.match(run(["version", "--target", target]), /Toscanini CLI: 0\.7\.0[\s\S]*Project: 0\.5\.0[\s\S]*Status: project update required/);
  run(["update", "--target", target]);
  assert.match(run(["version", "--target", target]), /Toscanini CLI: 0\.7\.0[\s\S]*Project: 0\.7\.0[\s\S]*Status: current/);
});

test("analyze runs only enabled adapter analyzers", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  writeFileSync(resolve(target, "artisan"), "");
  writeFileSync(resolve(target, "composer.json"), JSON.stringify({ require: { "laravel/framework": "^13.0" } }));
  run(["init", "--target", target, "--yes"]);
  const output = run(["analyze", "--target", target]);
  assert.match(output, /Laravel: enabled; detected/);
  assert.match(output, /PASS\s+Laravel framework \(\^13\.0\)/);
  assert.match(output, /MISSING \[recommended\] Laravel Boost/);
  assert.match(output, /MISSING \[recommended\] Laravel Pint/);
  assert.doesNotMatch(output, /Spec Kit:/);
});

test("Spec Kit analyzer reports an enabled but missing installation", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["adapter", "add", "spec-kit", "--target", target]);
  const output = run(["analyze", "--target", target]);
  assert.match(output, /Spec Kit: enabled; not detected/);
  assert.match(output, /MISSING \[required\] Spec Kit installation/);
});

test("Laravel Boost policy is explicit and retained", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  writeFileSync(resolve(target, "artisan"), "");
  writeFileSync(resolve(target, "composer.json"), JSON.stringify({ require: { "laravel/framework": "^13.0" }, scripts: { verify: "echo ok" } }));
  run(["init", "--target", target, "--yes"]);
  assert.equal(run(["laravel", "boost", "--target", target]).trim(), "optional");
  run(["laravel", "boost", "required", "--target", target]);
  const manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.equal(manifest.configuration.laravelBoost, "required");
  assert.throws(() => run(["verify", "--target", target]), /BLOCKED: Laravel Boost is required/);
});

test("verify blocks a Spec Kit project without an exact run contract", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  mkdirSync(resolve(target, ".specify"));
  writeFileSync(resolve(target, "package.json"), JSON.stringify({ scripts: { verify: "echo ok" } }));
  run(["init", "--target", target, "--yes"]);
  assert.throws(() => run(["verify", "--target", target]), /--run-id is required/);
});

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
  assert.equal(manifest.configuration.agents.includes("test-analyst"), true);
  run(["agent", "disable", "test-analyst", "--target", target]);
  const updated = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.equal(updated.configuration.agents.includes("test-analyst"), false);
});

test("agent list shows every available agent and its current state", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["agent", "disable", "qa", "--target", target]);
  const output = run(["agent", "list", "--target", target]);
  assert.match(output, /enabled\s+architect/);
  assert.match(output, /disabled\s+qa/);
  assert.match(output, /enabled\s+test-analyst/);
  for (const agent of ["architect", "architecture-reviewer", "code-reviewer", "design-agent", "design-reviewer", "qa", "test-analyst"]) {
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

test("assurance defaults to standard and can be changed", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  assert.equal(run(["assurance", "--target", target]).trim(), "standard");
  run(["assurance", "fast", "--target", target]);
  let manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.equal(manifest.configuration.assurance, "fast");
  assert.match(readFileSync(resolve(target, "AGENTS.md"), "utf8"), /Default assurance: fast/);
  run(["assurance", "critical", "--target", target]);
  manifest = JSON.parse(readFileSync(resolve(target, ".toscanini/manifest.json"), "utf8"));
  assert.equal(manifest.configuration.assurance, "critical");
});

test("terminal UI is an optional adapter with a truthful snapshot", () => {
  const target = mkdtempSync(resolve(tmpdir(), "toscanini-cli-"));
  run(["init", "--target", target, "--yes"]);
  run(["adapter", "add", "terminal-ui", "--target", target]);
  execFileSync("python3", [resolve(target, ".toscanini/bin/toscanini-event.py"), "--agent", "worker", "--role", "worker", "--event", "started", "--state", "active", "--summary", "Implementing the task API"], { cwd: target });
  const output = run(["ui", "--target", target]);
  assert.match(output, /COMMAND MATRIX/);
  assert.match(output, /ORCHESTRATION NETWORK/);
  assert.match(output, /ASSURANCE\s+STANDARD/);
  assert.match(output, /Local workflow telemetry/);
  assert.match(output, /Implementing the task API/);
});
