// Global state
let state = {
    persons: [],
    platforms: [],
    events: {},
    unlinkedEvents: [],
    stats: {},
    maigretResults: null,
    maigretLoading: false
};

let maigretProgressTimer = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadInitialData();
    setInterval(refreshData, 30000); // Refresh every 30 seconds
});

// Tab switching
function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            switchTab(targetTab);
        });
    });
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'instagram') loadPlatformEvents('instagram');
    else if (tabName === 'pinterest') loadPlatformEvents('pinterest');
    else if (tabName === 'spotify') loadPlatformEvents('spotify');
    else if (tabName === 'maigret') renderMaigretResults();
    else if (tabName === 'settings') loadSettings();
}

// Load initial data
async function loadInitialData() {
    await Promise.all([
        loadStats(),
        loadPlatforms(),
        loadPersons(),
        loadUnlinkedEvents()
    ]);
}

async function refreshData() {
    await loadInitialData();
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        alert(`Error: ${error.message}`);
        throw error;
    }
}

// Stats
async function loadStats() {
    const data = await apiCall('/api/stats');
    state.stats = data.stats;
    renderStats();
}

function renderStats() {
    const statsEl = document.getElementById('stats');
    statsEl.innerHTML = `
        <div class="stat-item">
            <div class="stat-value">${state.stats.total_persons || 0}</div>
            <div class="stat-label">Persons</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${state.stats.total_profiles || 0}</div>
            <div class="stat-label">Profiles</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">${state.stats.recent_events || 0}</div>
            <div class="stat-label">Recent Events</div>
        </div>
    `;
}

// Maigret Search
async function searchMaigret(event) {
    event.preventDefault();

    const username = document.getElementById('maigret-username').value.trim();
    const topSites = parseInt(document.getElementById('maigret-top-sites').value, 10);
    const timeout = parseInt(document.getElementById('maigret-timeout').value, 10);
    const maxConnections = parseInt(document.getElementById('maigret-max-connections').value, 10);
    const retries = parseInt(document.getElementById('maigret-retries').value, 10);
    const idType = document.getElementById('maigret-id-type').value;
    const tags = document.getElementById('maigret-tags').value;
    const siteList = document.getElementById('maigret-sites').value;
    const allSites = document.getElementById('maigret-all-sites').checked;
    const includeDisabled = document.getElementById('maigret-include-disabled').checked;
    const checkDomains = document.getElementById('maigret-check-domains').checked;
    const useCookies = document.getElementById('maigret-use-cookies').checked;

    if (!username) {
        alert('Username is required');
        return;
    }

    setMaigretLoading(true);
    startMaigretProgress();
    const resultsContainer = document.getElementById('maigret-results');
    resultsContainer.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">🔎</div>
            <p>Searching for @${escapeHtml(username)}...</p>
        </div>
    `;

    try {
        const data = await apiCall('/api/maigret/search', {
            method: 'POST',
            body: JSON.stringify({
                username,
                top_sites: topSites,
                timeout,
                max_connections: maxConnections,
                retries,
                id_type: idType,
                tags,
                site_list: siteList,
                all_sites: allSites,
                include_disabled: includeDisabled,
                check_domains: checkDomains,
                use_cookies: useCookies
            })
        });

        state.maigretResults = data;
        renderMaigretResults();
    } catch (error) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <p>${escapeHtml(error.message || 'Search failed')}</p>
            </div>
        `;
    } finally {
        stopMaigretProgress();
        setMaigretLoading(false);
    }
}

function setMaigretLoading(isLoading) {
    state.maigretLoading = isLoading;
    const button = document.getElementById('maigret-search-btn');
    if (!button) return;
    button.disabled = isLoading;
    button.textContent = isLoading ? 'Searching...' : 'Search';
}

function startMaigretProgress() {
    const container = document.getElementById('maigret-progress');
    const bar = document.getElementById('maigret-progress-bar');
    const text = document.getElementById('maigret-progress-text');
    if (!container || !bar) return;

    container.classList.add('active');
    if (text) {
        text.textContent = 'Searching...';
    }

    let progress = 5;
    bar.style.width = `${progress}%`;

    if (maigretProgressTimer) {
        clearInterval(maigretProgressTimer);
    }

    maigretProgressTimer = setInterval(() => {
        progress = Math.min(progress + Math.random() * 8 + 4, 90);
        bar.style.width = `${progress}%`;
    }, 700);
}

