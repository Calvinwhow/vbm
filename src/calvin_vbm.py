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
        return path.replace('\\', '/') if platform.system() == "Windows" else path

    @staticmethod
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
