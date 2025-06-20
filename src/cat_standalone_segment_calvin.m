% Batch file for CAT12 segmentation for SPM12/CAT12 standalone installation
%
%_______________________________________________________________________
% $Id$

% first undefined data field, that will be dynamically replaced by cat_standalone.sh
matlabbatch{1}.spm.tools.cat.estwrite.data = '<UNDEFINED>';

% Entry for choosing TPM
% Remove comments and edit entry if you would like to change the parameter.
% Otherwise the default value from cat_defaults.m is used.
% Or use 1st parameter field, that will be dynamically replaced by cat_standalone.sh
%matlabbatch{1}.spm.tools.cat.estwrite.opts.tpm = '<UNDEFINED>';

% Entry for choosing shooting template
% Remove comments and edit entry if you would like to change the parameter.
% Otherwise the default value from cat_defaults.m is used.
% Or use 2nd parameter field, that will be dynamically replaced by cat_standalone.sh
%matlabbatch{1}.spm.tools.cat.estwrite.extopts.registration.regmethod.shooting.shootingtpm = '<UNDEFINED>';

% Strength of Shooting registration: 0 - Dartel, eps (fast), 0.5 (default) to 1 (accurate) optimized Shooting, 4 - default Shooting; default 0.5
matlabbatch{1}.spm.tools.cat.estwrite.extopts.registration.regmethod.shooting.regstr = 0;

% voxel size for normalized data (EXPERIMENTAL: inf - use Tempate values)
matlabbatch{1}.spm.tools.cat.estwrite.extopts.registration.vox = 2;

% additional bounding box
matlabbatch{1}.spm.tools.cat.estwrite.extopts.registration.bb = 12;

% Affine regularisation (SPM12 default = mni) - '';'mni';'eastern';'subj';'none';'rigid'
matlabbatch{1}.spm.tools.cat.estwrite.opts.affreg = 'mni';    

% Strength of the bias correction that controls the biasreg and biasfwhm parameter (CAT only!)
% 0 - use SPM parameter; eps - ultralight, 0.25 - light, 0.5 - medium, 0.75 - strong, and 1 - heavy corrections
% job.opts.biasreg	= min(  10 , max(  0 , 10^-(job.opts.biasstr*2 + 2) ));
% job.opts.biasfwhm	= min( inf , max( 30 , 30 + 60*job.opts.biasstr ));  
matlabbatch{1}.spm.tools.cat.estwrite.opts.biasstr = 0.5;     

% Affine PreProcessing (APP) with rough bias correction and brain extraction for special anatomies (nonhuman/neonates) 
% 0 - none; 1070 - default; [1 - light; 2 - full; 1144 - update of 1070, 5 - animal (no affreg)]
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.APP = 1070;

% Strength of the local adaptation: 0 to 1; default 0.5
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.LASstr = 0.5;

% Strength of the noise correction: 0 to 1; 0 - no filter, -Inf - auto, 1 - full, 2 - ISARNLM (else SANLM), default -Inf
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.NCstr = -Inf;

% Strength of skull-stripping: 0 - SPM approach; eps to 1  - gcut; 2 - new APRG approach; -1 - no skull-stripping (already skull-stripped); default = 2
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.gcutstr = 0;

% Strength of the cleanup process: 0 to 1; default 0.5
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.cleanupstr = 0.5;

% resolution handling: 'native','fixed','best', 'optimal'
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.restypes.optimal = [1 0.3];

% use center-of-mass approach for estimating origin
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.setCOM = 1;

% modify affine scaling
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.affmod = 0;

% use k-means AMAP approach or SPM segmentation for initial segmentation
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.spm_kamap = 0;

% Correction of WM hyperintensities: 0 - no correction, 1 - only for Dartel/Shooting
% 2 - also correct segmentation (to WM), 3 - handle as separate class; default 1
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.WMHC = 2;

% Stroke lesion correction (SLC): 0 - no correction, 1 - handling of manual lesion that have to be set to zero!
% 2 - automatic lesion detection (in development)
matlabbatch{1}.spm.tools.cat.estwrite.extopts.segmentation.SLC = 0;

