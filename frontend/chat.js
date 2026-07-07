const API_BASE = window.location.origin;
const messagesArea = document.getElementById('messages-area');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const errorToast = document.getElementById('error-toast');
const docCount = document.getElementById('doc-count');
const chunkCount = document.getElementById('chunk-count');
let isLoading = false;

async function loadStats() {
    try {
        const res = await fetch(API_BASE + '/api/stats');
        if (res.ok) {
            const data = await res.json();
            docCount.textContent = data.total_documents_indexed + ' CVs';
            chunkCount.textContent = data.total_chunks_indexed + ' chunks';
        }
    } catch (e) {
        console.error('Failed to load stats:', e);
        docCount.textContent = '?';
        chunkCount.textContent = '?';
    }
}
loadStats();

function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

function askExample(btn) {
    chatInput.value = btn.textContent.trim();
    autoResize(chatInput);
    chatInput.focus();
}

function showError(msg) {
    errorToast.textContent = msg;
    errorToast.classList.add('visible');
    setTimeout(() => errorToast.classList.remove('visible'), 5000);
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

function formatText(text) {
    let html = escapeHtml(text);
    html = html.split('\n').join('<br>');
    html = html.split('**').map(function(part, i) {
        return i % 2 === 1 ? '<strong>' + part + '</strong>' : part;
    }).join('');
    html = html.split('*').map(function(part, i) {
        return i % 2 === 1 ? '<em>' + part + '</em>' : part;
    }).join('');
    html = html.split('`').map(function(part, i) {
        return i % 2 === 1 ? '<code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:0.9em;">' + part + '</code>' : part;
    }).join('');
    return html;
}

function addMessage(text, sender, sources) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ' + sender;
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        const tags = sources.map(function(s) {
            return '<span class="source-tag">' + s + '</span>';
        }).join('');
        sourcesHtml = '<div class="sources-box"><div class="sources-box-title">Sources</div><div>' + tags + '</div></div>';
    }
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    msgDiv.innerHTML = '<div class="message-bubble">' + formatText(text) + sourcesHtml + '</div><div class="message-meta">' + (sender === 'user' ? 'You' : 'AI Assistant') + ' &bull; ' + time + '</div>';
    messagesArea.appendChild(msgDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function showThinking() {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message assistant';
    thinkingDiv.id = 'thinking-indicator';
    thinkingDiv.innerHTML = '<div class="message-bubble"><div class="thinking"><span>Searching CVs and generating answer</span><div class="thinking-dots"><span></span><span></span><span></span></div></div></div>';
    messagesArea.appendChild(thinkingDiv);
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

function hideThinking() {
    const el = document.getElementById('thinking-indicator');
    if (el) el.remove();
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isLoading) return;
    const welcome = messagesArea.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    addMessage(text, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';
    isLoading = true;
    sendBtn.disabled = true;
    showThinking();
    try {
        const res = await fetch(API_BASE + '/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text, top_k: 5 })
        });
        hideThinking();
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Request failed');
        }
        const data = await res.json();
        addMessage(data.answer, 'assistant', data.sources);
        loadStats();
    } catch (err) {
        hideThinking();
        showError(err.message || 'Failed to get response. Is the backend running?');
        console.error(err);
    } finally {
        isLoading = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

chatInput.focus();
