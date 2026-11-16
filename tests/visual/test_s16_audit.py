"""Protect audit decisions against ambiguous references and stale acceptance."""

from types import SimpleNamespace

import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

from audit_s16_semantics import match_native,palette_check
from report_s16_status import visual_acceptances,authorized_marker_propagation


def test_cyclic_palette_ties_preserve_direction_without_hiding_reversal():
    image=np.zeros((16,128,3),dtype=np.uint8)
    for n,colour in enumerate(((255,0,0),(0,128,0),(0,0,255),(255,0,0))):
        image[:,n*32:(n+1)*32]=colour
    bar=SimpleNamespace(orientation='horizontal',cmap=ListedColormap(['red','green','blue','red']))
    result=palette_check(image,bar,[0,0,128,16])
    assert result['passed'] and result['maximum_rgb_distance']==0
    assert result['palette_indices'][-1]==3
    assert not palette_check(image[:,::-1],bar,[0,0,128,16])['passed']


def test_native_block_histogram_is_not_confused_with_ccdf():
    figure=Figure();axis=figure.add_subplot()
    axis.set(title='Block sizes (areas), n=67',xlabel='Block size (area), pixels$^2$',ylabel='Frequency, %')
    index=[{'family':'blocks','index':i,'data':{'axes':{
        'title':'Block sizes (areas), n=65','XLabel':'Block size (area), pixels^2','YLabel':label}}}
        for i,label in enumerate(('Cumulative frequency','Frequency, %'))]
    assert match_native(figure,index,'FracPaQ2D_blocksizehisto_SD11A.png')['index']==1


def test_same_title_map_uses_correct_native_sampling_context():
    figure=Figure();axis=figure.add_subplot()
    axis.set(title='Mapped trace segments, n=1076',xlabel='X, pixels',ylabel='Y, pixels')
    index=[{'family':family,'data':{'axes':{'title':axis.get_title(),
        'XLabel':axis.get_xlabel(),'YLabel':axis.get_ylabel()}}} for family in ('circular','graphs')]
    assert match_native(figure,index,'guiFracPaQ2D_graphtracemap_SD11A.png')['family']=='graphs'
    assert match_native(figure,index,'FracPaQ2D_scancircle_SD11A.png')['family']=='circular'


def test_user_acceptance_requires_current_pair_and_identified_region():
    record={'name':'example.png','native_sha256':'native','candidate_sha256':'current',
            'regions':[{'name':'legend','xyxy':[10,20,30,40],'passed':False}]}
    decision={'figure':'example.png','region':'legend','native_sha256':'native',
              'candidate_sha256':'current','xyxy':[10,20,30,40]}
    accepted,pending=visual_acceptances([record],{'accepted_regions':[decision]})
    assert accepted==[decision] and not pending
    for changed in ({'candidate_sha256':'stale'},{'native_sha256':'stale'},
                    {'region':'title'},{'xyxy':[0,0,30,40]}):
        accepted,pending=visual_acceptances([record],{'accepted_regions':[{**decision,**changed}]})
        assert not accepted and len(pending)==1


def test_accepted_title_does_not_approve_independent_legend():
    common={'native_sha256':'native','candidate_sha256':'candidate'}
    records=[{'name':'example.png',**common,'regions':[{'name':name,'passed':False}]}
             for name in ('title','legend')]
    decisions={'accepted_regions':[{'figure':'example.png','region':'title',**common}]}
    accepted,pending=visual_acceptances(records,decisions)
    assert len(accepted)==1 and [r['name'] for r in pending]==['legend']


def marker_propagation_case():
    name='FracPaQ2D_tracemap_SD11A.png';hashes={'native_sha256':'native','candidate_sha256':'new'}
    record={'name':name,**hashes,'regions':[{'name':'plot','xyxy':[0,0,10,10],'passed':False}]}
    item={'figure':name,'region':'plot',**hashes,'xyxy':[0,0,10,10],
          'passed':True,'prior_gate_satisfied':True,'changed_pixels_outside_marker_footprints':0}
    code={'plots':'current'}
    proof={'passed':True,'implementation':code,'authorized_global_instruction':'normal markers','records':[item]}
    decisions={'renderer_change_authorized':{'user_statement':'normal markers'}}
    accepted=[{'detail_case':n} for n in range(1,17)]
    return record,item,code,proof,decisions,accepted


def test_marker_propagation_requires_final_style_acceptance_and_global_request():
    record,item,code,proof,decisions,accepted=marker_propagation_case()
    assert len(authorized_marker_propagation([record],accepted,decisions,proof,code))==1
    assert not authorized_marker_propagation([record],accepted[:-1],decisions,proof,code)
    assert not authorized_marker_propagation([record],accepted,{},proof,code)
    assert not authorized_marker_propagation([record],accepted,decisions,proof,{'plots':'changed'})


def test_marker_propagation_cannot_hide_nonmarker_changes_or_unrelated_regions():
    record,item,code,proof,decisions,accepted=marker_propagation_case()
    for changed in ({'changed_pixels_outside_marker_footprints':1},
                    {'prior_gate_satisfied':False},{'candidate_sha256':'stale'},
                    {'native_sha256':'stale'},{'xyxy':[1,1,9,9]},
                    {'figure':'unrelated.png'},{'region':'title'}):
        altered={**proof,'records':[{**item,**changed}]}
        assert not authorized_marker_propagation([record],accepted,decisions,altered,code)
