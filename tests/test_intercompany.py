from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
def test_ic_netting_ready():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=6, n_entities=3)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    assert any(ic.status in ("net_ready","open","balanced") for ic in s["ic"])
