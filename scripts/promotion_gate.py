import argparse
from pathlib import Path
import json

def generate_promotion_report(champion_metrics: dict, challenger_metrics: dict, output_path: str):
    champ_f1 = champion_metrics.get("f1", 0.0)
    chall_f1 = challenger_metrics.get("f1", 0.0)
    
    champ_recall = champion_metrics.get("recall", 0.0)
    chall_recall = challenger_metrics.get("recall", 0.0)
    
    # Promotion Logic: Challenger must improve F1 by at least 1% without dropping recall below 95%
    promotion_passed = False
    reasons = []
    
    if chall_recall < 0.95:
        reasons.append("Failed: Challenger recall is below the strict 95% threshold.")
    elif chall_f1 <= champ_f1 + 0.01:
        reasons.append(f"Failed: Challenger F1 ({chall_f1:.3f}) did not improve over Champion ({champ_f1:.3f}) by at least 1%.")
    else:
        promotion_passed = True
        reasons.append("Passed: Challenger met all strict safety and performance bounds.")
        
    status_text = "PROMOTED" if promotion_passed else "REJECTED"
    color = "green" if promotion_passed else "red"
    
    html = f"""<html>
<head><style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ border-collapse: collapse; width: 50%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    .status {{ font-weight: bold; color: {color}; }}
</style></head>
<body>
    <h1>Model Promotion Gate</h1>
    <h2 class="status">Status: {status_text}</h2>
    <ul>
        {"".join(f"<li>{r}</li>" for r in reasons)}
    </ul>
    
    <h3>Metrics Comparison</h3>
    <table>
        <tr><th>Metric</th><th>Champion</th><th>Challenger</th><th>Delta</th></tr>
        <tr><td>F1 Score</td><td>{champ_f1:.3f}</td><td>{chall_f1:.3f}</td><td>{chall_f1 - champ_f1:.3f}</td></tr>
        <tr><td>Recall</td><td>{champ_recall:.3f}</td><td>{chall_recall:.3f}</td><td>{chall_recall - champ_recall:.3f}</td></tr>
    </table>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
        
    print(f"Generated {output_path} (Status: {status_text})")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--champion-metrics", required=True, help="JSON file with champion metrics")
    parser.add_argument("--challenger-metrics", required=True, help="JSON file with challenger metrics")
    parser.add_argument("--output", default="reports/model_promotion_report.html")
    args = parser.parse_args()
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    with open(args.champion_metrics, "r") as f:
        champ = json.load(f)
    with open(args.challenger_metrics, "r") as f:
        chall = json.load(f)
        
    generate_promotion_report(champ, chall, args.output)
