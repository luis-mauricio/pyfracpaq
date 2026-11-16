% Rendering measurements only; supplied MATLAB sources remain unchanged.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-style');if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_style';
ranges=[0 1997.7;1.8 1988.5;0 350.207;0 337.2;0 1076;0 180;-921 901;480 1620;22.97 1355;0 1.3e-12];
records=struct([]);
for i=1:size(ranges,1)
 f=figure;ax=axes;plot(ranges(i,:),ranges(i,:),'rs');xlabel('X, pixels');ylabel('Frequency');title({'Title 1076';''});grid on;
 before=properties(ax);xlim(ranges(i,:));ylim(ranges(i,:));manual=properties(ax);
 guiPrint(f,['probe' num2str(i)]);printed=properties(ax);
 print(f,['probe' num2str(i) '.svg'],'-dsvg');
 records(i).range=ranges(i,:);records(i).auto=before;records(i).manual=manual;records(i).printed=printed;
 close(f);
end
fid=fopen('probes.json','w');fwrite(fid,jsonencode(records));fclose(fid);
disp('Native style probes captured.');
function p=properties(ax)
 drawnow;p=struct('position',ax.Position,'xlim',ax.XLim,'ylim',ax.YLim,'xtick',ax.XTick,'ytick',ax.YTick,...
 'font',ax.FontName,'fontsize',ax.FontSize,'labelsize',ax.XLabel.FontSize,'titlesize',ax.Title.FontSize,...
 'ticklength',ax.TickLength,'linewidth',ax.LineWidth,'xlabelposition',ax.XLabel.Position,...
 'ylabelposition',ax.YLabel.Position,'titleposition',ax.Title.Position);
end
