from sqlalchemy import create_engine
import os

engine = None
db_dir = "data/vampyre.db"
def load_db():
    global engine
    engine = create_engine('sqlite:///' + os.path.abspath(db_dir))