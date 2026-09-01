# Security Policy

ArtifactCourt is a Bradbury testnet application. Bonds use faucet-issued test GEN and have no promised monetary value.

## Core invariants

- Release and artifact links bind a full 40-character Git commit.
- The evidence graph becomes immutable before a challenge can open.
- Challenger bond equals the maintainer bond exactly.
- Maintainer and challenger receive independent 7,000-character evidence budgets.
- Validators re-fetch public sources during every adjudication; pre-fetched UI content is never authoritative.
- Conditional remediation requires the affected consumer owner's wallet approval.
- `UNRESOLVED` never selects a winner and remains retryable until a permissionless party refund timeout.
- Every settlement zeroes bond accounting before external transfers.

## Trust boundaries

Public web evidence can be unavailable, malicious, or contain prompt injection. The contract labels all fetched material as untrusted, constrains the output schema, checks cross-field invariants, and requires validators to agree on the consequential verdict and affected consumer.

The contract does not prove that software is bug-free. It adjudicates the exact locked revision against the exact registered evidence graph and compatibility constraints.

## Reporting

Open a GitHub issue without sensitive data. Do not include private keys, wallet recovery phrases, API tokens, or unpublished vulnerability details.

