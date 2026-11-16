% Genuine original-source executions for the user-selected SD11A.txt.
% This script neither edits originals nor creates references with Python.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'fracpaq-matlab'));
base=fullfile(root,'tests/reference/sprint16/sd11a');p=jsondecode(fileread(fullfile(base,'parameters.json')));
out=fullfile(base,'native');if ~exist(out,'dir'),mkdir(out);end;cd(out);
set(groot,'DefaultFigureVisible','off');set(groot,'DefaultAxesFontName','Arial');
set(groot,'DefaultTextFontName','Arial');global sTag;sTag=['_' p.tag];
native_version=version;rng(p.mle_seed_matlab,'twister');calls=struct;
figure;[traces,xmin,ymin,xmax,ymax]=guiFracPaQ2Dlist(fullfile(root,p.input),0,gca,[0 0 1]);close all;
geometry=geometry_data(traces);save('geometry.mat','geometry','native_version','-v7');
lengths=[traces.segmentLength];raw=[traces.segmentAngle];total=[traces.totalLength];
core=struct;core.angles=doubleAngles(raw',p.north);core.angle_centres=linspace(0,360,p.angle_bins+1);
core.angle_frequencies=hist(core.angles,core.angle_centres);
for subject={'trace','segment'}
 subject=subject{1};x=lengths;if strcmp(subject,'trace'),x=total;end
 centres=min(x):(max(x)-min(x))/p.length_bins:max(x);frequency=hist(x,centres);
 core.([subject '_histogram'])=struct('centres',centres,'frequencies',frequency);
 centres=min(x):1:max(x);frequency=hist(x,centres);
 core.([subject '_complementary'])=struct('centres',centres,'frequencies',frequency,'complementary',numel(x)-cumsum(frequency));
end
area=(xmax-xmin)*(ymax-ymin);poles=round(raw+90-p.north);
[core.F2,core.polar2]=getF2tensor(lengths,poles,area);
[core.F4,core.polar4]=getF4tensor(lengths,poles,area);
[core.F8,core.polar8]=getF8tensor(lengths,poles,area);core.F0=sum(lengths.^2)/area;
% Supplied permeability equations, including the raw-angle pole convention.
pole=raw+90-p.north;P=zeros(2);apertures=ones(size(lengths))*p.fixed_aperture;
for k=1:numel(lengths)
 n=[cosd(pole(k));sind(pole(k))];P=P+apertures(k)^3*lengths(k)*(n*n')/area;
end
K=p.lambda/12*(trace(P)*eye(2)-P);alpha=0:2*pi/360:2*pi;
polar=K(1,1)*cos(alpha).^2+2*K(1,2)*cos(alpha).*sin(alpha)+K(2,2)*sin(alpha).^2;
core.permeability=struct('p',P,'k',K,'polar',polar,'apertures',apertures,'area',area);
save('core.mat','core','native_version','-v7');
calls.maps=family('maps',@() guiFracPaQ2Dtracemap(traces,0,p.north,p.show_nodes,false,false,[0 0 1],false,...
 true,false,false,true,true,true,p.sigma1,p.sigma2,p.stress_azimuth,false,false,p.cohesion,p.pore_pressure,p.friction));
calls.lengths=family('lengths',@() guiFracPaQ2Dlength(traces,0,p.north,p.length_bins,...
 true,true,true,false,false,false,false,false,[0 0 1],p.lower_cut,p.upper_cut,false));
calls.angles=family('angles',@() guiFracPaQ2Dangle(traces,p.north,p.angle_bins,p.rose_bins,...
 true,true,false,false,true,p.rose_weighted,p.rose_mean,p.rose_colour,[0 0 1]));
calls.mle=family('mle',@() guiFracPaQ2Dlength(traces,0,p.north,p.length_bins,...
 false,false,false,true,false,false,false,false,[0 0 1],p.lower_cut,p.upper_cut,false));
calls.circular=family('circular',@() guiFracPaQ2Dpattern(traces,0,p.blocks,...
 true,true,false,p.show_circles,p.circles,false,false,[0 0 1],p.tolerance));
calls.connectivity=family('connectivity',@() guiFracPaQ2Dpattern(traces,0,p.blocks,...
 false,false,true,false,p.circles,false,false,[0 0 1],p.tolerance));
calls.permeability=family('permeability',@() guiFracPaQ2Dtensor(traces,p.north,p.lambda,...
 false,false,p.fixed_aperture,0,0,0,[0 0 1]));
for k=1:4
 names={'slip','dilation','susceptibility','csf'};name=names{k};
 calls.(name)=family(name,@() stability_original(traces,p,k));
end
calls.blocks=family('blocks',@() guiFracPaQ2Dlength(traces,0,p.north,p.length_bins,...
 false,false,false,false,false,true,false,false,[0 0 1],p.lower_cut,p.upper_cut,false));
calls.variogram=family('variogram',@() guiFracPaQ2Dlength(traces,0,p.north,p.length_bins,...
 false,false,false,false,false,false,false,false,[0 0 1],p.lower_cut,p.upper_cut,true));
calls.graphs=family('graphs',@() guiFracPaQ2Dgraphs(traces,0,p.graph_x',p.graph_y',[0 0 1],...
 p.graph_circles,false,false,true,true,true,true,true,true,true,true));
% Save a checkpoint before the full integrated primary wavelet function.
write_calls(calls,p,native_version);
% Match guiFracPaQ2D.m:1394: the GUI inverts the entered factors first.
calls.wavelets=family('wavelets',@() guiFracPaQ2Dwavelet(traces,p.wavelet_a',1./p.wavelet_L',...
 p.wavelet_step,p.wavelet_morlet,[0 0 1],false,false));
write_calls(calls,p,native_version);
disp('SD11A original-source comparisons captured.');

function stability_original(traces,p,k)
 flags=false(1,4);flags(k)=true;
 guiFracPaQ2Dtracemap(traces,0,p.north,false,false,false,[0 0 1],false,...
 false,flags(1),flags(2),false,false,false,p.sigma1,p.sigma2,p.stress_azimuth,...
 flags(3),flags(4),p.cohesion,p.pore_pressure,p.friction);
end

function geometry=geometry_data(traces)
 geometry=struct('node_coordinates',[],'segment_coordinates',[],'segment_lengths',[traces.segmentLength],...
  'raw_angles',[traces.segmentAngle],'trace_lengths',[traces.totalLength],...
  'trace_midpoints',[[traces.midpointX]' [traces.midpointY]'],...
  'segment_midpoints',[],'start_lengths',[],'end_lengths',[],...
  'source_euclidean_lengths',[traces.euclideanLength]);
 for k=1:numel(traces)
  geometry.node_coordinates=[geometry.node_coordinates;[[traces(k).Node.x]' [traces(k).Node.y]']];
  for j=1:traces(k).nSegments
   seg=traces(k).Segment(j);
   geometry.segment_coordinates=[geometry.segment_coordinates;seg.Point1(:)' seg.Point2(:)'];
   geometry.segment_midpoints=[geometry.segment_midpoints;seg.midpointX seg.midpointY];
   geometry.start_lengths=[geometry.start_lengths;seg.startLength];
   geometry.end_lengths=[geometry.end_lengths;seg.endLength];
  end
 end
end

function record=family(name,operation)
 start=tic;close all;
 try
  operation();record=struct('success',true);
 catch err
  record=struct('success',false,'identifier',err.identifier,'error',err.message,'stack',err.stack);
  disp(['Native ' name ' failed: ' err.message]);
 end
 figures=findall(groot,'Type','figure');[~,order]=sort([figures.Number]);figures=figures(order);
 figures_data=cell(1,numel(figures));
 for k=1:numel(figures),figures_data{k}=capture_figure(figures(k));end
 save([name '_figures.mat'],'figures_data','-v7');
 record.seconds=toc(start);record.figures=numel(figures);close all;
 disp(['SD11A native family finished: ' name]);
end

function data=capture_figure(fig)
 data=struct('position',fig.Position,'paper_position',fig.PaperPosition,'axes',{{}},'colourbars',{{}});
 axes=[findall(fig,'Type','axes');findall(fig,'Type','polaraxes')];
 for j=1:numel(axes)
  ax=axes(j);entry=struct('type',ax.Type,'title',{ax.Title.String},'position',ax.Position,...
   'font_name',ax.FontName,'font_size',ax.FontSize,'lines',{{}},'images',{{}},'bars',{{}},'patches',{{}});
  for property={'XLim','YLim','XTick','YTick','XTickLabel','YTickLabel','XLabel','YLabel'}
   name=property{1};if isprop(ax,name)
    if contains(name,'Label') && any(strcmp(name,{'XLabel','YLabel'})),entry.(name)=ax.(name).String;
    else,entry.(name)=ax.(name);end
   end
  end
  objects=findall(ax,'Type','line');
  for i=1:numel(objects)
   object=objects(i);line=struct('colour',object.Color,'linewidth',object.LineWidth,'marker',object.Marker,...
     'point_count',numel(object.XData));
   if numel(object.XData)>10000 && object.LineWidth==.25
    line.coordinates_omitted='Dense decorative rose circle only; no scientific observations resampled.';
   else,line.x=object.XData;line.y=object.YData;end
   entry.lines{end+1}=line;
  end
  objects=findall(ax,'Type','image');
  for i=1:numel(objects),object=objects(i);entry.images{end+1}=struct('x',object.XData,'y',object.YData,'values',object.CData);end
  objects=findall(ax,'Type','bar');
  for i=1:numel(objects),object=objects(i);entry.bars{end+1}=struct('x',object.XData,'y',object.YData,'width',object.BarWidth);end
  objects=findall(ax,'Type','patch');
  for i=1:numel(objects),object=objects(i);entry.patches{end+1}=struct('x',object.XData,'y',object.YData,'colour',object.FaceColor);end
  data.axes{end+1}=entry;
 end
 bars=findall(fig,'Type','colorbar');
 for j=1:numel(bars)
  bar=bars(j);data.colourbars{end+1}=struct('position',bar.Position,'limits',bar.Limits,...
   'ticks',bar.Ticks,'labels',{bar.TickLabels},'label',{bar.Label.String});
 end
end

function write_calls(calls,parameters,native_version)
 record=struct('native_version',native_version,'parameters',parameters,'calls',calls);
 fid=fopen('native_calls.json','w');fwrite(fid,jsonencode(record));fclose(fid);
end
