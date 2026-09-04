import atexit
import json
import os
from hypothesis import given, settings
import hypothesis.strategies as st


class RelayModel:
    def __init__(self, job_id: int = 1):
        self.job_id = job_id
        self.status = "pending"
        self.attempts = 0
        self.dispatches = 0
        self.worker_id = None
        self.durable_effects = []
        self.effect_attempts = 0
        self.history = []

    def claim(self, worker_id: str = "worker-1"):
        if self.status != "pending":
            return False
        self.status = "running"
        self.attempts += 1
        self.dispatches += 1
        self.worker_id = worker_id
        self.history.append(f"claim({worker_id})")
        return True

    def effect_write(self, allow_stale: bool = False):
        if not allow_stale and self.status != "running":
            return False
        key = f"job:{self.job_id}"
        self.effect_attempts += 1
        is_mutant = os.environ.get("DIN5_MUTANT") == "no_dedup"
        if is_mutant:
            self.durable_effects.append(key)
        else:
            if key not in self.durable_effects:
                self.durable_effects.append(key)
        self.history.append("effect_write()")
        return True

    def crash(self):
        if self.status != "running":
            return False
        self.worker_id = None
        self.history.append("crash()")
        return True

    def reclaim(self):
        if self.status != "running":
            return False
        self.status = "pending"
        self.worker_id = None
        self.history.append("reclaim()")
        return True

    def mark_succeeded(self):
        if self.status != "running":
            return False
        self.status = "succeeded"
        self.worker_id = None
        self.history.append("mark_succeeded()")
        return True

    def mark_failed(self):
        if self.status != "running":
            return False
        self.status = "failed"
        self.worker_id = None
        self.history.append("mark_failed()")
        return True

    def mark_dead_letter(self):
        if self.status != "running":
            return False
        self.status = "dead_letter"
        self.worker_id = None
        self.history.append("mark_dead_letter()")
        return True

    def apply_action(self, action: str, worker_id: str = "worker-1"):
        if action == "claim":
            return self.claim(worker_id)
        elif action == "effect_write":
            return self.effect_write()
        elif action == "crash":
            return self.crash()
        elif action == "reclaim":
            return self.reclaim()
        elif action == "mark_succeeded":
            return self.mark_succeeded()
        elif action == "mark_failed":
            return self.mark_failed()
        elif action == "mark_dead_letter":
            return self.mark_dead_letter()
        return False


# ==========================================
# C2 Deterministic Test Nodes
# ==========================================

def test_zero_writes_has_zero_effects():
    model = RelayModel()
    assert len(model.durable_effects) == 0


def test_one_dispatch_one_effect():
    model = RelayModel()
    assert model.claim("worker-1")
    assert model.effect_write()
    assert model.mark_succeeded()
    assert model.dispatches == 1
    assert len(model.durable_effects) == 1
    assert model.status == "succeeded"


def test_reclaim_two_dispatches_one_effect():
    model = RelayModel()
    assert model.claim("worker-1")
    assert model.effect_write()
    assert model.crash()
    assert model.reclaim()
    assert model.claim("worker-2")
    assert model.effect_write()
    assert model.mark_succeeded()
    assert model.dispatches >= 2
    assert model.attempts == 2
    assert len(model.durable_effects) == 1
    assert model.status == "succeeded"


def test_p27_extra_dispatch_preserves_safety():
    model = RelayModel()
    # 3 attempts
    for i in range(1, 4):
        assert model.claim(f"worker-{i}")
        assert model.effect_write()
        assert model.crash()
        assert model.reclaim()
    # P-27 overdraft to 4th attempt
    assert model.claim("worker-4")
    assert model.effect_write()
    assert model.mark_dead_letter()
    assert model.dispatches >= 2
    assert model.attempts == 4
    assert len(model.durable_effects) == 1
    assert model.status == "dead_letter"


# ==========================================
# C3 & C4 Hypothesis Properties & Artifacts
# ==========================================

MODEL_STATS = {
    "all_sequence_examples": 0,
    "redispatch_examples": 0,
    "redispatch_examples_with_two_or_more_dispatches": 0,
    "max_dispatches_observed": 0,
    "safety_failures": 0,
}


