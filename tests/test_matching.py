from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
def test_matching_rules():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=3, n_entities=3)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    m = s["matches"]
    assert len(m) == 2
    assert m[0].cleared + m[0].residual > 0
    assert m[1].cleared + m[1].residual >= 0
