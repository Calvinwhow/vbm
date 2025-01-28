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
    def pull_dockerfile(method='easyreg'):
        """
        Pulls a Dockerfile from the calvinwhow repository based on the method specified.

        Args:
            method (str): The method to determine which Dockerfile to pull ('cat12' for VBM or 'easyreg' for ER).
        """
        try:
            # Determine the tag to use based on the method
            if method == "cat12":
                tag = "vbm"
            elif method == "easyreg":
                tag = "er"
            else:
                raise ValueError(f"Unsupported method: {method}. Use 'cat12' or 'easyreg'.")

            # Pull the Dockerfile from the appropriate repository and tag
            print(f"Pulling Dockerfile with tag: {tag} from calvinwhow...")
            result = subprocess.run(
                ["docker", "pull", f"calvinwhow/{tag}:latest"],
                capture_output=True,
                text=True
            )

            # Output the result of the pull command
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args)

            print(f"Dockerfile for {method} successfully pulled.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while pulling the Dockerfile: {e}")
        except ValueError as ve:
            print(ve)


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
    def run_docker_with_script(data_dir_path, script_path, tag='cat12'):
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
                        
    @staticmethod
    def run_docker_container(method, data_dir, command_type, options):
        """
        Runs the Docker container with the specified method, command type, and options.

        Args:
            method (str): The method for the container ('cat12' or 'easyreg').
            data_dir (str): The absolute path to the data directory to mount in the container.
            command_type (str): The command to run inside the container ('easyreg-mri' or 'easywarp-mri').
            options (dict): Dictionary containing additional options for the command. 
                            Keys and values correspond to command-line arguments.

        Example Usage:
            options = {
                '--ref': '/root/data/reference_image.nii.gz',
                '--flo': '/root/data/floating_image.nii.gz',
                '--threads': '6'
            }
            CalvinVBM.run_docker_container(
                method='easyreg',
                data_dir='/path/to/your/data/dir',
                command_type='easyreg-mri',
                options=options
            )
        """
        try:
            # Validate method
            if method not in ["cat12", "easyreg"]:
                raise ValueError(f"Unsupported method: {method}. Use 'cat12' or 'easyreg'.")

            # Map method to Docker image
            docker_image = "vbm:latest" if method == "cat12" else "er:latest"

            # Validate command type
            if command_type not in ["easyreg-mri", "easywarp-mri"]:
                raise ValueError(f"Unsupported command type: {command_type}. Use 'easyreg-mri' or 'easywarp-mri'.")

            # Validate data directory
            if not os.path.isdir(data_dir):
                raise FileNotFoundError(f"Data directory not found: {data_dir}")

            # Construct volume mount argument
            data_dir_docker_path = CalvinVBM.convert_path_for_docker(data_dir)
            volume_mount = f"-v {data_dir_docker_path}:/root/data"

            # Construct command options
            command_options = " ".join([f"{key} {value}" for key, value in options.items()])

            # Construct and execute the Docker run command
            docker_command = [
                "docker", "run", "--rm", "-it",
                volume_mount,
                docker_image,
                command_type
            ] + command_options.split()

            print(f"Running Docker container with command: {' '.join(docker_command)}")
            result = subprocess.run(docker_command, capture_output=True, text=True)

            # Output the result
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args)

            print("Docker container executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running the Docker container: {e}")
        except ValueError as ve:
            print(ve)
        except FileNotFoundError as fe:
            print(fe)
