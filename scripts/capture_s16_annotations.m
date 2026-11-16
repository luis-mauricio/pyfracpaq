% Deterministic Plot* replays, without rerunning fitting or Monte Carlo.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-annotations');if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_annotation';x=[1;10;20;30;50;100;200;500];z=x(x>=20);records=struct;
for kind={'power_law','exponential','lognormal'}
 switch kind{1}
  case 'power_law',PlotPowerLaw(x,x,z,20,2.5373,[0 0 1]);
  case 'exponential',PlotExp(x,x,x,.0045678,1,[0 0 1]);
  case 'lognormal',PlotLogNorm(x,x,x,3.12345,1.23456,1,[0 0 1]);
 end
 f=gcf;drawnow;t=findall(f,'Type','textboxshape');leg=findall(f,'Type','legend');
 records.(kind{1})=struct('figure_pixels',f.Position,'position_before_print',t.Position,...
  'font',t.FontName,'fontsize',t.FontSize,'margin',t.Margin,'string',{t.String},'units',t.Units,...
  'vertical_alignment',t.VerticalAlignment,'horizontal_alignment',t.HorizontalAlignment,...
  'fit',t.FitBoxToText,'legend_position',leg.Position,'legend_tokens',leg.ItemTokenSize);
 guiPrint(f,kind{1});records.(kind{1}).position_after_print=t.Position;close all;
end
fid=fopen('annotations.json','w');fwrite(fid,jsonencode(struct('native_version',version,'records',records)));fclose(fid);
disp('Deterministic native annotations captured.');
