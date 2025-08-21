from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
def test_hitl_queue_contains_controls():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=7, n_entities=3)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    ids = [h.id for h in s["hitl_queue"]]
    assert any(x.startswith("H-REC-") for x in ids) or any(x.startswith("H-JE-") for x in ids)
