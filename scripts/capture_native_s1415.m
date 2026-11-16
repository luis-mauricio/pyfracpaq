% Execute unchanged supplied functions/scripts; never write into originals.
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'fracpaq-matlab'));
out14=fullfile(root,'tests/reference/sprint14/native');
out15=fullfile(root,'tests/reference/sprint15/native');
if ~exist(out14,'dir'),mkdir(out14);end
if ~exist(out15,'dir'),mkdir(out15);end
set(groot,'DefaultFigureVisible','off');
set(groot,'DefaultAxesFontName','Arial');
native_version=version;
x=1:8;y=1:5;data=zeros(5,8);data(2,2:7)=1;data(2:5,6)=.5;
a=[1.5 3];theta=[0 pi/6 pi/2];L=[.5 1];
[wm,em]=morletCWT(data,x,y,a,theta,L);
[sm,esm]=morletCWTself(x,y,a,theta,L);
[wh,eh]=mexicanhatCWT(data,x,y,a,theta,L);
[sh,esh]=mexicanhatCWTself(x,y,a,theta,L);
save(fullfile(out14,'cwt_arrays.mat'),'x','y','data','a','theta','L',...
 'wm','em','sm','esm','wh','eh','sh','esh','native_version');
disp('Native rectangular kernels and self responses saved.');
global sTag;
cd(out14);traces=make_traces({[0 0;100 0;100 60],[20 10;40 30]});
% Empty a intentionally runs ONLY the actual original raster stage (no CWT).
guiFracPaQ2Dwavelet(traces,[],1,90,true,[0 0 1],false,false);
movefile('FracPaQ2D_wavelet_traces.png','native_integrated_raster.png');
calls=struct;
for kind={'morlet','mexican','rectangular','step40','step270'}
 name=kind{1};folder=fullfile(out14,name);if ~exist(folder,'dir'),mkdir(folder);end
 cd(folder);img=uint8(ones(8,8)*255);img(3,2:7)=0;img(2:7,6)=0;
 step=45;if strcmp(name,'rectangular'),img=img(:,1:6);end
 if strcmp(name,'step40'),step=40;end
 if strcmp(name,'step270'),step=270;end
 imwrite(repmat(img,1,1,3),'FracPaQ2D_wavelet_traces.png');sTag=['_native_' name];
 try
  guiFracPaQ2Dwavelet2(2,[.5 1],step,~strcmp(name,'mexican'),[0 0 1]);
  calls.(name)=struct('success',true);
 catch err
  calls.(name)=struct('success',false,'error',err.message,'identifier',err.identifier);
 end
 close all;
end
fid=fopen(fullfile(out14,'native_calls.json'),'w');fwrite(fid,jsonencode(calls));fclose(fid);
cd(out15);
[xx,yy]=meshgrid(1:43,1:39);rgb=uint8(cat(3,mod(xx*19+yy*3,256),mod(xx*7+yy*13,256),mod(xx*2+yy*23,256)));
imwrite(rgb,'MacduffColourCropped.jpg');
% eval keeps cwd here, unlike run(script), which changes into its source folder.
eval(fileread(fullfile(root,'fracpaq-matlab','FracPaQ2D_imagePreprocess.m')));
gray=imgEx1gray;median=imgEx1med;difference=imgEx1diff;edges=imgEx1edge;
closed=imgEx1close;thinned=imgEx1inv;processed=~thinned;
save(fullfile(out15,'preprocess_arrays.mat'),'gray','median','difference','edges','closed','thinned','processed');
print(gcf,fullfile(out15,'preprocess_panel.png'),'-dpng','-r100');close all;
textsource=sprintf('1,,hello\r\n2,3,"a,b"\r\n');
[mixed,readstats]=readtext(textsource,',','','"','textsource');
figure;imagesc(0);caxis([-2 5]);balance=cmocean('balance',7,'pivot',1);close all;
lengths=[2 3];angles=[30 110];[tensor16,polar16]=getF16tensor(lengths,angles,20);
segments=[1 1 9 9;1 9 9 1;5 1 5 9];
[probe_m,probe_ij,probe_mq]=probePlane(1,0,0,10,10,segments,8);
save(fullfile(out15,'aux_arrays.mat'),'mixed','readstats','balance','tensor16','polar16',...
 'segments','probe_m','probe_ij','probe_mq','native_version');
disp('Native Sprint 14/15 capture finished.');

function traces=make_traces(points)
 traces=struct;
 for k=1:numel(points)
  p=points{k};lengths=sqrt(sum(diff(p).^2,2));
  traces(k).totalLength=sum(lengths);traces(k).nNodes=size(p,1);traces(k).nSegments=numel(lengths);
  for j=1:size(p,1),traces(k).Node(j).x=p(j,1);traces(k).Node(j).y=p(j,2);end
 end
end
