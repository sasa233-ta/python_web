import sys
from app.utils.stock_analyzer import get_model_accuracy

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python accuracy_check.py <symbol>")
        sys.exit(1)
    symbol = sys.argv[1]
    # 4桁数字なら.Tを自動付与
    if symbol.isdigit() and len(symbol) == 4:
        symbol = symbol + ".T"
    try:
        acc = get_model_accuracy(symbol)
        print(f"{symbol} モデル正解率: {acc*100:.1f}%")
    except Exception as e:
        print(f"get_model_accuracy error: {e}")
