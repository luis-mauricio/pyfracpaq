% Additional independent MATLAB contexts; original sources are read-only.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
base=fullfile(root,'tests/reference/sprint16/final');out=fullfile(base,'native-contexts');
if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_context';native_version=version;records=struct;
f=figure;ax=axes;hold on;
for i=1:4
 names={'o','s','d','^'};plot(i,1,names{i},'MarkerSize',6,'Color','r');
end
xlim([0 5]);ylim([0 2]);guiPrint(f,'markers');print(f,'markers.svg','-dsvg');close all;
maxima=[1 1.2345645446 1.0064e-12 3.6 4.1 5.8];polar=struct([]);
for i=1:numel(maxima)
 f=figure;ax=polaraxes;polarplot(ax,0:pi/180:2*pi,ones(1,361)*maxima(i));
 ax.ThetaZeroLocation='top';ax.ThetaDir='clockwise';title('Polar probe');
 guiPrint(f,['polar' num2str(i)]);
 polar(i).maximum=maxima(i);polar(i).limits=ax.RLim;polar(i).ticks=ax.RTick;close all;
end
f=figure;ax=axes;imagesc(magic(12));axis equal tight;cb=colorbar('southoutside');
xlabel('X, pixels');ylabel('Y, pixels');cb.Label.String='Colourbar label';
guiPrint(f,'colourbar');print(f,'colourbar.svg','-dsvg');
records.colourbar=struct('fontsize',cb.FontSize,'labelsize',cb.Label.FontSize,'ticklength',cb.TickLength,...
 'tickdirection',cb.TickDirection,'position',cb.Position,'gridalpha',ax.GridAlpha,...
 'minorgridalpha',ax.MinorGridAlpha,'minorgridlinestyle',ax.MinorGridLineStyle);close all;
records.polar=polar;
figure;[traces,~,~,~,~]=guiFracPaQ2Dlist(fullfile(root,'fracpaq-matlab/SD11A.txt'),0,gca,[0 0 1]);close all;
for kernel={'morlet','mexican'}
 kind=kernel{1};folder=fullfile(out,kind);if ~exist(folder,'dir'),mkdir(folder);end;cd(folder);
 start=tic;
 try
  guiFracPaQ2Dwavelet(traces,[16 32],[.5 .25],30,strcmp(kind,'morlet'),[0 0 1],false,false);
  records.(kind)=struct('success',true,'seconds',toc(start));
 catch err
  records.(kind)=struct('success',false,'seconds',toc(start),'identifier',err.identifier,'error',err.message,'stack',err.stack);
 end
 figs=findall(groot,'Type','figure');capture=cell(1,numel(figs));
 for i=1:numel(figs)
  axs=findall(figs(i),'Type','axes');entries=cell(1,numel(axs));
  for j=1:numel(axs)
   ax=axs(j);im=findall(ax,'Type','image');bars=findall(ax,'Type','bar');
   e=struct('title',{ax.Title.String},'position',ax.Position,'images',{{}},'bars',{{}});
   for k=1:numel(im),e.images{end+1}=im(k).CData;end
   for k=1:numel(bars),e.bars{end+1}=struct('x',bars(k).XData,'y',bars(k).YData);end
   entries{j}=e;
  end
  capture{i}=entries;
 end
 save('panels.mat','capture','native_version','-v7');close all;cd(out);
 disp(['Wavelet context finished: ' kind]);
end
fid=fopen('contexts.json','w');fwrite(fid,jsonencode(struct('native_version',native_version,'records',records,...
 'wavelets',struct('a',[16 32],'entered_L',[2 4],'ratios',[.5 .25],'step',30,'input','fracpaq-matlab/SD11A.txt'))));fclose(fid);
