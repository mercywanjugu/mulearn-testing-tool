from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess

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
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SANDBOX_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "Online", "message": "MuLearn Multi-Language Engine is ready."}

@app.post("/run-mutation/")
async def run_mutation_test(
    code_file: UploadFile = File(...), 
    test_file: UploadFile = File(...)
):
    code_path = os.path.join(UPLOAD_DIR, code_file.filename)
    test_path = os.path.join(UPLOAD_DIR, test_file.filename)
    
    with open(code_path, "wb") as b:
        shutil.copyfileobj(code_file.file, b)
    with open(test_path, "wb") as b:
        shutil.copyfileobj(test_file.file, b)

    with open(code_path, "r") as f:
        original_code = f.read()

    # Create the mutant by swapping '+' with '-'
    if "+" in original_code:
        mutated_code = original_code.replace("+", "-")
    else:
        mutated_code = original_code

    # ==========================================
    # OPTION A: PYTHON EXECUTION ENGINE (.py)
    # ==========================================
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
            if run_process.returncode != 0:
                return {
                    "status": "Success",
                    "result": "Mutant KILLED (Python)",
                    "details": "Great job! The Python test suite caught the intentional math error and failed as expected."
                }
            else:
                return {
                    "status": "Warning",
                    "result": "Mutant SURVIVED (Python)",
                    "details": "The Python test suite is weak! It passed even though '+' was changed to '-'."
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "Success",
                "result": "Mutant KILLED (Infinite Loop)",
                "details": "The Python mutant caused an infinite loop and was stopped by the 2-second timer."
            }

    # ==========================================
    # OPTION B: C++ EXECUTION ENGINE (.cpp)
    # ==========================================
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
            return {
                "status": "Failed",
                "result": "Mutant Statically Caught",
                "details": "The mutant caused a C++ compilation error.",
                "compiler_error": compile_process.stderr
            }

        try:
            run_process = subprocess.run(
                [output_binary],
                timeout=2.0, capture_output=True, text=True
            )
            if run_process.returncode != 0:
                return {
                    "status": "Success",
                    "result": "Mutant KILLED (C++)",
                    "details": "Excellent! The C++ test suite caught the intentional math error and failed."
                }
            else:
                return {
                    "status": "Warning",
                    "result": "Mutant SURVIVED (C++)",
                    "details": "The C++ test suite is weak! It passed even though '+' was changed to '-'."
                }
        except subprocess.TimeoutExpired:
            return {
                "status": "Success",
                "result": "Mutant KILLED (Infinite Loop)",
                "details": "The C++ mutant triggered an infinite loop and was stopped by the 2-second timer."
            }

    else:
        return {
            "status": "Warning",
            "result": "Unsupported File Type",
            "details": "Please upload a valid .py or .cpp file."
        }

