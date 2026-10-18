import csv
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def load_and_read_csv(file_path):
    """Step 1 & 2: Load and read the CSV file."""
    print(f"Loading and reading file: {file_path}")
    rows = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)
    return headers, rows

def clean_data_with_openai(headers, rows):
    """Step 3: Send data to OpenAI to clean invalid, wrong, and unclean entries."""
    print("Sending data to OpenAI for cleaning...")
    
    # Convert data to JSON string for the LLM to process easily
    data_payload = {
        "headers": headers,
        "records": rows
    }
    
    prompt = f"""
    You are an expert data cleaning assistant. 
    Here is a dataset containing 50 records with potential issues such as typos, 
    incorrect formatting, invalid values, missing data, or inconsistent casing.
    
    Please clean this dataset:
    1. Fix typos, standardize date formats, normalize names/emails, and handle missing or invalid entries logically.
    2. Do not invent completely fake data unless necessary to fix a clear typo, but ensure all fields are valid according to their context.
    3. Return ONLY valid JSON containing the cleaned "headers" and "records" in the exact same structure. Do not include markdown formatting blocks like ```json in your response, just return the raw JSON string.

    Input Data:
    {json.dumps(data_payload, indent=2)}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini", # Cost-effective and fast for data tasks
        messages=[
            {"role": "system", "content": "You are a precise data cleaning utility that returns strictly valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    cleaned_content = response.choices[0].message.content.strip()
    
    # Strip markdown code blocks if the model accidentally included them
    if cleaned_content.startswith("```"):
        cleaned_content = cleaned_content.split("\n", 1)[1]
        cleaned_content = cleaned_content.rsplit("\n", 1)[0]
        
    cleaned_data = json.loads(cleaned_content)
    return cleaned_data["headers"], cleaned_data["records"]

def create_final_csv(output_path, headers, rows):
    """Step 4: Create the final cleaned CSV file."""
    print(f"Creating final CSV file at: {output_path}")
    with open(output_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print("ETL Pipeline completed successfully!")

def main():
    input_file = "student_enrollment_raw.csv"
    output_file = "cleaned_data.csv"
    
    # Execute ETL steps
    headers, raw_rows = load_and_read_csv(input_file)
    cleaned_headers, cleaned_rows = clean_data_with_openai(headers, raw_rows)
    create_final_csv(output_file, cleaned_headers, cleaned_rows)

if __name__ == "__main__":
    main()