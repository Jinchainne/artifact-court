# Builder Submission

## Title

ArtifactCourt - Consensus-Backed Software Release Adjudication

## Notes / Description

ArtifactCourt is a complete GenLayer application for adjudicating software release integrity and downstream compatibility. Maintainers bind a full Git commit, immutable artifacts, SHA-256 declarations, and a test GEN bond. Independent consumer wallets own compatibility constraints, while challengers must match the maintainer bond and receive a reserved evidence budget. Validators fetch artifact bytes to verify locked digests, then independently re-fetch both parties and every constraint before consensus controls activation and settlement. Conditional fixes require affected-consumer approval and validator re-check. Network failures remain unresolved without awarding either side; terminal timeouts refund both principals. The React app executes all contract reads/writes and waits for accepted receipts.

## Evidence

- Live app: https://artifact-court.vercel.app
- GitHub: https://github.com/Jinchainne/artifact-court
- Contract: https://explorer-bradbury.genlayer.com/address/0x2e6b043D7A204D9611D30fFeE3eb83E4EAbc24D2
- Deployment transaction: https://explorer-bradbury.genlayer.com/tx/0x5887dcded30d83c31b53dbff98fb2f564fa139ce4cbb70d517ec6b79fea7b2f8
- Behavioral tests: https://github.com/Jinchainne/artifact-court/blob/main/tests/test_contract_behavior.py
- Judge walkthrough: https://github.com/Jinchainne/artifact-court/blob/main/docs/JUDGE-WALKTHROUGH.md
