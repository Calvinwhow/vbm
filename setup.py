from setuptools import setup, find_packages

setup(
    name='Atrophy-PyPer',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'numpy',
        'pandas',
        'scipy',
        'jax',
        'forestplot',
        'tqdm',
        'tensorly',
        'statsmodels',
        'nilearn',
        'natsort',
        'seaborn',
        'calvin-utils @ git+https://github.com/Calvinwhow/calvin_utils_project.git'
    ],
    author='Calvin William Howard',
    author_email='choward12@bwh.harvard.edu',
    description='This package uses spm/cat12 in Docker files I have created to process and extract tissue segments. It then uses python perform z-scoring and w-scoring of those segments. This expects you have nimlab installed.',
    url='https://github.com/Calvinwhow/vbm.git',
)
