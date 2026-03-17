#!/usr/bin/env node
// Test harness for n8n workflow JavaScript logic
// Run: node n8n/test-workflow-logic.js

let passed = 0;
let failed = 0;
const failures = [];

function assert(testName, condition, detail) {
  if (condition) {
    passed++;
  } else {
    failed++;
    failures.push({ testName, detail });
    console.log(`  FAIL: ${testName} — ${detail}`);
  }
}

// ============================================================
// Extract Parse Email logic
// ============================================================
function decodeHtml(str) {
  return str.replace(/&#39;/g,"'").replace(/&#x27;/g,"'").replace(/&apos;/g,"'")
    .replace(/&#34;/g,'"').replace(/&quot;/g,'"').replace(/&amp;/g,'&')
    .replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#x2F;/g,'/')
    .replace(/&#(\d+);/g,(m,c)=>String.fromCharCode(parseInt(c,10)));
}

const productMap = [
  {type:'arm_sleeves',label:'Arm Sleeves',patterns:[/\barm\s*sleeves?\b/,/\barm-sleeves?\b/,/\barmsleeves?\b/,/\barmband\b/,/\bgauntlet\b/,/\bcompression\s+arm\b/]},
  {type:'capris',label:'Capris',patterns:[/\bcapris?\b/,/\bopaque\s+capri\b/]},
  {type:'leggings',label:'Leggings',patterns:[/\bleggings?\b/,/\btights\b/,/\bpantyhose\b/,/\bbike\s+shorts?\b/,/\bcompression\s+shorts?\b/,/\bmen'?s?\s+briefs?\b/,/\blong\s+briefs?\b/,/\bshort\s+briefs?\b/,/\bactive\s+massage\s+legging\b/,/\bopaque\s+legging\b/,/\bhigh\s+waist\s+legging\b/,/\bmaternity\s+legging\b/]},
  {type:'socks',label:'Compression Socks',patterns:[/\bsocks?\b/,/\bknee[\s-]?highs?\b/,/\bkneehighs?\b/,/\bankle\s+socks?\b/,/\bmid[\s-]?calf\b/,/\bcalf\s+sleeves?\b/,/\bthigh\s+highs?\b/,/\bcompression\s+socks?\b/,/\bclosed\s+toe\s+knee\b/]},
  {type:'bras',label:'Bras',patterns:[/\bbras?\b/,/\bbraless\s+top\b/,/\btank\s+top\b/,/\bcompression\s+top\b/,/\bbodysuit\b/,/\bbuilt[\s-]?in\s+bra\b/,/\bsports\s+bra\b/,/\bcompression\s+bra\b/]}
];

const requiredMeasurements = {
  arm_sleeves:['bicep_circumference_cm','wrist_circumference_cm','arm_length_cm'],
  leggings:['height_cm','weight_kg','hip_circumference_cm','waist_circumference_cm'],
  capris:['height_cm','weight_kg','hip_circumference_cm','waist_circumference_cm'],
  socks:['calf_circumference_cm','ankle_circumference_cm'],
  bras:['bust_circumference_cm','underbust_circumference_cm']
};

function feetInchesToCm(f,i){return((f*12)+(i||0))*2.54;}
function inToCm(v){return v*2.54;}
function lbsToKg(v){return v/2.2046;}
const numberWords={zero:0,one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12};
function parseNum(s){const k=s.trim().toLowerCase();if(numberWords[k]!==undefined)return numberWords[k];const n=parseFloat(k);return isNaN(n)?null:n;}

function extractValue(text,patterns){
  for(const p of patterns){const m=text.match(p.regex);if(m){let v;
    if(p.type==='feet_inches'){const f=parseNum(m[1]);const i=m[2]?parseNum(m[2]):0;if(f===null)continue;v=feetInchesToCm(f,i||0);}
    else{v=parseNum(m[1]);if(v===null)continue;if(p.unit==='inches')v=inToCm(v);if(p.unit==='lbs')v=lbsToKg(v);}
    return Math.round(v*100)/100;}}return null;}

const heightPatterns=[
  {regex:/(\d+)\s*'\s*(\d+)?\s*"?/,type:'feet_inches'},
  {regex:/(\d+)\s*(?:feet|foot|ft)\.?\s*(\d+)?\s*(?:inches|inch|in)?/i,type:'feet_inches'},
  {regex:/(\w+)\s+foot\s+(\w+)/i,type:'feet_inches'},
  {regex:/height\s*(?:is|:|=)?\s*([\d.]+)\s*cm/i,unit:'cm'},
  {regex:/([\d.]+)\s*cm\s*(?:tall|height)/i,unit:'cm'},
  {regex:/i(?:'m|\s+am)\s+([\d.]+)\s*cm/i,unit:'cm'},
  {regex:/height\s*(?:is|:|=)?\s*([\d.]+)\s*(?:in|inches)/i,unit:'inches'},
  {regex:/height\s*(?:is|:|=)?\s*([\d.]+)/i,unit:'cm'}
];
const weightPatterns=[
  {regex:/(?:weight|weigh)\s+(?:about|around|approximately)?\s*([\d.]+)\s*(?:lbs?|pounds?)/i,unit:'lbs'},
  {regex:/(?:weight|weigh)[:\s]+([\d.]+)\s*(?:lbs?|pounds?)/i,unit:'lbs'},
  {regex:/([\d.]+)\s*(?:lbs?|pounds?)(?:\s|$|,|\.|and)/i,unit:'lbs'},
  {regex:/(?:weight|weigh)\s+(?:about|around|approximately)?\s*([\d.]+)\s*(?:kg|kilogram)/i,unit:'cm'},
  {regex:/(?:weight|weigh)[:\s]+([\d.]+)\s*(?:kg|kilogram)/i,unit:'cm'},
  {regex:/([\d.]+)\s*(?:kg|kilogram)s?(?:\s|$|,|\.|and)/i,unit:'cm'},
  {regex:/(?:weight|weigh)\s+(?:about|around|approximately)?\s*([\d.]+)/i,unit:'cm'}
];

function circumPat(name){
  const n=name.replace(/_/g,'[\\s-]?');
  return [
    {regex:new RegExp(n+'\\s+(?:is|are|of|about|around|approximately|measures?|measuring)?\\s*([\\d.]+)\\s*(?:in|inches|\\")', 'i'),unit:'inches'},
    {regex:new RegExp('([\\d.]+)\\s*(?:in|inches|inch)\\s*'+n,'i'),unit:'inches'},
    {regex:new RegExp(n+'[:\\s]+([\\d.]+)\\s*(?:in|inches|\\")', 'i'),unit:'inches'},
    {regex:new RegExp(n+'\\s+(?:is|are|of|about|around|approximately|measures?|measuring)?\\s*([\\d.]+)\\s*cm','i'),unit:'cm'},
    {regex:new RegExp('([\\d.]+)\\s*cm\\s*'+n,'i'),unit:'cm'},
    {regex:new RegExp(n+'[:\\s]+([\\d.]+)\\s*cm','i'),unit:'cm'},
    {regex:new RegExp('my\\s+'+n+'\\s+(?:is|are|measures?)\\s+(?:about|around|approximately)?\\s*([\\d.]+)\\s*(?:in|inches|\\")', 'i'),unit:'inches'},
    {regex:new RegExp('my\\s+'+n+'\\s+(?:is|are|measures?)\\s+(?:about|around|approximately)?\\s*([\\d.]+)\\s*cm','i'),unit:'cm'},
    {regex:new RegExp('my\\s+'+n+'\\s+(?:is|are|measures?)\\s+(?:about|around|approximately)?\\s*([\\d.]+)','i'),unit:'cm'},
    {regex:new RegExp(n+'\\s+(?:is|are|of|about|around|approximately|measures?|measuring)?\\s*([\\d.]+)','i'),unit:'cm'},
    {regex:new RegExp(n+'[:\\s]+([\\d.]+)','i'),unit:'cm'}
  ];
}

const bodyParts=[
  {key:'bust_circumference_cm',names:['bust']},
  {key:'underbust_circumference_cm',names:['underbust','under bust','under-bust']},
  {key:'waist_circumference_cm',names:['waist']},
  {key:'hip_circumference_cm',names:['hip','hips']},
  {key:'calf_circumference_cm',names:['calf']},
  {key:'ankle_circumference_cm',names:['ankle']},
  {key:'bicep_circumference_cm',names:['bicep','upper arm','upper-arm']},
  {key:'wrist_circumference_cm',names:['wrist']},
  {key:'arm_length_cm',names:['arm length','arm-length']}
];

function parseOne(item) {
  let body = (item.json.textPlain || item.json.snippet || '');
  const subject = (item.json.subject || '');
  body = decodeHtml(body);
  const bodyLower = body.toLowerCase();
  const combined = subject.toLowerCase() + ' ' + bodyLower;

  const detectedProducts = [];
  for (const prod of productMap) {
    for (const pat of prod.patterns) {
      if (pat.test(combined)) { detectedProducts.push({type:prod.type,label:prod.label}); break; }
    }
  }

  const measurements = {};
  const hv = extractValue(bodyLower, heightPatterns); if (hv) measurements.height_cm = hv;
  const wv = extractValue(bodyLower, weightPatterns); if (wv) measurements.weight_kg = wv;
  for (const part of bodyParts) {
    for (const name of part.names) {
      const v = extractValue(bodyLower, circumPat(name));
      if (v) { measurements[part.key] = v; break; }
    }
  }

  const products = []; let hasProcessable = false; let hasMissing = false;
  for (const prod of detectedProducts) {
    const req = requiredMeasurements[prod.type] || [];
    const pm = {}; const miss = [];
    for (const r of req) { if (measurements[r] !== undefined) pm[r] = measurements[r]; else miss.push(r); }
    const can = miss.length === 0;
    if (can) hasProcessable = true;
    if (miss.length > 0) hasMissing = true;
    products.push({productType:prod.type,productLabel:prod.label,measurements:pm,missingMeasurements:miss,canProcess:can});
  }

  // Extract sender email robustly
  const rawFrom = item.json.from || item.json.From || item.json.sender || item.json.senderAddress || '';
  let senderEmail = rawFrom;
  let senderName = '';
  const angleMatch = rawFrom.match(/<([^>]+@[^>]+)>/);
  if (angleMatch) { senderEmail = angleMatch[1].trim(); senderName = rawFrom.split('<')[0].replace(/[^a-zA-Z0-9 .'-]/g, '').trim(); }
  if (!senderName) senderName = item.json.fromName || item.json.senderName || '';
  if (!senderName && senderEmail.includes('@')) senderName = senderEmail.split('@')[0];
  if (!senderName) senderName = 'Customer';

  return {
    fromEmail: senderEmail,
    fromName: senderName,
    subject, messageId: item.json.messageId || item.json.id || '',
    threadId: item.json.threadId || '', originalBody: body,
    products, allMeasurements: measurements,
    hasProcessableProduct: hasProcessable,
    hasMissingMeasurements: hasMissing && !hasProcessable,
    hasNoProduct: detectedProducts.length === 0
  };
}

// ============================================================
// Smart Filter logic
// ============================================================
function smartFilter(item) {
  const subject = (item.json.subject || '').toLowerCase();
  const body = (item.json.textPlain || item.json.snippet || '').toLowerCase();
  const combined = subject + ' ' + body;

  const exclusions = [
    'order #', 'order number', 'order confirmation',
    'shipped', 'tracking', 'delivery',
    'unsubscribe', 'opt out', 'opt-out',
    'oversized', 'resize image', 'image size',
    'invoice', 'receipt', 'payment confirmation',
    'return label', 'refund processed',
    '888-841-8834 | solideaus.com',
    'solidea sizing assistant', 'your recommended size',
    'measurements we still need'
  ];
  if (exclusions.some(ex => combined.includes(ex))) return false;

  const sizingKeywords = [
    'what size', 'which size', 'sizing', 'size recommendation',
    'size guide', 'help with size', 'size chart',
    'recommend a size', 'recommend size', 'right size',
    'correct size', 'best size', 'size advice',
    'need help with fit', 'help me find my size',
    'not sure what size', 'unsure about size'
  ];
  const measurementKeywords = [
    'cm', 'centimeter', 'inches', 'inch',
    'height', 'weight', 'bust', 'waist', 'hip',
    'calf', 'ankle', 'wrist', 'bicep', 'underbust',
    'arm length', 'circumference',
    'feet', 'foot', 'lbs', 'pounds', 'kg', 'kilogram',
    'measure', 'measurement'
  ];
  const fitKeywords = ['fit', 'fitting', 'compression level', 'too tight', 'too loose'];

  const hasSizingIntent = sizingKeywords.some(kw => combined.includes(kw));
  const hasMeasurement = measurementKeywords.some(kw => combined.includes(kw));
  const hasFitInSubject = fitKeywords.some(kw => subject.includes(kw));

  return hasSizingIntent || hasMeasurement || hasFitInSubject;
}

// ============================================================
// Reply Chain Check logic
// ============================================================
function replyChainCheck(item, ownerEmail) {
  const labels = item.json.labels || item.json.labelIds || [];
  const labelNames = labels.map(l =>
    (typeof l === 'string' ? l : (l.name || l.id || '')).toUpperCase()
  );
  if (labelNames.includes('DRAFT')) return false;
  if (labelNames.length > 0 && !labelNames.includes('INBOX')) return false;

  const fromEmail = (item.json.from || item.json.From || '').toLowerCase();
  if (fromEmail.includes(ownerEmail)) return false;

  const snippet = (item.json.snippet || '').toLowerCase();
  const textPlain = (item.json.textPlain || '').toLowerCase();
  const checkText = snippet + ' ' + textPlain;

  const ourSignatures = [
    'solidea sizing email assistant',
    'your recommended size is',
    'measurements we still need',
    '888-841-8834 | solideaus.com'
  ];
  if (ourSignatures.some(sig => checkText.includes(sig))) return false;

  return true;
}

// ============================================================
// Format measurements helper (from Log Config nodes)
// ============================================================
const fmtM=(m)=>{if(!m||Object.keys(m).length===0)return 'None';const N={height_cm:'Height',weight_kg:'Weight',bust_circumference_cm:'Bust',underbust_circumference_cm:'Underbust',waist_circumference_cm:'Waist',hip_circumference_cm:'Hip',calf_circumference_cm:'Calf',ankle_circumference_cm:'Ankle',bicep_circumference_cm:'Bicep',wrist_circumference_cm:'Wrist',arm_length_cm:'Arm length'};return Object.entries(m).map(([k,v])=>(N[k]||k)+': '+v+(k==='weight_kg'?' kg':' cm')).join(', ');};

// ============================================================
// Format Reply logic (multi-product grouping)
// ============================================================
function formatReply(items) {
  const groups = {};
  for (const item of items) {
    const key = item.messageId || item.fromEmail || 'unknown';
    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
  }

  const results = [];
  for (const key of Object.keys(groups)) {
    const emailItems = groups[key];
    const first = emailItems[0];
    const name = first.fromName || 'there';
    const multi = emailItems.length > 1;
    const allProducts = [];

    for (const d of emailItems) {
      allProducts.push({
        productType: d.currentProduct.productType,
        productLabel: d.currentProduct.productLabel,
        recommendedSize: d.recommended_size,
        confidence: d.confidence || 'exact',
        notes: d.notes || ''
      });
    }

    results.push({
      toEmail: first.fromEmail,
      subject: 'Re: ' + first.subject,
      recommendedSize: allProducts.map(p => p.productLabel + ': ' + p.recommendedSize).join(', '),
      productType: allProducts.map(p => p.productType).join(', '),
      productLabel: allProducts.map(p => p.productLabel).join(', '),
      products: allProducts,
      threadId: first.threadId,
      messageId: first.messageId,
      fromName: first.fromName,
      fromEmail: first.fromEmail,
      isMulti: multi
    });
  }
  return results;
}


// ============================================================
// TESTS
// ============================================================
console.log('\n=== SENDER EMAIL EXTRACTION ===\n');

// Test 1: "Name <email>" format
let r = parseOne({ json: { from: 'Jane Doe <jane@example.com>', subject: 'sizing help', textPlain: 'I need leggings, 5\'6", 140 lbs, waist 28 inches, hip 38 inches' } });
assert('Name <email> format - email extracted', r.fromEmail === 'jane@example.com', `got "${r.fromEmail}"`);
assert('Name <email> format - name extracted', r.fromName === 'Jane Doe', `got "${r.fromName}"`);

// Test 2: Plain email address
r = parseOne({ json: { from: 'customer@gmail.com', subject: 'bra sizing', textPlain: 'bust 38 inches underbust 32 inches' } });
assert('Plain email - email preserved', r.fromEmail === 'customer@gmail.com', `got "${r.fromEmail}"`);
assert('Plain email - name from local part', r.fromName === 'customer', `got "${r.fromName}"`);

// Test 3: Quoted name format
r = parseOne({ json: { from: '"Mary Smith" <mary@test.com>', subject: 'sizing', textPlain: 'socks, calf 15 inches, ankle 9 inches' } });
assert('Quoted name - email extracted', r.fromEmail === 'mary@test.com', `got "${r.fromEmail}"`);
assert('Quoted name - name extracted (quotes stripped)', r.fromName === 'Mary Smith', `got "${r.fromName}"`);

// Test 4: Empty from field, fallback to fromName
r = parseOne({ json: { from: '', fromName: 'Bob Jones', subject: 'sizing', textPlain: 'leggings' } });
assert('Empty from + fromName fallback', r.fromName === 'Bob Jones', `got "${r.fromName}"`);

// Test 5: Completely empty sender
r = parseOne({ json: { subject: 'sizing', textPlain: 'leggings' } });
assert('No sender info - defaults to Customer', r.fromName === 'Customer', `got "${r.fromName}"`);
assert('No sender info - email is empty string', r.fromEmail === '', `got "${r.fromEmail}"`);

// Test 6: From field via From (capital F)
r = parseOne({ json: { From: 'Alt <alt@example.com>', subject: 'sizing', textPlain: 'socks' } });
assert('Capital-F From field - email extracted', r.fromEmail === 'alt@example.com', `got "${r.fromEmail}"`);


console.log('\n=== PRODUCT DETECTION ===\n');

// Test: each product type detected
const productTests = [
  { text: 'I need arm sleeves', expect: 'arm_sleeves' },
  { text: 'looking at compression arm sleeve', expect: 'arm_sleeves' },
  { text: 'interested in capris', expect: 'capris' },
  { text: 'opaque capri size?', expect: 'capris' },
  { text: 'what size leggings', expect: 'leggings' },
  { text: 'compression shorts sizing', expect: 'leggings' },
  { text: 'tights size help', expect: 'leggings' },
  { text: 'active massage legging', expect: 'leggings' },
  { text: 'maternity legging size', expect: 'leggings' },
  { text: 'need compression socks', expect: 'socks' },
  { text: 'knee high sizing', expect: 'socks' },
  { text: 'thigh highs size', expect: 'socks' },
  { text: 'closed toe knee size', expect: 'socks' },
  { text: 'what size bra', expect: 'bras' },
  { text: 'sports bra sizing', expect: 'bras' },
  { text: 'compression top size', expect: 'bras' },
  { text: 'bodysuit sizing', expect: 'bras' },
];

for (const t of productTests) {
  r = parseOne({ json: { from: 'a@b.com', subject: t.text, textPlain: '' } });
  const found = r.products.map(p => p.productType);
  assert(`Product: "${t.text}"`, found.includes(t.expect), `expected ${t.expect}, got [${found}]`);
}

// Test: no product detected
r = parseOne({ json: { from: 'a@b.com', subject: 'general question', textPlain: 'I have a question about your company' } });
assert('No product - hasNoProduct=true', r.hasNoProduct === true, `got ${r.hasNoProduct}`);

// Test: multiple products in one email
r = parseOne({ json: { from: 'a@b.com', subject: 'sizing help', textPlain: 'I need leggings and also socks. height 5\'6", 140 lbs, waist 28 inches, hip 38 inches, calf 15 inches, ankle 9 inches' } });
const types = r.products.map(p => p.productType);
assert('Multi-product: leggings detected', types.includes('leggings'), `got [${types}]`);
assert('Multi-product: socks detected', types.includes('socks'), `got [${types}]`);
assert('Multi-product: both processable', r.products.every(p => p.canProcess), `processable: ${r.products.map(p=>p.canProcess)}`);


console.log('\n=== MEASUREMENT EXTRACTION ===\n');

// Height formats
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: "I'm 5'6\" and weigh 140 lbs" } });
assert('Height 5\'6" -> ~167.64 cm', Math.abs(r.allMeasurements.height_cm - 167.64) < 0.1, `got ${r.allMeasurements.height_cm}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'height is 170 cm' } });
assert('Height 170 cm', r.allMeasurements.height_cm === 170, `got ${r.allMeasurements.height_cm}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: '5 foot 10' } });
assert('Height "5 foot 10" -> ~177.8 cm', Math.abs(r.allMeasurements.height_cm - 177.8) < 0.1, `got ${r.allMeasurements.height_cm}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'I am 165cm tall' } });
assert('Height "165cm tall"', r.allMeasurements.height_cm === 165, `got ${r.allMeasurements.height_cm}`);

// Weight formats
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'I weigh 150 lbs' } });
assert('Weight 150 lbs -> ~68.04 kg', Math.abs(r.allMeasurements.weight_kg - 68.04) < 0.1, `got ${r.allMeasurements.weight_kg}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'weight: 65 kg' } });
assert('Weight 65 kg', r.allMeasurements.weight_kg === 65, `got ${r.allMeasurements.weight_kg}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'I weigh about 130 pounds' } });
assert('Weight "about 130 pounds"', r.allMeasurements.weight_kg !== undefined, `got ${r.allMeasurements.weight_kg}`);

// Circumference measurements
r = parseOne({ json: { from: 'a@b.com', subject: 'socks', textPlain: 'calf 15 inches ankle 9 inches' } });
assert('Calf 15 in -> ~38.1 cm', Math.abs(r.allMeasurements.calf_circumference_cm - 38.1) < 0.1, `got ${r.allMeasurements.calf_circumference_cm}`);
assert('Ankle 9 in -> ~22.86 cm', Math.abs(r.allMeasurements.ankle_circumference_cm - 22.86) < 0.1, `got ${r.allMeasurements.ankle_circumference_cm}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'bras', textPlain: 'my bust is 95 cm and underbust is 77 cm' } });
assert('Bust 95 cm', r.allMeasurements.bust_circumference_cm === 95, `got ${r.allMeasurements.bust_circumference_cm}`);
assert('Underbust 77 cm', r.allMeasurements.underbust_circumference_cm === 77, `got ${r.allMeasurements.underbust_circumference_cm}`);

r = parseOne({ json: { from: 'a@b.com', subject: 'arm sleeves', textPlain: 'bicep 12 inches, wrist 6.5 inches, arm length 24 inches' } });
assert('Bicep 12 in -> ~30.48 cm', Math.abs(r.allMeasurements.bicep_circumference_cm - 30.48) < 0.1, `got ${r.allMeasurements.bicep_circumference_cm}`);
assert('Wrist 6.5 in -> ~16.51 cm', Math.abs(r.allMeasurements.wrist_circumference_cm - 16.51) < 0.1, `got ${r.allMeasurements.wrist_circumference_cm}`);
assert('Arm length 24 in -> ~60.96 cm', Math.abs(r.allMeasurements.arm_length_cm - 60.96) < 0.1, `got ${r.allMeasurements.arm_length_cm}`);

// Waist + hip
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'waist 28 inches, hip 38 inches' } });
assert('Waist 28 in -> ~71.12 cm', Math.abs(r.allMeasurements.waist_circumference_cm - 71.12) < 0.1, `got ${r.allMeasurements.waist_circumference_cm}`);
assert('Hip 38 in -> ~96.52 cm', Math.abs(r.allMeasurements.hip_circumference_cm - 96.52) < 0.1, `got ${r.allMeasurements.hip_circumference_cm}`);

