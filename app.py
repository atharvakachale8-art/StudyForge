from flask import Flask, render_template

print("Starting Program...")

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

print("Before app.run()")

if __name__ == "__main__":
    app.run(debug=True)
    print("This should never print")