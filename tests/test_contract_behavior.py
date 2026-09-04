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

    def _evidence_item(self, url, body=b"evidence content"):
        """Helper to create an EvidenceItem with a matching digest."""
        digest = "sha256:" + __import__("hashlib").sha256(body).hexdigest()
        return types.SimpleNamespace(url=url, declared_digest=digest)

    def case(self, **overrides):
        ev_body_m = b"maintainer evidence body"
        ev_body_c = b"challenger evidence body"
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
                    constraint_url="https://consumer.example/constraint",
                )
            ],
            "maintainer_evidence": [
                self._evidence_item("https://maintainer.example/release", ev_body_m)
            ],
            "challenger_evidence": [
                self._evidence_item("https://challenger.example/regression", ev_body_c)
            ],
            "state": self.module.CaseState.CHALLENGED,
            "graph_digest": "sha256:" + "c" * 64,
            "verdict": "",
            "reasoning": "",
            "affected_consumer_id": "",
            "remediation_required": "",
            "remediation_url": "",
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
            constraint_url="https://indexer.example/constraint",
        )
        first.dependencies = [first.dependencies[0], second_dependency]
        second = self.case()
        second.dependencies = [second_dependency, second.dependencies[0]]
        self.assertEqual(self.module._canonical_graph(first), self.module._canonical_graph(second))

    def test_evidence_items_are_bound_to_content_digests(self):
        """Evidence items must carry a declared SHA-256 digest that validators verify."""
        body = b"immutable evidence content"
        digest = "sha256:" + __import__("hashlib").sha256(body).hexdigest()
        item = self.module.EvidenceItem("https://example.com/evidence", digest)
        self.assertEqual(item.url, "https://example.com/evidence")
        self.assertEqual(item.declared_digest, digest)

    def test_fetch_urls_verifies_content_digests(self):
        """_fetch_urls must verify fetched content matches declared evidence digests."""
        body_a = b"first evidence piece"
        body_b = b"second evidence piece"
        digest_a = "sha256:" + __import__("hashlib").sha256(body_a).hexdigest()
        digest_b = "sha256:" + __import__("hashlib").sha256(body_b).hexdigest()

        items = [
            types.SimpleNamespace(url="https://example.com/a", declared_digest=digest_a),
            types.SimpleNamespace(url="https://example.com/b", declared_digest=digest_b),
        ]

        bodies = {
            "https://example.com/a": body_a,
            "https://example.com/b": body_b,
        }
        self.module.gl.nondet.web.get = lambda url: types.SimpleNamespace(status=200, body=bodies[url])

        text, available, digests_match = self.contract._fetch_urls("TEST", items, 7000)

        self.assertTrue(available)
        self.assertTrue(digests_match)
        self.assertIn(digest_a, text)
        self.assertIn(digest_b, text)

    def test_fetch_urls_fails_closed_on_digest_mismatch(self):
        """Evidence with a wrong declared digest must report digests_match=False."""
        body = b"actual content"
        wrong_digest = "sha256:" + "0" * 64

        items = [
            types.SimpleNamespace(url="https://example.com/evidence", declared_digest=wrong_digest),
        ]

        self.module.gl.nondet.web.get = lambda url: types.SimpleNamespace(status=200, body=body)

        text, available, digests_match = self.contract._fetch_urls("TEST", items, 7000)

        self.assertTrue(available)
        self.assertFalse(digests_match)

    def test_fetch_urls_handles_unavailable_evidence(self):
        """Unavailable evidence must report available=False."""
        items = [
            types.SimpleNamespace(url="https://example.com/down", declared_digest="sha256:" + "a" * 64),
        ]

        self.module.gl.nondet.web.get = lambda url: types.SimpleNamespace(status=503, body=b"")

        text, available, digests_match = self.contract._fetch_urls("TEST", items, 7000)

        self.assertFalse(available)
        self.assertTrue(digests_match)  # no content to compare, so no mismatch

    def test_each_party_keeps_an_independent_evidence_budget(self):
        body_m = b"M" * 20_000
        body_c = b"C" * 20_000
        digest_m = "sha256:" + __import__("hashlib").sha256(body_m).hexdigest()
        digest_c = "sha256:" + __import__("hashlib").sha256(body_c).hexdigest()

        items_m = [types.SimpleNamespace(url="https://maintainer.example/release", declared_digest=digest_m)]
        items_c = [types.SimpleNamespace(url="https://challenger.example/regression", declared_digest=digest_c)]

        self.module.gl.nondet.web.get = lambda url: types.SimpleNamespace(
            status=200,
            body=body_m if "maintainer" in url else body_c,
        )

        maintainer_packet, maintainer_available, _ = self.contract._fetch_urls(
            "MAINTAINER", items_m, self.module.SIDE_EVIDENCE_BUDGET
        )
        challenger_packet, challenger_available, _ = self.contract._fetch_urls(
            "CHALLENGER", items_c, self.module.SIDE_EVIDENCE_BUDGET
        )
        self.assertTrue(maintainer_available and challenger_available)
        self.assertEqual(maintainer_packet.split(":\n", 1)[1].count("M"), 7000)
        self.assertEqual(challenger_packet.split(":\n", 1)[1].count("C"), 7000)

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
        case.remediation_url = "https://maintainer.example/adapter"
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
            self.contract.register_consumer(1, "self-client", "https://consumer.example/constraint")

    def test_remediation_fetch_failure_keeps_bonds_and_conditional_state(self):
        case = self.case(
            state=self.module.CaseState.CONDITIONAL,
            affected_consumer_id="wallet-client",
            remediation_required="Publish a compatibility adapter for the affected consumer.",
            remediation_url="https://maintainer.example/adapter",
            remediation_approved=True,
        )
        self.contract.cases[1] = case
        self.module._now = lambda: 250

        # Mock _reproduce_remediation_requirement to return matching result
        def mock_reproduce(c):
            return {
                "verdict": "CONDITIONAL",
                "affected_consumer_id": "wallet-client",
                "reasoning": "Reproduced successfully.",
                "remediation": "Publish a compatibility adapter for the affected consumer.",
            }
        self.contract._reproduce_remediation_requirement = mock_reproduce

        self.module.gl.nondet.web.render = lambda _url, mode="text": (_ for _ in ()).throw(RuntimeError("offline"))
        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))

        outcome = self.contract.verify_remediation(1)

        self.assertEqual(outcome, "UNRESOLVED")
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)
        self.assertEqual(transfers, [])

    def test_remediation_reproduction_mismatch_blocks_settlement(self):
        """If the reproduced remediation requirement does not match the stored one, settlement is blocked."""
        case = self.case(
            state=self.module.CaseState.CONDITIONAL,
            affected_consumer_id="wallet-client",
            remediation_required="Publish a compatibility adapter for the affected consumer.",
            remediation_url="https://maintainer.example/adapter",
            remediation_approved=True,
        )
        self.contract.cases[1] = case
        self.module._now = lambda: 250

        # Mock _reproduce_remediation_requirement to return a DIFFERENT remediation
        def mock_reproduce(c):
            return {
                "verdict": "CONDITIONAL",
                "affected_consumer_id": "wallet-client",
                "reasoning": "Different reasoning.",
                "remediation": "A completely different remediation action.",
            }
        self.contract._reproduce_remediation_requirement = mock_reproduce

        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))

        outcome = self.contract.verify_remediation(1)

        self.assertEqual(outcome, "UNRESOLVED")
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)
        self.assertEqual(transfers, [])
        self.assertIn("does not match", case.reasoning)

    def test_remediation_reproduction_verdict_change_blocks_settlement(self):
        """If the reproduced verdict is no longer CONDITIONAL, settlement is blocked."""
        case = self.case(
            state=self.module.CaseState.CONDITIONAL,
            affected_consumer_id="wallet-client",
            remediation_required="Publish a compatibility adapter.",
            remediation_url="https://maintainer.example/adapter",
            remediation_approved=True,
        )
        self.contract.cases[1] = case
        self.module._now = lambda: 250

        # Mock reproduction returning INCOMPATIBLE instead of CONDITIONAL
        def mock_reproduce(c):
            return {
                "verdict": "INCOMPATIBLE",
                "affected_consumer_id": "",
                "reasoning": "Evidence now shows incompatibility.",
                "remediation": "",
            }
        self.contract._reproduce_remediation_requirement = mock_reproduce

        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))

        outcome = self.contract.verify_remediation(1)

        self.assertEqual(outcome, "UNRESOLVED")
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)

    def test_remediation_reproduction_consumer_change_blocks_settlement(self):
        """If the reproduced affected consumer differs, settlement is blocked."""
        case = self.case(
            state=self.module.CaseState.CONDITIONAL,
            affected_consumer_id="wallet-client",
            remediation_required="Publish a compatibility adapter.",
            remediation_url="https://maintainer.example/adapter",
            remediation_approved=True,
        )
        self.contract.cases[1] = case
        self.module._now = lambda: 250

        # Mock reproduction returning different consumer
        def mock_reproduce(c):
            return {
                "verdict": "CONDITIONAL",
                "affected_consumer_id": "api-indexer",
                "reasoning": "Different consumer affected.",
                "remediation": "Publish a compatibility adapter.",
            }
        self.contract._reproduce_remediation_requirement = mock_reproduce

        transfers = []
        self.contract._transfer = lambda recipient, amount: transfers.append((recipient, amount))

        outcome = self.contract.verify_remediation(1)

        self.assertEqual(outcome, "UNRESOLVED")
        self.assertEqual(case.state, self.module.CaseState.CONDITIONAL)
        self.assertFalse(case.settled)
        self.assertIn("different affected consumer", case.reasoning)

    def test_submit_evidence_requires_matching_digests(self):
        """submit_evidence must accept parallel URL and digest arrays."""
        case = self.case(state=self.module.CaseState.CHALLENGED)
        self.contract.cases[1] = case
        self.module._now = lambda: 150
        self.module.gl.message.sender_address = self.maintainer

        # Mismatched lengths should fail
        with self.assertRaisesRegex(RuntimeError, "corresponding content digest"):
            self.contract.submit_evidence(1, ["https://example.com/e1"], ["sha256:" + "a" * 64, "sha256:" + "b" * 64])

        # Matching lengths should succeed
        self.contract.submit_evidence(
            1,
            ["https://example.com/e1", "https://example.com/e2"],
            ["sha256:" + "a" * 64, "sha256:" + "b" * 64],
        )
        self.assertEqual(len(case.maintainer_evidence), 2)
        self.assertEqual(case.maintainer_evidence[0].url, "https://example.com/e1")
        self.assertEqual(case.maintainer_evidence[0].declared_digest, "sha256:" + "a" * 64)
        self.assertEqual(case.maintainer_evidence[1].url, "https://example.com/e2")
        self.assertEqual(case.maintainer_evidence[1].declared_digest, "sha256:" + "b" * 64)

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
