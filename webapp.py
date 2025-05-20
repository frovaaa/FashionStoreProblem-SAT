from flask import Flask, request, render_template, redirect, url_for
import subprocess
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    # Support quick test links
    testfile = request.args.get("test")
    if testfile and os.path.exists(testfile):
        filepath = testfile
        proc = subprocess.run(
            ["python3", "fashion.py", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = proc.stdout.decode("utf-8")
        return render_template("index.html", result=result)
    if request.method == "POST":
        file = request.files.get("inputfile")
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            proc = subprocess.run(
                ["python3", "fashion.py", filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = proc.stdout.decode("utf-8")
    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
