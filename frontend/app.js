// If frontend is served on a different port (e.g. http.server on 5500),
// point API calls to the backend at port 8000. If frontend and backend
// run on the same origin (port 8000), leave apiBase empty.
const apiBase = (location.port && location.port !== '8000') ? 'http://127.0.0.1:8000' : '';

async function _handleResponse(res) {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText} - ${text}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return null;
}

async function fetchTasks(){
  const res = await fetch(`${apiBase}/tasks`);
  return _handleResponse(res);
}

// fetch with query params
async function fetchTasksWithParams(params = {}){
  const qs = new URLSearchParams();
  if (typeof params.completed !== 'undefined' && params.completed !== null) qs.set('completed', String(params.completed));
  if (params.q) qs.set('q', params.q);
  const url = `${apiBase}/tasks` + (qs.toString() ? `?${qs.toString()}` : '');
  const res = await fetch(url);
  return _handleResponse(res);
}

async function createTask(title, description){
  const res = await fetch(`${apiBase}/tasks`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({title, description})
  });
  return _handleResponse(res);
}

async function updateTask(id, patch){
  const res = await fetch(`${apiBase}/tasks/${id}`, {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(patch)
  });
  return _handleResponse(res);
}

function el(tag, props={}, ...children){
  const e = document.createElement(tag);
  Object.entries(props).forEach(([k,v])=>{ if(k==='class') e.className=v; else if(k in e) e[k]=v; else e.setAttribute(k,v)});
  children.flat().forEach(c=>{ if(typeof c==='string') e.appendChild(document.createTextNode(c)); else if(c) e.appendChild(c) });
  return e;
}

async function render(){
  const list = document.getElementById('tasks');
  list.innerHTML='';
  try{
    const q = document.getElementById('filterQ')?.value.trim() || '';
    const compSel = document.getElementById('filterCompleted')?.value || 'all';
    let completed = null;
    if (compSel === 'active') completed = false;
    if (compSel === 'completed') completed = true;
    const tasks = await fetchTasksWithParams({completed, q});
    tasks.forEach(t=>{
      const badge = el('span',{class: 'badge ' + (t.completed ? 'done' : 'active')}, t.completed ? 'Ukończone' : 'Aktywne');
      const dates = el('div',{class:'dates'},
        t.created_at ? el('div',{class:'date created'}, 'Utworzono: ' + new Date(t.created_at).toLocaleString()) : null,
        t.completed_at ? el('div',{class:'date completed_at'}, 'Zakończono: ' + new Date(t.completed_at).toLocaleString()) : null
      );

      const item = el('li',{class:'task'+(t.completed? ' completed':'' )},
        el('input',{type:'checkbox',checked:!!t.completed}),
        el('div',{class:'content'},
          el('div',{class:'title'}, t.title, ' ', badge),
          t.description? el('div',{class:'desc'}, t.description) : null,
          dates
        ),
        el('div',{class:'controls'},
          el('button',{class:'btn edit'}, 'Edytuj'),
          el('button',{class:'btn toggle'}, t.completed? 'Oznacz jako nieukończone' : 'Oznacz jako ukończone')
        )
      );

      const checkbox = item.querySelector('input[type=checkbox]');
      checkbox.addEventListener('change', async ()=>{
        await updateTask(t.id, {completed: checkbox.checked});
        render();
      });

      item.querySelector('.edit').addEventListener('click', async ()=>{
        const newTitle = prompt('Nowy tytuł', t.title);
        if(newTitle===null) return;
        const newDesc = prompt('Nowy opis', t.description||'')
        await updateTask(t.id, {title:newTitle, description:newDesc});
        render();
      });

      item.querySelector('.toggle').addEventListener('click', async ()=>{
        await updateTask(t.id, {completed: !t.completed});
        render();
      });

      list.appendChild(item);
    })
  }catch(err){
    list.appendChild(el('li',{}, 'Błąd: ' + err.message));
  }
}

document.addEventListener('DOMContentLoaded', ()=>{
  const addBtn = document.getElementById('addBtn');
  addBtn.addEventListener('click', async ()=>{
    const title = document.getElementById('title').value.trim();
    const desc = document.getElementById('description').value.trim();
    if(!title) { alert('Wpisz tytuł'); return }
    await createTask(title, desc||null);
    document.getElementById('title').value='';
    document.getElementById('description').value='';
    render();
  });

  // filters
  const fq = document.getElementById('filterQ');
  const fc = document.getElementById('filterCompleted');
  if(fq) fq.addEventListener('input', ()=>{ render(); });
  if(fc) fc.addEventListener('change', ()=>{ render(); });

  render();
});
