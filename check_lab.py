import json
import os

def validate_lab():
    print("Dang kiem tra dinh dang bai nop...")

    required_files = [
        "reports/summary.json",
        "reports/benchmark_results.json",
        "analysis/failure_analysis.md"
    ]

    # 1. Kiểm tra sự tồn tại của tất cả file
    missing = []
    for f in required_files:
        if os.path.exists(f):
            print(f"Tim thay: {f}")
        else:
            print(f"Thieu file: {f}")
            missing.append(f)

    if missing:
        print(f"\nThieu {len(missing)} file. Hay bo sung truoc khi nop bai.")
        return

    # 2. Kiểm tra nội dung summary.json
    try:
        with open("reports/summary.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"File reports/summary.json khong phai JSON hop le: {e}")
        return

    if "metrics" not in data or "metadata" not in data:
        print("File summary.json thieu truong 'metrics' hoac 'metadata'.")
        return

    metrics = data["metrics"]

    print(f"\n--- Thống kê nhanh ---")
    print(f"Tổng số cases: {data['metadata'].get('total', 'N/A')}")
    print(f"Điểm trung bình: {metrics.get('avg_score', 0):.2f}")

    # EXPERT CHECKS
    has_retrieval = "hit_rate" in metrics
    if has_retrieval:
        print(f"Da tim thay Retrieval Metrics (Hit Rate: {metrics['hit_rate']*100:.1f}%)")
    else:
        print(f"CANH BAO: Thieu Retrieval Metrics (hit_rate).")

    has_multi_judge = "agreement_rate" in metrics
    if has_multi_judge:
        print(f"Da tim thay Multi-Judge Metrics (Agreement Rate: {metrics['agreement_rate']*100:.1f}%)")
    else:
        print(f"CANH BAO: Thieu Multi-Judge Metrics (agreement_rate).")

    if data["metadata"].get("version"):
        print(f"Da tim thay thong tin phien ban Agent (Regression Mode)")

    print("\nBai lab da san sang de cham diem!")

if __name__ == "__main__":
    validate_lab()
