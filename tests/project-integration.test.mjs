import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const contract = await readFile(new URL("../contracts/artifact_court.py", import.meta.url), "utf8");
const client = await readFile(new URL("../src/lib/genlayer.ts", import.meta.url), "utf8");
const app = await readFile(new URL("../src/App.tsx", import.meta.url), "utf8");

test("contract uses consequential non-deterministic consensus", () => {
  for (const signal of [
    "gl.nondet.web.render",
    "gl.nondet.web.get",
    "gl.nondet.exec_prompt",
    "gl.vm.run_nondet_unsafe",
    "validator_fn",
    "_apply_verdict",
    "_settle",
  ]) assert.ok(contract.includes(signal), signal);
});

test("frontend reads, writes, and waits for accepted receipts", () => {
  for (const signal of [
    "readContract",
    "writeContract",
    "waitForTransactionReceipt",
    'status: "ACCEPTED"',
    'write(client, "adjudicate"',
    'write(client, "verify_remediation"',
    'write(client, "refund_timed_out"',
  ]) assert.ok(client.includes(signal), signal);
  assert.ok(app.includes("writes.openChallenge"));
  assert.ok(app.includes("writes.submitEvidence"));
});

test("security invariants remain visible in source", () => {
  assert.ok(contract.includes("Challenger bond must exactly match the maintainer bond"));
  assert.ok(contract.includes("SIDE_EVIDENCE_BUDGET"));
  assert.ok(contract.includes("Only the affected consumer owner may approve remediation"));
  assert.ok(contract.includes("Maintainer cannot own a consumer compatibility constraint"));
  assert.ok(contract.includes('"outcome": "UNRESOLVED"'));
  assert.ok(contract.includes("Resolution timed out; use the refund path"));
});
