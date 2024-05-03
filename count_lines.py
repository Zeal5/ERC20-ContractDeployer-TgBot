import os

def count_lines_in_python_files(directory):
    total_lines = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                print(file)
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    lines = sum(1 for line in f)
                    total_lines += lines
    return total_lines

# Use the current working directory
current_directory = os.getcwd() + "/cogs"
total_lines = count_lines_in_python_files(current_directory)
print(f'Total lines of code in Python files in the current directory: {total_lines}')