// Missing measurements
r = parseOne({ json: { from: 'a@b.com', subject: 'socks', textPlain: 'calf 15 inches' } });
assert('Socks missing ankle', r.products[0].missingMeasurements.includes('ankle_circumference_cm'), `missing: ${r.products[0].missingMeasurements}`);
assert('Socks not processable', r.products[0].canProcess === false, `canProcess: ${r.products[0].canProcess}`);


console.log('\n=== PROCESSABLE / MISSING / NO-PRODUCT FLAGS ===\n');

// Full leggings measurements
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: "5'6\", 140 lbs, waist 28 inches, hip 38 inches" } });
assert('Full leggings - hasProcessableProduct', r.hasProcessableProduct === true, `got ${r.hasProcessableProduct}`);
assert('Full leggings - not hasMissingMeasurements', r.hasMissingMeasurements === false, `got ${r.hasMissingMeasurements}`);

// Partial leggings measurements (missing waist)
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: "5'6\", 140 lbs, hip 38 inches" } });
assert('Partial leggings - not processable', r.hasProcessableProduct === false, `got ${r.hasProcessableProduct}`);
assert('Partial leggings - hasMissingMeasurements', r.hasMissingMeasurements === true, `got ${r.hasMissingMeasurements}`);

// Multi-product: one processable, one not
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings and bra', textPlain: "5'6\", 140 lbs, waist 28 inches, hip 38 inches" } });
assert('Multi: leggings processable', r.products.find(p=>p.productType==='leggings').canProcess === true, 'leggings not processable');
assert('Multi: bras not processable', r.products.find(p=>p.productType==='bras').canProcess === false, 'bras unexpectedly processable');
assert('Multi: hasProcessableProduct true (at least one)', r.hasProcessableProduct === true, `got ${r.hasProcessableProduct}`);


