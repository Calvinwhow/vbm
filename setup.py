from setuptools import setup, find_packages

setup(
    name='calvin_vbm',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['./generate_setup.py', './calvin_utils/__init__.py', './calvin_utils/nifti_utils/__init__.py', './calvin_utils/nifti_utils/matrix_utilities.py', './calvin_utils/nifti_utils/generate_nifti.py', './calvin_utils/file_utils/__init__.py', './calvin_utils/file_utils/dataframe_utilities.py', './calvin_utils/file_utils/import_matrices.py', './rois/__init__.py', './containers/__init__.py', './01_preprocess_tissue_segments.ipynb', './02_atrophy_seed_derivation.ipynb', './03_extract_atrophy_information.ipynb', './00_process_atrophy.ipynb', './w_score_tissue_segments/01_preprocess_tissue_segments.ipynb', './w_score_tissue_segments/02_atrophy_seed_derivation.ipynb']},
    install_requires=['nltools', 'pandas', 'numpy', 'warnings', 'nibabel', 'natsort', 're', 'nilearn', 'os', 'nimlab', 'glob', 'calvin_utils', 'scipy'],
    author='Calvin William Howard',
    author_email='choward12@bwh.harvard.edu',
    description='This package uses spm/cat12 in Docker files I have created to process and extract tissue segments. It then uses python perform z-scoring and w-scoring of those segments. This expects you have nimlab installed.',
    url='https://github.com/Calvinwhow/vbm.git',
)
