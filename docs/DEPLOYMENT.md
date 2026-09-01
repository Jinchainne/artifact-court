# Deployment

## Preflight

```bash
npm ci
npm test
npm run verify
npm run build
python -m py_compile contracts/artifact_court.py
python -m genvm_linter.cli check contracts/artifact_court.py
```

## Contract

Deploy `contracts/artifact_court.py` to `testnet-bradbury` with no constructor arguments. Wait for `ACCEPTED`, verify validator agreement, retrieve the deployed schema, and call `list_case_ids` as a read canary.

Record the exact contract address and transaction hash in `deployments/bradbury.json`.

## Frontend

Set:

```text
VITE_ARTIFACT_COURT_ADDRESS=<accepted contract address>
```

Rebuild after changing the address because Vite embeds public configuration at build time. Deploy the repository root to Vercel, make the project public, and verify the production JavaScript bundle contains the accepted address.

## Release checks

- GitHub repository visibility is public.
- Vercel deployment returns HTTP 200.
- Contract explorer shows accepted deployment.
- Production app reads `list_case_ids` from the accepted address.
- No `.env`, private key, GitHub token, or Vercel token is committed.

