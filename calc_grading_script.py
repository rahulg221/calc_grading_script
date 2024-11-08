import subprocess
import os
import sys
import tarfile
import re
from datetime import datetime
import pytz
import pandas as pd
import shutil
import tempfile

score = 0

expected_output_given = """
a: 2
x: 4
y: 3
z: 1
"""

expected_output_new = """
a: 1
x: 5
y: 2
z: 2
"""

def normalize_content(content):
    # Remove all whitespace from the content
    return ''.join(content.split())

def grade_repo(nid, clone_directory):
    global score

    # Check if the repo exists
    repo_path = "calc_new"
    
    if os.path.isdir(repo_path):
      #print("Repo exists: +1pts")
      score += 1
    else:
      #print("Repo does not exist. No credit, see Dr. Gazzillo for questions and concerns.")
      return score
      
    # Check commit times to see if submitted past deadline
    if not check_commit_times(clone_directory):
      return score

    required_files = {"grammar/Arithmetic.g4", "calc/Calc.py", "pyproject.toml", "Pipfile", "calc/__init__.py", "grammar/Makefile", "grammar/__init__.py", ".gitignore", "grammar/.gitignore"}
    actual_files = set()
    
    # Traverse calc_new directory
    for directory_path, directory_names, file_names in os.walk(clone_directory):
      # Skip directories or files under .git
      if '.git' in directory_path.split(os.sep):
          continue
      
      for file_name in file_names:
          file_path = os.path.relpath(os.path.join(directory_path, file_name), clone_directory)
          #print(file_path)
          actual_files.add(file_path)
    
    # Check if the required files are present 
    if required_files.issubset(actual_files):
        if actual_files == required_files:
            #print("Repo contains only the required files: +1pts")
            score += 1
        #else:
            #print("Repo contains the required files, but also has extra files: +0pts")
    #else:
        #print("Repo does not contain all the required files: +0pts")
      
    # Change to the cloned directory
    os.chdir(clone_directory)

    try:
      # Install dependencies with Pipenv
      pipenv_install = subprocess.run(["pipenv", "install", "-e", "./"], capture_output=True, text=True, timeout=300)
      #if pipenv_install.returncode == 0:
          #print("Dependencies installed successfully.")
      #else:
          #print("Dependency installation failed.")
          #print(pipenv_install.stderr)
  
      # Run pipenv shell and compile grammar with make
      make_grammar = subprocess.run(["pipenv", "run", "make", "-C", "grammar/"], capture_output=True, text=True, timeout=300)
      #if make_grammar.returncode == 0:
          #print("Grammar compiled successfully.")
      #else:
          #print("Grammar compilation failed.")
          #print(make_grammar.stderr)
  
      # Run calc/Calc.py with heredoc input using subprocess
      calc_run = subprocess.run(
          ["pipenv", "run", "python3", "calc/Calc.py"],
          input="a := 2\nx := a + 2\ny := 3\nz := x % y\n",
          text=True,
          capture_output=True
      )
  
      if calc_run.returncode == 0:
          #print("Output:\n", calc_run.stdout)
          if (normalize_content(calc_run.stdout) == normalize_content(expected_output_given)):
            #print("Calc.py ran successfully. +2pts")
            #print("Calc.py output successful with given example input. +1pts")
            score += 3
      #else:
          #print("Running Calc.py failed.")
          #print(calc_run.stderr)
          
      calc_run = subprocess.run(
          ["pipenv", "run", "python3", "calc/Calc.py"],
          input="a := 1\nx := a + 4\ny := 2\nz := y % x\n",
          text=True,
          capture_output=True
      )
  
      if calc_run.returncode == 0:
          #print("Output:\n", calc_run.stdout)
          if (normalize_content(calc_run.stdout) == normalize_content(expected_output_new)):
            #print("Calc.py output successful with new example input. +1pts")
            score += 1
      #else:
          #print("Running Calc.py failed.")
          #print(calc_run.stderr)

    #except subprocess.TimeoutExpired as e:
      #print("The subprocess timed out and was terminated:", e)
    #except subprocess.SubprocessError as e:
      #print(f"An error occurred while running a subprocess: {e}")
    #except Exception as e:
      #print(f"An unexpected error occurred: {e}")
    finally:
        # Return to the original directory
        os.chdir("..")
        
    total_possible_score = 6
    
    final_score = round(score, 2)
    
    #print(f"TOTAL SCORE for {nid}: {final_score}/{total_possible_score}")
    print(final_score)
    return final_score

