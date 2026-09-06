# Builder Submission

## Title

ArtifactCourt - Consensus-Backed Software Release Adjudication

## Notes / Description

ArtifactCourt is a complete GenLayer application for adjudicating software release integrity and downstream compatibility. Maintainers bind a full Git commit, immutable artifacts, SHA-256 declarations, and a test GEN bond. Consumer constraints, both parties' semantic evidence, and remediation are also pinned to full-commit GitHub content plus SHA-256. Validators fetch and hash exact bytes before prompting. Consensus must reproduce the verdict, affected consumer, and exact remediation requirement; remediation settlement additionally requires the stored requirement digest. Digest or network failures remain unresolved without awarding either side. The React app executes every contract workflow and waits for accepted receipts before refreshing state.

## Evidence

- Live app: https://artifact-court.vercel.app
- GitHub: https://github.com/Jinchainne/artifact-court
- Contract: https://explorer-bradbury.genlayer.com/address/0x68D30326B420EA691C25728adbCeC38150f2F616
- Deployment transaction: https://explorer-bradbury.genlayer.com/tx/0x919941d71de070402c90eb484c8edc73da399387a2a5dc1f612693c58d6fbe48
- Behavioral tests: https://github.com/Jinchainne/artifact-court/blob/main/tests/test_contract_behavior.py
- Judge walkthrough: https://github.com/Jinchainne/artifact-court/blob/main/docs/JUDGE-WALKTHROUGH.md
