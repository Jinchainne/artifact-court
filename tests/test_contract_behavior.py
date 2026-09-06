import importlib.util
import pathlib
import sys
import types
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "artifact_court.py"


class _Decorator:
    def __call__(self, value):
        return value

    @property
    def payable(self):
        return self


class _GenericList(list):
    @classmethod
    def __class_getitem__(cls, _item):
        return cls


class _GenericMap(dict):
    @classmethod
    def __class_getitem__(cls, _item):
        return cls


def _load_contract():
    gl = types.SimpleNamespace(
        Contract=object,
        evm=types.SimpleNamespace(contract_interface=_Decorator()),
        public=types.SimpleNamespace(write=_Decorator(), view=_Decorator()),
        nondet=types.SimpleNamespace(
            web=types.SimpleNamespace(
                render=lambda _url, mode="text": "",
                get=lambda _url: types.SimpleNamespace(status=200, body=b"artifact"),
            ),
            exec_prompt=lambda _prompt, response_format="json": {},
        ),
        vm=types.SimpleNamespace(
            UserError=RuntimeError,
            Result=object,
            Return=type("Return", (), {}),
            run_nondet_unsafe=lambda leader, _validator: leader(),
        ),
        message_raw={"datetime": "2026-09-01T00:00:00Z"},
        message=types.SimpleNamespace(sender_address="0x" + "1" * 40, value=0),
    )
    module_stub = types.ModuleType("genlayer")
    module_stub.gl = gl
    module_stub.allow_storage = _Decorator()
    module_stub.u256 = int
    module_stub.Address = str
    module_stub.DynArray = _GenericList
    module_stub.TreeMap = _GenericMap
    previous = sys.modules.get("genlayer")
    sys.modules["genlayer"] = module_stub
    try:
        spec = importlib.util.spec_from_file_location("artifact_court_behavior", CONTRACT_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            del sys.modules["genlayer"]
        else:
            sys.modules["genlayer"] = previous


class ArtifactCourtBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.module = _load_contract()
        self.contract = object.__new__(self.module.ArtifactCourt)
        self.contract.cases = {}
        self.maintainer = "0x" + "1" * 40
        self.challenger = "0x" + "2" * 40
        self.consumer = "0x" + "3" * 40

    def case(self, **overrides):
        values = {
            "id": 1,
            "maintainer": self.maintainer,
            "challenger": self.challenger,
            "title": "Gateway release",
            "revision_url": "https://github.com/acme/gateway/commit/" + "a" * 40,
            "revision": "a" * 40,
            "release_notes": "A bounded release candidate with explicit API guarantees.",
            "maintainer_bond": 100,
            "challenger_bond": 100,
            "artifacts": [
                types.SimpleNamespace(
                    kind="SOURCE",
                    immutable_url="https://github.com/acme/gateway/blob/" + "a" * 40 + "/src/api.ts",
                    declared_digest="sha256:" + "b" * 64,
                )
            ],
            "dependencies": [
                types.SimpleNamespace(
                    consumer_id="wallet-client",
                    owner=self.consumer,
                    constraint_url="https://github.com/consumer/wallet/blob/" + "e" * 40 + "/constraint.md",
                    constraint_digest="sha256:" + "f" * 64,
                )
            ],
            "maintainer_evidence": [
                types.SimpleNamespace(
                    immutable_url="https://github.com/maintainer/release/blob/" + "1" * 40 + "/evidence.md",
                    declared_digest="sha256:" + "2" * 64,
                )
            ],
            "challenger_evidence": [
                types.SimpleNamespace(
                    immutable_url="https://github.com/challenger/review/blob/" + "3" * 40 + "/evidence.md",
                    declared_digest="sha256:" + "4" * 64,
                )
            ],
            "state": self.module.CaseState.CHALLENGED,
            "graph_digest": "sha256:" + "c" * 64,
            "verdict": "",
            "reasoning": "",
            "affected_consumer_id": "",
            "remediation_required": "",
            "remediation_requirement_digest": "",
            "remediation_url": "",
            "remediation_digest": "",
            "remediation_approved": False,
            "challenge_deadline": 100,
            "evidence_deadline": 200,
            "resolution_timeout": 300,
            "settled": False,
        }
        values.update(overrides)
        return types.SimpleNamespace(**values)

    def test_revision_and_artifacts_are_bound_to_full_commit(self):
        with self.assertRaisesRegex(RuntimeError, "40-character commit"):
            self.module._immutable_revision_url("https://github.com/acme/gateway/commit/main")
        url, revision = self.module._immutable_revision_url(
            "https://github.com/acme/gateway/commit/" + "a" * 40
        )
        self.assertEqual(revision, "a" * 40)
        self.assertIn(revision, url)
        with self.assertRaisesRegex(RuntimeError, "case revision"):
            self.module._immutable_artifact_url(
                "https://github.com/acme/gateway/blob/" + "d" * 40 + "/src/api.ts",
                revision,
            )

    def test_graph_digest_is_stable_across_consumer_registration_order(self):
        first = self.case()
        second_dependency = types.SimpleNamespace(
            consumer_id="api-indexer",
            owner="0x" + "4" * 40,
            constraint_url="https://github.com/indexer/spec/blob/" + "5" * 40 + "/constraint.md",
            constraint_digest="sha256:" + "6" * 64,
        )
        first.dependencies = [first.dependencies[0], second_dependency]
        second = self.case()
        second.dependencies = [second_dependency, second.dependencies[0]]
        self.assertEqual(self.module._canonical_graph(first), self.module._canonical_graph(second))

    def test_each_party_keeps_an_independent_evidence_budget(self):
        maintainer_body = b"M" * 20_000
        challenger_body = b"C" * 20_000
        maintainer = self.case().maintainer_evidence
        challenger = self.case().challenger_evidence
        maintainer[0].declared_digest = "sha256:" + __import__("hashlib").sha256(maintainer_body).hexdigest()
        challenger[0].declared_digest = "sha256:" + __import__("hashlib").sha256(challenger_body).hexdigest()
        self.module.gl.nondet.web.get = lambda url: types.SimpleNamespace(
            status=200,
            body=maintainer_body if "maintainer" in url else challenger_body,
        )
        maintainer_packet, maintainer_available, maintainer_match = self.contract._fetch_evidence(
            "MAINTAINER", maintainer, self.module.SIDE_EVIDENCE_BUDGET
        )
        challenger_packet, challenger_available, challenger_match = self.contract._fetch_evidence(
            "CHALLENGER", challenger, self.module.SIDE_EVIDENCE_BUDGET
        )
        self.assertTrue(maintainer_available and challenger_available)
        self.assertTrue(maintainer_match and challenger_match)
        self.assertEqual(maintainer_packet.split(":\n", 1)[1].count("M"), 7000)
        self.assertEqual(challenger_packet.split(":\n", 1)[1].count("C"), 7000)

    def test_semantic_evidence_is_immutable_and_hash_bound(self):
        with self.assertRaisesRegex(RuntimeError, "immutable GitHub"):
            self.module._immutable_content_url(
                "https://github.com/maintainer/release/blob/main/evidence.md"
            )
        evidence = self.case().maintainer_evidence
        body = b"Immutable semantic evidence body."
        self.module.gl.nondet.web.get = lambda _url: types.SimpleNamespace(status=200, body=body)
        evidence[0].declared_digest = "sha256:" + __import__("hashlib").sha256(body).hexdigest()
        _, available, matches = self.contract._fetch_evidence("MAINTAINER", evidence, 7000)
        self.assertTrue(available)
        self.assertTrue(matches)
        evidence[0].declared_digest = "sha256:" + "0" * 64
        _, available, matches = self.contract._fetch_evidence("MAINTAINER", evidence, 7000)
        self.assertTrue(available)
        self.assertFalse(matches)

    def test_validators_fetch_artifact_bytes_and_compare_locked_digest(self):
        body = b"export const apiVersion = '2.4';\n"
        case = self.case()
        case.artifacts[0].declared_digest = "sha256:" + __import__("hashlib").sha256(body).hexdigest()
        self.module.gl.nondet.web.get = lambda _url: types.SimpleNamespace(status=200, body=body)

        packet, available, matches = self.contract._fetch_artifacts(case)

        self.assertTrue(available)
        self.assertTrue(matches)
        self.assertIn(case.artifacts[0].declared_digest, packet)
        case.artifacts[0].declared_digest = "sha256:" + "0" * 64
        _, available, matches = self.contract._fetch_artifacts(case)
        self.assertTrue(available)
        self.assertFalse(matches)

    def test_artifact_transport_failure_is_unresolved_not_a_digest_mismatch(self):
        case = self.case()
        self.module.gl.nondet.web.get = lambda _url: types.SimpleNamespace(status=503, body=b"")
        _, available, matches = self.contract._fetch_artifacts(case)
        self.assertFalse(available)
        self.assertTrue(matches)

    def test_challenger_bond_must_exactly_match_maintainer_bond(self):
        case = self.case(state=self.module.CaseState.LOCKED, challenger=self.module.ZERO_ADDRESS, challenger_bond=0)
        self.contract.cases[1] = case
        self.module._now = lambda: 50
        self.module.gl.message.sender_address = self.challenger
        self.module.gl.message.value = 1
        with self.assertRaisesRegex(RuntimeError, "exactly match"):
            self.contract.open_challenge(1)
        self.module.gl.message.value = 100
        self.contract.open_challenge(1)
        self.assertEqual(case.state, self.module.CaseState.CHALLENGED)
        self.assertEqual(case.challenger_bond, 100)

    def test_compatible_and_incompatible_verdicts_control_bond_settlement(self):
        for verdict, winner, expected_state in (
            ("COMPATIBLE", self.maintainer, self.module.CaseState.ACTIVATED),
            ("INCOMPATIBLE", self.challenger, self.module.CaseState.REJECTED),
        ):
            case = self.case()
            self.contract.cases[1] = case
            transfers = []
            self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount)) if amount > 0 else None
            self.contract._apply_verdict(
                case,
                {"verdict": verdict, "affected_consumer_id": "", "reasoning": "Evidence establishes the terminal result.", "remediation": ""},
            )
            self.assertEqual(case.state, expected_state)
            self.assertEqual(transfers, [(winner, 200)])
            self.assertTrue(case.settled)

    def test_conditional_verdict_preserves_bonds_and_consumer_owns_approval(self):
        case = self.case()
        self.contract.cases[1] = case
        self.contract._apply_verdict(
            case,
            {
                "verdict": "CONDITIONAL",
                "affected_consumer_id": "wallet-client",
                "reasoning": "The client requires a migration adapter before activation.",
                "remediation": "Publish and bind the compatibility adapter.",
            },
        )
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)
        case.remediation_url = "https://github.com/maintainer/release/blob/" + "1" * 40 + "/adapter.md"
        self.module.gl.message.sender_address = self.challenger
        with self.assertRaisesRegex(RuntimeError, "affected consumer owner"):
            self.contract.approve_remediation(1)
        self.module.gl.message.sender_address = self.consumer
        self.contract.approve_remediation(1)
        self.assertTrue(case.remediation_approved)

    def test_maintainer_cannot_self_own_a_consumer_constraint(self):
        case = self.case(state=self.module.CaseState.DRAFT, dependencies=[])
        self.contract.cases[1] = case
        self.module.gl.message.sender_address = self.maintainer
        with self.assertRaisesRegex(RuntimeError, "cannot own"):
            self.contract.register_consumer(
                1,
                "self-client",
                "https://github.com/consumer/wallet/blob/" + "e" * 40 + "/constraint.md",
                "sha256:" + "f" * 64,
            )

    def test_remediation_fetch_failure_keeps_bonds_and_conditional_state(self):
        case = self.case(
            state=self.module.CaseState.CONDITIONAL,
            affected_consumer_id="wallet-client",
            remediation_required="Publish a compatibility adapter for the affected consumer.",
            remediation_requirement_digest="sha256:" + "7" * 64,
            remediation_url="https://github.com/maintainer/release/blob/" + "1" * 40 + "/adapter.md",
            remediation_digest="sha256:" + "8" * 64,
            remediation_approved=True,
        )
        self.contract.cases[1] = case
        self.module._now = lambda: 250
        self.module.gl.nondet.web.get = lambda _url: (_ for _ in ()).throw(RuntimeError("offline"))
        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))

        outcome = self.contract.verify_remediation(1)

        self.assertEqual(outcome, "UNRESOLVED")
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)
        self.assertEqual(transfers, [])

    def test_exact_remediation_requirement_is_part_of_validator_agreement(self):
        digest = "sha256:" + "9" * 64
        leader = {
            "verdict": "CONDITIONAL",
            "affected_consumer_id": "wallet-client",
            "reasoning": "The adapter is required before this consumer can migrate safely.",
            "remediation": "Publish adapter version 2.1 with the documented legacy route mapping.",
        }
        validator = dict(leader)
        self.assertTrue(self.contract._adjudication_consensus_matches(leader, validator))
        validator["remediation"] = "Publish a different adapter requirement."
        self.assertFalse(self.contract._adjudication_consensus_matches(leader, validator))
        remediation_leader = {"outcome": "SATISFIED", "requirement_digest": digest}
        remediation_validator = dict(remediation_leader)
        self.assertTrue(
            self.contract._remediation_consensus_matches(
                remediation_leader, remediation_validator, digest
            )
        )
        remediation_validator["requirement_digest"] = "sha256:" + "0" * 64
        self.assertFalse(
            self.contract._remediation_consensus_matches(
                remediation_leader, remediation_validator, digest
            )
        )

    def test_mismatched_remediation_requirement_cannot_trigger_settlement(self):
        import hashlib

        requirement = "Publish adapter version 2.1 with the documented legacy route mapping."
        requirement_digest = "sha256:" + hashlib.sha256(requirement.encode("utf-8")).hexdigest()
        remediation_body = b"Adapter 2.1 implements every documented legacy route mapping."
        constraint_body = b"Activation requires the documented legacy route mapping to remain available."
        case = self.case(
            state=self.module.CaseState.CONDITIONAL,
            affected_consumer_id="wallet-client",
            remediation_required=requirement,
            remediation_requirement_digest=requirement_digest,
            remediation_url="https://github.com/maintainer/release/blob/" + "1" * 40 + "/adapter.md",
            remediation_digest="sha256:" + hashlib.sha256(remediation_body).hexdigest(),
            remediation_approved=True,
        )
        case.dependencies[0].constraint_digest = (
            "sha256:" + hashlib.sha256(constraint_body).hexdigest()
        )
        self.contract.cases[1] = case
        self.module._now = lambda: 250
        self.module.gl.nondet.web.get = lambda url: types.SimpleNamespace(
            status=200,
            body=remediation_body if "adapter.md" in url else constraint_body,
        )
        responses = iter(
            [
                {
                    "outcome": "SATISFIED",
                    "requirement_digest": requirement_digest,
                    "reasoning": "The immutable remediation satisfies the exact stored requirement.",
                },
                {
                    "outcome": "SATISFIED",
                    "requirement_digest": "sha256:" + "0" * 64,
                    "reasoning": "This validator evaluated a different remediation requirement.",
                },
            ]
        )
        self.module.gl.nondet.exec_prompt = lambda _prompt, response_format="json": next(responses)

        def require_validator_agreement(leader_fn, validator_fn):
            leader_result = self.module.gl.vm.Return()
            leader_result.calldata = leader_fn()
            if not validator_fn(leader_result):
                raise RuntimeError("validator disagreement")
            return leader_result.calldata

        self.module.gl.vm.run_nondet_unsafe = require_validator_agreement
        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))

        with self.assertRaisesRegex(RuntimeError, "exact remediation requirement"):
            self.contract.verify_remediation(1)
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)
        self.assertEqual(transfers, [])

    def test_unresolved_case_refunds_both_bonds_after_timeout(self):
        case = self.case(state=self.module.CaseState.UNRESOLVED)
        self.contract.cases[1] = case
        self.module._now = lambda: 301
        self.module.gl.message.sender_address = self.maintainer
        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))
        self.contract.refund_timed_out(1)
        self.assertEqual(transfers, [(self.maintainer, 100), (self.challenger, 100)])
        self.assertEqual(case.state, self.module.CaseState.REFUNDED)
        self.assertTrue(case.settled)


if __name__ == "__main__":
    unittest.main()
