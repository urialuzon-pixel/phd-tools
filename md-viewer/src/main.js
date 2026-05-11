import { Editor, rootCtx, defaultValueCtx } from '@milkdown/core';
import { commonmark } from '@milkdown/preset-commonmark';
import { nord } from '@milkdown/theme-nord';
import { replaceAll } from '@milkdown/utils';
import '@milkdown/theme-nord/style.css';
import placeholder from './sample.md?raw';

const editorEl = document.querySelector('#editor');

const editor = await Editor.make()
  .config(ctx => {
    ctx.set(rootCtx, editorEl);
    ctx.set(defaultValueCtx, placeholder);
  })
  .use(nord)
  .use(commonmark)
  .create();

// File picker
function loadFile(file) {
  if (!file || !file.name.endsWith('.md')) return;
  const reader = new FileReader();
  reader.onload = () => editor.action(replaceAll(reader.result));
  reader.readAsText(file);
}

document.querySelector('#file-input').addEventListener('change', e => {
  loadFile(e.target.files[0]);
  e.target.value = '';
});

// Drag & Drop
document.addEventListener('dragover', e => { e.preventDefault(); document.body.classList.add('dragging'); });
document.addEventListener('dragleave', e => { if (!e.relatedTarget) document.body.classList.remove('dragging'); });

document.addEventListener('drop', e => {
  e.preventDefault();
  document.body.classList.remove('dragging');
  const file = e.dataTransfer?.files[0];
  if (!file || !file.name.endsWith('.md')) return;
  loadFile(file);
});
