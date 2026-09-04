import { FormEvent, startTransition, useEffect, useState } from "react";
import {
  CONTRACT_ADDRESS,
  EXPLORER_URL,
  connectWallet,
  listCaseIds,
  readArtifact,
  readCase,
  readDependency,
  walletClient,
  writes,
} from "./lib/genlayer";
import type { ReleaseCase } from "./types";

type View = "docket" | "submit" | "inspect" | "workflow";

const ZERO = "0x0000000000000000000000000000000000000000";
const short = (value: string, size = 8) =>
  value.length > size * 2 ? `${value.slice(0, size)}...${value.slice(-size)}` : value;

function toWei(value: string) {
  const [whole = "0", decimal = ""] = value.trim().split(".");
  return BigInt(whole || "0") * 10n ** 18n + BigInt((decimal + "0".repeat(18)).slice(0, 18));
}

function formatGen(value: number | string) {
  const raw = BigInt(String(value || 0));
  const whole = raw / 10n ** 18n;
  const decimal = (raw % 10n ** 18n).toString().padStart(18, "0").slice(0, 4).replace(/0+$/, "");
  return `${whole}${decimal ? `.${decimal}` : ""} GEN`;
}

function dateTime(value: number | string) {
  return new Date(Number(value) * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface EvidencePair {
  url: string;
  digest: string;
}

function App() {
  const [view, setView] = useState<View>("docket");
  const [account, setAccount] = useState<`0x${string}` | "">("");
  const [cases, setCases] = useState<ReleaseCase[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [artifacts, setArtifacts] = useState<Record<string, unknown>[]>([]);
  const [dependencies, setDependencies] = useState<Record<string, unknown>[]>([]);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("Bradbury read model ready");

  const [release, setRelease] = useState({
    title: "",
    revisionUrl: "",
    notes: "",
    deadline: new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 16),
    bond: "0.01",
  });
  const [artifact, setArtifact] = useState({ kind: "SOURCE", url: "", digest: "sha256:" });
  const [consumer, setConsumer] = useState({ id: "", url: "" });
  const [evidencePairs, setEvidencePairs] = useState<EvidencePair[]>([{ url: "", digest: "sha256:" }]);
  const [remediation, setRemediation] = useState("");

  const selected = cases.find((item) => Number(item.id) === selectedId) ?? null;
  const policyBoundToExecution = Boolean(
    selected?.settled && ["ACTIVATED", "REJECTED", "REFUNDED", "CANCELLED"].includes(selected.state),
  );

  async function refresh(preferredId?: number) {
    try {
      const ids = (await listCaseIds()) as number[];
      const loaded = await Promise.all([...ids].reverse().map((id) => readCase(Number(id))));
      startTransition(() => {
        setCases(loaded as unknown as ReleaseCase[]);
        const target = preferredId ?? selectedId ?? (ids.length ? Number(ids[ids.length - 1]) : null);
        setSelectedId(target);
      });
      setNotice(`${ids.length} release case${ids.length === 1 ? "" : "s"} synchronized`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Unable to read contract state");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (!selected) {
      setArtifacts([]);
      setDependencies([]);
      return;
    }
    const artifactReads = Array.from({ length: Number(selected.artifact_count) }, (_, index) =>
      readArtifact(Number(selected.id), index),
    );
    const dependencyReads = Array.from({ length: Number(selected.dependency_count) }, (_, index) =>
      readDependency(Number(selected.id), index),
    );
    void Promise.all([Promise.all(artifactReads), Promise.all(dependencyReads)]).then(([a, d]) => {
      setArtifacts(a as Record<string, unknown>[]);
      setDependencies(d as Record<string, unknown>[]);
    });
  }, [selectedId, selected?.artifact_count, selected?.dependency_count]);

  async function connect() {
    try {
      const next = await connectWallet();
      setAccount(next);
      setNotice(`Wallet ${short(next, 6)} connected`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Wallet connection failed");
    }
  }

  async function transact(label: string, action: (client: any) => Promise<unknown>) {
    if (!account) {
      setNotice("Connect a wallet before writing to ArtifactCourt");
      return;
    }
    setBusy(label);
    setNotice(`${label}: awaiting wallet confirmation`);
    try {
      await action(walletClient(account));
      setNotice(`${label}: accepted by GenLayer validators`);
      await refresh(selectedId ?? undefined);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : `${label} failed`);
    } finally {
      setBusy("");
    }
  }

  async function createRelease(event: FormEvent) {
    event.preventDefault();
    await transact("Create release", (client) =>
      writes.createRelease(
        client,
        [release.title, release.revisionUrl, release.notes, Math.floor(new Date(release.deadline).getTime() / 1000)],
        toWei(release.bond),
      ),
    );
    setView("docket");
  }

  function openCase(id: number) {
    setSelectedId(id);
    setView("inspect");
  }

  const clientAction = (label: string, action: (client: any, id: number) => Promise<unknown>) => {
    if (!selectedId) return;
    void transact(label, (client) => action(client, selectedId));
  };

  function addEvidenceRow() {
    setEvidencePairs([...evidencePairs, { url: "", digest: "sha256:" }]);
  }

  function removeEvidenceRow(index: number) {
    setEvidencePairs(evidencePairs.filter((_, i) => i !== index));
  }

  function updateEvidenceRow(index: number, field: "url" | "digest", value: string) {
    const updated = [...evidencePairs];
    updated[index] = { ...updated[index], [field]: value };
    setEvidencePairs(updated);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand" onClick={() => setView("docket")}>
          <span className="brand-mark">AC</span>
          <span><strong>ArtifactCourt</strong><small>Release adjudication network</small></span>
        </button>
        <nav aria-label="Primary navigation">
          {(["docket", "submit", "inspect", "workflow"] as View[]).map((item) => (
            <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
              {item === "submit" ? "New release" : item}
            </button>
          ))}
        </nav>
        <button className="wallet" onClick={connect}>{account ? short(account, 5) : "Connect wallet"}</button>
      </header>

      <main>
        <section className="status-strip">
          <span className="pulse" />
          <span>{notice}</span>
          <a href={`${EXPLORER_URL}/address/${CONTRACT_ADDRESS}`} target="_blank" rel="noreferrer">
            Bradbury contract {short(CONTRACT_ADDRESS, 5)}
          </a>
        </section>

        {view === "docket" && (
          <>
            <section className="hero">
              <div>
                <span className="eyebrow">Consensus before activation</span>
                <h1>Ship software with<br /><em>evidence under oath.</em></h1>
                <p>
                  ArtifactCourt locks release artifacts and consumer constraints, then lets GenLayer validators
                  re-fetch both sides before a bonded verdict controls activation. Every evidence item is
                  content-bound with a SHA-256 digest for tamper-evident adjudication.
                </p>
                <div className="hero-actions">
                  <button className="primary" onClick={() => setView("submit")}>Open a release case</button>
                  <button className="secondary" onClick={() => void refresh()}>Refresh court ledger</button>
                </div>
              </div>
              <div className="protocol-card">
                <div className="protocol-number">04</div>
                <p>terminal routes</p>
                <ul>
                  <li><span>01</span> Compatible activation</li>
                  <li><span>02</span> Consumer remediation</li>
                  <li><span>03</span> Incompatible rejection</li>
                  <li><span>04</span> Fail-closed refund</li>
                </ul>
              </div>
            </section>

            <section className="section-head">
              <div><span className="eyebrow">Public docket</span><h2>Release cases</h2></div>
              <span>{cases.length.toString().padStart(2, "0")} on-chain records</span>
            </section>
            <section className="docket-grid">
              {cases.length === 0 && (
                <button className="empty-card" onClick={() => setView("submit")}>
                  <strong>No cases yet</strong><span>Create the first immutable release docket</span>
                </button>
              )}
              {cases.map((item) => (
                <button className="case-card" key={String(item.id)} onClick={() => openCase(Number(item.id))}>
                  <div className="case-top"><span>CASE {String(item.id).padStart(4, "0")}</span><b data-state={item.state}>{item.state}</b></div>
                  <h3>{item.title}</h3>
                  <p>{item.release_notes}</p>
                  <div className="case-meta">
                    <span><small>Revision</small>{short(item.revision, 6)}</span>
                    <span><small>Bond</small>{formatGen(item.maintainer_bond)}</span>
                    <span><small>Graph</small>{item.dependency_count} consumers</span>
                  </div>
                </button>
              ))}
            </section>
          </>
        )}

        {view === "submit" && (
          <section className="form-layout">
            <div className="form-intro">
              <span className="eyebrow">Maintainer filing</span>
              <h1>Open a release case</h1>
              <p>The commit reference is permanent. Artifacts and consumer constraints can be attached while the case remains a draft.</p>
              <ol>
                <li><b>01</b> Bind full commit</li><li><b>02</b> Register evidence graph</li><li><b>03</b> Lock and invite challenge</li>
              </ol>
            </div>
            <form className="filing-form" onSubmit={createRelease}>
              <label>Release title<input required value={release.title} onChange={(e) => setRelease({ ...release, title: e.target.value })} placeholder="Atlas Gateway v2.4" /></label>
              <label>Immutable GitHub revision URL<input required value={release.revisionUrl} onChange={(e) => setRelease({ ...release, revisionUrl: e.target.value })} placeholder="https://github.com/org/repo/commit/40-character-sha" /></label>
              <label>Release notes<textarea required value={release.notes} onChange={(e) => setRelease({ ...release, notes: e.target.value })} placeholder="Describe behavior changes, compatibility promises, and migration boundaries." /></label>
              <div className="two-col">
                <label>Challenge deadline<input type="datetime-local" required value={release.deadline} onChange={(e) => setRelease({ ...release, deadline: e.target.value })} /></label>
                <label>Maintainer bond (GEN)<input required value={release.bond} onChange={(e) => setRelease({ ...release, bond: e.target.value })} inputMode="decimal" /></label>
              </div>
              <button className="primary full" disabled={Boolean(busy)}>{busy || "Create draft on GenLayer"}</button>
            </form>
          </section>
        )}

        {view === "inspect" && !selected && (
          <section className="empty-inspector"><h2>Select a release case</h2><p>Open a case from the public docket to inspect its evidence graph and available actions.</p><button className="primary" onClick={() => setView("docket")}>Return to docket</button></section>
        )}

        {view === "inspect" && selected && (
          <section className="inspector">
            <div className="inspector-heading">
              <div><span className="eyebrow">Case {String(selected.id).padStart(4, "0")}</span><h1>{selected.title}</h1></div>
              <b className="large-state" data-state={selected.state}>{selected.state}</b>
            </div>
            <div className="summary-row">
              <span><small>Maintainer bond</small>{formatGen(selected.maintainer_bond)}</span>
              <span><small>Challenge closes</small>{dateTime(selected.challenge_deadline)}</span>
              <span><small>Evidence closes</small>{dateTime(selected.evidence_deadline)}</span>
              <span><small>Revision</small><a href={selected.revision_url} target="_blank" rel="noreferrer">{short(selected.revision, 7)}</a></span>
            </div>

            <div className="inspector-grid">
              <div className="evidence-column">
                <article className="ledger-block">
                  <div className="block-title"><span>01</span><h2>Locked evidence graph</h2></div>
                  <p>{selected.release_notes}</p>
                  <code>{selected.graph_digest || "Graph remains editable until maintainer lock"}</code>
                  <h3>Artifacts</h3>
                  {artifacts.map((item, index) => <a className="evidence-item" key={index} href={String(item.immutable_url)} target="_blank" rel="noreferrer"><b>{String(item.kind)}</b><span>{short(String(item.declared_digest), 12)}</span></a>)}
                  {!artifacts.length && <p className="muted">No release artifacts registered.</p>}
                  <h3>Consumer constraints</h3>
                  {dependencies.map((item, index) => <a className="evidence-item" key={index} href={String(item.constraint_url)} target="_blank" rel="noreferrer"><b>{String(item.consumer_id)}</b><span>owned by {short(String(item.owner), 5)}</span></a>)}
                  {!dependencies.length && <p className="muted">No consumer constraints registered.</p>}
                </article>

                <article className="ledger-block verdict-block">
                  <div className="block-title"><span>02</span><h2>Consensus verdict</h2></div>
                  <strong>{selected.verdict || "AWAITING ADJUDICATION"}</strong>
                  <p>{selected.reasoning || "Validators will independently re-fetch each reserved evidence partition and verify content-bound digests after the evidence window closes."}</p>
                  <p className="binding-status">{policyBoundToExecution ? "Verdict bound to terminal execution and settled accounting." : "No terminal execution is permitted before the contract reaches a final route."}</p>
                  {selected.remediation_required && <div className="remedy"><small>Consumer-owned remediation</small>{selected.remediation_required}</div>}
                </article>
              </div>

              <aside className="action-rail">
                <span className="eyebrow">Case actions</span>
                <h2>Advance the docket</h2>

                {selected.state === "DRAFT" && (
                  <>
                    <form onSubmit={(e) => { e.preventDefault(); clientAction("Add artifact", (client, id) => writes.addArtifact(client, [id, artifact.kind, artifact.url, artifact.digest])); }}>
                      <h3>Add immutable artifact</h3>
                      <select value={artifact.kind} onChange={(e) => setArtifact({ ...artifact, kind: e.target.value })}><option>SOURCE</option><option>SCHEMA</option><option>BINARY</option><option>MIGRATION</option><option>SPECIFICATION</option></select>
                      <input required value={artifact.url} onChange={(e) => setArtifact({ ...artifact, url: e.target.value })} placeholder="Immutable blob/raw URL" />
                      <input required value={artifact.digest} onChange={(e) => setArtifact({ ...artifact, digest: e.target.value })} placeholder="sha256:..." />
                      <button disabled={Boolean(busy)}>Register artifact</button>
                    </form>
                    <form onSubmit={(e) => { e.preventDefault(); clientAction("Register consumer", (client, id) => writes.registerConsumer(client, [id, consumer.id, consumer.url])); }}>
                      <h3>Register as consumer</h3>
                      <input required value={consumer.id} onChange={(e) => setConsumer({ ...consumer, id: e.target.value })} placeholder="consumer-id" />
                      <input required value={consumer.url} onChange={(e) => setConsumer({ ...consumer, url: e.target.value })} placeholder="Public constraint URL" />
                      <button disabled={Boolean(busy)}>Own this constraint</button>
                    </form>
                    <div className="button-pair"><button onClick={() => clientAction("Lock release", (client, id) => writes.lockRelease(client, id))}>Lock evidence graph</button><button className="danger" onClick={() => clientAction("Cancel draft", (client, id) => writes.cancelDraft(client, id))}>Cancel & refund</button></div>
                  </>
                )}

                {selected.state === "LOCKED" && (
                  <div className="action-box"><h3>Match the maintainer bond</h3><p>Opening a challenge locks equal risk on both sides.</p><button onClick={() => clientAction("Open challenge", (client, id) => writes.openChallenge(client, id, BigInt(String(selected.maintainer_bond))))}>Challenge with {formatGen(selected.maintainer_bond)}</button><button className="subtle" onClick={() => clientAction("Activate unchallenged", (client, id) => writes.activateUnchallenged(client, id))}>Activate after deadline</button></div>
                )}

                {(selected.state === "CHALLENGED" || selected.state === "UNRESOLVED") && (
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    const validPairs = evidencePairs.filter((p) => p.url.trim() && p.digest.trim() && p.digest !== "sha256:");
                    const urls = validPairs.map((p) => p.url.trim());
                    const digests = validPairs.map((p) => p.digest.trim());
                    void transact("Submit evidence", (client) => writes.submitEvidence(client, selectedId!, urls, digests));
                  }}>
                    <h3>Content-bound evidence</h3>
                    <p>Each URL must carry a SHA-256 digest binding it to immutable content. Validators verify fetched bytes match every declared digest.</p>
                    {evidencePairs.map((pair, index) => (
                      <div key={index} className="evidence-pair-row">
                        <input required value={pair.url} onChange={(e) => updateEvidenceRow(index, "url", e.target.value)} placeholder="https://..." />
                        <input required value={pair.digest} onChange={(e) => updateEvidenceRow(index, "digest", e.target.value)} placeholder="sha256:..." />
                        {evidencePairs.length > 1 && <button type="button" className="subtle" onClick={() => removeEvidenceRow(index)}>Remove</button>}
                      </div>
                    ))}
                    {evidencePairs.length < 5 && <button type="button" className="subtle" onClick={addEvidenceRow}>+ Add evidence item</button>}
                    <button disabled={Boolean(busy)}>Replace my evidence set</button>
                    <button type="button" className="subtle" onClick={() => clientAction("Adjudicate", (client, id) => writes.adjudicate(client, id))}>Run consensus after deadline</button>
                  </form>
                )}

                {selected.state === "CONDITIONAL" && (
                  <form onSubmit={(e) => { e.preventDefault(); clientAction("Submit remediation", (client, id) => writes.submitRemediation(client, id, remediation)); }}>
                    <h3>Conditional remediation</h3>
                    <p>{selected.remediation_required}</p>
                    <p className="muted">Validators will reproduce this exact requirement from content-bound evidence before settlement can proceed.</p>
                    <input required value={remediation} onChange={(e) => setRemediation(e.target.value)} placeholder="Public remediation evidence URL" />
                    <button disabled={Boolean(busy)}>Submit remediation</button>
                    <button type="button" className="subtle" onClick={() => clientAction("Approve remediation", (client, id) => writes.approveRemediation(client, id))}>Affected consumer approves</button>
                    <button type="button" className="subtle" onClick={() => clientAction("Verify remediation", (client, id) => writes.verifyRemediation(client, id))}>Validator re-check</button>
                  </form>
                )}

                {(["CHALLENGED", "UNRESOLVED", "CONDITIONAL"] as string[]).includes(selected.state) && <button className="danger full" onClick={() => clientAction("Timeout refund", (client, id) => writes.refundTimedOut(client, id))}>Refund both bonds after timeout</button>}
                {(["ACTIVATED", "REJECTED", "REFUNDED", "CANCELLED"] as string[]).includes(selected.state) && <div className="terminal"><span>Terminal record</span><p>This case is immutable and its bond accounting is closed.</p></div>}
              </aside>
            </div>
          </section>
        )}

        {view === "workflow" && (
          <section className="workflow-page">
            <span className="eyebrow">Protocol map</span>
            <h1>One docket, five safeguards</h1>
            <p className="lead">ArtifactCourt combines immutable provenance, content-bound evidence, dependency-aware compatibility and matched-bond settlement without trusting a pre-fetched evidence packet.</p>
            <div className="workflow-grid">
              {[
                ["01", "Bind", "A full Git commit, artifact digests and consumer-owned constraints form a canonical graph digest."],
                ["02", "Challenge", "A challenger must match the maintainer bond exactly, creating symmetric exposure."],
                ["03", "Re-fetch", "Validators independently render each side, verify content-bound evidence digests, and preserve separate evidence budgets."],
                ["04", "Remediate", "Conditional verdicts name one affected consumer whose wallet controls approval. Validators reproduce the exact remediation requirement before settlement."],
                ["05", "Settle", "Activation, rejection or fail-closed timeout directly controls bond delivery."],
              ].map(([number, title, copy]) => <article key={number}><span>{number}</span><h2>{title}</h2><p>{copy}</p></article>)}
            </div>
            <div className="state-line"><b>DRAFT</b><i /><b>LOCKED</b><i /><b>CHALLENGED</b><i /><b>CONSENSUS</b><i /><b>TERMINAL</b></div>
          </section>
        )}
      </main>
      <footer><span>ArtifactCourt / Bradbury Testnet</span><span>Content-bound evidence. Independent validators. Deterministic consequences.</span></footer>
    </div>
  );
}

export default App;
