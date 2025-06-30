# Standalone VBM Processing Kit

This project provides a set of Jupyter notebooks for processing voxel-based morphometry (VBM) data with Atrophy PyPer.

## Dependencies

- **Calvin Utils**: Utility functions required for this project.
  - Repository: [Calvin Utils](https://github.com/Calvinwhow/calvin_utils_project.git)

## Installation

To set up the environment for this project, follow these steps:

1. **Install Calvin Utils**:
    ```sh
    pip install git+https://github.com/Calvinwhow/calvin_utils_project.git
    ```

2. **Clone this VBM repository**:
    ```sh
    git clone https://github.com/Calvinwhow/vbm.git
    ```

## Running the Notebooks

The project is orchestrated through a series of Jupyter notebooks. To process the data, run the notebooks in the following order:

1. **00_process_atrophy.ipynb**: Initial processing of atrophy data.
2. **01_preprocess_tissue_segments.ipynb**: Preprocessing of tissue segment data.
3. **02A_Z_atrophy_seed_derivation.ipynb**: Derivation of atrophy seeds (Part A).
4. **02B_W_atrophy_seed_derivation.ipynb**: Derivation of atrophy seeds (Part B).
5. **03_extract_atrophy_information.ipynb**: Extraction of atrophy information.

### Notes

- If you have already extracted segments, you can start directly with notebook `01_preprocess_tissue_segments.ipynb`.

## Project Architecture

The following diagram illustrates the overall architecture and workflow of the project:
```
+-----------------------------+
|     00_process_atrophy      |
+------------+----------------+
             |
             v
+------------+----------------+
| 01_preprocess_tissue_segments|
+------------+----------------+             +------------+----------------+
             | ------------------------->   |02B_W_atrophy_seed_derivation|
             v                              +------------+----------------+
+------------+----------------+                          |
|02A_Z_atrophy_seed_derivation|                          |
+------------+----------------+                          |
             | <------------------------------------------ 
             v
+------------+----------------+
|03_extract_atrophy_information|
+-----------------------------+
```