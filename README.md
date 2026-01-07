# Standalone VBM Processing Kit

This project provides a set of Jupyter notebooks for processing voxel-based morphometry (VBM) data with Atrophy PyPer.

## Dependencies

- Python 
  - Stable on Python 3.10.18

## Installation

To set up the environment for this project, follow these steps:

1. Clone this VBM repository
    ```
    git clone https://github.com/Calvinwhow/vbm.git
    ```

2. Move to installed directory 
    ```
    cd /git/clone/directory
    ```
    
3. Install
    ```
    pip install -e .
    ```

## Running the Notebooks

The project is orchestrated through a series of Jupyter notebooks. To process the data, run the notebooks in the following order:

1. **00_process_atrophy.ipynb**: Initial processing of atrophy data.
2. **01_preprocess_tissue_segments.ipynb**: Preprocessing of tissue segment data.
3. **02A_Z_atrophy_seed_derivation.ipynb**: Derivation of atrophy seeds (Part A). Requires control distribution.
4. **02B_W_atrophy_seed_derivation.ipynb**: Derivation of atrophy seeds (Part B). Requires control distribution.
5. **03_extract_atrophy_information.ipynb**: Extraction of atrophy information.
6. **04a_generate_Z_controls.ipynb**: Generates control distribution if you don't have one.

## Project Architecture

The following diagram illustrates the overall architecture and workflow of the project:
```
+-----------------------------+
|     00_process_atrophy      |
+------------+----------------+             +------------+----------------+
             | <-------(Optional)--------   |    04a_generate_Z_controls  |
             v                              +------------+----------------+
+------------+----------------+
| 01_preprocess_tissue_segments|
+------------+----------------+             +------------+----------------+
             | ---------(Optional)------>   |02B_W_atrophy_seed_derivation|
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