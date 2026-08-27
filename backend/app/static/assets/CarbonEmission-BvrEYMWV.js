import{K as g}from"./KpiCard-DvndKWDN.js";import{C as f}from"./ChartCard-39KwjBMD.js";import{D as R}from"./DataTable-BGWb4t_a.js";import{a as T}from"./index-CVGeu6FU.js";import{t as x,P as y,s as E,a as k,b as B}from"./useEChart-Rh31nB0w.js";import{o as j,c as C,b as s,g as n,w as D,F as A,r as F,j as p,i as $,l as m,d as H,p as M,E as S}from"./index-DFrNyjyl.js";const U={class:"page"},Y={class:"page-head"},P={class:"kpi-grid"},V={class:"two-col"},X={__name:"CarbonEmission",setup(W){const d=p(!1),v=p(!1),e=p({}),h=p(null),b=p(null),w=[{prop:"period",label:"月份",width:140},{prop:"emission",label:"排放量 (tCO₂)",minWidth:150,align:"right",sortable:!0,formatter:t=>Number(t.emission||0).toLocaleString("zh-CN")}];function _(){var a,i,l;const t=e.value;(a=t.bySource)!=null&&a.length&&h.value&&h.value.setOption({color:y,tooltip:{...x,trigger:"item",formatter:o=>`${o.name}<br/><b>${Number(o.value).toLocaleString("zh-CN")} tCO₂</b> (${o.percent}%)`},legend:{bottom:0,textStyle:{color:"#55655f",fontSize:12}},series:[{type:"pie",radius:["44%","68%"],center:["50%","44%"],itemStyle:{borderColor:"#fff",borderWidth:2,borderRadius:6},label:{formatter:`{b}
{d}%`,fontSize:11,color:"#55655f"},data:t.bySource}]}),(l=(i=t.trend)==null?void 0:i.axis)!=null&&l.length&&b.value&&b.value.setOption({color:[y[3]],tooltip:{...x,trigger:"axis"},grid:{left:12,right:20,top:30,bottom:8,containLabel:!0},xAxis:{type:"category",data:t.trend.axis,axisLabel:k,axisLine:B,axisTick:{show:!1}},yAxis:{type:"value",name:"tCO₂",nameTextStyle:{color:"#8b988f"},axisLabel:k,splitLine:E},series:[{name:"碳排放量",type:"bar",barWidth:14,itemStyle:{borderRadius:[5,5,0,0],color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"#d64545"},{offset:1,color:"rgba(214,69,69,0.25)"}]}},data:t.trend.data}]})}async function L(){d.value=!0;try{e.value=await T.carbonEmission(),_()}catch{}finally{d.value=!1}}async function O(){v.value=!0;try{const t=z(e.value),a=new Blob([t],{type:"text/html;charset=utf-8"}),i=URL.createObjectURL(a),l=document.createElement("a");l.href=i,l.download=`碳排放核算年度报告_${new Date().getFullYear()}.html`,document.body.appendChild(l),l.click(),l.remove(),URL.revokeObjectURL(i),S.success("年度报告已导出（HTML格式）")}catch{S.error("报告导出失败，请稍后重试")}finally{v.value=!1}}function z(t){var o,c,u;const a=new Date().getFullYear(),i=(t.bySource||[]).map(r=>`
    <tr>
      <td>${r.name}</td>
      <td style="text-align:right;">${Number(r.value).toLocaleString("zh-CN")}</td>
      <td style="text-align:right;">${r.share}%</td>
    </tr>
  `).join(""),l=(((o=t.trend)==null?void 0:o.axis)||[]).map((r,N)=>`
    <tr>
      <td>${r}</td>
      <td style="text-align:right;">${Number(t.trend.data[N]||0).toLocaleString("zh-CN")}</td>
    </tr>
  `).join("");return`
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>${a}年度碳排放核算报告</title>
  <style>
    body { font-family: "Microsoft YaHei", Arial, sans-serif; padding: 40px; color: #333; }
    h1 { text-align: center; color: #16241f; border-bottom: 3px solid #0c8f7a; padding-bottom: 15px; }
    h2 { color: #0c8f7a; margin-top: 30px; border-left: 4px solid #0c8f7a; padding-left: 12px; }
    .header-info { text-align: center; margin: 20px 0; color: #666; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 10px; }
    th { background: #f5f7fa; font-weight: bold; }
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
    .kpi-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; text-align: center; }
    .kpi-label { font-size: 14px; color: #666; }
    .kpi-value { font-size: 24px; font-weight: bold; color: #16241f; margin: 8px 0; }
    .kpi-unit { font-size: 12px; color: #999; }
    .footer { margin-top: 40px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee; padding-top: 15px; }
  </style>
</head>
<body>
  <h1>${a}年度碳排放核算报告</h1>
  <div class="header-info">
    <p>报告生成时间：${new Date().toLocaleString("zh-CN")}</p>
    <p>核算依据：GB/T 32151 系列标准及行业核算指南</p>
  </div>

  <h2>一、核心指标概览</h2>
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">累计排放总量</div>
      <div class="kpi-value">${t.total??"--"}</div>
      <div class="kpi-unit">${t.unit||"tCO₂"}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">排放强度</div>
      <div class="kpi-value">${t.intensity??"--"}</div>
      <div class="kpi-unit">${t.intensity_unit||""}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">最大排放源</div>
      <div class="kpi-value" style="font-size:18px;">${((c=t.topSource)==null?void 0:c.name)||"--"}</div>
      <div class="kpi-unit">${t.topSource?`${t.topSource.value.toLocaleString("zh-CN")} tCO₂ · ${t.topSource.share}%`:""}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">预警信息</div>
      <div class="kpi-value">${((u=t.warnings)==null?void 0:u.length)??0}</div>
      <div class="kpi-unit">条</div>
    </div>
  </div>

  <h2>二、按能源来源拆分</h2>
  <table>
    <thead>
      <tr>
        <th>能源类型</th>
        <th style="text-align:right;">排放量 (tCO₂)</th>
        <th style="text-align:right;">占比</th>
      </tr>
    </thead>
    <tbody>
      ${i||'<tr><td colspan="3" style="text-align:center;">暂无数据</td></tr>'}
    </tbody>
  </table>

  <h2>三、月度排放趋势</h2>
  <table>
    <thead>
      <tr>
        <th>月份</th>
        <th style="text-align:right;">排放量 (tCO₂)</th>
      </tr>
    </thead>
    <tbody>
      ${l||'<tr><td colspan="2" style="text-align:center;">暂无数据</td></tr>'}
    </tbody>
  </table>

  <h2>四、预警信息</h2>
  ${(t.warnings||[]).length>0?`
    <ul>
      ${(t.warnings||[]).map(r=>`<li>${r.content}</li>`).join("")}
    </ul>
  `:"<p>当前无预警信息。</p>"}

  <div class="footer">
    <p>本报告由工业企业和园区数字化能碳管理中心自动生成</p>
    <p>© ${a} 能碳管理中心系统 v0.2.0</p>
  </div>
</body>
</html>
  `.trim()}return j(L),(t,a)=>{var o,c;const i=$("el-button"),l=$("el-alert");return m(),C("div",U,[s("div",Y,[a[1]||(a[1]=s("div",null,[s("h2",null,"碳排放核算"),s("p",null,"总量与强度核算、来源拆分、月度趋势与预警 · 依据 GB/T 32151 系列及行业核算标准")],-1)),n(i,{type:"primary",loading:v.value,onClick:O},{default:D(()=>[...a[0]||(a[0]=[H(" 导出年度报告 (HTML) ",-1)])]),_:1},8,["loading"])]),s("div",P,[n(g,{label:"累计排放总量",value:e.value.total??"--",unit:e.value.unit||"tCO₂",accent:"danger",sub:`区间 ${(e.value.range||[]).join(" ~ ")}`},null,8,["value","unit","sub"]),n(g,{label:"排放强度",value:e.value.intensity??"--",unit:e.value.intensity_unit||"",decimals:4,accent:"blue"},null,8,["value","unit"]),n(g,{label:"最大排放源",value:((o=e.value.topSource)==null?void 0:o.name)||"--",decimals:0,accent:"brand",sub:e.value.topSource?`${e.value.topSource.value.toLocaleString("zh-CN")} tCO₂ · ${e.value.topSource.share}%`:""},null,8,["value","sub"]),n(g,{label:"预警信息",value:((c=e.value.warnings)==null?void 0:c.length)??0,unit:"条",decimals:0,accent:"amber"},null,8,["value"])]),(m(!0),C(A,null,F(e.value.warnings||[],(u,r)=>(m(),M(l,{key:r,title:u.content,type:"warning","show-icon":"",closable:!1},null,8,["title"]))),128)),s("div",V,[n(f,{ref_key:"pieRef",ref:h,title:"按能源来源拆分",desc:"本期累计 · tCO₂",loading:d.value,height:"320px"},null,8,["loading"]),n(f,{ref_key:"trendRef",ref:b,title:"月度排放趋势",desc:"单位 tCO₂",loading:d.value,height:"320px"},null,8,["loading"])]),n(R,{title:"月度核算明细",columns:w,data:e.value.items||[],loading:d.value,"max-height":"400","show-index":""},null,8,["data","loading"])])}}};export{X as default};