console.log('\n=== SMART FILTER ===\n');

// Should pass
assert('SF: sizing intent passes', smartFilter({ json: { subject: 'what size leggings', textPlain: '' } }), 'rejected');
assert('SF: measurement keyword passes', smartFilter({ json: { subject: 'help', textPlain: 'my waist is 28 inches' } }), 'rejected');
assert('SF: fit in subject passes', smartFilter({ json: { subject: 'compression level help', textPlain: '' } }), 'rejected');
assert('SF: "cm" keyword passes', smartFilter({ json: { subject: 'sizing', textPlain: 'bust is 95 cm' } }), 'rejected');

// Should be excluded
assert('SF: order confirmation excluded', !smartFilter({ json: { subject: 'order confirmation', textPlain: 'Your order #12345 has been placed' } }), 'passed when should be excluded');
assert('SF: shipping excluded', !smartFilter({ json: { subject: 'Your item has shipped', textPlain: 'tracking number...' } }), 'passed');
assert('SF: unsubscribe excluded', !smartFilter({ json: { subject: 'sizing help', textPlain: 'click here to unsubscribe' } }), 'passed');
assert('SF: our own signature excluded', !smartFilter({ json: { subject: 'Re: sizing', textPlain: 'your recommended size is M' } }), 'passed');
assert('SF: invoice excluded', !smartFilter({ json: { subject: 'Invoice for order', textPlain: 'receipt attached' } }), 'passed');

