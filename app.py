from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import time
import os

app = Flask(__name__)

# Глобальная переменная для управления выполнением кода
stop_execution = False

def run_python_code(code):
    global stop_execution
    stop_execution = False

    try:
        # Создаем временный файл для выполнения кода
        with open("temp_code.py", "w") as f:
            f.write(code)

        # Запускаем код в подпроцессе
        process = subprocess.Popen(["python", "temp_code.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ожидаем завершения или остановки
        while process.poll() is None:
            if stop_execution:
                process.terminate()
                break
            time.sleep(0.1)

        # Получаем вывод
        stdout, stderr = process.communicate()
        output = stdout.decode("utf-8") + stderr.decode("utf-8")

    except Exception as e:
        output = str(e)
    finally:
        if os.path.exists("temp_code.py"):
            os.remove("temp_code.py")

    return output

@app.route("/")
def index():
    return render_template("test.html")

@app.route("/run", methods=["POST"])
def run_code():
    code = request.json.get("code")
    output = run_python_code(code)
    return jsonify({"output": output})

@app.route("/stop", methods=["POST"])
def stop_code():
    global stop_execution
    stop_execution = True
    return jsonify({"status": "stopped"})

@app.route("/install", methods=["POST"])
def install_library():
    library = request.json.get("library")
    try:
        subprocess.check_call(["pip", "install", library])
        return jsonify({"status": "success", "message": f"Library {library} installed successfully."})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(debug=True)