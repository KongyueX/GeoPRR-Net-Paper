"""Plot frozen-reader comparisons and complete-pipeline trade-offs from released results."""
from pathlib import Path
import csv
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
DOMAINS = ['SyncG Scene-Holdout', 'Industrial-1395', 'RF100-VL']
DOMAIN_NAMES = ['SyncG', 'Industrial-1395', 'RF100-VL']
METHODS = ['GeoPRR-Net', 'VDN', 'DeepLabV3+-ROI', 'YOLO11s-Pose-4KP']
SHORT = ['GeoPRR', 'VDN', 'DeepLab', 'YOLO']
COLORS = ['#0F4D92', '#168A82', '#B17645', '#7563A8']
INK = '#1D2A36'
GRID = '#D9E1E7'
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.labelcolor': INK, 'text.color': INK, 'xtick.color': INK, 'ytick.color': INK,
    'axes.edgecolor': '#657482', 'axes.linewidth': .65,
    'legend.frameon': False, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'savefig.facecolor': 'white', 'figure.facecolor': 'white',
})

def read(path):
    with (ROOT / path).open() as f:
        return list(csv.DictReader(f))

def frozen_industrial():
    rows = [r for r in read('data/figure_inputs_20260908/frozen_industrial.csv')
            if r['scope'] == 'all_conditions']
    out = {}
    for method in dict.fromkeys(r['method'] for r in rows):
        chosen = [r for r in rows if r['method'] == method]
        assert len(chosen) == 3
        out[method] = {}
        for field in ['pooled_nmae', 'pooled_acc_at_5_percent', 'pooled_coverage']:
            values = [100 * float(r[field]) for r in chosen]
            out[method][field] = (statistics.mean(values), statistics.stdev(values))
    return out

def structured():
    rows = {(r['domain'], r['method']): r for r in read('data/figure_inputs_20260908/structured.csv')}
    nmae = np.zeros((3, 4)); nsd = np.zeros_like(nmae)
    acc = np.zeros_like(nmae); asd = np.zeros_like(nmae); cov = np.zeros_like(nmae)
    for i, domain in enumerate(DOMAINS):
        for j, method in enumerate(METHODS):
            r = rows[(domain, method)]
            nmae[i,j] = 100*float(r['nmae_mean'])
            nsd[i,j] = 100*float(r['nmae_sample_sd'])
            acc[i,j] = 100*float(r['acc_at_5_mean'])
            asd[i,j] = 100*float(r['acc_at_5_sample_sd'])
            cov[i,j] = 100*float(r['coverage_mean'])
    frozen = frozen_industrial()['GeoPRR-Net']
    nmae[1,0], nsd[1,0] = frozen['pooled_nmae']
    acc[1,0], asd[1,0] = frozen['pooled_acc_at_5_percent']
    cov[1,0] = frozen['pooled_coverage'][0]
    assert nmae.shape == (3,4) and np.isfinite(nmae).all()
    assert np.all(nmae > 0) and abs(nmae[1,0]-10.85073272807019) < 1e-8
    assert np.all((acc >= 0) & (acc <= 100)) and np.all((cov >= 0) & (cov <= 100))
    return nmae, nsd, acc, asd, cov

def save(fig, stem):
    fig.savefig(OUT / f'{stem}.png', dpi=600)
    fig.savefig(OUT / f'{stem}.svg')
    fig.savefig(OUT / f'{stem}.pdf')
    plt.close(fig)

