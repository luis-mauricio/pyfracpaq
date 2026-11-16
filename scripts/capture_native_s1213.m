% Execute supplied sources without editing them; keep results outside originals.
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'fracpaq-matlab'));
out12=fullfile(root,'tests/reference/sprint12/native');
out13=fullfile(root,'tests/reference/sprint13/native');
if ~exist(out12,'dir'),mkdir(out12);end
if ~exist(out13,'dir'),mkdir(out13);end
set(groot,'DefaultFigureVisible','off');
set(groot,'DefaultAxesFontName','Arial');
set(groot,'DefaultTextFontName','Arial');
native_version=version;

x=[0 0;1 0;0 2;2 1];values=[1;3;2;4];
variograms=struct;
variograms.default=variogram(x,values,'nrbins',30);
variograms.gamma=variogram(x,values,'nrbins',4,'maxdist',3);
variograms.cloud1=variogram(x,values,'nrbins',4,'maxdist',3,'type','cloud1');
variograms.cloud2=variogram(x,values,'nrbins',4,'maxdist',3,'type','cloud2');
variograms.anisotropic=variogram(x,values,'nrbins',4,'maxdist',3,'anisotropy',true,'thetastep',30);
variograms.anisotropic40=variogram(x,values,'nrbins',4,'maxdist',3,'anisotropy',true,'thetastep',40);
for n=[999 1000]
 coords=[(0:n-1)' zeros(n,1)];v=mod((0:n-1)',5);
 variograms.(['n' num2str(n)])=variogram(coords,v,'nrbins',3,'maxdist',1.1);
end
variograms.coincident=variogram([0 0;0 0],[1;3],'nrbins',3);
variograms.nan_removed=variogram([x;nan nan],[values;nan],'nrbins',4,'maxdist',3);
save(fullfile(out12,'variogram_arrays.mat'),'variograms','x','values','native_version');
disp('Native variogram arrays saved.');

global sTag;
block_inputs=struct;
block_inputs.separate={ [10 10;50 10;50 50;10 50;10 10],...
                        [70 30;110 30;110 70;70 70;70 30] };
block_inputs.nested={ [0 0;100 0;100 80;0 80;0 0],...
                     [30 25;70 25;70 55;30 55;30 25] };
block_inputs.oblique={ [0 20;40 0;80 20;40 60;0 20] };
blocks=struct;
for name={'separate','nested','oblique','scaled'}
 name=name{1};folder=fullfile(out12,name);if ~exist(folder,'dir'),mkdir(folder);end
 cd(folder);scale=1;points=block_inputs.separate;
 if strcmp(name,'nested'),points=block_inputs.nested;
 elseif strcmp(name,'oblique'),points=block_inputs.oblique;
 elseif strcmp(name,'scaled'),scale=10;points=cellfun(@(p)p/scale,points,'UniformOutput',false);end
 traces=make_traces(points);sTag=['_native_' name];
 try
  guiFracPaQ2Dlength(traces,double(scale>1)*scale,0,10,false,false,false,false,false,true,...
                     false,false,[0 0 1],0,0,false);
  blocks.(name)=struct('success',true);
 catch err
  blocks.(name)=struct('success',false,'error',err.message,'identifier',err.identifier);
 end
 if exist('FracPaQ2D_blocksize.bmp','file')
  indexed=imread('FracPaQ2D_blocksize.bmp');threshold=graythresh(indexed);
  binary=imbinarize(indexed);cc=bwconncomp(binary);props=regionprops(cc,'Area','Centroid');
  area=cat(1,props.Area);centroids=cat(1,props.Centroid);touches=false(numel(props),1);
  for j=1:cc.NumObjects
   [r,c]=ind2sub(size(binary),cc.PixelIdxList{j});
   touches(j)=any(r==1 | r==size(binary,1) | c==1 | c==size(binary,2));
  end
  save('raster_arrays.mat','indexed','binary','threshold','area','centroids','touches','scale','points');
 end
 close all;
 disp(['Native block case finished: ' name]);
