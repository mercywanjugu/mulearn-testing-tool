from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess

app = FastAPI()

# 🛡️ FIX: This tells your Ubuntu browser that it's 100% safe to link React and FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allows your React app port
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP actions (POST, GET, etc.)
    allow_headers=["*"],  # Allows all communication headers
)

UPLOAD_DIR = "./uploaded_code"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"status": "Online", "message": "MuLearn Engine is ready."}

@app.post("/run-mutation/")
async def run_mutation_test(
    code_file: UploadFile = File(...), 
    test_file: UploadFile = File(...)
):
    # Make sure we read the single actual file object out of the incoming array
    # because React passes files slightly differently than Swagger Docs
    actual_code_file = code_file[0] if isinstance(code_file, list) else code_file
    actual_test_file = test_file[0] if isinstance(test_file, list) else test_file

    code_path = os.path.join(UPLOAD_DIR, actual_code_file.filename)
    test_path = os.path.join(UPLOAD_DIR, actual_test_file.filename)
    
    with open(code_path, "wb") as b:
        shutil.copyfileobj(actual_code_file.file, b)
    with open(test_path, "wb") as b:
        shutil.copyfileobj(actual_test_file.file, b)

    with open(code_path, "r") as f:
        original_code = f.read()

    if "+" in original_code:
        mutated_code = original_code.replace("+", "-")
    else:
        mutated_code = original_code

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
            "details": "The mutant caused a compilation error.",
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
                "result": "Mutant KILLED",
                "details": "Excellent! The student's test suite successfully noticed the intentional math error and failed."
            }
        else:
            return {
                "status": "Warning",
                "result": "Mutant SURVIVED",
                "details": "The student's test suite is weak! It passed even though the addition sign was changed to subtraction."
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "Success",
            "result": "Mutant KILLED (Infinite Loop)",
            "details": "The mutant triggered an infinite loop, but was safely terminated by our 2-second protective timer."
        }
