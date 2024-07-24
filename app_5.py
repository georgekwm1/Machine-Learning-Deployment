from flask import Flask, jsonify, request, render_template, send_file, redirect, url_for
from sqlalchemy import Column, Integer, String, Float, Table, MetaData, create_engine, text
import marshmallow
import sqlite3
import io
import os
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
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
# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'geonaetltd@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# initialize the database and other apps
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

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
        "name": "Ogbonna George Ekwueme",
        "role": "Team Lead / Backend Developer / Machine Learning Engineer",
        "image": "https://avatars.githubusercontent.com/u/10302268?v=4",
        "linkedin": "https://www.linkedin.com/in/georgekwm1",
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
        "twitter": "https://twitter.com/Yuskey123"
    }
]


@app.route('/')
def Home():
    """Home page"""
    return render_template('index.html')


@app.route('/about')
def about():
    """About page"""
    return render_template('about.html', team_members=team_members)


@app.route('/test')
def test():
    return jsonify(message="This is a test"), 200


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        number = request.form['number']
        text_area = request.form['text']

        # Send email
        msg = Message()
        msg.subject = "Contact submission form"
        msg.sender = 'geonaetltd@gmail.com'
        msg.recipients = ['geonaetltd@gmail.com',
                          'timmyspark1@gmail.com', 'hamisuyusuf180@gmail.com']
        msg.body = f"""
        First Name: {firstname}
        Last Name: {lastname}
        Email: {email}
        Phone Number: {number}
        Message: {text_area}
        """
        msg.reply_to = email
        mail.send(msg)
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


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


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """"Uploads file to be predicted"""
    if request.method == 'POST':
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

                prediction_list = prediction_list[:10]

                return render_template('predict.html', prediction=prediction_list, download_link='/download')
            return render_template('home.html', error="No file uploaded")
    return render_template('predict.html')


@app.route('/download')
def download_file():
    return send_file('prediction.csv', as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
