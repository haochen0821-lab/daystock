// ── 狀態 ──────────────────────────────────────────────
const composer = [];
let activeCatId = null;
let activeCatName = '全部';
let searchTimer = null;
let allTags = [];
let currentTagsAdd = [];   // 新增提示詞用
let currentTagsEdit = [];  // 編輯 tag 用
let importFiles = [];

// ── 主題 ──────────────────────────────────────────────
function initTheme() { applyTheme(localStorage.getItem('pm-theme') || 'light'); }
function applyTheme(theme) {
    document.body.classList.remove('theme-light','theme-dark');
    document.body.classList.add('theme-'+theme);
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = theme==='dark' ? '☀️' : '🌙';
    localStorage.setItem('pm-theme', theme);
}
function toggleTheme() {
    applyTheme(localStorage.getItem('pm-theme')==='dark' ? 'light' : 'dark');
}

// ── 工具 ──────────────────────────────────────────────
function openModal(id) { document.getElementById(id).style.display='flex'; }
function closeModal(id) { document.getElementById(id).style.display='none'; }

async function api(url, method='GET', body=null) {
    const opts = { method, headers:{'Content-Type':'application/json'} };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return res.json();
}

function toast(msg, type='success') {
    const el = document.createElement('div');
    el.textContent = msg;
    el.style.cssText = `position:fixed;bottom:24px;right:24px;z-index:9999;
        background:var(--bg2);border:1px solid ${type==='success'?'var(--success)':'var(--danger)'};
        color:${type==='success'?'var(--success)':'var(--danger)'};
        padding:10px 20px;border-radius:8px;font-size:13px;box-shadow:var(--shadow);`;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2500);
}

function escHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Tag 系統 ──────────────────────────────────────────
async function loadAllTags() {
    allTags = await api('/api/tags');
}

function makeTagSystem(suffix) {
    const arr = suffix === 'add' ? currentTagsAdd : currentTagsEdit;
    const chipsEl = document.getElementById(`tag-chips-${suffix}`);
    const inputEl = document.getElementById(`tag-input-${suffix}`);
    const suggEl  = document.getElementById(`tag-suggestions-${suffix}`);
    if (!chipsEl || !inputEl || !suggEl) return;

    function renderChips() {
        chipsEl.innerHTML = arr.map((t,i) => `
            <span class="tag-chip">${escHtml(t)}
                <button class="tag-chip-remove" onclick="removeTagFrom('${suffix}',${i})">×</button>
            </span>`).join('');
    }

    function showSuggestions(val) {
        const filtered = allTags.filter(t =>
            (!val.trim() || t.toLowerCase().includes(val.toLowerCase())) && !arr.includes(t)
        );
        if (!filtered.length) { suggEl.style.display='none'; return; }
        suggEl.style.display='block';
        suggEl.innerHTML = filtered.map(t =>
            `<div class="tag-suggestion-item" onmousedown="addTagTo('${suffix}','${escHtml(t).replace(/'/g,"\\'")}');makeTagSystem('${suffix}')">${escHtml(t)}</div>`
        ).join('');
    }

    // 移除舊的事件再綁定，避免重複
    const newInput = inputEl.cloneNode(true);
    inputEl.parentNode.replaceChild(newInput, inputEl);

    newInput.oninput = e => showSuggestions(e.target.value);
    newInput.onfocus = e => showSuggestions(e.target.value);
    newInput.onkeydown = e => {
        if (e.key==='Enter') { e.preventDefault(); addTagTo(suffix, e.target.value); makeTagSystem(suffix); }
        else if (e.key==='Backspace' && !e.target.value && arr.length) {
            arr.pop(); renderChips();
        }
    };
    newInput.onblur = () => setTimeout(() => { suggEl.style.display='none'; }, 200);
    renderChips();
}

