import pandas as pd
from flask import Flask, request, jsonify
import re
import time
import flask
import matplotlib.pyplot as plt
import io

# main.csv is a stock market analysis of Twitter, Inc. from 2019 to October 2022. I downloaded it from https://www.kaggle.com/datasets/whenamancodes/twitter-stock-market-analysis-founding-years?resource=download

app = Flask(__name__)
df = pd.read_csv("main.csv")

home_visits_count = 0
index_a_count = 0
index_b_count = 0
#do not allow more than 1 request per minute from any one IP address
last_visits = dict()

@app.route('/')
def home():
    global home_visits_count
    
    while home_visits_count < 10:
        if (home_visits_count % 2 == 0):
            with open("index_b.html") as f:
                html = f.read()
        else:
            with open("index_a.html") as f:
                html = f.read()
        home_visits_count += 1
        return html
    
    if index_a_count >= index_b_count:
        with open("index_a.html") as f:
                html = f.read()
    else:
        with open("index_b.html") as f:
                html = f.read()
    return html
      
@app.route("/browse.html")
def browse():
    #reference: https://www.geeksforgeeks.org/how-to-render-pandas-dataframe-as-html-table/
    return "<html><head></head><body><h1>Browse</h1>{}</body></html>".format(df.to_html())

@app.route("/browse.json")
def browse_json():
    global last_visits
    visitor = request.remote_addr
    df_dict = df.to_dict(orient = "records")
    
    if visitor not in last_visits:
        last_visits[visitor] = time.time()
        return jsonify(df_dict) 
    elif time.time() - last_visits[visitor] > 60:
        last_visits[visitor] = time.time()
        return jsonify(df_dict)
    else:
        return flask.Response("<p>Try again in 60 seconds</p>", status = 429, headers = {"Retry-After": "60"})
            
@app.route("/visitors.json")
def visitors_json():
    return list(last_visits.keys())
    

@app.route("/donate.html")
def donate():
    global index_a_count
    global index_b_count
    
    index_version = request.args.get("from", "version")
    if home_visits_count < 10:
        if index_version == "A":
            index_a_count += 1
        else: 
            index_b_count += 1
    return "<html><head></head><body><h1>Donate</h1></body></html>"

@app.route('/email', methods=["POST"])
def email():
    email = str(request.data, "utf-8")
    name = r"^\w+"
    at = r"@"
    domain = r"\w+\.(edu|com|net|org)"
    full_regex = f"(({name})({at})({domain}))"
    if len(re.findall(full_regex, email)) > 0: # 1
        with open("emails.txt", "a") as f: # open file in append mode
            f.write(email + "\n") # 2
            #num_subscribed = len(f.readlines())
        #reference: https://www.geeksforgeeks.org/count-number-of-lines-in-a-text-file-in-python/
        with open("emails.txt", "r") as f:
            num_subscribed = len(f.readlines())
        return jsonify(f"thanks, you're subscriber number {num_subscribed}!")
    return jsonify(f"Invalid email address. Reenter a valid email address.") # 3
    
@app.route("/dashboard_1.svg")
def dashboard_1():
    daily = request.args.get("daily", "daily_measure")
    
    if daily == "amtsold":
        fig, ax = plt.subplots(figsize=(5,4))
        ax.plot(df["Date"], df["Volume"])
        ax.set_xticks(ticks = [0, 482, 963], labels = ["1/2/2019", "11/27/2020", "10/27/2022"])
        ax.set_yticks(ticks = [3661053, 64557482, 132776016, 200994550, 269213085], labels = ["3.6", "64.6", "132.8", "201", ">269"])
        ax.set_xlabel("Date")
        ax.set_ylabel("Amount of Stock Sold (in millions)")
        ax.set_title("Daily Amount of Twitter Stock Sold from 2019-2022")
        plt.tight_layout() 
    else:
        fig, ax = plt.subplots(figsize=(5,4))
        ax.plot(df["Date"], df["High"])
        ax.set_xticks(ticks = [0, 482, 963], labels = ["1/2/2019", "11/27/2020", "10/27/2022"])
        ax.set_xlabel("Date")
        ax.set_ylabel("Price of Stock (USD)")
        ax.set_title("Highest Daily Twitter Stock Price from 2019-2022")
        plt.tight_layout()
        
    f = io.BytesIO()
    fig.savefig(f, format="svg")
    plt.close()
    return flask.Response(f.getvalue(), headers = {"Content-Type": "image/svg+xml"})
    
@app.route("/dashboard_2.svg")
def dashboard_2():
    fig, ax = plt.subplots(figsize=(8,7))
    ax.plot(df["Date"], df["Open"], label = "Open")
    ax.plot(df["Date"], df["Adj Close"], label = "Close")
    ax.legend()
    ax.set_xticks(ticks = [0, 482, 963], labels = ["1/2/2019", "11/27/2020", "10/27/2022"])
    ax.set_xlabel("Date")
    ax.set_ylabel("Price of Stock (USD)")
    ax.set_title("Price of Twitter Stock at Market Open vs Close from 2019-2022")
    
    f = io.BytesIO()
    fig.savefig(f, format="svg")
    plt.close()
    return flask.Response(f.getvalue(), headers = {"Content-Type": "image/svg+xml"})    

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) 