% surface options
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.pbtres = 0.5;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.pbtmethod = 'pbt2x';
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.reduce_mesh = 1;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.scale_cortex = 0.7;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.add_parahipp = 0.1;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.close_parahipp = 0;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.surface.SRP = 22;

% set this to 1 for skipping preprocessing if already processed data exist
matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.lazy = 1;

% catch errors: 0 - stop with error (default); 1 - catch preprocessing errors (requires MATLAB 2008 or higher); 
matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.ignoreErrors = 1;

% verbose output: 1 - default; 2 - details; 3 - write debugging files
matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.verb = 2;

% display and print out pdf-file of results: 0 - off, 2 - volume only, 2 - volume and surface (default)
matlabbatch{1}.spm.tools.cat.estwrite.extopts.admin.print = 2;

% surface and thickness creation:   0 - no (default), 1 - lh+rh, 2 - lh+rh+cerebellum, 
% 3 - lh, 4 - rh, 5 - lh+rh (fast, no registration, only for quick quality check and not for analysis),
% 6 - lh+rh+cerebellum (fast, no registration, only for quick quality check and not for analysis)
% 9 - thickness only (for ROI analysis, experimental!)
% +10 to estimate WM and CSF width/depth/thickness (experimental!)
matlabbatch{1}.spm.tools.cat.estwrite.output.surface = 0;       

% BIDS output
matlabbatch{1}.spm.tools.cat.estwrite.output.BIDS.BIDSno = 1;
                                                            
% define here volume atlases
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.neuromorphometrics = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.lpba40 = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.cobra = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.hammers = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.ibsr = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.aal3 = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.mori = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.thalamus = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.anatomy3 = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.julichbrain = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.Schaefer2018_100Parcels_17Networks_order = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.Schaefer2018_200Parcels_17Networks_order = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.Schaefer2018_400Parcels_17Networks_order = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.Schaefer2018_600Parcels_17Networks_order = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.ROImenu.atlases.ownatlas = {''};

% Writing options (see cat_defaults for the description of parameters)
%   native    0/1     (none/yes)
%   warped    0/1     (none/yes)
%   mod       0/1/2/3 (none/affine+nonlinear/nonlinear only/both)
%   dartel    0/1/2/3 (none/rigid/affine/both)

% GM/WM/CSF/WMH
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.dartel = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.dartel = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.CSF.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.CSF.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.CSF.mod = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.CSF.dartel = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.WMH.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WMH.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WMH.mod = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WMH.dartel = 0;

% stroke lesion tissue maps (only for opt.extopts.SLC>0) - in development
matlabbatch{1}.spm.tools.cat.estwrite.output.SL.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.SL.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.SL.mod = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.SL.dartel = 0;

% Tissue classes 4-6 to create own TPMs
matlabbatch{1}.spm.tools.cat.estwrite.output.TPMC.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.TPMC.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.TPMC.mod = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.TPMC.dartel = 0;

% atlas maps (for evaluation)
matlabbatch{1}.spm.tools.cat.estwrite.output.atlas.native = 0;

% label 
% background=0, CSF=1, GM=2, WM=3, WMH=4 (if opt.extopts.WMHC==3), SL=1.5 (if opt.extopts.SLC>0)
matlabbatch{1}.spm.tools.cat.estwrite.output.label.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.label.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.label.dartel = 0;

% bias and noise corrected, global intensity normalized
matlabbatch{1}.spm.tools.cat.estwrite.output.bias.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.bias.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.bias.dartel = 0;

% bias and noise corrected, (locally - if LAS>0) intensity normalized
matlabbatch{1}.spm.tools.cat.estwrite.output.las.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.las.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.las.dartel = 0;

% jacobian determinant 0/1 (none/yes)
matlabbatch{1}.spm.tools.cat.estwrite.output.jacobianwarped = 0;

% deformations, order is [forward inverse]
matlabbatch{1}.spm.tools.cat.estwrite.output.warps = [1 1];

