import os
import re

def collect_imports(directory):
    imports = set()
    import_pattern = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)')
    
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py') or filename.endswith('.ipynb'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r') as file:
                    for line in file:
                        match = import_pattern.match(line)
                        if match:
                            imports.add(match.group(1))
    return imports

def generate_setup_py(package_name, version, author, author_email, description, url, directory):
    imports = collect_imports(directory)
    py_files = collect_files(directory, ['.py'])
    nb_files = collect_files(directory, ['.ipynb'])
    
    with open('setup.py', 'w') as f:
        f.write(f"""from setuptools import setup, find_packages

setup(
    name='{package_name}',
    version='{version}',
    packages=find_packages(),
    include_package_data=True,
    package_data={{'': {py_files + nb_files}}},
    install_requires={list(imports)},
    author='{author}',
    author_email='{author_email}',
    description='{description}',
    url='{url}',
)
""")

def collect_files(directory, extensions):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                files.append(os.path.join(root, filename))
    return files

# Customize these values
package_name = 'calvin_vbm'
version = '0.1'
author = 'Calvin William Howard'
author_email = 'choward12@bwh.harvard.edu'
description='This package uses spm/cat12 in Docker files I have created to process and extract tissue segments. It then uses python perform z-scoring and w-scoring of those segments. This expects you have nimlab installed.'
url = 'https://github.com/Calvinwhow/vbm.git'
directory = '.'

generate_setup_py(package_name, version, author, author_email, description, url, directory)
