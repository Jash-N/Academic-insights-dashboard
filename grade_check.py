# Importing required libraries
import pandas as pd 
import tkinter as tk
from tkinter import filedialog, messagebox
import mysql.connector
import openpyxl

# Database connection details 
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root" 
DB_NAME = "grade_project_db"
TABLE_NAME = "grades"

# Create DB
def create_table(cursor):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        student_id VARCHAR(50),
        student_name VARCHAR(100),
        subject VARCHAR(50),
        marks_obtained INT,
        total_marks INT,
        grade VARCHAR(5),
        term VARCHAR(20),
        year INT,
        UNIQUE KEY unique_grade (
            student_id, student_name, subject, marks_obtained, total_marks, grade, term, year
        )
    )
    """)

# ---------- NORMALIZATION ----------
def normalize_dataframe(df):
    rename_map = {
        "ID": "student_id",
        "Student_ID": "student_id",
        "Name": "student_name",
        "StudentName": "student_name"
    }
    df.rename(columns=rename_map, inplace=True)

    records = []
    year = 2025
    term = "Term 1"
    total_marks = 100

    # Detect subjects dynamically (anything not in ID/Name columns)
    subject_cols = [
        c for c in df.columns
        if c not in ["student_id", "student_name"] and pd.api.types.is_numeric_dtype(df[c])
    ]

    for _, row in df.iterrows():
        student_id = row.get("student_id", None)
        student_name = row.get("student_name", None)

        for subject in subject_cols:
            marks_obtained = row[subject]
            if pd.isnull(marks_obtained):
                continue  # skip if marks are missing
            marks_obtained = int(marks_obtained)
            
            if marks_obtained >= 94:
                grade = "A+"
            elif marks_obtained >= 85:
                grade = "A"
            elif marks_obtained >= 80:
                grade = "B"
            elif marks_obtained >= 60:
                grade = "C"
            elif marks_obtained >= 50:
                grade = "D"
            else:
                grade = "F"

            records.append({
                "student_id": student_id,
                "student_name": student_name,
                "subject": subject,
                "marks_obtained": marks_obtained,
                "total_marks": total_marks,
                "grade": grade,
                "term": term,
                "year": year
            })

    return pd.DataFrame(records)

# ---------- MAIN PROCESS ----------
def process_file(file_path):
    # Read file, ignore index column if present
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, engine="openpyxl") 
    else:
        messagebox.showerror("Error", "Unsupported file format!")
        return

    # If the file already has a 'subject' column, skip normalization
    if "subject" in df.columns and "marks_obtained" in df.columns:
        normalized_df = df
    else:
        normalized_df = normalize_dataframe(df)

    # Remove completely empty rows
    normalized_df = normalized_df.dropna(how='all')

    # Remove index column if present
    if normalized_df.columns[0].lower().startswith("unnamed") or normalized_df.columns[0] == "":
        normalized_df = normalized_df.iloc[:, 1:]

    # Remove duplicate rows based on all columns (except the index)
    normalized_df = normalized_df.drop_duplicates(
        subset=["student_id", "student_name", "subject", "marks_obtained", "total_marks", "grade", "term", "year"]
    )

    # Connect DB
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.database = DB_NAME

    create_table(cursor)

    # Insert data
    for _, row in normalized_df.iterrows():
        try:
            cursor.execute(f"""
            INSERT IGNORE INTO {TABLE_NAME} 
            (student_id, student_name, subject, marks_obtained, total_marks, grade, term, year)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, tuple(row))
        except Exception as e:
            print("Error inserting row:", row)
            print(e)
    
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Data uploaded successfully to MySQL!")

# ---------- UI ----------
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV/Excel Files", "*.csv *.xlsx")])
    if file_path:
        process_file(file_path)

root = tk.Tk()
root.title("Student Grade Uploader")

btn = tk.Button(root, text="Upload Grade File (Excel or CSV)", command=upload_file, width=45, height=2)
btn.pack(pady=20)

root.mainloop() 