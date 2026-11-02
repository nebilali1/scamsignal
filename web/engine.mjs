/* Portable inference and rules. No network, storage, or third-party scripts. */
export const escapeHTML = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function createEngine(data) {
  const model=data.model, vocabulary=new Map(model.features.map((t,i)=>[t,i]));
  function vectorize(text) {
    const words=text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu,'').match(/[\p{L}\p{N}_]{2,}/gu)||[];
    const terms=[...words,...words.slice(0,-1).map((w,i)=>w+' '+words[i+1])];
    const counts=new Map();
    for(const term of terms){const i=vocabulary.get(term);if(i!==undefined)counts.set(i,(counts.get(i)||0)+1);}
    const weighted=[...counts].sort((a,b)=>a[0]-b[0]).map(([i,n])=>[i,(1+Math.log(n))*model.idf[i]]);
    const norm=Math.sqrt(weighted.reduce((s,[,v])=>s+v*v,0));
    return norm?weighted.map(([i,v])=>[i,v/norm]):[];
  }
  function predict(text) {
    const vector=vectorize(text), contributions=vector.map(([i,v])=>[i,v*model.coefficients[i]]);
    const z=contributions.reduce((s,[,v])=>s+v,0)+model.intercept;
    const raw=z>=0?1/(1+Math.exp(-z)):Math.exp(z)/(1+Math.exp(z));
    return {score:vector.length?raw:null,raw_score:raw,flag:vector.length?raw>=model.threshold:null,
      terms:contributions.sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,8).filter(([,v])=>Math.abs(v)>.015).map(([i,v])=>({term:model.features[i],contribution:v}))};
  }
  function suppress(text,start,end,id){
    if(id==='secrecy')return false;
    const prefix=text.slice(0,start).split(/[.!?;\n]|\b(?:but|however)\b/i).at(-1).slice(-90);
    if(/\b(?:never|do not|don't|dont|must not|should not|shouldn't|won't|will not|no need to|not required to|avoid)\s+(?:(?:ever|again|ask you to|need to)\s+)*$/i.test(prefix))return true;
    return id==='upfront_fee' && (/^\s+(?:is |are )?(?:not required|not needed|waived|never required)\b/i.test(text.slice(end,end+28)) || /\b(?:no|without|waive(?:d)?)\s+(?:an?\s+)?$/i.test(prefix));
  }
  function rules(text){
    const findings=[];
    for(const rule of data.rules){
      const spans=[...text.matchAll(new RegExp(rule.pattern,'gi'))].filter(m=>!suppress(text,m.index,m.index+m[0].length,rule.id)).map(m=>({start:m.index,end:m.index+m[0].length,text:m[0]}));
      if(spans.length)findings.push({...rule,spans,evidence:spans[0].text});
    }
    return {findings,score:Math.min(100,findings.reduce((s,f)=>s+f.weight,0))};
  }
  function analyze(text){
    if(!text.trim())throw Error('Paste a message or select a demo to begin.');
    if(text.length>12000)throw Error('Use 12,000 characters or fewer.');
    const lines=text.split(/\r?\n/).map(l=>l.trim()).filter(Boolean);
    if(lines.length>80)throw Error('Use 80 messages or fewer, one per line.');
    const seen=new Map();let firstRule=null,firstModel=null,peak=null;
    const events=lines.map((line,i)=>{
      const parsed=line.match(/^([\p{L}\p{N}_ .'-]{1,32}):\s+(.+)$/u);
      const sender=parsed?parsed[1]:'Message',body=parsed?parsed[2]:line;
      const r=rules(body),p=predict(body),number=i+1;
      r.findings.forEach(f=>{if(!seen.has(f.id))seen.set(f.id,{...f,first_message:number});});
      if(r.findings.length&&firstRule===null)firstRule=number;
      if(p.flag&&firstModel===null)firstModel=number;
      if(p.score!==null)peak=Math.max(peak??0,p.score);
      const cumulative=Math.min(100,[...seen.values()].reduce((s,f)=>s+f.weight,0));
      const label=cumulative>=55||firstModel!==null?'Elevated concern':cumulative>0?'Review suggested':'No strong signal';
      return {number,sender,message:body,...r,model:p,cumulative,peak,findingsSoFar:[...seen.values()],label};
    });
    const firsts=[firstRule,firstModel].filter(n=>n!==null);
    return {events,firstRule,firstModel,firstSignal:firsts.length?Math.min(...firsts):null};
  }
  return {predict,rules,analyze,vectorize};
}
export function highlight(text,findings){
  const spans=findings.flatMap(f=>f.spans).sort((a,b)=>a.start-b.start),merged=[];
  for(const s of spans){const last=merged.at(-1);if(last&&s.start<=last.end)last.end=Math.max(last.end,s.end);else merged.push({...s});}
  let html='',cursor=0;for(const s of merged){html+=escapeHTML(text.slice(cursor,s.start))+'<mark>'+escapeHTML(text.slice(s.start,s.end))+'</mark>';cursor=s.end;}
  return html+escapeHTML(text.slice(cursor));
}
export function reportJSON(result,includeText=false){
  const last=result.events.at(-1);
  const report={product:'ScamSignal AI',scope:'Educational screening, not a fraud verdict',triage:last.label,rule_severity:last.cumulative,peak_message_model_score:last.peak,model_score_meaning:'Maximum SMS spam score, not a conversation fraud probability',first_rule_warning:result.firstRule,first_model_flag:result.firstModel,message_count:result.events.length,findings:last.findingsSoFar.map(({id,label,category,weight,first_message,explanation,next_step})=>({id,label,category,weight,first_message,explanation,next_step})),includes_original_text:includeText};
  if(includeText)report.messages=result.events.map(e=>({sender:e.sender,text:e.message}));
  return JSON.stringify(report,null,2);
}
