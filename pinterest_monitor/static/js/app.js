let boards = [];
let users = [];
let chartInstance = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Load dark mode preference
    const darkMode = localStorage.getItem('darkMode') === 'true';
    if (darkMode) {
        document.documentElement.setAttribute('data-bs-theme', 'dark');
    }
    
    loadConfig();
    loadBoards();
    loadUsers();
    loadStats();
    
    // Auto-refresh every 30 seconds
    setInterval(loadBoards, 30000);
    setInterval(loadUsers, 30000);
    setInterval(loadStats, 30000);
    
    // Form handlers
    document.getElementById('addUserForm').addEventListener('submit', handleAddUser);
    document.getElementById('addBoardForm').addEventListener('submit', handleAddBoard);
});

// Load configuration
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        if (data.success && data.config) {
            document.getElementById('checkInterval').textContent = data.config.check_interval;
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Dark mode toggle
function toggleDarkMode() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('darkMode', newTheme === 'dark');
}

// Load all boards
async function loadBoards() {
    try {
        const response = await fetch('/api/boards');
        const data = await response.json();
        
        if (data.success) {
            boards = data.boards;
            document.getElementById('boardCount').textContent = boards.length;
            renderBoards();
        }
    } catch (error) {
        console.error('Error loading boards:', error);
    }
}

