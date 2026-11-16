% Additional audit calls, preserving the first failed absolute-path GUI case.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/native/details');if ~exist(out,'dir'),mkdir(out);end
cd(out);set(groot,'DefaultFigureVisible','off');set(groot,'DefaultAxesFontName','Arial');
global sTag;sTag='_audit';calls=struct;hough_real=struct;
for name={'MacduffBinary','Orkney1aBinary'}
 name=name{1};image=imread(fullfile(root,'fracpaq-matlab',[name '.tif']));
 binary=bwmorph(imcomplement(image),'clean');
 [H,theta,rho]=hough(binary,'RhoResolution',1,'Theta',-90:.5:89.5);
 threshold=ceil(.33*max(H(:)));P=houghpeaks(H,1000,'threshold',threshold);
 lines=houghlines(binary,theta,rho,P,'FillGap',5,'MinLength',3);
 endpoints=zeros(numel(lines),2,2);
 for j=1:numel(lines),endpoints(j,1,:)=lines(j).point1;endpoints(j,2,:)=lines(j).point2;end
 hough_real.(name)=struct('binary',binary,'H',H,'theta',theta,'rho',rho,'threshold',threshold,...
                        'peaks',P,'endpoints',endpoints);
 disp(['Native real Hough completed: ' name]);
end
save('hough_real.mat','hough_real');
% Genuine Hough diagnostic and missing-field case Q-06.
try
 figure;ax=gca;
 traces=guiFracPaQ2Dimage(fullfile(root,'tests/fixtures/images/tensor_network.tif'),0,1000,.33,5,3,ax);
 save('image_reader.mat','traces');calls.image_reader=struct('success',true);
catch err,calls.image_reader=failed(err);end
close all;
copyfile(fullfile(root,'tests/reference/sprint16/inputs/directional.txt'),'audit_nodes.txt');
try
 h=guiFracPaQ2D('Visible','off');drawnow;handles=guidata(h);
 snapshot(h,'initial');
 set(handles.edit_filename,'String','audit_nodes.txt');
 guiFracPaQ2D('edit_filename_Callback',handles.edit_filename,[],handles);
 handles=guidata(h);guiFracPaQ2D('pushbutton_preview_Callback',handles.pushbutton_preview,[],handles);
 snapshot(h,'preview');
 for name={'Maps','Lengths','Angles','Fluid','Wavelets','Graphs'}
  name=name{1};handles=guidata(h);button=handles.(['pb' name 'Tab']);
  guiFracPaQ2D(['pb' name 'Tab_Callback'],button,[],handles);snapshot(h,lower(name));
 end
 calls.gui=struct('success',true);
catch err,calls.gui=failed(err);end
close all;
fid=fopen('native_calls.json','w');fwrite(fid,jsonencode(calls));fclose(fid);
disp('Native Sprint16 details finished.');

function value=failed(err)
 value=struct('success',false,'identifier',err.identifier,'error',err.message);disp(err.message);
end

function snapshot(h,name)
 drawnow;print(h,['gui_' name '.png'],'-dpng','-r100');
 set(h,'Units','pixels');position=h.Position;
 objects=findall(h);controls=struct;
 for j=1:numel(objects)
  obj=objects(j);tag=get(obj,'Tag');
  if isempty(tag) || ~isvarname(tag),continue;end
  props=struct('type',get(obj,'Type'));
  if isprop(obj,'Position'),props.pixels=getpixelposition(obj,true);end
  for prop={'String','Value','Visible','Enable','FontName','FontSize','FontUnits'}
   p=prop{1};if isprop(obj,p),props.(p)=get(obj,p);end
  end
  controls.(tag)=props;
 end
 save(['gui_' name '.mat'],'position','controls');
end