end
fid=fopen(fullfile(out12,'native_calls.json'),'w');fwrite(fid,jsonencode(blocks));fclose(fid);

points={[-6 -3;-3 3;3 3;6 -3],[0 -.5;0 .5]};
traces=make_traces(points);line_x=[-6 6];line_y=[0 0];
cd(out13);sTag='_native';
guiFracPaQ2Dgraphs(traces,0,line_x,line_y,[0 0 1],3,false,false,...
 true,true,true,true,true,true,true,true);
figures=findall(groot,'Type','figure');[~,idx]=sort([figures.Number]);figures=figures(idx);
names={'trace_along','segment_along','angle_along','map','intensity','density',...
       'trace_from','segment_from','angle_from'};
graphs=struct;
for j=1:numel(figures)
 ax=findall(figures(j),'Type','axes');ax=ax(1);lines=flipud(findall(ax,'Type','line'));
 xdata=cell(1,numel(lines));ydata=xdata;
 for k=1:numel(lines),xdata{k}=lines(k).XData;ydata{k}=lines(k).YData;end
 graphs.(names{j})=struct('x',{xdata},'y',{ydata},'position',ax.Position,...
   'xlim',ax.XLim,'ylim',ax.YLim,'title',ax.Title.String,'xlabel',ax.XLabel.String,...
   'ylabel',ax.YLabel.String,'font',ax.FontName,'font_size',ax.FontSize);
end
save(fullfile(out13,'graph_arrays.mat'),'graphs','points','line_x','line_y','native_version');
close all;
calls=struct;
for name={'no_intersections','zero_line','density_only'}
 name=name{1};xline=line_x;yline=line_y;traces=make_traces(points);
 if strcmp(name,'no_intersections'),yline=[10 10];end
 if strcmp(name,'zero_line'),xline=[0 0];yline=[0 0];end
 sTag=['_native_' name];
 try
  if strcmp(name,'density_only')
   guiFracPaQ2Dgraphs(traces,0,xline,yline,[0 0 1],3,false,false,...
     false,false,false,false,true,false,false,false);
  else
   guiFracPaQ2Dgraphs(traces,0,xline,yline,[0 0 1],3,false,false,...
     true,false,false,false,false,false,false,false);
  end
  calls.(name)=struct('success',true,'figures',numel(findall(groot,'Type','figure')));
 catch err
  calls.(name)=struct('success',false,'error',err.message,'identifier',err.identifier);
 end
 close all;
end
fid=fopen(fullfile(out13,'native_calls.json'),'w');fwrite(fid,jsonencode(calls));fclose(fid);
cd(out12);sTag='_native_variogram';traces=make_traces(points);
guiFracPaQ2Dlength(traces,0,0,10,false,false,false,false,false,false,...
                   false,false,[0 0 1],0,0,true);
close all;
disp('Native Sprints 12/13 capture completed.');

function traces=make_traces(points)
 traces=struct;
 for k=1:numel(points)
  p=points{k};lengths=sqrt(sum(diff(p).^2,2));cum=[0;cumsum(lengths)];
  traces(k).nNodes=size(p,1);traces(k).nSegments=numel(lengths);
  traces(k).totalLength=sum(lengths);traces(k).segmentLength=lengths';
  angle=atand(diff(p(:,1))./diff(p(:,2)));angle(angle<0)=angle(angle<0)+180;
  traces(k).segmentAngle=angle';
  half=sum(lengths)/2;index=find(cum(2:end)>=half,1);
  midpoint=p(index,:)+(half-cum(index))/lengths(index)*(p(index+1,:)-p(index,:));
  traces(k).midpointX=midpoint(1);traces(k).midpointY=midpoint(2);
  for j=1:size(p,1),traces(k).Node(j).x=p(j,1);traces(k).Node(j).y=p(j,2);end
  for j=1:numel(lengths)
   traces(k).Segment(j).Point1=p(j,:);traces(k).Segment(j).Point2=p(j+1,:);
   traces(k).Segment(j).midpointX=mean(p(j:j+1,1));
   traces(k).Segment(j).midpointY=mean(p(j:j+1,2));
  end
 end
end
