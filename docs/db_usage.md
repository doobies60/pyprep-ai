DB取得の基本コード:

全件取得: Model.query.all()

条件絞り込み: Model.query.filter_by(column=value).first()

ランダム1件: Model.query.order_by(db.func.random()).first()