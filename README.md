# ArtifactCourt

**Consensus-backed release integrity, compatibility adjudication, and bonded remediation on GenLayer.**

ArtifactCourt turns a software release candidate into an auditable on-chain case. A maintainer binds a full Git commit, immutable artifact URLs, declared SHA-256 digests, and consumer-owned compatibility constraints. Every evidence item submitted by either party carries a content-bound SHA-256 digest that validators verify against fetched bytes. A challenger can match the maintainer's bond and submit counter-evidence. GenLayer validators then re-fetch every evidence partition, verify content integrity, and produce a verdict that directly controls activation, remediation ownership, rejection, or refunds. Before conditional settlement can proceed, validators independently reproduce the exact remediation requirement from the content-bound evidence.

> ArtifactCourt does not claim that software is bug-free. It decides whether one exact release revision satisfies one exact locked dependency graph under public evidence available at adjudication time.

## Live release

| Surface | Value |
| --- | --- |
| Application | [https://artifact-court.vercel.app](https://artifact-court.vercel.app) |
| Network | GenLayer Bradbury testnet |
| Contract | [`0x2e6b...24D2`](https://explorer-bradbury.genlayer.com/address/0x2e6b043D7A204D9611D30fFeE3eb83E4EAbc24D2) |
| Deployment transaction | [`0x5887...b2f8`](https://explorer-bradbury.genlayer.com/tx/0x5887dcded30d83c31b53dbff98fb2f564fa139ce4cbb70d517ec6b79fea7b2f8) |
| Chain | `testnet-bradbury` |

Bradbury GEN is faucet-issued test currency with no promised monetary value.

## Why GenLayer is essential

A deterministic contract can compare hashes, enforce deadlines, and account for bonds, but it cannot determine whether an API migration, schema change, binary, or adapter actually satisfies prose compatibility constraints spread across public sources. ArtifactCourt uses GenLayer-native non-deterministic execution for that consequential decision:

1. `gl.nondet.web.get(...)` retrieves immutable artifact bytes and verifies their locked SHA-256 digests.
2. `gl.nondet.web.get(...)` independently re-fetches maintainer and challenger evidence, verifying each item's content-bound SHA-256 digest against fetched bytes.
3. `gl.nondet.web.render(...)` independently re-fetches consumer constraints.
4. Each side receives a separate 7,000-character budget; one party cannot crowd the other out of validator context.
5. `gl.nondet.exec_prompt(...)` returns a strict compatibility verdict schema.
6. `gl.vm.run_nondet_unsafe(...)` requires validators to independently reproduce the verdict and affected consumer.
7. Before conditional settlement, validators reproduce the exact remediation requirement from content-bound evidence and confirm it matches the stored value.
8. The agreed result changes contract state and settles matched bonds.

The React app calls the deployed contract through `genlayer-js`, waits for an `ACCEPTED` transaction receipt, and re-reads authoritative state after every write.

## Workflow

```mermaid
flowchart LR
    A[Create bonded draft] --> B[Attach immutable artifacts]
    B --> C[Consumers register constraints]
    C --> D[Lock canonical graph digest]
    D -->|No challenge| E[Activate and refund maintainer]
    D -->|Matched bond| F[Reserved evidence windows]
    F --> G[Validators re-fetch all partitions]
    G -->|COMPATIBLE| H[Activate; maintainer wins pot]
    G -->|INCOMPATIBLE| I[Reject; challenger wins pot]
    G -->|CONDITIONAL| J[Consumer-owned remediation]
    J --> K[Validator remediation re-check]
    K --> H
    K --> I
    G -->|UNRESOLVED| L[Retry-safe pending state]
    L --> G
    L -->|Timeout| M[Refund both bonds]
    J -->|Timeout| M
```

## State machine

| State | Meaning | Allowed next states |
| --- | --- | --- |
| `DRAFT` | Maintainer and consumers build the evidence graph | `LOCKED`, `CANCELLED` |
| `LOCKED` | Graph digest is immutable; challenge window is open | `CHALLENGED`, `ACTIVATED` |
| `CHALLENGED` | Equal bonds are locked; each party owns a reserved evidence partition | `ACTIVATED`, `REJECTED`, `CONDITIONAL`, `UNRESOLVED`, `REFUNDED` |
| `UNRESOLVED` | Evidence was unavailable, contradictory, or insufficient | retry adjudication, `REFUNDED` |
| `CONDITIONAL` | One registered consumer owns a concrete remediation gate | `ACTIVATED`, `REJECTED`, `REFUNDED` |
| `ACTIVATED` | Compatible or unchallenged release; accounting closed | terminal |
| `REJECTED` | Incompatible release; accounting closed | terminal |
| `REFUNDED` | Consensus/remediation timed out; principals returned | terminal |
| `CANCELLED` | Maintainer cancelled an unlocked draft | terminal |

## Contract invariants

- **Immutable provenance:** revision URLs require a full 40-character Git commit; artifact URLs must contain the same revision.
- **Verified artifact bytes:** validators fetch each canonical raw artifact and compare its observed SHA-256 with the locked declaration.
- **Canonical evidence graph:** artifact declarations and sorted consumer constraints are committed to a SHA-256 graph digest.
- **Consumer ownership:** each constraint is bound to the wallet that registered it.
- **Independent constraints:** the maintainer cannot register or approve a consumer constraint for their own release.
- **Symmetric exposure:** challenger bond must exactly equal the maintainer bond.
- **Content-bound evidence:** every party evidence item carries a declared SHA-256 digest; validators verify fetched bytes match and fail closed on any mismatch.
- **Balanced context:** maintainer and challenger have independent evidence budgets.
- **Fresh evidence:** validators fetch sources during adjudication and remediation verification.
- **Fail-closed uncertainty:** required fetch failure produces `UNRESOLVED`, not a guessed winner.
- **Fail-closed evidence integrity:** evidence digest mismatch produces `UNRESOLVED`, preventing tampered evidence from influencing the verdict.
- **Fail-closed remediation:** unavailable remediation evidence preserves the conditional state and both bonds.
- **Reproduced remediation requirement:** before conditional settlement, validators independently re-derive the exact remediation requirement from content-bound evidence and confirm it matches the stored value.
- **Consumer-owned remediation:** only the affected consumer wallet can approve a conditional fix.
- **Pull-safe finality:** terminal settlement zeroes stored liabilities before emitting transfers.
- **Liveness:** unresolved or conditional cases refund both principals after a fixed timeout.

## Project structure

```text
artifact-court/
|-- contracts/
|   `-- artifact_court.py       # Intelligent Contract and settlement state machine
|-- deployments/
|   `-- bradbury.json           # Machine-readable production release record
|-- docs/
|   |-- ARCHITECTURE.md         # Trust boundaries and adjudication design
|   |-- DEPLOYMENT.md           # Reproducible deployment procedure
|   `-- JUDGE-WALKTHROUGH.md    # Reviewer verification path
|-- scripts/
|   `-- verify-project.mjs      # Contract/client binding verification
|-- src/
|   |-- lib/genlayer.ts         # Bradbury read/write clients and receipts
|   |-- App.tsx                 # Public docket and complete transaction workflow
|   |-- styles.css              # Responsive ArtifactCourt visual system
|   `-- types.ts                # Authoritative frontend read model
|-- tests/
|   |-- project-integration.test.mjs
|   `-- test_contract_behavior.py
|-- SECURITY.md
|-- package.json
`-- vercel.json
```

## Public contract methods

### Writes

`create_release`, `add_artifact`, `register_consumer`, `lock_release`, `cancel_draft`, `open_challenge`, `submit_evidence`, `adjudicate`, `submit_remediation`, `approve_remediation`, `verify_remediation`, `activate_unchallenged`, `refund_timed_out`

### Views

`get_case`, `get_artifact`, `get_dependency`, `get_evidence`, `list_case_ids`, `get_policy`

## Local verification

```bash
npm ci
npm test
npm run verify
npm run build
python -m py_compile contracts/artifact_court.py
python -m genvm_linter.cli check contracts/artifact_court.py
```

Current regression coverage includes full-commit binding, graph determinism, content-bound evidence digests, evidence digest mismatch detection, balanced evidence budgets, matched bonds, winner-controlled settlement, consumer remediation authority, remediation requirement reproduction, reproduction mismatch detection, timeout refunds, frontend reads/writes, receipt confirmation, and GenLayer consensus primitives.

## Local development

```bash
cp .env.example .env.local
npm run dev
```

Set `VITE_ARTIFACT_COURT_ADDRESS` to the deployed Bradbury contract. No private key or deployment token belongs in browser environment variables.

## Judge walkthrough

1. Open the public docket and connect a Bradbury-compatible wallet.
2. Create a release with a full GitHub commit URL and test GEN bond.
3. Add at least one artifact URL containing that exact commit and a `sha256:` digest.
4. From a consumer wallet, register a public compatibility constraint.
5. Lock the graph, then open a challenge from a different wallet with the displayed matching bond.
6. Submit public evidence from both bonded wallets, each with a SHA-256 content digest.
7. After the evidence deadline, call adjudication and inspect the accepted transaction plus stored verdict. Validators verify every evidence item's content-bound digest.
8. For a conditional verdict, verify that only the affected consumer wallet can approve remediation. Validators will reproduce the exact remediation requirement from content-bound evidence before settlement.
9. For unresolved evidence, retry before timeout or refund both principals after timeout.

See [docs/JUDGE-WALKTHROUGH.md](docs/JUDGE-WALKTHROUGH.md) for code-level evidence.

## Acknowledgements

ArtifactCourt is an original implementation informed by public GenLayer patterns for validator-fetched market settlement, immutable compatibility graphs, retry-safe unresolved verdicts, artifact provenance, and regression-focused release discipline. No reference project is used as a runtime dependency.

## License

MIT. See [LICENSE](LICENSE).