// Should NOT pass (no sizing intent, no measurements, no fit keyword)
assert('SF: generic question rejected', !smartFilter({ json: { subject: 'Question about returns', textPlain: 'How do I return an item?' } }), 'passed');


console.log('\n=== REPLY CHAIN CHECK ===\n');

const ownerEmail = 'orders@solideaus.com';

// Should pass (legitimate customer email)
assert('RCC: customer email passes', replyChainCheck({ json: { from: 'customer@gmail.com', labels: ['INBOX'], snippet: 'what size socks' } }, ownerEmail), 'rejected');

// Should be filtered out
assert('RCC: draft filtered', !replyChainCheck({ json: { from: 'customer@gmail.com', labels: ['DRAFT'], snippet: '' } }, ownerEmail), 'passed');
assert('RCC: sent-only filtered', !replyChainCheck({ json: { from: 'x@y.com', labels: ['SENT'], snippet: '' } }, ownerEmail), 'passed');
assert('RCC: self-send filtered', !replyChainCheck({ json: { from: 'orders@solideaus.com', labels: ['INBOX'], snippet: '' } }, ownerEmail), 'passed');
assert('RCC: reply to our email filtered', !replyChainCheck({ json: { from: 'customer@gmail.com', labels: ['INBOX'], snippet: '', textPlain: 'Thanks! Your recommended size is M in our Leggings.' } }, ownerEmail), 'passed');
assert('RCC: our signature in snippet filtered', !replyChainCheck({ json: { from: 'customer@gmail.com', labels: ['INBOX'], snippet: '888-841-8834 | solideaus.com' } }, ownerEmail), 'passed');

