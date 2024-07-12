import pandas as pd
from engine import MachineModel


# file = 'data/sales_data_training.csv'
file_to_predict = 'data/sales_data_test.csv'
# df0 = pd.read_csv(file)
# df0 = df0.dropna()
df_p = pd.read_csv(file_to_predict)
df_p = df_p.dropna()

machine = MachineModel(df_p)
model = machine.load_model('output/model/ML_model.h5')
prediction = machine.predict(model, df_p)
print(prediction[:, 0][1])
