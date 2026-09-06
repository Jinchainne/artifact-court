export type CaseState =
  | "DRAFT"
  | "LOCKED"
  | "CHALLENGED"
  | "CONDITIONAL"
  | "UNRESOLVED"
  | "ACTIVATED"
  | "REJECTED"
  | "REFUNDED"
  | "CANCELLED";

export type AnchoredEvidence = {
  immutable_url: string;
  declared_digest: string;
};

export interface ReleaseCase {
  id: number | string;
  maintainer: string;
  challenger: string;
  title: string;
  revision_url: string;
  revision: string;
  release_notes: string;
  maintainer_bond: number | string;
  challenger_bond: number | string;
  artifact_count: number | string;
  dependency_count: number | string;
  maintainer_evidence: AnchoredEvidence[];
  challenger_evidence: AnchoredEvidence[];
  state: CaseState;
  graph_digest: string;
  verdict: string;
  reasoning: string;
  affected_consumer_id: string;
  remediation_required: string;
  remediation_requirement_digest: string;
  remediation_url: string;
  remediation_digest: string;
  remediation_approved: boolean;
  challenge_deadline: number | string;
  evidence_deadline: number | string;
  resolution_timeout: number | string;
  settled: boolean;
}
