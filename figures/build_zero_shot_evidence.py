"""Build paired reading transitions and complete source-group effects."""
from pathlib import Path
import csv
import gzip
import json
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/figure_inputs_shared_full_20260911'
OUT = Path(__file__).resolve().parent
METHODS = ['resnet18','efficientnet_b0','mobilenet_v3_large','yolo','vdn','deeplab']
NAMES = ['Raw ResNet-18','Raw EfficientNet-B0','Raw MobileNetV3-L','YOLO','VDN','DeepLab']
COLORS = ['#657587','#929EAB','#B3BDC7','#7563A8','#168A82','#B17645']
MARKERS = ['o','s','^','D','P','X']
SEEDS = ['20262020','20262021','20262022']
DATASETS = [('rf100','RF100-VL',35),('industrial','Industrial-1395',52)]
INK = '#233244'
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
 'font.size':9,'axes.labelsize':9,'axes.titlesize':10,'xtick.labelsize':8,'ytick.labelsize':8,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':INK,'axes.labelcolor':INK,
 'text.color':INK,'xtick.color':INK,'ytick.color':INK,'axes.linewidth':.7,
 'pdf.fonttype':42,'svg.fonttype':'none','legend.frameon':False})


def csv_rows(name):
    with (DATA/name).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


SUMMARY = {(x['family'],x['method'],x['dataset'],x['scope']):x for x in csv_rows('seed_mean_sample_sd.csv')}
PAIRED = {(x['comparison'],x['dataset'],x['scope']):x for x in csv_rows('paired_comparisons.csv')}
with gzip.open(DATA/'details/group_comparisons.csv.gz','rt') as f:
    GROUPS = [x for x in csv.DictReader(f) if x['scope']=='all_conditions' and
              x['comparison'] in ['geoprr_minus_'+m for m in METHODS] and
              x['dataset'] in ['rf100','industrial']]

outcomes={}
source=[]
for ds,_,n_groups in DATASETS:
    records={}
    with gzip.open(DATA/f'details/per_sample/{ds}_main.csv.gz','rt') as f:
        for x in csv.DictReader(f):
            if x['method'] not in METHODS+['geoprr']:
                continue
            key=(x['seed'],x['sample_id'],x['condition'])
            records.setdefault(x['method'],{})[key]=(x['status']=='success' and float(x['normalized_absolute_error'])<=.05)
    count=len(records['geoprr'])
    assert count == (151 if ds=='rf100' else 1395)*6*3
    for m in METHODS:
        assert records[m].keys()==records['geoprr'].keys()
        per_seed=defaultdict(lambda:[0,0,0])
        for key, ours in records['geoprr'].items():
            theirs=records[m][key];a=per_seed[key[0]]
            a[0]+=1;a[1]+=int(ours and not theirs);a[2]+=int(theirs and not ours)
        rescue=[100*per_seed[seed][1]/per_seed[seed][0] for seed in SEEDS]
        loss=[100*per_seed[seed][2]/per_seed[seed][0] for seed in SEEDS]
        rr={'recovered':statistics.mean(rescue),'lost':statistics.mean(loss),
            'recovered_sd':statistics.stdev(rescue),'lost_sd':statistics.stdev(loss)}
        expected=float(SUMMARY['main','geoprr',ds,'all_conditions']['acc_at_5_pct_mean'])-float(SUMMARY['main',m,ds,'all_conditions']['acc_at_5_pct_mean'])
        assert abs(rr['recovered']-rr['lost']-expected)<1e-10
        outcomes[ds,m]=rr
        groups=[x for x in GROUPS if x['dataset']==ds and x['comparison']=='geoprr_minus_'+m]
        assert len(groups)==n_groups
        q=PAIRED['geoprr_minus_'+m,ds,'all_conditions']
        weighted_gain=sum(-float(x['candidate_minus_reference_pct_fs'])*int(x['rows_per_seed']) for x in groups)/sum(int(x['rows_per_seed']) for x in groups)
        assert abs(weighted_gain+float(q['candidate_minus_reference_pct_fs']))<1e-10
        source.append({'dataset':ds,'comparator':m,**rr,'net_acc5_gain_pp':expected,
                       'group_count':n_groups,'weighted_nmae_gain_pct_fs':weighted_gain,
                       'gain_ci_low':-float(q['ci95_high_pct_fs']),'gain_ci_high':-float(q['ci95_low_pct_fs'])})

fig,axes=plt.subplots(2,2,figsize=(8.4,7.4),gridspec_kw={'height_ratios':[1,1.05]})
fig.subplots_adjust(left=.20,right=.97,top=.935,bottom=.17,wspace=.28,hspace=.42)
lim=max(v['recovered']+v['recovered_sd'] for v in outcomes.values())
lim=np.ceil(lim/5)*5+5
rng=np.random.default_rng(20260911)

