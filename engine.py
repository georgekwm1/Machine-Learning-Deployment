import matplotlib.pyplot as plt
from keras._tf_keras.keras.layers import SimpleRNN, Dense, Dropout
from keras._tf_keras.keras.models import Sequential
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from keras._tf_keras.keras.models import load_model
import os
import pandas as pd
import joblib
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


class MachineModel():
    def __init__(self, dataframe=None) -> None:
        self.dataframe = dataframe

    def buidmodel(self) -> None:
        # Drop string or object type columns
        iter_columns = list(
            self.dataframe.dtypes[self.dataframe.dtypes != 'object'].index)
        # Specify the columns used to train the model(inputs) and column that defines the expected outputs
        inputs = self.dataframe[iter_columns].drop(columns=iter_columns[-1])
        outputs = self.dataframe[iter_columns[-1]].values

        # Separate data into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            inputs, outputs, test_size=0.2, random_state=5)

        # Specify a scaler
        x_scaler = MinMaxScaler((0, 1))
        y_scaler = MinMaxScaler((0, 1))

        # Scale the training dataset by fitting and transforming
        X_train_scaled = x_scaler.fit_transform(X_train)
        y_train_scaled = y_scaler.fit_transform(y_train.reshape(-1, 1))

        # Scale the testing dataset by transforming
        X_test_scaled = x_scaler.transform(X_test)
        y_test_scaled = y_scaler.transform(y_test.reshape(-1, 1))

        # Reshape the data like [rows, timestep, columns]
        X_train_reshaped = X_train_scaled.reshape(
            (X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
        X_test_reshaped = X_test_scaled.reshape(
            (X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))

        epochs = 50
        batch_size = 32
        # input_node = inputs.shape[1]
        layer_1_nodes = 300
        layer_2_nodes = 150
        layer_3_nodes = 75
        output_node = 1
        dropout = 0.2

        # Define the nodes of the model
        model = Sequential([SimpleRNN(layer_1_nodes, input_shape=(X_train_reshaped.shape[1], X_train_reshaped.shape[2]), return_sequences=True),
                            Dropout(dropout),
                            SimpleRNN(layer_2_nodes, return_sequences=True),
                            Dropout(dropout),
                            SimpleRNN(layer_3_nodes),
                            Dense(output_node)])

        # Compile model
        model.compile(optimizer='adam', loss='mse')

        # Train the model
        history = model.fit(X_train_reshaped, y_train_scaled, epochs=epochs,
                            batch_size=batch_size, verbose=1, validation_split=0.1)

        # Predict the test data
        predict_scaled = model.predict(X_test_reshaped)
        prediction = y_scaler.inverse_transform(predict_scaled)

        # Save the model
        model.save('output/model/ML_model.h5')
        joblib.dump(x_scaler, 'output/model/x_scaler.gz')
        joblib.dump(y_scaler, 'output/model/y_scaler.gz')

        # Plot the comparison of the predicted value and the actual test value
        plt.plot(y_test, label="Actual Value", color='red', linewidth=2)
        plt.plot(prediction, label="Predicted Value",
                 color='blue', linewidth=2)
        plt.legend()
        plt.savefig("output/pictures/figure.jpg")
        print("Graph generated successfully")

        # Calculate the metrics
        mae_score = mean_absolute_error(y_test, prediction)
        mse_score = mean_squared_error(y_test, prediction)
        r2 = r2_score(y_test, prediction)

        # Output the evaluation result
        print(f"MAE Score: {mae_score}")
        print(f"MSE Score: {mse_score}")
        print(f"R2 Score: {r2 * 100}%")

    def load_model(self, model_path: str) -> any:
        """Load the model from the given path."""
        try:
            model = load_model(model_path, custom_objects={'mse': 'mse'})
            return model
        except FileNotFoundError as e:
            print(
                f"Could not load the specified Model, please check you inputed the correct path: {e}")

    def predict(self, model: any, input_data: any) -> any:
        """Uses the model to give predictions for the input data"""
        iter_columns = list(
            input_data.dtypes[input_data.dtypes != 'object'].index)

        x_scaler = joblib.load('output/model/x_scaler.gz')
        y_scaler = joblib.load('output/model/y_scaler.gz')

        inputs = input_data[iter_columns].drop(
            columns=iter_columns[-1]).values  # Convert to NumPy array
        inputs_scaled = x_scaler.fit_transform(inputs)
        input_reshaped = inputs_scaled.reshape(
            (inputs_scaled.shape[0], 1, inputs_scaled.shape[1]))
        prediction_scaled = model.predict(input_reshaped)
        prediction = y_scaler.inverse_transform(prediction_scaled)
        return prediction