def check_commit_times(cloned_directory):
    global score
    
    # Define the deadline as Oct 3, 2024, 11:59 PM EST
    deadline_str = "2024-10-29 23:59:59"
    est = pytz.timezone('US/Eastern')
    deadline = est.localize(datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S'))

    # Run git log command to get the commit dates in the local timezone
    git_log_command = 'git log --pretty=format:"%ad" --date=local'
    
    #print("Git commit history:")
    # Use the run_command function to execute the git log command
    success, git_log_output = run_command(git_log_command, cwd=cloned_directory)
    
    if not success:
        #print(f"Failed to get git log from {cloned_directory}")
        score = 0
        return
    
    commit_dates = git_log_output.splitlines()
    
    if not commit_dates:
        #print("No commits found in the repository.")
        score = 0
        return
    
    commits_before_deadline = 0
    commits_after_deadline = 0

    # Check all commits
    for commit_date_str in commit_dates:
        # Convert the commit date string from local time to EST for comparison
        commit_date = datetime.strptime(commit_date_str, '%a %b %d %H:%M:%S %Y')
        local_tz = pytz.timezone('US/Eastern') 
        
        # Compare commit time to the deadline in EST
        commit_date_est = local_tz.localize(commit_date)

        if commit_date_est <= deadline:
            commits_before_deadline += 1
        else:
            commits_after_deadline += 1

    # Logic to check commit times and print the corresponding message
    if commits_before_deadline > 0 and commits_after_deadline == 0:
        #print("First commit was before the due date: +0pts")
        return True
    elif commits_before_deadline > 0 and commits_after_deadline > 0:
        #print("Late penalty applied: -0.5pts")
        score -= 0.5
        return True
    elif commits_before_deadline == 0 and commits_after_deadline > 0:
        #print("First commit was after deadline: No credit, see Dr. Gazzillo for questions and concerns")
        score = 0
        return False

def run_command(command, cwd=None):
    try:
        # Run the command and capture output in binary mode to manually handle decoding
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True)
        
        # Strict UTF-8 decoding, replacing invalid characters if any
        stdout = result.stdout.decode('utf-8', errors='replace')  # Replace invalid characters
        stderr = result.stderr.decode('utf-8', errors='replace')  # Replace invalid characters

        # Print the appropriate output based on success or failure
        #if result.returncode == 0 or result.returncode == 1:
          #print(f"Command succeeded: {command}")
          #print(stdout)
        #else:
          #print(f"Command failed: {command}")
          #print(stderr)

        # Return success/failure and the captured stdout
        return (result.returncode == 0 or result.returncode == 1), stdout  # Return the output
    except Exception as e:
        #print(f"Error running command {command}: {e}")
        return False, ""

def main():
    global score
    
    if len(sys.argv) == 2:
      nid = sys.argv[1]
      
      repo_url = f"gitolite3@eustis3.eecs.ucf.edu:cop3402/{nid}/calc"
      clone_directory = "calc_new"
      
      # Remove existing directory if it exists
      if os.path.exists(clone_directory):
          shutil.rmtree(clone_directory)

      # Clone the repository
      cmd = f"git clone {repo_url} {clone_directory}"
      success, _ = run_command(cmd)
      if not success:
          # If cloning failed, give a grade of 0 for this student
          #print(f"Failed to clone repository for NID {nid}.")
          return 0

      # Check the cloned directory
      run_command(f"ls {clone_directory}")

      # Run the grading function
      score = grade_repo(nid, clone_directory)
      return score
    else:
      #print("Usage: python calc_grading_script.py <NID>")
      sys.exit(1)

      
if __name__ == "__main__":
    main()
