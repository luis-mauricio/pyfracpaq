% Sprint16 audit. Execute unchanged supplied code; all outputs live outside it.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/native');if ~exist(out,'dir'),mkdir(out);end
cd(out);set(groot,'DefaultFigureVisible','off');set(groot,'DefaultAxesFontName','Arial');
set(groot,'DefaultTextFontName','Arial');native_version=version;global sTag;sTag='_audit';
calls=struct;
inputs={'directional','rectangular','tensor_network'};hough_refs=struct;
for item=1:numel(inputs)
 name=inputs{item};file=fullfile(root,'tests/fixtures/images',[name '.tif']);
 image=imread(file);binary=bwmorph(imcomplement(image),'clean');
 [H,theta,rho]=hough(binary,'RhoResolution',1,'Theta',-90:.5:89.5);
 threshold=ceil(.33*max(H(:)));P=houghpeaks(H,1000,'threshold',threshold);
 lines=houghlines(binary,theta,rho,P,'FillGap',5,'MinLength',3);
 endpoints=zeros(numel(lines),2,2);
 for j=1:numel(lines),endpoints(j,1,:)=lines(j).point1;endpoints(j,2,:)=lines(j).point2;end
 hough_refs.(name)=struct('image',image,'binary',binary,'H',H,'theta',theta,'rho',rho,...
                         'threshold',threshold,'peaks',P,'endpoints',endpoints);
end
save('hough_arrays.mat','hough_refs','native_version');disp('Native Hough arrays saved.');
figure;ax=gca;
[traces,xmin,ymin,xmax,ymax]=guiFracPaQ2Dlist(fullfile(root,'tests/reference/sprint16/inputs/directional.txt'),0,ax,[0 0 1]);
close all;save('geometry_arrays.mat','traces','xmin','ymin','xmax','ymax');
try
 guiFracPaQ2Dtracemap(traces,0,12,true,false,false,[0 0 1],false,true,false,false,...
                     true,true,true,100,50,0,false,false,0,0,.6);
 calls.maps=struct('success',true);save_fig_arrays('maps_arrays.mat');
catch err,calls.maps=failed(err);end
close all;
try
 guiFracPaQ2Dlength(traces,0,12,20,true,true,true,false,false,false,false,false,[0 0 1],0,0,false);
 calls.lengths=struct('success',true);save_fig_arrays('length_arrays.mat');
catch err,calls.lengths=failed(err);end
close all;
try
 guiFracPaQ2Dangle(traces,12,20,10,true,true,false,false,false,false,true,true,[0 0 1]);
 calls.angles=struct('success',true);save_fig_arrays('angle_arrays.mat');
catch err,calls.angles=failed(err);end
close all;
try
 guiFracPaQ2Dpattern(traces,0,4,true,true,false,true,3,false,false,[0 0 1],0);
 calls.circular=struct('success',true);save_fig_arrays('circular_arrays.mat');
catch err,calls.circular=failed(err);end
close all;
% Reproduce censor output; source tables are genuine and separately tagged.
sTag='_censor';figure;
try
 edge=guiFracPaQ2Dlist(fullfile(root,'tests/fixtures/nodes/lengths_edges.txt'),0,gca,[0 0 1]);close all;
 guiFracPaQ2Dlength(edge,0,0,20,false,false,true,false,true,false,false,false,[0 0 1],0,0,false);
 calls.censor=struct('success',true);
catch err,calls.censor=failed(err);end
close all;
% Actual doubleAngles/reverseAxis conventions, including extreme north.
raw=[0 .5 30 90 179.5];angular=struct;
for north=[-360 0 12.5 360]
 doubled=doubleAngles(raw',north);flipped=reverseAxis(doubled);
 angular.(['north_' strrep(strrep(num2str(north),'-','minus'),'.','p')])=...
 struct('north',north,'raw',raw,'doubled',doubled,'flipped',flipped);
end
save('angular_conventions.mat','angular');
% Capture genuine GUI rendering/callbacks in this batch process only.
try
 h=guiFracPaQ2D('Visible','off');drawnow;
 set(h,'Units','pixels');gui_position=h.Position;
 print(h,'gui_initial.png','-dpng','-r100');
 handles=guidata(h);set(handles.edit_filename,'String',fullfile(root,'tests/reference/sprint16/inputs/directional.txt'));
 guiFracPaQ2D('edit_filename_Callback',handles.edit_filename,[],handles);
 handles=guidata(h);guiFracPaQ2D('pushbutton_preview_Callback',handles.pushbutton_preview,[],handles);
 print(h,'gui_preview.png','-dpng','-r100');
 for name={'Maps','Lengths','Angles','Fluid','Wavelets','Graphs'}
  name=name{1};handles=guidata(h);button=handles.(['pb' name 'Tab']);
  guiFracPaQ2D(['pb' name 'Tab_Callback'],button,[],handles);
  print(h,['gui_' lower(name) '.png'],'-dpng','-r100');
 end
 save('gui_position.mat','gui_position');calls.gui=struct('success',true);
catch err,calls.gui=failed(err);end
close all;
fid=fopen('native_calls.json','w');fwrite(fid,jsonencode(calls));fclose(fid);
disp('Native Sprint16 capture finished.');

function value=failed(err)
 value=struct('success',false,'identifier',err.identifier,'error',err.message);
 disp(['Native failure: ' err.message]);
end

function save_fig_arrays(file)
 figs=findall(groot,'Type','figure');[~,order]=sort([figs.Number]);figs=figs(order);
 arrays=struct;
 for f=1:numel(figs)
  axes=findall(figs(f),'Type','axes');
  for j=1:numel(axes)
   ax=axes(j);images=findall(ax,'Type','image');lines=findall(ax,'Type','line');
   data=struct('title',{ax.Title.String},'xlabel',{ax.XLabel.String},'ylabel',{ax.YLabel.String},...
    'xlim',ax.XLim,'ylim',ax.YLim,'position',ax.Position,'cmap',colormap(ax));
   data.images=cell(1,numel(images));data.lines=cell(1,numel(lines));
   for k=1:numel(images),data.images{k}=struct('values',images(k).CData,'x',images(k).XData,'y',images(k).YData);end
   for k=1:numel(lines),data.lines{k}=struct('x',lines(k).XData,'y',lines(k).YData,'colour',lines(k).Color);end
   arrays.(['figure' num2str(f) '_axes' num2str(j)])=data;
  end
 end
 save(file,'arrays');
end
