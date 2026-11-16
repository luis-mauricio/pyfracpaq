% Native FracPaQ/MathWorks comparison only. Does not modify supplied sources.
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'fracpaq-matlab'));
set(groot,'DefaultFigureVisible','off');
set(groot,'DefaultAxesFontName','Arial');
set(groot,'DefaultTextFontName','Arial');
input=load(fullfile(root,'tests/reference/sprint8/shared_ks_inputs.mat'));
models={'power_law','exponential','lognormal'};
ks=struct;
for k=1:numel(models)
 name=models{k}; obs=input.([name '_observed']); draws=input.([name '_draws']);
 stat=zeros(2500,1); p=zeros(2500,1); h=zeros(2500,1); alpha=.05;
 if k==1, alpha=.1; end
 for j=1:2500
  [h(j),p(j),stat(j)]=kstest2(obs,draws(j,:)','alpha',alpha,'tail','unequal');
 end
 ks.(name)=struct('D',stat,'p',p,'h',h,'alpha',alpha);
end
native_version=version;
save(fullfile(root,'tests/reference/sprint8/shared_ks_outputs.mat'),'ks','native_version');
[h05,p,D]=kstest2(1:20,(1:20)+8,'alpha',.05);
[h10,~,~]=kstest2(1:20,(1:20)+8,'alpha',.1);
threshold=struct('first',1:20,'second',(1:20)+8,'p',p,'D',D,'h05',h05,'h10',h10);
fid=fopen(fullfile(root,'tests/reference/sprint8/native/ks_threshold.json'),'w');fwrite(fid,jsonencode(threshold));fclose(fid);
cd(fullfile(root,'tests/reference/sprint8/native'));
rng(77,'twister');
x=input.sample;
fit_records=struct;
for cut=0:1
 uc=10*cut; lc=20*cut; key=['cuts' num2str(cut)];
 try
  [a,xmin,y,z,h,p]=fittingPL(x,uc,lc,[0 0 1]);
  fit_records.(key).power_law=struct('alpha',a,'xmin',xmin,'y',y,'z',z,'H',h,'P',p);
  print(gcf,['power_law_' key '.png'],'-dpng','-r150');close(gcf);
 catch err, fit_records.(key).power_law=struct('error',err.message,'identifier',err.identifier); end
 try
  [lambda,xmin,y,z,h,p]=fittingExponential(x,uc,lc,[0 0 1]);
  fit_records.(key).exponential=struct('lambda',lambda,'xmin',xmin,'y',y,'z',z,'H',h,'P',p);
  print(gcf,['exponential_' key '.png'],'-dpng','-r150');close(gcf);
 catch err, fit_records.(key).exponential=struct('error',err.message,'identifier',err.identifier); end
 try
  [mu,sigma,xmin,y,z,h,p]=fittingLognormal(x,uc,lc,[0 0 1]);
  fit_records.(key).lognormal=struct('mu',mu,'sigma',sigma,'xmin',xmin,'y',y,'z',z,'H',h,'P',p);
  print(gcf,['lognormal_' key '.png'],'-dpng','-r150');close(gcf);
 catch err, fit_records.(key).lognormal=struct('error',err.message,'identifier',err.identifier); end
end
fit_records.version=version;fit_records.input=x;
fid=fopen('native_fits.json','w');fwrite(fid,jsonencode(fit_records));fclose(fid);
cd(fullfile(root,'tests/reference/sprint9/native'));
names={'isolated','tee_zero','tee','cross','undershoot','overshoot','kink_cross'};
records=struct;
for c=1:numel(names)
 name=names{c};
 if strcmp(name,'isolated'), points={[-1 0;1 0]};
 elseif strcmp(name,'kink_cross'), points={[-2 0;0 0;2 0],[0 -2;0 2]};
 else
  gap=0;
  if strcmp(name,'cross'), gap=-2; elseif strcmp(name,'undershoot'), gap=.1; elseif strcmp(name,'overshoot'), gap=-.1; end
  points={[-2 0;2 0],[0 gap;0 2]};
 end
 tolerance=.2;if strcmp(name,'tee_zero'),tolerance=0;end
 traces=struct;segments=[];
 for t=1:numel(points)
  p=points{t};traces(t).nSegments=size(p,1)-1;
  for j=1:size(p,1),traces(t).Node(j).x=p(j,1);traces(t).Node(j).y=p(j,2);end
  segments=[segments; p(1:end-1,:) p(2:end,:)];
 end
 global sTag;sTag=['_native_' name];
 try
  [y,x,i]=getConnectivity(traces,segments,-3,-3,3,3,3,false,false,0,tolerance);
  records.(name)=struct('I',i,'Y',y,'X',x,'tolerance',tolerance);
 catch err, records.(name)=struct('error',err.message,'identifier',err.identifier,'tolerance',tolerance);end
 close all;
end
records.version=version;
fid=fopen('native_topology.json','w');fwrite(fid,jsonencode(records));fclose(fid);
disp('Native Sprint 8/9 references completed.');
