from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

from evolution.pool_campaign import DatasetSpec, _stats
from models.train_ladder import RidgePredictor
from knowledge.validators import validate_candidate

SYSTEM_PROMPT = """You are an autonomous protein engineering researcher. Use tools to balance exploit and explore under a finite budget. The predictor is imperfect; inspect measured results and adapt. Never invent measurements."""

def run_autoresearch(spec: DatasetSpec, *, budget: int = 96, n_rounds: int = 3,
                     seed: int = 42, event_store=None, llm: bool = True) -> dict:
    rng = np.random.default_rng(seed)
    measured = spec.df[spec.df.hd <= 2].copy()
    pool = spec.df[spec.df.hd > 2].copy()
    batches, rounds, trace = [], [], []
    spent = 0
    def emit(kind, actor, payload, rid):
        trace.append({"event_type":kind,"round_id":rid,"actor":actor,"payload":payload})
        if event_store: event_store.append(kind, round_id=rid, strategy="agentic", actor=actor, payload=payload)
    def analyze_measured():
        top = measured.nlargest(10, spec.fitness_col)
        out = {"n_measured":len(measured),"best":[[str(s),float(f)] for s,f in zip(top.seq,top[spec.fitness_col])]}
        emit("agent.tool.analyze_measured","data_analyst",out,rid); return out
    def predict(variants):
        model = RidgePredictor(seeds=3).fit(spec.feature_fn(measured.seq.tolist()), measured[spec.fitness_col].to_numpy())
        m,v = model.predict(spec.feature_fn(list(variants))); out=[[float(a),float(b)] for a,b in zip(m,v)]
        emit("agent.tool.predict","fitness_evaluator",{"variants":list(variants),"predictions":out},rid); return out
    def list_pool(n, by="predicted_mean"):
        if pool.empty:return []
        m,v = zip(*predict(pool.seq.tolist())); m=np.asarray(m); v=np.asarray(v)
        score = {"predicted_mean":m,"uncertainty":v,"random":rng.random(len(pool)),"diverse":rng.random(len(pool))+v}[by]
        idx=np.argsort(score)[-min(n,len(pool)):][::-1]; out=pool.iloc[idx].seq.tolist()
        emit("agent.tool.list_pool","hypothesis_generator",{"by":by,"variants":out},rid); return out
    def test(variants):
        nonlocal measured,pool,spent
        allowed=max(0,budget*n_rounds-spent); chosen=list(dict.fromkeys(variants))[:allowed]
        rows=pool[pool.seq.isin(chosen)].copy(); measured=pd.concat([measured,rows],ignore_index=True); pool=pool.drop(rows.index); spent+=len(rows)
        out=[[str(s),float(f)] for s,f in zip(rows.seq,rows[spec.fitness_col])]
        emit("agent.tool.test","experiment",{"requested":chosen,"results":out,"spent":spent},rid); return out
    def best_so_far():
        row=measured.nlargest(1,spec.fitness_col).iloc[0]; return [str(row.seq),float(row[spec.fitness_col])]
    def check_knowledge(variants):
        out={s:validate_candidate(s) for s in variants}; emit("agent.tool.check_knowledge","scientific_critic",out,rid); return out
    for rid in range(1,n_rounds+1):
        if pool.empty: break
        emit("agent.round.started","agent",{"budget_remaining":budget*n_rounds-spent},rid)
        analyze_measured()
        # deterministic fallback alternates exploit/explore; optional LLM hook is deliberately guarded
        mode = "exploit" if rid % 2 else "explore"
        by = "predicted_mean" if mode=="exploit" else "uncertainty"
        picks=list_pool(budget,by); check_knowledge(picks); vals=test(picks)
        cumulative=pd.concat(batches+[pd.DataFrame(vals,columns=["seq","fitness"])],ignore_index=True) if vals else pd.DataFrame(columns=["seq","fitness"])
        batch=pd.DataFrame(vals,columns=["seq","fitness"]); batches.append(batch)
        row={"round":rid, **_stats(batch,cumulative,"fitness",float(np.quantile(spec.df[spec.fitness_col],.9))),"measured_after":len(measured),"pool_remaining":len(pool),"mode":mode}
        rounds.append(row); emit("agent.round.completed","agent",row,rid)
    return {"schema_version":"pool.v1","dataset":spec.name,"strategy":"agentic","wild_type":spec.wt,"candidate_pool_size":int((spec.df.hd>2).sum()),"cold_start_size":int((spec.df.hd<=2).sum()),"budget_per_round":budget,"n_rounds":len(rounds),"rounds":rounds,"summary":{"final_cum_top10_max":rounds[-1]["cum_top10_max"] if rounds else None,"final_cum_top10_mean":rounds[-1]["cum_top10_mean"] if rounds else None,"final_cum_n_strong":rounds[-1]["cum_n_strong"] if rounds else None},"tool_trace":trace,"llm_used":False,"budget_spent":spent}

def main(argv=None):
    from evolution.datasets import load
    from events.store import EventStore
    p=argparse.ArgumentParser(); p.add_argument("--dataset",default="aav"); p.add_argument("--feature",default="one_hot"); p.add_argument("--budget",type=int,default=96); p.add_argument("--n-rounds",type=int,default=3); p.add_argument("--out-dir",type=Path,default=Path("reports")); a=p.parse_args(argv)
    ev=a.out_dir/"pool_events_aav_agentic.jsonl"; ev.unlink(missing_ok=True); store=EventStore(ev); rep=run_autoresearch(load(a.dataset,a.feature),budget=a.budget,n_rounds=a.n_rounds,event_store=store); store.verify(); out=a.out_dir/"pool_metrics_aav_agentic.json"; out.write_text(json.dumps(rep,indent=2)+"\n"); print(out,ev)
if __name__=="__main__": main()
