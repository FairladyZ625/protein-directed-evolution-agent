# V0.7 池内峰为何对 surrogate 隐形：低阶缺测与头部外推失真

2026-09-12；分支 `t-astra-mech`；代码基准 `ccbfce6c98a8b9f247b37aee456819c8f703878f`。
本文件是用户指定的只读机制研究；未改模型、采集、数据、门禁或其他文件。

**根因一句话：关键二阶组合缺测、已见突变的背景效应不稳定，加上正则化模型对高阶候选的头部外推失真，使峰被低估并被大量虚高预测挤出前列；现有证据不能把它定性为必需观测才知的三阶峰。**

## 1. 范围与证据边界

实际对象为 **AAV**，不是 GB1。加载 38,265 条，HD≤2 已测集 10,433，HD>2 未测池 27,832；HD≤4 且平均 BLOSUM62≥0 的门内池 9,533。
目标 fitness=8.416205130560002，只是上述未测池最优；cold-start 已有 9.53645667061，不能称全部数据或生物序列空间的全局最优。
重算全表 Hamming distance 与 `hd` 字段一致：`hd_mismatches 0`。
表中 oracle 值仅用于事后诊断；训练、超参选择和对照表征只用 cold-start 标签。没有查询网络或调用 LLM。
先固定全局对照：原 pairwise、去 WT 指示列的 mutation-only pairwise、全局 additive；没有根据峰坐标挑特征、超参或获胜模型。
峰局部删项属于用户要求的**后验解释**，不可转为在线选变量规则。未搜索更多模型或按峰名次调参。

参考材料已只读核对：worker handbook、domain research、v0.4–v0.7 报告、v06-backtrack-analysis、frontier-landscape-synthesis。
主 checkout 缺少的 v0.6/v0.7/分析文档从 t-v06/t-v07/t-analysis worktree 读取。
没有找到本 Mission 独立 task package；现有 v0.7 task_plan 属另一个更大实施任务，未擅自接管其执行面或生命周期。
历史多 seed 达峰率及六轮曲线是既有报告证据，本轮未重跑；下列机制数字均为本轮 runner 输出。

## 2. 突变集及 cold-start 的单/双证据

WT：`DEEEIRTTNPVATEQYGSVSTNLQRGNR`；目标：`QEEEIRTTNPVATEQYGEASTNLQRGNR`，均为 28 aa。
代码零基突变 **D0Q / S17E / V18A**；窗口一基 **D1Q / S18E / V19A**，**HD=3**。以下简称 A/B/C，不推定全蛋白坐标。

| 背景 | cold-start n | 实测 fitness | 原模型预测 |
|---|---:|---:|---:|
| WT | 1 | -0.918194 | 1.505710 |
| A | 1 | 0.302016 | 0.591992 |
| B | 1 | 3.287418 | 3.434876 |
| C | 1 | 0.889606 | 1.317249 |
| AB | **0** | **缺测** | 2.462832 |
| AC | 1 | 2.087894 | 2.041990 |
| BC | 1 | 5.770209 | 5.700363 |
| ABC（未测池目标） | 0 | 8.416205（后验查表） | 6.366779 |

AB 在加载后的**全部 38,265 条中也不存在**，不是被错误 HD 切走。
相对实测 WT 的单点增益 A/B/C 为 **+1.220210 / +4.205612 / +1.807800**。
实测 WT 锚定二阶差分 `εij=fij-fi-fj+fWT`：AC=**-0.021921**，BC=**+0.674991**，AB 不可算。
BC 加 C 的收益为 2.482791；AC 加 C 的收益为 1.785878；双点高 fitness 不等于同等幅度的上位效应。

“含该突变”的群体均值会受背景组成混杂，故同时计算配对边际：在 cold-start 内，对每个含突变的序列撤回该突变，只保留两端都有标签的配对。

