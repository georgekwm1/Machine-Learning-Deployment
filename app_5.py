from flask import Flask, jsonify, request, render_template, send_file, redirect
from sqlalchemy import Column, Integer, String, Float, Table, MetaData, create_engine, text
import marshmallow
import sqlite3
import io
import os
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import pandas as pd
from engine import MachineModel

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(BASE_DIR, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['SESSION_TYPE'] = 'filesystem'

# initialize the database and other apps
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define a base metadata object for dynamic table creation
metadata = MetaData()

# Import the file to be processed as a dataframe


def is_csv(filename):
    """Check if file is a csv file"""
    return filename.lower().endswith('.csv')


def is_excel(filename):
    """Check if file an excel file"""
    return filename.lower().endswith('.xlsx')

# Database models


class InputSchema(ma.Schema):
    id = fields.Integer()

    class Meta:
        fields = ('id',)


def add_dynamic_fields(schema_class, iter_columns):
    """Add field attributes dynamically to a specified Class"""
    for column in iter_columns:
        setattr(schema_class, column, fields.Field)

    schema_class.Meta.fields = ('id', ) + tuple(iter_columns)
    return schema_class

# Team Members Json

team_members = [
    {
        "name": "George Ogbonna",
        "role": "Team Lead / Backend Developer",
        "image": "https://avatars.githubusercontent.com/u/10302268?v=4",
        "linkedin": "https://www.linkedin.com/in/memberone",
        "github": "https://github.com/georgekwm1",
        "twitter": "https://x.com/georgekwm1"
    },
    {
        "name": "Erinle Oluwatimilehin",
        "role": "Frontend Developer",
        "image": "images/Timi-logo.png",
        "linkedin": "https://www.linkedin.com/in/oluwatimilehin-erinle-2a241b1b0",
        "github": "https://github.com/timmySpark",
        "twitter": "https://twitter.com/timmy__spark"
    },
     {
        "name": "Hamisu Yusuf",
        "role": "Devops",
        "image": "https://avatars.githubusercontent.com/u/111646226?v=4",
        "linkedin": "https://www.linkedin.com/in/hamisu-yusuf",
        "github": "https://github.com/hamisuyusuf",
        "twitter": "https://twitter.com/membertwo"
    }
]


@app.route('/')
def Home():
    """Home page"""
    return render_template('index.html')


@app.route('/test')
def test():
    return jsonify(message="This is a test"), 200


@app.route('/pred')
def pred():
    return render_template('predict.html')


@app.route('/about')
def about():
    return render_template('about.html', team_members=team_members)


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Uploads file to be evaluated and used to build and train a model to be used in prediction"""

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

            # metadata.drop_all(db.engine)
            # db.session.commit()

            # Create the machine model object
            machine_model = MachineModel(df0)

            # Build the machine model
            machine_model.buidmodel()

            # Print the list of columns in the dataframe
            print(iter_columns)

            with app.app_context():
                # Drop any existing database tables
                # Drop the existing table
                with db.engine.connect() as connection:
                    connection.execute(
                        text('DROP TABLE IF EXISTS "Input_Table"'))
                    connection.commit()

                # Dynamically create the table with columns
                dynamic_columns = [Column('id', Integer, primary_key=True)]
                dynamic_columns.extend([Column(col, Integer)
                                       for col in iter_columns])

                dynamic_table = Table(
                    'Input_Table', metadata, *dynamic_columns, extend_existing=True)
                metadata.create_all(db.engine)

                # Print the list of columns in the dynamic table
                print([c.name for c in dynamic_table.columns])

                # Insert data into the database
                number_of_rows = df0.shape[0]
                for row in range(number_of_rows):
                    input_data = {col: df0.iloc[row][col]
                                  for col in iter_columns}
                    db.session.execute(
                        dynamic_table.insert().values(input_data))
                db.session.commit()

            # Return the filename and the list of columns
            def transfer():
                return add_dynamic_fields(InputSchema, iter_columns)

            updated_schema = transfer()
            return render_template('predict.html', file=None, prediction=[], download_link=None), 200

        else:
            raise RuntimeError("Dataframe could not be initialized")


@app.route('/predict', methods=['POST'])
def predict():
    """"Uploads file to be predicted"""
    db.drop_all()
    db.session.commit()
    if 'pred_file' not in request.files:
        return 'No file inserted'
    file = request.files['pred_file']
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
            # df0 = df0.dropna()

            # Print the list of columns in the Input model
            print([c.name for c in metadata.tables['Input_Table'].columns])

            # Select only columns that do not contain strings or are of Object type
            iter_columns = (df0.dtypes[df0.dtypes != 'object'].index if len(
                df0.dtypes[df0.dtypes != 'object']) > 0 else []).to_list()

            machine = MachineModel()
            model = machine.load_model('output/model/ML_model.h5')
            prediction = machine.predict(model, df0)

            # Save prediction to a CSV file
            prediction_df = pd.DataFrame(prediction)
            new_prediction = prediction_df.iloc[:]
            df0[iter_columns[-1]] = new_prediction
            df0.to_csv('prediction.csv', index=False)
            print(df0)

            # Convert DataFrame to a list of dictionaries for Jinja2
            prediction_list = df0.to_dict(orient='records')

            return render_template('predict.html', prediction=prediction_list, download_link='/download')
        return render_template('home.html', error="No file uploaded")


@app.route('/download')
def download_file():
    return send_file('prediction.csv', as_attachment=True)


@app.route('/404')
def err():
    return render_template('404.html')


if __name__ == "__main__":
    app.run(debug=True)
