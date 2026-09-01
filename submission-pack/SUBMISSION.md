# Builder Submission

## Title

ArtifactCourt - Consensus-Backed Software Release Adjudication

## Notes / Description

ArtifactCourt is a complete GenLayer application for adjudicating software release integrity and downstream compatibility. Maintainers bind a full Git commit, immutable artifact URLs, SHA-256 declarations, consumer-owned constraints, and a test GEN bond. A challenger must match that bond and receives an independent evidence budget. GenLayer validators re-fetch both parties and every locked constraint before an agreed COMPATIBLE, CONDITIONAL, INCOMPATIBLE, or UNRESOLVED verdict controls activation and settlement. Conditional fixes require approval from the affected consumer wallet and a second validator re-check. Unavailable evidence remains retry-safe; terminal timeouts refund both principals. The public React app executes all contract reads/writes and waits for accepted receipts.

## Evidence

- Live app: https://artifact-court.vercel.app
- GitHub: https://github.com/Jinchainne/artifact-court
- Contract: https://explorer-bradbury.genlayer.com/address/0x9AFEc9731370e4A14a48a450B8408b13f702489c
- Deployment transaction: https://explorer-bradbury.genlayer.com/tx/0x98ff08178a528f37d6c2305baf6d76e7cc02a78b143d959106d6424c00021d60
- Behavioral tests: https://github.com/Jinchainne/artifact-court/blob/main/tests/test_contract_behavior.py
- Judge walkthrough: https://github.com/Jinchainne/artifact-court/blob/main/docs/JUDGE-WALKTHROUGH.md