function stopMaigretProgress() {
    const container = document.getElementById('maigret-progress');
    const bar = document.getElementById('maigret-progress-bar');
    const text = document.getElementById('maigret-progress-text');
    if (!container || !bar) return;

    if (maigretProgressTimer) {
        clearInterval(maigretProgressTimer);
        maigretProgressTimer = null;
    }

    bar.style.width = '100%';
    if (text) {
        text.textContent = 'Complete';
    }

    setTimeout(() => {
        container.classList.remove('active');
        bar.style.width = '0%';
    }, 600);
}

function renderMaigretResults() {
    const container = document.getElementById('maigret-results');
    if (!container) return;

    if (!state.maigretResults) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔎</div>
                <p>Run a search to see results.</p>
            </div>
        `;
        return;
    }

    const { username, stats, found, filters } = state.maigretResults;
    const duration = formatDuration(stats.duration_ms);
    const scopeSites = stats.scope_sites || stats.checked_sites || 0;
    const tags = (filters && filters.tags && filters.tags.length) ? filters.tags.join(', ') : null;
    const sites = (filters && filters.site_list && filters.site_list.length) ? filters.site_list.join(', ') : null;

    if (!found || found.length === 0) {
        container.innerHTML = `
            <div class="search-summary">
                <div class="summary-title">Results for @${escapeHtml(username)}</div>
                <div class="help-text">
                    Checked ${stats.checked_sites} of ${scopeSites} sites in ${duration}.
                    ${tags ? `<br>Tags: ${escapeHtml(tags)}` : ''}
                    ${sites ? `<br>Sites: ${escapeHtml(sites)}` : ''}
                </div>
            </div>
            <div class="empty-state">
                <div class="empty-state-icon">🕵️</div>
                <p>No claimed profiles found.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="search-summary">
            <div class="summary-title">Results for @${escapeHtml(username)}</div>
            <div class="help-text">
                Found ${found.length} profiles across ${stats.checked_sites} of ${scopeSites} sites in ${duration}.
                ${tags ? `<br>Tags: ${escapeHtml(tags)}` : ''}
                ${sites ? `<br>Sites: ${escapeHtml(sites)}` : ''}
            </div>
        </div>
        <div class="results-grid">
            ${found.map(result => {
                const url = result.url ? escapeHtml(result.url) : '';
                const tags = result.tags && result.tags.length
                    ? `<div class="result-tags">${result.tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}</div>`
                    : '';
                return `
                    <div class="result-item">
                        <div class="result-header">
                            <div class="result-site">${escapeHtml(result.site_name)}</div>
                            ${url ? `<a class="result-link" href="${url}" target="_blank" rel="noopener">Open</a>` : ''}
                        </div>
                        ${url ? `<div class="result-url">${url}</div>` : ''}
                        ${tags}
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// Platforms
async function loadPlatforms() {
    const data = await apiCall('/api/platforms');
    state.platforms = data.platforms;
}

// Persons
async function loadPersons() {
    const data = await apiCall('/api/persons');
    state.persons = data.persons;
    renderPersons();
}

function renderPersons() {
    const container = document.getElementById('persons-list');
    
    if (state.persons.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">👤</div>
                <p>No persons yet. Click "Add Person" to start monitoring.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = state.persons.map(person => {
        const latestEvent = person.latest_event;
        const timeAgo = latestEvent ? formatTimeAgo(latestEvent.event_time || latestEvent.created_at) : null;
        
        return `
            <div class="person-card">
                <div class="person-header">
                    <div>
                        <div class="person-name">${escapeHtml(person.name)}</div>
                        ${person.notes ? `<div class="help-text">${escapeHtml(person.notes)}</div>` : ''}
                    </div>
                    <div class="person-actions">
                        <button class="btn-icon" onclick="showLinkProfileModal(${person.id})" title="Link profile">🔗</button>
                        <button class="btn-icon" onclick="editPerson(${person.id})" title="Edit">✏️</button>
                        <button class="btn-icon" onclick="deletePerson(${person.id})" title="Delete">🗑️</button>
                    </div>
                </div>
                
                <div class="profiles">
                    ${person.profiles.length === 0 ? 
                        '<span class="help-text">No profiles linked</span>' :
                        person.profiles.map(p => `
                            <span class="profile-badge">
                                ${getPlatformIcon(p.platform_name)} ${escapeHtml(p.platform_username)}
                                <span class="remove" onclick="unlinkProfile(${p.id})" title="Unlink">×</span>
                            </span>
                        `).join('')
                    }
                </div>
                
                <div class="latest-activity">
                    ${latestEvent ? `
                        <div class="activity-time">Last update: ${timeAgo}</div>
                        <div class="activity-summary">${escapeHtml(latestEvent.summary)}</div>
                    ` : `
                        <div class="no-activity">No activity yet</div>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

// Unlinked events
async function loadUnlinkedEvents() {
    const data = await apiCall('/api/events/unlinked');
    state.unlinkedEvents = data.events;
    renderUnlinkedEvents();
}

function renderUnlinkedEvents() {
    const container = document.getElementById('unlinked-events');
    
    if (state.unlinkedEvents.length === 0) {
        container.innerHTML = '<div class="help-text">No unlinked events</div>';
        return;
    }
    
    container.innerHTML = state.unlinkedEvents.slice(0, 10).map(event => 
        renderEvent(event)
    ).join('');
}

// Platform events
async function loadPlatformEvents(platformName) {
    const platform = state.platforms.find(p => p.name === platformName);
    if (!platform) return;
    
    const data = await apiCall(`/api/events?platform_id=${platform.id}&limit=50`);
    state.events[platformName] = data.events;
    renderPlatformEvents(platformName);
}

function renderPlatformEvents(platformName) {
    const container = document.getElementById(`${platformName}-events`);
    const events = state.events[platformName] || [];
    
    if (events.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">${getPlatformIcon(platformName)}</div>
                <p>No ${platformName} events yet</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = events.map(event => renderEvent(event)).join('');
}

function renderEvent(event) {
    const timeAgo = formatTimeAgo(event.event_time || event.created_at);
    
    return `
        <div class="event-item">
            <div class="event-icon">${getPlatformIcon(event.platform_name)}</div>
            <div class="event-content">
                <div class="event-header">
                    <div>
                        <span class="event-username">@${escapeHtml(event.platform_username)}</span>
                        ${event.person_name ? `<span class="help-text"> (${escapeHtml(event.person_name)})</span>` : ''}
                    </div>
                    <div class="event-time">${timeAgo}</div>
                </div>
                <div class="event-summary">${escapeHtml(event.summary)}</div>
            </div>
        </div>
    `;
}

// Settings
async function loadSettings() {
    renderWebhookInfo();
    renderPersonsManager();
    renderPlatformsConfig();
    loadInstagramSession();
    loadInstagramFirefoxProfiles();
}

function renderWebhookInfo() {
    const container = document.getElementById('webhook-info');
    container.innerHTML = state.platforms.map(platform => `
        <div class="webhook-item">
            <h4>${getPlatformIcon(platform.name)} ${platform.display_name}</h4>
            <p class="help-text">Configure your ${platform.display_name} monitor to POST webhooks to:</p>
            <div class="webhook-url">${platform.webhook_url}</div>
        </div>
    `).join('');
}

function renderPersonsManager() {
    const container = document.getElementById('persons-manager');
    
    if (state.persons.length === 0) {
        container.innerHTML = '<p class="help-text">No persons yet</p>';
        return;
    }
    
    container.innerHTML = `
        <table class="persons-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Profiles</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${state.persons.map(person => `
                    <tr>
                        <td>
                            <strong>${escapeHtml(person.name)}</strong>
                            ${person.notes ? `<br><span class="help-text">${escapeHtml(person.notes)}</span>` : ''}
                        </td>
                        <td>${person.profiles.length} linked</td>
                        <td>
                            <button class="btn-icon" onclick="showLinkProfileModal(${person.id})">🔗</button>
                            <button class="btn-icon" onclick="editPerson(${person.id})">✏️</button>
                            <button class="btn-icon" onclick="deletePerson(${person.id})">🗑️</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function renderPlatformsConfig() {
    const container = document.getElementById('platforms-config');
    
    container.innerHTML = `
        <table class="persons-table">
            <thead>
                <tr>
                    <th>Platform</th>
                    <th>Trigger URL</th>
                    <th>Webhook Secret</th>
                    <th>Configuration</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${state.platforms.map(platform => `
                    <tr>
                        <td><strong>${getPlatformIcon(platform.name)} ${platform.display_name}</strong></td>
                        <td>
                            <input type="text" 
                                   id="trigger-url-${platform.id}" 
                                   value="${platform.trigger_url || ''}" 
                                   placeholder="http://localhost:5001/api/check-now"
                                   style="width: 100%; padding: 4px 8px; background: var(--bg-tertiary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 4px;">
                        </td>
                        <td>
                            <input type="password" 
                                   id="secret-${platform.id}" 
                                   value="${platform.webhook_secret || ''}" 
                                   placeholder="Optional"
                                   style="width: 100%; padding: 4px 8px; background: var(--bg-tertiary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 4px;">
                        </td>
                        <td>
                            <button class="btn-icon" onclick="showPlatformConfigModal(${platform.id})" title="Configure">⚙️</button>
                        </td>
                        <td>
                            <button class="btn btn-primary" onclick="savePlatformSettings(${platform.id})" style="padding: 4px 12px; font-size: 0.85rem;">Save</button>
                            <button class="btn btn-secondary" onclick="triggerPlatformCheck(${platform.id})" style="padding: 4px 12px; font-size: 0.85rem;">Trigger Check</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// Instagram session management
function getInstagramBaseUrl() {
    const input = document.getElementById('instagram-session-base-url');
    if (!input) return 'http://localhost:8000';
    let base = input.value.trim() || input.placeholder || 'http://localhost:8000';
    if (!base.startsWith('http://') && !base.startsWith('https://')) {
        base = `http://${base}`;
    }
    return base.replace(/\/+$/, '');
}

function instagramSessionApi(path, options = {}) {
    const baseUrl = encodeURIComponent(getInstagramBaseUrl());
    const url = `/api/instagram${path}?base_url=${baseUrl}`;
    return apiCall(url, options);
}

async function loadInstagramSession() {
    try {
        const data = await instagramSessionApi('/session');
        renderInstagramSession(data);
    } catch (error) {
        renderInstagramSession(null, error.message || 'Failed to load session');
    }
}

function renderInstagramSession(data, errorMessage) {
    const badge = document.getElementById('instagram-session-badge');
    const text = document.getElementById('instagram-session-text');
    const meta = document.getElementById('instagram-session-meta');
    if (!badge || !text || !meta) return;

    if (!data) {
        badge.textContent = 'Error';
        badge.className = 'status-badge status-error';
        text.textContent = errorMessage || 'Failed to load';
        meta.textContent = '';
        return;
    }

    const active = data.active === true;
    const username = data.username ? `@${data.username}` : 'No session configured';
    badge.textContent = active ? 'Active' : 'Inactive';
    badge.className = `status-badge ${active ? 'status-active' : 'status-idle'}`;
    text.textContent = username;

    const details = [];
    if (data.method) details.push(`Method: ${data.method}`);
    if (data.file_path) details.push(`File: ${data.file_path}`);
    if (data.file_size_human) details.push(`Size: ${data.file_size_human}`);
    if (data.last_modified_relative) details.push(`Updated: ${data.last_modified_relative}`);
    meta.textContent = details.join(' • ');
}

async function setInstagramSession() {
    const usernameInput = document.getElementById('instagram-session-username');
    const methodSelect = document.getElementById('instagram-session-method');
    const username = usernameInput ? usernameInput.value.trim() : '';
    const method = methodSelect ? methodSelect.value : 'session';
    if (!username) {
        alert('Session username is required');
        return;
    }
    await instagramSessionApi('/session', {
        method: 'POST',
        body: JSON.stringify({ username, method })
    });
    await loadInstagramSession();
}

async function loadInstagramFirefoxProfiles() {
    const select = document.getElementById('instagram-firefox-profile');
    if (!select) return;
    select.innerHTML = '<option value="">Loading...</option>';
    try {
        const data = await instagramSessionApi('/session/firefox/profiles');
        if (!data.success || !data.profiles || data.profiles.length === 0) {
            select.innerHTML = '<option value="">No profiles found</option>';
            return;
        }
        select.innerHTML = data.profiles
            .map(profile => `<option value="${profile.path}">${profile.name}</option>`)
            .join('');
    } catch (error) {
        select.innerHTML = '<option value="">Failed to load profiles</option>';
    }
}

async function importInstagramFirefoxSession() {
    const select = document.getElementById('instagram-firefox-profile');
    const path = select ? select.value : '';
    if (!path) {
        alert('Select a Firefox profile first');
        return;
    }
    await instagramSessionApi('/session/firefox/import', {
        method: 'POST',
        body: JSON.stringify({ path })
    });
    await loadInstagramSession();
}

async function testInstagramSession() {
    await instagramSessionApi('/session/test', { method: 'POST', body: JSON.stringify({}) });
    await loadInstagramSession();
}

async function refreshInstagramSession() {
    await instagramSessionApi('/session/refresh', { method: 'POST', body: JSON.stringify({}) });
    await loadInstagramSession();
}

async function clearInstagramSession() {
    if (!confirm('Clear the current Instagram session?')) return;
    await instagramSessionApi('/session/clear', { method: 'POST', body: JSON.stringify({}) });
    await loadInstagramSession();
}

// Person modals
function showAddPersonModal() {
    document.getElementById('person-id').value = '';
    document.getElementById('person-name').value = '';
    document.getElementById('person-notes').value = '';
    document.getElementById('person-modal-title').textContent = 'Add Person';
    openModal('person-modal');
}

function editPerson(personId) {
    const person = state.persons.find(p => p.id === personId);
    if (!person) return;
    
    document.getElementById('person-id').value = person.id;
    document.getElementById('person-name').value = person.name;
    document.getElementById('person-notes').value = person.notes || '';
    document.getElementById('person-modal-title').textContent = 'Edit Person';
    openModal('person-modal');
}

async function savePerson(event) {
    event.preventDefault();
    
    const personId = document.getElementById('person-id').value;
    const name = document.getElementById('person-name').value.trim();
    const notes = document.getElementById('person-notes').value.trim();
    
    if (personId) {
        await apiCall(`/api/persons/${personId}`, {
            method: 'PUT',
            body: JSON.stringify({ name, notes })
        });
    } else {
        await apiCall('/api/persons', {
            method: 'POST',
            body: JSON.stringify({ name, notes })
        });
    }
    
    closeModal('person-modal');
    await loadPersons();
    await loadStats();
}

async function deletePerson(personId) {
    if (!confirm('Delete this person and all their linked profiles?')) return;
    
    await apiCall(`/api/persons/${personId}`, { method: 'DELETE' });
    await loadPersons();
    await loadStats();
}

// Profile linking
function showLinkProfileModal(personId) {
    document.getElementById('profile-person-id').value = personId;
    document.getElementById('profile-username').value = '';
    
    const platformSelect = document.getElementById('profile-platform');
    platformSelect.innerHTML = state.platforms.map(p => 
        `<option value="${p.id}">${getPlatformIcon(p.name)} ${p.display_name}</option>`
    ).join('');
    
    openModal('profile-modal');
}

async function linkProfile(event) {
    event.preventDefault();
    
    const personId = document.getElementById('profile-person-id').value;
    const platformId = document.getElementById('profile-platform').value;
    const username = document.getElementById('profile-username').value.trim();
    
    await apiCall(`/api/persons/${personId}/profiles`, {
        method: 'POST',
        body: JSON.stringify({ platform_id: parseInt(platformId), username })
    });
    
    closeModal('profile-modal');
    await loadPersons();
    await loadStats();
}

async function unlinkProfile(profileId) {
    if (!confirm('Unlink this profile?')) return;
    
    await apiCall(`/api/profiles/${profileId}`, { method: 'DELETE' });
    await loadPersons();
    await loadStats();
}

// Modal helpers
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Utility functions
function getPlatformIcon(platformName) {
    const icons = {
        instagram: '📷',
        pinterest: '📌',
        spotify: '🎵'
    };
    return icons[platformName] || '📱';
}

function formatTimeAgo(timestamp) {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    const weeks = Math.floor(days / 7);
    if (weeks < 4) return `${weeks}w ago`;
    const months = Math.floor(days / 30);
    return `${months}mo ago`;
}

function formatDuration(ms) {
    if (ms === null || ms === undefined) return '0s';
    const seconds = ms / 1000;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remaining = Math.round(seconds % 60);
    return `${minutes}m ${remaining}s`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Trigger all platform checks
async function triggerAllChecks() {
    if (!confirm('Trigger manual checks for all configured platforms?')) return;
    
    const results = [];
    for (const platform of state.platforms) {
        if (platform.trigger_url) {
            try {
                const result = await apiCall(`/api/platforms/${platform.id}/trigger`, {
                    method: 'POST'
                });
                results.push(`✓ ${platform.display_name}: ${result.message}`);
            } catch (error) {
                results.push(`✗ ${platform.display_name}: ${error.message}`);
            }
        }
    }
    
    if (results.length === 0) {
        alert('No platforms have trigger URLs configured. Configure them in Settings.');
    } else {
        alert('Trigger Results:\n\n' + results.join('\n'));
        
        // Refresh data after a moment
        setTimeout(async () => {
            await loadInitialData();
        }, 3000);
    }
}

// Platform settings
async function savePlatformSettings(platformId) {
    const triggerUrl = document.getElementById(`trigger-url-${platformId}`).value.trim();
    const secret = document.getElementById(`secret-${platformId}`).value.trim();
    
    try {
        await apiCall(`/api/platforms/${platformId}`, {
            method: 'PUT',
            body: JSON.stringify({
                trigger_url: triggerUrl || null,
                webhook_secret: secret || null
            })
        });
        
        alert('Platform settings saved!');
        await loadPlatforms();
    } catch (error) {
        console.error('Failed to save platform settings:', error);
    }
}

async function triggerPlatformCheck(platformId) {
    const platform = state.platforms.find(p => p.id === platformId);
    if (!platform) return;
    
    if (!platform.trigger_url) {
        alert(`No trigger URL configured for ${platform.display_name}. Please set it first and save.`);
        return;
    }
    
    if (!confirm(`Trigger a manual check for ${platform.display_name}?`)) return;
    
    try {
        const result = await apiCall(`/api/platforms/${platformId}/trigger`, {
            method: 'POST'
        });
        
        alert(result.message || 'Check triggered successfully!');
        
        // Refresh events after a moment
        setTimeout(async () => {
            await loadInitialData();
        }, 2000);
    } catch (error) {
        alert(`Failed to trigger check: ${error.message}`);
    }
}

function showPlatformConfigModal(platformId) {
    const platform = state.platforms.find(p => p.id === platformId);
    if (!platform) return;
    
    const config = platform.config_json ? JSON.parse(platform.config_json) : {};
    
    // Create a simple config editor modal
    const configStr = JSON.stringify(config, null, 2);
    const newConfig = prompt(
        `Edit configuration for ${platform.display_name} (JSON format):\n\nExample:\n{\n  "check_interval": 300,\n  "enabled": true\n}`,
        configStr
    );
    
    if (newConfig !== null) {
        try {
            JSON.parse(newConfig); // Validate JSON
            savePlatformConfig(platformId, newConfig);
        } catch (e) {
            alert('Invalid JSON format!');
        }
    }
}

async function savePlatformConfig(platformId, configJson) {
    try {
        await apiCall(`/api/platforms/${platformId}`, {
            method: 'PUT',
            body: JSON.stringify({ config_json: configJson })
        });
        
        alert('Configuration saved!');
        await loadPlatforms();
    } catch (error) {
        alert(`Failed to save configuration: ${error.message}`);
    }
}