// Edge: empty labels should pass (some Gmail setups)
assert('RCC: empty labels passes', replyChainCheck({ json: { from: 'customer@gmail.com', labels: [], snippet: 'what size' } }, ownerEmail), 'rejected');


console.log('\n=== MEASUREMENT FORMATTING (fmtM) ===\n');

assert('fmtM: empty obj -> None', fmtM({}) === 'None', `got "${fmtM({})}"`);
assert('fmtM: null -> None', fmtM(null) === 'None', `got "${fmtM(null)}"`);
assert('fmtM: bra measurements', fmtM({bust_circumference_cm:95,underbust_circumference_cm:77}) === 'Bust: 95 cm, Underbust: 77 cm', `got "${fmtM({bust_circumference_cm:95,underbust_circumference_cm:77})}"`);
assert('fmtM: weight shows kg', fmtM({height_cm:170,weight_kg:65}).includes('Weight: 65 kg'), `got "${fmtM({height_cm:170,weight_kg:65})}"`);
assert('fmtM: height shows cm', fmtM({height_cm:170,weight_kg:65}).includes('Height: 170 cm'), `got "${fmtM({height_cm:170,weight_kg:65})}"`);


console.log('\n=== FORMAT REPLY (MULTI-PRODUCT GROUPING) ===\n');

