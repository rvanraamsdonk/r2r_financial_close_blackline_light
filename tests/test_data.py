from r2r.data.repo import DataRepo
def test_repo_shapes():
    d = DataRepo(period="2025-08", prior_period="2025-07", seed=1, n_entities=4).snapshot()
    assert len(d["entities"])==4
    assert {"gl","ar","ap","bank","ic","budget","fx"}.issubset(d.keys())
