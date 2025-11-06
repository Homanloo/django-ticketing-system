// API Configuration
const API_BASE_URL = window.location.origin + '/api/v1';
const USER_API_BASE_URL = API_BASE_URL + '/users';

// State Management
let accessToken = localStorage.getItem('accessToken') || null;
let currentUser = JSON.parse(localStorage.getItem('currentUser')) || null;
let currentTickets = [];
let currentTicketDetail = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    if (accessToken && currentUser) {
        showDashboard();
        loadTickets();
    } else {
        showLogin();
    }
}

// Page Navigation
function showLogin() {
    hideAllPages();
    document.getElementById('login-page').classList.remove('hidden');
}

function showRegister() {
    hideAllPages();
    document.getElementById('register-page').classList.remove('hidden');
}

function showDashboard() {
    hideAllPages();
    document.getElementById('dashboard-page').classList.remove('hidden');
    if (currentUser) {
        document.getElementById('user-name').textContent = `Hi, ${currentUser.username}`;
    }
}

function hideAllPages() {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.add('hidden');
    });
}

// Event Listeners
function setupEventListeners() {
    // Auth Forms
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Auth Navigation
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        showRegister();
    });
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        showLogin();
    });
    
    // Tickets
    document.getElementById('create-ticket-btn').addEventListener('click', () => {
        loadUserOrders();
        document.getElementById('create-ticket-modal').classList.remove('hidden');
    });
    document.getElementById('close-create-modal').addEventListener('click', () => {
        document.getElementById('create-ticket-modal').classList.add('hidden');
        document.getElementById('create-ticket-form').reset();
    });
    document.getElementById('cancel-create').addEventListener('click', () => {
        document.getElementById('create-ticket-modal').classList.add('hidden');
        document.getElementById('create-ticket-form').reset();
    });
    document.getElementById('create-ticket-form').addEventListener('submit', handleCreateTicket);
    
    // Ticket Detail Modal
    document.getElementById('close-detail-modal').addEventListener('click', () => {
        document.getElementById('ticket-detail-modal').classList.add('hidden');
    });
    
    // Filters
    // document.getElementById('status-filter').addEventListener('change', loadTickets);
    // document.getElementById('priority-filter').addEventListener('change', loadTickets);
    
    // Close modals on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });
}

// API Helpers
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for cookies
    };
    
    if (accessToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {}),
        },
    };
    
    try {
        const response = await fetch(url, finalOptions);
        
        // Handle token refresh if unauthorized
        if (response.status === 401 && accessToken) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Retry the original request
                finalOptions.headers['Authorization'] = `Bearer ${accessToken}`;
                const retryResponse = await fetch(url, finalOptions);
                return handleResponse(retryResponse);
            } else {
                handleLogout();
                return null;
            }
        }
        
        return handleResponse(response);
    } catch (error) {
        console.error('API Request Error:', error);
        showAlert('Network error. Please try again.', 'error');
        return null;
    }
}

async function handleResponse(response) {
    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
        data = await response.json();
    } else {
        data = await response.text();
    }
    
    if (!response.ok) {
        throw new Error(JSON.stringify(data));
    }
    
    return data;
}