| 突变 | 含该突变 n | 含 / 不含的均值 | 配对 n | 配对增益均值 / 中位数 | 配对增益范围 |
|---|---:|---|---:|---|---|
| A | 52 | -0.010347 / -1.692023 | 52 | **-0.605824 / -0.513251** | [-4.852542, 2.923898] |
| B | 78 | 2.686214 / -1.716557 | 78 | **1.995957 / 2.122102** | [-4.917623, 6.356779] |
| C | 78 | 0.864526 / -1.702835 | 78 | **-0.030860 / -0.006034** | [-3.882899, 4.594391] |

因此 A 在 WT 背景有益，却在这些可配对背景中平均有害；C 平均近中性，B 较稳定地有益但也非处处有益。
这些是所测背景的描述统计，不是随机实验得到的普适因果效应，也没有独立重复来量化测量噪声。

## 3. 为何排 #426：低估之外，还有预测虚高的竞争者

生产类实测：alpha=300，调参 split Spearman=**0.905917215**；预测均值 **6.366778604**、方差 **1.288612185**（SD≈1.13517）。
均值排名 **全池 #2758 / 门内 #426**；门内约前4.47%，超过单批48及静态288预算线，不等于所有闭环路径的可达性上限。
均值来自单个全量拟合；方差来自 bootstrap seeds 0/1/2 的总体方差，**不是五模型均值或校准后的预测区间**。
冷启动纯 UCB=`mean+3√var` 的目标排名反而为全池 #3969／门内 #539；不能把后续探索命中当作初始 UCB 已识别峰。

| 门内按均值选取 | 预测均值 | 实测均值（后验） | 实测最大值 | 至少一个未见残基对的比例 |
|---|---:|---:|---:|---:|
| top48 | 11.306529 | 2.883794 | 7.391004 | 52.08% |
| top288 | 8.669775 | 2.641190 | 7.828968 | 57.99% |
| 峰前425条 | 8.041300 | 2.683542 | 7.828968 | 55.29% |

top48 预测范围 **[9.996596,14.441225]**。峰的预测误差仅 +2.049427（真值−预测），而竞争者整体严重高估。
训练保留560个 one-hot 列，展开157,080列，仅25,202列在训练非零；池中另有31,955列首次非零。峰恰有1个未见残基对，即 AB。
未见对列系数为0；对其他候选的过估不能仅由“有未见对”推出，表格仅证实覆盖缺口和头部失真并存。

“向均值回归的离群点”只能部分成立：cold-start 标签均值 -1.683641，SD=3.303298；峰高但低于已知最大值。
原调参验证集 MSE=2.432951，残差95%/99%分位=2.522487/3.684057；峰误差对应其约90.42%分位，并非极端不可解释残差。
该比较跨 HD 分布，只是尺度参照，不能作峰的显著性检验。
验证集真实 top10% 均值3.907278、预测均值2.223305，确有高值收缩现象；同时 WT 被高估2.423904，不能把所有误差解释成统一减幅。

## 4. 删哪些交互项会改变排名

固定模型、对**整个候选池**施加同一删项，不重训；排名均为严格大于目标分数的条数+1。
先看生产多项式中对应突变×突变列（系数已除以 scaler.scale）：

| 删除原始列 | 支持数 | 删除的贡献 | 新预测 | 全池 / 门内排名 |
|---|---:|---:|---:|---|
| AB | 0 | 0 | 6.366779 | 2758 / 426 |
| AC | 1 | +1.598625 | 4.768153 | 4310 / 1050 |
| BC | 1 | +2.426211 | 3.940568 | 5471 / 1583 |

one-hot 含 WT 状态，原始系数有冗余，不能直接当生物上位效应。
再用模型八顶点预测作 WT 锚定差分，得到可解释的局部预测函数：
`fhat = 1.505710 -0.913718*A +1.929165*B -0.188462*C -0.058326*AB +1.638459*AC +2.453949*BC`。
它在目标复原6.366778604，三阶差分仅1.78e-15，符合二阶函数；模型没有表达显式三阶作用。

