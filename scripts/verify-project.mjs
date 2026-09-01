import { readFile } from "node:fs/promises";

const contract = await readFile(new URL("../contracts/artifact_court.py", import.meta.url), "utf8");
const client = await readFile(new URL("../src/lib/genlayer.ts", import.meta.url), "utf8");
const requiredMethods = [
  "create_release",
  "add_artifact",
  "register_consumer",
  "lock_release",
  "open_challenge",
  "submit_evidence",
  "adjudicate",
  "submit_remediation",
  "approve_remediation",
  "verify_remediation",
  "activate_unchallenged",
  "refund_timed_out",
];

for (const method of requiredMethods) {
  if (!contract.includes(`def ${method}`)) throw new Error(`Contract method missing: ${method}`);
  if (!client.includes(`"${method}"`)) throw new Error(`Frontend write missing: ${method}`);
}

if (!contract.includes("gl.vm.run_nondet_unsafe")) throw new Error("Consensus execution missing");
if (!contract.includes("gl.nondet.web.render")) throw new Error("Validator web re-fetch missing");
if (!client.includes("waitForTransactionReceipt")) throw new Error("Receipt confirmation missing");

console.log("ArtifactCourt verification passed: contract, consensus, settlement, and frontend bindings align.");

