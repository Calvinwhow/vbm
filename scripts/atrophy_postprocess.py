"""Postprocessing: thresholded maps keep only atrophy beyond a z cut-off; every other voxel becomes 0."""
from typing import Dict

import pandas as pd


def threshold_maps(zscores: Dict[str, pd.DataFrame], tissue_z_cutoff: float = 2, composite_z_cutoff: float = 0) -> Dict[str, pd.DataFrame]:
    """Keep z > tissue_z_cutoff for each tissue and z > composite_z_cutoff for the composite; zero the rest."""
    cutoffs = {name: composite_z_cutoff if name == "composite" else tissue_z_cutoff for name in zscores}
    return {name: frame.where(frame > cutoffs[name], 0) for name, frame in zscores.items()}
