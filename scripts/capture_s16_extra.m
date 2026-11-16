% Remaining figure types and renderer properties, unchanged source functions.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-extra');if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_extra';native_version=version;calls=struct;
figure;
try
 traces=guiFracPaQ2Dimage(fullfile(root,'tests/fixtures/images/tensor_network.tif'),0,1000,.33,5,3,gca);
 calls.hough=struct('success',true);fig=gcf;axs=findall(fig,'Type','axes');layout=cell(1,numel(axs));
 for i=1:numel(axs)
  ax=axs(i);layout{i}=struct('title',{ax.Title.String},'position',ax.Position,'view',ax.View,...
   'camera_position',ax.CameraPosition,'camera_target',ax.CameraTarget,'camera_up',ax.CameraUpVector,...
   'camera_angle',ax.CameraViewAngle,'projection',ax.Projection,'DAR',ax.DataAspectRatio,'PBAR',ax.PlotBoxAspectRatio,...
   'xlim',ax.XLim,'ylim',ax.YLim,'zlim',ax.ZLim,'xtick',ax.XTick,'ytick',ax.YTick,'ztick',ax.ZTick);
 end
 save('hough_layout.mat','layout','native_version','-v7');
catch err,calls.hough=struct('success',false,'error',err.message,'stack',err.stack);end
close all;
bridge=jsondecode(fileread(fullfile(root,'tests/reference/sprint16/final/inputs/multicolour/bridge.json')));
try
 alltraces=[];
 for i=1:numel(bridge.groups)
  g=bridge.groups(i);figure;part=guiFracPaQ2Dlist(fullfile(root,g.path),0,gca,g.rgb');
  if isempty(alltraces),alltraces=part;else,alltraces=[alltraces part];end;close all;
 end
 guiFracPaQ2Dtracemap(alltraces,0,0,true,false,false,[0 0 1],true,true,false,false,...
 false,false,false,100,50,0,false,false,0,0,.6);
 calls.multicolour=struct('success',true,'scope',bridge.scope);
 save('multicolour_geometry.mat','alltraces','bridge','native_version','-v7');
catch err,calls.multicolour=struct('success',false,'error',err.message,'stack',err.stack);end
close all;
f=figure;ax=axes;loglog([7 20 50 100 300 2000],[200 100 30 10 3 1],'s','LineWidth',1,'MarkerFaceColor','b');
axis square;grid on;xlim([6.68 2262]);ylim([.1 256]);xlabel('Trace length, pixels');ylabel('Frequency, n(L)');title({'Log grid probe';''});
guiPrint(f,'log_grid');print(f,'log_grid.svg','-dsvg');close all;
fid=fopen('calls.json','w');fwrite(fid,jsonencode(struct('native_version',native_version,'calls',calls)));fclose(fid);
disp('Additional source figures captured.');
