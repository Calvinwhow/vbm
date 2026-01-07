import nibabel as nib
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
import os
import datetime
from matplotlib import cm
from PIL import Image, ImageDraw, ImageFont   # add this import once

class NiftiToDicomV2:
    '''
    To trigger RGB writeouts, provide the original image path alongside the nifti to dicom path. 
    '''
    def __init__(self, nii_path: str, output_dir: str, orig_img_path: str = None, example_dcm_path: str = None):
        self.nii_path = nii_path
        self.output_dir = output_dir
        self.orig_img_path = orig_img_path
        os.makedirs(self.output_dir, exist_ok=True)
        self._get_basic_metadata()
        self._get_identifier_metadata(example_dcm_path)
    
    ### Metadata Utils ###
    def _get_basic_metadata(self):
        self.date = datetime.date.today().strftime("%Y%m%d")
        self.time = datetime.datetime.now().strftime("%H%M%S")
        self.instance_id = pydicom.uid.generate_uid()
        self.series_id = pydicom.uid.generate_uid()
        self.ref_id = pydicom.uid.generate_uid()
        
    def _get_identifier_metadata(self, example_dcm_path=None):
        """
        Accepts an example DICOM to copy metadata from or sets standard values
        Sets properties of the class to handle the identifier fields of the metadata
        """
        if example_dcm_path is not None: 
            dcm = pydicom.dcmread(example_dcm_path)
        else:
            dcm = None
        self.PatientName = dcm.PatientName if dcm is not None else "Anonymized^Patient"
        self.PatientID = dcm.PatientID if dcm is not None else "000000"
        self.StudyID = dcm.StudyID if dcm is not None else "1"
        self.AccessionNumber = dcm.AccessionNumber if dcm is not None else "000000"
        self.StudyInstanceUID = dcm.StudyInstanceUID if dcm is not None else self.instance_id
        self.SeriesInstanceUID = dcm.SeriesInstanceUID if dcm is not None else self.series_id
        self.FrameOfReferenceUID = dcm.FrameOfReferenceUID if dcm is not None else self.ref_id
        self.ImageType = "DERIVED\\SECONDARY"
    
    def _get_dcm_slice_metadata(self):
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.MRImageStorage
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = "1.2.826.0.1.3680043.9999.1"
        file_meta.ImplementationVersionName = "13378008135"
        return file_meta
    
    def _get_metadata_values(self, ds):
        '''Get metadata that stays constant for every file'''
        # Identifier Info
        ds.PatientName = self.PatientName
        ds.PatientID = self.PatientID
        ds.StudyID = self.StudyID            # (0020,0010) required by some viewers
        ds.AccessionNumber = self.AccessionNumber # (0008, 0050)
        ds.StudyInstanceUID = self.StudyInstanceUID # (0020,000D)
        ds.SeriesInstanceUID = self.SeriesInstanceUID # (0020,000E)
        ds.FrameOfReferenceUID = self.FrameOfReferenceUID # (0020,0052)
        ds.ImageType = self.ImageType
        # Study/Series Descriptions
        ds.Modality = "MR" # (0008,0060)
        ds.Manufacturer = "PythonConverter" # (0008,0070)
        ds.SeriesNumber = 1 # (0020,0011)
        ds.SeriesDescription = "Calvin Howard Burned DICOM" # (0008,103E)
        ds.ProtocolName = "Calvin Howard Burned DICOM"
        ds.StudyDescription = "MR Brain"
        ds.StudyDate = self.date # (0008,0020)
        ds.StudyTime = self.time # (0008,0030)
        ds.ContentDate = self.date # (0008,0023)
        ds.ContentTime = self.time # (0008,0033)
        ds.SeriesTime = self.time
        ds.SeriesDate = self.date           
        return ds
        
    ### Voxel Normalization Tools ###
    def _to_uint8(self, x):
        x = (x - x.min()) / (x.ptp())
        return (x * 255).astype(np.uint8)

    def _normalize_to_dicom(self, data: np.ndarray) -> np.ndarray:
        data_min, data_max = data.min(), data.max()
        normalized = (data - data_min) / (data_max - data_min)
        return (normalized * 4095).astype(np.uint16)
    
    ### DICOM Writing Utils ###
    def _append_colorbar(self, rgb_slice, vmin, vmax, cmap_name = 'viridis', bar_px = 40):
        """
        Add a vertical colour bar (vmax at top to vmin at bottom) with text.
        Text burned: top = vmax, middle = 'atrophy', bottom = vmin
        """
        h = rgb_slice.shape[0]

        # ----- gradient bar (H, bar_px, 3 uint8) -----
        grad = np.linspace(1, 0, h, dtype=np.float32)[:, None]          # 0 -> 1 top -> bot
        grad = np.repeat(grad, bar_px, axis=1)              # duplicate bar to be pixels=bar_pix wide
        bar  = (cm.get_cmap(cmap_name)(grad)[..., :3] * 255).astype(np.uint8) #converts 0-1 values to rgb triplet, multiplied by 255 and cast to uint8 for image data

        # ----- convert bar to pillow image -----
        img  = Image.fromarray(bar) # convert to pillow image to write text on bar
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        
        # ----- annotate colour bar -----
        draw.text((2, 0),               f'{vmax:.0f}', fill=(1, 1, 1), font=font) #add vmax 2 pix from left, 0 px from top, in white, default font.
        draw.text((2, (h//4) *1),       'more\nsevere', fill=(1, 1, 1), font=font),#label for understanding
        draw.text((2, h//2),            'atrophy\n(z)', fill=(1, 1, 1), font=font),#label for understanding
        draw.text((2, (h//4) *3),       'less\nsevere', fill=(1, 1, 1), font=font),#label for understanding
        draw.text((2, h-15),            f'{vmin:.0f}', fill=(1, 1, 1), font=font) #add min 2 pix from left, 15 px from bot, in white, default font.

        bar  = np.array(img, dtype=np.uint8) # Convert image to a numpy array
        return np.concatenate((rgb_slice, bar), axis=1) #stick bar on the right of the img_slice data.   arr shape = (h, w, 3)
    
    def _write_black_and_white(self, data, affine):
        '''Normalize data to 0-4095 (12-bit typical DICOM CT range)'''
        data_normalized = self._normalize_to_dicom(data)
        for slice_idx in range(data_normalized.shape[2]):
            slice_data = data_normalized[:, :, slice_idx] # rows are ant-post, cols are top-bot, and slice are left
            self._write_slice(slice_data, slice_idx, affine, rgb=False)
            
    def _write_coloured(self, data, affine, cmap='viridis', alpha=0.6, t=0.5):
        '''Write a coloured image. Assumes any overlay values are already thresholded.
        Assumption:  every nonzero voxel in burned-in image IS the mask.
        No extra thresholding/logic required.
        
        t: Threshold to prevent noise.
        '''
        # ---------- derive mask & prepare uint8 data ---------------------------
        t1_vol   = nib.load(self.orig_img_path).get_fdata()
        overlay  = data - t1_vol          
        mask     = overlay > t                 # boolean mask

        gray_u8  = self._to_uint8(data)   # greyscale base 0‑255
        over_u8  = self._to_uint8(overlay)  # 0‑255 drives the colour
        rgb_ovl  = (cm.get_cmap(cmap)(over_u8 / 255)[..., :3] * 255).astype(np.uint8)
        
        # ---------- legend -------------------------------
        vmin, vmax = overlay[mask].min(), overlay[mask].max()     # scale for legend
        # ---------- blend & write slice‑by‑slice -------------------------------
        for k in range(gray_u8.shape[2]):
            rgb = np.repeat(gray_u8[:, :, k, None], 3, -1)   # H×W×3 uint8
            m   = mask[:, :, k]
            if m.any():                                      # skip empty slices
                rgb[m] = ((1 - alpha) * rgb[m] + alpha * rgb_ovl[:, :, k][m]).astype(np.uint8)
            rgb = self._append_colorbar(rgb, vmin, vmax, cmap) # add colour bar
            self._write_slice(rgb, k, affine, rgb=True)      # same writer as before

    def convert(self):
        '''Writes out black and white dicom if an overlay is provided.'''
        nii = nib.load(self.nii_path)
        data = nii.get_fdata()
        affine = nii.affine
        
        if self.orig_img_path is None:       
            self._write_black_and_white(data, affine)
        else:
            self._write_coloured(data, affine)
   
   ### DICOM Slice Writing ###                      
    def _write_slice(self, slice_data: np.ndarray, slice_idx: int, affine: np.ndarray, rgb: bool=False):        
        ### Dicom Information ###
        filename = os.path.join(self.output_dir, f'slice_{slice_idx:04d}.dcm')
        
        # Get Metadata Specific to this DICOM file
        file_meta = self._get_dcm_slice_metadata()
        
        # Get DICOM Metadata That is General Across all Similar Files
        ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
        ds = self._get_metadata_values(ds)
        
        # file‑meta (group 0002)
        ds.SOPClassUID     = file_meta.MediaStorageSOPClassUID  # (0008,0016)
        ds.SOPInstanceUID  = file_meta.MediaStorageSOPInstanceUID # (0008,0018)
        
        # instance identifier data
        ds.InstanceNumber  = slice_idx + 1              # (0020,0013)
        
        ### Positional Data ###
        # Convert RAS (nifti) affine to LPS (dicom)
        ras2lps = np.diag([-1, -1, 1])            # flip X & Y to LPS space

        # voxel‑axis matrix and slice origin in LPS
        M   = ras2lps @ affine[:3, :3]
        ipp = ras2lps @ (affine[:3, 3] + slice_idx * affine[:3, 2])

        # direction cosines (unit vectors)
        row = M[:, 0] / np.linalg.norm(M[:, 0])
        col = M[:, 1] / np.linalg.norm(M[:, 1])
        if np.dot(np.cross(row, col), M[:, 2]) < 0:
            col = -col
        ds.Rows, ds.Columns        = slice_data.shape[:2]
        ds.PixelSpacing            = [f"{np.linalg.norm(M[:,0]):.6f}",
                                    f"{np.linalg.norm(M[:,1]):.6f}"]
        ds.SliceThickness          = f"{np.linalg.norm(M[:,2]):.6f}"
        ds.SpacingBetweenSlices    = ds.SliceThickness
        ds.ImagePositionPatient    = [f"{x:.6f}" for x in ipp]
        ds.ImageOrientationPatient = [f"{x:.6f}" for x in (*col, *row)]
        ds.SliceLocation           = f"{ipp[2]:.6f}"
        
        ### Colouring and Pixel Data ###
        # Format pixels for colour (atrophy burn-in) vs monochrone (surgical targets)
        if rgb:
            ds.PhotometricInterpretation = "RGB"
            ds.SamplesPerPixel = 3
            ds.PlanarConfiguration = 0
            ds.BitsAllocated = ds.BitsStored = 8
            ds.HighBit = 7
            ds.PixelRepresentation = 0
            
            slice_data = np.ascontiguousarray(
                slice_data.astype(np.uint8)
            )
        else:
            ds.PhotometricInterpretation = "MONOCHROME2"  # (0028,0004)
            ds.SamplesPerPixel           = 1              # (0028,0002)
            ds.BitsAllocated             = 16             # (0028,0100)
            ds.BitsStored                = 16             # (0028,0101)
            ds.HighBit                   = 15             # (0028,0102)
            ds.PixelRepresentation       = 0              # (0028,0103)
            ds.RescaleIntercept          = 0              # (0028,1052)
            ds.RescaleSlope              = 1              # (0028,1053)
        
        # Commit pixels to metadata
        ds.PixelData = slice_data.tobytes()           # (7FE0,0010) 
        
        # Finalize and save
        ds.save_as(filename)