def absolute_comparison():
    nmae, nsd, acc, asd, _ = structured()
    fig, axs = plt.subplots(2, 3, figsize=(7.2, 5.1))
    fig.subplots_adjust(left=.075, right=.985, top=.86, bottom=.09, wspace=.35, hspace=.52)
    for col, name in enumerate(DOMAIN_NAMES):
        for row, (values, spread, ylabel) in enumerate([(nmae, nsd, 'NMAE (%FS)'), (acc, asd, 'Acc@5%')]):
            ax = axs[row,col]
            ax.set_axisbelow(True); ax.grid(axis='y', color=GRID, linewidth=.5)
            ax.bar(range(4), values[col], yerr=spread[col], color=COLORS, width=.68,
                   error_kw={'ecolor': INK, 'elinewidth': .7, 'capsize': 2})
            ymax = float(np.max(values[col]+spread[col]))*1.24 if row==0 else 112
            ax.set_ylim(0,ymax)
            ax.set_xticks(range(4), SHORT)
            ax.tick_params(axis='x',length=0,pad=4)
            ax.set_ylabel(ylabel)
            ax.set_title(f'({chr(97+row*3+col)}) {name}',loc='left',fontweight='bold',pad=8)
            for j,v in enumerate(values[col]):
                ax.text(j,v+spread[col,j]+.032*ymax,f'{v:.2f}' if row==0 else f'{v:.1f}',
                        ha='center',va='bottom',fontsize=6.5,fontweight='bold' if j==0 else 'normal')
            if row==1: ax.set_yticks([0,25,50,75,100])
    fig.suptitle('Frozen source-trained readers across datasets',fontsize=11,fontweight='bold',y=.97)
    fig.text(.5,.912,'Mean ± sample SD across three seeds; complete six-condition rosters',ha='center',fontsize=7)
    save(fig,'fig_structured_frozen_comparison')

def relative_comparison():
    nmae, _, acc, _, cov = structured()
    reductions=100*(nmae[:,1:]-nmae[:,[0]])/nmae[:,1:]
    gains=acc[:,[0]]-acc[:,1:]
    fig, axs = plt.subplots(1,3,figsize=(7.2,3.15))
    fig.subplots_adjust(left=.15,right=.985,top=.74,bottom=.27,wspace=.30)
    mats=[reductions,gains,cov]
    titles=['(a) NMAE reduction','(b) Acc@5% gain','(c) Valid outputs']
    units=['Relative reduction (%)','Gain (percentage points)','Coverage (%)']
    for i,(ax,mat) in enumerate(zip(axs,mats)):
        vmax=100 if i in (0,2) else max(1,float(gains.max())*1.05)
        im=ax.imshow(mat,cmap='Blues',vmin=0,vmax=vmax,aspect='auto')
        ax.set_title(titles[i],loc='left',fontweight='bold',pad=10)
        names=SHORT[1:] if i<2 else SHORT
        ax.set_xticks(range(len(names)),names,rotation=30,ha='right',rotation_mode='anchor')
        ax.set_yticks(range(3),DOMAIN_NAMES if i==0 else ['']*3)
        ax.tick_params(length=0)
        for row in range(3):
            for col in range(mat.shape[1]):
                value=mat[row,col]
                ax.text(col,row,f'{value:.1f}',ha='center',va='center',fontsize=7,
                        color='white' if value/vmax>.55 else INK,fontweight='bold')
        cb=fig.colorbar(im,ax=ax,orientation='horizontal',fraction=.10,pad=.38,aspect=20)
        cb.ax.tick_params(labelsize=6);cb.set_label(units[i],fontsize=6.5,labelpad=2)
    fig.suptitle('Size of improvement and valid-reading coverage',fontsize=11,fontweight='bold',y=.965)
    fig.text(.5,.86,'Descriptive effects from three-seed means; Industrial-1395 uses frozen GeoPRR-Net',ha='center',fontsize=7)
    save(fig,'fig_structured_frozen_advantage')