function addTagTo(suffix, tag) {
    tag = tag.trim();
    const arr = suffix==='add' ? currentTagsAdd : currentTagsEdit;
    if (!tag || arr.includes(tag)) return;
    arr.push(tag);
    const chipsEl = document.getElementById(`tag-chips-${suffix}`);
    const inputEl = document.getElementById(`tag-input-${suffix}`);
    const suggEl  = document.getElementById(`tag-suggestions-${suffix}`);
    chipsEl.innerHTML = arr.map((t,i) => `
        <span class="tag-chip">${escHtml(t)}
            <button class="tag-chip-remove" onclick="removeTagFrom('${suffix}',${i})">×</button>
        </span>`).join('');
    inputEl.value = '';
    if (suggEl) suggEl.style.display='none';
}

function removeTagFrom(suffix, idx) {
    const arr = suffix==='add' ? currentTagsAdd : currentTagsEdit;
    arr.splice(idx,1);
    const chipsEl = document.getElementById(`tag-chips-${suffix}`);
    chipsEl.innerHTML = arr.map((t,i) => `
        <span class="tag-chip">${escHtml(t)}
            <button class="tag-chip-remove" onclick="removeTagFrom('${suffix}',${i})">×</button>
        </span>`).join('');
}

// ── 搜尋 ──────────────────────────────────────────────
function onSearch(val) {
    clearTimeout(searchTimer);
    const resultsEl = document.getElementById('search-results');
    const catList = document.getElementById('category-list');
    if (!val.trim()) { resultsEl.style.display='none'; catList.style.display='block'; return; }
    searchTimer = setTimeout(async () => {
        const prompts = await api(`/api/prompts?search=${encodeURIComponent(val)}`);
        catList.style.display='none'; resultsEl.style.display='block';
        const listEl = document.getElementById('search-results-list');
        if (!prompts.length) { listEl.innerHTML='<p class="empty-hint">沒有符合的提示詞</p>'; return; }
        listEl.innerHTML = prompts.map(p => `
            <div class="search-result-item" onclick="previewPrompt('${escHtml(p.title).replace(/'/g,"\\'")}',\`${(p.content||'').replace(/\\/g,'\\\\').replace(/`/g,'\\`')}\`,${JSON.stringify(p.tags||[])})">
                <div style="font-weight:600;">${escHtml(p.title)}</div>
                <div class="search-result-cat">${escHtml((p.content||'').substring(0,60))}...</div>
            </div>`).join('');
    }, 300);
}

// ── 類別 ──────────────────────────────────────────────
function openAddCategory() {
    document.getElementById('new-category-name').value = '';
    openModal('modal-add-category');
    setTimeout(() => document.getElementById('new-category-name').focus(), 100);
}
async function submitAddCategory() {
    const name = document.getElementById('new-category-name').value.trim();
    if (!name) return;
    const data = await api('/api/categories','POST',{name});
    if (data.error) { toast(data.error,'error'); return; }
    closeModal('modal-add-category');
    location.reload();
}

function openEditCategory(catId, currentName) {
    document.getElementById('edit-cat-id').value = catId;
    document.getElementById('edit-cat-name').value = currentName;
    openModal('modal-edit-category');
    setTimeout(() => document.getElementById('edit-cat-name').focus(), 100);
}
async function submitEditCategory() {
    const catId = document.getElementById('edit-cat-id').value;
    const name = document.getElementById('edit-cat-name').value.trim();
    if (!name) return;
    const data = await api(`/api/categories/${catId}`,'PUT',{name});
    if (data.error) { toast(data.error,'error'); return; }
    closeModal('modal-edit-category');
    const nameEl = document.getElementById(`cat-name-${catId}`);
    if (nameEl) nameEl.textContent = name;
    toast('類別名稱已更新');
}

async function deleteCategory(catId) {
    if (!confirm('確定刪除此類別？類別內的提示詞也會一併刪除。')) return;
    await api(`/api/categories/${catId}`,'DELETE');
    location.reload();
}

