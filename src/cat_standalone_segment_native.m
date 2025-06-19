matlabbatch{1}.spm.tools.cat.estwrite.data = {'<UNDEFINED>'};

% CAT12 defaults with minor customizations:
matlabbatch{1}.spm.tools.cat.estwrite.nproc = 0; % automatic threads
matlabbatch{1}.spm.tools.cat.estwrite.opts.tpm = {'/opt/spm/spm12_mcr/home/gaser/gaser/spm/spm12/tpm/TPM.nii'};
matlabbatch{1}.spm.tools.cat.estwrite.opts.affreg = 'mni';
matlabbatch{1}.spm.tools.cat.estwrite.opts.biasstr = 0.5;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.APP = 1070;
matlabbatch{1}.spm.tools.cat.estwrite.extopts.darteltpm = {'/opt/spm/spm12_mcr/home/gaser/gaser/spm/spm12/toolbox/cat12/templates_MNI152NLin2009cAsym/Template_1_Dartel.nii'};
matlabbatch{1}.spm.tools.cat.estwrite.extopts.LASstr = 0.5;

% Native space outputs (no normalization yet)
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.native = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.GM.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.native = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.WM.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.CSF.native = 1;
matlabbatch{1}.spm.tools.cat.estwrite.output.CSF.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.TPMC.native = 0; % Native TPM probability maps
matlabbatch{1}.spm.tools.cat.estwrite.output.TPMC.warped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.label.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.surface = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.bias.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.las.native = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.jacobianwarped = 0;
matlabbatch{1}.spm.tools.cat.estwrite.output.warps = [1 1];