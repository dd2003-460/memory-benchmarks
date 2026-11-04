#!/usr/bin/env python3
"""Compare conv4 rerun #2 (entity guard) vs baseline, per-category and per-question."""
import json, glob, os

BASE = "results/locomo/locomo_results_20261104_195846.json"
PRED_DIR = "results/locomo/predicted_locomo-vllm"

def load_baseline():
    with open(BASE) as f:
        data = json.load(f)
    evs = {}
    for ev in data["evaluations"]:
        if ev.get("conversation_idx") == 4:
            qid = ev["question_id"]
            c = ev.get("cutoff_results", {}).get("top_10", {})
            evs[qid] = {
                "judgment": c.get("judgment", "?"),
                "score": c.get("score", 0.0),
                "category": ev.get("category_name", "?"),
                "question": ev.get("question", ""),
                "ground_truth": ev.get("ground_truth_answer", ""),
            }
    return evs

def load_rerun():
    """Load only full01-eg (rerun #2) files."""
    evs = {}
    for f in sorted(glob.glob(os.path.join(PRED_DIR, "conv4_q*.json"))):
        with open(f) as fh:
            d = json.load(fh)
        if "full01-eg" not in d.get("user_id", ""):
            continue
        qid = d["question_id"]
        c = d.get("cutoff_results", {}).get("top_10", {})
        evs[qid] = {
            "judgment": c.get("judgment", "?"),
            "score": c.get("score", 0.0),
            "generated_answer": c.get("generated_answer", ""),
        }
    return evs

def main():
    base = load_baseline()
    rerun = load_rerun()
    
    print(f"Baseline conv4 questions: {len(base)}")
    print(f"Rerun #2 completed: {len(rerun)}")
    
    if len(rerun) < 178:
        print(f"\n⚠️  Rerun incomplete ({len(rerun)}/178). Partial comparison only.")
    
    # Per-category stats
    cats = ["single-hop", "multi-hop", "temporal", "open-domain"]
    print(f"\n{'Category':<15} {'Baseline':>10} {'Rerun#2':>10} {'Delta':>8}")
    print("-" * 48)
    for cat in cats:
        b_total = sum(1 for e in base.values() if e["category"] == cat)
        b_correct = sum(1 for e in base.values() if e["category"] == cat and e["judgment"] == "CORRECT")
        r_in_cat = [e for q, e in rerun.items() if base[q]["category"] == cat]
        r_total = len(r_in_cat)
        r_correct = sum(1 for e in r_in_cat if e["judgment"] == "CORRECT")
        
        b_pct = f"{b_correct}/{b_total} ({b_correct/b_total*100:.1f}%)" if b_total else "N/A"
        r_pct = f"{r_correct}/{r_total} ({r_correct/r_total*100:.1f}%)" if r_total else "N/A"
        
        if b_total and r_total:
            delta = (r_correct/r_total - b_correct/b_total) * 100
            delta_s = f"{delta:+.1f}pp"
        else:
            delta_s = "N/A"
        
        print(f"{cat:<15} {b_pct:>10} {r_pct:>10} {delta_s:>8}")
    
    # Overall
    b_total = len(base)
    b_correct = sum(1 for e in base.values() if e["judgment"] == "CORRECT")
    r_total = len(rerun)
    r_correct = sum(1 for e in rerun.values() if e["judgment"] == "CORRECT")
    print("-" * 48)
    print(f"{'OVERALL':<15} {b_correct}/{b_total} ({b_correct/b_total*100:.1f}%)  {r_correct}/{r_total} ({r_correct/r_total*100:.1f}%)  {(r_correct/r_total-b_correct/b_total)*100:+.1f}pp")
    
    # Flipped questions
    flipped_fix = []
    flipped_break = []
    for qid, r in rerun.items():
        if qid not in base:
            continue
        b_j = base[qid]["judgment"]
        r_j = r["judgment"]
        if b_j == "WRONG" and r_j == "CORRECT":
            flipped_fix.append((qid, base[qid]["category"], base[qid]["question"][:60], r.get("generated_answer","")[:80]))
        elif b_j == "CORRECT" and r_j == "WRONG":
            flipped_break.append((qid, base[qid]["category"], base[qid]["question"][:60]))
    
    if flipped_fix:
        print(f"\n✅ FIXED ({len(flipped_fix)}):")
        for qid, cat, q, ans in flipped_fix:
            print(f"  {qid} [{cat}] {q}")
            print(f"     → {ans}")
    
    if flipped_break:
        print(f"\n❌ BROKEN ({len(flipped_break)}):")
        for qid, cat, q in flipped_break:
            print(f"  {qid} [{cat}] {q}")
    
    # OD detail
    od_base = {q: e for q, e in base.items() if e["category"] == "open-domain"}
    od_rerun = {q: e for q, e in rerun.items() if q in od_base}
    if od_rerun:
        print(f"\n📋 OD detail ({len(od_rerun)}/14 answered):")
        for qid in sorted(od_rerun, key=lambda x: int(x.split('q')[1])):
            b = od_base[qid]["judgment"]
            r = od_rerun[qid]["judgment"]
            mark = "✅" if (b=="WRONG" and r=="CORRECT") else ("❌" if (b=="CORRECT" and r=="WRONG") else "  ")
            print(f"  {mark} {qid}: {b}→{r} | {od_base[qid]['ground_truth'][:40]}")

if __name__ == "__main__":
    main()