// Single product
let replyItems = [{
  messageId: 'msg1', fromEmail: 'jane@test.com', fromName: 'Jane', subject: 'Sizing',
  threadId: 't1', currentProduct: { productType: 'bras', productLabel: 'Bras' },
  recommended_size: 'M', confidence: 'exact', notes: ''
}];
let replies = formatReply(replyItems);
assert('Single product reply: 1 result', replies.length === 1, `got ${replies.length}`);
assert('Single product reply: correct size', replies[0].recommendedSize === 'Bras: M', `got "${replies[0].recommendedSize}"`);
assert('Single product reply: not multi', replies[0].isMulti === false, `got ${replies[0].isMulti}`);

// Multi-product same email
replyItems = [
  { messageId: 'msg2', fromEmail: 'bob@test.com', fromName: 'Bob', subject: 'Sizing',
    threadId: 't2', currentProduct: { productType: 'leggings', productLabel: 'Leggings' },
    recommended_size: 'ML', confidence: 'interpolated', notes: '' },
  { messageId: 'msg2', fromEmail: 'bob@test.com', fromName: 'Bob', subject: 'Sizing',
    threadId: 't2', currentProduct: { productType: 'socks', productLabel: 'Compression Socks' },
    recommended_size: 'M', confidence: 'exact', notes: '' }
];
replies = formatReply(replyItems);
assert('Multi-product reply: 1 grouped result', replies.length === 1, `got ${replies.length}`);
assert('Multi-product reply: isMulti true', replies[0].isMulti === true, `got ${replies[0].isMulti}`);
assert('Multi-product reply: combined sizes', replies[0].recommendedSize === 'Leggings: ML, Compression Socks: M', `got "${replies[0].recommendedSize}"`);
assert('Multi-product reply: combined types', replies[0].productType === 'leggings, socks', `got "${replies[0].productType}"`);

