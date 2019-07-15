from sqlalchemy import Table, Column, Float, String, MetaData

engine = db.create_engine('sqlite:///stocks_formatted.db')
meta = db.MetaData()
#use adjusted close
close = db.Table(
   'close', meta, 
   db.Column('date', db.String, primary_key = True), 
   db.Column('ticker', db.Float), 
)

volume = db.Table(
   'volume', meta, 
   db.Column('date', db.String, primary_key = True), 
   db.Column('ticker', db.Float), 
)

dividend = Table(
   'dividend', meta, 
   db.Column('dividend', db.String, primary_key = True), 
   db.Column('ticker', db.Float), 
)

meta.create_all(engine)