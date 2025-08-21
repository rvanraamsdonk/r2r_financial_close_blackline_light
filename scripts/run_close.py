import os, sys, click
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from r2r.data.repo import DataRepo
from r2r.policies import POLICY
from r2r.graph import build_graph
from r2r.agents.reporting import generate_executive_dashboard, generate_forensic_report, generate_matching_analysis
from r2r import console

@click.command()
@click.option("--period", default="2025-08", help="Period to close (YYYY-MM)", show_default=True)
@click.option("--prior", default="2025-07", help="Prior period for comparison", show_default=True)
@click.option("--entities", default=3, type=int, help="Number of entities (3=static dataset)", show_default=True)
@click.option("--seed", default=42, type=int, help="Random seed", show_default=True)
@click.option("--rich", is_flag=True, help="Enable rich visual displays", show_default=True)
def main(period, prior, entities, seed, rich):
    repo = DataRepo(period=period, prior_period=prior, n_entities=entities, seed=seed)
    app, console_obj, init = build_graph(data_repo=repo, policy=POLICY)
    console_obj.banner(f"R2R CLOSE RUN PERIOD {period}")
    state = app.invoke({**init})
    console_obj.banner("Run Complete")
    
    # Basic summary
    print(f"Summary: recs={len(state.get('recs',[]))} matches={len(state.get('matches',[]))} journals={len(state.get('journals',[]))} flux_alerts={len(state.get('flux',[]))} ic_docs={len(state.get('ic',[]))} hitl_cases={len(state.get('hitl_queue',[]))}")
    
    # Rich visual displays if requested
    if rich:
        print("\n" + "="*80)
        print("RICH VISUAL SUMMARY")
        print("="*80)
        
        # Extract data from state
        recs = state.get("recs", [])
        matches = state.get("matches", [])
        forensic_findings = []  # Extract from events or other state
        data = state.get("data", {})
        
        # Generate and display executive dashboard
        dashboard = generate_executive_dashboard(recs, matches, forensic_findings, console_obj)
        console_obj.executive_dashboard_display(dashboard)
        
        # Generate and display forensic report  
        forensic_report = generate_forensic_report(forensic_findings, [], console_obj)
        console_obj.forensic_findings_display(forensic_report.get('findings', []))
        
        # Generate and display matching analysis
        matching_analysis = generate_matching_analysis(matches, console_obj)
        console_obj.matching_analysis_display(matching_analysis)

if __name__ == "__main__":
    main()
