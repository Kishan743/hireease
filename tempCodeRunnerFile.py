from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "HIRE-EASE IS RUNNING -- NOT NOTES"

if __name__ == "__main__":