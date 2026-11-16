"""Analytic trace topology, native hist3 convention, provenance and empty classes."""

import json
from dataclasses import replace

import numpy as np
import pytest

from pyfracpaq.analysis.connectivity import classify_connectivity,connectivity_maps,node_histogram
from pyfracpaq.domain import TraceInput,build_dataset
from pyfracpaq.geometry import Bounds,GeometryError
from pyfracpaq.io.connectivity import export_connectivity
from reference_common import ROOT

DOMAIN=Bounds(-3,-3,3,3)


def dataset(points,domain=DOMAIN):
    return build_dataset([TraceInput(tuple(map(tuple,p))) for p in points],source_bounds=domain)


@pytest.mark.parametrize('gap,tolerance,counts',[
    (0,0,(3,1,0)),(.1,.2,(3,1,0)),(-.1,.2,(3,1,0)),
    (.2,.2,(3,1,0)),(np.nextafter(.2,1),.2,(4,0,0)),
    (-.1,0,(4,0,1)),(-2,0,(4,0,1)),
])
def test_tee_undershoot_overshoot_cross_and_exact_tolerance_boundary(gap,tolerance,counts):
    data=dataset([[[-2,0],[2,0]],[[0,gap],[0,2]]])
    before=data.as_arrays().segment_coordinates.copy()
    result=classify_connectivity(data,tolerance)
    assert result.counts==counts
    np.testing.assert_array_equal(data.as_arrays().segment_coordinates,before)
    if gap==.1 and tolerance==.2:
        assert len(result.snaps)==1
        assert result.snaps[0].original==(0,.1) and result.snaps[0].junction==(0,0)
        assert result.y_nodes.trace_ids==((0,1),)


def test_no_intersections_isolated_and_closed_trace_return_complete_empty_arrays():
    single=classify_connectivity(dataset([[[-1,0],[1,0]]]),.2)
    assert single.counts==(2,0,0)
    assert single.x_nodes.coordinates.shape==single.y_nodes.coordinates.shape==(0,2)
    parallel=classify_connectivity(dataset([[[-2,-1],[2,-1]],[[-2,1],[2,1]]]),.2)
    assert parallel.counts==(4,0,0)
    closed=classify_connectivity(dataset([[[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]]]),.2)
    assert closed.counts==(0,0,0)


def test_internal_polyline_vertex_is_not_a_trace_endpoint_and_duplicates_keep_provenance():
    points=[[[-2,0],[0,0],[2,0]],[[0,-2],[0,2]]]
    result=classify_connectivity(dataset(points),.2)
    assert result.counts==(4,0,1)
    assert result.exact_pair_intersections==2
    assert result.x_nodes.segment_ids==(((0,0),(0,1),(1,0)),)
    duplicate=classify_connectivity(dataset([[[-2,0],[2,0]],[[-2,0],[2,0]],[[0,-2],[0,2]]]),0)
    assert duplicate.counts==(4,0,1) and duplicate.overlap_pairs==1
    assert duplicate.x_nodes.trace_ids==((0,1,2),)


def test_self_crossings_are_not_intertrace_junctions():
    result=classify_connectivity(dataset([[[-2,-2],[2,2],[-2,2],[2,-2]]]),0)
    assert result.counts==(2,0,0)


def test_border_exclusion_is_exact_and_only_affects_i_nodes():
    result=classify_connectivity(dataset([[[-3,0],[3,0]],[[0,0],[0,3]]]),0)
    assert result.counts==(0,1,0)
    maps=connectivity_maps(result,3)
    assert maps.xy_heatmap.values.sum()==1 and maps.i_heatmap.values.sum()==0
    assert maps.maximum==1


@pytest.mark.parametrize('scale', [1,2,1e10])
def test_translation_and_physical_scaling_preserve_node_classes(scale):
    points=np.array([[[-2,0],[2,0]],[[0,.1],[0,2]]])+[100,-80]
    data=dataset(points,Bounds(97,-83,103,-77)).with_scale(scale)
    got=classify_connectivity(data,.2/scale)
    assert got.counts==(3,1,0)
    np.testing.assert_allclose(got.y_nodes.coordinates,[[100/scale,-80/scale]],rtol=1e-10,atol=1e-12)


def test_heatmaps_match_native_bin_edges_constant_ranges_and_matrix_orientation():
    native=json.loads((ROOT/'tests/reference/sprint8/native_ks_hist.json').read_text())
    histogram=node_histogram([[0,0],[1,1],[2,2]],2,2,DOMAIN)
    np.testing.assert_array_equal(histogram.values,np.asarray(native['hist_counts']).T)
    np.testing.assert_array_equal(histogram.x,native['hist_centres_x'])
    constant=node_histogram([[2,3],[2,3]],3,4,Bounds(-10,-10,10,10))
    np.testing.assert_array_equal(constant.values,np.asarray(native['constant_counts']).T)
    np.testing.assert_array_equal(constant.x,native['constant_x'])
    np.testing.assert_array_equal(constant.y,native['constant_y'])
    assert not constant.values.flags.writeable


def test_grid_aspect_counts_and_empty_classes():
    data=dataset([[[-1,0],[1,0]]],Bounds(-6,-3,6,3))
    result=connectivity_maps(classify_connectivity(data),3)
    assert result.i_heatmap.values.shape==(3,6)
    assert result.i_heatmap.values.sum()==2
    assert not result.xy_heatmap.values.any()
    assert result.maximum==int(result.i_heatmap.values.max())
    with pytest.raises((GeometryError,MemoryError)):connectivity_maps(result.topology,100000)


def test_count_file_source_order_blank_tag_and_other_files_preserved(tmp_path):
    keep=tmp_path/'unrelated.txt';keep.write_text('keep')
    path=export_connectivity((3,1,2),'',tmp_path)
    assert path.name=='FracPaQ2Dconnectivity_.txt'
    assert path.read_bytes()==b'I 3\nX 2\nY 1\n'
    export_connectivity((0,0,0),'',tmp_path)
    assert keep.read_text()=='keep' and path.read_text()=='I 0\nX 0\nY 0\n'


def test_topology_cancellation_never_returns_partial_success():
    with pytest.raises(InterruptedError):
        classify_connectivity(dataset([[[-1,0],[1,0]]]),interrupted=lambda:True)
