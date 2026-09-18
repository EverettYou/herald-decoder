#!/usr/bin/env python3
"""Paired directed/hidden-orientation acquisition with an explicit ternary batch path."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from time import monotonic
import numpy as np
import pymatching
from numba import njit
import run_a7_ler as directed
from artifact_backend import _cached_decoder
from numba_fusion_decoder import (
    GROUP_IRREPS, GeneralizedSyndrome, UndirectedFusionBeliefMatchingDecoder,
    _infer_undirected_inplace, group_fusion_distribution,
)

LAB=Path(__file__).resolve().parents[1]

@njit(cache=True,fastmath=True)
def infer_ternary_batch(m,labels,bank,factor_dirs,factor_degrees,edge_dirs,edge_degrees,p,max_iterations,damping,tolerance):
    count=m.shape[0];directions=int(np.sum(factor_degrees))
    outputs=np.empty((count,edge_dirs.shape[0]),dtype=np.float64)
    convergence=np.empty(count,dtype=np.uint8);iterations=np.empty(count,dtype=np.int64);residuals=np.empty(count,dtype=np.float64)
    variable=np.empty((directions,3));factors=np.empty((directions,3));updated_variable=np.empty((directions,3));updated_factors=np.empty((directions,3))
    for sample in range(count):
        convergence[sample],iterations[sample],residuals[sample]=_infer_undirected_inplace(
            m[sample],labels[sample],bank,factor_dirs,factor_degrees,edge_dirs,edge_degrees,p,max_iterations,damping,tolerance,
            variable,factors,updated_variable,updated_factors,outputs[sample])
    return outputs,convergence,iterations,residuals


def infer_hidden_batch(decoder,m,labels):
    return infer_ternary_batch(m,labels,decoder.bank,decoder.factor_dirs,decoder.factor_degrees,
                              decoder.edge_dirs,decoder.edge_degrees,decoder.p,decoder.max_iterations,decoder.damping,decoder.tolerance)


def record_tables(graph,boundary_rows,group):
    incident=graph.incident;max_degree=max(map(len,incident));codes={label:i for i,label in enumerate(GROUP_IRREPS[group])}
    edges=np.zeros((len(incident),max_degree),dtype=np.int64);degrees=np.array([len(x) for x in incident],dtype=np.int64)
    boundary=np.zeros(len(incident),dtype=np.uint8);boundary[list(boundary_rows)]=1
    cdf=np.ones((len(incident),3**max_degree,len(codes)),dtype=np.float64);labels=np.zeros(cdf.shape,dtype=np.int8)
    for vertex,leaves in enumerate(incident):
        for j,(edge,rep) in enumerate(leaves):edges[vertex,j]=edge
        for configuration in range(3**len(leaves)):
            value=configuration;active=[]
            for edge,rep in leaves:
                state=value%3;value//=3
                if state:active.append('fund' if (rep=='3')==(state==1) else 'anti')
            channel={directed.TRIVIAL[group]:1.0} if boundary[vertex] else group_fusion_distribution(group,tuple(active))
            cumulative=0.
            for output,(label,probability) in enumerate(channel.items()):
                cumulative+=probability;cdf[vertex,configuration,output]=cumulative;labels[vertex,configuration,output]=codes[label]
            labels[vertex,configuration,len(channel):]=codes[label]
    return edges,degrees,boundary,cdf,labels

@njit(cache=True)
def generate_hidden_records(errors,reverse,uniforms,edges,degrees,boundary,cdf,codes):
    count,vertices=uniforms.shape;m=np.zeros((count,vertices),dtype=np.uint8);labels=np.empty((count,vertices),dtype=np.int8)
    for sample in range(count):
        for vertex in range(vertices):
            configuration=0;base=1;active=0
            for position in range(degrees[vertex]):
                edge=edges[vertex,position]
                if errors[sample,edge]:configuration+=base*(1+reverse[sample,edge]);active+=1
                base*=3
            if not boundary[vertex]:m[sample,vertex]=active&1
            selected=codes[vertex,configuration,-1]
            for output in range(codes.shape[2]):
                if uniforms[sample,vertex]<=cdf[vertex,configuration,output]:selected=codes[vertex,configuration,output];break
            labels[sample,vertex]=selected
    return m,labels


def decoder_for(graph,boundary,group,p,orientation):
    return _cached_decoder(graph,group=group,orientation_mode=orientation,use_irrep=True,p=p,damping=.5,
                           boundary_factor_rows=boundary,measure_boundary_representation=False,algorithm='sum_product')


def matching_failures(model,m,detector_rows,errors,marginals):
    assert np.all(np.isfinite(marginals)) and np.all((marginals>=0)&(marginals<=1))
    flags=np.zeros(len(errors),dtype=np.uint8);invalid=0
    matrix=model.check_matrix
    for sample in range(len(errors)):
        beliefs=np.clip(marginals[sample],1e-12,1-1e-12)
        matching=pymatching.Matching.from_check_matrix(matrix,weights=np.log((1-beliefs)/beliefs))
        syndrome=m[sample,detector_rows];correction=matching.decode(syndrome).astype(np.uint8)
        residual=syndrome^(np.asarray(matrix@correction).ravel().astype(np.uint8)&1)
        invalid+=int(np.any(residual));flags[sample]=directed.final_decoder_failure(residual,bool(model.logical_parity(errors[sample]^correction)))
    assert invalid==0,'Matching correction left nonzero measured syndrome'
    return flags


def run_cell(lattice,group,size,p,shots,seed,batch_size=256,save_path=None):
    start=monotonic();model,graph,detector_rows,boundary=directed.context(lattice,size)
    fixed=decoder_for(graph,boundary,group,p,'directed')
    hidden=decoder_for(graph,boundary,group,p,'undirected') if group!='SU2' else fixed
    fixed_tables=directed._record_tables(graph,boundary,group);hidden_tables=record_tables(graph,boundary,group)
    rng=np.random.default_rng(seed);orientation_rng=np.random.default_rng(seed+10000000)
    failures=np.zeros((2,shots),dtype=np.uint8);nonconvergence=np.zeros((2,shots),dtype=np.uint8)
    iteration_sum=np.zeros(2,dtype=np.int64);max_residual=np.zeros(2)
    hashes={name:hashlib.sha256() for name in ('activity','m','directed_R','hidden_R','orientation')}
    active_forward=0;active_reverse=0
    for begin in range(0,shots,batch_size):
        count=min(batch_size,shots-begin)
        errors=(rng.random((count,len(graph.edges)))<p).astype(np.uint8)
        uniforms=rng.random((count,len(graph.vertices)))
        reverse=(orientation_rng.random(errors.shape)<.5).astype(np.uint8)
        active_reverse+=int(np.sum(errors*reverse));active_forward+=int(np.sum(errors*(1-reverse)))
        m,fixed_labels=directed._generate_records_numba(errors,uniforms,*fixed_tables)
        mh,hidden_labels=generate_hidden_records(errors,reverse,uniforms,*hidden_tables)
        assert np.array_equal(m,mh)
        for name,values in [('activity',errors),('m',m),('directed_R',fixed_labels),('hidden_R',hidden_labels),('orientation',reverse)]:hashes[name].update(values.tobytes())
        db=fixed.infer_batch(m,fixed_labels)
        if group=='SU2':
            assert np.array_equal(fixed_labels,hidden_labels),'SU2 channel depends on hidden orientation'
            # Exact quotient of the physically redundant active orientations.
            hb=fixed.infer_batch(m,hidden_labels)
        else:hb=infer_hidden_batch(hidden,m,hidden_labels)
        for arm,bp in enumerate((db,hb)):
            marginals,converged,iterations,residual=bp
            assert np.all(np.isfinite(residual))
            failures[arm,begin:begin+count]=matching_failures(model,m,detector_rows,errors,marginals)
            nonconvergence[arm,begin:begin+count]=1-converged
            iteration_sum[arm]+=int(np.sum(iterations));max_residual[arm]=max(max_residual[arm],float(np.max(residual)))
    if group=='SU2':assert np.array_equal(failures[0],failures[1]) and np.array_equal(nonconvergence[0],nonconvergence[1])
    joint=np.bincount(2*failures[0]+failures[1],minlength=4).reshape(2,2)
    result={'lattice':lattice,'group':group,'L':size,'p':p,'shots':shots,'seed':seed,'orientation_seed':seed+10000000,'batch_size':batch_size,
            'scoring_rule':directed.SCORING_RULE,'joint_failures_directed_by_hidden':joint.tolist(),
            'truth_and_record_sha256':{k:v.hexdigest() for k,v in hashes.items()},
            'active_forward':active_forward,'active_reverse':active_reverse,
            'elapsed_seconds':monotonic()-start,'arms':{}}
    for arm,name in enumerate(('directed','hidden_orientation')):
        k=int(failures[arm].sum());result['arms'][name]={'logical_failures':k,'ler':k/shots,'wilson95':list(directed.wilson(k,shots)),
            'invalid_correction':0,'bp_nonconverged':int(nonconvergence[arm].sum()),'mean_iterations':float(iteration_sum[arm]/shots),'max_terminal_delta':float(max_residual[arm])}
    if save_path:
        path=Path(save_path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp.npz')
        np.savez_compressed(temp,failures=np.packbits(failures,axis=1),bp_nonconverged=np.packbits(nonconvergence,axis=1),shots=shots,seed=seed,orientation_seed=seed+10000000)
        temp.replace(path);result['shot_indicators_path']=str(path.relative_to(LAB));result['shot_indicators_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return result