def efficiency():
    frozen=frozen_industrial()
    geoprr=next(r for r in read('data/figure_inputs_shared_full_20260911/seed_mean_sample_sd.csv')
                if r['family']=='main' and r['method']=='geoprr' and r['dataset']=='industrial' and r['scope']=='all_conditions')
    frozen['GeoPRR-Net']['pooled_nmae']=(float(geoprr['nmae_pct_fs_mean']),float(geoprr['nmae_pct_fs_sample_sd']))
    raw={r['method']:r for r in read('data/figure_inputs_20260908/efficiency_raw.csv')}
    arms={r['arm']:r for r in read('data/figure_inputs_20260908/efficiency_structured.csv')}
    external={r['method']:r for r in read('data/figure_inputs_20260908/structured_industrial.csv')
              if r['dataset']=='Industrial-1395' and r['condition_scope']=='all_conditions'}
    names=['GeoPRR-Net','VDN + refs','DeepLab + refs','YOLO11s-Pose','Raw ResNet-18','Raw EfficientNet-B0','Raw MobileNetV3-L']
    colors=COLORS+['#607080','#91A1B0','#B8C1CA']
    markers=['D','o','s','^','v','P','X']
    series=[]
    for key in ['GeoPRR-Net','vdn_auto_geometry','deeplab_auto_geometry','yolo11s_pose4kp','Raw ResNet-18','Raw EfficientNet-B0','Raw MobileNetV3-Large']:
        if key in raw:
            r=raw[key];n,sd=frozen[key]['pooled_nmae']
            series.append((n,sd,float(r['p50_ms']),float(r['p95_ms']),float(r['parameters'])/1e6,float(r['peak_allocated_mib'])))
        else:
            r=arms[key]
            method={'vdn_auto_geometry':'VDN','deeplab_auto_geometry':'DeepLabV3+-ROI','yolo11s_pose4kp':'YOLO11s-Pose-4KP'}[key]
            a=external[method]
            series.append((float(a['nmae_percent_fs_mean']),float(a['nmae_percent_fs_sample_sd']),float(r['p50_ms']),float(r['p95_ms']),float(r['params_m']),float(r['peak_cuda_mib'])))
    data=np.array(series);assert data.shape==(7,6) and np.isfinite(data).all()
    fig=plt.figure(figsize=(7.2,4.7))
    ax=fig.add_axes([.085,.235,.47,.59])
    ap=fig.add_axes([.755,.61,.215,.215]);am=fig.add_axes([.755,.22,.215,.25])
    for i,(n,sd,p50,p95,params,mem) in enumerate(data):
        ax.hlines(n,p50,p95,color=colors[i],linewidth=1.5,zorder=2)
        ax.errorbar(p50,n,yerr=sd,fmt=markers[i],color=colors[i],markersize=6.5 if i==0 else 5,
                    capsize=2,elinewidth=.8,markeredgecolor='white',markeredgewidth=.4,zorder=3)
    ax.set_xlim(0,float(data[:,3].max())*1.13)
    ax.set_ylim(0,float(np.max(data[:,0]+data[:,1]))*1.13)
    ax.set_xlabel('P50 complete-pipeline latency (ms)');ax.set_ylabel('Industrial-1395 NMAE (%FS)')
    ax.grid(color=GRID,linewidth=.5);ax.set_axisbelow(True)
    ax.set_title('(a) Error and latency',loc='left',fontweight='bold',pad=9)
    ax.text(.97,.04,'Lower error and latency are preferable',transform=ax.transAxes,ha='right',fontsize=6.5,color='#657482')
    for a,field,title,label in [(ap,4,'(b) Pipeline parameters','Million parameters'),(am,5,'(c) Peak CUDA memory','MiB')]:
        a.barh(range(7),data[:,field],color=colors,height=.63)
        a.set_yticks(range(7),names,fontsize=6.3);a.invert_yaxis()
        a.set_xlim(0,float(data[:,field].max())*1.28)
        a.set_xlabel(label,fontsize=7);a.tick_params(axis='x',labelsize=6)
        a.tick_params(axis='y',length=0)
        a.grid(axis='x',color=GRID,linewidth=.5);a.set_axisbelow(True)
        a.set_title(title,loc='left',fontweight='bold',pad=8)
        for i,v in enumerate(data[:,field]):
            a.text(v+data[:,field].max()*.025,i,f'{v:.1f}',va='center',fontsize=6)
    handles=[Line2D([0],[0],marker=m,color=c,linestyle='',markersize=5,label=n) for n,c,m in zip(names,colors,markers)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.52,.008),ncol=3,fontsize=6.5,columnspacing=1.8,handletextpad=.5)
    fig.suptitle('Reading accuracy and complete-pipeline cost',fontsize=11,fontweight='bold',y=.97)
    fig.text(.5,.905,'Frozen models: six-condition accuracy and batch-1 FP32 timing',ha='center',fontsize=7)
    save(fig,'fig_complete_reader_tradeoff')

