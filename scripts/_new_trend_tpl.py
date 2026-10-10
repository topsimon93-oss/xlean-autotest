_TREND_TPL = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>xLean 测试质量报告</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#0d0f13; --card:#151820; --card2:#1c202b; --line:#262b36;
  --txt:#e8eaef; --sub:#9aa3b2; --dim:#626b7a;
  --ok:#22c55e; --bad:#ef4444; --warn:#f59e0b; --info:#3b82f6; --skip:#64748b;
}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;margin:0;background:var(--bg);color:var(--txt);-webkit-font-smoothing:antialiased}
.wrap{max-width:1240px;margin:0 auto;padding:26px 22px 60px}

/* 结论横幅 */
.verdict{display:flex;align-items:center;gap:18px;padding:22px 26px;border-radius:14px;border:1px solid var(--line);background:linear-gradient(135deg,var(--card),var(--card2));margin-bottom:16px}
.verdict .light{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26px;flex:none;box-shadow:0 0 0 6px rgba(0,0,0,.2)}
.verdict .light.pass{background:rgba(34,197,94,.15);color:var(--ok)}
.verdict .light.fail{background:rgba(239,68,68,.15);color:var(--bad)}
.verdict h1{margin:0;font-size:20px;letter-spacing:.3px}
.verdict .vsub{margin-top:5px;color:var(--sub);font-size:13px;line-height:1.6}
.verdict .meta{margin-left:auto;text-align:right;font-size:12px;color:var(--dim);line-height:1.7;flex:none}
.verdict .meta b{color:var(--sub);font-weight:600}