// Load all users
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const data = await response.json();
        
        if (data.success) {
            users = data.users;
            document.getElementById('profileCount').textContent = users.length;
            renderUsers();
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Load all boards
async function loadBoards() {
    try {
        const response = await fetch('/api/boards');
        const data = await response.json();
        
        if (data.success) {
            boards = data.boards;
            renderBoards();
        }
    } catch (error) {
        console.error('Error loading boards:', error);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            document.getElementById('stats').textContent = 
                `${stats.total_users} profiles • ${stats.total_boards} boards • ${stats.total_pins.toLocaleString()} pins`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Render user profiles
function renderUsers() {
    const container = document.getElementById('profilesList');
    
    if (users.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-person-x"></i>
                <h5>No profiles yet</h5>
                <p>Add a Pinterest user to start tracking their boards</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="p-3">';
    
    users.forEach(user => {
        const lastChecked = user.last_checked ? timeAgo(new Date(user.last_checked)) : 'Never';
        const lastUpdate = user.last_activity_time ? timeAgo(new Date(user.last_activity_time)) : 'No updates yet';
        const boardCount = user.board_count || 0;
        
        html += `
            <div class="board-card card mb-3">
                <div class="board-header">
                    <div>
                        <h5 class="mb-1">
                            <i class="bi bi-person-circle"></i> ${escapeHtml(user.display_name || user.username)}
                        </h5>
                        <small class="text-muted">@${escapeHtml(user.username)} • ${boardCount} board${boardCount !== 1 ? 's' : ''}</small>
                    </div>
                    <div class="board-actions">
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="board-body">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <small class="text-muted d-block">Last Update:</small>
                            <span class="last-pin">${lastUpdate}</span>
                        </div>
                        <div class="col-md-6 text-end">
                            <small class="text-muted d-block">Last Checked:</small>
                            <span class="time-ago">${lastChecked}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Render boards list
function renderBoards() {
    const container = document.getElementById('boardsList');
    
    if (boards.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <h5>No boards yet</h5>
                <p>Add a Pinterest user or board to start monitoring</p>
            </div>
        `;
        return;
    }
    
    // Group boards by username
    const boardsByUser = {};
    boards.forEach(board => {
        if (!boardsByUser[board.username]) {
            boardsByUser[board.username] = [];
        }
        boardsByUser[board.username].push(board);
    });
    
    let html = '<div class="p-3">';
    
    // Render each user's boards
    Object.keys(boardsByUser).sort().forEach((username, index) => {
        const userBoards = boardsByUser[username];
        const totalPins = userBoards.reduce((sum, b) => sum + b.current_pin_count, 0);
        const collapseId = `collapse-${username.replace(/[^a-z0-9]/gi, '-')}`;
        
        html += `
            <div class="user-section mb-4">
                <div class="user-section-header" onclick="toggleUserBoards('${collapseId}')" style="cursor: pointer;">
                    <div class="d-flex align-items-center justify-content-between">
                        <h6 class="mb-0">
                            <i class="bi bi-chevron-down collapse-arrow" id="arrow-${collapseId}" style="transition: transform 0.2s;"></i>
                            <i class="bi bi-person"></i> @${escapeHtml(username)}
                            <span class="badge bg-secondary ms-2">${userBoards.length} board${userBoards.length !== 1 ? 's' : ''}</span>
                            <span class="badge bg-info ms-1">${totalPins.toLocaleString()} pins</span>
                        </h6>
                    </div>
                </div>
                <div class="user-boards mt-2 collapse show" id="${collapseId}">
        `;
        
        userBoards.forEach(board => {
            const lastChecked = board.last_checked ? timeAgo(new Date(board.last_checked)) : 'Never';
            const lastPin = board.last_pin_time ? timeAgo(new Date(board.last_pin_time)) : 'No new pins detected';
            const pinCount = board.current_pin_count.toLocaleString();
            
            html += `
                <div class="board-card card mb-2">
                    <div class="board-header">
                        <div>
                            <h6 class="mb-1 board-name-text">
                                <a href="${board.url}" target="_blank" class="board-link">
                                    ${escapeHtml(board.name)}
                                    <i class="bi bi-box-arrow-up-right small"></i>
                                </a>
                            </h6>
                        </div>
                        <div class="board-actions">
                            <button class="btn btn-sm btn-outline-success" onclick="checkSingleBoard(${board.id})" title="Check this board now">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-primary" onclick="showBoardDetails(${board.id})">
                                <i class="bi bi-graph-up"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteBoard(${board.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="board-body">
                        <div class="row align-items-center">
                            <div class="col-md-3 text-center">
                                <div class="pin-count">${pinCount}</div>
                                <small class="text-muted">pins</small>
                            </div>
                            <div class="col-md-5">
                                <small class="text-muted d-block">Last Pin:</small>
                                <span class="last-pin">${lastPin}</span>
                            </div>
                            <div class="col-md-4 text-end">
                                <small class="text-muted d-block">Last Checked:</small>
                                <span class="time-ago">${lastChecked}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Toggle user boards collapse
function toggleUserBoards(collapseId) {
    const element = document.getElementById(collapseId);
    const arrow = document.getElementById(`arrow-${collapseId}`);
    
    if (element.classList.contains('show')) {
        element.classList.remove('show');
        arrow.style.transform = 'rotate(-90deg)';
    } else {
        element.classList.add('show');
        arrow.style.transform = 'rotate(0deg)';
    }
}

// Handle add user form
async function handleAddUser(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adding...';
    
    try {
        const response = await fetch('/api/add-user', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('username').value = '';
            loadBoards();
            loadUsers();
            loadStats();
        } else {
            showToast(data.error || 'Failed to add user', 'error');
        }
    } catch (error) {
        showToast('Error adding user: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Handle add board form
async function handleAddBoard(e) {
    e.preventDefault();
    
    const url = document.getElementById('boardUrl').value.trim();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Adding...';
    
    try {
        const response = await fetch('/api/add-board', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            document.getElementById('boardUrl').value = '';
            loadBoards();
            loadStats();
        } else {
            showToast(data.error || 'Failed to add board', 'error');
        }
    } catch (error) {
        showToast('Error adding board: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Delete board
async function deleteBoard(boardId) {
    if (!confirm('Are you sure you want to stop monitoring this board?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/board/${boardId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Board removed from monitoring', 'success');
            loadBoards();
            loadStats();
        } else {
            showToast(data.error || 'Failed to delete board', 'error');
        }
    } catch (error) {
        showToast('Error deleting board: ' + error.message, 'error');
    }
}

// Delete user
async function deleteUser(userId) {
    if (!confirm('Are you sure? This will also delete all boards for this user.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/user/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('User profile and boards removed', 'success');
            loadUsers();
            loadBoards();
            loadStats();
        } else {
            showToast(data.error || 'Failed to delete user', 'error');
        }
    } catch (error) {
        showToast('Error deleting user: ' + error.message, 'error');
    }
}

// Check single board
async function checkSingleBoard(boardId) {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
    
    try {
        const response = await fetch(`/api/board/${boardId}/check`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Board checked!', 'success');
            setTimeout(() => loadBoards(), 1000);
        } else {
            showToast(data.error || 'Check failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

// Show board details with history chart
async function showBoardDetails(boardId) {
    const board = boards.find(b => b.id === boardId);
    if (!board) return;
    
    document.getElementById('modalBoardName').textContent = board.name;
    
    try {
        const response = await fetch(`/api/board/${boardId}/history`);
        const data = await response.json();
        
        if (data.success && data.history.length > 0) {
            renderHistoryChart(data.history);
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('boardModal'));
    modal.show();
}

// Render history chart
function renderHistoryChart(history) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    
    // Destroy existing chart
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    // Reverse to show oldest to newest
    const reversed = [...history].reverse();
    
    const labels = reversed.map(h => new Date(h.checked_at).toLocaleDateString());
    const data = reversed.map(h => h.pin_count);
    
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Pin Count',
                data: data,
                borderColor: '#e60023',
                backgroundColor: 'rgba(230, 0, 35, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

// Manual check
async function checkNow() {
    const btn = event.target.closest('button');
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Checking...';
    
    try {
        const response = await fetch('/api/check-now', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('All boards checked!', 'success');
            loadBoards();
            loadUsers();
            loadStats();
        } else {
            showToast(data.error || 'Check failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('toast');
    const toastBody = document.getElementById('toastMessage');
    
    toastBody.textContent = message;
    toastEl.className = `toast ${type === 'error' ? 'bg-danger text-white' : ''}`;
    
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Time ago helper
function timeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    const intervals = {
        year: 31536000,
        month: 2592000,
        week: 604800,
        day: 86400,
        hour: 3600,
        minute: 60
    };
    
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / secondsInUnit);
        if (interval >= 1) {
            return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
        }
    }
    
    return 'Just now';
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
