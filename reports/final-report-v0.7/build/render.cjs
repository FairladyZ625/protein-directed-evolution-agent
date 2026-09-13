const {chromium}=require('playwright');
const path=require('path'); const fs=require('fs');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage();
 await page.goto('file://'+path.join(root,'scientific_report_v0.7_two_column.html'));
 await page.emulateMedia({media:'print'});await page.evaluate(()=>document.fonts.ready);
 const qa=await page.evaluate(()=>[...document.querySelectorAll('.page')].map(p=>{
  const content=p.querySelector('.content'),r=content.getBoundingClientRect();
  const elems=[...content.querySelectorAll('p,h1,h2,h3,table,figure,math')];
  const bad=elems.map(el=>{const b=el.getBoundingClientRect();return {tag:el.tagName,text:el.textContent.slice(0,70),left:b.left-r.left,right:b.right-r.right,bottom:b.bottom-r.bottom}}).filter(b=>b.left<-.5||b.right>.5||b.bottom>.5);
  const images=[...p.querySelectorAll('img')].map(i=>({ok:i.complete&&i.naturalWidth>0,w:i.naturalWidth,h:i.naturalHeight}));
  return {page:p.dataset.page,bad,images,height:content.scrollHeight,allowed:content.clientHeight};
 }));
 fs.writeFileSync(path.join(root,'evidence/layout-check.json'),JSON.stringify(qa,null,2));
 console.log(JSON.stringify(qa.map(x=>({page:x.page,bad:x.bad.length,height:x.height,allowed:x.allowed})),null,2));
 await page.pdf({path:path.join(root,'scientific_report_v0.7_two_column.pdf'),preferCSSPageSize:true,printBackground:true});
 await browser.close();
})();
