"""Independent GF(2) coset enumeration at L=3,4, using audit adapters."""
from pathlib import Path
exec(Path(__file__).with_name('audit_run.py').read_text().split('g=build(2);')[0])
rng=np.random.default_rng(853923)
for L,n in [(3,15),(4,8)]:
    g=build(L);_,edges,ds,H,mask=arrays(g)
    A=H.copy();piv=[];row=0
    for col in range(A.shape[1]):
        ix=np.flatnonzero(A[row:,col])
        if not len(ix):continue
        j=row+ix[0];A[[j,row]]=A[[row,j]]
        other=np.flatnonzero(A[:,col]);other=other[other!=row];A[other]^=A[row]
        piv.append(col);row+=1
        if row==A.shape[0]:break
    free=[j for j in range(A.shape[1]) if j not in piv]
    B=np.zeros((len(free),A.shape[1]),np.uint8)
    for i,j in enumerate(free):B[i,j]=1;B[i,piv]=A[:row,j]
    K=((np.arange(2**len(free))[:,None]>>np.arange(len(free)))&1).astype(np.uint8)@B%2
    rec={'L':L,'observations':n,'coset_size':len(K),'invalid':0,'nonoptimal_logical':0,'nonMAP_sector':0,'max_posterior_abs_error':0.}
    if 'opus' in model:
        if run=='run_01':
            from decoder_api import decode_with_info
            def post(s,h,p,q):
                c,info=decode_with_info(g,p,q,s,h)
                v=info['posterior'];return v if int(c@mask)%2==0 else 1-v
        elif run=='run_02':
            pd=HeraldedMLDecoder(g,use_cache=False)
            def post(s,h,p,q):
                c,v=pd.class_posterior(p,q,s,h);return v if int(c@mask)%2==0 else 1-v
        else:
            pd=MLDecoder(g)
            def post(s,h,p,q):
                c,v=pd.posterior(p,q,s,h);return 1-v if int(c@mask)%2==0 else v
    elif 'fable' in model and run=='run_03':
        from decoder import class_log_weights
        def post(s,h,p,q):
            z0,z1=class_log_weights(g,p,q,s,h);return np.asarray(1/(1+np.exp(z1-z0))).item()
    else:post=None
    for i in range(n):
        p,q=[(.2,.5),(.4,.9),(.5,1)][i%3];x=(rng.random(len(edges))<p).astype(np.uint8)
        nn=H@x;s=nn%2;h=((nn>=2)&(rng.random(len(ds))<q)).astype(np.uint8)
        X=K^x;counts=X@H.T;eligible=counts>=2;wt=X.sum(1)
        w=p**wt*(1-p)**(len(edges)-wt)*np.prod(np.where(h,np.where(eligible,q,0),np.where(eligible,1-q,1)),axis=1)
        logical=X@mask%2;mass=np.bincount(logical,weights=w,minlength=2)
        if post is not None:rec['max_posterior_abs_error']=max(rec['max_posterior_abs_error'],abs(post(s,h,p,q)-mass[0]/sum(mass)))
        c=np.asarray(decoder(g,p,q)(s,h));valid=c.shape==(len(edges),) and np.all((c==0)|(c==1)) and np.array_equal(H@c%2,s)
        if not valid:rec['invalid']+=1;continue
        decision=int(c@mask%2);best=[w[logical==j].max() for j in [0,1]]
        rec['nonoptimal_logical']+=int(mass[decision]+1e-10*sum(mass)<max(mass))
        rec['nonMAP_sector']+=int(best[decision]+1e-10*max(best)<max(best))
    result['tests'].append(rec);print(rec,flush=True)
(ROOT/'output/scicode2/run_evaluation'/f'{model}_{run}_larger.json').write_text(json.dumps(result,indent=2)+'\n')
