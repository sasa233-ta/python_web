import numpy as np

def analyze_stock(prices):
    """
    取得済み株価データの末尾（＝12週遅れの最新）を基準に3日後上昇確率を予測
    prices: 昇順（日付古→新）
    """
    if not prices or len(prices) < 20:
        return {"mean": None, "std": None, "prediction": None, "prob_up_3days": None}   # データ不足
    
    window = 120  # 直近3ヶ月分で回帰
    base_idx = len(prices) - 1  # データ末尾
    start_idx = max(0, base_idx - window + 1)
    x = np.arange(start_idx, base_idx + 1)
    y = np.array(prices[start_idx:base_idx + 1])
    if len(y) < 10:
        return {"mean": None, "std": None, "prediction": None, "prob_up_3days": None}
    # 線形回帰
    coef = np.polyfit(x, y, 1)
    pred_3days = np.polyval(coef, base_idx + 3)
    base_price = prices[base_idx]
    std = np.std(y)
    mean = np.mean(y)
    prob_up_3days = 1 - float(np.round(np.clip(np.random.normal(0.6, 0.1), 0, 1), 2)) if std == 0 else float(1 - np.exp(-(pred_3days - base_price) / (std + 1e-6)))
    prob_up_3days = float(np.clip(prob_up_3days, 0, 1))
    return {
        "mean": float(mean),
        "std": float(std),
        "prediction": float(pred_3days),
        "prob_up_3days": prob_up_3days
    }
