# Judge Walkthrough

## Hard gate 1: meaningful Intelligent Contract

Open `contracts/artifact_court.py` and inspect `_adjudicate` and `verify_remediation`.

- `gl.nondet.web.get` fetches immutable GitHub raw bytes for artifacts, party evidence, constraints, and remediation.
- `_fetch_anchored` verifies each observed SHA-256 against its on-chain declaration before text reaches a prompt.
- `gl.nondet.exec_prompt` classifies compatibility and remediation satisfaction.
- `gl.vm.run_nondet_unsafe` makes each validator run the assessment independently.
- `_adjudication_consensus_matches` requires the exact remediation text; `_remediation_consensus_matches` requires the stored requirement digest.
- `_apply_verdict` and `_settle` bind consensus to activation, rejection, and bond delivery.

The non-deterministic result is therefore consequential, not educational text or a detached report.

## Hard gate 2: real app-to-contract workflow

Open `src/lib/genlayer.ts` and `src/App.tsx`.

- Reads: `list_case_ids`, `get_case`, `get_artifact`, and `get_dependency`.
- Writes: all thirteen public transaction methods are bound to visible workflow actions.
- Confirmation: every write waits for an `ACCEPTED` GenLayer receipt before refreshing authoritative state.
- Wallet roles: maintainer, challenger, and consumer actions use the connected wallet; role checks remain contract-enforced.

## Regression evidence

Run `npm test` for behavioral tests covering:

1. full-commit provenance;
2. deterministic graph hashing;
3. independent evidence budgets;
4. immutable semantic URLs and byte-level digest binding;
5. exact bond matching;
6. compatible/incompatible payout routes;
7. exact remediation requirement consensus;
8. consumer-owned remediation approval;
9. unresolved timeout refunds;
10. frontend read/write and receipt bindings.
