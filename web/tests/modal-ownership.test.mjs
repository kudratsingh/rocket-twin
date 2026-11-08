import test from 'node:test';
import assert from 'node:assert/strict';
import { ownedByOpenDialog } from '../src/workspaces/modalOwnership.ts';
test('dialog descendants including SVG focus defer capture/sidebar/Focus shortcuts to native dialog',()=>{
 const seen=[];
 for(const tag of ['BUTTON','SELECT','g']) assert.equal(ownedByOpenDialog({tagName:tag,closest(selector){seen.push(selector);return {tagName:'DIALOG',open:true};}}),true);
 assert.deepEqual(seen,['dialog[open]','dialog[open]','dialog[open]']);
});
test('normal sidebar controls retain Escape ownership, and non-element targets are harmless',()=>{
 assert.equal(ownedByOpenDialog({closest(){return null;}}),false);
 for(const target of [null,undefined,{},'dialog',42]) assert.equal(ownedByOpenDialog(target),false);
});