// Two different emails in same batch (different messageIds)
replyItems = [
  { messageId: 'msg3', fromEmail: 'a@test.com', fromName: 'A', subject: 'S1',
    threadId: 't3', currentProduct: { productType: 'bras', productLabel: 'Bras' },
    recommended_size: 'S', confidence: 'exact', notes: '' },
  { messageId: 'msg4', fromEmail: 'b@test.com', fromName: 'B', subject: 'S2',
    threadId: 't4', currentProduct: { productType: 'socks', productLabel: 'Compression Socks' },
    recommended_size: 'L', confidence: 'exact', notes: '' }
];
replies = formatReply(replyItems);
assert('Two emails: 2 separate results', replies.length === 2, `got ${replies.length}`);


console.log('\n=== EDGE CASES ===\n');

// HTML entities in body
r = parseOne({ json: { from: 'a@b.com', subject: 'bras', textPlain: 'bust is 37&#34; and underbust 32&#34;' } });
assert('HTML entity &#34; decoded to "', r.allMeasurements.bust_circumference_cm !== undefined, `bust: ${r.allMeasurements.bust_circumference_cm}`);

// Number words
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: 'five foot six, weight 140 lbs, waist 28 inches, hip 38 inches' } });
assert('Number words "five foot six"', Math.abs(r.allMeasurements.height_cm - 167.64) < 0.1, `got ${r.allMeasurements.height_cm}`);

