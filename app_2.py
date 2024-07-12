from flask import Flask, jsonify, request, render_template
from sqlalchemy import Column, Integer, String, Float
import marshmallow
import sqlite3
import io
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
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

# initialize the database and other apps
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# Ensure the upload folder exists
# if not os.path.exists(app.config['SQLALCHEMY_DATABASE_URI']):
#     os.makedirs(app.config['SQLALCHEMY_DATABASE_URI'])

# Import the file to be processed as a dataframe


def is_csv(filename):
    return filename.lower().endswith('.csv')


def is_excel(filename):
    return filename.lower().endswith('.xlsx')

# Database models


class Input(db.Model):
    __tablename__ = 'Input_Table'
    id = Column(Integer, primary_key=True)

    # Endpoints


@app.route('/')
def hello_world():
    return render_template('home.html')


@app.route('/test')
def test():
    return jsonify(message="This is a test"), 200


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file inserted'
    file = request.files['file']
    if file.filename == '':
        return 'No file selected'
    if file:
        filename = file.filename

        df0 = None

        if is_csv(filename):
            try:
                df0 = pd.read_csv(io.BytesIO(file.read()))
            except Exception as e:
                print(f"Error reading csv file: {e}")
        elif is_excel(file):
            try:
                df0 = pd.read_excel(io.BytesIO(file.read()))
            except Exception as e:
                print(f"Error reading excel file: {e}")

        if df0 is not None:
            # Preprocess and clean data
            df0 = df0.dropna()
            # Select only columns that do not contain strings or are of Object type
            iter_columns = (df0.dtypes[df0.dtypes != 'object'].index if len(
                df0.dtypes[df0.dtypes != 'object']) > 0 else []).to_list()

            # Create the machine model object
            machine_model = MachineModel(df0)

            # Build the machine model
            machine_model.buidmodel()

            # Print the list of columns in the dataframe
            print(iter_columns)

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
                    input_data = {col: df0.iloc[row][col]
                                  for col in iter_columns}
                    input_record = Input(**input_data)
                    db.session.add(input_record)
                db.session.commit()

                # Serialization of Objects that cannot be jsonify(i.e. values stored in the database)
                input = ["id"]
                input.extend(iter_columns)

                class InputSchema(ma.Schema):
                    class Meta:

                        fields = tuple(input)
        else:
            raise RuntimeError("Dataframe could not be initialized")


@app.route('/predict', methods=['POST'])
def predict():
    input_data = request.get_json()
    input_record = Input(**input_data)
    db.session.add(input_record)
    db.session.commit()
    machine = MachineModel()
    model = machine.load_model('output/model/ML_model.h5')
    prediction = machine.predict(model, input_data)
    return jsonify(prediction=prediction)


if __name__ == "__main__":
    app.run(debug=True)
