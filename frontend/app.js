'use strict';
const $ = id => document.getElementById(id);
const table = $('task-list');
const dialog = $('task-dialog');
const form = $('task-form');
let tasks = [];
let editingId = null;
const categoryNames = {work:'Munka',personal:'Személyes',study:'Tanulás',other:'Egyéb'};
const priorityNames = {low:'Alacsony',medium:'Normál',high:'Magas'};

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {cache:'no-store', ...options});
  let payload;
  try {payload = await response.json();} catch {throw new Error('A szerver válasza nem feldolgozható.');}
  if (!response.ok) throw new Error(payload.error || 'Váratlan hiba történt.');
  return payload;
}
function message(text='') {$('message').textContent = text;}
function isOverdue(t) {const d=new Date();const today=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;return !t.completed && t.due_date && t.due_date < today;}
function formatDate(iso) {if (!iso) return '—'; const [y,m,d]=iso.split('-'); return `${y}. ${m}. ${d}.`;}
function setOnline(ok) {$('server-status').classList.toggle('offline', !ok); $('status-label').textContent = ok ? 'Minden rendszer működik' : 'Kapcsolati hiba';}
function node(tag, cls, content) {const el=document.createElement(tag); if(cls)el.className=cls; if(content!==undefined)el.textContent=content; return el;}
function stats() {
  $('stat-total').textContent=tasks.length;
  $('stat-active').textContent=tasks.filter(t=>!t.completed).length;
  $('stat-done').textContent=tasks.filter(t=>t.completed).length;
  $('stat-overdue').textContent=tasks.filter(isOverdue).length;
  $('count-pill').textContent=tasks.length;
  const bar=$('completion-bar'); if(bar) bar.style.width=(tasks.length?100*tasks.filter(t=>t.completed).length/tasks.length:0)+'%';
}
function visibleTasks() {
  const query=$('search').value.trim().toLocaleLowerCase('hu');
  const status=$('filter').value;
  const sort=$('sort').value;
  const filtered=tasks.filter(t=>{
    if(query && !`${t.title} ${t.description||''}`.toLocaleLowerCase('hu').includes(query))return false;
    if(status==='active' && t.completed)return false;
    if(status==='done' && !t.completed)return false;
    if(status==='overdue' && !isOverdue(t))return false;
    return true;
  });
  const priorityRank={high:0,medium:1,low:2};
  filtered.sort((a,b)=>sort==='due' ? ((a.due_date||'9999') .localeCompare(b.due_date||'9999') || b.id-a.id) : sort==='priority' ? (priorityRank[a.priority]-priorityRank[b.priority] || b.id-a.id) : b.id-a.id);
  return filtered;
}
function render() {
  stats(); table.replaceChildren();
  const rows=visibleTasks();
  $('empty-state').hidden=rows.length>0;
  $('result-count').textContent=`${rows.length} megjelenített feladat`;
  for(const task of rows) {
    const tr=node('tr',task.completed?'row-done':'');
    const main=node('td','task-cell'); const line=node('div','task-line');
    const check=node('input','task-checkbox'); check.type='checkbox'; check.checked=task.completed; check.setAttribute('aria-label',`${task.title} kész`);
    check.addEventListener('change',async()=>{check.disabled=true;try{await api(`/tasks/${task.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({completed:check.checked})});await load();}catch(e){message(e.message);check.checked=!check.checked;}finally{check.disabled=false;}});
    const text=node('div','task-text');text.append(node('strong','task-name',task.title));if(task.description)text.append(node('small','task-desc',task.description));
    line.append(check,text);main.append(line);tr.append(main);
    tr.append(node('td','',categoryNames[task.category]||'Egyéb'));
    const priority=node('td');priority.append(node('span',`priority priority-${task.priority}`,`● ${priorityNames[task.priority]||'Normál'}`));tr.append(priority);
    tr.append(node('td',isOverdue(task)?'late-date':'',formatDate(task.due_date)));
    const state=node('td');state.append(node('span',`state state-${task.completed?'done':'active'}`,task.completed?'✓ Elkészült':'◷ Folyamatban'));tr.append(state);
    const actions=node('td','actions');const edit=node('button','icon-action','Szerkesztés');edit.type='button';edit.addEventListener('click',()=>openDialog(task));
    const del=node('button','icon-action delete','Törlés');del.type='button';del.addEventListener('click',async()=>{if(!confirm(`Biztosan törlöd ezt a feladatot?\n${task.title}`))return;try{await api(`/tasks/${task.id}`,{method:'DELETE'});await load();}catch(e){message(e.message);}});
    actions.append(edit,del);tr.append(actions);table.append(tr);
  }
}
async function load() {try{const result=await api('/tasks');tasks=result.tasks;setOnline(true);message();render();}catch(e){setOnline(false);message(e.message);}}
function openDialog(task=null) {
  form.reset();editingId=task?.id??null;
  $('modal-title').textContent=task?'Feladat szerkesztése':'Új feladat';
  $('save-button').textContent=task?'Módosítás mentése':'Feladat mentése';
  if(task){$('new-task').value=task.title;$('description').value=task.description||'';$('category').value=task.category;$('priority').value=task.priority;$('due-date').value=task.due_date||'';}
  dialog.showModal();$('new-task').focus();
}
$('open-create').addEventListener('click',()=>openDialog());
$('empty-create').addEventListener('click',()=>openDialog());
$('close-dialog').addEventListener('click',()=>dialog.close());
$('cancel-dialog').addEventListener('click',()=>dialog.close());
$('search').addEventListener('input',render);
$('filter').addEventListener('change',render);
$('sort').addEventListener('change',render);
form.addEventListener('submit',async e=>{
  e.preventDefault();const title=$('new-task').value.trim();if(!title)return;
  const payload={title,description:$('description').value,category:$('category').value,priority:$('priority').value,due_date:$('due-date').value||null};
  $('save-button').disabled=true;
  try{await api(editingId===null?'/tasks':`/tasks/${editingId}`,{method:editingId===null?'POST':'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});dialog.close();await load();}
  catch(err){alert(err.message);}finally{$('save-button').disabled=false;}
});
load();
