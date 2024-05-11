import pandas as pd
import requests
import json

keyFile = open('D:/OneDrive/PycharmProjects/bzm_telraam/Data_files/telraam_api.txt', 'r')
access_token = keyFile.readline().rstrip()
keyFile.close()

url = "https://telraam-api.net/v1/reports/traffic"
body = {
    "id":"9000001661",
    "time_start":"2024-01-01 00:00:00Z",
    "time_end":"2024-02-28 00:00:00Z",
    "level":"segments",
    "format":"per-hour"
}
headers = {
  'X-Api-Key': access_token
}
payload = str(body)
response = requests.request("POST", url, headers=headers, data=payload)
json = response.json()
#print(json)
dataframe = pd.DataFrame(json['report'])
print(dataframe.columns)
print(dataframe['car'])
dataframe.to_csv('test.csv')