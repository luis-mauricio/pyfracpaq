% Data-free rectangular grids, mixed TeX labels, and default legend metrics.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-grid-primitives');cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_primitive';native_version=version;
for direction={'vertical','horizontal'}
 f=figure;ax=axes;set(ax,'XScale','log','YScale','log','XLim',[1 1000],'YLim',[1 1000]);box on;
 set(ax,'XGrid','off','YGrid','off','XMinorGrid','off','YMinorGrid','off');
 if strcmp(direction{1},'vertical'),ax.XMinorGrid='on';else,ax.YMinorGrid='on';end
 guiPrint(f,['grid_' direction{1} '_rectangular']);close all;
end
f=figure;ax=axes;axis square;
title({'Normalised slip tendency for \sigma_1=100 MPa, \sigma_2=50 MPa, \theta=0\circ';''});
xlabel('X, pixels');ylabel('Y, pixels');guiPrint(f,'mixed_text');print(f,'mixed_text.svg','-dsvg');close all;
f=figure;ax=axes;plot([0 100],[0 20],'k',[0 100],[0 60],'r');
leg=legend('Stress','Sliding or Failure','Location','northeast');
record=struct('native_version',native_version,'font',leg.FontName,'fontsize',leg.FontSize,...
 'position',leg.Position,'token',leg.ItemTokenSize,'linewidth',leg.LineWidth,'numcolumns',leg.NumColumns);
guiPrint(f,'legend');fid=fopen('legend.json','w');fwrite(fid,jsonencode(record));fclose(fid);close all;
disp('Text, legend and rectangular primitives captured.');
