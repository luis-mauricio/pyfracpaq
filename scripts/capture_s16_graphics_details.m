% Supplementary graphical properties; the original source tree stays read-only.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/final/native-graphics-details');
if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off','DefaultAxesFontName','Arial','DefaultTextFontName','Arial');
global sTag;sTag='_details';native_version=version;records=struct;
figure;guiFracPaQ2Dimage(fullfile(root,'tests/fixtures/images/tensor_network.tif'),0,1000,.33,5,3,gca);
f=gcf;ax=findall(f,'Type','axes');records.hough=cell(1,numel(ax));
for i=1:numel(ax)
 a=ax(i);surfaces=findall(a,'Type','surface');meshes=cell(1,numel(surfaces));
 for j=1:numel(surfaces)
  s=surfaces(j);meshes{j}=struct('x',s.XData,'y',s.YData,'z',s.ZData,'c',s.CData,...
   'edge',s.EdgeColor,'face',s.FaceColor,'width',s.LineWidth,'mapping',s.CDataMapping,'meshstyle',s.MeshStyle);
 end
 im=findall(a,'Type','image');images=cell(1,numel(im));
 for j=1:numel(im),images{j}=struct('x',im(j).XData,'y',im(j).YData,'interpolation',im(j).Interpolation);end
 records.hough{i}=struct('title',{a.Title.String},'clim',a.CLim,'colormap',a.Colormap,...
  'surfaces',{meshes},'images',{images},'position',a.Position,'xlim',a.XLim,'ylim',a.YLim);
end
print(f,'hough.svg','-dsvg');close all;
% A small, isolated mesh makes flat edge-colour ownership inspectable.
f=figure;[x,y]=meshgrid(0:5,0:4);z=reshape(0:29,5,6);mesh(x,y,z);axis square tight;view(0,90);
colormap(hot(256));guiPrint(f,'mesh_probe');print(f,'mesh_probe.svg','-dsvg');close all;
records.histograms=struct([]);index=0;
for kernel={'morlet','mexican'}
 kind=kernel{1};data=load(fullfile(root,'tests/reference/sprint16/final/native-contexts',kind,'panels.mat'));
 for i=1:numel(data.capture)
  for j=1:numel(data.capture{i})
   a=data.capture{i}{j};
   if contains(string(a.title(1)),'WC histogram')
    b=a.bars{1};f=figure;ax=axes;bar(b.x,b.y,1);axis square;grid on;
    index=index+1;records.histograms(index).kernel=kind;
    records.histograms(index).title=a.title;records.histograms(index).xlim=ax.XLim;
    records.histograms(index).xtick=ax.XTick;close all;
   end
  end
 end
end
save('properties.mat','records','native_version','-v7');
disp('Supplementary graphical properties captured.');