| 删除 WT 锚定交互效应 | 新预测 | 全池 / 门内排名 |
|---|---:|---|
| AB | 6.425104 | 2713 / 414 |
| AC | 4.728319 | 4361 / 1072 |
| BC | 3.912829 | 5513 / 1608 |
| 三者全删 | 2.332696 | 8693 / 3190 |

这是局部差分在全池对应指示乘积上的冻结干预，并非全局重拟合结果。
即使删掉唯一负贡献 AB，仍只到 #414；**两个有数据的交互是在救排名，而非压低峰**。
模型 AC差分1.638459 与实测-0.021921 不一致，部分来自 WT/单点拟合偏差；不能把模型系数等同实测机制。

## 5. 三阶上位是否必要？现有数据不能识别

用已测 WT/A/B/C/AC/BC，假定无三阶作用，则
`fABC = fAB + fAC + fBC - fA - fB - fC + fWT = fAB + 2.460869245`。
若缺测 AB=**5.955335886**，一个纯二阶局部景观已经精确解释8.416205；若另假设 AB 无上位，则 AB=4.507627582，ABC预测6.968496827。
后一假设下的1.447708差额可以叫条件三阶残差，但 **AB无上位不是观测事实**。
更直接的不可识别性证明：向任意拟合函数加 `λ·1[D0Q]·1[S17E]`，所有 cold-start 预测及其 held-out 指标完全不变，却改变含 AB 的未测候选排序；无需引入三阶项。
同样，三个突变指示的乘积在所有 HD≤2 数据上恒零，不能靠这种 cold-start CV估计独立三阶系数。
所以“已覆盖峰全部单/双点，剩下必是三阶上位”的前提已被本轮否定。生物机制、独立测量噪声、高阶残差的归因均未获证实。

## 6. 有没有合法 surrogate 能把它排高？

本轮只测试三个预先固定的全局表征。外层随机80/20划分seed42，仅在外层训练数据内重做筛列/缩放/内层alpha选择；外层标签不用于选择超参。
所有模型沿用 alpha网格[1,10,100,300]和min_count=10，不按峰排名选择。外层结果：

| 表征 | 外层 Spearman | Pearson | MSE | 真实top10%召回 | 全cold-start预测峰 / 门内排名 |
|---|---:|---:|---:|---:|---|
| 原pairwise | 0.909370 | 0.886297 | 2.404037 | 0.511962 | 6.366779 / 426 |
| 全局mutation-only pairwise | 0.895742 | 0.867224 | 3.908087 | 0.459330 | 7.481467 / 1375 |
| 全局additive（沿用缩放及alpha选择） | 0.909495 | 0.890789 | 2.291431 | 0.483254 | 2.992217 / 2663 |

mutation-only 虽提高峰的绝对预测，**排名反而下降**；不能凭预测接近8.416就宣布改善。
additive 的低阶CV甚至微高，但对该峰排序更差；0.000125差距不构成显著优势，也不与历史不同additive实现的CV混为一谈。
原pairwise在门内未测池后验 Spearman仅 **0.597348**、Pearson0.598908、MSE6.972168、top10%召回0.268344。
这显示低阶随机验证不能代表HD3–4头部排序；外层验证虽独立，也仍是低阶分布。
标签shuffle阴性对照实跑：Spearman **0.013438177**，alpha300；原标签调参CV0.905917215，信号确实随标签置乱而消失。

**结论边界**：本轮没有找到经上述合法验证支持、能把峰排入top288的替代surrogate；也不能由三个模型证明“任何surrogate都不行”。
同一cold-start允许不同未测景观，单靠这些标签无法保证特定未测点是最优；额外先验可能奏效，但需独立证据，不能用峰身份来选择先验。
不必断言“非直接测峰不可”：新的、一般性选择的组合测量也可能改善排序。缺失AB在当前池也不存在，因此建议不能直接提名该缺真值双点来绕开oracle。
下一步应预注册对所有候选通用的组合覆盖/不确定性策略，并用新增测量校准高HD的头部误差；不能从本报告点名的A/B/C回灌在线规则。

## 7. 复现、交付与未验证项

