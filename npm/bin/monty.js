#!/usr/bin/env node
// The monty launcher. The engine is Python; npm is the doorway.
//
// What this does, in order: find uv (or install it once, from the official
// script, saying so); then exec `uv tool run --from <engine> monty …`. uvx
// caches the resolved environment, so after the first run this shim costs
// ~50ms. No postinstall — everything happens lazily, visibly, on first use.
//
// MONTY_FROM overrides the engine source (development, forks, pins).

"use strict";
const { spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const { join } = require("node:path");
const os = require("node:os");

const ENGINE =
  process.env.MONTY_FROM ||
  require("../package.json").montology.engine;

function findUv() {
  const candidates = [
    process.env.MONTY_UV,
    "uv",
    join(os.homedir(), ".local", "bin", "uv"),
    join(os.homedir(), ".cargo", "bin", "uv"),
  ].filter(Boolean);
  for (const uv of candidates) {
    const probe = spawnSync(uv, ["--version"], { stdio: "ignore" });
    if (probe.status === 0) return uv;
  }
  return null;
}

function installUv() {
  process.stderr.write("monty: uv not found — installing it once (astral.sh/uv)…\n");
  const result =
    process.platform === "win32"
      ? spawnSync("powershell", ["-ExecutionPolicy", "ByPass", "-c",
          "irm https://astral.sh/uv/install.ps1 | iex"], { stdio: "inherit" })
      : spawnSync("sh", ["-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
          { stdio: "inherit" });
  if (result.status !== 0) {
    process.stderr.write(
      "monty: could not install uv. Repair: install it yourself " +
      "(https://docs.astral.sh/uv/getting-started/installation/) and rerun.\n");
    process.exit(1);
  }
  const uv = findUv();
  if (!uv) {
    const hint = join(os.homedir(), ".local", "bin");
    process.stderr.write(
      `monty: uv installed but not on PATH yet. Repair: add ${hint} to PATH ` +
      "(restart the terminal) and rerun.\n");
    process.exit(1);
  }
  return uv;
}

const uv = findUv() || installUv();
const run = spawnSync(
  uv,
  ["tool", "run", "--from", ENGINE, "monty", ...process.argv.slice(2)],
  { stdio: "inherit" },
);
process.exit(run.status === null ? 1 : run.status);
