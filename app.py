from flask import Flask, render_template
import pyodbc
import plotly.express as px
import plotly.io as pio
import pandas as pd
import redis
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)

# load_dotenv()
# redis_host = os.getenv('REDIS_HOST')
# redis_conn_str = os.getenv('REDIS_CONNECTION_STRING')
# redis_client=redis.Redis(host=redis_host, port=6380, password=redis_conn_str, ssl=True)

# Connect to Azure SQL Database
def get_data_from_sql():
    # try:
    #     cached_data = redis_client.get('water_quality_data')
    #     if cached_data:
    #         print("Fetching data from cache...")
    #         return pd.DataFrame(json.loads(cached_data))
    # except Exception as e:
    #     print(f"Error accessing cache: {e}")

    conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};'
                          'SERVER=team-5-server.database.windows.net;'
                          'DATABASE=water-quality-management;'
                          'UID=team-5;'
                          'PWD=ppcm@12345')
    query = "SELECT * FROM water_quality"
    data = pd.read_sql(query, conn)
    conn.close()

    # redis_client.set('water_quality_data', data.to_json(orient='records'), ex=3600)
    return data

@app.route('/')
def dashboard():
    # Get the data from SQL
    data = get_data_from_sql()

    # Convert "Date Time" to datetime format
    data['Date_Time'] = pd.to_datetime(data['Date_Time'])

    # Generate insights
    unsafe_data = data[data['Quality'] == 'Unsafe']
    safe_count = len(data[data['Quality'] == 'Safe'])
    unsafe_count = len(unsafe_data)
    unsafe_summary = unsafe_data.groupby('City')['Quality'].count().reset_index()
    unsafe_summary.columns = ['City', 'Unsafe Count']

    # Create charts using Plotly
    fig1 = px.line(data, x='Date_Time', y='pH', color='City',
                   title='pH Levels Over Time',
                   labels={'Date Time': 'Date', 'pH': 'pH Level'})
    
    fig2 = px.bar(unsafe_summary, x='City', y='Unsafe Count',
                  title='Unsafe Water Quality Incidents by City',
                  labels={'City': 'City', 'Unsafe Count': 'Count of Unsafe Reports'},
                  color='Unsafe Count',
                  color_continuous_scale='Reds')
    
    fig3 = px.scatter(data, x='Date_Time', y='Turbidity', color='Quality',
                      title='Turbidity Levels Over Time',
                      labels={'Date Time': 'Date', 'Turbidity': 'Turbidity Level'},
                      color_discrete_map={'safe': 'green', 'unsafe': 'red'})

    # Convert Plotly figures to HTML for embedding
    graph1 = pio.to_html(fig1, full_html=False)
    graph2 = pio.to_html(fig2, full_html=False)
    graph3 = pio.to_html(fig3, full_html=False)

    # Pass insights and graphs to the template
    return render_template('dashboard.html', 
                           graph1=graph1, graph2=graph2, graph3=graph3,
                           safe_count=safe_count, unsafe_count=unsafe_count)

if __name__ == '__main__':
    app.run(debug=True)
