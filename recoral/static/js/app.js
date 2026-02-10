const App = (() => {
    const state = {
        identities: [],
        events: [],
        stats: {},
        searchResults: null,
        currentView: 'dashboard',
        detailId: null,
        activityOffset: 0,
        activityTotal: 0,
    };

    const PAGE_SIZE = 50;
    let progressTimer = null;

    // ---- Init ----
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.nav-item').forEach(el =>
            el.addEventListener('click', () => navigate(el.dataset.view))
        );
        loadDashboard();
        setInterval(() => { if (state.currentView === 'dashboard') loadDashboard(); }, 30000);
    });

    // ---- Navigation ----
    function navigate(view) {
        state.currentView = view;
        document.querySelectorAll('.nav-item').forEach(n =>
            n.classList.toggle('active', n.dataset.view === view)
        );
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        const el = document.getElementById(`view-${view}`);
        if (el) el.classList.add('active');

        if (view === 'dashboard') loadDashboard();
        else if (view === 'identities') loadIdentities();
        else if (view === 'activity') { state.activityOffset = 0; loadActivity(); }
        else if (view === 'settings') loadSettings();
    }

    // ---- API ----
    async function api(url, opts = {}) {
        try {
            const resp = await fetch(url, {
                ...opts,
                headers: { 'Content-Type': 'application/json', ...opts.headers },
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || `Request failed (${resp.status})`);
            return data;
        } catch (e) {
            if (!opts.silent) toast(e.message, true);
            throw e;
        }
    }

    // ---- Dashboard ----
    async function loadDashboard() {
        const [statsData, eventsData] = await Promise.all([
            api('/api/stats', { silent: true }),
            api('/api/events?limit=20', { silent: true }),
        ]);
        state.stats = statsData.stats;
        document.getElementById('stats-row').innerHTML = [
            statCard(state.stats.identities || 0, 'Identities'),
            statCard(state.stats.accounts || 0, 'Accounts'),
            statCard(state.stats.recent_events || 0, 'Events (24h)'),
        ].join('');
        renderAlerts(statsData.alerts || []);
        renderEventFeed('recent-events', eventsData.events, 'No activity yet. Add some accounts and run a check.');
    }

    function renderAlerts(alerts) {
        const el = document.getElementById('alerts-bar');
        if (!alerts || alerts.length === 0) { el.innerHTML = ''; return; }
        el.innerHTML = alerts.map(a => {
            const isIgAuth = a.platform === 'instagram' && /session|expired|login|unauthorized/i.test(a.error);
            return `
                <div class="alert-item">
                    <div class="alert-icon">&#9888;</div>
                    <div class="alert-body">
                        <div class="alert-title">${platformIcon(a.platform)} @${esc(a.username)} <span class="text-muted">&middot; ${esc(a.identity_name)}</span></div>
                        <div class="alert-message">${esc(a.error)}</div>
                    </div>
                    ${isIgAuth ? `<button class="btn btn-ghost btn-sm alert-fix-btn" onclick="App.fixIgSession(this, ${a.account_id})">Fix Session</button>` : ''}
                    <div class="alert-count">${a.error_count}x</div>
                </div>
            `;
        }).join('');
    }

    function statCard(value, label) {
        return `<div class="stat-card"><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`;
    }

    // ---- Events ----
    function renderEventFeed(containerId, events, emptyMsg) {
        const el = document.getElementById(containerId);
        if (!events || events.length === 0) {
            el.innerHTML = `<div class="empty-state"><p>${esc(emptyMsg)}</p></div>`;
            return;
        }
        el.innerHTML = events.map(e => `
            <div class="event-row" onclick="App.showEvent(${e.id})" title="Click for details">
                <div class="event-platform">${platformIcon(e.platform)}</div>
                <div class="event-body">
                    <div class="event-top">
                        <div>
                            <span class="event-who">@${esc(e.username)}</span>
                            ${e.identity_name ? `<span class="event-identity-name">&middot; ${esc(e.identity_name)}</span>` : ''}
                        </div>
                        <span class="event-when">${timeAgo(e.created_at)}</span>
                    </div>
                    <div class="event-summary">${esc(e.summary)}</div>
                    <div class="event-type-badge">${eventTypeLabel(e.event_type)}</div>
                </div>
            </div>
        `).join('');
    }

    function eventTypeLabel(type) {
        const labels = {
            follower_change: 'followers', following_change: 'following',
            bio_change: 'bio', new_post: 'post', name_change: 'name',
            privacy_change: 'privacy', new_pins: 'pins', new_board: 'board',
            board_update: 'board', new_follower: 'follower', lost_follower: 'follower',
            new_following: 'following', unfollowed: 'unfollow',
            new_playlist: 'playlist', removed_playlist: 'playlist',
            session_expired: 'error', auth_failed: 'error',
        };
        return labels[type] || type;
    }

    async function showEvent(eventId) {
        const data = await api(`/api/events/${eventId}`);
        const e = data.event;
        const parsed = e.event_data_parsed;

        let detailHtml = `
            <div class="event-detail-header">
                <div class="event-platform-lg">${platformIcon(e.platform)}</div>
                <div>
                    <div class="event-detail-who">@${esc(e.username)}</div>
                    <div class="event-detail-meta">${esc(e.platform)} &middot; ${esc(e.identity_name)} &middot; ${timeAgo(e.created_at)}</div>
                </div>
            </div>
            <div class="event-detail-summary">${esc(e.summary)}</div>
        `;

        if (parsed) {
            detailHtml += '<div class="event-detail-data">';
            if (parsed.old_bio !== undefined && parsed.new_bio !== undefined) {
                detailHtml += `
                    <div class="diff-block">
                        <div class="diff-label">Before</div>
                        <div class="diff-content diff-old">${esc(parsed.old_bio || '(empty)')}</div>
                    </div>
                    <div class="diff-block">
                        <div class="diff-label">After</div>
                        <div class="diff-content diff-new">${esc(parsed.new_bio || '(empty)')}</div>
                    </div>
                `;
            } else if (parsed.names) {
                detailHtml += `<div class="diff-block"><div class="diff-label">Users</div><div class="diff-content">${parsed.names.map(n => esc(n)).join(', ')}</div></div>`;
            } else if (parsed.old !== undefined && parsed.new !== undefined) {
                const isIgFollower = e.platform === 'instagram' && (e.event_type === 'follower_change' || e.event_type === 'following_change');
                detailHtml += `
                    <div class="diff-inline">
                        <span class="diff-old">${esc(String(parsed.old))}</span>
                        <span class="diff-arrow">&rarr;</span>
                        <span class="diff-new">${esc(String(parsed.new))}</span>
                    </div>
                    ${isIgFollower ? '<div class="diff-hint">instagram only exposes the count, not individual names. tracking who specifically followed/unfollowed is not possible without scraping, which gets flagged. <span class="diff-hint-icon" title="instagram\'s api doesn\'t return follower lists reliably. the count is all we can track.">?</span></div>' : ''}
                `;
            } else {
                detailHtml += `<pre class="diff-raw">${esc(JSON.stringify(parsed, null, 2))}</pre>`;
            }
            detailHtml += '</div>';
        }

        document.getElementById('event-detail-content').innerHTML = detailHtml;
        openModal('modal-event');
    }

    async function loadActivity() {
        const platform = document.getElementById('activity-platform-filter').value;
        const url = `/api/events?limit=${PAGE_SIZE}&offset=${state.activityOffset}` +
                    (platform ? `&platform=${platform}` : '');
        const data = await api(url, { silent: true });
        state.activityTotal = data.total || 0;
        renderEventFeed('activity-feed', data.events, 'No activity recorded yet.');
        renderPagination();
    }

    function renderPagination() {
        const el = document.getElementById('activity-pagination');
        if (state.activityTotal <= PAGE_SIZE) { el.innerHTML = ''; return; }
        const page = Math.floor(state.activityOffset / PAGE_SIZE) + 1;
        const total = Math.ceil(state.activityTotal / PAGE_SIZE);
        el.innerHTML = `
            <button class="btn btn-ghost btn-sm" ${page <= 1 ? 'disabled' : ''} onclick="App.activityPage(${page - 1})">Prev</button>
            <span class="page-info">${page} / ${total}</span>
            <button class="btn btn-ghost btn-sm" ${page >= total ? 'disabled' : ''} onclick="App.activityPage(${page + 1})">Next</button>
        `;
    }

    function activityPage(page) {
        state.activityOffset = (page - 1) * PAGE_SIZE;
        loadActivity();
    }

    // ---- Identities ----
    async function loadIdentities() {
        const data = await api('/api/identities', { silent: true });
        state.identities = data.identities;
        const el = document.getElementById('identities-grid');
        if (state.identities.length === 0) {
            el.innerHTML = `<div class="empty-state full-width"><p>No identities yet. Create one to start monitoring.</p><button class="btn btn-primary" onclick="App.showAddIdentity()" style="margin-top:12px">+ New Identity</button></div>`;
            return;
        }
        el.innerHTML = state.identities.map(i => {
            const latest = i.latest_event;
            const ago = latest ? timeAgo(latest.created_at) : null;
            const hasErrors = i.accounts.some(a => a.error_count > 0);
            return `
                <div class="identity-card" onclick="App.showDetail(${i.id})">
                    <div class="identity-top">
                        <div>
                            <div class="identity-name">${esc(i.name)}${hasErrors ? ' <span class="health-dot error" title="Some accounts have errors"></span>' : ''}</div>
                            ${i.notes ? `<div class="identity-notes">${esc(i.notes)}</div>` : ''}
                        </div>
                        <div class="identity-actions" onclick="event.stopPropagation()">
                            <button class="btn-icon" onclick="App.editIdentity(${i.id})" title="Edit">&#9998;</button>
                            <button class="btn-icon" onclick="App.deleteIdentity(${i.id})" title="Delete">&times;</button>
                        </div>
                    </div>
                    <div class="accounts-list">
                        ${i.accounts.length === 0 ? '<span class="text-muted text-sm">No accounts linked</span>' :
                            i.accounts.map(a => `
                                <span class="account-chip">
                                    <span class="platform-dot ${a.platform}"></span>
                                    ${esc(a.username)}
                                    ${a.error_count > 0 ? '<span class="chip-error" title="' + esc(a.last_error || 'Error') + '">!</span>' : ''}
                                </span>
                            `).join('')}
                    </div>
                    <div class="identity-footer">
                        ${ago ? `<div>Last activity: ${ago}</div><div class="activity-line">${esc(latest.summary)}</div>` : '<span class="text-muted">No activity yet</span>'}
                    </div>
                </div>
            `;
        }).join('');
    }

    // ---- Identity Detail ----
    async function showDetail(id) {
        state.detailId = id;
        const data = await api(`/api/identities/${id}`);
        const ident = data.identity;
        const eventsData = await api(`/api/events?identity_id=${id}&limit=50`, { silent: true });

        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById('view-identity-detail').classList.add('active');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

        document.getElementById('identity-detail-actions').innerHTML = `
            <button class="btn btn-ghost btn-sm" onclick="App.editIdentity(${id})">Edit</button>
            <button class="btn btn-primary btn-sm" onclick="App.showAddAccount(${id})">+ Add Account</button>
        `;

        document.getElementById('identity-detail-content').innerHTML = `
            <div class="detail-header">
                <div>
                    <div class="detail-name">${esc(ident.name)}</div>
                    ${ident.notes ? `<div class="detail-notes">${esc(ident.notes)}</div>` : ''}
                </div>
            </div>
            <div class="detail-accounts">
                ${ident.accounts.map(a => `
                    <div class="detail-account-card ${a.error_count > 0 ? 'has-error' : ''}">
                        <div class="detail-account-info">
                            <div class="detail-account-platform">${platformIcon(a.platform)}</div>
                            <div>
                                <div class="detail-account-name">@${esc(a.username)}</div>
                                <div class="detail-account-plat">
                                    ${esc(a.platform)}${a.last_checked ? ` &middot; ${timeAgo(a.last_checked)}` : ''}
                                    ${a.error_count > 0 ? `<span class="error-badge" title="${esc(a.last_error || '')}">${a.error_count} error${a.error_count > 1 ? 's' : ''}</span>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="detail-account-actions">
                            <button class="btn-icon" onclick="App.checkAccount(${a.id})" title="Check now">&#8635;</button>
                            <button class="btn-icon" onclick="App.removeAccount(${a.id}, ${id})" title="Remove">&times;</button>
                        </div>
                    </div>
                `).join('') || '<div class="text-muted full-width">No accounts. Add one to start monitoring.</div>'}
            </div>
            <div class="panel">
                <div class="panel-header"><h2>Activity Timeline</h2></div>
                <div id="detail-events" class="event-feed"></div>
            </div>
        `;

        renderEventFeed('detail-events', eventsData.events, 'No events for this identity yet.');
    }

    // ---- CRUD ----
    function showAddIdentity() {
        document.getElementById('identity-edit-id').value = '';
        document.getElementById('identity-name').value = '';
        document.getElementById('identity-notes').value = '';
        document.getElementById('modal-identity-title').textContent = 'New Identity';
        openModal('modal-identity');
    }

    function editIdentity(id) {
        const ident = state.identities.find(i => i.id === id);
        if (!ident) return;
        document.getElementById('identity-edit-id').value = id;
        document.getElementById('identity-name').value = ident.name;
        document.getElementById('identity-notes').value = ident.notes || '';
        document.getElementById('modal-identity-title').textContent = 'Edit Identity';
        openModal('modal-identity');
    }

    async function saveIdentity(e) {
        e.preventDefault();
        const id = document.getElementById('identity-edit-id').value;
        const name = document.getElementById('identity-name').value.trim();
        const notes = document.getElementById('identity-notes').value.trim();
        if (id) {
            await api(`/api/identities/${id}`, { method: 'PUT', body: JSON.stringify({ name, notes }) });
        } else {
            await api('/api/identities', { method: 'POST', body: JSON.stringify({ name, notes }) });
        }
        closeModal('modal-identity');
        await loadIdentities();
        loadDashboard();
        if (state.detailId == id) showDetail(id);
    }

    async function deleteIdentity(id) {
        if (!confirm('Delete this identity and all its accounts?')) return;
        await api(`/api/identities/${id}`, { method: 'DELETE' });
        await loadIdentities();
        loadDashboard();
    }

    // ---- Accounts ----
    function showAddAccount(identityId) {
        document.getElementById('account-identity-id').value = identityId;
        document.getElementById('account-username').value = '';
        document.getElementById('account-platform').value = '';
        document.getElementById('account-sp-dc').value = '';
        document.getElementById('account-ig-session').value = '';
        document.getElementById('spotify-config-field').style.display = 'none';
        document.getElementById('instagram-config-field').style.display = 'none';
        document.querySelectorAll('.platform-opt').forEach(b => b.classList.remove('selected'));
        openModal('modal-account');
    }

    function pickPlatform(platform) {
        document.getElementById('account-platform').value = platform;
        document.querySelectorAll('.platform-opt').forEach(b =>
            b.classList.toggle('selected', b.dataset.platform === platform)
        );
        document.getElementById('spotify-config-field').style.display = platform === 'spotify' ? '' : 'none';
        document.getElementById('instagram-config-field').style.display = platform === 'instagram' ? '' : 'none';
    }

    async function saveAccount(e) {
        e.preventDefault();
        const identityId = document.getElementById('account-identity-id').value;
        const platform = document.getElementById('account-platform').value;
        const username = document.getElementById('account-username').value.trim();
        if (!platform) { toast('Select a platform', true); return; }

        const body = { platform, username };
        if (platform === 'spotify') {
            const spdc = document.getElementById('account-sp-dc').value.trim();
            if (spdc) body.config = { sp_dc: spdc };
        }
        if (platform === 'instagram') {
            const igSession = document.getElementById('account-ig-session').value.trim();
            if (igSession) body.config = { session_username: igSession };
        }

        await api(`/api/identities/${identityId}/accounts`, { method: 'POST', body: JSON.stringify(body) });
        closeModal('modal-account');
        toast(`Added @${username} on ${platform}`);
        if (state.detailId == identityId) showDetail(identityId);
        loadIdentities();
        loadDashboard();
    }

    async function removeAccount(accountId, identityId) {
        if (!confirm('Remove this account?')) return;
        await api(`/api/accounts/${accountId}`, { method: 'DELETE' });
        if (state.detailId == identityId) showDetail(identityId);
        loadIdentities();
    }

    async function checkAccount(accountId) {
        toast('Check started...');
        await api(`/api/check/${accountId}`, { method: 'POST' });
    }

    async function checkAll() {
        toast('Checking all accounts...');
        await api('/api/check-all', { method: 'POST' });
    }

    // ---- Maigret Search ----
    async function searchMaigret(e) {
        e.preventDefault();
        const username = document.getElementById('search-username').value.trim();
        if (!username) return;

        const btn = document.getElementById('search-btn');
        btn.disabled = true;
        btn.textContent = 'Searching...';
        startProgress();

        try {
            const data = await api('/api/maigret/search', {
                method: 'POST',
                body: JSON.stringify({
                    username,
                    top_sites: parseInt(document.getElementById('search-scope').value),
                    timeout: parseInt(document.getElementById('search-timeout').value),
                    max_connections: parseInt(document.getElementById('search-max-conn').value),
                    tags: document.getElementById('search-tags').value,
                    all_sites: document.getElementById('search-all-sites').checked,
                    include_disabled: document.getElementById('search-disabled').checked,
                    use_cookies: document.getElementById('search-cookies').checked,
                }),
            });
            state.searchResults = data;
            renderSearchResults();
        } catch (err) {
            document.getElementById('search-results').innerHTML =
                `<div class="empty-state"><p>${esc(err.message)}</p></div>`;
        } finally {
            stopProgress();
            btn.disabled = false;
            btn.textContent = 'Search';
        }
    }

    function renderSearchResults() {
        const el = document.getElementById('search-results');
        const r = state.searchResults;
        if (!r) { el.innerHTML = ''; return; }
        const { username, stats, found } = r;
        const dur = stats.duration_ms < 60000
            ? `${(stats.duration_ms / 1000).toFixed(1)}s`
            : `${Math.floor(stats.duration_ms / 60000)}m ${Math.round((stats.duration_ms % 60000) / 1000)}s`;

        if (!found || found.length === 0) {
            el.innerHTML = `<div class="search-summary"><h3>@${esc(username)}</h3><div class="meta">Checked ${stats.checked_sites} sites in ${dur}. No profiles found.</div></div>`;
            return;
        }

        const linkable = new Set(['instagram', 'pinterest', 'spotify']);

        el.innerHTML = `
            <div class="search-summary">
                <h3>@${esc(username)}</h3>
                <div class="meta">Found ${found.length} profiles across ${stats.checked_sites} sites in ${dur}</div>
            </div>
            <div class="results-grid">
                ${found.map(f => {
                    const siteLower = f.site_name.toLowerCase();
                    const canLink = linkable.has(siteLower);
                    return `
                        <div class="result-card">
                            <div class="result-head">
                                <span class="result-site">${esc(f.site_name)}</span>
                                <div class="result-actions">
                                    ${canLink ? `<button class="btn btn-ghost btn-xs" onclick="App.showLinkResult('${siteLower}', '${esc(username)}')">+ Link</button>` : ''}
                                    ${f.url ? `<a class="result-link" href="${esc(f.url)}" target="_blank" rel="noopener">Open</a>` : ''}
                                </div>
                            </div>
                            ${f.url ? `<div class="result-url">${esc(f.url)}</div>` : ''}
                            ${f.tags && f.tags.length ? `<div class="result-tags">${f.tags.map(t => `<span>${esc(t)}</span>`).join('')}</div>` : ''}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    // ---- Link search result to identity ----
    async function showLinkResult(platform, username) {
        // Load identities for the select
        if (state.identities.length === 0) {
            const data = await api('/api/identities', { silent: true });
            state.identities = data.identities;
        }
        const select = document.getElementById('link-identity-select');
        if (state.identities.length === 0) {
            toast('Create an identity first', true);
            return;
        }
        select.innerHTML = state.identities.map(i =>
            `<option value="${i.id}">${esc(i.name)}</option>`
        ).join('');
        document.getElementById('link-platform').value = platform;
        document.getElementById('link-username').value = username;
        openModal('modal-link');
    }

    async function confirmLink() {
        const identityId = document.getElementById('link-identity-select').value;
        const platform = document.getElementById('link-platform').value;
        const username = document.getElementById('link-username').value;

        try {
            await api('/api/maigret/link', {
                method: 'POST',
                body: JSON.stringify({ identity_id: parseInt(identityId), platform, username }),
            });
            closeModal('modal-link');
            toast(`Linked @${username} to identity`);
            loadIdentities();
        } catch (e) {
            // error already toasted by api()
        }
    }

    // ---- Settings ----
    async function loadSettings() {
        const data = await api('/api/settings', { silent: true });
        const s = data.settings;
        document.getElementById('setting-check-interval').value = s.check_interval || 300;
        document.getElementById('setting-instagram-session').value = s.instagram_session || '';
        document.getElementById('setting-sp-dc-cookie').value = s.sp_dc_cookie || '';
        document.getElementById('setting-discord-webhook').value = s.discord_webhook || '';
        document.getElementById('setting-ntfy-topic').value = s.ntfy_topic || '';
        document.getElementById('setting-ntfy-server').value = s.ntfy_server || 'https://ntfy.sh';
        document.getElementById('setting-notifications-enabled').checked = s.notifications_enabled !== 'false';

        const igUser = s.instagram_session || 'USERNAME';
        document.getElementById('ig-cmd-text').textContent = `instaloader --login ${igUser}`;

        const info = data.info;
        document.getElementById('settings-info').innerHTML = [
            infoRow('Host', `${info.host}:${info.port}`),
            infoRow('Debug', info.debug ? 'On' : 'Off'),
            infoRow('Database', info.database.split('/').pop()),
            infoRow('Interval', `${s.check_interval}s`),
        ].join('');
    }

    function infoRow(key, val) {
        return `<div class="info-row"><span class="info-key">${esc(key)}</span><span class="info-val">${esc(val)}</span></div>`;
    }

    async function saveSettings() {
        await api('/api/settings', {
            method: 'PUT',
            body: JSON.stringify({
                check_interval: document.getElementById('setting-check-interval').value,
                instagram_session: document.getElementById('setting-instagram-session').value.trim(),
                sp_dc_cookie: document.getElementById('setting-sp-dc-cookie').value.trim(),
                discord_webhook: document.getElementById('setting-discord-webhook').value.trim(),
                ntfy_topic: document.getElementById('setting-ntfy-topic').value.trim(),
                ntfy_server: document.getElementById('setting-ntfy-server').value.trim() || 'https://ntfy.sh',
                notifications_enabled: document.getElementById('setting-notifications-enabled').checked ? 'true' : 'false',
            }),
        });
        toast('Settings saved');
        loadSettings();
    }

    async function testNotification() {
        const btn = document.getElementById('test-notif-btn');
        btn.disabled = true;
        btn.textContent = 'Sending...';
        try {
            const data = await api('/api/settings/test-notification', { method: 'POST' });
            const r = data.results;
            const parts = [];
            if (r.discord === true) parts.push('Discord: sent');
            else if (r.discord === false) parts.push('Discord: failed');
            if (r.ntfy === true) parts.push('ntfy: sent');
            else if (r.ntfy === false) parts.push('ntfy: failed');
            toast(parts.length ? parts.join(', ') : 'No notification channels configured');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Test Notification';
        }
    }

    async function checkIgStatus() {
        const btn = document.getElementById('check-ig-status-btn');
        const status = document.getElementById('ig-status-text');
        btn.disabled = true;
        btn.textContent = 'Checking...';
        status.textContent = '';
        try {
            const data = await api('/api/settings/ig-status', { silent: true });
            if (data.status === 'valid') {
                status.textContent = `@${data.username} — valid`;
                status.style.color = 'var(--green)';
            } else if (data.status === 'expired') {
                status.textContent = `@${data.username} — expired`;
                status.style.color = 'var(--red)';
            } else {
                status.textContent = data.message;
                status.style.color = 'var(--orange)';
            }
        } catch (e) {
            status.textContent = e.message;
            status.style.color = 'var(--red)';
        } finally {
            btn.disabled = false;
            btn.textContent = 'Check Login Status';
        }
    }

    async function fixIgSession(btn, accountId) {
        btn.disabled = true;
        btn.textContent = 'Checking...';
        let fixed = false;
        for (const browser of ['chrome', 'firefox']) {
            try {
                const data = await api('/api/settings/import-ig-session', {
                    method: 'POST', body: JSON.stringify({ browser }), silent: true,
                });
                if (data.success) {
                    toast(`Session reimported from ${browser}${data.username ? ` for @${data.username}` : ''}`);
                    fixed = true;
                    if (accountId) {
                        await api(`/api/check/${accountId}`, { method: 'POST', silent: true });
                        toast('Recheck triggered');
                    }
                    setTimeout(loadDashboard, 5000);
                    break;
                }
            } catch (e) { /* try next browser */ }
        }
        if (!fixed) {
            toast('No valid Instagram session found in Chrome or Firefox. Log into instagram.com first.', true);
            btn.disabled = false;
            btn.textContent = 'Fix Session';
            return;
        }
        btn.textContent = 'Fixed';
    }

    async function importIgSession(browser) {
        const btn = document.getElementById(`import-${browser}-btn`);
        const status = document.getElementById('ig-import-status');
        if (btn) { btn.disabled = true; btn.textContent = 'Importing...'; }
        if (status) status.textContent = `Extracting from ${browser}...`;
        try {
            const data = await api('/api/settings/import-ig-session', {
                method: 'POST',
                body: JSON.stringify({ browser }),
            });
            if (data.success) {
                if (data.needs_username) {
                    toast(`Session imported! Enter your IG username below.`);
                    if (status) status.textContent = `Session saved. Enter your Instagram username in the field above.`;
                } else {
                    toast(`Session imported for @${data.username}`);
                    if (status) status.textContent = `Imported session for @${data.username}`;
                    const sessionInput = document.getElementById('setting-instagram-session');
                    if (sessionInput) sessionInput.value = data.username;
                    const modalInput = document.getElementById('account-ig-session');
                    if (modalInput) modalInput.value = data.username;
                }
            } else {
                toast(data.error, true);
                if (status) status.textContent = data.error;
            }
        } catch (e) {
            if (status) status.textContent = e.message;
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = `Import from ${browser.charAt(0).toUpperCase() + browser.slice(1)}`; }
        }
    }

    async function importSpotifyCookie(browser) {
        const btn = document.getElementById(`import-spotify-${browser}-btn`);
        const status = document.getElementById('spotify-import-status');
        if (btn) { btn.disabled = true; btn.textContent = 'Importing...'; }
        if (status) status.textContent = `Extracting from ${browser}...`;
        try {
            const data = await api('/api/settings/import-spotify-cookie', {
                method: 'POST',
                body: JSON.stringify({ browser }),
            });
            if (data.success) {
                toast('Spotify sp_dc cookie imported');
                if (status) status.textContent = 'Cookie imported successfully.';
                const input = document.getElementById('setting-sp-dc-cookie');
                if (input) input.value = data.sp_dc;
            } else {
                toast(data.error, true);
                if (status) status.textContent = data.error;
            }
        } catch (e) {
            if (status) status.textContent = e.message;
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = `Import from ${browser.charAt(0).toUpperCase() + browser.slice(1)}`; }
        }
    }

    function copyCmd(elementId) {
        const text = document.getElementById(elementId).textContent;
        navigator.clipboard.writeText(text).then(() => toast('Copied'));
    }

    // ---- Progress ----
    function startProgress() {
        const wrap = document.getElementById('search-progress');
        const bar = document.getElementById('search-progress-bar');
        const label = document.getElementById('search-progress-text');
        wrap.classList.add('active');
        label.textContent = 'Searching...';
        let p = 5;
        bar.style.width = `${p}%`;
        if (progressTimer) clearInterval(progressTimer);
        progressTimer = setInterval(() => {
            p = Math.min(p + Math.random() * 8 + 3, 92);
            bar.style.width = `${p}%`;
        }, 600);
    }

    function stopProgress() {
        const wrap = document.getElementById('search-progress');
        const bar = document.getElementById('search-progress-bar');
        const label = document.getElementById('search-progress-text');
        if (progressTimer) { clearInterval(progressTimer); progressTimer = null; }
        bar.style.width = '100%';
        label.textContent = 'Done';
        setTimeout(() => { wrap.classList.remove('active'); bar.style.width = '0%'; }, 500);
    }

    // ---- Modal helpers ----
    function openModal(id) { document.getElementById(id).classList.add('active'); }
    function closeModal(id) { document.getElementById(id).classList.remove('active'); }
    function closeModalOverlay(e, id) {
        if (e.target === e.currentTarget) closeModal(id);
    }

    // ---- Toast ----
    function toast(msg, isError = false) {
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();
        const el = document.createElement('div');
        el.className = `toast${isError ? ' error' : ''}`;
        el.textContent = msg;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 3000);
    }

    // ---- Utils ----
    function platformIcon(name) {
        const icons = { instagram: '\ud83d\udcf7', pinterest: '\ud83d\udccc', spotify: '\ud83c\udfb5' };
        return icons[name] || '\ud83d\udcf1';
    }

    function timeAgo(ts) {
        if (!ts) return '?';
        const utc = ts.endsWith('Z') || ts.includes('+') ? ts : ts.replace(' ', 'T') + 'Z';
        const s = Math.floor((Date.now() - new Date(utc).getTime()) / 1000);
        if (s < 0) return 'just now';
        if (s < 60) return 'just now';
        const m = Math.floor(s / 60);
        if (m < 60) return `${m}m ago`;
        const h = Math.floor(m / 60);
        if (h < 24) return `${h}h ago`;
        const d = Math.floor(h / 24);
        if (d < 7) return `${d}d ago`;
        if (d < 30) return `${Math.floor(d / 7)}w ago`;
        return `${Math.floor(d / 30)}mo ago`;
    }

    function esc(text) {
        if (text === null || text === undefined) return '';
        const d = document.createElement('div');
        d.textContent = String(text);
        return d.innerHTML;
    }

    return {
        navigate, loadActivity, activityPage, showDetail, showAddIdentity, editIdentity,
        saveIdentity, deleteIdentity, showAddAccount, pickPlatform,
        saveAccount, removeAccount, checkAccount, checkAll,
        searchMaigret, showEvent, showLinkResult, confirmLink,
        closeModal, closeModalOverlay, openModal,
        loadSettings, saveSettings, testNotification,
        checkIgStatus, fixIgSession, importIgSession, importSpotifyCookie, copyCmd,
    };
})();
