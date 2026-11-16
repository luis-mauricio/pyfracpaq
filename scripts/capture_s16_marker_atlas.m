% Primitive rendering assets, independent of all scientific reference datasets.
% No supplied source is modified; the runtime will use generated glyph assets,
% just as it uses the frozen native colour tables, without MATLAB installed.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-marker-atlas');
if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off');global sTag;sTag='_atlas';
f=figure;ax=axes('Position',[0 0 1 1]);hold on;entries=struct([]);index=0;
for shape={'o','s'}
 for size=[2 3 4 6 8 12]
  for width=[.5 1]
   for filled=[false true]
    index=index+1;x=.5+mod(index-1,8);y=.5+floor((index-1)/8);
    face='none';if filled,face=[0 0 1];end
    plot(x,y,'LineStyle','none','Marker',shape{1},'MarkerSize',size,...
         'LineWidth',width,'MarkerEdgeColor',[0 0 0],'MarkerFaceColor',face);
    entries(index).shape=shape{1};entries(index).size_points=size;
    entries(index).linewidth_points=width;entries(index).filled=filled;
    entries(index).x=x;entries(index).y=y;
   end
  end
 end
end
axis equal off;xlim([0 8]);ylim([0 8]);guiPrint(f,'marker_primitives');
records=struct('native_version',version,'dpi',600,'paper_cm',[20 20],...
 'scope','Primitive glyph assets only, not scientific comparison goldens.', 'entries',entries);
fid=fopen('atlas.json','w');fwrite(fid,jsonencode(records));fclose(fid);close all;
disp('Native primitive atlas captured.');