def dump_artifact():
    artifact_path = os.environ.get("DIN5_MODEL_ARTIFACT")
    if not artifact_path:
        return
    mode = "no_dedup" if os.environ.get("DIN5_MUTANT") == "no_dedup" else "dedup_on"
    data = {
        "mode": mode,
        "all_sequence_examples": MODEL_STATS["all_sequence_examples"],
        "redispatch_examples": MODEL_STATS["redispatch_examples"],
        "redispatch_examples_with_two_or_more_dispatches": MODEL_STATS[
            "redispatch_examples_with_two_or_more_dispatches"
        ],
        "max_dispatches_observed": MODEL_STATS["max_dispatches_observed"],
        "safety_failures": MODEL_STATS["safety_failures"],
    }
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    with open(artifact_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


atexit.register(dump_artifact)

ACTION_STRATEGY = st.lists(
    st.sampled_from(
        [
            "claim",
            "effect_write",
            "crash",
            "reclaim",
            "mark_succeeded",
            "mark_failed",
            "mark_dead_letter",
        ]
    ),
    max_size=30,
)


@settings(max_examples=200, deadline=None)
@given(actions=ACTION_STRATEGY)
def test_all_action_sequences_preserve_effect_safety(actions):
    MODEL_STATS["all_sequence_examples"] += 1
    model = RelayModel()
    worker_counter = 1
    for act in actions:
        w_id = f"worker-{worker_counter}"
        if act == "claim":
            worker_counter += 1
        model.apply_action(act, worker_id=w_id)

    if model.dispatches > MODEL_STATS["max_dispatches_observed"]:
        MODEL_STATS["max_dispatches_observed"] = model.dispatches

    effect_count = len(model.durable_effects)
    if effect_count > 1:
        MODEL_STATS["safety_failures"] += 1
    assert effect_count <= 1, (
        f"Falsifying example: shrunk_trace={model.history}; dispatches={model.dispatches}; "
        f"effect_writes={model.effect_attempts}; effect_count={effect_count}"
    )


@settings(max_examples=100, deadline=None)
@given(actions=ACTION_STRATEGY)
def test_redispatch_sequences_preserve_effect_safety(actions):
    MODEL_STATS["redispatch_examples"] += 1
    # Construction-guaranteed redispatch skeleton
    skeleton = ["claim", "effect_write", "crash", "reclaim", "claim"]
    full_actions = skeleton + actions

    model = RelayModel()
    worker_counter = 1
    for act in full_actions:
        w_id = f"worker-{worker_counter}"
        if act == "claim":
            worker_counter += 1
        model.apply_action(act, worker_id=w_id)

    if model.dispatches >= 2:
        MODEL_STATS["redispatch_examples_with_two_or_more_dispatches"] += 1

    if model.dispatches > MODEL_STATS["max_dispatches_observed"]:
        MODEL_STATS["max_dispatches_observed"] = model.dispatches

    effect_count = len(model.durable_effects)
    if effect_count > 1:
        MODEL_STATS["safety_failures"] += 1

    assert effect_count <= 1, (
        f"Falsifying example: shrunk_trace={model.history}; dispatches={model.dispatches}; "
        f"effect_writes={model.effect_attempts}; effect_count={effect_count}"
    )


def test_generation_blind_stale_mark_trace():
    model = RelayModel()
    assert model.claim("worker-A")
    assert model.effect_write()
    assert model.reclaim()
    assert model.claim("worker-B")
    stale_mark_rowcount = 1 if model.status == "running" else 0
    if stale_mark_rowcount == 1:
        model.status = "succeeded"
        model.history.append("stale_mark(worker-A)")

    assert model.effect_write(allow_stale=True)
    current_owner_mark_rowcount = 1 if model.status == "running" else 0
    if current_owner_mark_rowcount == 1:
        model.status = "succeeded"
    model.history.append("mark(worker-B)")

    assert len(model.durable_effects) == 1
    assert model.dispatches == 2
    assert stale_mark_rowcount == 1
    assert current_owner_mark_rowcount == 0

