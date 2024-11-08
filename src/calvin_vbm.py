import os
import sys
import platform
import subprocess

class CalvinVBM:
    """
    CalvinVBM is a class for orchestrating neuroimaging data processing using Docker.
    It facilitates building Docker images and running Docker containers on individual directories containing NIfTI files.
    """

    @staticmethod
    def build_docker_image(project_root_path=None):
        """
        Navigates to the /containers directory under the provided project root path
        and builds the Docker image from Dockerfile.cat12. If no project_root_path 
        is provided, it assumes the script is running from /notebooks and uses a 
        relative path.

        Args:
            project_root_path (str): The absolute path to the project root directory.
        """
        if project_root_path:
            containers_path = os.path.join(project_root_path, "containers")
        else:
            containers_path = "../containers"

        if not os.path.isdir(containers_path):
            raise FileNotFoundError(f"Directory not found: {containers_path}")

        # Change to the containers directory
        os.chdir(containers_path)
        print("Building Docker image...")
        result = subprocess.run(
            ["docker", "build", "-t", "cat12:latest", "-f", "Dockerfile.cat12", "."],
            capture_output=True,
            text=True
        )
        if result.stdout: print(result.stdout)
        if result.stderr: print(result.stderr)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args)
        print("Docker image built successfully.")

    @staticmethod
    def convert_path_for_docker(path):
        """
        Converts a Windows path to a Docker-compatible path (if running on Windows).

        Args:
            path (str): The original file system path.

        Returns:
            str: The converted path suitable for Docker volume mounting.
        """
        if platform.system() == "Windows":
            return path.replace("\\", "/") #.replace("C:", "C")
        return path

    @staticmethod
    def run_docker_on_folder(folder_path):
        """
        Runs the Docker container on the specified folder containing NIfTI files.

        Args:
            folder_path (str): The path to the folder containing NIfTI files.
        """
        try:
            docker_path = CalvinVBM.convert_path_for_docker(folder_path)
            print(f"Processing folder with Docker: {folder_path}")
            subprocess.run(["docker", "run", "--rm", "-v", f"{docker_path}:/data", "cat12:latest"], check=True)
            print(f"Finished processing: {folder_path}")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while processing {folder_path} with Docker: {e}")

    @staticmethod
    def submit_hpc_jobs(data_dir, docker_script_path, job_script_path):
        """
        Submits jobs to an HPC scheduler for processing each subdirectory 
        in the specified data directory.

        Args:
            data_dir (str): The path to the directory containing subdirectories with NIfTI files.
            docker_script_path (str): The path to the Docker run script.
            job_script_path (str): The path to the job submission script for HPC.
        """
        # Ensure the data directory exists
        if not os.path.isdir(data_dir):
            print(f"Data directory does not exist: {data_dir}")
            sys.exit(1)

        # Iterate over all subdirectories and submit a job for each
        for folder_name in os.listdir(data_dir):
            folder_path = os.path.join(data_dir, folder_name)
            if os.path.isdir(folder_path):
                CalvinVBM.submit_hpc_job(folder_path, docker_script_path, job_script_path)

    @staticmethod
    def submit_hpc_job(folder_path, docker_script_path, job_script_path):
        """
        Submits a single job to an HPC scheduler for processing a given folder.

        Args:
            folder_path (str): The path to the folder to process.
            docker_script_path (str): The path to the Docker run script.
            job_script_path (str): The path to the job submission script for HPC.
        """
        try:
            print(f"Submitting job for folder: {folder_path}")
            # Replace the following line with your HPC's job submission command
            subprocess.run([
                "bsub", "-J", "cat12_job", 
                "-o", "/path/to/output.txt", 
                "-e", "/path/to/error.txt", 
                "-q", "normal", 
                "-R", "rusage[mem=6000]", 
                "python", docker_script_path, folder_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while submitting {folder_path}: {e}")