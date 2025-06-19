import os 
import subprocess
import platform

class CalvinVBM:
    def __init__(self, container='cat12'):
        """
        Initializes the object with a specified container type.
        Args:
            container (str): The container type to use. Defaults to 'cat12'.
        """
        
        self.container = container
        self.tags = {'cat12': 'cat12:latest', 'easyreg': 'er:latest'}
        self.tag = self.tags.get(container, None)
                
    def push_docker_image(self, image_name):
        """Pushes the Docker image to the Docker Hub repository."""
        subprocess.run(["docker", "push", image_name], check=True)
        print(f"Successfully pushed {image_name} to Docker Hub")

    def build_docker_image(self, dockerfile_path):
        """Builds the Docker image based on the specified container type."""
        if not self.tag:
            raise ValueError("Method must be 'cat12' or 'easyreg'.")
        image_name = f"calvinwhow/{self.tag}"
        subprocess.run(["docker", "build", "-t", image_name, "-f", dockerfile_path, "."], check=True)
        print(f"Successfully built {image_name}")
        self.push_docker_image(image_name)
        print(f"Image {image_name} pushed to Docker Hub")

    def pull_docker_image(self):
        if not self.tag:
            raise ValueError("Method must be 'cat12' or 'easyreg'.")
        image_name = f"calvinwhow/{self.tag}"
        subprocess.run(["docker", "pull", image_name], check=True)
        print(f"Successfully pulled {image_name}")

    def convert_path_for_docker(self, path):
        """Converts a Windows path to a Docker-compatible path (if running on Windows)."""
        return path.replace('\\', '/') if platform.system() == "Windows" else path

    def run_docker_with_script(self, data_dir, script_path, verbose=True):
        """Run a Docker container and execute the specified script.

        Args:
            data_dir (str): Directory with NIfTI data.
            script_path (str): Script to execute inside the container.
        """
        script_path = os.path.abspath(CalvinVBM.convert_path_for_docker(script_path))
        data_dir = os.path.abspath(CalvinVBM.convert_path_for_docker(data_dir))
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)

        # Run the Docker container with mounted volumes
        print(f"Running Docker container with script: {script_name}")
        cmd = (
            f'docker run --rm '
            f'-v {data_dir}:/data '
            f'-v {script_dir}:/scripts '
            f'{self.tag} /scripts/{script_name}'
        )
        if verbose:
            print(cmd)
        subprocess.run(cmd, shell=True, check=True)
