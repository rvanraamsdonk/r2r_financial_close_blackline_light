from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
def test_matching_summary():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=3, n_entities=3)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    mr = s["matches"][0]
    assert mr.cleared + mr.residual > 0
