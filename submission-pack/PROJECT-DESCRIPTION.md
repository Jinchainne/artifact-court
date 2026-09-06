# ArtifactCourt - GenLayer Release Adjudication Network

ArtifactCourt is a complete GenLayer application for adjudicating software release integrity and downstream compatibility. Maintainers bind a full Git commit, immutable artifacts, SHA-256 declarations, and a bond. Independent consumer wallets register and own compatibility constraints before the evidence graph is locked. A challenger can match the maintainer bond and submit a reserved counter-evidence set.

GenLayer validators fetch canonical raw bytes and compare observed SHA-256 digests for artifacts, maintainer evidence, challenger evidence, consumer constraints, and remediation. Their agreed `COMPATIBLE`, `CONDITIONAL`, `INCOMPATIBLE`, or `UNRESOLVED` verdict directly controls activation and bond settlement. Conditional consensus includes the exact remediation requirement and stores its digest. After affected-consumer approval, remediation validators must reproduce that exact digest before either payout path can execute. Missing or mismatched evidence remains retry-safe, while a fixed timeout refunds both principals.

The public React application connects wallets, executes all contract writes, waits for accepted receipts, and reads authoritative on-chain case state.
