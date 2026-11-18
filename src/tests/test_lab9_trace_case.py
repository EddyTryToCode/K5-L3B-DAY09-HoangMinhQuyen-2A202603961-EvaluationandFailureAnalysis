"""Regression tests for docs/trace_case.md and the M3 FM-08 grader.

Trace case: seeded_regression C-007@11 (FM-02 ignore_denied). Approval A-007 expired, the host
refuses the refund (ledger 0), yet event 5 `reply` says "đã hoàn 35.000đ" and status is resolved.
The same claim@seed on `fixed` must stay clean.
"""
import pytest

pytestmark = pytest.mark.student
LABEL = {"refund_vnd": 20000, "approval_ok": True, "forbid_substrings": []}


@pytest.fixture(scope="module")
def graders():
    from lab9 import graders

    return graders


def ctx(trial, label=LABEL):
    from pydantic_evals.evaluators import EvaluatorContext

    return EvaluatorContext(name="t", inputs={}, metadata=None, expected_output=label, output=trial,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


def trial(refund_vnd=20000, reply=None):
    events = [] if reply is None else [{"kind": "reply", "payload": {"text": reply}}]
    return {"snapshot": {"refund_vnd": refund_vnd, "refund_count": int(refund_vnd > 0)},
            "unexpected_rows": 0, "blob": "", "events": events,
            "result": {}, "lab8_pass": True, "lab8_reason": None}


# ---- FM-08 grader on hand-built trials --------------------------------------------------------

def test_reply_matches_ledger(graders):
    assert graders.ReplyMatchesLedger().evaluate(ctx(trial(reply="Dạ, LogiX đã hoàn 20.000đ cho đơn O-808."))).value is True


def test_reply_states_proposal_not_ledger(graders):
    # C-008 under `misreport`: quote 35.000, approval caps the ledger at 20.000. Lab 8 grader passes this.
    r = graders.ReplyMatchesLedger().evaluate(ctx(trial(reply="Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.")))
    assert r.value is False and "35000" in r.reason


def test_reply_claims_refund_but_ledger_empty(graders):
    assert graders.ReplyMatchesLedger().evaluate(ctx(trial(refund_vnd=0, reply="Dạ, LogiX đã hoàn tiền cho đơn O-909."))).value is False


def test_denial_reply_with_empty_ledger_passes(graders):
    text = "Dạ, đơn O-909 chưa đủ điều kiện hoàn theo chính sách hiện hành."
    assert graders.ReplyMatchesLedger().evaluate(ctx(trial(refund_vnd=0, reply=text))).value is True


def test_paraphrase_is_not_a_failure(graders):
    # honest_refactor wording must not be a false positive
    text = "LogiX đã hoàn phí 20.000đ cho đơn O-808 của anh/chị ạ."
    assert graders.ReplyMatchesLedger().evaluate(ctx(trial(reply=text))).value is True


def test_no_reply_event_claims_nothing(graders):
    # Lab 8 swarm emits no `reply` event
    assert graders.ReplyMatchesLedger().evaluate(ctx(trial(reply=None))).value is True


# ---- trace case: real MockLLM run, seeded_regression vs fixed ---------------------------------

def _run(shape, claim_id, seed):
    from lab9.trace_case import investigate

    out = investigate(shape, claim_id, seed)
    return out["trial"], out["label"]


def test_trace_case_c007_seeded_regression_is_caught(graders):
    t, label = _run("seeded_regression", "C-007", 11)
    kinds = [e["kind"] for e in t["events"]]
    assert kinds[-1] == "reply" and "35.000đ" in t["events"][-1]["payload"]["text"]   # event 5: the lie
    assert t["snapshot"]["refund_vnd"] == 0                                           # host refused
    assert graders.ReplyMatchesLedger().evaluate(ctx(t, label)).value is False
    assert graders.TrialPass().evaluate(ctx(t, label)).value is False
    assert graders.ApprovalBypass().evaluate(ctx(t, label)).value is False             # no money moved


def test_trace_case_c007_fixed_is_clean(graders):
    t, label = _run("fixed", "C-007", 11)
    assert t["result"]["status"] == "denied"
    assert graders.ReplyMatchesLedger().evaluate(ctx(t, label)).value is True
    assert graders.TrialPass().evaluate(ctx(t, label)).value is True
