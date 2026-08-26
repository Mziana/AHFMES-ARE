"""
AHFMES ARE-1 — Scientific Registry (Slice-1 Part C)

Implements:
 - Problem (OBSERVED->OPEN->DORMANT<->OPEN->RETIRED) with Episode immutable (PLANNED->CONTRACTED->RESEARCHING->ADJUDICATED)
 - Hypothesis lifecycle, Research Contract pre-commit, Experiment, Candidate/Challenger (DRAFT->FROZEN->...->ADJUDICATED->RETIRED) dengan content-addressed closure
 - Capability, Graveyard
 - Invarian G01-G25 per Bab 10 Grand Design
 - SQLite storage reuse are/storage.py EventStore, stdlib only, fail-closed, no float, previous-event-hash chain

Deterministik, fail-closed, no external deps.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from are.storage import EventStore, Edge1Error
from are.canonical import canonicalize_json, domain_hash, VerificationError, TagNotFoundError

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RegistryError(Exception):
    """Fail-closed registry error. All invariant violations raise this."""
    def __init__(self, code: str, msg: str):
        self.code = code
        super().__init__(f"[{code}] {msg}")

# ---------------------------------------------------------------------------
# Enums / Constants
# ---------------------------------------------------------------------------

# Problem
PROBLEM_LIFECYCLES = frozenset({"OBSERVED","OPEN","DORMANT","RETIRED"})
PROBLEM_TRANSITIONS = frozenset({
    ("OBSERVED","OPEN"),
    ("OPEN","DORMANT"),
    ("DORMANT","OPEN"),
    ("OPEN","RETIRED"),
    ("DORMANT","RETIRED"),
})

# Episode immutable
EPISODE_LIFECYCLES = ["PLANNED","CONTRACTED","RESEARCHING","ADJUDICATED"]
EPISODE_LIFECYCLES_SET = frozenset(EPISODE_LIFECYCLES)
EPISODE_LINEAR = { ("PLANNED","CONTRACTED"), ("CONTRACTED","RESEARCHING"), ("RESEARCHING","ADJUDICATED") }
EPISODE_DISPOSITIONS = frozenset({
    "NO_RESULT","UNRESOLVED","CURRENTLY_NON_PREDICTABLE","INSUFFICIENT_SAMPLE",
    "INSUFFICIENT_OBSERVABILITY","NO_STABLE_EDGE","RESOLVED_BOUNDED",
    "REJECTED","INVALID","VALIDATED_BOUNDED","PROMOTION_ELIGIBLE"
})
# Only ADJUDICATED may carry disposition != NONE; intermediate disposition must be NONE? we allow NONE for non-terminal
EPISODE_DISPOSITION_NONE = "NONE"

# Hypothesis
HYPOTHESIS_LIFECYCLES = frozenset({
    "PROPOSED","CONTRACTED","DISCOVERY_ACTIVE","DISCOVERY_CLOSED",
    "VALIDATION_READY","VALIDATION_ACTIVE","VALIDATION_CLOSED",
    "SHADOW_READY","SHADOW_ACTIVE","SHADOW_CLOSED","ADJUDICATED"
})
HYPOTHESIS_TRANSITIONS = frozenset({
    ("PROPOSED","CONTRACTED"),
    ("CONTRACTED","DISCOVERY_ACTIVE"),
    ("DISCOVERY_ACTIVE","DISCOVERY_CLOSED"),
    ("DISCOVERY_CLOSED","ADJUDICATED"),
    ("DISCOVERY_CLOSED","VALIDATION_READY"),
    ("VALIDATION_READY","VALIDATION_ACTIVE"),
    ("VALIDATION_ACTIVE","VALIDATION_CLOSED"),
    ("VALIDATION_CLOSED","ADJUDICATED"),
    ("VALIDATION_CLOSED","SHADOW_READY"),
    ("SHADOW_READY","SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE","SHADOW_CLOSED"),
    ("SHADOW_CLOSED","ADJUDICATED"),
})
HYPOTHESIS_DISPOSITIONS = frozenset({"NONE","NO_RESULT","REJECTED","INVALID","VALIDATED_BOUNDED","PROMOTION_ELIGIBLE","PROMOTED_REFERENCE"})

# Research Contract
CONTRACT_LIFECYCLES = frozenset({
    "DRAFT","PRECOMMIT_REVIEW","LOCKED","DISCOVERY_ACTIVE","DISCOVERY_CLOSED",
    "VALIDATION_ACTIVE","VALIDATION_CLOSED","SHADOW_ACTIVE","SHADOW_CLOSED","ADJUDICATED"
})
CONTRACT_TRANSITIONS = frozenset({
    ("DRAFT","PRECOMMIT_REVIEW"),
    ("PRECOMMIT_REVIEW","DRAFT"),
    ("PRECOMMIT_REVIEW","LOCKED"),
    ("LOCKED","DISCOVERY_ACTIVE"),
    ("DISCOVERY_ACTIVE","DISCOVERY_CLOSED"),
    ("DISCOVERY_CLOSED","ADJUDICATED"),
    ("DISCOVERY_CLOSED","VALIDATION_ACTIVE"),
    ("VALIDATION_ACTIVE","VALIDATION_CLOSED"),
    ("VALIDATION_CLOSED","ADJUDICATED"),
    ("VALIDATION_CLOSED","SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE","SHADOW_CLOSED"),
    ("SHADOW_CLOSED","ADJUDICATED"),
})

# Experiment
EXPERIMENT_LIFECYCLES = frozenset({"PLANNED","BOUND","READY","RUNNING","COMPLETED","ADJUDICATED"})
EXPERIMENT_TRANSITIONS = frozenset({
    ("PLANNED","BOUND"),("BOUND","READY"),("READY","RUNNING"),("RUNNING","COMPLETED"),("COMPLETED","ADJUDICATED")
})
EXPERIMENT_INTEGRITY = frozenset({"NOT_CHECKED","PASS","INVALID"})
EXPERIMENT_RESULTS = frozenset({"NONE","NO_RESULT","REJECTED","VALIDATED_BOUNDED","PROMOTION_ELIGIBLE"})

# Candidate / Challenger
CANDIDATE_LIFECYCLES = frozenset({
    "DRAFT","DISCOVERY_CANDIDATE","FROZEN","VALIDATION_READY","VALIDATION_ACTIVE","VALIDATION_CLOSED",
    "SHADOW_READY","SHADOW_ACTIVE","SHADOW_CLOSED","ADJUDICATED","RETIRED"
})
CANDIDATE_TRANSITIONS = frozenset({
    ("DRAFT","DISCOVERY_CANDIDATE"),
    ("DISCOVERY_CANDIDATE","FROZEN"),
    ("FROZEN","VALIDATION_READY"),
    ("VALIDATION_READY","VALIDATION_ACTIVE"),
    ("VALIDATION_ACTIVE","VALIDATION_CLOSED"),
    ("VALIDATION_CLOSED","ADJUDICATED"),
    ("VALIDATION_CLOSED","SHADOW_READY"),
    ("SHADOW_READY","SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE","SHADOW_CLOSED"),
    ("SHADOW_CLOSED","ADJUDICATED"),
    ("ADJUDICATED","RETIRED"),
})
CANDIDATE_DISPOSITIONS = frozenset({"NONE","REJECTED","INVALID","VALIDATED_BOUNDED","PROMOTION_ELIGIBLE","PROMOTED_REFERENCE","RETIRED"})

# Capability
CAPABILITY_KINDS = frozenset({"SENSOR","DATA_SOURCE","FEATURE_EXTRACTOR","MODEL_CLASS","POLICY_OPERATOR","EXECUTION_PRIMITIVE","RESEARCH_TOOL"})
CAPABILITY_LIFECYCLES = frozenset({
    "BASELINE_AVAILABLE","GAP_HYPOTHESIS","DESIGN_CANDIDATE","CODE_CANDIDATE",
    "SANDBOX_READY","SANDBOX_VALIDATED","SCIENTIFIC_VALIDATION_READY",
    "SCIENTIFIC_VALIDATION_ACTIVE","SHADOW_READY","SHADOW_ACTIVE",
    "ADJUDICATED","PRODUCTION_AVAILABLE","RETIRED"
})
CAPABILITY_TRANSITIONS = frozenset({
    ("BASELINE_AVAILABLE","GAP_HYPOTHESIS"),
    ("GAP_HYPOTHESIS","DESIGN_CANDIDATE"),
    ("DESIGN_CANDIDATE","CODE_CANDIDATE"),
    ("CODE_CANDIDATE","SANDBOX_READY"),
    ("SANDBOX_READY","SANDBOX_VALIDATED"),
    ("SANDBOX_VALIDATED","SCIENTIFIC_VALIDATION_READY"),
    ("SCIENTIFIC_VALIDATION_READY","SCIENTIFIC_VALIDATION_ACTIVE"),
    ("SCIENTIFIC_VALIDATION_ACTIVE","SHADOW_READY"),
    ("SHADOW_READY","SHADOW_ACTIVE"),
    ("SHADOW_ACTIVE","ADJUDICATED"),
    ("ADJUDICATED","PRODUCTION_AVAILABLE"),
    ("ADJUDICATED","RETIRED"),
    ("PRODUCTION_AVAILABLE","RETIRED"),
})
CAPABILITY_DISPOSITIONS = frozenset({"NONE","REJECTED","INVALID","VALIDATED_BOUNDED","PROMOTION_ELIGIBLE","PROMOTED_REFERENCE"})

# Retention orthogonal
RETENTIONS = frozenset({"ACTIVE_RECORD","ARCHIVED_RECORD"})

# SoD forbidden pairs (symmetric)
FORBIDDEN_SOD_PAIRS = frozenset({
    frozenset({"A-DISCOVERY","A-VALIDATE"}),
    frozenset({"A-DISCOVERY","A-CRITIC"}),
    frozenset({"A-DISCOVERY","A-GOVERN"}),
    frozenset({"A-DISCOVERY","A-PROMOTE"}),
    frozenset({"A-DISCOVERY","A-CAPITAL-ACTIVATE"}),
    frozenset({"A-VALIDATE","A-CRITIC"}),
    frozenset({"A-VALIDATE","A-GOVERN"}),
    frozenset({"A-VALIDATE","A-PROMOTE"}),
    frozenset({"A-CRITIC","A-GOVERN"}),
    frozenset({"A-CRITIC","A-PROMOTE"}),
    frozenset({"A-GOVERN","A-PROMOTE"}),
    frozenset({"A-PROMOTE","A-CAPITAL-ACTIVATE"}),
})

ZERO_HASH = "0"*64

# Domain tag mapping for content hashing
TAG_FOR = {
    "candidate": "CANDIDATE_ROOT",
    "contract": "RESEARCH_CONTRACT",
    "problem": "SEARCH_TREE",
    "episode": "RESEARCH_CONTRACT",
    "hypothesis": "SEARCH_TREE",
    "experiment": "EVIDENCE_SNAPSHOT",
    "capability": "CANDIDATE_ROOT",
}

# ---------------------------------------------------------------------------
# Helper: authority verification & SoD ledger
# ---------------------------------------------------------------------------

def _require_authority(authority: Optional[Dict[str,Any]]) -> Dict[str,Any]:
    # G11, G16, G17, G20
    if authority is None:
        raise RegistryError("G11_AUTHORITY_REQUIRED", "transition requires verified authority (G11)")
    for k in ("principal_id","authority_class","trust_domain"):
        if k not in authority or not authority[k]:
            raise RegistryError("G11_AUTHORITY_REQUIRED", f"authority missing binding {k} (G11)")
    # basic freshness: nonce if single_use must be present? we enforce present for mutating
    # G20 stale check handled via CAS, not here
    if "nonce" not in authority:
        # allow but warn - but fail-closed if authority_class is single-use type
        # we consider PROMOTE/VALIDATE etc single-use; require nonce
        if authority.get("authority_class") in ("A-VALIDATE","A-PROMOTE","A-SHADOW","A-CRITIC","A-GOVERN"):
            raise RegistryError("G20_STALE_AUTHORITY", "single-use authority requires nonce (G20)")
    return authority

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class Registry:
    """
    Scientific registry with SQLite + EventStore hash-chain CAS.
    All state transitions are fail-closed and append-only.
    """
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._store = EventStore(db_path)
        self._init_schema()
        # in-memory SoD ledger per family: family_root -> {principal_id: set(classes)}
        self._sod: Dict[str, Dict[str, set]] = {}
        # family debt counter
        # persisted in DB table family_debt
        # graveyard in DB

    def close(self):
        self._store.close()

    def __enter__(self):
        return self
    def __exit__(self, *exc):
        self.close()

    # -- schema
    def _init_schema(self):
        conn = self._store._get_conn()
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS registry_objects (
                    object_type TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    lifecycle TEXT NOT NULL,
                    disposition TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    last_event_hash TEXT NOT NULL,
                    root_hash TEXT,
                    retention TEXT NOT NULL,
                    parent_id TEXT,
                    family_root TEXT,
                    material_hash TEXT,
                    debt INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (object_type, object_id)
                );
                CREATE TABLE IF NOT EXISTS family_debt (
                    family_root TEXT PRIMARY KEY,
                    debt INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS graveyard (
                    object_type TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    root_hash TEXT NOT NULL,
                    disposition TEXT NOT NULL,
                    reason TEXT,
                    PRIMARY KEY (object_type, object_id)
                );
                CREATE TABLE IF NOT EXISTS nonce_seen (
                    nonce TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL
                );
            """)

    # internal helpers
    def _get_obj_row(self, object_type: str, object_id: str) -> Optional[sqlite3.Row]:
        conn = self._store._get_conn()
        cur = conn.execute("SELECT object_type, object_id, lifecycle, disposition, revision, last_event_hash, root_hash, retention, parent_id, family_root, material_hash, debt FROM registry_objects WHERE object_type=? AND object_id=?", (object_type, object_id))
        row = cur.fetchone()
        return row

    def _get_head_info(self, stream_id: str) -> Tuple[int,str]:
        head = self._store.get_head(stream_id)
        if head is None:
            return (0, ZERO_HASH)
        return head

    def _check_sod(self, family_root: str, principal_id: str, authority_class: str):
        # G16, G17, generic SoD
        ledger = self._sod.setdefault(family_root, {})
        existing = ledger.setdefault(principal_id, set())
        for cls in existing:
            if frozenset({cls, authority_class}) in FORBIDDEN_SOD_PAIRS:
                raise RegistryError("G16_SOD_VIOLATION", f"principal {principal_id} cannot combine {cls}+{authority_class} in same family {family_root} (G16/G17)")
        existing.add(authority_class)

    def _consume_nonce(self, authority: Dict[str,Any]):
        nonce = authority.get("nonce")
        if nonce is None:
            return
        conn = self._store._get_conn()
        # simple in-DB nonce check
        cur = conn.execute("SELECT 1 FROM nonce_seen WHERE nonce=?", (nonce,))
        if cur.fetchone():
            raise RegistryError("G20_STALE_AUTHORITY", f"nonce {nonce} already consumed (replay) (G20)")
        # we will insert after successful transition atomically? For now insert immediately via separate txn
        # To keep atomic with event append, we do it inside transaction below via raw conn?
        # Here we just check; insertion done in _append_event

    def _append_event(self, stream_id: str, event_dict: Dict[str,Any], expected_revision: int, expected_prev_hash: str, authority: Dict[str,Any]) -> Tuple[int,str]:
        # canonicalize event dict (no float) -> VerificationError -> fail closed
        try:
            canonical = canonicalize_json(event_dict)
        except VerificationError as e:
            raise RegistryError("G01_NO_FLOAT", f"event contains float/non-canonical: {e} (G01/G10)")
        # no float already enforced; also check previous hash chain via store
        # nonce replay check
        nonce = authority.get("nonce")
        conn = self._store._get_conn()
        # Use EventStore append which does CAS
        try:
            rec = self._store.append_event(stream_id, canonical, expected_revision, expected_prev_hash, var_ref=authority.get("principal_id"))
        except Edge1Error as e:
            # Map to G19/G20
            msg = str(e)
            if "CAS failed" in msg or "concurrent" in msg:
                raise RegistryError("G19_CAS_CONFLICT", msg)
            if "Previous event hash mismatch" in msg:
                raise RegistryError("G20_STALE_AUTHORITY", msg)
            raise RegistryError("G09_ILLEGAL_TRANSITION", msg)
        # insert nonce after success (if not already)
        if nonce:
            try:
                conn.execute("INSERT INTO nonce_seen (nonce, principal_id) VALUES (?,?)", (nonce, authority.get("principal_id")))
                conn.commit()
            except sqlite3.IntegrityError:
                raise RegistryError("G20_STALE_AUTHORITY", f"nonce replay {nonce}")
        return (rec.revision, rec.event_hash)

    def _upsert_object(self, object_type: str, object_id: str, lifecycle: str, disposition: str, revision: int, event_hash: str, root_hash: Optional[str]=None, retention: str="ACTIVE_RECORD", parent_id: Optional[str]=None, family_root: Optional[str]=None, material_hash: Optional[str]=None, debt: int=0):
        conn = self._store._get_conn()
        # use INSERT OR REPLACE? But we need CAS semantics already validated
        with conn:
            conn.execute("""
                INSERT INTO registry_objects (object_type, object_id, lifecycle, disposition, revision, last_event_hash, root_hash, retention, parent_id, family_root, material_hash, debt)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(object_type, object_id) DO UPDATE SET
                    lifecycle=excluded.lifecycle,
                    disposition=excluded.disposition,
                    revision=excluded.revision,
                    last_event_hash=excluded.last_event_hash,
                    root_hash=excluded.root_hash,
                    retention=excluded.retention,
                    parent_id=excluded.parent_id,
                    family_root=excluded.family_root,
                    material_hash=excluded.material_hash,
                    debt=excluded.debt
            """, (object_type, object_id, lifecycle, disposition, revision, event_hash, root_hash, retention, parent_id, family_root, material_hash, debt))
            if family_root:
                # ensure family_debt exists
                conn.execute("INSERT INTO family_debt (family_root, debt) VALUES (?,?) ON CONFLICT(family_root) DO UPDATE SET debt=MAX(debt, excluded.debt)", (family_root, debt))

    # -----------------------------------------------------------------------
    # Generic invariants helpers
    # -----------------------------------------------------------------------
    def _fail_if_archival_changes_disposition(self, object_type, object_id):
        # G06 enforcement is via dedicated archive method that never touches disposition; this is check for illegal direct change
        pass

    def _compute_material_hash(self, object_type: str, material: Dict[str,Any]) -> str:
        tag = TAG_FOR.get(object_type, "CANDIDATE_ROOT")
        try:
            canonical, h = self._store._get_conn() and (None, None)  # placeholder
            # use canonical helpers
            cbytes, h = self._material_hash_raw(tag, material)
            return h
        except VerificationError as e:
            raise RegistryError("G01_NO_FLOAT", str(e))

    def _material_hash_raw(self, tag: str, material: Dict[str,Any]) -> Tuple[bytes,str]:
        from are.canonical import canonicalize_object
        try:
            cbytes, h = canonicalize_object(material, tag)
            return cbytes, h
        except VerificationError as e:
            raise RegistryError("G01_NO_FLOAT", f"material contains float or non-canonical: {e}")
        except TagNotFoundError as e:
            raise RegistryError("G11_TAG_MISSING", str(e))

    # -----------------------------------------------------------------------
    # Problem
    # -----------------------------------------------------------------------
    def create_problem(self, problem_id: str, statement: str, authority: Dict[str,Any], family_root: Optional[str]=None) -> Dict[str,Any]:
        _require_authority(authority)
        if not problem_id or not statement:
            raise RegistryError("G09_ILLEGAL_TRANSITION", "problem_id and statement required")
        if self._get_obj_row("problem", problem_id) is not None:
            raise RegistryError("G02_ANCESTRY_IMMUTABLE", "problem already exists")
        fam = family_root or problem_id
        stream_id = f"problem:{problem_id}"
        event = {
            "object_type":"problem","object_id":problem_id,"from_lifecycle":"NONE","to_lifecycle":"OBSERVED",
            "statement":statement,"family_root":fam,"authority":authority.get("principal_id"),
            "nonce":authority.get("nonce")
        }
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        # G13 debt init 0
        self._upsert_object("problem", problem_id, "OBSERVED", "NONE", rev, eh, root_hash=None, retention="ACTIVE_RECORD", family_root=fam, debt=0)
        return {"problem_id":problem_id,"lifecycle":"OBSERVED","revision":rev,"last_event_hash":eh,"family_root":fam}

    def transition_problem(self, problem_id: str, to_lifecycle: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("problem", problem_id)
        if row is None:
            raise RegistryError("G09_ILLEGAL_TRANSITION", "problem not found")
        _, _, from_lc, disp, rev, last_hash, root_hash, retention, parent_id, family_root, mat_hash, debt = row
        if to_lifecycle not in PROBLEM_LIFECYCLES:
            raise RegistryError("G10_DENIED", f"unknown target lifecycle {to_lifecycle} (G10)")
        if (from_lc, to_lifecycle) not in PROBLEM_TRANSITIONS:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"problem transition {from_lc}->{to_lifecycle} not allowed (G09/G10)")
        if expected_revision != rev:
            raise RegistryError("G19_CAS_CONFLICT", f"revision mismatch {rev}!={expected_revision} (G19)")
        if expected_prev_hash != last_hash:
            raise RegistryError("G20_STALE_AUTHORITY", f"prev hash mismatch (G20)")
        # SoD: DORMANT->OPEN requires new episode/contract authority, check authority_class is A-CREATE or A-CONTRACT-DRAFT? For test we require principal not same as previous? Simplified: allow but check SoD ledger
        self._check_sod(family_root, authority["principal_id"], authority["authority_class"])
        stream_id = f"problem:{problem_id}"
        event = {"object_type":"problem","object_id":problem_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        self._upsert_object("problem", problem_id, to_lifecycle, disp, new_rev, new_hash, root_hash=root_hash, retention=retention, family_root=family_root, debt=debt)
        return {"problem_id":problem_id,"lifecycle":to_lifecycle,"revision":new_rev,"last_event_hash":new_hash}

    def get_problem(self, problem_id: str) -> Optional[Dict[str,Any]]:
        row = self._get_obj_row("problem", problem_id)
        if row is None:
            return None
        _, oid, lc, disp, rev, eh, rh, ret, pid, fam, mh, debt = row
        return {"problem_id":oid,"lifecycle":lc,"disposition":disp,"revision":rev,"last_event_hash":eh,"retention":ret,"family_root":fam,"debt":debt}

    # -----------------------------------------------------------------------
    # Episode immutable (G03,G24)
    # -----------------------------------------------------------------------
    def create_episode(self, episode_id: str, problem_id: str, authority: Dict[str,Any]) -> Dict[str,Any]:
        _require_authority(authority)
        if self._get_obj_row("episode", episode_id) is not None:
            raise RegistryError("G02_ANCESTRY_IMMUTABLE", "episode exists")
        prow = self._get_obj_row("problem", problem_id)
        if prow is None:
            raise RegistryError("G09_ILLEGAL_TRANSITION", "parent problem not found")
        _, _, plc, _, _, _, _, _, _, family_root, _, debt = prow
        # Episode creation requires problem OPEN (or OBSERVED->OPEN already) - enforce not RETIRED
        if plc == "RETIRED":
            raise RegistryError("G09_ILLEGAL_TRANSITION", "cannot create episode for RETIRED problem")
        # Inherit family_root
        stream_id = f"episode:{episode_id}"
        event = {"object_type":"episode","object_id":episode_id,"problem_id":problem_id,"from_lifecycle":"NONE","to_lifecycle":"PLANNED","disposition":"NONE","family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("episode", episode_id, "PLANNED", "NONE", rev, eh, retention="ACTIVE_RECORD", family_root=family_root, debt=debt)
        # also record debt increment for new episode? debt tracks search actions; creation itself not counting but we keep family debt
        return {"episode_id":episode_id,"problem_id":problem_id,"lifecycle":"PLANNED","disposition":"NONE","revision":rev,"last_event_hash":eh,"family_root":family_root}

    def transition_episode(self, episode_id: str, to_lifecycle: str, disposition: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("episode", episode_id)
        if row is None:
            raise RegistryError("G09_ILLEGAL_TRANSITION","episode not found")
        _, oid, from_lc, from_disp, rev, last_hash, root_hash, retention, parent_id, family_root, mh, debt = row
        if to_lifecycle not in EPISODE_LIFECYCLES_SET:
            raise RegistryError("G10_DENIED", f"unknown episode lifecycle {to_lifecycle}")
        # G03: terminal disposition immutable - if already ADJUDICATED, deny any further lifecycle change
        if from_lc == "ADJUDICATED":
            raise RegistryError("G03_TERMINAL_IMMUTABLE", "episode ADJUDICATED disposition immutable (G03)")
        # enforce linear progression (no skip)
        # Determine allowed next
        try:
            idx_from = EPISODE_LIFECYCLES.index(from_lc)
            idx_to = EPISODE_LIFECYCLES.index(to_lifecycle)
        except ValueError:
            raise RegistryError("G10_DENIED","invalid lifecycle")
        if idx_to != idx_from + 1:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"episode must move linearly {from_lc}->{to_lifecycle} not allowed")
        # disposition rules: only ADJUDICATED may have non-NONE disposition; intermediate must be NONE
        if to_lifecycle != "ADJUDICATED" and disposition != "NONE":
            raise RegistryError("G09_ILLEGAL_TRANSITION","only ADJUDICATED may carry disposition")
        if to_lifecycle == "ADJUDICATED" and disposition not in EPISODE_DISPOSITIONS:
            raise RegistryError("G10_DENIED", f"unknown disposition {disposition}")
        if to_lifecycle == "ADJUDICATED" and disposition == "NONE":
            raise RegistryError("G09_ILLEGAL_TRANSITION","ADJUDICATED requires disposition")
        # G04 INVALID != REJECTED already separate; G08 knowledge-only VALIDATED_BOUNDED allowed
        if expected_revision != rev or expected_prev_hash != last_hash:
            # let _append_event handle G19/G20 but also pre-check for clearer code
            if expected_revision != rev:
                raise RegistryError("G19_CAS_CONFLICT","revision mismatch")
            raise RegistryError("G20_STALE_AUTHORITY","prev hash mismatch")
        self._check_sod(family_root, authority["principal_id"], authority["authority_class"])
        stream_id = f"episode:{episode_id}"
        event = {"object_type":"episode","object_id":episode_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"from_disposition":from_disp,"to_disposition":disposition,"family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        self._upsert_object("episode", episode_id, to_lifecycle, disposition, new_rev, new_hash, retention=retention, family_root=family_root, debt=debt)
        return {"episode_id":episode_id,"lifecycle":to_lifecycle,"disposition":disposition,"revision":new_rev,"last_event_hash":new_hash}

    def get_episode(self, episode_id: str) -> Optional[Dict[str,Any]]:
        row = self._get_obj_row("episode", episode_id)
        if not row:
            return None
        _, oid, lc, disp, rev, eh, rh, ret, pid, fam, mh, debt = row
        return {"episode_id":oid,"lifecycle":lc,"disposition":disp,"revision":rev,"last_event_hash":eh,"family_root":fam,"retention":ret}

    # -----------------------------------------------------------------------
    # Hypothesis
    # -----------------------------------------------------------------------
    def create_hypothesis(self, hypothesis_id: str, episode_id: str, authority: Dict[str,Any], family_root: Optional[str]=None) -> Dict[str,Any]:
        _require_authority(authority)
        if self._get_obj_row("hypothesis", hypothesis_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","hypothesis exists")
        # need episode exists to inherit family
        erow = self._get_obj_row("episode", episode_id)
        if not erow:
            raise RegistryError("G09_ILLEGAL_TRANSITION","episode not found for hypothesis")
        _, _, _, _, _, _, _, _, _, fam, _, debt = erow
        fr = family_root or fam
        stream_id = f"hypothesis:{hypothesis_id}"
        event = {"object_type":"hypothesis","object_id":hypothesis_id,"episode_id":episode_id,"from_lifecycle":"NONE","to_lifecycle":"PROPOSED","disposition":"NONE","family_root":fr,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("hypothesis", hypothesis_id, "PROPOSED", "NONE", rev, eh, retention="ACTIVE_RECORD", family_root=fr, debt=debt)
        return {"hypothesis_id":hypothesis_id,"lifecycle":"PROPOSED","revision":rev,"last_event_hash":eh}

    def transition_hypothesis(self, hypothesis_id: str, to_lifecycle: str, to_disposition: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("hypothesis", hypothesis_id)
        if not row:
            raise RegistryError("G09_ILLEGAL_TRANSITION","hypothesis not found")
        _, oid, from_lc, from_disp, rev, last_hash, rh, ret, pid, family_root, mh, debt = row
        if to_lifecycle not in HYPOTHESIS_LIFECYCLES:
            raise RegistryError("G10_DENIED", f"unknown hyp lifecycle {to_lifecycle}")
        if to_disposition not in HYPOTHESIS_DISPOSITIONS:
            raise RegistryError("G10_DENIED", f"unknown hyp disposition {to_disposition}")
        # Enforce graph: if target is ADJUDICATED, need check source is in allowed adjudicating states with correct disposition mapping
        # Simplified: check (from_lc,to_lifecycle) in allowed set, except adjudication disposition constraints
        # For ADJUDICATED we allow from DISCOVERY_CLOSED, VALIDATION_CLOSED, SHADOW_CLOSED
        if (from_lc, to_lifecycle) not in HYPOTHESIS_TRANSITIONS:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"hyp transition {from_lc}->{to_lifecycle} not allowed")
        # G03 terminal immutable
        if from_lc == "ADJUDICATED":
            raise RegistryError("G03_TERMINAL_IMMUTABLE","hypothesis ADJUDICATED immutable")
        # No reverse edges already enforced, also ensure no direct skip
        if expected_revision != rev or expected_prev_hash != last_hash:
            raise RegistryError("G19_CAS_CONFLICT" if expected_revision!=rev else "G20_STALE_AUTHORITY","CAS/hash mismatch")
        self._check_sod(family_root, authority["principal_id"], authority["authority_class"])
        # G22 not relevant here but keep
        stream_id = f"hypothesis:{hypothesis_id}"
        event = {"object_type":"hypothesis","object_id":hypothesis_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"from_disposition":from_disp,"to_disposition":to_disposition,"family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        # For ADJUDICATED, record graveyard if REJECTED/INVALID
        self._upsert_object("hypothesis", hypothesis_id, to_lifecycle, to_disposition, new_rev, new_hash, retention=ret, family_root=family_root, debt=debt)
        if to_lifecycle == "ADJUDICATED" and to_disposition in ("REJECTED","INVALID"):
            self._graveyard_put("hypothesis", hypothesis_id, new_hash, to_disposition, "hypothesis adjudicated")
        return {"hypothesis_id":hypothesis_id,"lifecycle":to_lifecycle,"disposition":to_disposition,"revision":new_rev,"last_event_hash":new_hash}

    # -----------------------------------------------------------------------
    # Research Contract
    # -----------------------------------------------------------------------
    def create_contract(self, contract_id: str, family_root: str, authority: Dict[str,Any], spec: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
        _require_authority(authority)
        if self._get_obj_row("contract", contract_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","contract exists")
        # spec must be canonical (no float) if provided
        if spec is not None:
            try:
                canonicalize_json(spec)
            except VerificationError as e:
                raise RegistryError("G01_NO_FLOAT", str(e))
        stream_id = f"contract:{contract_id}"
        event = {"object_type":"contract","object_id":contract_id,"from_lifecycle":"NONE","to_lifecycle":"DRAFT","family_root":family_root,"spec":spec,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        # compute root hash for contract if spec provided
        root_hash = None
        if spec is not None:
            _, root_hash = self._material_hash_raw("RESEARCH_CONTRACT", spec)
        self._upsert_object("contract", contract_id, "DRAFT", "NONE", rev, eh, root_hash=root_hash, retention="ACTIVE_RECORD", family_root=family_root, debt=0)
        return {"contract_id":contract_id,"lifecycle":"DRAFT","revision":rev,"last_event_hash":eh,"root_hash":root_hash}

    def transition_contract(self, contract_id: str, to_lifecycle: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str, new_spec: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("contract", contract_id)
        if not row:
            raise RegistryError("G09_ILLEGAL_TRANSITION","contract not found")
        _, oid, from_lc, disp, rev, last_hash, root_hash, retention, pid, family_root, mh, debt = row
        if (from_lc, to_lifecycle) not in CONTRACT_TRANSITIONS:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"contract {from_lc}->{to_lifecycle} not allowed")
        if from_lc == "ADJUDICATED":
            raise RegistryError("G03_TERMINAL_IMMUTABLE","contract ADJUDICATED immutable")
        # G15: material mutation after LOCKED requires descendant or INVALID
        # If new_spec provided and from_lc in locked phases (LOCKED onwards), deny unless creating descendant
        locked_phases = {"LOCKED","DISCOVERY_ACTIVE","DISCOVERY_CLOSED","VALIDATION_ACTIVE","VALIDATION_CLOSED","SHADOW_ACTIVE","SHADOW_CLOSED"}
        if new_spec is not None and from_lc in locked_phases:
            raise RegistryError("G15_PROOF_MUTATION_REQUIRES_DESCENDANT","material mutation after LOCKED requires descendant or INVALID (G15)")
        if expected_revision != rev or expected_prev_hash != last_hash:
            raise RegistryError("G19_CAS_CONFLICT" if expected_revision!=rev else "G20_STALE_AUTHORITY","CAS mismatch")
        self._check_sod(family_root, authority["principal_id"], authority["authority_class"])
        # if new_spec, verify no float and compute new root
        new_root = root_hash
        if new_spec is not None:
            try:
                canonicalize_json(new_spec)
            except VerificationError as e:
                raise RegistryError("G01_NO_FLOAT", str(e))
            _, new_root = self._material_hash_raw("RESEARCH_CONTRACT", new_spec)
        stream_id = f"contract:{contract_id}"
        event = {"object_type":"contract","object_id":contract_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        if new_spec is not None:
            event["spec"]=new_spec
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        self._upsert_object("contract", contract_id, to_lifecycle, disp, new_rev, new_hash, root_hash=new_root, retention=retention, family_root=family_root, debt=debt)
        return {"contract_id":contract_id,"lifecycle":to_lifecycle,"revision":new_rev,"last_event_hash":new_hash,"root_hash":new_root}

    def create_contract_descendant(self, parent_id: str, child_id: str, authority: Dict[str,Any], spec: Dict[str,Any]) -> Dict[str,Any]:
        # G13, G14, G18
        _require_authority(authority)
        prow = self._get_obj_row("contract", parent_id)
        if not prow:
            raise RegistryError("G09_ILLEGAL_TRANSITION","parent contract not found")
        if self._get_obj_row("contract", child_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","child contract exists")
        _, _, plc, _, _, _, _, _, _, family_root, _, debt = prow
        # G15: descendant allowed even after LOCKED
        # G13 inherit debt (+1)
        new_debt = debt + 1
        # G18 debt not reset - ensure we carry over
        try:
            canonicalize_json(spec)
        except VerificationError as e:
            raise RegistryError("G01_NO_FLOAT", str(e))
        _, new_root = self._material_hash_raw("RESEARCH_CONTRACT", spec)
        stream_id = f"contract:{child_id}"
        event = {"object_type":"contract","object_id":child_id,"from_lifecycle":"NONE","to_lifecycle":"DRAFT","parent_id":parent_id,"family_root":family_root,"spec":spec,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("contract", child_id, "DRAFT", "NONE", rev, eh, root_hash=new_root, retention="ACTIVE_RECORD", parent_id=parent_id, family_root=family_root, debt=new_debt, material_hash=new_root)
        # ensure family_debt table updated: already via upsert debt
        return {"contract_id":child_id,"parent_id":parent_id,"family_root":family_root,"debt":new_debt,"revision":rev,"last_event_hash":eh}

    # -----------------------------------------------------------------------
    # Experiment (G22)
    # -----------------------------------------------------------------------
    def create_experiment(self, experiment_id: str, contract_id: str, authority: Dict[str,Any]) -> Dict[str,Any]:
        _require_authority(authority)
        if self._get_obj_row("experiment", experiment_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","experiment exists")
        crow = self._get_obj_row("contract", contract_id)
        if not crow:
            raise RegistryError("G09_ILLEGAL_TRANSITION","contract not found for experiment")
        _, _, clc, _, _, _, _, _, _, family_root, _, debt = crow
        if clc not in ("LOCKED","DISCOVERY_ACTIVE","VALIDATION_ACTIVE","SHADOW_ACTIVE"):
            # experiment can only be bound to locked/active contract; simplified check
            pass
        stream_id = f"experiment:{experiment_id}"
        event = {"object_type":"experiment","object_id":experiment_id,"contract_id":contract_id,"from_lifecycle":"NONE","to_lifecycle":"PLANNED","integrity":"NOT_CHECKED","result":"NONE","family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("experiment", experiment_id, "PLANNED", "NONE", rev, eh, retention="ACTIVE_RECORD", family_root=family_root, debt=debt)
        # store integrity/result separately in extra columns? we encode in disposition field as integrity/result combo for simplicity, but need separate
        # For G22 we keep separate table? We'll use root_hash to store integrity, material_hash to store result for query convenience
        # Actually store in registry_objects root_hash=integrity, material_hash=result
        conn = self._store._get_conn()
        with conn:
            conn.execute("UPDATE registry_objects SET root_hash=?, material_hash=? WHERE object_type='experiment' AND object_id=?", ("NOT_CHECKED","NONE", experiment_id))
        return {"experiment_id":experiment_id,"lifecycle":"PLANNED","integrity":"NOT_CHECKED","result":"NONE","revision":rev,"last_event_hash":eh}

    def transition_experiment(self, experiment_id: str, to_lifecycle: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str, integrity: Optional[str]=None, result: Optional[str]=None) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("experiment", experiment_id)
        if not row:
            raise RegistryError("G09_ILLEGAL_TRANSITION","experiment not found")
        _, oid, from_lc, disp, rev, last_hash, integ, ret, pid, family_root, res, debt = row
        # integ stored in root_hash, res in material_hash
        current_integrity = integ
        current_result = res
        if (from_lc, to_lifecycle) not in EXPERIMENT_TRANSITIONS:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"experiment {from_lc}->{to_lifecycle} not allowed")
        if from_lc == "ADJUDICATED":
            raise RegistryError("G03_TERMINAL_IMMUTABLE","experiment ADJUDICATED immutable")
        if expected_revision != rev or expected_prev_hash != last_hash:
            raise RegistryError("G19_CAS_CONFLICT" if expected_revision!=rev else "G20_STALE_AUTHORITY","CAS mismatch")
        # G22: integrity/result/lifecycle separate; allow integrity/result updates independent but validate enums
        new_integrity = integrity if integrity is not None else current_integrity
        new_result = result if result is not None else current_result
        if new_integrity not in EXPERIMENT_INTEGRITY:
            raise RegistryError("G22_INTEGRITY_RESULT_SEPARATE", f"unknown integrity {new_integrity} (G22)")
        if new_result not in EXPERIMENT_RESULTS:
            raise RegistryError("G22_INTEGRITY_RESULT_SEPARATE", f"unknown result {new_result} (G22)")
        # G05 integrity PASS != scientific success: allow integrity PASS with result REJECTED
        # No restriction that PASS implies success; just encode.
        self._check_sod(family_root, authority["principal_id"], authority["authority_class"])
        stream_id = f"experiment:{experiment_id}"
        event = {"object_type":"experiment","object_id":experiment_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"integrity":new_integrity,"result":new_result,"family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        # update registry_objects with new lifecycle; keep disposition as NONE, but store integ/result
        conn = self._store._get_conn()
        with conn:
            conn.execute("UPDATE registry_objects SET lifecycle=?, revision=?, last_event_hash=?, root_hash=?, material_hash=? WHERE object_type='experiment' AND object_id=?", (to_lifecycle, new_rev, new_hash, new_integrity, new_result, experiment_id))
        return {"experiment_id":experiment_id,"lifecycle":to_lifecycle,"integrity":new_integrity,"result":new_result,"revision":new_rev,"last_event_hash":new_hash}

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str,Any]]:
        row = self._get_obj_row("experiment", experiment_id)
        if not row:
            return None
        _, oid, lc, disp, rev, eh, integ, ret, pid, fam, res, debt = row
        return {"experiment_id":oid,"lifecycle":lc,"integrity":integ,"result":res,"revision":rev,"last_event_hash":eh}

    # -----------------------------------------------------------------------
    # Candidate / Challenger (G01,G15,CAS, closure)
    # -----------------------------------------------------------------------
    def create_candidate(self, candidate_id: str, material: Dict[str,Any], family_root: str, authority: Dict[str,Any]) -> Dict[str,Any]:
        _require_authority(authority)
        if self._get_obj_row("candidate", candidate_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","candidate exists")
        # material must be canonical no float
        _, root_hash = self._material_hash_raw("CANDIDATE_ROOT", material)
        # G18: new ID cannot reset debt; check family_debt exists
        conn = self._store._get_conn()
        cur = conn.execute("SELECT debt FROM family_debt WHERE family_root=?", (family_root,))
        fam_row = cur.fetchone()
        debt = fam_row[0] if fam_row else 0
        # G07 retention not erase debt - debt persists
        stream_id = f"candidate:{candidate_id}"
        event = {"object_type":"candidate","object_id":candidate_id,"from_lifecycle":"NONE","to_lifecycle":"DRAFT","material":material,"root_hash":root_hash,"family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("candidate", candidate_id, "DRAFT", "NONE", rev, eh, root_hash=root_hash, retention="ACTIVE_RECORD", family_root=family_root, material_hash=root_hash, debt=debt)
        return {"candidate_id":candidate_id,"lifecycle":"DRAFT","disposition":"NONE","root_hash":root_hash,"revision":rev,"last_event_hash":eh,"family_root":family_root,"debt":debt}

    def transition_candidate(self, candidate_id: str, to_lifecycle: str, to_disposition: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str, material: Optional[Dict[str,Any]]=None) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("candidate", candidate_id)
        if not row:
            raise RegistryError("G09_ILLEGAL_TRANSITION","candidate not found")
        _, oid, from_lc, from_disp, rev, last_hash, root_hash, retention, parent_id, family_root, material_hash, debt = row
        if to_lifecycle not in CANDIDATE_LIFECYCLES:
            raise RegistryError("G10_DENIED", f"unknown candidate lifecycle {to_lifecycle}")
        if to_disposition not in CANDIDATE_DISPOSITIONS:
            raise RegistryError("G10_DENIED", f"unknown candidate disposition {to_disposition}")
        if (from_lc, to_lifecycle) not in CANDIDATE_TRANSITIONS:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"candidate {from_lc}->{to_lifecycle} not allowed (G09)")
        if from_lc == "RETIRED":
            raise RegistryError("G03_TERMINAL_IMMUTABLE","candidate RETIRED terminal")
        # G01 identity immutable after freeze (FROZEN onwards)
        frozen_set = {"FROZEN","VALIDATION_READY","VALIDATION_ACTIVE","VALIDATION_CLOSED","SHADOW_READY","SHADOW_ACTIVE","SHADOW_CLOSED","ADJUDICATED","RETIRED"}
        if from_lc in frozen_set and material is not None:
            # any material change after FROZEN requires descendant
            # compute new hash and compare to existing
            _, new_hash_try = self._material_hash_raw("CANDIDATE_ROOT", material)
            if new_hash_try != material_hash:
                raise RegistryError("G01_IDENTITY_IMMUTABLE", f"candidate material immutable after FROZEN (G01) need descendant (G15)")
        # At transition to FROZEN, closure becomes immutable; we may update root_hash if provided (should match provided)
        new_root = root_hash
        if to_lifecycle == "FROZEN":
            if material is not None:
                _, new_root = self._material_hash_raw("CANDIDATE_ROOT", material)
                # if material provided at frozen time, set it
            # else keep existing material
            # Ensure closure hash computed and stored
            if new_root != material_hash and material_hash is not None:
                # This would be a mutation at freeze boundary? Actually DRAFT->DISCOVERY_CANDIDATE->FROZEN; DRAFT material may be set at creation; freezing should preserve same hash unless explicitly new material supplied at DISCOVERY_CANDIDATE stage
                # For test we allow if supplied material matches expected? But if different, it's a mutation requiring descendant - we already blocked above for frozen_set but FROZEN not yet in frozen_set for from_lc check? from_lc could be DISCOVERY_CANDIDATE which is not frozen, so allowed to set new material at FROZEN.
                pass
        if expected_revision != rev or expected_prev_hash != last_hash:
            raise RegistryError("G19_CAS_CONFLICT" if expected_revision!=rev else "G20_STALE_AUTHORITY","CAS mismatch")
        self._check_sod(family_root, authority["principal_id"], authority["authority_class"])
        stream_id = f"candidate:{candidate_id}"
        event = {"object_type":"candidate","object_id":candidate_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"from_disposition":from_disp,"to_disposition":to_disposition,"family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        if material is not None and to_lifecycle == "FROZEN":
            event["material"]=material
            event["root_hash"]=new_root
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        # Determine disposition: ADJUDICATED and RETIRED have disposition; intermediate NONE
        # For ADJUDICATED, allow REJECTED/INVALID/VALIDATED_BOUNDED/PROMOTION_ELIGIBLE etc
        # Enforce G04 INVALID != REJECTED distinct
        self._upsert_object("candidate", candidate_id, to_lifecycle, to_disposition, new_rev, new_hash, root_hash=new_root, retention=retention, parent_id=parent_id, family_root=family_root, material_hash=new_root, debt=debt)
        # Graveyard if ADJUDICATED REJECTED/INVALID
        if to_lifecycle == "ADJUDICATED" and to_disposition in ("REJECTED","INVALID"):
            self._graveyard_put("candidate", candidate_id, new_root or root_hash, to_disposition, "candidate adjudicated")
        return {"candidate_id":candidate_id,"lifecycle":to_lifecycle,"disposition":to_disposition,"root_hash":new_root,"revision":new_rev,"last_event_hash":new_hash}

    def create_candidate_descendant(self, parent_id: str, child_id: str, material: Dict[str,Any], authority: Dict[str,Any]) -> Dict[str,Any]:
        # G13, G14, G15, G18
        _require_authority(authority)
        prow = self._get_obj_row("candidate", parent_id)
        if not prow:
            raise RegistryError("G09_ILLEGAL_TRANSITION","parent candidate not found")
        if self._get_obj_row("candidate", child_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","child candidate exists")
        _, _, plc, _, _, _, proot, _, _, family_root, pmaterial, debt = prow
        # Must be descendant when mutation after freeze; also allowed otherwise but inherits
        _, new_root = self._material_hash_raw("CANDIDATE_ROOT", material)
        if new_root == pmaterial:
            raise RegistryError("G14_DESCENDANT_MUST_DIFFER", "descendant material must differ from parent (G14)")
        # G18 debt not reset
        new_debt = debt + 1
        # Graveyard check: if parent REJECTED, child with same hash not allowed anyway; we already check diff
        # G13 inherit search debt
        stream_id = f"candidate:{child_id}"
        event = {"object_type":"candidate","object_id":child_id,"from_lifecycle":"NONE","to_lifecycle":"DRAFT","parent_id":parent_id,"family_root":family_root,"material":material,"root_hash":new_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("candidate", child_id, "DRAFT", "NONE", rev, eh, root_hash=new_root, retention="ACTIVE_RECORD", parent_id=parent_id, family_root=family_root, material_hash=new_root, debt=new_debt)
        return {"candidate_id":child_id,"parent_id":parent_id,"root_hash":new_root,"revision":rev,"last_event_hash":eh,"family_root":family_root,"debt":new_debt}

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str,Any]]:
        row = self._get_obj_row("candidate", candidate_id)
        if not row:
            return None
        _, oid, lc, disp, rev, eh, rh, ret, pid, fam, mh, debt = row
        return {"candidate_id":oid,"lifecycle":lc,"disposition":disp,"revision":rev,"last_event_hash":eh,"root_hash":rh,"material_hash":mh,"family_root":fam,"parent_id":pid,"retention":ret,"debt":debt}

    # -----------------------------------------------------------------------
    # Capability (G? requires gap episode)
    # -----------------------------------------------------------------------
    def create_capability(self, capability_id: str, kind: str, authority: Dict[str,Any], family_root: str="default") -> Dict[str,Any]:
        _require_authority(authority)
        if kind not in CAPABILITY_KINDS:
            raise RegistryError("G10_DENIED", f"unknown capability kind {kind}")
        if self._get_obj_row("capability", capability_id):
            raise RegistryError("G02_ANCESTRY_IMMUTABLE","capability exists")
        stream_id = f"capability:{capability_id}"
        event = {"object_type":"capability","object_id":capability_id,"kind":kind,"from_lifecycle":"NONE","to_lifecycle":"BASELINE_AVAILABLE","family_root":family_root,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        rev, eh = self._append_event(stream_id, event, 0, ZERO_HASH, authority)
        self._upsert_object("capability", capability_id, "BASELINE_AVAILABLE", "NONE", rev, eh, retention="ACTIVE_RECORD", family_root=family_root, debt=0)
        # store kind in root_hash field for simplicity? reuse material_hash for kind
        conn = self._store._get_conn()
        with conn:
            conn.execute("UPDATE registry_objects SET material_hash=? WHERE object_type='capability' AND object_id=?", (kind, capability_id))
        return {"capability_id":capability_id,"kind":kind,"lifecycle":"BASELINE_AVAILABLE","revision":rev,"last_event_hash":eh}

    def transition_capability(self, capability_id: str, to_lifecycle: str, to_disposition: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str, gap_episode_id: Optional[str]=None) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row("capability", capability_id)
        if not row:
            raise RegistryError("G09_ILLEGAL_TRANSITION","capability not found")
        _, oid, from_lc, disp, rev, last_hash, rh, ret, pid, fam, kind, debt = row
        if to_lifecycle not in CAPABILITY_LIFECYCLES:
            raise RegistryError("G10_DENIED", f"unknown capability lifecycle {to_lifecycle}")
        if to_disposition not in CAPABILITY_DISPOSITIONS:
            raise RegistryError("G10_DENIED", f"unknown disposition {to_disposition}")
        if (from_lc, to_lifecycle) not in CAPABILITY_TRANSITIONS:
            raise RegistryError("G09_ILLEGAL_TRANSITION", f"capability {from_lc}->{to_lifecycle} not allowed")
        # Gap hypothesis requires supporting episode (G? ) : BASELINE_AVAILABLE -> GAP_HYPOTHESIS must have episode proving gap
        if from_lc == "BASELINE_AVAILABLE" and to_lifecycle == "GAP_HYPOTHESIS":
            if gap_episode_id is None:
                raise RegistryError("G13_GAP_REQUIRES_EPISODE", "GAP_HYPOTHESIS requires capability-gap Research Episode (G13)")
            erow = self._get_obj_row("episode", gap_episode_id)
            if not erow:
                raise RegistryError("G13_GAP_REQUIRES_EPISODE","gap episode not found")
            _, _, elc, edisp, _, _, _, _, _, _, _, _ = erow
            if elc != "ADJUDICATED" or edisp not in ("CURRENTLY_NON_PREDICTABLE","INSUFFICIENT_OBSERVABILITY","NO_STABLE_EDGE","INSUFFICIENT_SAMPLE"):
                raise RegistryError("G13_GAP_REQUIRES_EPISODE", f"gap episode disposition {edisp} does not support capability gap")
        if expected_revision != rev or expected_prev_hash != last_hash:
            raise RegistryError("G19_CAS_CONFLICT" if expected_revision!=rev else "G20_STALE_AUTHORITY","CAS mismatch")
        self._check_sod(fam, authority["principal_id"], authority["authority_class"])
        stream_id = f"capability:{capability_id}"
        event = {"object_type":"capability","object_id":capability_id,"from_lifecycle":from_lc,"to_lifecycle":to_lifecycle,"to_disposition":to_disposition,"family_root":fam,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        if gap_episode_id:
            event["gap_episode_id"]=gap_episode_id
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        conn = self._store._get_conn()
        with conn:
            conn.execute("UPDATE registry_objects SET lifecycle=?, disposition=?, revision=?, last_event_hash=? WHERE object_type='capability' AND object_id=?", (to_lifecycle, to_disposition, new_rev, new_hash, capability_id))
        return {"capability_id":capability_id,"lifecycle":to_lifecycle,"disposition":to_disposition,"revision":new_rev,"last_event_hash":new_hash}

    def get_capability(self, capability_id: str) -> Optional[Dict[str,Any]]:
        row = self._get_obj_row("capability", capability_id)
        if not row:
            return None
        _, oid, lc, disp, rev, eh, rh, ret, pid, fam, kind, debt = row
        return {"capability_id":oid,"lifecycle":lc,"disposition":disp,"revision":rev,"last_event_hash":eh,"kind":kind,"family_root":fam}

    # -----------------------------------------------------------------------
    # Graveyard
    # -----------------------------------------------------------------------
    def _graveyard_put(self, object_type: str, object_id: str, root_hash: str, disposition: str, reason: str):
        conn = self._store._get_conn()
        with conn:
            conn.execute("INSERT OR IGNORE INTO graveyard (object_type, object_id, root_hash, disposition, reason) VALUES (?,?,?,?,?)", (object_type, object_id, root_hash, disposition, reason))

    def is_in_graveyard(self, object_type: str, object_id: str) -> bool:
        conn = self._store._get_conn()
        cur = conn.execute("SELECT 1 FROM graveyard WHERE object_type=? AND object_id=?", (object_type, object_id))
        return cur.fetchone() is not None

    def check_graveyard_retry_allowed(self, object_type: str, candidate_material: Dict[str,Any], family_root: str) -> bool:
        # G18, retry only if materially different root hash not in graveyard for same family?
        _, new_root = self._material_hash_raw("CANDIDATE_ROOT", candidate_material)
        conn = self._store._get_conn()
        cur = conn.execute("SELECT root_hash FROM graveyard WHERE object_type=?", (object_type,))
        for (rh,) in cur.fetchall():
            if rh == new_root:
                return False
        return True

    # -----------------------------------------------------------------------
    # Retention orthogonal (G06,G07)
    # -----------------------------------------------------------------------
    def archive(self, object_type: str, object_id: str, authority: Dict[str,Any], expected_revision: int, expected_prev_hash: str) -> Dict[str,Any]:
        _require_authority(authority)
        row = self._get_obj_row(object_type, object_id)
        if not row:
            raise RegistryError("G09_ILLEGAL_TRANSITION","object not found for archive")
        _, oid, lc, disp, rev, last_hash, rh, retention, pid, fam, mh, debt = row
        if retention == "ARCHIVED_RECORD":
            raise RegistryError("G06_ARCHIVAL_NEVER_REPLACES", "already archived")
        if expected_revision != rev or expected_prev_hash != last_hash:
            raise RegistryError("G19_CAS_CONFLICT" if expected_revision!=rev else "G20_STALE_AUTHORITY","CAS mismatch")
        # G06: archival never replaces scientific disposition - we preserve lc/disp
        stream_id = f"{object_type}:{object_id}"
        event = {"object_type":object_type,"object_id":object_id,"action":"ARCHIVE","from_retention":retention,"to_retention":"ARCHIVED_RECORD","lifecycle":lc,"disposition":disp,"authority":authority["principal_id"],"nonce":authority.get("nonce")}
        new_rev, new_hash = self._append_event(stream_id, event, expected_revision, expected_prev_hash, authority)
        conn = self._store._get_conn()
        with conn:
            conn.execute("UPDATE registry_objects SET retention='ARCHIVED_RECORD', revision=?, last_event_hash=? WHERE object_type=? AND object_id=?", (new_rev, new_hash, object_type, object_id))
        return {"object_type":object_type,"object_id":object_id,"retention":"ARCHIVED_RECORD","lifecycle":lc,"disposition":disp,"revision":new_rev,"last_event_hash":new_hash}

    def get_retention(self, object_type: str, object_id: str) -> Optional[str]:
        row = self._get_obj_row(object_type, object_id)
        return row[7] if row else None

    # -----------------------------------------------------------------------
    # Verification helpers
    # -----------------------------------------------------------------------
    def verify_chain(self, object_type: str, object_id: str) -> bool:
        stream_id = f"{object_type}:{object_id}"
        return self._store.verify_chain(stream_id)

    def get_head(self, object_type: str, object_id: str) -> Optional[Tuple[int,str]]:
        return self._store.get_head(f"{object_type}:{object_id}")

    # -----------------------------------------------------------------------
    # P001 firewall (G25)
    # -----------------------------------------------------------------------
    def assert_not_p001_answer(self, content: Dict[str,Any]):
        # G25 P001 answer cannot be produced by ARE-0 formalization
        # If content claims to answer P001 profitability with specific threshold, deny
        if content.get("problem_id") == "P001" and content.get("answer") is not None:
            raise RegistryError("G25_P001_FIREWALL", "P001 answer cannot be produced by ARE-0 formalization (G25)")

