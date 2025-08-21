from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
def test_flux_alerts_exist():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=5, n_entities=2)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    assert isinstance(s.get("flux", []), list)