下方是本轮实际执行的只读stdin runner；只打印结果，不落缓存/模型/脚本文件。单线程运行环境：
`PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -`。
CSV SHA256=`520c7c6545e61d3c23b41616fbb6afe3396c3ca11da1fe14ead92846dfeffa77`。
`models/train_ladder.py` SHA256=`993f399f3797219e2b48900546229b264d5714372b47608d6802c50405ea5487`。
NumPy/SciPy/sklearn=2.5.3/1.18.1/1.9.0；runner完成exit0。未跑产品测试、CI、六轮矩阵或ESM；没有产品代码变更。
`ha fact record`及doc sync预检返回`daemon_unavailable: workspace is not registered`，**未取得canonical fact/receipt**；未扩写注册配置。
本Mission未提供独立task-id，未冒用其他任务提交receipt。交付为本worktree指定文件；`harness/`被公共repo忽略，遵守“不提交public-repository artifacts”，未强行git add。
本地origin/main=`be62937`，与HEAD无共同祖先；用户要求离线，未fetch或强拼rebase，最新远端状态未验证。因仅治理文档且无可提交的授权代码变更，未造空commit。

```python
import os
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
import numpy as np, pandas as pd, scipy, sklearn, hashlib, json, itertools
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from models.train_ladder import EpistasisRidgePredictor
from evolution.datasets import load_aav, AAV_CSV
from analysis.epistasis_surrogate_scan import _gate_ok
def emit(k, **v): print(k, json.dumps(v, ensure_ascii=False), flush=True)
spec=load_aav(); df=spec.df; wt=spec.wt
train=df[df.hd<=2].reset_index(drop=True); pool=df[df.hd>2].reset_index(drop=True)
X=spec.feature_fn(train.seq.tolist()); y=train.fitness.to_numpy(); XP=spec.feature_fn(pool.seq.tolist())
gate=np.array([_gate_ok(s,wt) for s in pool.seq])
model=EpistasisRidgePredictor().fit(X,y); mean,var=model.predict(XP)
peak="QEEEIRTTNPVATEQYGEASTNLQRGNR"; pi=pool.index[pool.seq==peak][0]
changes=[(p,a) for p,(w,a) in enumerate(zip(wt,peak)) if w!=a]
def rank(z):return [int((z>z[pi]).sum()+1),int((z[gate]>z[pi]).sum()+1)]
emit("base", n=len(df),cold=len(train),pool=len(pool),gate=int(gate.sum()),length=len(wt),changes=changes,alpha=model._alpha,cv=model.val_spearman,mean=float(mean[pi]),var=float(var[pi]),rank=rank(mean),y=float(pool.fitness.iloc[pi]),cold_mean=float(y.mean()),cold_sd=float(y.std()),cold_max=float(y.max()),sha=hashlib.sha256(AAV_CSV.read_bytes()).hexdigest(),versions=[np.__version__,scipy.__version__,sklearn.__version__])
seqs=[]; keys=[]
for size in range(4):
 for inds in itertools.combinations(range(3),size):
  s=list(wt)
  for i in inds:p,a=changes[i];s[p]=a
  seqs.append("".join(s));keys.append(inds)
cm,cv=model.predict(spec.feature_fn(seqs)); cube={}
for i,(inds,s) in enumerate(zip(keys,seqs)):
 rows=train[train.seq==s]
 cube[inds]=float(cm[i])
 emit("cube",subset=inds,seq=s,n=len(rows),fitness=rows.fitness.tolist(),prediction=float(cm[i]),var=float(cv[i]))
for i,(p,a) in enumerate(changes):
 mask=train.seq.str[p].eq(a).to_numpy()
 # Background-matched mutation additions: both labels from cold-start.
 lookup=dict(zip(train.seq,y)); dif=[]
 for s,fy in zip(train.seq[mask],y[mask]):
  b=list(s);b[p]=wt[p];b="".join(b)
  if b in lookup:dif.append(float(fy-lookup[b]))
 emit("marginal",mutation=f"{wt[p]}{p}{a}",n=int(mask.sum()),mean=float(y[mask].mean()),other_mean=float(y[~mask].mean()),matched_n=len(dif),matched_mean=float(np.mean(dif)) if dif else None,matched_median=float(np.median(dif)) if dif else None,matched_range=[min(dif),max(dif)] if dif else None)
for i,j in itertools.combinations(range(3),2):
 p,a=changes[i];q,b=changes[j];mask=train.seq.str[p].eq(a)&train.seq.str[q].eq(b)
 emit("pair_support",pair=[i,j],n=int(mask.sum()),y=train.fitness[mask].tolist())
# WT-anchored finite differences are invariant to redundant one-hot coefficient gauge.
sing={i:cube[(i,)]-cube[()] for i in range(3)}
pairs={(i,j):cube[(i,j)]-cube[(i,)]-cube[(j,)]+cube[()] for i,j in itertools.combinations(range(3),2)}
emit("decomposition",intercept=cube[()],singles=sing,pairs={str(k):v for k,v in pairs.items()},reconstructed=cube[()]+sum(sing.values())+sum(pairs.values()),triple_difference=cube[(0,1,2)]-cube[()]-sum(sing.values())-sum(pairs.values()))
allmask=[pool.seq.str[p].eq(a).to_numpy() for p,a in changes]
for (i,j),v in pairs.items():
 z=mean-v*(allmask[i]&allmask[j]);emit("drop_effect",pair=[i,j],effect=v,mean=float(z[pi]),rank=rank(z))
z=mean.copy()
for (i,j),v in pairs.items():z-=v*(allmask[i]&allmask[j])
emit("drop_all_three",mean=float(z[pi]),rank=rank(z))
# Original fixed split diagnostic: no additional data or oracle used.
xp=model._scaler.transform(model._expand(X)); tr,va=train_test_split(np.arange(len(y)),test_size=.2,random_state=0)
vm=Ridge(alpha=model._alpha,solver="sparse_cg").fit(xp[tr],y[tr]);vp=vm.predict(xp[va]);res=y[va]-vp
emit("validation",spearman=float(spearmanr(vp,y[va]).statistic),pearson=float(np.corrcoef(vp,y[va])[0,1]),mse=float(np.mean(res**2)),residual_quantiles=np.quantile(res,[.01,.5,.9,.95,.99]).tolist(),peak_residual=float(pool.fitness.iloc[pi]-mean[pi]),residual_percentile=float(np.mean(res<=pool.fitness.iloc[pi]-mean[pi])),top_true_y_mean=float(np.mean(y[va][y[va]>=np.quantile(y[va],.9)])),top_true_pred_mean=float(np.mean(vp[y[va]>=np.quantile(y[va],.9)])))
null=EpistasisRidgePredictor().fit(X,np.random.default_rng(42).permutation(y))
emit("shuffle",cv=null.val_spearman,alpha=null._alpha)
# Prespecified comparison: global WT-reference mutation indicators, no target coordinates.
XM=X.copy();XPM=XP.copy();wtcols=np.flatnonzero(spec.feature_fn([wt])[0])
XM[:,wtcols]=0;XPM[:,wtcols]=0
for label,xx,pp in [("mutation_only_pair",XM,XPM)]:
 mm=EpistasisRidgePredictor().fit(xx,y);mu,vv=mm.predict(pp)
 emit("alternative",name=label,alpha=mm._alpha,cv=mm.val_spearman,mean=float(mu[pi]),var=float(vv[pi]),rank=rank(mu))

# Independent outer holdout, fixed before comparison; inner alpha selection uses fit only.
from sklearn.preprocessing import PolynomialFeatures
import scipy.sparse as sp
class Additive(EpistasisRidgePredictor):
 def _expand(self,X,fit=False):return sp.csr_matrix(np.asarray(X,dtype=float)[:,self._keep])
def met(yt,yp):
 k=max(1,int(np.ceil(len(yt)*.1))); a=set(np.argsort(-yt)[:k]);b=set(np.argsort(-yp)[:k])
 return dict(spearman=float(spearmanr(yt,yp).statistic),pearson=float(np.corrcoef(yt,yp)[0,1]),mse=float(np.mean((yt-yp)**2)),top10pct_recall=len(a&b)/k)
ot,ov=train_test_split(np.arange(len(y)),test_size=.2,random_state=42)
for name,xx,pp,cls in [("pair",X,XP,EpistasisRidgePredictor),("mutation_pair",XM,XPM,EpistasisRidgePredictor),("additive",X,XP,Additive)]:
 om=cls(var_seeds=0).fit(xx[ot],y[ot]);pred=om._mean_model.predict(om._scaler.transform(om._expand(xx[ov])))
 emit("outer",name=name,alpha=om._alpha,inner=om.val_spearman,**met(y[ov],pred))
 if name=="additive":
  am=cls().fit(xx,y);mu,vv=am.predict(pp);emit("alternative",name=name,alpha=am._alpha,cv=am.val_spearman,mean=float(mu[pi]),rank=rank(mu))
# Rank pressure from unobserved residue-pair columns, diagnosed without fitting to pool labels.
raw=model._expand(X); rawp=model._expand(XP); support=np.asarray(raw.sum(axis=0)).ravel()
unseen=np.asarray(rawp[:,support==0].sum(axis=1)).ravel()
emit("support",kept=int(model._keep.sum()),expanded=raw.shape[1],train_nonzero_columns=int((support>0).sum()),pool_unseen_columns=int(((np.asarray(rawp.sum(axis=0)).ravel()>0)&(support==0)).sum()),peak_unseen=int(unseen[pi]))
# Post-hoc pool evaluation only, never used for model selection.
gids=np.flatnonzero(gate); order=gids[np.argsort(-mean[gids])]
for n in [48,288,425]:
 ids=order[:n];emit("rank_pressure",n=n,pred_mean=float(mean[ids].mean()),truth_mean=float(pool.fitness.iloc[ids].mean()),truth_max=float(pool.fitness.iloc[ids].max()),unseen_fraction=float(np.mean(unseen[ids]>0)),pred_min=float(mean[ids].min()),pred_max=float(mean[ids].max()))
emit("pool_evaluation",**met(pool.fitness.to_numpy()[gate],mean[gate]))
true=dict(zip(train.seq,y));vals={inds:true.get(s) for inds,s in zip(keys,seqs)}
a,b,c=vals[(0,)],vals[(1,)],vals[(2,)];f0=vals[()];ac,bc=vals[(0,2)],vals[(1,2)]
offset=ac+bc-a-b-c+f0;needed=float(pool.fitness.iloc[pi]-offset)
emit("identifiability",single_effects=[a-f0,b-f0,c-f0],epistasis_ac=ac-a-c+f0,epistasis_bc=bc-b-c+f0,pairwise_offset=offset,AB_for_zero_triple=needed,AB_additive=a+b-f0,ABC_zero_AB_epistasis=offset+a+b-f0,peak_UCB_rank=rank(mean+3*np.sqrt(var)))
# Exact frozen-model interventions on individual raw polynomial coefficients (gauge-dependent).
indices=np.flatnonzero(model._keep); powers=model._poly.powers_
for i,j in itertools.combinations(range(3),2):
 ia=int(np.flatnonzero(indices==changes[i][0]*20+"ACDEFGHIKLMNPQRSTVWY".index(changes[i][1]))[0])
 ib=int(np.flatnonzero(indices==changes[j][0]*20+"ACDEFGHIKLMNPQRSTVWY".index(changes[j][1]))[0])
 col=int(np.flatnonzero((powers[:,ia]==1)&(powers[:,ib]==1))[0])
 coef=float(model._mean_model.coef_[col]/model._scaler.scale_[col])
 z=mean-coef*(allmask[i]&allmask[j]);emit("drop_raw_column",pair=[i,j],train_support=int(support[col]),coefficient=coef,mean=float(z[pi]),rank=rank(z))
```

