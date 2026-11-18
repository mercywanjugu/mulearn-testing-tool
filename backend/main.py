from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess
import sqlite3
import time
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploaded_code"
SANDBOX_DIR = "./uploaded_code/sandbox"
DB_PATH = "./mulearn.db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SANDBOX_DIR, exist_ok=True)

# ==========================================
# SQLITE DATABASE SETUP (Matches Chapter 4 ERD)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PROJECTS (
            Project_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Project_Name TEXT,
            Programming_Language TEXT,
            Date_Created TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CODE_FILES (
            File_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Project_ID INTEGER,
            File_Name TEXT,
            Local_Storage_Path TEXT,
            Total_Lines INTEGER,
            FOREIGN KEY(Project_ID) REFERENCES PROJECTS(Project_ID)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MUTATION_RUNS (
            Run_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            File_ID INTEGER,
            File_Name TEXT,
            Language TEXT,
            Result_Status TEXT,
            Final_Mutation_Score REAL,
            Execution_Duration REAL,
            Timestamp TEXT,
            FOREIGN KEY(File_ID) REFERENCES CODE_FILES(File_ID)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_run_to_db(filename, language, result_status, score, duration, total_lines):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO PROJECTS (Project_Name, Programming_Language, Date_Created) VALUES (?, ?, ?)",
        (f"Assignment_{filename}", language, now)
    )
    project_id = cursor.lastrowid
    
    cursor.execute(
        "INSERT INTO CODE_FILES (Project_ID, File_Name, Local_Storage_Path, Total_Lines) VALUES (?, ?, ?, ?)",
        (project_id, filename, os.path.join(UPLOAD_DIR, filename), total_lines)
    )
    file_id = cursor.lastrowid
    
    cursor.execute(
        """INSERT INTO MUTATION_RUNS 
           (File_ID, File_Name, Language, Result_Status, Final_Mutation_Score, Execution_Duration, Timestamp) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (file_id, filename, language, result_status, score, round(duration, 3), now)
    )
    conn.commit()
    conn.close()

@app.get("/")
def read_root():
    return {"status": "Online", "message": "MuLearn Multi-Language & SQLite Engine is ready."}

@app.get("/history/")
def get_history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM MUTATION_RUNS ORDER BY Run_ID DESC LIMIT 5")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"runs": rows}

@app.post("/run-mutation/")
async def run_mutation_test(
    code_file: UploadFile = File(...), 
    test_file: UploadFile = File(...)
):
    start_time = time.time()
    code_path = os.path.join(UPLOAD_DIR, code_file.filename)
    test_path = os.path.join(UPLOAD_DIR, test_file.filename)
    
    with open(code_path, "wb") as b:
        shutil.copyfileobj(code_file.file, b)
    with open(test_path, "wb") as b:
        shutil.copyfileobj(test_file.file, b)

    with open(code_path, "r") as f:
        original_code = f.read()

    total_lines = len(original_code.splitlines())

    if "+" in original_code:
        mutated_code = original_code.replace("+", "-")
    else:
        mutated_code = original_code

    # OPTION A: PYTHON EXECUTION ENGINE (.py)
    if code_file.filename.endswith(".py"):
        sandbox_code_path = os.path.join(SANDBOX_DIR, code_file.filename)
        sandbox_test_path = os.path.join(SANDBOX_DIR, test_file.filename)

        with open(sandbox_code_path, "w") as f:
            f.write(mutated_code)
        shutil.copy(test_path, sandbox_test_path)

        try:
            run_process = subprocess.run(
                ["python3", test_file.filename],
                cwd=SANDBOX_DIR,
                timeout=2.0,
                capture_output=True,
                text=True
            )
            duration = time.time() - start_time
            if run_process.returncode != 0:
                res_text = "Mutant KILLED (Python)"
                save_run_to_db(code_file.filename, "Python", res_text, 100.0, duration, total_lines)
                return {
                    "status": "Success",
                    "result": res_text,
                    "details": "Great job! The Python test suite caught the intentional math error and failed as expected."
                }
            else:
                res_text = "Mutant SURVIVED (Python)"
                save_run_to_db(code_file.filename, "Python", res_text, 0.0, duration, total_lines)
                return {
                    "status": "Warning",
                    "result": res_text,
                    "details": "The Python test suite is weak! It passed even though '+' was changed to '-'."
                }
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            res_text = "Mutant KILLED (Infinite Loop)"
            save_run_to_db(code_file.filename, "Python", res_text, 100.0, duration, total_lines)
            return {
                "status": "Success",
                "result": res_text,
                "details": "The Python mutant caused an infinite loop and was stopped by the 2-second timer."
            }

    # OPTION B: C++ EXECUTION ENGINE (.cpp)
    elif code_file.filename.endswith(".cpp"):
        mutant_file_path = os.path.join(UPLOAD_DIR, "mutant_calculator.cpp")
        with open(mutant_file_path, "w") as f:
            f.write(mutated_code)

        output_binary = os.path.join(UPLOAD_DIR, "mutant_test_run")
        
        compile_process = subprocess.run(
            ["g++", mutant_file_path, test_path, "-o", output_binary],
            capture_output=True, text=True
        )

        if compile_process.returncode != 0:
            duration = time.time() - start_time
            res_text = "Mutant Statically Caught"
            save_run_to_db(code_file.filename, "C++", res_text, 100.0, duration, total_lines)
            return {
                "status": "Failed",
                "result": res_text,
                "details": "The mutant caused a C++ compilation error.",
                "compiler_error": compile_process.stderr
            }

        try:
            run_process = subprocess.run(
                [output_binary],
                timeout=2.0, capture_output=True, text=True
            )
            duration = time.time() - start_time
            if run_process.returncode != 0:
                res_text = "Mutant KILLED (C++)"
                save_run_to_db(code_file.filename, "C++", res_text, 100.0, duration, total_lines)
                return {
                    "status": "Success",
                    "result": res_text,
                    "details": "Excellent! The C++ test suite caught the intentional math error and failed."
                }
            else:
                res_text = "Mutant SURVIVED (C++)"
                save_run_to_db(code_file.filename, "C++", res_text, 0.0, duration, total_lines)
                return {
                    "status": "Warning",
                    "result": res_text,
                    "details": "The C++ test suite is weak! It passed even though '+' was changed to '-'."
                }
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            res_text = "Mutant KILLED (Infinite Loop)"
            save_run_to_db(code_file.filename, "C++", res_text, 100.0, duration, total_lines)
            return {
                "status": "Success",
                "result": res_text,
                "details": "The C++ mutant triggered an infinite loop and was stopped by the 2-second timer."
            }

    else:
        return {
            "status": "Warning",
            "result": "Unsupported File Type",
            "details": "Please upload a valid .py or .cpp file."
        }


