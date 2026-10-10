def _trend_html(history: list, titles: dict) -> str:
    """趋势页主体：专业测试仪表盘（Chart.js 交互式）。

    模块：顶部 KPI / 通过率趋势 / 耗时趋势 / 失败热点 / 用例稳定率矩阵 /
          最慢用例 TOP / 失败原因聚合 / 历史明细（可搜索、可点看单用例走势）。
    纯前端计算，数据由 history.json 注入。
    """
    payload = json.dumps(history, ensure_ascii=False)
    titles_json = json.dumps(titles, ensure_ascii=False)

    html = _TREND_TPL.replace("__PAYLOAD__", payload).replace("__TITLES__", titles_json)
    return html


_TREND_TPL = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>xLean 测试质量仪表盘</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#0f1115; --card:#181b22; --card2:#1f232c; --line:#2a2f3a;
  --txt:#e6e8ec; --sub:#8b93a1; --dim:#5c6470;
  --ok:#2fd57f; --bad:#ff5c6c; --warn:#ffb547; --info:#4d9fff; --skip:#6b7280;
}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;margin:0;background:var(--bg);color:var(--txt);-webkit-font-smoothing:antialiased}
.wrap{max-width:1200px;margin:0 auto;padding:28px 22px 60px}
.head{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px}
.head h1{font-size:22px;margin:0;letter-spacing:.5px}
.brand{display:flex;align-items:center;gap:10px}
.logo{width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#4d9fff,#7c5cff);display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:16px}
.sub{color:var(--sub);font-size:13px}
.tag{display:inline-block;padding:3px 10px;border-radius:999px;background:var(--card2);border:1px solid var(--line);color:var(--sub);font-size:12px}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:18px}
@media(max-width:1000px){.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:560px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;position:relative;overflow:hidden}
.kpi::after{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--ac,#4d9fff)}
.kpi .v{font-size:26px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1}
.kpi .v small{font-size:14px;font-weight:600;color:var(--sub)}
.kpi .t{font-size:12px;color:var(--sub);margin-top:8px}
.kpi .d{font-size:11px;color:var(--dim);margin-top:3px}
.grid{display:grid;gap:14px;margin-bottom:14px}
.g2{grid-template-columns:1fr 1fr}
.g32{grid-template-columns:2fr 1fr}
@media(max-width:900px){.g2,.g32{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}
.card h2{margin:0 0 3px;font-size:15px;font-weight:700}
.card .meta{color:var(--dim);font-size:12px;margin-bottom:14px}
canvas{max-height:300px}
.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.pill{padding:6px 13px;border-radius:999px;border:1px solid var(--line);background:var(--card);cursor:pointer;font-size:12.5px;color:var(--sub);user-select:none;transition:.15s}
.pill:hover{border-color:var(--info);color:var(--txt)}
.pill.on{background:var(--info);color:#fff;border-color:var(--info)}
.search{margin-left:auto;background:var(--card2);border:1px solid var(--line);border-radius:8px;padding:7px 12px;color:var(--txt);font-size:13px;width:200px;outline:none}
.search:focus{border-color:var(--info)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:600;padding:9px 10px;border-bottom:1px solid var(--line);font-size:12px;white-space:nowrap}
td{padding:10px;border-bottom:1px solid #1d2028;vertical-align:top}
tr:hover td{background:#1b1f27}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.cname{display:inline-block;cursor:pointer;padding:2px 7px;border-radius:5px;margin:1px 2px 1px 0;transition:.12s;border:1px solid transparent}
.cname:hover{background:var(--card2);border-color:var(--line)}
.cname.sel,.mrow.sel{background:rgba(77,159,255,.14);border-color:var(--info)}
.sec{font-size:11px;color:var(--dim)}
.insight{background:linear-gradient(135deg,rgba(255,181,71,.08),rgba(255,92,108,.05));border:1px solid rgba(255,181,71,.25);border-radius:12px;padding:14px 16px;margin-bottom:14px}
.insight h3{margin:0 0 8px;font-size:13px;color:var(--warn)}
.insight ul{margin:0;padding-left:18px;color:var(--txt);font-size:13px;line-height:1.7}
.footer{color:var(--dim);font-size:11px;text-align:center;margin-top:24px}
</style></head><body><div class="wrap">

<div class="head">
  <div class="brand">
    <div class="logo">XL</div>
    <div>
      <h1>xLean 测试质量仪表盘</h1>
      <div class="sub">Appium 回归 · 历史趋势 · 稳定性分析</div>
    </div>
  </div>
  <span class="tag" id="rangeTag">最近 __N__ 次运行</span>
</div>

<div class="insight"><h3>&#9889; 洞察与建议</h3><ul id="insights"></ul></div>

<div class="kpis" id="kpis"></div>

<div class="grid g2">
  <div class="card"><h2>通过率趋势</h2><div class="meta">每次运行 passed / total 百分比</div><canvas id="c-rate"></canvas></div>
  <div class="card"><h2>总耗时趋势</h2><div class="meta">每次运行累计秒数</div><canvas id="c-time"></canvas></div>
</div>

<div class="grid g32">
  <div class="card"><h2>用例稳定率矩阵</h2><div class="meta">每行一个用例，色块=单次运行结果（绿=过 红=挂），点任一行看走势</div><div id="matrix"></div></div>
  <div class="card"><h2>最慢用例 TOP5</h2><div class="meta">按历史平均耗时排序</div><canvas id="c-slow"></canvas></div>
</div>

<div class="grid g2">
  <div class="card"><h2>失败热点</h2><div class="meta">各用例累计失败次数</div><canvas id="c-fail"></canvas></div>
  <div class="card"><h2>单用例耗时波动</h2><div class="meta" id="case-meta">点击上方矩阵或下方明细的用例名查看</div><canvas id="c-case"></canvas></div>
</div>

<div class="card">
  <div class="toolbar">
    <h2 style="margin:0">历史明细</h2>
    <span class="pill on" data-f="all">全部</span>
    <span class="pill" data-f="fail">失败过的</span>
    <input class="search" id="q" placeholder="搜索用例&#8230;">
  </div>
  <table><thead><tr><th>时间</th><th>结果</th><th>耗时</th><th>用例明细</th></tr></thead><tbody id="tbl"></tbody></table>
</div>

<div class="footer">数据源 history.json · 每次跑 Appium 回归自动追加 · 点用例名可下钻历史耗时</div>
</div>

<script>
const H = __PAYLOAD__;
const TITLES = __TITLES__;
const title = n => TITLES[n] || n;
const C = {ok:'#2fd57f',bad:'#ff5c6c',warn:'#ffb547',info:'#4d9fff',skip:'#6b7280'};

let caseFilter='all', selectedCase=null, searchText='';
let charts={};
function destroy(n){ if(charts[n]){charts[n].destroy(); delete charts[n];} }
function cnv(id){ return document.getElementById(id); }

const lbl = r => r.ts.slice(5,16);
const stColor = s => ({PASS:C.ok,FAIL:C.bad,ERROR:C.bad,SKIP:C.skip}[s]||C.skip);

function kpis(){
  const last = H[H.length-1];
  const total = H.reduce((a,r)=>a+r.total,0);
  const passed = H.reduce((a,r)=>a+r.passed,0);
  const rate = total? passed/total : 0;
  const recent = H.slice(-3);
  const stable = recent.length? recent.filter(r=>r.failed===0).length/recent.length : 0;
  const avgTime = total? H.reduce((a,r)=>a+r.elapsed,0)/H.length : 0;
  const best = H.reduce((a,r)=>Math.min(a,r.elapsed),1e9);
  const worst = H.reduce((a,r)=>Math.max(a,r.elapsed),0);
  const k = (v,small,t,d,ac)=>
    '<div class="kpi" style="--ac:'+ac+'"><div class="v">'+v+(small?'<small> '+small+'</small>':'')+'</div><div class="t">'+t+'</div><div class="d">'+d+'</div></div>';
  cnv('kpis').innerHTML =
    k(H.length,'','运行次数','累计 '+H.length+' 次回归',C.info)+
    k(last.passed,'/'+last.total,'最近一次','最新 '+last.ts.slice(0,16), last.failed? C.bad:C.ok)+
    k((rate*100).toFixed(1),'%','累计通过率',passed+' / '+total,C.ok)+
    k((stable*100).toFixed(0),'%','近3次稳定率',recent.length+' 次中 '+recent.filter(r=>r.failed===0).length+' 次全过',C.warn)+
    k(Math.round(avgTime),'s','平均耗时','最快 '+Math.round(best)+'s / 最慢 '+Math.round(worst)+'s',C.info)+
    k(H.reduce((a,r)=>a+r.failed,0),'','累计失败','历史失败总条数',C.bad);
}

function insights(){
  const li = [];
  const last = H[H.length-1];
  if(last.failed>0) li.push('最近一次有 <b>'+last.failed+'</b> 条失败，建议优先排查。');
  const names = [...new Set(H.flatMap(r=>r.cases.map(c=>c.name)))];
  const consecutive = names.filter(n=>{
    const tail = H.slice(-2);
    return tail.every(r=>{const c=r.cases.find(x=>x.name===n); return c&&['FAIL','ERROR'].includes(c.status);});
  });
  if(consecutive.length) li.push('连续 2 次失败的用例：<b>'+consecutive.map(title).join('、')+'</b>');
  const avg = names.map(n=>({n, t:H.reduce((a,r)=>{const c=r.cases.find(x=>x.name===n);return a+(c?c.time:0);},0)/H.length})).sort((a,b)=>b.t-a.t);
  if(avg.length) li.push('最慢用例：<b>'+title(avg[0].n)+'</b>（平均 '+Math.round(avg[0].t)+'s）');
  const half = Math.ceil(H.length/2);
  const firstHalf = H.slice(0,half).reduce((a,r)=>a+r.elapsed,0)/(half||1);
  const secondHalf = H.slice(half).reduce((a,r)=>a+r.elapsed,0)/((H.length-half)||1);
  if(H.length>=4 && secondHalf>firstHalf*1.15) li.push('耗时呈上升趋势（前段 '+Math.round(firstHalf)+'s → 后段 '+Math.round(secondHalf)+'s），关注设备性能或等待窗口。');
  else if(H.length>=4 && secondHalf<firstHalf*0.85) li.push('耗时在下降（'+Math.round(firstHalf)+'s → '+Math.round(secondHalf)+'s），优化见效。');
  cnv('insights').innerHTML = li.length? li.map(x=>'<li>'+x+'</li>').join('') : '<li>暂无异常，一切健康。</li>';
}

function visibleRuns(){
  return H.map((r,i)=>({r,i})).filter(x=>caseFilter==='all'||x.r.failed>0);
}

function drawRate(){
  const vr = visibleRuns();
  destroy('rate');
  charts.rate = new Chart(cnv('c-rate'), {
    type:'line',
    data:{labels:vr.map(x=>lbl(x.r)),
      datasets:[{label:'通过率 %',data:vr.map(x=>x.r.total? +(x.r.passed/x.r.total*100).toFixed(1):0),
        borderColor:C.info,backgroundColor:'rgba(77,159,255,.15)',fill:true,tension:.32,pointRadius:4,pointBackgroundColor:C.info}]},
    options:{plugins:{legend:{display:false}},scales:{y:{min:0,max:100,ticks:{callback:v=>v+'%'}}}}
  });
}

function drawTime(){
  const vr = visibleRuns();
  destroy('time');
  charts.time = new Chart(cnv('c-time'), {
    type:'bar',
    data:{labels:vr.map(x=>lbl(x.r)),
      datasets:[{label:'总耗时(s)',data:vr.map(x=>x.r.elapsed),backgroundColor:vr.map(x=>x.r.failed?C.bad:C.info),borderRadius:4}]},
    options:{plugins:{legend:{display:false}}}
  });
}

function drawFail(){
  const names=[...new Set(H.flatMap(r=>r.cases.map(c=>c.name)))];
  const fails=names.map(n=>H.reduce((a,r)=>a+(r.cases.find(c=>c.name===n&&['FAIL','ERROR'].includes(c.status))?1:0),0));
  destroy('fail');
  charts.fail = new Chart(cnv('c-fail'), {
    type:'bar',
    data:{labels:names.map(title),datasets:[{label:'累计失败',data:fails,backgroundColor:C.bad,borderRadius:3}]},
    options:{indexAxis:'y',plugins:{legend:{display:false}}}
  });
}

function drawSlow(){
  const names=[...new Set(H.flatMap(r=>r.cases.map(c=>c.name)))];
  const avg=names.map(n=>({n,t:H.reduce((a,r)=>{const c=r.cases.find(x=>x.name===n);return a+(c?c.time:0);},0)/H.length})).sort((a,b)=>b.t-a.t).slice(0,5);
  destroy('slow');
  charts.slow = new Chart(cnv('c-slow'), {
    type:'bar',
    data:{labels:avg.map(x=>title(x.n)),datasets:[{label:'平均耗时(s)',data:avg.map(x=>+x.t.toFixed(1)),backgroundColor:C.warn,borderRadius:4}]},
    options:{plugins:{legend:{display:false}}}
  });
}

function drawCase(){
  if(!selectedCase){ cnv('c-case').style.display='none'; cnv('case-meta').textContent='点击上方矩阵或下方明细的用例名查看'; return; }
  cnv('c-case').style.display='block';
  cnv('case-meta').innerHTML='正在查看：<b>'+title(selectedCase)+'</b>';
  const data=H.map(r=>{const c=r.cases.find(x=>x.name===selectedCase);return c?c.time:null;});
  const cols=H.map(r=>{const c=r.cases.find(x=>x.name===selectedCase);return c?(['FAIL','ERROR'].includes(c.status)?C.bad:C.info):'#333';});
  destroy('case');
  charts.case = new Chart(cnv('c-case'), {
    type:'bar',
    data:{labels:H.map((r,i)=>lbl(r)),datasets:[{label:title(selectedCase)+' 耗时(s)',data,backgroundColor:cols,borderRadius:4}]},
    options:{plugins:{legend:{display:false}}}
  });
}

function matrix(){
  const names=[...new Set(H.flatMap(r=>r.cases.map(c=>c.name)))];
  const html = '<div style="overflow-x:auto"><table style="min-width:600px"><thead><tr><th style="width:40%">用例</th><th>稳定率</th><th>历次运行</th></tr></thead><tbody>'+
    names.map(n=>{
      const runs = H.map(r=>r.cases.find(c=>c.name===n));
      const pass = runs.filter(c=>c&&c.status==='PASS').length;
      const valid = runs.filter(c=>c).length;
      const rate = valid? Math.round(pass/valid*100):0;
      const cells = runs.map(c=>c
        ?'<span class="dot" style="background:'+stColor(c.status)+'" title="'+c.time+'s"></span>'
        :'<span class="dot" style="background:#333"></span>').join('');
      const rateCol = rate===100?'<span style="color:'+C.ok+'">'+rate+'%</span>'
        : rate>=80? '<span style="color:'+C.warn+'">'+rate+'%</span>'
        : '<span style="color:'+C.bad+'">'+rate+'%</span>';
      return '<tr class="mrow" data-name="'+n+'" style="cursor:pointer"><td>'+title(n)+'</td><td>'+rateCol+'</td><td>'+cells+'</td></tr>';
    }).join('')+'</tbody></table></div>';
  cnv('matrix').innerHTML=html;
  cnv('matrix').querySelectorAll('.mrow').forEach(tr=>{
    tr.onclick=()=>{ selectCase(tr.dataset.name); };
  });
}

function drawTable(){
  const q = searchText.toLowerCase();
  const tb = cnv('tbl'); tb.innerHTML='';
  H.slice().reverse().forEach(r=>{
    const names = r.cases.map(c=>c.name);
    if(searchText && !names.some(n=>title(n).toLowerCase().includes(q) || n.toLowerCase().includes(q))) return;
    if(caseFilter==='fail' && r.failed===0) return;
    const row=document.createElement('tr');
    row.innerHTML = '<td style="white-space:nowrap">'+r.ts+'</td>'+
      '<td>'+(r.failed===0
        ?'<span style="color:'+C.ok+';font-weight:700">'+r.passed+'/'+r.total+' 全过</span>'
        :'<span style="color:'+C.bad+';font-weight:700">'+r.passed+'/'+r.total+' · '+r.failed+' 失败</span>')+'</td>'+
      '<td style="white-space:nowrap;font-variant-numeric:tabular-nums">'+Math.round(r.elapsed)+'s</td>'+
      '<td>'+r.cases.map(c=>'<span class="cname" data-name="'+c.name+'"><span class="dot" style="background:'+stColor(c.status)+'"></span>'+title(c.name)+' <span class="sec">'+c.time+'s</span></span>').join('')+'</td>';
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

kpis(); insights(); matrix(); drawRate(); drawTime(); drawFail(); drawSlow(); drawCase(); drawTable();
</script></body></html>"""


