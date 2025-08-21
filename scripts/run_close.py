import os, sys, click
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph

@click.command()
@click.option("--period", default="2025-08", show_default=True)
@click.option("--prior", default="2025-07", show_default=True)
@click.option("--entities", default=6, show_default=True, type=int)
@click.option("--seed", default=42, show_default=True, type=int)
def main(period, prior, entities, seed):
    repo = DataRepo(period=period, prior_period=prior, n_entities=entities, seed=seed)
    app, console, init = build_graph(data_repo=repo, policy=POLICY)
    console.banner(f"R2R CLOSE RUN PERIOD {period}")
    state = app.invoke({**init})
    console.banner("Run Complete")
    print(f"Summary: recs={len(state.get('recs',[]))} matches={len(state.get('matches',[]))} journals={len(state.get('journals',[]))} flux_alerts={len(state.get('flux',[]))} ic_docs={len(state.get('ic',[]))} hitl_cases={len(state.get('hitl_queue',[]))}")

if __name__ == "__main__":
    main()
