from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph

def test_decert_on_gl_change():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=10, n_entities=3)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    assert any(r.status == "decertified" for r in s["recs"])
