from flask import Flask, request, render_template
import subprocess
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def parse_sat_output(output):
    lines = output.splitlines()
    if any("UNSAT" in line for line in lines):
        return "UNSATISFIABLE", []
    selected = []
    for line in lines:
        if line.startswith("v ") or line.startswith("s SATISFIABLE"):
            continue
        if line.strip().startswith("c "):
            # Try to extract selected garment from comment lines
            parts = line.strip().split()
            if len(parts) > 1 and parts[1].startswith("G_"):
                selected.append(parts[1][2:])  # Remove 'G_' prefix
    if selected:
        return "SATISFIABLE", selected
    return "SATISFIABLE", []


@app.route("/load_test_file")
def load_test_file():
    """Load content of a test file for filling dropdowns."""
    testfile = request.args.get("file")
    if not testfile:
        return "No file specified", 400
    
    # Security check - only allow files from sat_tests and unsat_tests directories
    if not (testfile.startswith("sat_tests/") or testfile.startswith("unsat_tests/")):
        return "Invalid file path", 400
    
    if not os.path.exists(testfile):
        return "File not found", 404
    
    try:
        with open(testfile, 'r') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}", 500


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    status = None
    selected = []
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
        status, selected = parse_sat_output(result)
        return render_template(
            "index.html", result=result, status=status, selected=selected
        )
    
    if request.method == "POST":
        # Check for text restrictions input
        text_restrictions = request.form.get("text_restrictions", "").strip()
        if text_restrictions:
            # Parse text restrictions
            garment_pairs = []
            lines = text_restrictions.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        garment_type = parts[0].lower()
                        garment_color = parts[1].lower()
                        garment_pairs.append((garment_type, garment_color))
            
            if garment_pairs:
                # Write to a temp file in the same format as the uploaded file
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, mode="w", suffix=".txt", dir=UPLOAD_FOLDER
                ) as tmp:
                    for g, c in garment_pairs:
                        tmp.write(f"{g} {c}\n")
                    tmp_path = tmp.name
                proc = subprocess.run(
                    ["python3", "fashion.py", tmp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                result = proc.stdout.decode("utf-8")
                status, selected = parse_sat_output(result)
                return render_template(
                    "index.html", result=result, status=status, selected=selected
                )
        
        # Check for garment/color direct input (dropdown selections)
        garment_types = request.form.getlist("garment_type[]")
        garment_colors = request.form.getlist("garment_color[]")
        # Only use if at least one non-empty pair is present
        garment_pairs = [
            (g.strip(), c.strip())
            for g, c in zip(garment_types, garment_colors)
            if g.strip() and c.strip()
        ]
        if garment_pairs:
            # Write to a temp file in the same format as the uploaded file
            import tempfile

            with tempfile.NamedTemporaryFile(
                delete=False, mode="w", suffix=".txt", dir=UPLOAD_FOLDER
            ) as tmp:
                for g, c in garment_pairs:
                    tmp.write(f"{g} {c}\n")
                tmp_path = tmp.name
            proc = subprocess.run(
                ["python3", "fashion.py", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            result = proc.stdout.decode("utf-8")
            status, selected = parse_sat_output(result)
        else:
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
                status, selected = parse_sat_output(result)
    
    return render_template(
        "index.html", result=result, status=status, selected=selected
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=True, host="0.0.0.0", port=port)
