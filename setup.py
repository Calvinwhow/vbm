from setuptools import setup, find_packages

setup(
    name='atropos',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'nltools',
        'pandas',
        'numpy',
        'nibabel',
        'natsort',
        'nilearn',
        'scipy',
        'calvin-utils @ git+https://github.com/Calvinwhow/calvin_utils_project.git',
    ],
    author='Calvin William Howard',
    author_email='choward12@bwh.harvard.edu',
    description='A package for processing and scoring tissue segments using SPM/CAT12 and Python.',
    url='https://github.com/Calvinwhow/vbm.git',
)
