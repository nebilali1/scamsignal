import fs from 'node:fs';
import {createEngine,highlight,reportJSON} from '../web/engine.mjs';
const html=fs.readFileSync(new URL('../web/dist/index.html',import.meta.url),'utf8');
const data=JSON.parse(html.match(/<script id="scamsignal-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const engine=createEngine(data);
const input=JSON.parse(fs.readFileSync(0,'utf8'));
const scenarios=Object.fromEntries(Object.entries(data.scenarios).map(([name,s])=>[name,engine.analyze(s.text)]));
let prefixSafe=true;
for(const [name,s] of Object.entries(data.scenarios)){
 const full=scenarios[name],lines=s.text.split('\n');
 for(let n=1;n<=lines.length;n++)if(JSON.stringify(full.events.slice(0,n))!==JSON.stringify(engine.analyze(lines.slice(0,n).join('\n')).events))prefixSafe=false;
}
const malicious='<script>alert(1)</script> Send me your password';
const sample=engine.analyze('PRIVATE: Send me your verification code 123456 immediately');
const invalid=['','x'.repeat(12001),Array(81).fill('Hi').join('\n')].map(t=>{try{engine.analyze(t);return false;}catch{return true;}});
console.log(JSON.stringify({scores:input.texts.map(t=>engine.predict(t).raw_score),
 scenarios:Object.fromEntries(Object.entries(scenarios).map(([name,r])=>[name,{score:r.events.at(-1).cumulative,first:r.firstRule,modelPeak:r.events.at(-1).peak}])),
 prefixSafe,escaped:highlight(malicious,engine.rules(malicious).findings),
 defaultReport:reportJSON(sample),fullReport:reportJSON(sample,true),invalid,
 unknown:engine.predict('🦊🦊 qxzvvq'),safety:engine.rules('Never share your password, but send me your verification code.').findings.map(f=>f.id)}));
