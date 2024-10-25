from flask import Flask, request, send_file, render_template
import requests
import pandas as pd
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    from_date = request.form['from_date']  # Expecting format: YYYY-MM-DD
    to_date = request.form['to_date']      # Expecting format: YYYY-MM-DD

    url = 'https://1paytag.hdfcbank.com/walletmware/api/wallet/txn/wallettxninfo'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'C240330814:95ef659313847c7485d43d66b8c5b9e8b817c9c136d2798333c5df693b6efc2a',
        'salt': '95ef659313847c7485d43d66b8c5b9e8b817c9c136d2798333c5df693b6efc2a'
    }

    # Format dates to required format
    new_from_date_time = f"{from_date.replace('-', '')} 000000"
    new_to_date_time = f"{to_date.replace('-', '')} 235959"

    data = {
        "requestTime": "20210215125830",
        "fromDate": new_from_date_time,
        "walletId": "W0124020218238920055",
        "merchantID": "HDFCWL",
        "requestID": "001",
        "toDate": new_to_date_time,
        "contactNumber": "",
        "vehicleNumber": "",
        "requestSource": "BD"
    }

    # Make the API call
    response = requests.post(url, json=data, headers=headers)

    # Print the response status and body for debugging
    print(f"Response Status Code: {response.status_code}")
    #print(f"Response Body: {response.text}")

    if response.status_code == 200:
        response_data = response.json()
        # Check if 'data' key exists in the response
        if 'data' in response_data:
            if response_data['data']:  # Check if data list is not empty
                df = pd.json_normalize(response_data['data'])

                # Filter and rename columns
                df = df[['reqTime', 'partnerRefId', 'narration', 'transactiontype',
                         'openingBalance', 'txnAmt', 'closingBalance',
                         'vehicleNo', 'tollplazaname', 'tollplazaid', 'tollTxnDateTime']]

                df.rename(columns={
                    'reqTime': 'Date and Time',
                    'partnerRefId': 'Transaction ID',
                    'narration': 'Narration',
                    'transactiontype': 'Transaction Type',
                    'openingBalance': 'Opening Balance',
                    'txnAmt': 'Amount',
                    'closingBalance': 'Closing Balance',
                    'vehicleNo': 'Vehicle No',
                    'tollplazaname': 'Toll Name',
                    'tollplazaid': 'Toll ID',
                    'tollTxnDateTime': 'Plaza Reader Time'
                }, inplace=True)

                # Convert Date and Time to datetime format and format accordingly
                df['Date and Time'] = pd.to_datetime(df['Date and Time']).dt.strftime('%d-%m-%Y %H:%M:%S')
                df['Plaza Reader Time'] = pd.to_datetime(df['Plaza Reader Time']).dt.strftime('%d-%m-%Y %H:%M:%S')

                # Convert specified columns to numeric
                df['Opening Balance'] = pd.to_numeric(df['Opening Balance'], errors='coerce')
                df['Closing Balance'] = pd.to_numeric(df['Closing Balance'], errors='coerce')
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

                # Create a new 'Date' column with only the date part, formatted as 'dd-mm-yyyy'
                df['Date'] = pd.to_datetime(df['Date and Time']).dt.strftime('%d-%m-%Y')

                # Create an empty column named 'Wallet Transaction ID' at position 3
                df.insert(3, 'Wallet Transaction ID', '-')

                # Reorder the columns
                df = df[['Date and Time', 'Date', 'Transaction ID', 'Wallet Transaction ID', 'Narration',
                         'Transaction Type', 'Opening Balance', 'Amount', 'Closing Balance',
                         'Vehicle No', 'Toll Name', 'Toll ID', 'Plaza Reader Time']]

                # Create the Excel file name using fromDate and toDate
                excel_filename = f"transactions_{from_date.replace('-', '')}_to_{to_date.replace('-', '')}.xlsx"

                # Save DataFrame to Excel
                df.to_excel(excel_filename, index=False)
                print(f"Data saved to Excel file: {excel_filename}")

                return send_file(excel_filename, as_attachment=True)

            else:
                return "No transactions found for the given date range.", 200
        else:
            return f"Error: 'data' key not found in response. Full response: {response_data}", 500
    else:
        return f"Failed to fetch data. Status code: {response.status_code}", 500

if __name__ == '__main__':
    app.run(debug=True)