for j,(ds,title,n_groups) in enumerate(DATASETS):
    ax=axes[0,j]
    ax.plot([0,lim],[0,lim],color='#8592A2',lw=.9,ls='--',zorder=0)
    ax.fill_between([0,lim],[0,lim],[lim,lim],color='#EEF4FA',zorder=-1)
    for m,name,color,marker in zip(METHODS,NAMES,COLORS,MARKERS):
        v=outcomes[ds,m]
        ax.errorbar(v['lost'],v['recovered'],xerr=v['lost_sd'],yerr=v['recovered_sd'],
                    fmt=marker,color=color,ms=7.5,elinewidth=.85,capsize=2,
                    markeredgecolor='white',markeredgewidth=.6,zorder=3)
    ax.set(xlim=(0,lim),ylim=(0,lim),xlabel='Lost readings (%)',ylabel='Recovered readings (%)')
    ax.set_aspect('equal',adjustable='box')
    ax.set_title(f'({chr(97+j)}) {title}',loc='left',fontweight='bold',pad=10)
    ax.set_axisbelow(True);ax.grid(color='#DEE5ED',lw=.55)
    ax.set_xticks(np.arange(0,lim+1,10));ax.set_yticks(np.arange(0,lim+1,10))

    ax=axes[1,j]
    ax.axvspan(0,72,color='#EEF4FA',zorder=-2)
    ax.axvline(0,color='#8592A2',lw=.8,ls='--',zorder=-1)
    for k,(m,color) in enumerate(zip(METHODS,COLORS)):
        groups=sorted([x for x in GROUPS if x['dataset']==ds and x['comparison']=='geoprr_minus_'+m],key=lambda x:x['group_id'])
        gains=np.array([-float(x['candidate_minus_reference_pct_fs']) for x in groups])
        violin=ax.violinplot([gains],positions=[k],vert=False,widths=.66,
                              showmeans=False,showmedians=False,showextrema=False,points=150)
        for body in violin['bodies']:
            verts=body.get_paths()[0].vertices
            verts[:,1]=np.minimum(verts[:,1],k)
            body.set_facecolor(color);body.set_edgecolor('none');body.set_alpha(.24)
        jitter=.10+rng.uniform(0,.15,len(gains))
        ax.scatter(gains,k+jitter,s=10,color=color,alpha=.70,linewidths=0,zorder=2)
        q=PAIRED['geoprr_minus_'+m,ds,'all_conditions']
        mean=-float(q['candidate_minus_reference_pct_fs'])
        lo=-float(q['ci95_high_pct_fs']);hi=-float(q['ci95_low_pct_fs'])
        ax.errorbar(mean,k-.07,xerr=[[mean-lo],[hi-mean]],fmt='D',color=INK,
                    ms=4.4,elinewidth=1.5,capsize=2.5,zorder=4)
    ax.set_yticks(range(6),NAMES if j==0 else ['']*6)
    ax.set_ylim(5.65,-.55);ax.set_xlim(-38,72)
    ax.set_xticks([-30,0,30,60]);ax.set_xlabel('Comparator − GeoPRR NMAE (%FS)')
    group_label='source groups' if ds=='rf100' else 'acquisition groups'
    ax.set_title(f'({chr(99+j)}) {n_groups} {group_label}',loc='left',fontweight='bold',pad=10)
    ax.set_axisbelow(True);ax.grid(axis='x',color='#DEE5ED',lw=.55)

handles=[Line2D([0],[0],marker=m,color=c,linestyle='',label=n,markersize=6) for n,c,m in zip(NAMES,COLORS,MARKERS)]
fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.54,.055),ncol=3,
           fontsize=8.5,columnspacing=2.1,handletextpad=.5)
fig.legend(handles=[Line2D([0],[0],marker='D',color=INK,label='Image-weighted mean and 95% CI',markersize=4.4,lw=1.4)],
           loc='lower center',bbox_to_anchor=(.54,.018),fontsize=8.5)
for extension in ['png','pdf','svg']:
    fig.savefig(OUT/f'fig_zero_shot_evidence.{extension}',dpi=300,facecolor='white')
plt.close(fig)
(OUT/'zero_shot_evidence_source.json').write_text(json.dumps(source,indent=2))
(OUT/'zero_shot_evidence_caption.md').write_text('''Zero-shot paired outcomes and source-group effects. All comparisons use the full six-condition main-family rosters and automatic reference geometry. (a,b) Recovered readings are those where the comparator is incorrect and GeoPRR is correct; lost readings reverse these outcomes. Correctness requires a successful reading with absolute error at most 5%FS. Points and whiskers are means and sample standard deviations of the three paired source-seed rates. The diagonal indicates equal recovery and loss. (c,d) Every source group is shown once for each comparator; each dot represents its three-seed mean paired NMAE gain, with positive values favoring GeoPRR. Half-violins describe the unweighted distribution across groups. Dark diamonds and bars show the image-weighted overall gain and the published paired group-bootstrap 95% interval. Group points are descriptive, not individual significance tests.\n''')
print('Saved',OUT/'fig_zero_shot_evidence.png')
print('Verified 12 paired Acc5 balances and 12 weighted group effects')
