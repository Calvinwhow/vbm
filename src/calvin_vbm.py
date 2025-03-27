import os
import sys
import platform
import subprocess
import re
import xml.etree.ElementTree as ET


class CalvinVBM:
    """
    CalvinVBM is a class for orchestrating neuroimaging data processing using Docker.
    It facilitates building Docker images and running Docker containers on individual directories containing NIfTI files.
    """

    @staticmethod
    def build_docker_image(project_root_path=None, dockerfile_path="Dockerfile.cat12"):
        """
        Builds the Docker image from the specified Dockerfile.

        Args:
            project_root_path (str): The absolute path to the project root directory.
            dockerfile_path (str): The filename of the Dockerfile (default is 'Dockerfile.cat12').
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
            ["docker", "build", "-t", "cat12:latest", "-f", dockerfile_path, "."],
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
        """
        return path.replace("\\", "/")

    @staticmethod
    def run_docker_with_script(data_dir, script_path, container='cat12', verbose=True):
        """
        Runs a Docker container with the specified script mounted and executed.

        Args:
            data_dir (str): The path to the directory containing the NIfTI data.
            script_path (str): The path to the script to run inside the container.
        """
        # Convert paths for Docker compatibility
        data_dir = os.path.abspath(CalvinVBM.convert_path_for_docker(data_dir))

        script_path = os.path.abspath(CalvinVBM.convert_path_for_docker(script_path))
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)

        # Run the Docker container with mounted volumes
        print(f"Running Docker container with script: {script_name}")
        cmd = (
            f'docker run --rm '
            f'-v {data_dir}:/data '
            f'-v {script_dir}:/scripts '
            f'{container}:latest /scripts/{script_name}'
        )
        if verbose:
            print(cmd)
        
        subprocess.run(cmd, shell=True, check=True)
        print("Docker container executed successfully.")