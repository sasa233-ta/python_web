import sys
import logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
from app.utils.rss_excel_loader import get_model_accuracy_excel
import traceback

if __name__ == "__main__":
    # symbol引数は不要（Excelファイルのデータをそのまま使うため）
    try:
        # 9531
        # 1736
        # 6309
        # 6758
        acc_pt, acc_lgb, acc_lstm, acc_ensemble3 = get_model_accuracy_excel("9531")
        print(f"PyTorch正解率: {acc_pt*100:.1f}%", flush=True)
        print(f"LightGBM正解率: {acc_lgb*100:.1f}%", flush=True)
        print(f"LSTM正解率: {acc_lstm*100:.1f}%" if acc_lstm is not None else "LSTM正解率: N/A", flush=True)
        print(f"3モデルアンサンブル正解率: {acc_ensemble3*100:.1f}%" if acc_ensemble3 is not None else "3モデルアンサンブル正解率: N/A", flush=True)
    except Exception as e:
        print(f"get_model_accuracy_excel error: {e}", flush=True)
        traceback.print_exc()
