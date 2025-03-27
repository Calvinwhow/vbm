import subprocess
import platform

class CalvinVBM:
    @staticmethod
    def pull_docker_image(method='easyreg'):
        tag = {'cat12': 'vbm', 'easyreg': 'er'}.get(method)
        if not tag:
            raise ValueError("Method must be 'cat12' or 'easyreg'.")

        image_name = f"calvinwhow/{tag}:latest"
        subprocess.run(["docker", "pull", image_name], check=True)
        print(f"Successfully pulled {image_name}")

    @staticmethod
    def convert_path_for_docker(path):
        """
        Converts a Windows path to a Docker-compatible path (if running on Windows).
        """
        return path.replace("\\", "/")
        return path.replace('\\', '/') if platform.system() == "Windows" else path

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
    def run_container(method, data_dir, command_type, options):
        if method not in ["cat12", "easyreg"]:
            raise ValueError("Method must be 'cat12' or 'easyreg'.")

        docker_image = f"calvinwhow/{'vbm' if method == 'cat12' else 'er'}:latest"
        data_dir_docker = CalvinVBM.convert_path_for_docker(data_dir)

        docker_cmd = [
            "docker", "run", "--rm", "-it",
            "-v", f"{data_dir_docker}:/root/data",
            docker_image,
            command_type
        ]

        for key, val in options.items():
            docker_cmd.extend([key, val])

        subprocess.run(docker_cmd, check=True)
        print("Docker container ran successfully.")


def format_easyreg_options(file_target, ref_target="MNI152_T1_2mm_brain"):
    base = "/root/data"
    return {
        '--ref': f'{base}/{ref_target}.nii',
        '--flo': f'{base}/{file_target}.nii',
        '--ref_seg': f'{base}/derivatives/{ref_target}_seg.nii',
        '--flo_seg': f'{base}/derivatives/{file_target}_seg.nii',
        '--flo_reg': f'{base}/derivatives/{file_target}_reg.nii',
        '--fwd_field': f'{base}/derivatives/forward_field.nii',
        '--bak_field': f'{base}/derivatives/inverse_field.nii',
        '--threads': '4'
    }

# Example usage:
if __name__ == "__main__":
    method = 'easyreg'
    data_dir = '/absolute/path/to/your/data'
    command_type = 'easyreg-mri'

    CalvinVBM.pull_docker_image(method)

    options = format_easyreg_options(file_target='demo_pt')

    CalvinVBM.run_container(method, data_dir, command_type, options)
