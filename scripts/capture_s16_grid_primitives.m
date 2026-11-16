% Isolated grid primitives, independent of every scientific comparison input.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-grid-primitives');
if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_primitive';records=struct('native_version',version,'dpi',600,'paper_cm',[20 20]);
for direction={'vertical','horizontal'}
 f=figure;ax=axes;set(ax,'XScale','log','YScale','log','XLim',[1 1000],'YLim',[1 1000]);
 axis square;box on;
 set(ax,'XGrid','off','YGrid','off','XMinorGrid','off','YMinorGrid','off');
 if strcmp(direction{1},'vertical'),ax.XMinorGrid='on';else,ax.YMinorGrid='on';end
 guiPrint(f,['grid_' direction{1}]);close all;
end
fid=fopen('capture.json','w');fwrite(fid,jsonencode(records));fclose(fid);
disp('Independent grid primitives captured.');
