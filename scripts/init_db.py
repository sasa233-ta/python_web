from app.core.db import engine
from app.models.user_model import Base
from app.models.trade_model import TradeHistory
from app.models.stock_model import Stock  # 追加

Base.metadata.create_all(engine)
print('DB初期化完了')