def zero_shot():
    rows=read('data/figure_inputs_20260908/zero_shot_summary.csv')
    datasets=['RF100-VL','Industrial-1395']
    names=['GeoPRR-Net','Raw ResNet-18','Raw EfficientNet-B0','Raw MobileNetV3-Large']
    lookup={(r['dataset'],r['method']):r for r in rows}
    assert len(lookup)==8
    colors=['#0F4D92','#607080','#91A1B0','#B8C1CA']
    fig=plt.figure(figsize=(7.2,4.0))
    left=fig.add_axes([.075,.235,.39,.54]);right=fig.add_axes([.685,.235,.28,.54])
    width=.18
    for j,name in enumerate(names):
        vals=np.array([float(lookup[(d,name)]['nmae_mean_percent_fs']) for d in datasets])
        sd=np.array([float(lookup[(d,name)]['nmae_sd_percent_fs']) for d in datasets])
        xpos=np.arange(2)+(j-1.5)*width
        left.bar(xpos,vals,width=width*.92,color=colors[j],yerr=sd,
                 error_kw={'ecolor':INK,'elinewidth':.7,'capsize':2},label=name)
        for x,y,e in zip(xpos,vals,sd):left.text(x,y+e+.5,f'{y:.1f}',ha='center',va='bottom',fontsize=6.5,fontweight='bold' if j==0 else 'normal')
    left.set_xticks([0,1],['RF100-VL\n151 images','Industrial-1395\n1,395 images'])
    left.set_ylim(0,31);left.set_ylabel('NMAE (%FS)')
    left.set_title('(a) Error on real-image inputs',loc='left',fontweight='bold',pad=9)
    left.grid(axis='y',color=GRID,linewidth=.5);left.set_axisbelow(True)
    yy=[5.5,4.5,3.5,1.5,.5,-.5]
    tick=[];row=0
    for k,dataset in enumerate(datasets):
        color=['#168A82','#0F4D92'][k]
        right.text(0,6.28 if k==0 else 2.28,dataset,fontsize=7,fontweight='bold',color=color)
        for name in names[1:]:
            r=lookup[(dataset,name)];v=float(r['relative_reduction_percent'])
            lo=float(r['relative_ci95_low_percent']);hi=float(r['relative_ci95_high_percent'])
            assert lo<=v<=hi
            right.errorbar(v,yy[row],xerr=[[v-lo],[hi-v]],fmt='o',color=color,capsize=2,markersize=4,elinewidth=.9)
            tick.append(name.replace('Raw ','').replace('MobileNetV3-Large','MobileNetV3-L'));row+=1
    right.axvline(0,color='#657482',linewidth=.7,linestyle='--')
    right.set_xlim(-80,70);right.set_ylim(-1.05,6.85)
    right.set_yticks(yy,tick,fontsize=6.6);right.tick_params(axis='y',length=0)
    right.set_xticks([-80,-40,0,40]);right.grid(axis='x',color=GRID,linewidth=.5);right.set_axisbelow(True)
    right.set_xlabel('Relative NMAE reduction (%)',fontsize=7)
    right.set_title('(b) Paired improvement',loc='left',fontweight='bold',pad=9)
    fig.suptitle('Zero-shot transfer to two real-image datasets',fontsize=11,fontweight='bold',y=.97)
    fig.text(.5,.884,'Frozen SyncG-trained readers; no target-domain training or adaptation',ha='center',fontsize=7)
    fig.legend(*left.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.015),ncol=2,fontsize=6.8,columnspacing=2.5)
    save(fig,'fig_zero_shot_transfer')

if __name__=='__main__':
    absolute_comparison();relative_comparison();efficiency();zero_shot()
    print('Wrote four comparison figures from the complete released summaries.')
