% Additional genuine calls for NMS boundaries, palettes and wavelet plot arrays.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
set(groot,'DefaultFigureVisible','off');global sTag;sTag='_details';
details=struct;
for name={'morlet','mexican'}
 name=name{1};folder=fullfile(root,'tests/reference/sprint14/native',['details_' name]);
 if ~exist(folder,'dir'),mkdir(folder);end
 cd(folder);imwrite(imread(fullfile(root,'tests/reference/sprint14/native',name,'FracPaQ2D_wavelet_traces.png')),'FracPaQ2D_wavelet_traces.png');
 guiFracPaQ2Dwavelet2(2,[.5 1],45,strcmp(name,'morlet'),[0 0 1]);
 images=findall(groot,'Type','image');
 for j=1:numel(images)
  ax=images(j).Parent;heading=ax.Title.String;
  if iscell(heading),heading=strjoin(heading);end
  if contains(heading,'WC map'),details.(name).wc=images(j).CData;
  else,details.(name).binary=images(j).CData;end
 end
 close all;
end
save(fullfile(root,'tests/reference/sprint14/native/gui_arrays.mat'),'details');
cd(fullfile(root,'tests/reference/sprint15/native'));
inputs={uint8(repmat(0:16:240,16,1)),uint8(zeros(17,19)),uint8(zeros(7,9))};
inputs{2}(4:14,5:15)=255;inputs{3}(4,5)=255;edges=cell(size(inputs));
for j=1:numel(inputs),edges{j}=edge(inputs{j});end
figure;imagesc(0);caxis([-2 5]);balance=cmocean('balance','pivot',1,7);close all;
bone256=bone(256);
angles=[0 10 20 90 180 270 350];
figure;roseLinear(angles,30,0,0,[0 0 1]);p=findall(gcf,'Type','patch');
linear_x=p.XData;linear_y=p.YData;close all;
historical_counts=histc(angles,15:30:345);
save('details_arrays.mat','inputs','edges','balance','bone256','linear_x','linear_y','historical_counts');
disp('Additional native wavelet/utility arrays saved.');
