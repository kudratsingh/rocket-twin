import assert from 'node:assert/strict';
import test from 'node:test';
test('manual viewport panel distinguishes actual CSS size from target without claiming zoom or resizing',async()=>{
 const {createServer}=await import('vite');const {default:React}=await import('react');const {renderToStaticMarkup}=await import('react-dom/server');
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{const {ViewportVerificationPanel}=await server.ssrLoadModule('/src/workspaces/ViewportVerification.tsx');
 const render=(width,height)=>renderToStaticMarkup(React.createElement(ViewportVerificationPanel,{observation:{width,height,dpr:2},target:0,onTarget:()=>{},onClose:()=>{}}));
 assert.match(render(1440,900),/Requested size matches/);assert.match(render(1965,1074),/not reached/);
 for(const text of ['CSS px','Keep browser zoom at100%','does not resize anything','not screenshot pixels','Hide measurement panel'])assert.ok(render(1440,900).includes(text),text);
 }finally{await server.close();}
});
