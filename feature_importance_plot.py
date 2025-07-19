import matplotlib.pyplot as plt
import sys
import logging
from app.utils.rss_excel_loader import get_model_accuracy_excel

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def plot_feature_importance(importances, model_name, topn=20):
    if not isinstance(importances, dict):
        print(f"{model_name} 重要度: {importances}")
        return
    items = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)[:topn]
    labels, values = zip(*items)
    plt.figure(figsize=(8, max(4, len(labels)*0.4)))
    plt.barh(labels[::-1], values[::-1])
    plt.title(f"{model_name} Feature Importance (Top {topn})")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "9531"
    acc_pt, acc_lgb, acc_lstm, acc_stack, importances = get_model_accuracy_excel(ticker)
    print(f"PyTorch正解率: {acc_pt*100:.1f}%")
    print(f"LightGBM正解率: {acc_lgb*100:.1f}%")
    print(f"LSTM正解率: {acc_lstm*100:.1f}%")
    print(f"Stacking正解率: {acc_stack*100:.1f}%")
    for model in ["LightGBM", "PyTorch", "LSTM"]:
        plot_feature_importance(importances.get(model, {}), model)
