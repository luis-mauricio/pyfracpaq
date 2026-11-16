% Resolve the project from this script, independently of the working directory.
root = fileparts(fileparts(mfilename('fullpath')));
out = fullfile(root,'tests','reference','sprint8');
a = [1 1 2 3 5 8]; b = [0 1 2 2 4 9];
[h05,p,d] = kstest2(a,b,'alpha',0.05,'tail','unequal');
[h10,p10,d10] = kstest2(a,b,'alpha',0.1,'tail','unequal');
[N,C] = hist3([0 0; 1 1; 2 2],[2 2]);
[Nconstant,Cconstant] = hist3([2 3;2 3],[3 4]);
[Nempty,Cempty] = hist3(zeros(0,2),[2 3]);
r = struct('matlab_version',version,'method','kstest2, two-sided asymptotic', ...
 'first',a,'second',b,'h05',h05,'h10',h10,'p',p,'distance',d, ...
 'hist_counts',N,'hist_centres_x',C{1},'hist_centres_y',C{2}, ...
 'constant_counts',Nconstant,'constant_x',Cconstant{1},'constant_y',Cconstant{2}, ...
 'empty_counts',Nempty,'empty_x',Cempty{1},'empty_y',Cempty{2});
fid=fopen(fullfile(out,'native_ks_hist.json'),'w');
fwrite(fid,jsonencode(r),'char');fclose(fid);
disp('Native numeric K-S/hist3 reference saved.');