/* KPI */
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:16px}
@media(max-width:1000px){.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:560px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px;position:relative;overflow:hidden}
.kpi::after{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--ac,#3b82f6)}
.kpi .v{font-size:25px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1;letter-spacing:-.5px}
.kpi .v small{font-size:13px;font-weight:600;color:var(--sub)}
.kpi .t{font-size:12px;color:var(--sub);margin-top:9px}
.kpi .d{font-size:11px;color:var(--dim);margin-top:3px}
.kpi .trend{font-size:11px;margin-top:6px;font-weight:600}
.up{color:var(--ok)} .down{color:var(--bad)} .flat{color:var(--dim)}

/* 通用卡片 */
.grid{display:grid;gap:14px;margin-bottom:14px}
.g2{grid-template-columns:1fr 1fr}
.g32{grid-template-columns:1.6fr 1fr}
@media(max-width:900px){.g2,.g32{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:18px}
.card h2{margin:0 0 2px;font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px}
.card h2 .badge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:5px;background:var(--card2);border:1px solid var(--line);color:var(--sub)}
.card .meta{color:var(--dim);font-size:12px;margin-bottom:14px;line-height:1.5}
canvas{max-height:280px}

/* 缺陷清单 */
.defect{border:1px solid rgba(239,68,68,.35);border-left:3px solid var(--bad);border-radius:10px;padding:13px 15px;margin-bottom:10px;background:rgba(239,68,68,.04)}
.defect .df-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:7px}
.defect .df-name{font-weight:700;font-size:13.5px}
.defect .tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid}
.tag.reg{color:#fca5a5;border-color:rgba(239,68,68,.4);background:rgba(239,68,68,.12)}
.tag.flaky{color:#fbbf24;border-color:rgba(245,158,11,.4);background:rgba(245,158,11,.12)}
.tag.new{color:#93c5fd;border-color:rgba(59,130,246,.4);background:rgba(59,130,246,.12)}
.tag.slow{color:#fbbf24;border-color:rgba(245,158,11,.4);background:rgba(245,158,11,.12)}
.defect .df-desc{font-size:12.5px;color:var(--sub);line-height:1.65}
.defect .df-trace{font-size:11.5px;color:var(--dim);margin-top:6px;font-family:ui-monospace,Consolas,monospace}

/* 稳定率矩阵 */
.matrix-tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.matrix-tbl th{text-align:left;color:var(--dim);font-weight:600;padding:8px 8px;border-bottom:1px solid var(--line);font-size:11px;white-space:nowrap}
.matrix-tbl td{padding:8px;border-bottom:1px solid #1b1e27;vertical-align:middle}
.matrix-tbl tr:hover td{background:#191d26}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle}
.cell{display:inline-block;width:16px;height:16px;border-radius:4px;margin-right:4px;cursor:pointer;border:1px solid transparent}
.cell:hover{border-color:var(--info)}
.cell.pass{background:rgba(34,197,94,.5)} .cell.fail{background:var(--bad)} .cell.err{background:#7f1d1d} .cell.skip{background:#334155}
.mrow{cursor:pointer}
.mrow:hover td{background:#191d26!important}
.stable{color:var(--ok);font-weight:700}.warn{color:var(--warn);font-weight:700}.unstable{color:var(--bad);font-weight:700}
.flaky-tag{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:5px;background:rgba(245,158,11,.15);color:var(--warn);font-size:10px;font-weight:700}

/* 明细表 */
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:600;padding:9px 10px;border-bottom:1px solid var(--line);font-size:12px;white-space:nowrap}
td{padding:10px;border-bottom:1px solid #1b1e27;vertical-align:top}
tr:hover td{background:#191d26}
.cname{display:inline-block;cursor:pointer;padding:2px 8px;border-radius:5px;margin:1px 3px 1px 0;transition:.12s;border:1px solid transparent;font-size:12.5px}
.cname:hover{background:var(--card2);border-color:var(--line)}
.cname.sel,.mrow.sel td{background:rgba(59,130,246,.12)}
.cname.sel{border-color:var(--info)}
.sec{font-size:11px;color:var(--dim)}
.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.pill{padding:6px 13px;border-radius:999px;border:1px solid var(--line);background:var(--card);cursor:pointer;font-size:12.5px;color:var(--sub);user-select:none;transition:.15s}
.pill:hover{border-color:var(--info);color:var(--txt)}
.pill.on{background:var(--info);color:#fff;border-color:var(--info)}
.search{margin-left:auto;background:var(--card2);border:1px solid var(--line);border-radius:8px;padding:7px 12px;color:var(--txt);font-size:13px;width:210px;outline:none}
.search:focus{border-color:var(--info)}
.footer{color:var(--dim);font-size:11px;text-align:center;margin-top:26px;line-height:1.8}
.empty{color:var(--dim);text-align:center;padding:24px;font-size:13px}
</style></head><body><div class="wrap">

<div class="verdict" id="verdict"></div>
<div class="kpis" id="kpis"></div>

<div id="defects-section"></div>

<div class="grid g2">
  <div class="card"><h2>通过率趋势</h2><div class="meta">每次运行通过率，虚线为历史均值基线</div><canvas id="c-rate"></canvas></div>
  <div class="card"><h2>总耗时趋势</h2><div class="meta">每次运行累计耗时（秒），红色=有失败</div><canvas id="c-time"></canvas></div>
</div>

<div class="grid g32">
  <div class="card"><h2>用例稳定率矩阵 <span class="badge" id="flaky-count"></span></h2><div class="meta">每行一个用例，色块=历次运行结果，点任一行看下方走势；标黄=不稳定(Flaky)</div><div id="matrix"></div></div>
  <div class="card"><h2>最慢用例 TOP5</h2><div class="meta">按历史平均耗时排序，超过 SLA 阈值标红</div><canvas id="c-slow"></canvas></div>
</div>

<div class="grid g2">
  <div class="card"><h2>失败热点</h2><div class="meta">各用例累计失败次数（FAIL + ERROR）</div><canvas id="c-fail"></canvas></div>
  <div class="card"><h2>单用例耗时走势</h2><div class="meta" id="case-meta">点击上方矩阵或下方明细的用例名查看</div><canvas id="c-case"></canvas></div>
</div>

<div class="card">
  <div class="toolbar">
    <h2 style="margin:0">历史运行明细</h2>
    <span class="pill on" data-f="all">全部</span>
    <span class="pill" data-f="fail">失败过的</span>
    <input class="search" id="q" placeholder="搜索用例&#8230;">
  </div>
  <table><thead><tr><th>运行#</th><th>时间</th><th>结果</th><th>通过率</th><th>耗时</th><th>用例明细</th></tr></thead><tbody id="tbl"></tbody></table>
</div>

<div class="footer">数据源 history.json · 每次跑 Appium 回归自动追加 · SLA 阈值：单用例 120s / 全量 20min · 点用例名下钻历史耗时</div>
</div>

<script>
const H = __PAYLOAD__;
const TITLES = __TITLES__;
const title = n => TITLES[n] || n;
const C = {ok:'#22c55e',bad:'#ef4444',warn:'#f59e0b',info:'#3b82f6',skip:'#64748b'};
const SLA_CASE = 120;   // 单用例 SLA 秒
const SLA_TOTAL = 1200; // 全量 SLA 秒（20min）

let caseFilter='all', selectedCase=null, searchText='';
let charts={};
function destroy(n){ if(charts[n]){charts[n].destroy(); delete charts[n];} }
function cnv(id){ return document.getElementById(id); }
const lbl = r => r.ts.slice(5,16);
const stColor = s => ({PASS:C.ok,FAIL:C.bad,ERROR:C.bad,SKIP:C.skip}[s]||C.skip);
const isFail = s => ['FAIL','ERROR'].includes(s);
const uniq = () => [...new Set(H.flatMap(r=>r.cases.map(c=>c.name)))];
const caseByName = (r,n) => r.cases.find(c=>c.name===n);

/* 判断 Flaky：存在 pass 之后又 fail（或 fail 之后又 pass）的用例 */
function isFlaky(name){
  const seq = H.map(r=>{const c=caseByName(r,name);return c? (isFail(c.status)?'F':'P') : null;}).filter(Boolean);
  if(seq.length<2) return false;
  return seq.some((s,i)=> i>0 && s!==seq[i-1]);
}
/* 最近一次是否失败 */
function lastFailed(name){
  for(let i=H.length-1;i>=0;i--){const c=caseByName(H[i],name); if(c) return isFail(c.status);}
  return false;
}

/* 顶部结论 */
function verdict(){
  const last = H[H.length-1];
  const total = H.reduce((a,r)=>a+r.total,0);
  const passed = H.reduce((a,r)=>a+r.passed,0);
  const rate = total? passed/total : 0;
  const ok = last.failed===0;
  const el = cnv('verdict');
  const light = ok? 'pass':'fail';
  const ico = ok? '✓':'✕';
  let msg;
  if(ok) msg = '本轮回归 <b>全部 '+last.passed+' 条用例通过</b>，质量可发布。';
  else msg = '本轮 <b>'+last.failed+' 条用例失败</b>，需定位并修复后复测。';
  const reg = lastFailedAnyNewRegression();
  el.innerHTML =
    '<div class="light '+light+'">'+ico+'</div>'+
    '<div><h1>'+ (ok?'PASS · 回归通过':'FAIL · 回归失败') +'</h1>'+
    '<div class="vsub">'+msg+(reg? ' <span style="color:var(--bad)">其中 <b>'+reg+'</b> 条为回归(此前通过、本次失败)。</span>':'')+'</div></div>'+
    '<div class="meta">运行 #'+H.length+'<br><b>'+last.ts+'</b><br>累计通过率 <b>'+(rate*100).toFixed(1)+'%</b>（'+passed+'/'+total+'）</div>';
}
/* 统计"上次通过、本次失败"的回归数 */
function lastFailedAnyNewRegression(){
  if(H.length<2) return 0;
  const prev=H[H.length-2], last=H[H.length-1];
  let n=0;
  last.cases.forEach(c=>{
    if(!isFail(c.status)) return;
    const pc = caseByName(prev,c.name);
    if(pc && pc.status==='PASS') n++;
  });
  return n;
}

/* KPI */
function kpis(){
  const last = H[H.length-1];
  const total = H.reduce((a,r)=>a+r.total,0);
  const passed = H.reduce((a,r)=>a+r.passed,0);
  const rate = total? passed/total : 0;
  // 首次通过率 FPR：历史所有用例中，第一次运行即 PASS 的比例
  const names = uniq();
  const fpr = names.filter(n=>{const first=H[0].cases.find(c=>c.name===n); return first&&first.status==='PASS';}).length / (names.length||1);
  const avgTime = H.reduce((a,r)=>a+r.elapsed,0)/H.length;
  const best = H.reduce((a,r)=>Math.min(a,r.elapsed),1e9);
  const worst = H.reduce((a,r)=>Math.max(a,r.elapsed),0);
  const flakyNames = names.filter(isFlaky);
  const prevRate = H.length>=2? (H[H.length-2].total? H[H.length-2].passed/H[H.length-2].total:0) : rate;
  const rateDelta = H.length>=2? rate-prevRate : 0;
  const prevTime = H.length>=2? H[H.length-2].elapsed : avgTime;
  const timeDelta = H.length>=2? last.elapsed-prevTime : 0;

  const k = (v,small,t,d,ac,trendHtml)=>
    '<div class="kpi" style="--ac:'+ac+'"><div class="v">'+v+(small?'<small> '+small+'</small>':'')+'</div><div class="t">'+t+'</div><div class="d">'+d+'</div>'+(trendHtml||'')+'</div>';
  const trend = (delta, goodWhenDown) => {
    if(delta===0) return '<div class="trend flat">— 持平</div>';
    const good = goodWhenDown? delta<0 : delta>0;
    const cls = good?'up':'down';
    const arrow = delta>0?'▲':'▼';
    return '<div class="trend '+cls+'">'+arrow+' '+Math.abs(delta).toFixed(1)+' '+ (goodWhenDown?'':'%') +'</div>';
  };
  cnv('kpis').innerHTML =
    k(H.length,'','运行次数','累计 '+H.length+' 次回归',C.info,'')+
    k(last.passed,'/'+last.total,'最近一次结果',last.ts.slice(0,16), last.failed? C.bad:C.ok,'')+
    k((rate*100).toFixed(1),'%','累计通过率',passed+' / '+total, C.ok, trend(rateDelta*100,false))+
    k((fpr*100).toFixed(0),'%','首次通过率',names.length+' 用例首次即过', C.info,'')+
    k(flakyNames.length,'','不稳定用例',flakyNames.length? '需关注：'+flakyNames.slice(0,2).map(title).join('、')+(flakyNames.length>2?'…':''):'全部稳定', flakyNames.length?C.warn:C.ok,'')+
    k(_fmt(last.elapsed),'','本次耗时', '最快 '+_fmt(best)+' / 最慢 '+_fmt(worst), last.elapsed>SLA_TOTAL?C.bad:C.info, trend(timeDelta,true));
}
function _fmt(s){ s=Math.round(s); if(s<60)return s+'s'; return Math.floor(s/60)+'m'+(s%60)+'s'; }

/* 缺陷清单 */
function defects(){
  const names = uniq();
  const defs = names.filter(lastFailed).map(n=>{
    const runs = H.map(r=>caseByName(r,n));
    const failCount = runs.filter(c=>c&&isFail(c.status)).length;
    const lastStatus = runs.filter(Boolean).slice(-1)[0].status;
    const flaky = isFlaky(n);
    const reg = H.length>=2 && caseByName(H[H.length-2],n) && caseByName(H[H.length-2],n).status==='PASS';
    const avgT = runs.reduce((a,c)=>a+(c?c.time:0),0)/(runs.filter(Boolean).length||1);
    const slow = avgT>SLA_CASE;
    const tags=[];
    if(reg) tags.push('<span class="tag reg">回归 Regression</span>');
    if(flaky) tags.push('<span class="tag flaky">不稳定 Flaky</span>');
    else tags.push('<span class="tag new">持续失败</span>');
    if(slow) tags.push('<span class="tag slow">超时</span>');
    return {n, failCount, lastStatus, tags:tags.join(' '), avgT};
  });
  const sec = cnv('defects-section');
  if(!defs.length){ sec.innerHTML=''; return; }
  sec.innerHTML = '<div class="card" style="margin-bottom:14px"><h2>缺陷清单 <span class="badge">'+defs.length+' 个</span></h2><div class="meta">当前仍未通过、需要修复或排查的用例</div>'+
    defs.map(d=>{
      const desc = d.lastStatus==='ERROR'
        ? '执行期间抛异常（定位器失效 / 环境异常），非断言失败，需先确认环境与元素定位。'
        : '断言未通过，页面状态与预期不符。建议结合截图核对实际 UI。';
      return '<div class="defect">'+
        '<div class="df-head"><span class="df-name">'+title(d.n)+'</span>'+d.tags+'</div>'+
        '<div class="df-desc">'+desc+'</div>'+
        '<div class="df-trace">历史失败 '+d.failCount+' 次 · 平均耗时 '+Math.round(d.avgT)+'s</div>'+
        '</div>';
    }).join('')+'</div>';
}

/* 通过率趋势（带基线） */
function drawRate(){
  destroy('rate');
  const labels = H.map(r=>lbl(r));
  const data = H.map(r=>r.total? +(r.passed/r.total*100).toFixed(1):0);
  const avg = data.reduce((a,b)=>a+b,0)/data.length;
  charts.rate = new Chart(cnv('c-rate'), {
    type:'line',
    data:{labels,
      datasets:[
        {label:'通过率 %',data,borderColor:C.info,backgroundColor:'rgba(59,130,246,.15)',fill:true,tension:.3,pointRadius:4,pointBackgroundColor:H.map(r=>r.failed?C.bad:C.ok),pointBorderColor:'#fff',pointBorderWidth:1},
        {label:'基线均值',data:H.map(()=>+avg.toFixed(1)),borderColor:'#64748b',borderDash:[6,5],borderWidth:1.5,pointRadius:0,fill:false}
      ]},
    options:{plugins:{legend:{display:true,labels:{color:'#9aa3b2',boxWidth:12,boxHeight:12,font:{size:11}}}},scales:{x:{ticks:{color:'#626b7a'}},y:{min:0,max:100,ticks:{color:'#626b7a',callback:v=>v+'%'},grid:{color:'#1b1e27'}}}}
  });
}

/* 总耗时趋势 */
function drawTime(){
  destroy('time');
  charts.time = new Chart(cnv('c-time'), {
    type:'bar',
    data:{labels:H.map(r=>lbl(r)),
      datasets:[{label:'总耗时(s)',data:H.map(r=>r.elapsed),backgroundColor:H.map(r=>r.elapsed>SLA_TOTAL?C.bad:(r.failed?C.warn:C.info)),borderRadius:4}]},
    options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#626b7a'}},y:{ticks:{color:'#626b7a'},grid:{color:'#1b1e27'}}}}
  });
}

/* 失败热点 */
function drawFail(){
  const names=uniq();
  const fails=names.map(n=>H.reduce((a,r)=>a+(caseByName(r,n)&&isFail(caseByName(r,n).status)?1:0),0));
  destroy('fail');
  charts.fail = new Chart(cnv('c-fail'), {
    type:'bar',
    data:{labels:names.map(title),datasets:[{label:'累计失败',data:fails,backgroundColor:fails.map(f=>f>0?C.bad:'#334155'),borderRadius:3}]},
    options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#626b7a'},grid:{color:'#1b1e27'}},y:{ticks:{color:'#9aa3b2',font:{size:10}}}}}
  });
}

/* 最慢用例 TOP5 */
function drawSlow(){
  const names=uniq();
  const avg=names.map(n=>({n,t:H.reduce((a,r)=>{const c=caseByName(r,n);return a+(c?c.time:0);},0)/H.length})).sort((a,b)=>b.t-a.t).slice(0,5);
  destroy('slow');
  charts.slow = new Chart(cnv('c-slow'), {
    type:'bar',
    data:{labels:avg.map(x=>title(x.n)),datasets:[{label:'平均耗时(s)',data:avg.map(x=>+x.t.toFixed(1)),backgroundColor:avg.map(x=>x.t>SLA_CASE?C.bad:C.warn),borderRadius:4}]},
    options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#626b7a'}},y:{ticks:{color:'#626b7a'},grid:{color:'#1b1e27'}}}}
  });
}

/* 单用例走势 */
function drawCase(){
  if(!selectedCase){ cnv('c-case').style.display='none'; cnv('case-meta').textContent='点击上方矩阵或下方明细的用例名查看'; return; }
  cnv('c-case').style.display='block';
  cnv('case-meta').innerHTML='正在查看：<b>'+title(selectedCase)+'</b>'+(isFlaky(selectedCase)?' <span class="flaky-tag">不稳定</span>':'');
  const data=H.map(r=>{const c=caseByName(r,selectedCase);return c?c.time:null;});
  const cols=H.map(r=>{const c=caseByName(r,selectedCase);return c?(isFail(c.status)?C.bad:(c.time>SLA_CASE?C.warn:C.info)):'#333';});
  destroy('case');
  charts.case = new Chart(cnv('c-case'), {
    type:'bar',
    data:{labels:H.map((r,i)=>lbl(r)),datasets:[{label:title(selectedCase)+' 耗时(s)',data,backgroundColor:cols,borderRadius:4}]},
    options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#626b7a'}},y:{ticks:{color:'#626b7a'},grid:{color:'#1b1e27'}}}}
  });
}

/* 稳定率矩阵 */
function matrix(){
  const names=uniq();
  cnv('flaky-count').textContent = names.filter(isFlaky).length+' 个不稳定';
  const html = '<div style="overflow-x:auto"><table class="matrix-tbl" style="min-width:620px"><thead><tr><th style="width:42%">用例</th><th>稳定率</th><th>历次运行（左旧→右新）</th></tr></thead><tbody>'+
    names.map(n=>{
      const runs = H.map(r=>caseByName(r,n));
      const pass = runs.filter(c=>c&&c.status==='PASS').length;
      const valid = runs.filter(c=>c).length;
      const rate = valid? Math.round(pass/valid*100):0;
      const cells = runs.map(c=>{
        const cls = c? (c.status==='PASS'?'pass':(c.status==='ERROR'?'err':'fail')) : 'skip';
        return '<span class="cell '+cls+'" title="'+lbl(H[0])+'" onclick="selectCase(\''+n+'\')"></span>';
      }).join('');
      const flaky = isFlaky(n);
      const rateCol = rate===100?'<span class="stable">'+rate+'%</span>'
        : rate>=80? '<span class="warn">'+rate+'%</span>'
        : '<span class="unstable">'+rate+'%</span>';
      return '<tr class="mrow" data-name="'+n+'"><td>'+title(n)+(flaky?'<span class="flaky-tag">Flaky</span>':'')+'</td><td>'+rateCol+'</td><td>'+cells+'</td></tr>';
    }).join('')+'</tbody></table></div>';
  cnv('matrix').innerHTML=html;
  cnv('matrix').querySelectorAll('.mrow').forEach(tr=>{ tr.onclick=()=>selectCase(tr.dataset.name); });
}

/* 明细表 */
function drawTable(){
  const q = searchText.toLowerCase();
  const tb = cnv('tbl'); tb.innerHTML='';
  H.slice().reverse().forEach((r,idx)=>{
    const names = r.cases.map(c=>c.name);
    if(searchText && !names.some(n=>title(n).toLowerCase().includes(q) || n.toLowerCase().includes(q))) return;
    if(caseFilter==='fail' && r.failed===0) return;
    const runNo = H.length - idx;
    const rate = r.total? (r.passed/r.total*100).toFixed(0):0;
    const row=document.createElement('tr');
    row.innerHTML = '<td style="color:var(--dim);font-variant-numeric:tabular-nums">#'+runNo+'</td>'+
      '<td style="white-space:nowrap">'+r.ts+'</td>'+
      '<td>'+(r.failed===0
        ?'<span style="color:'+C.ok+';font-weight:700">'+r.passed+'/'+r.total+' 全过</span>'
        :'<span style="color:'+C.bad+';font-weight:700">'+r.passed+'/'+r.total+' · '+r.failed+' 失败</span>')+'</td>'+
      '<td style="font-variant-numeric:tabular-nums;color:'+(rate<100?C.warn:C.txt)+'">'+rate+'%</td>'+
      '<td style="white-space:nowrap;font-variant-numeric:tabular-nums;color:'+(r.elapsed>SLA_TOTAL?C.bad:'' )+'">'+_fmt(r.elapsed)+'</td>'+
      '<td>'+r.cases.map(c=>'<span class="cname" data-name="'+c.name+'"><span class="dot" style="background:'+stColor(c.status)+'"></span>'+title(c.name)+' <span class="sec">'+Math.round(c.time)+'s</span></span>').join('')+'</td>';
    tb.appendChild(row);
  });
}

function selectCase(name){
  selectedCase = name;
  document.querySelectorAll('.cname,.mrow').forEach(x=>x.classList.remove('sel'));
  document.querySelectorAll('[data-name="'+name+'"]').forEach(x=>x.classList.add('sel'));
  cnv('c-case').scrollIntoView({behavior:'smooth',block:'center'});
  drawCase();
}

document.querySelectorAll('.pill').forEach(p=>p.onclick=()=>{
  caseFilter=p.dataset.f;
  document.querySelectorAll('.pill').forEach(x=>x.classList.toggle('on',x===p));
  drawRate();drawTime();drawTable();
});
cnv('q').addEventListener('input',e=>{searchText=e.target.value;drawTable();});
cnv('tbl').addEventListener('click',e=>{const c=e.target.closest('.cname'); if(c) selectCase(c.dataset.name);});

verdict(); kpis(); defects(); matrix(); drawRate(); drawTime(); drawFail(); drawSlow(); drawCase(); drawTable();
</script></body></html>"""
