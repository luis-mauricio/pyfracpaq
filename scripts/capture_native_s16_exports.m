% Remaining export routes, executed without changes to the supplied sources.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
out=fullfile(root,'tests/reference/sprint16/native/exports');if ~exist(out,'dir'),mkdir(out);end
cd(out);set(groot,'DefaultFigureVisible','off');set(groot,'DefaultAxesFontName','Arial');
set(groot,'DefaultTextFontName','Arial');global sTag;sTag='_audit';calls=struct;
figure;traces=guiFracPaQ2Dlist(fullfile(root,'tests/reference/sprint16/inputs/directional.txt'),0,gca,[0 0 1]);close all;
try
 guiFracPaQ2Dpattern(traces,0,4,false,false,true,false,3,false,false,[0 0 1],0);
 calls.connectivity=struct('success',true);
catch err,calls.connectivity=failed(err);end
close all;
% Explicit alternating colours, same supplied geometry, no source mutation.
for j=1:numel(traces),if mod(j,2)==0,traces(j).Colour=[1 0 0];end;end
try
 guiFracPaQ2Dtracemap(traces,0,12,false,false,false,[0 0 1],true,false,false,false,...
                     false,false,false,100,50,0,false,false,0,0,.6);
 calls.multicolour=struct('success',true);save('multicolour_input.mat','traces');
catch err,calls.multicolour=failed(err);end
close all;
data=jsondecode(fileread(fullfile(root,'tests/reference/sprint16/all-outputs/input.json')));
fid=fopen('all_outputs_input.txt','w');
for j=1:numel(data)
 points=data(j).nodes;
 for k=1:size(points,1),fprintf(fid,'%.17g\t%.17g\t',points(k,1),points(k,2));end
 fprintf(fid,'\n');
end
fclose(fid);rng(20261114,'twister');
try
 figure;traces=guiFracPaQ2Dlist('all_outputs_input.txt',0,gca,[0 0 1]);close all;
 guiFracPaQ2Dlength(traces,0,12,20,false,false,false,true,false,false,false,false,[0 0 1],0,0,false);
 calls.mle_gui_function=struct('success',true);
catch err,calls.mle_gui_function=failed(err);end
close all;
for name={'simple','multicolour'}
 name=name{1};copyfile(fullfile(root,'tests/fixtures/svg',[name '.svg']),[name '.svg']);
 try
  convertSVG2txt_colour2([name '.svg']);calls.(['svg_' name])=struct('success',true);
 catch err,calls.(['svg_' name])=failed(err);end
end
fid=fopen('native_calls.json','w');fwrite(fid,jsonencode(calls));fclose(fid);
disp('Sprint16 remaining native export routes finished.');

function value=failed(err)
 value=struct('success',false,'identifier',err.identifier,'error',err.message);disp(err.message);
end
