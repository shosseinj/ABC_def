from pathlib import Path
import hashlib,inspect,json
import numpy as np,torch
from experiments.iris.phase21 import *
ROOT=Path(__file__).resolve().parents[1]

def test_frozen_constants_and_cosine_loss():
    assert SPLIT_SEEDS==(271,811,1618,2718,4242) and MODEL_SEEDS==(42,777,2026)
    assert LAMBDAS==(.1,.5,1.,2.) and EPSILONS==(.01,.02,.05,.1)
    assert torch.isclose(representation_loss(torch.tensor([[1.,0]]),torch.tensor([[1.,0]])),torch.tensor(0.))

def test_protocol_hash_and_boundaries():
    p=json.loads((ROOT/"results/iris_phase21_protocol.json").read_text());h=p.pop("protocol_sha256")
    assert h==hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    assert p["prior_phase21_output_inspection"] is False and p["data"]["sizes"]=={"train":90,"validation":30,"hidden":30}
    src=(ROOT/"scripts/run_phase21_representation_consistency.py").read_text()
    assert "load_iris_splits" not in src and "evaluate_test=False" in src
    assert "classical_timing_attack(model,clean_t,int(y),eps*T,T,20,eps*T/5,False" in src

def test_safe_denominators_pairing_and_gate():
    assert safe_mean([])[1]=="undefined_empty"
    a=[{"sample_id":1,"clean_correct":True,"attack_success":True},{"sample_id":2,"clean_correct":True,"attack_success":False}]
    b=[{"sample_id":1,"clean_correct":True,"attack_success":False},{"sample_id":2,"clean_correct":False,"attack_success":False}]
    q=common_clean_pair(a,b);assert q["N_common_clean_correct"]==1 and q["rescued"]==1
    assert "excluded_id" in inspect.signature(grouped_contrast).parameters

def test_gradient_partition_head_is_structurally_none():
    class M(torch.nn.Module):
        def __init__(self):super().__init__();self.qlayer=torch.nn.Linear(2,2);self.head=torch.nn.Linear(2,2)
    m=M();x=torch.ones(2,2);q=m.qlayer(x);loss=representation_loss(q,q+.1)
    g=grad_norms(loss,m);assert g["qlayer_status"]=="defined" and g["head_status"]=="none_structural"

def test_registration_and_generated_contract_if_present():
    from phase_runner import PHASE_TESTS
    assert PHASE_TESTS[21].endswith("test_phase21_representation_consistency.py")
    gate=ROOT/"results/iris_phase21_gate.json"
    if not gate.exists():return
    g=json.loads(gate.read_text());assert not g["test_set_accessed"] and not g["hidden_features_received"] and g["full_loader_calls"]==0
    manifests=json.loads((ROOT/"results/iris_phase21_split_manifest.json").read_text())["splits"]
    assert all(x["sizes"]==[90,30,30] and x["pairwise_intersections"]==[0,0,0] for x in manifests)

def test_exact_failed_stage_a_public_contract():
    import csv
    required=["iris_phase21_repr_diagnosis.csv","iris_phase21_repr_diagnosis.json","iris_phase21_robust_vs_fail.csv","iris_phase21_centroid_crossing.csv","iris_phase21_local_purity.csv","iris_phase21_stageA_gate.json","iris_phase21_scientific_audit.md","iris_phase21_beginner_summary.md","phase21_results.md"]
    assert all((ROOT/"results"/x).is_file() for x in required)
    rows=json.loads((ROOT/"results/iris_phase21_repr_diagnosis.json").read_text())
    assert len(rows)==3600 and len({(r["split_seed"],r["model_seed"],r["sample_id"],r["attack"],r["epsilon_fraction"]) for r in rows})==3600
    fields=set(rows[0]);assert {"clean_raw_features","attacked_raw_features","clean_normalized_features","attacked_normalized_features","clean_ttfs","attacked_ttfs","clean_quantum_features","attacked_quantum_features","clean_logits","attacked_logits","quantum_l2","margin_drop","centroid_crossing","sample_id"}<=fields
    assert sum(1 for _ in csv.DictReader((ROOT/"results/iris_phase21_centroid_crossing.csv").open()))==3600
    assert sum(1 for _ in csv.DictReader((ROOT/"results/iris_phase21_local_purity.csv").open()))==3600
    gate=json.loads((ROOT/"results/iris_phase21_stageA_gate.json").read_text());assert gate["pass"] is False
    assert not any((ROOT/"results").glob("iris_phase21_stage_b_*")) and not (ROOT/"results/iris_phase21_selected_config.json").exists()

def test_exact_report_headings_questions_and_exhaustive_manifest():
    titles=["Agents and Skills Used","Interpreter","Files Added","Files Modified","Regression Status","Phase 21 Protocol","Development Splits","Model Seeds","Stage A Representation Metrics","Robust vs Failed Samples","Class-Wise Representation Shift","Centroid Crossing","Local Purity Stability","Multi-Split Reproducibility","Stage A Gate"]
    report=(ROOT/"results/phase21_results.md").read_text();assert [x for x in report.splitlines() if x.startswith("## ")]==[f"## {i}. {x}" for i,x in enumerate(titles,1)]
    assert all(f"Q{i}:" in report for i in range(1,15))
    assert not any(x.startswith("## 16.") for x in report.splitlines())
    manifest=json.loads((ROOT/"results/iris_phase21_artifact_manifest.json").read_text());declared={x["path"] for x in manifest["generator_owned_outputs"]}|{x["path"] for x in manifest["agent_owned"]}|{"iris_phase21_artifact_manifest.json"}
    actual={p.name for p in (ROOT/"results").glob("iris_phase21_*")}|{p.name for p in (ROOT/"results/plots").glob("phase21_*")}|{"phase21_results.md"}
    assert actual==declared
    for x in manifest["generator_owned_outputs"]:
        p=(ROOT/x["location"]/x["path"]);assert hashlib.sha256(p.read_bytes()).hexdigest()==x["sha256"]