async function refreshAccessToken() {
    try {
        const response = await fetch(`${USER_API_BASE_URL}/auth/refresh/`, {
            method: 'POST',
            credentials: 'include',
        });
        
        if (response.ok) {
            const data = await response.json();
            accessToken = data.access;
            localStorage.setItem('accessToken', accessToken);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Token refresh error:', error);
        return false;
    }
}

// Authentication Handlers
async function handleLogin(e) {
    e.preventDefault();
    showLoading();
    
    const formData = {
        email: document.getElementById('login-email').value,
        password: document.getElementById('login-password').value,
    };
    
    try {
        const data = await apiRequest(`${USER_API_BASE_URL}/auth/login/`, {
            method: 'POST',
            body: JSON.stringify(formData),
        });
        
        if (data) {
            accessToken = data.access;
            currentUser = data.user;
            
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showAlert('Login successful!', 'success');
            showDashboard();
            loadTickets();
            document.getElementById('login-form').reset();
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Invalid email or password', 'error');
    } finally {
        hideLoading();
    }
}

async function handleRegister(e) {
    e.preventDefault();
    showLoading();
    
    const password = document.getElementById('register-password').value;
    const password2 = document.getElementById('register-password2').value;
    
    if (password !== password2) {
        showAlert('Passwords do not match', 'error');
        hideLoading();
        return;
    }
    
    const formData = {
        email: document.getElementById('register-email').value,
        password: password,
        password_confirmation: password2,
        first_name: document.getElementById('register-first-name').value,
        last_name: document.getElementById('register-last-name').value,
    };
    
    // Add username if provided (optional)
    const username = document.getElementById('register-username').value.trim();
    if (username) {
        formData.username = username;
    }
    
    try {
        const data = await apiRequest(`${USER_API_BASE_URL}/auth/register/`, {
            method: 'POST',
            body: JSON.stringify(formData),
        });
        
        if (data) {
            accessToken = data.access;
            currentUser = data.user;
            
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showAlert('Registration successful!', 'success');
            showDashboard();
            loadTickets();
            document.getElementById('register-form').reset();
        }
    } catch (error) {
        console.error('Registration error:', error);
        try {
            const errorData = JSON.parse(error.message);
            let errorMessage = 'Registration failed. ';
            
            if (errorData.username) {
                errorMessage += errorData.username[0];
            } else if (errorData.email) {
                errorMessage += errorData.email[0];
            } else if (errorData.password) {
                errorMessage += errorData.password[0];
            } else if (errorData.first_name) {
                errorMessage += 'First name is required.';
            } else if (errorData.last_name) {
                errorMessage += 'Last name is required.';
            } else {
                errorMessage += 'Please check your input.';
            }
            
            showAlert(errorMessage, 'error');
        } catch (e) {
            showAlert('Registration failed. Please try again.', 'error');
        }
    } finally {
        hideLoading();
    }
}

async function handleLogout() {
    showLoading();
    
    try {
        await apiRequest(`${USER_API_BASE_URL}/auth/logout/`, {
            method: 'POST',
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        accessToken = null;
        currentUser = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('currentUser');
        
        showAlert('Logged out successfully', 'info');
        showLogin();
        hideLoading();
    }
}

// Tickets Management
async function loadTickets() {
    showLoading();
    
    // const statusFilter = document.getElementById('status-filter').value;
    // const priorityFilter = document.getElementById('priority-filter').value;
    
    let url = `${API_BASE_URL}/my-tickets/`;
    const params = new URLSearchParams();
    
    // if (statusFilter) params.append('status', statusFilter);
    // if (priorityFilter) params.append('priority', priorityFilter);
    
    if (params.toString()) {
        url += `?${params.toString()}`;
    }
    
    try {
        const data = await apiRequest(url);
        
        if (data) {
            currentTickets = data;
            renderTickets(data);
        }
    } catch (error) {
        console.error('Load tickets error:', error);
        showAlert('Failed to load tickets', 'error');
    } finally {
        hideLoading();
    }
}

async function loadUserOrders() {
    try {
        const data = await apiRequest(`${API_BASE_URL}/my-orders/`);
        
        if (data) {
            const orderSelect = document.getElementById('ticket-order');
            // Clear existing options except the first one
            orderSelect.innerHTML = '<option value="">No specific order</option>';
            
            // Add user's orders to the dropdown
            data.forEach(order => {
                const option = document.createElement('option');
                option.value = order.id;
                option.textContent = `Order #${order.order_number} - ${order.status} (${formatDate(order.created_at)})`;
                orderSelect.appendChild(option);
            });
            
            if (data.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No orders available';
                option.disabled = true;
                orderSelect.appendChild(option);
            }
        }
    } catch (error) {
        console.error('Load orders error:', error);
        // Don't show error to user, just log it
    }
}

function renderTickets(tickets) {
    const ticketsList = document.getElementById('tickets-list');
    
    if (tickets.length === 0) {
        ticketsList.innerHTML = `
            <div class="empty-state">
                <h3>No tickets found</h3>
                <p>Create your first support ticket to get started.</p>
            </div>
        `;
        return;
    }
    
    ticketsList.innerHTML = tickets.map(ticket => `
        <div class="ticket-card" onclick="viewTicketDetail('${ticket.id}')">
            <div class="ticket-header">
                <div>
                    <div class="ticket-title">${escapeHtml(ticket.topic)}</div>
                </div>
                <div class="ticket-badges">
                    <span class="badge badge-status ${ticket.status}">${formatStatus(ticket.status)}</span>
                    <span class="badge badge-priority ${ticket.priority}">${ticket.priority}</span>
                </div>
            </div>
            <div class="ticket-description">
                ${escapeHtml(ticket.description)}
            </div>
            <div class="ticket-footer">
                <span>Created: ${formatDate(ticket.created_at)}</span>
                <span>Updated: ${formatDate(ticket.updated_at)}</span>
            </div>
        </div>
    `).join('');
}

async function handleCreateTicket(e) {
    e.preventDefault();
    showLoading();
    
    const formData = {
        topic: document.getElementById('ticket-topic').value,
        description: document.getElementById('ticket-description').value,
    };
    
    // Add order if selected
    const orderId = document.getElementById('ticket-order').value;
    if (orderId) {
        formData.order = orderId;
    }
    
    try {
        // Create ticket first
        const data = await apiRequest(`${API_BASE_URL}/tickets/`, {
            method: 'POST',
            body: JSON.stringify(formData),
        });
        
        if (data) {
            // Upload files if any were selected
            const fileInput = document.getElementById('ticket-files');
            if (fileInput.files.length > 0) {
                await uploadTicketFiles(data.id, fileInput.files);
            }
            
            showAlert('Ticket created successfully!', 'success');
            document.getElementById('create-ticket-modal').classList.add('hidden');
            document.getElementById('create-ticket-form').reset();
            document.getElementById('file-preview-list').innerHTML = '';
            loadTickets();
        }
    } catch (error) {
        console.error('Create ticket error:', error);
        showAlert('Failed to create ticket', 'error');
    } finally {
        hideLoading();
    }
}

async function uploadTicketFiles(ticketId, files) {
    const uploadPromises = [];
    
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        
        const promise = fetch(`${API_BASE_URL}/tickets/${ticketId}/attachments/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            },
            credentials: 'include',
            body: formData,
        });
        
        uploadPromises.push(promise);
    }
    
    try {
        await Promise.all(uploadPromises);
    } catch (error) {
        console.error('File upload error:', error);
        showAlert('Some files failed to upload', 'error');
    }
}

async function viewTicketDetail(ticketId) {
    showLoading();
    
    try {
        const ticket = await apiRequest(`${API_BASE_URL}/tickets/${ticketId}/`);
        const messages = await apiRequest(`${API_BASE_URL}/tickets/${ticketId}/messages/`);
        const activities = await apiRequest(`${API_BASE_URL}/tickets/${ticketId}/activities/`);
        const attachments = await apiRequest(`${API_BASE_URL}/tickets/${ticketId}/attachments/`);
        
        if (ticket && messages && activities && attachments) {
            currentTicketDetail = { ticket, messages, activities, attachments };
            renderTicketDetail();
            document.getElementById('ticket-detail-modal').classList.remove('hidden');
        }
    } catch (error) {
        console.error('View ticket detail error:', error);
        showAlert('Failed to load ticket details', 'error');
    } finally {
        hideLoading();
    }
}

function renderTicketDetail() {
    const { ticket, messages, activities, attachments } = currentTicketDetail;
    const content = document.getElementById('ticket-detail-content');
    
    content.innerHTML = `
        <div class="ticket-detail">
            <div class="ticket-detail-header">
                <h3 class="ticket-detail-title">${escapeHtml(ticket.topic)}</h3>
                <div class="ticket-detail-meta">
                    <span class="badge badge-status ${ticket.status}">${formatStatus(ticket.status)}</span>
                    <span class="badge badge-priority ${ticket.priority}">${ticket.priority}</span>
                </div>
                ${ticket.order ? `
                <div style="margin: 15px 0; padding: 12px; background-color: var(--background); border-radius: 8px; border-left: 3px solid var(--primary-color);">
                    <strong style="color: var(--text-primary);">Related Order:</strong>
                    <span style="color: var(--text-secondary);"> #${ticket.order.order_number} - ${ticket.order.status}</span>
                </div>
                ` : ''}
                <div class="ticket-detail-description">
                    <strong>Description:</strong><br>
                    ${escapeHtml(ticket.description)}
                </div>
                <div style="font-size: 13px; color: var(--text-secondary);">
                    Created: ${formatDateTime(ticket.created_at)} | 
                    Updated: ${formatDateTime(ticket.updated_at)}
                    ${ticket.resolved_at ? ` | Resolved: ${formatDateTime(ticket.resolved_at)}` : ''}
                </div>
            </div>
            
            <div class="ticket-detail-section">
                <h3>Messages</h3>
                <div class="messages-list">
                    ${messages.length > 0 ? messages.map(msg => `
                        <div class="message ${msg.is_staff_message ? 'staff-message' : ''}">
                            <div class="message-header">
                                <span class="message-author">
                                    ${msg.user_name}${msg.is_staff_message ? ' (Staff)' : ''}
                                </span>
                                <span class="message-time">${formatDateTime(msg.created_at)}</span>
                            </div>
                            <div class="message-content">${escapeHtml(msg.message)}</div>
                        </div>
                    `).join('') : '<p style="color: var(--text-secondary);">No messages yet.</p>'}
                </div>
                
                <form class="add-message-form" onsubmit="handleAddMessage(event, '${ticket.id}')">
                    <label for="new-message" style="font-weight: 600; margin-bottom: -10px;">Add a Message</label>
                    <textarea 
                        id="new-message" 
                        placeholder="Type your message here..." 
                        required
                        rows="5"
                    ></textarea>
                    <button type="submit" class="btn btn-primary">Send Message</button>
                </form>
            </div>
            
            <div class="ticket-detail-section">
                <h3>Attachments</h3>
                <div class="attachments-list">
                    ${attachments.length > 0 ? attachments.map(att => `
                        <div class="attachment-item">
                            <div class="attachment-info">
                                <span class="attachment-icon">📎</span>
                                <a href="${att.file_url}" target="_blank" class="attachment-name">${escapeHtml(att.filename)}</a>
                                <span class="attachment-size">(${formatFileSize(att.filesize)})</span>
                            </div>
                            <button class="btn-delete-attachment" onclick="deleteAttachment('${ticket.id}', '${att.id}')" title="Delete attachment">🗑️</button>
                        </div>
                    `).join('') : '<p style="color: var(--text-secondary);">No attachments yet.</p>'}
                </div>
                
                <div class="add-attachment-form">
                    <label for="new-attachment-${ticket.id}" style="font-weight: 600; margin-bottom: 10px; display: block;">Add Attachments</label>
                    <input type="file" id="new-attachment-${ticket.id}" multiple accept="*/*" style="margin-bottom: 10px;">
                    <button onclick="handleAddAttachments('${ticket.id}')" class="btn btn-primary">Upload Files</button>
                </div>
            </div>
            
            <div class="ticket-detail-section">
                <h3>Activity Log</h3>
                <div class="activities-list">
                    ${activities.length > 0 ? activities.map(activity => `
                        <div class="activity">
                            <div>${escapeHtml(activity.details)}</div>
                            <div class="activity-time">
                                by ${activity.performed_by_name} - ${formatDateTime(activity.created_at)}
                            </div>
                        </div>
                    `).join('') : '<p style="color: var(--text-secondary);">No activities yet.</p>'}
                </div>
            </div>
        </div>
    `;
}

async function handleAddMessage(e, ticketId) {
    e.preventDefault();
    showLoading();
    
    const messageInput = document.getElementById('new-message');
    const message = messageInput.value.trim();
    
    if (!message) {
        hideLoading();
        return;
    }
    
    try {
        const data = await apiRequest(`${API_BASE_URL}/tickets/${ticketId}/messages/`, {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
        
        if (data) {
            showAlert('Message sent successfully!', 'success');
            messageInput.value = '';
            // Reload ticket detail
            await viewTicketDetail(ticketId);
        }
    } catch (error) {
        console.error('Add message error:', error);
        showAlert('Failed to send message', 'error');
    } finally {
        hideLoading();
    }
}

// Utility Functions
function showLoading() {
    document.getElementById('loading-spinner').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-spinner').classList.add('hidden');
}

function showAlert(message, type = 'info') {
    const alert = document.getElementById('alert-message');
    alert.textContent = message;
    alert.className = `alert ${type}`;
    alert.classList.remove('hidden');
    
    setTimeout(() => {
        alert.classList.add('hidden');
    }, 4000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatStatus(status) {
    return status.replace('_', ' ').split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

async function handleAddAttachments(ticketId) {
    const fileInput = document.getElementById(`new-attachment-${ticketId}`);
    if (!fileInput.files || fileInput.files.length === 0) {
        showAlert('Please select files to upload', 'error');
        return;
    }
    
    showLoading();
    
    try {
        await uploadTicketFiles(ticketId, fileInput.files);
        showAlert('Files uploaded successfully!', 'success');
        // Reload ticket detail to show new attachments
        await viewTicketDetail(ticketId);
    } catch (error) {
        console.error('Upload attachment error:', error);
        showAlert('Failed to upload files', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteAttachment(ticketId, attachmentId) {
    if (!confirm('Are you sure you want to delete this attachment?')) {
        return;
    }
    
    showLoading();
    
    try {
        await fetch(`${API_BASE_URL}/tickets/${ticketId}/attachments/${attachmentId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            },
            credentials: 'include',
        });
        
        showAlert('Attachment deleted successfully!', 'success');
        // Reload ticket detail to reflect changes
        await viewTicketDetail(ticketId);
    } catch (error) {
        console.error('Delete attachment error:', error);
        showAlert('Failed to delete attachment', 'error');
    } finally {
        hideLoading();
    }
}

function formatFileSize(bytes) {
    if (!bytes) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

