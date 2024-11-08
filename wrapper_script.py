import os
import shutil
import subprocess
import pandas as pd

# Path to the CSV file containing NID and grades
csv_file = "calc_grades.csv"
# Test cases to pass to the grading script
test_cases = ["public_testcases", "private_testcases"]  # Add more as needed

# Read the CSV file
df = pd.read_csv(csv_file)
total_scores = 0
num_students = len(df)

for index, row in df.iterrows():
    try:
        score = 0
        nid = row['SIS Login ID']

        # Run the grading script for the current student and collect the score
        grading_cmd = ["pipenv", "python", "calc_grading_script.py", nid]
        result = subprocess.run(grading_cmd, capture_output=True, text=True)

        # Check if the grading script ran successfully
        if result.returncode == 0:
            # Parse the score from the output if it's returned as a numeric value
            score = float(result.stdout.strip())  # Adjust parsing as necessary
            print(f"Student {nid} graded with score: {score}.")
        else:
            print(f"Grading script failed for NID {nid}. Error: {result.stderr}")

        # Update the CSV with the calculated score
        df.at[index, 'calc (8598317)'] = score
        total_scores += score

    except Exception as e:
        print(f"Error processing student {nid}: {e}")
        # Optionally set score to 0 for the student that caused the error
        df.at[index, 'calc (8598317)'] = 0

# Save the updated grades back to the CSV file
df.to_csv(csv_file, index=False)

# Print the average score
print(f'Avg score: {total_scores / num_students}')
print('Grading complete.')
