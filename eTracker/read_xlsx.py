import pandas as pd



expenses = pd.read_excel('shopping.xlsx', usecols="A:G")
print(expenses.head())
