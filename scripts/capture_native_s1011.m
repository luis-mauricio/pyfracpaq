% Read-only execution of supplied FracPaQ routines and their stated equations.
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'fracpaq-matlab'));
out10=fullfile(root,'tests/reference/sprint10/native');
out11=fullfile(root,'tests/reference/sprint11/native');
if ~exist(out10,'dir'),mkdir(out10);end
if ~exist(out11,'dir'),mkdir(out11);end
set(groot,'DefaultFigureVisible','off');
set(groot,'DefaultAxesFontName','Arial');
set(groot,'DefaultTextFontName','Arial');
native_version=version;
alpha=0:2*pi/360:2*pi;
tensor_refs=struct;
for item=1:3
 if item==1,name='directional';lengths=[2 3 4];angles=[90 90 90];area=16;
 elseif item==2,name='isotropic';lengths=ones(1,36);angles=0:5:175;area=100;
 else,name='oblique';lengths=[2 3 4 5];angles=[13.5 56 120 271];area=32;end
 [F2,p2]=getF2tensor(lengths,angles,area);
 [F4,p4]=getF4tensor(lengths,angles,area);
 [F8,p8]=getF8tensor(lengths,angles,area);
 tensor_refs.(name)=struct('lengths',lengths,'angles',angles,'area',area,...
  'F0',sum(lengths.^2)/area,'F2',F2,'F4',F4,'F8',F8,'polar2',p2,'polar4',p4,'polar8',p8);
end
permeability_refs=struct;
for mode=1:4
 lengths=[2 3 4];poles=[90 120 155];area=24;lambda=.7;
 if mode==1,name='fixed';t=ones(size(lengths))*.001;
 elseif mode==2,name='scaled';t=.01*lengths.^.75;
 elseif mode==3,name='zero_aperture';t=zeros(size(lengths));
 else,name='zero_lambda';t=ones(size(lengths))*.001;lambda=0;end
 P=zeros(2);l=cosd(poles);m=sind(poles);
 for i=1:numel(lengths)
  P(1,1)=P(1,1)+t(i)^3*lengths(i)*l(i)*l(i)/area;
  P(2,2)=P(2,2)+t(i)^3*lengths(i)*m(i)*m(i)/area;
  P(1,2)=P(1,2)+t(i)^3*lengths(i)*l(i)*m(i)/area;
 end
 P(2,1)=P(1,2);K=lambda/12*(trace(P)*eye(2)-P);
 polar=K(1,1)*cos(alpha).^2+2*K(1,2)*cos(alpha).*sin(alpha)+K(2,2)*sin(alpha).^2;
 permeability_refs.(name)=struct('lengths',lengths,'poles',poles,'area',area,...
  'lambda',lambda,'apertures',t,'P',P,'K',K,'eigenvalues',sort(eig(K)),'polar',polar);
end
save(fullfile(out10,'tensor_arrays.mat'),'tensor_refs','permeability_refs','alpha','native_version');
stability_refs=struct;
for item=1:4
 raw=[0 90];north=0;theta=30;s1=100;s2=50;pf=10;C0=2;mu=.6;
 if item==1,name='rotated_orthogonal';
 elseif item==2,name='equal_stress';s2=s1;
 elseif item==3,name='zero_friction';mu=0;
 else,name='equality_csf';s2=s1;theta=0;mu=0;pf=0;C0=0;end
 preliminary=raw+90;
 sn0=(s1+s2)/2+(s1-s2)*cosd(2*preliminary)/2;
 tau0=abs(-(s1-s2)*sind(2*preliminary)/2);
 tsmax=max(abs(tau0./sn0));
 sfmin=min(sn0-pf-(tau0-C0)/mu);sfmax=max(sn0-pf-(tau0-C0)/mu);
 strikes=round(raw-north);strikes(strikes<1)=180;
 pole=strikes+90-theta;
 sn=abs((s1+s2)/2+(s1-s2)*cosd(2*pole)/2);
 tau=abs(-(s1-s2)*sind(2*pole)/2);
 ts=tau./sn;sf=sn-pf-(tau-C0)/mu;
 midpoints=5:10:355;pole_mid=midpoints+90-theta;
 sn_mid=(s1+s2)/2+(s1-s2)*cosd(2*pole_mid)/2;
 tau_mid=abs(-(s1-s2)*sind(2*pole_mid)/2);
 sf_indices=abs(round((sf-sfmin)/(sfmax-sfmin))*100);
 sf_indices(sf_indices<1)=1;
 stability_refs.(name)=struct('raw',raw,'north',north,'theta',theta,'sigma1',s1,'sigma2',s2,...
  'pf',pf,'C0',C0,'mu',mu,'sn',sn,'tau',tau,'source_Tsmax',tsmax,...
  'source_Sfmin',sfmin,'source_Sfmax',sfmax,'Ts',ts,'TsNorm',ts/tsmax,...
  'Td',(s1-sn)/(s1-s2),'Sf',sf,...
  'source_Sf_indices',sf_indices,...
  'map_csf',tau>=mu*(sn-pf)+C0,'rose_midpoints',midpoints,...
  'rose_csf',tau_mid>mu*(sn_mid-pf)+C0,'rose_csf_inclusive',tau_mid>=mu*(sn_mid-pf)+C0);
