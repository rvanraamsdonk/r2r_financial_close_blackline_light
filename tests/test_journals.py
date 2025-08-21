from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
def test_maker_checker_and_posting():
    repo = DataRepo(period="2025-08", prior_period="2025-07", seed=4, n_entities=2)
    app, _, init = build_graph(data_repo=repo, policy=POLICY)
    s = app.invoke({**init})
    assert any(h.type=="journal_post" and h.status=="approved" for h in s["hitl_queue"])
    # Ensure at least one journal posted
    assert any(j.status=="posted" for j in s["journals"])
