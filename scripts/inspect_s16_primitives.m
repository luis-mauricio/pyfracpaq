% Inspect renderer properties of an independent mesh, without copying code.
root=fileparts(fileparts(mfilename('fullpath')));
out=fullfile(root,'tests/reference/sprint16/final/native-graphics-details');
set(groot,'DefaultFigureVisible','off');warning('off','MATLAB:structOnObject');
f=figure;[x,y]=meshgrid(0:5,0:4);h=mesh(x,y,reshape(0:29,5,6));view(0,90);drawnow;
value=struct(h);names=fieldnames(value);record=struct('surface_fields',{names},'selected',struct);
for i=1:numel(names)
 name=names{i};
 if contains(lower(name),{'bias','offset','smooth','width','depth'})
  v=value.(name);if isnumeric(v)||islogical(v)||ischar(v),record.selected.(name)=v;end
 end
end
for key={'Face','AlongEdge','AcrossEdge'}
 name=key{1};
 if isfield(value,name)&&isobject(value.(name))
  sub=struct(value.(name));fields=fieldnames(sub);node=struct('fields',{fields},'selected',struct);
  for i=1:numel(fields)
   k=fields{i};
   if contains(lower(k),{'bias','offset','smooth','width','depth','layer'})||ismember(k,{'VertexData','StripData','ColorData','ColorBinding'})
    v=sub.(k);if isnumeric(v)||islogical(v)||ischar(v),node.selected.(k)=v;end
   end
  end
  record.(name)=node;
 end
end
fid=fopen(fullfile(out,'mesh-renderer-properties.json'),'w');fwrite(fid,jsonencode(record));fclose(fid);close(f);