// "I'm X cm" format
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: "I'm 165 cm and weigh 55 kg, waist 70 cm, hip 95 cm" } });
assert('"I\'m 165 cm" format', r.allMeasurements.height_cm === 165, `got ${r.allMeasurements.height_cm}`);
assert('Full metric leggings processable', r.hasProcessableProduct === true, `got ${r.hasProcessableProduct}`);

// Very informal email
r = parseOne({ json: { from: 'Jane <jane@gmail.com>', subject: 'hi!', textPlain: "hey i need help with sizing for your leggings. i'm 5'4, about 130 pounds, my hips are 36 inches and waist is 27 in. thanks!" } });
assert('Informal email: leggings detected', r.products[0]?.productType === 'leggings', `got ${r.products[0]?.productType}`);
assert('Informal email: processable', r.hasProcessableProduct === true, `got ${r.hasProcessableProduct}`);
assert('Informal email: email extracted', r.fromEmail === 'jane@gmail.com', `got "${r.fromEmail}"`);

// Email with "size" in signature but actual sizing question
r = parseOne({ json: { from: 'a@b.com', subject: 'Knee high sizing', textPlain: 'my calf measures 14 inches and ankle 8.5 inches' } });
assert('Knee high -> socks detected', r.products[0]?.productType === 'socks', `got ${r.products[0]?.productType}`);
assert('Knee high processable', r.hasProcessableProduct === true, `got ${r.hasProcessableProduct}`);

// Zero measurements but product mentioned
r = parseOne({ json: { from: 'a@b.com', subject: 'what size leggings should I get?', textPlain: 'I am interested in your leggings but not sure what size.' } });
assert('Product + no measurements: hasMissingMeasurements', r.hasMissingMeasurements === true, `got ${r.hasMissingMeasurements}`);
assert('Product + no measurements: not processable', r.hasProcessableProduct === false, `got ${r.hasProcessableProduct}`);

// Measurements but no product
r = parseOne({ json: { from: 'a@b.com', subject: 'help please', textPlain: "I'm 5'6\", 140 lbs, waist 28, hip 38" } });
assert('Measurements + no product: hasNoProduct', r.hasNoProduct === true, `got ${r.hasNoProduct}`);

// "hips" plural
r = parseOne({ json: { from: 'a@b.com', subject: 'leggings', textPlain: "my hips are 38 inches" } });
assert('"hips" plural matches hip', r.allMeasurements.hip_circumference_cm !== undefined, `got ${r.allMeasurements.hip_circumference_cm}`);

// Under-bust hyphenated
r = parseOne({ json: { from: 'a@b.com', subject: 'bras', textPlain: 'bust 36 inches, under-bust 30 inches' } });
assert('under-bust hyphenated matches', r.allMeasurements.underbust_circumference_cm !== undefined, `got ${r.allMeasurements.underbust_circumference_cm}`);

// Upper arm = bicep
r = parseOne({ json: { from: 'a@b.com', subject: 'arm sleeves', textPlain: 'upper arm 12 inches, wrist 6.5 inches, arm length 24 inches' } });
assert('"upper arm" matches bicep', r.allMeasurements.bicep_circumference_cm !== undefined, `got ${r.allMeasurements.bicep_circumference_cm}`);


// ============================================================
// SUMMARY
// ============================================================
console.log('\n' + '='.repeat(50));
console.log(`RESULTS: ${passed} passed, ${failed} failed out of ${passed + failed} tests`);
if (failures.length > 0) {
  console.log('\nFAILURES:');
  for (const f of failures) {
    console.log(`  - ${f.testName}: ${f.detail}`);
  }
}
console.log('='.repeat(50) + '\n');

process.exit(failed > 0 ? 1 : 0);
