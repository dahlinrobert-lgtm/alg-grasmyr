
const elkHarvest=[
{season:"2013/2014",year:2013,total:109,adult:53,calves:56,target:133,area:26777},
{season:"2014/2015",year:2014,total:112,adult:57,calves:55,target:143,area:32355},
{season:"2015/2016",year:2015,total:103,adult:58,calves:45,target:132,area:32355},
{season:"2016/2017",year:2016,total:106,adult:54,calves:52,target:100,area:32355},
{season:"2017/2018",year:2017,total:98,adult:55,calves:43,target:100,area:32355},
{season:"2018/2019",year:2018,total:123,adult:66,calves:57,target:145,area:35506},
{season:"2019/2020",year:2019,total:127,adult:71,calves:56,target:163,area:35506},
{season:"2020/2021",year:2020,total:120,adult:66,calves:54,target:131,area:35567},
{season:"2021/2022",year:2021,total:114,adult:70,calves:44,target:128,area:35567},
{season:"2022/2023",year:2022,total:118,adult:69,calves:49,target:127,area:35567},
{season:"2023/2024",year:2023,total:105,adult:62,calves:43,target:119,area:37133},
{season:"2024/2025",year:2024,total:112,adult:64,calves:48,target:135,area:37133},
{season:"2025/2026",year:2025,total:116,adult:71,calves:45,target:190,area:37133}];
const elkObs=[
{season:"2013/2014",year:2013,obs:0.0659,hours:6978,calves:0.491,significant:"Ja"},
{season:"2014/2015",year:2014,obs:0.069,hours:6724,calves:0.691,significant:"Ja"},
{season:"2015/2016",year:2015,obs:0.057,hours:4838,calves:0.598,significant:"Nej"},
{season:"2016/2017",year:2016,obs:0.0756,hours:3860,calves:0.677,significant:"Nej"},
{season:"2017/2018",year:2017,obs:0.0652,hours:4538,calves:0.714,significant:"Nej"},
{season:"2018/2019",year:2018,obs:0.0607,hours:5350,calves:0.5,significant:"Ja"},
{season:"2019/2020",year:2019,obs:0.056,hours:2323,calves:0.656,significant:"Nej"},
{season:"2020/2021",year:2020,obs:0.0551,hours:3502,calves:0.466,significant:"Nej"},
{season:"2021/2022",year:2021,obs:0.0447,hours:3716,calves:0.398,significant:"Nej"},
{season:"2022/2023",year:2022,obs:0.0601,hours:3163,calves:0.732,significant:"Nej"},
{season:"2023/2024",year:2023,obs:0.0498,hours:6211,calves:0.591,significant:"Ja"},
{season:"2024/2025",year:2024,obs:0.0542,hours:5020,calves:0.804,significant:"Ja"},
{season:"2025/2026",year:2025,obs:0.0386,hours:4353,calves:0.698,significant:"Nej"}];
const elkAge=[
{season:"2013/2014",year:2013,male:1.9,nMale:16,female:2.5,nFemale:20},
{season:"2014/2015",year:2014,male:2.4,nMale:28,female:3.7,nFemale:23},
{season:"2015/2016",year:2015,male:2.5,nMale:27,female:2.2,nFemale:23},
{season:"2016/2017",year:2016,male:2,nMale:21,female:3.1,nFemale:16},
{season:"2017/2018",year:2017,male:2.6,nMale:18,female:4.3,nFemale:11},
{season:"2018/2019",year:2018,male:3.1,nMale:10,female:3.2,nFemale:6},
{season:"2019/2020",year:2019,male:2.6,nMale:18,female:2.4,nFemale:12},
{season:"2020/2021",year:2020,male:2.9,nMale:20,female:3.5,nFemale:14},
{season:"2021/2022",year:2021,male:2.6,nMale:20,female:2.9,nFemale:17},
{season:"2022/2023",year:2022,male:2,nMale:2,female:7.5,nFemale:2},
{season:"2023/2024",year:2023,male:3.2,nMale:16,female:3,nFemale:11},
{season:"2024/2025",year:2024,male:2.6,nMale:19,female:4,nFemale:15},
{season:"2025/2026",year:2025,male:3.3,nMale:20,female:3.1,nFemale:17}];
const grasmyr=[
{season:"2010/2011",year:2010,total:15,adult:9,calves:6,target:13,area:4795},
{season:"2011/2012",year:2011,total:17,adult:11,calves:6,target:17,area:4795},
{season:"2012/2013",year:2012,total:15,adult:7,calves:8,target:15,area:4795}];
const modes={
 harvest:{title:"Avskjutning av älg",description:"Rapporterat antal fällda älgar per jaktår. Måltal visas som separat jämförelseserie.",series:[{key:"total",label:"Totalt fällda",color:"#244c3d"},{key:"target",label:"Avskjutningsmål",color:"#bb7b2a"}]},
 obs:{title:"Älgobservationer",description:"Älgobs per mantimme. Det är en observationsindikator och inte en direkt uppskattning av totalt antal älgar.",series:[{key:"obs",label:"Älgobs per mantimme",color:"#557ca8"}]},
 age:{title:"Medelålder på undersökta vuxna älgar",description:"Medelålder för handjur och hondjur, med antal undersökta djur i tabellen. Små urval kan ge stora svängningar.",series:[{key:"male",label:"Handjur, år",color:"#244c3d"},{key:"female",label:"Hondjur, år",color:"#bb7b2a"}]}
};
let mode="harvest";
const byId=id=>document.getElementById(id);
const fmt=(n,d=1)=>n===null||n===undefined||Number.isNaN(n)?"Saknas":Number(n).toLocaleString("sv-SE",{maximumFractionDigits:d});
function selectedData(){
 const area=byId("areaSelect").value;let arr=area==="grasmyr"?grasmyr:(mode==="harvest"?elkHarvest:mode==="obs"?elkObs:elkAge);
 const from=Number(byId("startYear").value),to=Number(byId("endYear").value);
 return arr.filter(d=>d.year>=from&&d.year<=to);
}
function drawChart(svg, data, series, opts={}){
 const w=900,h=320,ml=54,mr=22,mt=18,mb=48,pw=w-ml-mr,ph=h-mt-mb;
 svg.innerHTML="";
 if(!data.length){svg.innerHTML='<text x="450" y="150" text-anchor="middle" fill="#63736b" font-size="16">Inga rapporterade värden för valt intervall</text>';return;}
 const all=data.flatMap(d=>series.map(s=>d[s.key])).filter(v=>Number.isFinite(v));
 let min=0,max=Math.max(...all)*1.16;if(max===min)max=1;if(opts.zeroLine===false)min=Math.min(...all)*.8;
 const y=v=>mt+ph-(v-min)/(max-min)*ph;
 const x=i=>data.length===1?ml+pw/2:ml+i*pw/(data.length-1);
 for(let i=0;i<=4;i++){const val=min+(max-min)*i/4,yy=y(val);svg.insertAdjacentHTML("beforeend",'<line x1="'+ml+'" y1="'+yy+'" x2="'+(w-mr)+'" y2="'+yy+'" stroke="#e5ebe4"/><text x="'+(ml-10)+'" y="'+(yy+4)+'" text-anchor="end" fill="#63736b" font-size="11">'+fmt(val,2)+'</text>');}
 data.forEach((d,i)=>svg.insertAdjacentHTML("beforeend",'<text x="'+x(i)+'" y="'+(h-18)+'" text-anchor="middle" fill="#63736b" font-size="10">'+d.season.slice(2,4)+'</text>'));
 series.forEach(s=>{
  let points=data.map((d,i)=>d[s.key]===undefined||d[s.key]===null?null:[x(i),y(d[s.key])]);
  let seg=[];const flush=()=>{if(seg.length>1)svg.insertAdjacentHTML("beforeend",'<polyline fill="none" stroke="'+s.color+'" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="'+seg.map(p=>p.join(",")).join(" ")+'"/>');seg=[];};
  points.forEach(p=>{if(p){seg.push(p)}else flush()});flush();
  points.forEach((p,i)=>{if(p)svg.insertAdjacentHTML("beforeend",'<circle cx="'+p[0]+'" cy="'+p[1]+'" r="4.3" fill="'+s.color+'" stroke="white" stroke-width="1.5"><title>'+data[i].season+': '+fmt(data[i][s.key],3)+'</title></circle>');});
 });
 svg.insertAdjacentHTML("beforeend",'<line x1="'+ml+'" y1="'+(mt+ph)+'" x2="'+(w-mr)+'" y2="'+(mt+ph)+'" stroke="#adbaaf"/>');
}
function setTable(data){
 const table=byId("algTable"),head=table.querySelector("thead"),body=table.querySelector("tbody");
 let headers,rows;
 if(mode==="harvest" && byId("areaSelect").value==="grasmyr"){
  headers=["Jaktår","Totalt fällda","Vuxna","Kalvar","Avskjutningsmål","Registrerad areal"];
  rows=data.map(d=>[d.season,fmt(d.total,0),fmt(d.adult,0),fmt(d.calves,0),fmt(d.target,0),fmt(d.area,0)+" ha"]);
 } else if(mode==="harvest"){
  headers=["Jaktår","Totalt fällda","Vuxna","Kalvar","Avskjutningsmål","Registrerad areal"];
  rows=data.map(d=>[d.season,fmt(d.total,0),fmt(d.adult,0),fmt(d.calves,0),fmt(d.target,0),fmt(d.area,0)+" ha"]);
 } else if(mode==="obs"){
  headers=["Jaktår","Älgobs/mantimme","Mantimmar","Kalvar per hondjur","Statistiskt säkerställd"];
  rows=data.map(d=>[d.season,fmt(d.obs,4),fmt(d.hours,0),fmt(d.calves,3),d.significant||"—"]);
 } else {
  headers=["Jaktår","Medelålder handjur","Antal handjur","Medelålder hondjur","Antal hondjur"];
  rows=data.map(d=>[d.season,fmt(d.male,1),fmt(d.nMale,0),fmt(d.female,1),fmt(d.nFemale,0)]);
 }
 head.innerHTML="<tr>"+headers.map(x=>"<th>"+x+"</th>").join("")+"</tr>";
 body.innerHTML=rows.map(r=>"<tr>"+r.map(x=>"<td>"+x+"</td>").join("")+"</tr>").join("");
}
function renderElk(){
 const area=byId("areaSelect").value;
 if(area==="grasmyr" && mode!=="harvest"){byId("algChart").innerHTML='<text x="450" y="150" text-anchor="middle" fill="#63736b" font-size="15">Ingen användbar serie för vald statistiktyp</text>';byId("algLegend").innerHTML="";byId("algTable").querySelector("thead").innerHTML="<tr><th>Status</th></tr>";byId("algTable").querySelector("tbody").innerHTML='<tr><td>Portalens test gav inga användbara data. Detta är inte noll avskjutning.</td></tr>';byId("algDescription").textContent="Ingen användbar serie i undersökt Gräsmyrs VVO-underlag.";byId("algNote").textContent="Gräsmyrs VVO har här endast avskjutningsdata för tre säsonger. Älgobs och övriga indikatorer saknar verifierade data i försöken.";return;}
 const data=selectedData(),spec=modes[mode];drawChart(byId("algChart"),data,spec.series);
 byId("algLegend").innerHTML=spec.series.map(s=>'<span><i class="swatch" style="background:'+s.color+'"></i>'+s.label+'</span>').join("");
 byId("algDescription").textContent=spec.description;
 setTable(data);
 byId("algNote").textContent=area==="grasmyr"?"Historisk Gräsmyrs VVO-serie (portal-ID 718148). Endast de tre redovisade jaktåren har verifierad avskjutning här.":"Hörneåns ÄSO (portal-ID 724577). Områdets registrerade areal ändras mellan vissa rapportår; tolka jämförelser över tid tillsammans med gränshistoriken.";
}
document.querySelectorAll("[data-mode]").forEach(btn=>btn.addEventListener("click",()=>{
 mode=btn.dataset.mode;document.querySelectorAll("[data-mode]").forEach(b=>b.setAttribute("aria-pressed",String(b===btn)));renderElk();
}));
["areaSelect","startYear","endYear"].forEach(id=>byId(id).addEventListener("change",()=>{
 const start=Number(byId("startYear").value),end=Number(byId("endYear").value);
 if(start>end){byId("endYear").value=String(start>2020?2025:start>2017?2019:2022);}
 renderElk();
}));
byId("resetFilters").addEventListener("click",()=>{byId("areaSelect").value="hornean";byId("startYear").value="2013";byId("endYear").value="2025";mode="harvest";document.querySelectorAll("[data-mode]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.mode===mode)));renderElk();});
drawChart(byId("deerChart"),[],[{key:"total",label:"Totalt fällda",color:"#244c3d"}]);
byId("deerMetric").addEventListener("change",()=>{byId("deerStatus").textContent="Inga verifierade kronhjortsvärden har laddats in. Vald indikator: "+byId("deerMetric").selectedOptions[0].text+". Ingen linje betyder okänd rapportering, inte noll avskjutning.";});
byId("deerPeriod").addEventListener("change",()=>{byId("deerStatus").textContent="Kronhjortsdata saknas ännu för det valda intervallet; lägg endast in verifierade årsrapporter från Hörneåns KSO.";});
renderElk();
