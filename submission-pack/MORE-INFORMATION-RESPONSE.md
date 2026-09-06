# More Information Response

Bound every semantic source to immutable content. Party evidence, consumer constraints, and remediation now require full-commit GitHub blob/raw URLs plus declared SHA-256 digests. Validators fetch raw bytes with `gl.nondet.web.get`, calculate observed hashes, and only decode bounded text after every anchor matches. Unavailable or replaced content returns `UNRESOLVED`, preserves both bonds, and cannot influence settlement.

Strengthened conditional consensus so validators must reproduce the exact remediation requirement, not only the verdict and affected consumer. The accepted requirement is stored with its SHA-256 digest. Remediation validators must return that exact digest alongside their outcome before `SATISFIED` or `FAILED` can activate either payout path.

Added behavioral regressions for immutable semantic evidence, digest mismatch rejection, exact remediation-text agreement, exact requirement-digest agreement, client argument binding, accepted receipt waiting, and authoritative state refresh.
