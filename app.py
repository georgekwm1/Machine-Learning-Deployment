from flask import Flask
from sqlalchemy import Column, Integer, String, Float
import marshmallow
import sqlite3
import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import pandas as pd
from engine import MachineModel

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(BASE_DIR, 'database.db')

# initialize the database and other apps
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# Import the file to be processed as a dataframe


def is_csv(filename):
    return filename.lower().endswith('.csv')


def is_excel(filename):
    return filename.lower().endswith('.xlsx')


file = 'data/sales_data_training.csv'

df0 = None

if is_csv(file):
    try:
        df0 = pd.read_csv(file)
    except Exception as e:
        print(f"Error reading csv file: {e}")
elif is_excel(file):
    try:
        df0 = pd.read_excel(file)
    except Exception as e:
        print(f"Error reading excel file: {e}")

if df0 is not None:
    # Preprocess and clean data
    df0 = df0.dropna()
    # Select only columns that do not contain strings or are of Object type
    iter_columns = (df0.dtypes[df0.dtypes != 'object'].index if len(
        df0.dtypes[df0.dtypes != 'object']) > 0 else []).to_list()

    # Print the list of columns in the dataframe
    print(iter_columns)

    # Create the machine model object
    machine_model = MachineModel(df0)

    # Build the machine model
    machine_model.buidmodel()

    # Database models

    class Input(db.Model):
        __tablename__ = 'Input_Table'
        id = Column(Integer, primary_key=True)

    # Dynamically add columns to the Input model
    for col in iter_columns:
        setattr(Input, col, Column(Integer))

    # Print the list of columns in the Input model
    print([c.name for c in Input.__table__.columns])

    with app.app_context():
        # Drops any existing database
        db.drop_all()
        # Recreates database
        db.create_all()
        # Insert data into the database
        number_of_rows = df0.shape[0]
        number_of_cols = df0.shape[1]
        for row in range(number_of_rows):
            input_data = {col: df0.iloc[row][col] for col in iter_columns}
            input_record = Input(**input_data)
            db.session.add(input_record)
        db.session.commit()

    # Endpoints

    @app.route('/')
    def hello_world():
        return 'Hello world'

    # Serialization of Objects that cannot be jsonify(i.e. values stored in the database)
    fields = ["id"]
    fields.extend(iter_columns)

    class InputSchema(ma.Schema):
        class Meta:
            fields = tuple(fields)
else:
    raise RuntimeError("Dataframe could not be initialized")

if __name__ == "__main__":
    app.run(debug=True)
