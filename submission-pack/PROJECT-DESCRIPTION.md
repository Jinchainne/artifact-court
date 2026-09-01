# ArtifactCourt - GenLayer Release Adjudication Network

ArtifactCourt is a complete GenLayer application for adjudicating software release integrity and downstream compatibility. Maintainers bind a full Git commit, immutable artifacts, SHA-256 declarations, and a bond. Consumer wallets register and own compatibility constraints before the evidence graph is locked. A challenger can match the maintainer bond and submit a reserved counter-evidence set.

GenLayer validators independently re-fetch maintainer evidence, challenger evidence, and consumer constraints. Their agreed `COMPATIBLE`, `CONDITIONAL`, `INCOMPATIBLE`, or `UNRESOLVED` verdict directly controls activation and bond settlement. Conditional fixes require approval from the affected consumer wallet and a second validator re-check. Missing evidence remains retry-safe, while a fixed timeout refunds both principals.

The public React application connects wallets, executes all contract writes, waits for accepted receipts, and reads authoritative on-chain case state.

