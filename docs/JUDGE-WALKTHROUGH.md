# Judge Walkthrough

## Hard gate 1: meaningful Intelligent Contract

Open `contracts/artifact_court.py` and inspect `_adjudicate` and `verify_remediation`.

- `gl.nondet.web.get` fetches immutable artifact bytes and evidence content, verifying SHA-256 digests.
- `gl.nondet.web.render` fetches consumer constraints for semantic comparison.
- `gl.nondet.exec_prompt` classifies compatibility and remediation satisfaction.
- `gl.vm.run_nondet_unsafe` makes each validator run the assessment independently.
- `_reproduce_remediation_requirement` re-derives the exact remediation from content-bound evidence before settlement.
- `_apply_verdict` and `_settle` bind consensus to activation, rejection, and bond delivery.

The non-deterministic result is therefore consequential, not educational text or a detached report.

## Hard gate 2: real app-to-contract workflow

Open `src/lib/genlayer.ts` and `src/App.tsx`.

- Reads: `list_case_ids`, `get_case`, `get_artifact`, `get_dependency`, and `get_evidence`.
- Writes: all thirteen public transaction methods are bound to visible workflow actions.
- Confirmation: every write waits for an `ACCEPTED` GenLayer receipt before refreshing authoritative state.
- Wallet roles: maintainer, challenger, and consumer actions use the connected wallet; role checks remain contract-enforced.

## Regression evidence

Run `npm test` for behavioral tests covering:

1. full-commit provenance;
2. deterministic graph hashing;
3. content-bound evidence digests;
4. evidence digest mismatch detection;
5. independent evidence budgets;
6. exact bond matching;
7. compatible/incompatible payout routes;
8. consumer-owned remediation approval;
9. remediation requirement reproduction;
10. reproduction mismatch detection;
11. unresolved timeout refunds;
12. frontend read/write and receipt bindings.