function initCategorySort() {
    const el = document.getElementById('category-list');
    if (!el || typeof Sortable==='undefined') return;
    Sortable.create(el, {
        handle: '.drag-handle', animation: 150, ghostClass: 'sortable-ghost',
        onEnd: async () => {
            const order = [...el.querySelectorAll('.category-block')].map(b => parseInt(b.dataset.catId));
            await api('/api/categories/reorder','POST',{order});
        }
    });
}

// ── 提示詞 ────────────────────────────────────────────
async function togglePrompts(catId, btn) {
    const listEl = document.getElementById(`prompts-${catId}`);
    const isOpen = listEl.style.display !== 'none';

    if (activeCatId && activeCatId !== catId) {
        const prev = document.getElementById(`prompts-${activeCatId}`);
        const prevBtn = document.querySelector(`[data-cat-id="${activeCatId}"] .btn-sm`);
        if (prev) prev.style.display = 'none';
        if (prevBtn) prevBtn.textContent = '展開';
    }

    if (isOpen) {
        listEl.style.display = 'none';
        btn.textContent = '展開';
        activeCatId = null; activeCatName = '全部';
        updateCollectionFilter(); loadCollections(); return;
    }

    btn.textContent = '收合';
    listEl.style.display = 'block';
    activeCatId = catId;
    activeCatName = btn.closest('.category-block').querySelector('.category-name').textContent;
    updateCollectionFilter();
    const prompts = await api(`/api/prompts?category_id=${catId}`);
    renderPrompts(catId, prompts);
    loadCollections(catId);
}

function updateCollectionFilter() {
    const label = document.getElementById('collection-filter-label');
    if (label) label.textContent = activeCatName;
}