end
jet19=jet(19);jet100=jet(100);jet256=jet(256);
save(fullfile(out11,'stability_arrays.mat'),'stability_refs','jet19','jet100','jet256','native_version');
disp('Native tensor/stability numeric arrays saved.');

% Actual source functions, including their exports and observable failures.
global sTag;
cd(out10);sTag='_native';
traces=make_traces(0:5:175);
layouts=struct;
guiFracPaQ2Dcracktensor(traces,12,false,true);layouts.crack=figure_layout(gcf);close all;
guiFracPaQ2Dtensor(traces,12,.7,false,true,.001,0,0,0,[0 0 1]);layouts.permeability=figure_layout(gcf);close all;
fid=fopen(fullfile(out10,'layout.json'),'w');fwrite(fid,jsonencode(layouts));fclose(fid);
disp('Native tensor figures saved.');
records=struct;
cd(out11);
for family=1:4
 names={'slip','dilation','susceptibility','csf'};name=names{family};
 flags=false(1,4);flags(family)=true;sTag=['_native_' name];
 try
  guiFracPaQ2Dtracemap(traces,0,0,false,false,false,[0 0 1],false,...
   false,flags(1),flags(2),false,false,false,100,50,0,flags(3),flags(4),2,10,.6);
  records.(name)=struct('success',true);
  figures=findall(groot,'Type','figure');captured=cell(1,numel(figures));
  for j=1:numel(figures),captured{j}=figure_layout(figures(j));end
  layouts.stability.(name)=captured;
 catch err
  records.(name)=struct('success',false,'error',err.message,'identifier',err.identifier);
 end
 close all;
 disp(['Native stability case finished: ' name]);
end
sTag='_native_q17';
try
 guiFracPaQ2Dtracemap(make_traces([0 90]),0,0,false,false,false,[0 0 1],false,...
  false,true,false,false,false,false,100,50,30,false,false,2,10,.6);
 records.rotated_orthogonal=struct('success',true);
catch err
 records.rotated_orthogonal=struct('success',false,'error',err.message,'identifier',err.identifier);
end
close all;
for item=1:3
 flags=false(1,4);s1=100;s2=50;mu=.6;C0=2;pf=10;
 if item==1,name='zero_friction_susceptibility';flags(3)=true;mu=0;
 elseif item==2,name='equal_stress_dilation';flags(2)=true;s2=100;
 else,name='equality_csf';flags(4)=true;s2=100;mu=0;C0=0;pf=0;end
 sTag=['_native_' name];
 try
  guiFracPaQ2Dtracemap(make_traces([0 90]),0,0,false,false,false,[0 0 1],false,...
   false,flags(1),flags(2),false,false,false,s1,s2,30,flags(3),flags(4),C0,pf,mu);
  records.(name)=struct('success',true);
 catch err
  records.(name)=struct('success',false,'error',err.message,'identifier',err.identifier);
 end
 close all;
end
records.version=version;
fid=fopen(fullfile(out11,'native_calls.json'),'w');fwrite(fid,jsonencode(records));fclose(fid);
fid=fopen(fullfile(out11,'layout.json'),'w');fwrite(fid,jsonencode(layouts.stability));fclose(fid);
disp('Native Sprints 10/11 capture completed.');

function traces=make_traces(angles)
 traces=struct;
 for k=1:numel(angles)
  start=[k/4,k/8];finish=start+2*[sind(angles(k)),cosd(angles(k))];
  traces(k).nNodes=2;traces(k).nSegments=1;
  traces(k).Node(1).x=start(1);traces(k).Node(1).y=start(2);
  traces(k).Node(2).x=finish(1);traces(k).Node(2).y=finish(2);
  traces(k).Segment(1).Point1=start;traces(k).Segment(1).Point2=finish;
  traces(k).segmentLength=2;traces(k).totalLength=2;traces(k).segmentAngle=angles(k);
 end
end

function result=figure_layout(f)
 ax=findall(f,'Type','polaraxes');
 if isempty(ax),ax=findall(f,'Type','axes');end
 ax=ax(1);
 result=struct('position',ax.Position,'units',ax.Units,'font',ax.FontName,...
  'font_size',ax.FontSize,'line_width',ax.LineWidth,'grid_colour',ax.GridColor,...
  'grid_alpha',ax.GridAlpha,'title',char(join(string(ax.Title.String),newline)),...
  'title_font_size',ax.Title.FontSize,'figure_position',f.Position,...
  'paper_units',f.PaperUnits,'paper_position',f.PaperPosition);
 if isprop(ax,'RLim')
  result.radial_limits=ax.RLim;result.radial_ticks=ax.RTick;
  result.radial_axis_location=ax.RAxisLocation;
  result.theta_zero=ax.ThetaZeroLocation;result.theta_direction=ax.ThetaDir;
 else
  result.x_limits=ax.XLim;result.y_limits=ax.YLim;
  result.data_aspect=ax.DataAspectRatio;result.plot_box_aspect=ax.PlotBoxAspectRatio;
 end
 lgd=findall(f,'Type','legend');
 if ~isempty(lgd),result.legend_position=lgd(1).Position;result.legend_font_size=lgd(1).FontSize;end
end
