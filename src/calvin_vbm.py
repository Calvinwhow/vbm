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

        Args:
            path (str): The original file system path.

        Returns:
            str: The converted path suitable for Docker volume mounting.
        """
        if platform.system() == "Windows":
            return path.replace("\\", "/")
        return path

    @staticmethod
    def run_docker_with_script(data_dir_path, script_path):
        """
        Runs a Docker container with the specified script mounted and executed.

        Args:
            data_dir_path (str): The path to the directory containing the NIfTI data.
            script_path (str): The path to the script to run inside the container.
        """
        try:
            # Convert paths for Docker compatibility
            data_dir_docker_path = CalvinVBM.convert_path_for_docker(data_dir_path)
            script_docker_path = CalvinVBM.convert_path_for_docker(os.path.dirname(script_path))
            script_filename = os.path.basename(script_path)

            # Check if the Docker image exists; if not, build it
            image_check = subprocess.run(["docker", "images", "-q", "cat12:latest"], capture_output=True, text=True)
            if not image_check.stdout.strip():
                raise FileExistsError("Docker image not found. You must build or pull the image first.")

            # Run the Docker container with mounted volumes
            print(f"Running Docker container with script: {script_filename}")
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{data_dir_docker_path}:/data",
                "-v", f"{script_docker_path}:/scripts",
                "cat12:latest", f"/scripts/{script_filename}"
            ], check=True)
            print("Docker container executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running Docker: {e}")

    @staticmethod
    def extract_tiv_from_xml(bids_root):
        """
        Extracts TIV from CAT12 .xml report files and writes them to .tiv files.

        Args:
            bids_root (str): The root directory of the BIDS dataset.
        """
        for root, dirs, files in os.walk(bids_root):
            for file in files:
                if file.endswith(".xml") and "catROI_mwp2" in file:
                    xml_path = os.path.join(root, file)
                    try:
                        # Parse the XML file
                        tree = ET.parse(xml_path)
                        root_element = tree.getroot()

                        # Find the <vol_TIV> element under <subjectratings>
                        vol_tiv_element = root_element.find(".//subjectratings/vol_TIV")
                        if vol_tiv_element is not None:
                            tiv_value = vol_tiv_element.text
                            print(f"Extracted TIV: {tiv_value} from {xml_path}")

                            # Generate the .tiv filename
                            tiv_filename = os.path.splitext(file)[0] + ".tiv"
                            tiv_file_path = os.path.join(root, tiv_filename)

                            # Write the TIV value to a .tiv file
                            with open(tiv_file_path, 'w', encoding='utf-8') as tiv_file:
                                tiv_file.write(tiv_value + "\n")
                            print(f"TIV value written to: {tiv_file_path}")
                        else:
                            print(f"Could not find <vol_TIV> in {xml_path}")
                    except Exception as e:
                        print(f"Error processing {xml_path}: {e}")
