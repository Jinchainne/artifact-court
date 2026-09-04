import { createClient } from "genlayer-js";
import { testnetBradbury } from "genlayer-js/chains";

export const RPC_URL = "https://rpc-bradbury.genlayer.com";
export const EXPLORER_URL = "https://explorer-bradbury.genlayer.com";
export const CONTRACT_ADDRESS =
  (import.meta.env.VITE_ARTIFACT_COURT_ADDRESS as string) ||
  "0x2e6b043D7A204D9611D30fFeE3eb83E4EAbc24D2";

function address() {
  if (!/^0x[a-fA-F0-9]{40}$/.test(CONTRACT_ADDRESS) || /^0x0{40}$/.test(CONTRACT_ADDRESS)) {
    throw new Error("ArtifactCourt contract address has not been deployed yet");
  }
  return CONTRACT_ADDRESS as `0x${string}`;
}

export function readClient() {
  return createClient({ chain: testnetBradbury, endpoint: RPC_URL });
}

export function walletClient(account: `0x${string}`) {
  const provider = window.ethereum;
  if (!provider) throw new Error("Install MetaMask, Rabby, or OKX Wallet");
  return createClient({
    chain: testnetBradbury,
    account,
    provider,
    endpoint: RPC_URL,
  });
}

export async function connectWallet() {
  if (!window.ethereum) throw new Error("Install MetaMask, Rabby, or OKX Wallet");
  const accounts = (await window.ethereum.request({ method: "eth_requestAccounts" })) as string[];
  return accounts[0] as `0x${string}`;
}

async function confirmed(client: any, hash: any) {
  return client.waitForTransactionReceipt({
    hash,
    status: "ACCEPTED",
    fullTransaction: true,
    retries: 120,
    interval: 3000,
  });
}

async function write(
  client: any,
  functionName: string,
  args: any[],
  value?: bigint,
) {
  const hash = await client.writeContract({
    address: address(),
    functionName,
    args,
    ...(value === undefined ? {} : { value }),
  });
  return confirmed(client, hash);
}

export const writes = {
  createRelease: (client: any, args: any[], value: bigint) =>
    write(client, "create_release", args, value),
  addArtifact: (client: any, args: any[]) =>
    write(client, "add_artifact", args),
  registerConsumer: (client: any, args: any[]) =>
    write(client, "register_consumer", args),
  lockRelease: (client: any, id: number) =>
    write(client, "lock_release", [id]),
  cancelDraft: (client: any, id: number) =>
    write(client, "cancel_draft", [id]),
  openChallenge: (client: any, id: number, value: bigint) =>
    write(client, "open_challenge", [id], value),
  submitEvidence: (client: any, id: number, urls: string[], digests: string[]) =>
    write(client, "submit_evidence", [id, urls, digests]),
  adjudicate: (client: any, id: number) =>
    write(client, "adjudicate", [id]),
  submitRemediation: (client: any, id: number, url: string) =>
    write(client, "submit_remediation", [id, url]),
  approveRemediation: (client: any, id: number) =>
    write(client, "approve_remediation", [id]),
  verifyRemediation: (client: any, id: number) =>
    write(client, "verify_remediation", [id]),
  activateUnchallenged: (client: any, id: number) =>
    write(client, "activate_unchallenged", [id]),
  refundTimedOut: (client: any, id: number) =>
    write(client, "refund_timed_out", [id]),
};

export async function listCaseIds() {
  return readClient().readContract({ address: address(), functionName: "list_case_ids", args: [] });
}

export async function readCase(id: number) {
  return readClient().readContract({ address: address(), functionName: "get_case", args: [id] });
}

export async function readArtifact(id: number, index: number) {
  return readClient().readContract({ address: address(), functionName: "get_artifact", args: [id, index] });
}

export async function readDependency(id: number, index: number) {
  return readClient().readContract({ address: address(), functionName: "get_dependency", args: [id, index] });
}

declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
    };
  }
}