function renderPrompts(catId, prompts) {
    const listEl = document.getElementById(`prompts-${catId}`);
    if (!prompts.length) { listEl.innerHTML='<p class="empty-hint" style="padding:10px 0;">尚無提示詞</p>'; return; }
    listEl.innerHTML = prompts.map(p => {
        const inComposer = composer.some(c => c.prompt_id===p.id);
        const safeTitle = (p.title||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'");
        const safeContent = (p.content||'').replace(/\\/g,'\\\\').replace(/`/g,'\\`').replace(/\$/g,'\\$');
        const tags = (p.tags||[]).map(t => `<span class="prompt-tag">${escHtml(t)}</span>`).join('');
        const star = p.is_starred ? '⭐' : '☆';
        return `
        <div class="prompt-item ${inComposer?'selected':''}" id="prompt-item-${p.id}" data-prompt-id="${p.id}">
            <span class="prompt-drag-handle">⠿</span>
            <input type="checkbox" ${inComposer?'checked':''}
                onchange="toggleComposer(${p.id},${p.version_id||0},'${safeTitle}',\`${safeContent}\`,${p.version_number||1},this)">
            <div class="prompt-info" style="cursor:pointer;" onclick="previewPrompt('${safeTitle}',\`${safeContent}\`,${JSON.stringify(p.tags||[])})">
                <div class="prompt-title">${escHtml(p.title)}</div>
                <div class="prompt-preview">${escHtml(p.content||'')}</div>
                <div class="prompt-meta">
                    <span class="prompt-version">v${p.version_number||1}</span>${tags}
                </div>
            </div>
            <div class="prompt-actions">
                <button class="btn-star" onclick="toggleStarPrompt(${p.id},${catId})">${star}</button>
                <button class="btn-sm" onclick="openVersions(${p.id})">版本</button>
                <button class="btn-sm" onclick="downloadPrompt(${p.id})">匯出</button>
                <button class="btn-sm danger" onclick="deletePrompt(${p.id},${catId})">刪除</button>
            </div>
        </div>`;
    }).join('');
    initPromptSort(catId);
}

function initPromptSort(catId) {
    const el = document.getElementById(`prompts-${catId}`);
    if (!el || typeof Sortable==='undefined') return;
    Sortable.create(el, {
        handle: '.prompt-drag-handle', animation:150, ghostClass:'sortable-ghost',
        onEnd: async () => {
            const order = [...el.querySelectorAll('.prompt-item')].map(b => parseInt(b.dataset.promptId));
            await api('/api/prompts/reorder','POST',{order});
        }
    });
}

function openAddPrompt(catId) {
    currentTagsAdd = [];
    document.getElementById('add-prompt-cat-id').value = catId;
    document.getElementById('new-prompt-title').value = '';
    document.getElementById('new-prompt-content').value = '';
    openModal('modal-add-prompt');
    // 等 modal 顯示後再初始化 tag 系統
    setTimeout(() => makeTagSystem('add'), 150);
}

async function submitAddPrompt() {
    const catId = document.getElementById('add-prompt-cat-id').value;
    const title = document.getElementById('new-prompt-title').value.trim();
    const content = document.getElementById('new-prompt-content').value.trim();
    if (!title || !content) { toast('請填寫標題與內容','error'); return; }
    const data = await api('/api/prompts','POST',{category_id:catId, title, content, tags:currentTagsAdd});
    if (data.error) { toast(data.error,'error'); return; }
    closeModal('modal-add-prompt');
    await loadAllTags();
    if (activeCatId == catId) {
        const prompts = await api(`/api/prompts?category_id=${catId}`);
        renderPrompts(catId, prompts);
    }
    toast('提示詞已新增');
}

async function deletePrompt(promptId, catId) {
    if (!confirm('確定刪除此提示詞？')) return;
    await api(`/api/prompts/${promptId}`,'DELETE');
    const prompts = await api(`/api/prompts?category_id=${catId}`);
    renderPrompts(catId, prompts);
    const idx = composer.findIndex(c => c.prompt_id===promptId);
    if (idx!==-1) { composer.splice(idx,1); renderComposer(); }
    toast('已刪除');
}

async function toggleStarPrompt(promptId, catId) {
    await api(`/api/prompts/${promptId}/star`,'POST');
    const prompts = await api(`/api/prompts?category_id=${catId}`);
    renderPrompts(catId, prompts);
}

// ── 預覽 ──────────────────────────────────────────────
let previewCurrentContent = '';
function previewPrompt(title, content, tags) {
    previewCurrentContent = content;
    document.getElementById('preview-title').textContent = title;
    document.getElementById('preview-content').textContent = content;
    const tagsEl = document.getElementById('preview-tags');
    tagsEl.innerHTML = (tags||[]).map(t => `<span class="prompt-tag">${escHtml(t)}</span>`).join('');
    openModal('modal-preview');
}
async function copyPreviewContent() {
    await navigator.clipboard.writeText(previewCurrentContent);
    toast('已複製 ✓');
}

// ── 版本 & Tag Modal ──────────────────────────────────
function switchTab(tab) {
    document.getElementById('pane-versions').style.display = tab==='versions' ? 'block' : 'none';
    document.getElementById('pane-tags').style.display = tab==='tags' ? 'block' : 'none';
    document.getElementById('tab-versions').className = 'tab-btn' + (tab==='versions'?' active':'');
    document.getElementById('tab-tags').className = 'tab-btn' + (tab==='tags'?' active':'');
    if (tab==='tags') setTimeout(() => makeTagSystem('edit'), 100);
}

async function openVersions(promptId) {
    document.getElementById('version-prompt-id').value = promptId;
    document.getElementById('new-version-content').value = '';
    document.getElementById('new-version-note').value = '';
    switchTab('versions');
    openModal('modal-versions');
    await refreshVersionList(promptId);
    // 載入目前 tags 供編輯
    const tags = await api(`/api/prompts/${promptId}/tags`);
    currentTagsEdit = [...tags];
    // 等 modal 完全顯示後初始化
    setTimeout(() => makeTagSystem('edit'), 150);
}

async function refreshVersionList(promptId) {
    const versions = await api(`/api/prompts/${promptId}/versions`);
    document.getElementById('version-list').innerHTML = versions.map((v,i) => `
        <div class="version-entry ${i===0?'version-latest':''}">
            <div class="version-header">
                <span class="version-num">v${v.version_number} ${i===0?'（目前版本）':''}</span>
                <span class="version-note">${escHtml(v.note||'')}</span>
                ${versions.length>1 ? `<button class="btn-sm danger" onclick="deleteVersion(${v.id},${promptId})" style="margin-left:auto;">刪除此版</button>` : ''}
            </div>
            <div class="version-content">${escHtml(v.content)}</div>
        </div>`).join('');
}

async function deleteVersion(versionId, promptId) {
    if (!confirm('確定刪除此版本？')) return;
    const data = await api(`/api/versions/${versionId}`,'DELETE');
    if (data.error) { toast(data.error,'error'); return; }
    await refreshVersionList(promptId);
    toast('版本已刪除');
}

async function submitAddVersion() {
    const promptId = parseInt(document.getElementById('version-prompt-id').value);
    const content = document.getElementById('new-version-content').value.trim();
    const note = document.getElementById('new-version-note').value.trim();
    if (!content) { toast('請填寫內容','error'); return; }
    await api(`/api/prompts/${promptId}/versions`,'POST',{content,note});
    await refreshVersionList(promptId);
    document.getElementById('new-version-content').value = '';
    document.getElementById('new-version-note').value = '';
    toast('新版本已新增');

    // 重新整理左側提示詞列表
    if (activeCatId) {
        const prompts = await api(`/api/prompts?category_id=${activeCatId}`);
        renderPrompts(activeCatId, prompts);

        // 更新組合器中同一個提示詞的內容和版本號
        const updated = prompts.find(p => p.id === promptId);
        if (updated) {
            const idx = composer.findIndex(c => c.prompt_id === promptId);
            if (idx !== -1) {
                composer[idx].content = updated.content;
                composer[idx].version_number = updated.version_number;
                composer[idx].prompt_version_id = updated.version_id;
                renderComposer();
                saveComposerState();
                toast('組合器已同步更新 ✓');
            }
        }
    }
}

async function submitEditTags() {
    const promptId = document.getElementById('version-prompt-id').value;
    await api(`/api/prompts/${promptId}/tags`,'POST',{tags:currentTagsEdit});
    await loadAllTags();
    toast('Tag 已儲存 ✓');
    closeModal('modal-versions');
    if (activeCatId) {
        const prompts = await api(`/api/prompts?category_id=${activeCatId}`);
        renderPrompts(activeCatId, prompts);
    }
}

// ── 組合器 ────────────────────────────────────────────
function toggleComposer(promptId, versionId, title, content, versionNum, checkbox) {
    const item = document.getElementById(`prompt-item-${promptId}`);
    if (checkbox.checked) {
        if (!composer.some(c => c.prompt_id===promptId))
            composer.push({prompt_id:promptId, prompt_version_id:versionId, title, content, version_number:versionNum});
        item.classList.add('selected');
    } else {
        const idx = composer.findIndex(c => c.prompt_id===promptId);
        if (idx!==-1) composer.splice(idx,1);
        item.classList.remove('selected');
    }
    renderComposer(); saveComposerState();
}

function renderComposer() {
    const listEl = document.getElementById('composer-list');
    const outputEl = document.getElementById('composer-output');
    if (!composer.length) {
        listEl.innerHTML='<p class="empty-hint" id="composer-empty">從左側勾選提示詞加入組合</p>';
        outputEl.value=''; return;
    }
    listEl.innerHTML = composer.map((c,i) => `
        <div class="composer-item">
            <div style="flex:1;min-width:0;">
                <div style="font-weight:600;font-size:13px;">${escHtml(c.title)} <span style="color:var(--accent);font-size:11px;">v${c.version_number}</span></div>
                <div class="composer-item-preview">${escHtml(c.content)}</div>
            </div>
            <button class="btn-remove" onclick="removeFromComposer(${i})">×</button>
        </div>`).join('');
    outputEl.value = composer.map(c => c.content).join('\n\n');
}

function removeFromComposer(idx) {
    const item = composer[idx];
    composer.splice(idx,1);
    const cb = document.querySelector(`#prompt-item-${item.prompt_id} input[type=checkbox]`);
    if (cb) { cb.checked=false; document.getElementById(`prompt-item-${item.prompt_id}`)?.classList.remove('selected'); }
    renderComposer(); saveComposerState();
}

function clearComposer() {
    composer.forEach(c => {
        const cb = document.querySelector(`#prompt-item-${c.prompt_id} input[type=checkbox]`);
        if (cb) { cb.checked=false; document.getElementById(`prompt-item-${c.prompt_id}`)?.classList.remove('selected'); }
    });
    composer.length=0; renderComposer(); saveComposerState();
}

async function copyComposed() {
    const text = document.getElementById('composer-output').value;
    if (!text) { toast('組合是空的','error'); return; }
    await navigator.clipboard.writeText(text);
    toast('已複製到剪貼簿 ✓');
}

function saveComposerState() {
    try { localStorage.setItem('pm-composer', JSON.stringify(composer)); } catch(e) {}
}
function restoreComposerState() {
    try {
        const saved = localStorage.getItem('pm-composer');
        if (saved) { const items=JSON.parse(saved); composer.length=0; items.forEach(i=>composer.push(i)); renderComposer(); }
    } catch(e) {}
}

// ── 組合庫 ────────────────────────────────────────────
function openSaveCollection() {
    if (!composer.length) { toast('請先勾選提示詞','error'); return; }
    document.getElementById('new-collection-name').value = '';
    openModal('modal-save-collection');
    setTimeout(() => document.getElementById('new-collection-name').focus(), 100);
}

async function submitSaveCollection() {
    const name = document.getElementById('new-collection-name').value.trim();
    if (!name) { toast('請輸入組合名稱','error'); return; }
    const combined_text = document.getElementById('composer-output').value;
    const items = composer.map(c => ({prompt_id:c.prompt_id, prompt_version_id:c.prompt_version_id}));
    const data = await api('/api/collections','POST',{name, combined_text, items});
    if (data.error) { toast(data.error,'error'); return; }
    closeModal('modal-save-collection');
    toast('組合已儲存 ✓');
    loadCollections(activeCatId);
}

async function loadCollections(catId) {
    const url = catId ? `/api/collections?category_id=${catId}` : '/api/collections';
    const cols = await api(url);
    const el = document.getElementById('collection-list');
    if (!cols.length) { el.innerHTML='<p class="empty-hint">尚無符合的組合</p>'; return; }
    el.innerHTML = cols.map(c => {
        const star = c.is_starred ? '⭐' : '☆';
        return `
        <div class="collection-item">
            <div class="collection-header">
                <span class="collection-name">${escHtml(c.name)}</span>
                <button class="btn-star" onclick="toggleStarCollection(${c.id})">${star}</button>
            </div>
            <div class="collection-meta">${c.created_at?c.created_at.slice(0,10):''}</div>
            <div class="collection-actions">
                <button class="btn-sm" onclick="copyCollection(${c.id})">複製</button>
                <button class="btn-sm" onclick="showCollectionDetail(${c.id})">詳細</button>
                <button class="btn-sm" onclick="downloadCollection(${c.id})">匯出</button>
                <button class="btn-sm danger" onclick="deleteCollection(${c.id})">刪除</button>
            </div>
        </div>`;
    }).join('');
}

async function copyCollection(colId) {
    const data = await api(`/api/collections/${colId}`);
    await navigator.clipboard.writeText(data.collection.combined_text);
    toast('已複製到剪貼簿 ✓');
}

async function showCollectionDetail(colId) {
    const data = await api(`/api/collections/${colId}`);
    const itemList = data.items.map(i => `• ${i.title} (v${i.version_number})`).join('\n');
    alert(`【${data.collection.name}】\n\n包含：\n${itemList}\n\n---\n${data.collection.combined_text}`);
}

async function deleteCollection(colId) {
    if (!confirm('確定刪除此組合？')) return;
    await api(`/api/collections/${colId}`,'DELETE');
    toast('已刪除'); loadCollections(activeCatId);
}

async function toggleStarCollection(colId) {
    await api(`/api/collections/${colId}/star`,'POST');
    loadCollections(activeCatId);
}

// ── 匯出 ──────────────────────────────────────────────
function downloadPrompt(promptId) { window.location=`/api/export/prompt/${promptId}`; }
function downloadCollection(colId) { window.location=`/api/export/collection/${colId}`; }

// ── 匯入 ──────────────────────────────────────────────
async function openImport() {
    importFiles = [];
    document.getElementById('import-file-list').innerHTML = '';
    document.getElementById('file-input').value = '';

    const cats = await api('/api/categories');
    const sel = document.getElementById('import-category-select');
    const hint = document.getElementById('import-no-cat-hint');

    if (!cats.length) {
        sel.style.display = 'none';
        hint.style.display = 'block';
        document.getElementById('import-submit-btn').disabled = true;
    } else {
        sel.style.display = 'block';
        hint.style.display = 'none';
        document.getElementById('import-submit-btn').disabled = false;
        sel.innerHTML = cats.map(c => `<option value="${c.id}">${escHtml(c.name)}</option>`).join('');
    }
    openModal('modal-import');
}

async function createCatAndRefreshImport() {
    const name = document.getElementById('import-new-cat-name').value.trim();
    if (!name) { toast('請輸入類別名稱','error'); return; }
    const data = await api('/api/categories','POST',{name});
    if (data.error) { toast(data.error,'error'); return; }
    toast('類別已建立');
    // 重新整理匯入 modal
    await openImport();
    // 選到新建立的類別
    const sel = document.getElementById('import-category-select');
    for (let opt of sel.options) { if (opt.text === name) { opt.selected=true; break; } }
    // 重新整理主頁類別
    location.reload();
}

function onFileSelected(input) {
    importFiles = [...input.files];
    renderImportFileList();
}

function renderImportFileList() {
    const el = document.getElementById('import-file-list');
    el.innerHTML = importFiles.map((f,i) => `
        <div class="import-file-item">
            <span class="import-file-name">${escHtml(f.name)}</span>
            <span class="import-file-status" id="import-status-${i}">待匯入</span>
        </div>`).join('');
}

async function submitImport() {
    if (!importFiles.length) { toast('請先選擇檔案','error'); return; }
    const catId = document.getElementById('import-category-select')?.value || '';
    let successCount = 0;
    for (let i=0; i<importFiles.length; i++) {
        const statusEl = document.getElementById(`import-status-${i}`);
        try {
            const text = await importFiles[i].text();
            // 先解析，判斷是否為完整備份（含類別結構）
            let parsed;
            try { parsed = JSON.parse(text); } catch(e) { throw new Error('JSON格式錯誤'); }
            const isFullBackup = parsed.version === '2' && parsed.categories;
            const url = isFullBackup ? '/api/import' : `/api/import?category_id=${catId}`;
            const fd = new FormData();
            fd.append('file', new Blob([text],{type:'application/json'}), importFiles[i].name);
            const res = await fetch(url, {method:'POST', body:fd});
            const data = await res.json();
            if (data.ok) {
                if (statusEl) { statusEl.textContent='✓ '+data.message; statusEl.className='import-file-status ok'; }
                successCount++;
            } else {
                if (statusEl) { statusEl.textContent='✗ '+(data.error||'失敗'); statusEl.className='import-file-status err'; }
            }
        } catch(e) {
            if (statusEl) { statusEl.textContent='✗ '+(e.message||'格式錯誤'); statusEl.className='import-file-status err'; }
        }
    }
    if (successCount > 0) setTimeout(() => { closeModal('modal-import'); location.reload(); }, 1200);
}

function initDropZone() {
    const area = document.getElementById('upload-area');
    if (!area) return;
    area.addEventListener('dragover', e => { e.preventDefault(); area.style.borderColor='var(--accent)'; });
    area.addEventListener('dragleave', () => { area.style.borderColor=''; });
    area.addEventListener('drop', e => {
        e.preventDefault(); area.style.borderColor='';
        importFiles = [...e.dataTransfer.files].filter(f => f.name.endsWith('.json'));
        renderImportFileList();
    });
}

// ── 鍵盤 ──────────────────────────────────────────────
document.addEventListener('keydown', e => {
    if (e.key==='Escape') document.querySelectorAll('.modal-overlay').forEach(m => m.style.display='none');
});

// ── 頁面載入 ──────────────────────────────────────────
// ── 手機底部導覽 ──────────────────────────────────────
function isMobile() { return window.innerWidth <= 900; }

function mobileNav(tab) {
    if (!isMobile()) return;

    const panels = {
        prompts: document.querySelector('.panel-left'),
        composer: document.querySelector('.panel-mid') || document.querySelectorAll('.panel')[1],
        collections: document.querySelector('.panel-right') || document.querySelectorAll('.panel')[2]
    };

    // 取得所有面板（排除抽屜）
    const allPanels = document.querySelectorAll('.dashboard > .panel:not(.panel-left), .dashboard > .panel-left');

    // 先全部隱藏
    allPanels.forEach(p => p.classList.add('mobile-hidden'));

    // 顯示選中的
    if (tab === 'prompts') {
        const leftPanel = document.getElementById('panel-left');
        if (leftPanel) {
            leftPanel.classList.remove('mobile-hidden');
            leftPanel.classList.add('open');
            leftPanel.style.transform = 'translateX(0)';
            leftPanel.style.position = 'relative';
            leftPanel.style.width = '100%';
            leftPanel.style.boxShadow = 'none';
        }
    } else {
        // 關閉抽屜
        const leftPanel = document.getElementById('panel-left');
        if (leftPanel) leftPanel.classList.add('mobile-hidden');

        const allDashPanels = document.querySelectorAll('.dashboard > *:not(.panel-left):not(.drawer-overlay):not(.collapse-btn):not(.mobile-nav)');
        allDashPanels.forEach((p, i) => {
            if ((tab === 'composer' && i === 0) || (tab === 'collections' && i === 1)) {
                p.classList.remove('mobile-hidden');
            } else {
                p.classList.add('mobile-hidden');
            }
        });
    }

    // 更新按鈕狀態
    document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));
    const activeBtn = document.getElementById('mnav-' + tab);
    if (activeBtn) activeBtn.classList.add('active');
}

function initMobileNav() {
    if (!isMobile()) return;
    mobileNav('prompts');
}

function toggleLeftPanel() {
    const panel = document.getElementById('panel-left');
    const overlay = document.getElementById('drawer-overlay');
    const btn = document.getElementById('collapse-btn');
    if (!panel) return;
    const isOpen = panel.classList.toggle('open');
    if (overlay) overlay.classList.toggle('show', isOpen);
    if (btn) btn.style.display = isOpen ? 'none' : '';
}

function restoreLeftPanel() {
    // 抽屜預設關閉，不需要恢復狀態
}

window.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initCategorySort();
    initMobileNav();
    restoreComposerState();
    loadCollections();
    loadAllTags();
    initDropZone();

    document.getElementById('new-category-name')?.addEventListener('keydown', e => { if(e.key==='Enter') submitAddCategory(); });
    document.getElementById('edit-cat-name')?.addEventListener('keydown', e => { if(e.key==='Enter') submitEditCategory(); });
    document.getElementById('new-collection-name')?.addEventListener('keydown', e => { if(e.key==='Enter') submitSaveCollection(); });
    document.getElementById('new-version-note')?.addEventListener('keydown', e => { if(e.key==='Enter') submitAddVersion(); });
});
