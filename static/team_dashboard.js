const API_BASE = '/api';

// State Management
const state = {
    currentProjectId: null,
    teamMembers: [],
    members: {}, // Member ID to member object mapping
    projects: {},
    loading: false,
    searchQuery: '',
    statusFilter: 'all',
    memberSearchQuery: '',
    teamMemberSearchQuery: ''
};

// UI Notification System
const notifications = {
    show(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-circle',
            info: 'info'
        };

        toast.innerHTML = `
            <i data-lucide="${icons[type]}" class="h-5 w-5 mr-3 flex-shrink-0"></i>
            <span class="flex-1 font-medium">${message}</span>
            <button onclick="this.parentElement.remove()" class="ml-3 text-white/80 hover:text-white transition-colors">
                <i data-lucide="x" class="h-4 w-4"></i>
            </button>
        `;

        container.appendChild(toast);

        // Initialize Lucide icons for the new toast
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('removing');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }

        return toast;
    },

    success(message, duration) {
        return this.show(message, 'success', duration);
    },

    error(message, duration) {
        return this.show(message, 'error', duration);
    },

    warning(message, duration) {
        return this.show(message, 'warning', duration);
    },

    info(message, duration) {
        return this.show(message, 'info', duration);
    }
};

// Tech Stack Polling System
const techStackPolling = {
    activePolls: new Map(), // taskId -> { intervalId, attempts }
    maxAttempts: 20, // Poll for up to 20 attempts (about 1 minute)
    pollInterval: 3000, // Check every 3 seconds

    startPolling(taskId) {
        // Don't start if already polling
        if (this.activePolls.has(taskId)) {
            return;
        }

        console.log('Starting tech stack polling for task:', taskId);
        let attempts = 0;

        const intervalId = setInterval(async () => {
            attempts++;

            try {
                // Reload projects to get latest data
                await loadProjects();

                // Find the task
                let task = null;
                for (const projectId in state.projects) {
                    const project = state.projects[projectId];
                    task = project.tasks.find(t => t.id === taskId);
                    if (task) break;
                }

                // Check if tech stack has been generated
                if (task && task.techStack && task.techStack.techStack && task.techStack.techStack.length > 0) {
                    console.log('Tech stack found for task:', taskId);
                    notifications.success('Tech stack has been auto-generated! ✨');
                    renderAll();
                    this.stopPolling(taskId);
                } else if (attempts >= this.maxAttempts) {
                    console.log('Tech stack polling timeout for task:', taskId);
                    this.stopPolling(taskId);
                }
            } catch (error) {
                console.error('Error during tech stack polling:', error);
                this.stopPolling(taskId);
            }
        }, this.pollInterval);

        this.activePolls.set(taskId, { intervalId, attempts });
    },

    stopPolling(taskId) {
        const poll = this.activePolls.get(taskId);
        if (poll) {
            clearInterval(poll.intervalId);
            this.activePolls.delete(taskId);
            console.log('Stopped polling for task:', taskId);
        }
    },

    stopAll() {
        for (const [taskId, poll] of this.activePolls.entries()) {
            clearInterval(poll.intervalId);
        }
        this.activePolls.clear();
    }
};

// Confirmation Modal System
const confirmation = {
    show(options) {
        return new Promise((resolve) => {
            const modal = document.getElementById('confirmation-modal');
            const title = document.getElementById('confirmation-title');
            const message = document.getElementById('confirmation-message');
            const confirmBtn = document.getElementById('confirmation-confirm-btn');
            const cancelBtn = document.getElementById('confirmation-cancel-btn');
            const confirmBtnText = document.getElementById('confirm-btn-text');
            const confirmBtnSpinner = document.getElementById('confirm-btn-spinner');

            // Set content
            title.textContent = options.title || 'Confirm Action';
            message.textContent = options.message || 'Are you sure you want to proceed?';
            confirmBtnText.textContent = options.confirmText || 'Confirm';

            // Set button colors based on type
            confirmBtn.className = 'w-full inline-flex justify-center items-center rounded-lg border border-transparent shadow-sm px-4 py-2.5 text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 sm:w-auto sm:text-sm transition-all';
            if (options.type === 'danger') {
                confirmBtn.className += ' bg-red-600 hover:bg-red-700 focus:ring-red-500';
            } else {
                confirmBtn.className += ' bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';
            }

            // Show modal
            modal.classList.remove('hidden');

            // Initialize Lucide icons
            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                lucide.createIcons();
            }

            const cleanup = () => {
                modal.classList.add('hidden');
                confirmBtn.onclick = null;
                cancelBtn.onclick = null;
                confirmBtnSpinner.classList.add('hidden');
                confirmBtnText.classList.remove('hidden');
                confirmBtn.disabled = false;
                cancelBtn.disabled = false;
            };

            confirmBtn.onclick = async () => {
                if (options.onConfirm) {
                    // Show loading state
                    confirmBtnText.classList.add('hidden');
                    confirmBtnSpinner.classList.remove('hidden');
                    confirmBtn.disabled = true;
                    cancelBtn.disabled = true;

                    try {
                        await options.onConfirm();
                        cleanup();
                        resolve(true);
                    } catch (error) {
                        console.error('Confirmation action failed:', error);
                        confirmBtnText.classList.remove('hidden');
                        confirmBtnSpinner.classList.add('hidden');
                        confirmBtn.disabled = false;
                        cancelBtn.disabled = false;
                    }
                } else {
                    cleanup();
                    resolve(true);
                }
            };

            cancelBtn.onclick = () => {
                cleanup();
                resolve(false);
            };

            // Close on backdrop click
            modal.onclick = (e) => {
                if (e.target === modal) {
                    cleanup();
                    resolve(false);
                }
            };
        });
    }
};

// API Functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

async function loadTeamMembers() {
    return await apiCall('/team-members');
}

async function loadProjects() {
    return await apiCall('/projects');
}

async function saveTask(task) {
    return await apiCall('/tasks', {
        method: 'POST',
        body: JSON.stringify(task)
    });
}

async function deleteTask(taskId) {
    return await apiCall(`/tasks/${taskId}`, { method: 'DELETE' });
}

async function assignTask(taskId, assignedTo) {
    return await apiCall(`/tasks/${taskId}/assign`, {
        method: 'PUT',
        body: JSON.stringify({ assignedTo })
    });
}

async function saveProject(project) {
    return await apiCall('/projects', {
        method: 'POST',
        body: JSON.stringify(project)
    });
}

async function deleteProject(projectId) {
    return await apiCall(`/projects/${projectId}`, { method: 'DELETE' });
}

async function saveMember(member) {
    return await apiCall('/team-members', {
        method: 'POST',
        body: JSON.stringify(member)
    });
}

async function deleteMember(memberId) {
    return await apiCall(`/team-members/${memberId}`, { method: 'DELETE' });
}

async function initializeDatabase() {
    return await apiCall('/init-db', { method: 'POST' });
}

async function assignMemberToProject(projectId, memberId) {
    return await apiCall(`/projects/${projectId}/members`, {
        method: 'POST',
        body: JSON.stringify({ memberId })
    });
}

async function removeMemberFromProject(projectId, memberId) {
    return await apiCall(`/projects/${projectId}/members/${memberId}`, {
        method: 'DELETE'
    });
}

async function getProjectMembers(projectId) {
    return await apiCall(`/projects/${projectId}/members`);
}

async function syncMindmap() {
    try {
        await apiCall('/sync-mindmap', { method: 'POST' });
    } catch (error) {
        console.error('Failed to sync mindmap:', error);
    }
}

// Utility Functions
const getPriorityClasses = (priority) => {
    switch (priority) {
        case 'high': return 'bg-rose-500/20 text-rose-300 border border-rose-500/30';
        case 'medium': return 'bg-amber-500/20 text-amber-300 border border-amber-500/30';
        case 'low': return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        default: return 'bg-slate-700/50 text-slate-300 border border-slate-600/50';
    }
};

const getProjectTagColor = (color) => {
    switch (color) {
        case 'yellow': return 'bg-amber-500/20 text-amber-300 border border-amber-500/30';
        case 'green': return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        case 'blue': return 'bg-blue-500/20 text-blue-300 border border-blue-500/30';
        case 'red': return 'bg-rose-500/20 text-rose-300 border border-rose-500/30';
        case 'purple': return 'bg-purple-500/20 text-purple-300 border border-purple-500/30';
        default: return 'bg-slate-700/50 text-slate-300 border border-slate-600/50';
    }
};

const getStatusBadge = (status) => {
    switch (status) {
        case 'ongoing': return '<span class="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">Ongoing</span>';
        case 'completed': return '<span class="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded-full">Completed</span>';
        case 'archived': return '<span class="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">Archived</span>';
        default: return '';
    }
};

function filterProjects() {
    const projectsList = Object.values(state.projects);
    return projectsList.filter(project => {
        const matchesSearch = project.name.toLowerCase().includes(state.searchQuery.toLowerCase());
        const matchesStatus = state.statusFilter === 'all' || project.status === state.statusFilter;
        return matchesSearch && matchesStatus;
    });
}

// Rendering Functions
async function renderAll() {
    if (state.loading) return;
    state.loading = true;

    try {
        await renderSidebar();
        await renderMemberDirectory();
        await renderStatsCards();
        await renderTeamCards();
        await renderProjectBacklog();
        updateMainHeader();

        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }

        // Add drag listeners AFTER lucide icons are created
        addDragAndDropListeners();
    } finally {
        state.loading = false;
    }
}

async function renderSidebar() {
    const projectsList = filterProjects();

    const createLink = (project, isMobile = false) => {
        const isActive = project.id === state.currentProjectId;
        const activeClass = isActive ? 'text-white bg-blue-600' : 'text-gray-300 hover:text-white hover:bg-gray-700';
        const textClass = isMobile ? 'text-base' : 'text-sm';

        return `
            <a href="#" 
               class="group flex items-center justify-between px-2 py-2 ${textClass} font-medium rounded-md ${activeClass} project-link" 
               data-project-id="${project.id}"
               aria-current="${isActive ? 'page' : 'false'}">
                <span class="truncate">${project.name}</span>
                <div class="flex items-center gap-2">
                    ${getStatusBadge(project.status)}
                    <button class="delete-project-btn opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300" data-project-id="${project.id}" onclick="deleteProjectConfirm(event, '${project.id}')">
                        <i data-lucide="trash-2" class="h-4 w-4"></i>
                    </button>
                </div>
            </a>
        `;
    };

    const staticLinks = (isMobile = false) => {
        const textClass = isMobile ? 'text-base' : 'text-sm';
        const iconClass = isMobile ? 'mr-4 h-6 w-6' : 'mr-3 h-5 w-5';
        return `
            <a href="/" class="dashboard-link group flex items-center px-2 py-2 ${textClass} font-medium text-white bg-blue-600 rounded-md">
                <i data-lucide="layout-dashboard" class="${iconClass} text-white"></i>
                Team Dashboard
            </a>
            <a href="/mindmap" class="mindmap-link group flex items-center px-2 py-2 ${textClass} font-medium text-gray-300 rounded-md hover:text-white hover:bg-gray-700">
                <i data-lucide="git-branch" class="${iconClass} text-gray-400 group-hover:text-gray-300"></i>
                Project Mindmap
            </a>
            <a href="/onboarding" class="onboarding-link group flex items-center px-2 py-2 ${textClass} font-medium text-gray-300 rounded-md hover:text-white hover:bg-gray-700">
                <i data-lucide="rocket" class="${iconClass} text-gray-400 group-hover:text-gray-300"></i>
                Onboarding
            </a>
            <div class="mt-6">
                <div class="flex items-center justify-between px-2 mb-2">
                    <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Projects
                    </h3>
                    <button onclick="openProjectModal()" class="text-gray-400 hover:text-gray-300">
                        <i data-lucide="plus-circle" class="h-4 w-4"></i>
                    </button>
                </div>
                <div class="mt-2 space-y-1" role="list">
                    ${projectsList.map(p => createLink(p, isMobile)).join('')}
                </div>
            </div>
        `;
    };

    document.getElementById('desktop-project-menu').innerHTML = staticLinks(false);
    document.getElementById('mobile-project-menu').innerHTML = staticLinks(true);

    document.querySelectorAll('.project-link').forEach(link => {
        link.addEventListener('click', async (e) => {
            if (e.target.closest('.delete-project-btn')) return;
            e.preventDefault();
            state.currentProjectId = link.dataset.projectId;
            await renderAll();
            document.getElementById('mobile-sidebar').classList.add('hidden');
        });
    });
}

async function renderStatsCards() {
    const container = document.getElementById('stats-cards-container');
    const project = state.projects[state.currentProjectId];

    if (!project) {
        container.innerHTML = '<p class="col-span-4 text-center text-slate-400">Select a project to view stats</p>';
        return;
    }

    const tasks = project.tasks || [];
    const tasksInProgress = tasks.filter(t => t.assignedTo).length;
    const tasksInBacklog = tasks.filter(t => !t.assignedTo).length;
    const teamMembersOnProject = project.teamMembers ? project.teamMembers.length : 0;

    container.innerHTML = `
        <div class="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur-sm overflow-hidden shadow-lg rounded-xl border border-slate-700/50 cursor-pointer hover:border-emerald-500/50 hover:shadow-emerald-500/10 transition-all">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20"><i data-lucide="users" class="h-6 w-6 text-white"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dt class="text-sm font-medium text-slate-400 truncate">Team Members on Project</dt>
                        <dd class="text-3xl font-bold text-white">${teamMembersOnProject}</dd>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur-sm overflow-hidden shadow-lg rounded-xl border border-slate-700/50 cursor-pointer hover:border-emerald-500/50 hover:shadow-emerald-500/10 transition-all">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-12 w-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-500/20"><i data-lucide="folder-kanban" class="h-6 w-6 text-white"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dt class="text-sm font-medium text-slate-400 truncate">Total Project Tasks</dt>
                        <dd class="text-3xl font-bold text-white">${tasks.length}</dd>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur-sm overflow-hidden shadow-lg rounded-xl border border-slate-700/50 cursor-pointer hover:border-emerald-500/50 hover:shadow-emerald-500/10 transition-all">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-12 w-12 rounded-xl bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/20"><i data-lucide="check-circle" class="h-6 w-6 text-white"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dt class="text-sm font-medium text-slate-400 truncate">Tasks In-Progress</dt>
                        <dd class="text-3xl font-bold text-white">${tasksInProgress}</dd>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-gradient-to-br from-slate-800/80 to-slate-800/50 backdrop-blur-sm overflow-hidden shadow-lg rounded-xl border border-slate-700/50 cursor-pointer hover:border-emerald-500/50 hover:shadow-emerald-500/10 transition-all">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-12 w-12 rounded-xl bg-gradient-to-br from-rose-500 to-rose-600 flex items-center justify-center shadow-lg shadow-rose-500/20"><i data-lucide="list" class="h-6 w-6 text-white"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-slate-400 truncate">Unassigned Tasks</dt>
                            <dd class="text-3xl font-bold text-white">${tasksInBacklog}</dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function renderMemberDirectory() {
    const container = document.getElementById('member-directory-list');
    const countBadge = document.getElementById('member-count-badge');

    if (!container) return;

    const filteredMembers = state.teamMembers.filter(member => {
        const query = state.memberSearchQuery.toLowerCase();
        return member.name.toLowerCase().includes(query) ||
            member.role.toLowerCase().includes(query);
    });

    countBadge.textContent = `${filteredMembers.length} ${filteredMembers.length !== 1 ? 'members' : 'member'}`;

    if (filteredMembers.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-400 italic text-center py-4">No members found</p>';
        return;
    }

    container.innerHTML = '';

    filteredMembers.forEach(member => {
        const project = state.projects[state.currentProjectId];
        const isAssigned = project && project.teamMembers && project.teamMembers.includes(member.id);

        const card = document.createElement('div');
        card.className = 'flex items-center justify-between p-3 bg-gradient-to-r from-slate-800/60 to-slate-800/40 backdrop-blur-sm border border-slate-700/50 rounded-xl hover:border-emerald-500/50 hover:shadow-lg hover:shadow-emerald-500/10 transition-all member-card cursor-move';
        card.draggable = true;
        card.dataset.memberId = member.id;
        card.title = 'Drag to assign to a project';

        card.innerHTML = `
            <div class="flex items-center space-x-3 flex-1 min-w-0">
                <img class="w-10 h-10 rounded-full flex-shrink-0 ring-2 ring-slate-700" 
                     src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" 
                     alt="${member.name}">
                <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-semibold text-slate-100 truncate editable-field" contenteditable="true" data-member-id="${member.id}" data-field="name">${member.name}</h4>
                    <p class="text-xs text-slate-400 truncate editable-field" contenteditable="true" data-member-id="${member.id}" data-field="role">${member.role}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2 flex-shrink-0">
                ${isAssigned ?
                `<span class="text-xs px-2.5 py-1 bg-emerald-500/20 text-emerald-300 rounded-full font-medium border border-emerald-500/30">In Project</span>` :
                `<span class="text-xs px-2.5 py-1 bg-slate-700/50 text-slate-400 rounded-full font-medium border border-slate-600/50">Available</span>`
            }
                <button class="delete-member-btn text-rose-400 hover:text-rose-300 p-1.5 hover:bg-rose-500/10 rounded-lg transition-colors" onclick="deleteMemberConfirm(event, '${member.id}')">
                    <i data-lucide="trash-2" class="h-3.5 w-3.5"></i>
                </button>
            </div>
        `;

        container.appendChild(card);

        // Add event listeners for editable fields
        card.querySelectorAll('.editable-field[contenteditable="true"]').forEach(field => {
            field.addEventListener('blur', async () => {
                const memberId = field.dataset.memberId;
                const fieldName = field.dataset.field;
                const newValue = field.textContent.trim();

                const memberToUpdate = state.teamMembers.find(m => m.id === memberId);
                if (memberToUpdate && memberToUpdate[fieldName] !== newValue) {
                    memberToUpdate[fieldName] = newValue;
                    state.members[memberId] = memberToUpdate;
                    await saveMember(memberToUpdate);
                    notifications.success(`${fieldName === 'name' ? 'Name' : 'Role'} updated successfully`);
                }
            });

            // Prevent drag when editing
            field.addEventListener('mousedown', (e) => {
                e.stopPropagation();
            });
        });
    });

    // Re-render icons
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
}

async function renderTeamCards() {
    const container = document.getElementById('team-cards-container');
    container.innerHTML = '';

    const project = state.projects[state.currentProjectId];
    if (!project) return;

    // Only show members assigned to the current project
    const projectMembers = state.teamMembers.filter(member =>
        project.teamMembers && project.teamMembers.includes(member.id)
    );

    projectMembers.forEach(member => {
        const assignedTask = project.tasks.find(task => task.assignedTo === member.id);

        const card = document.createElement('li');
        card.className = 'col-span-1 bg-gradient-to-br from-slate-800/70 to-slate-800/50 backdrop-blur-sm rounded-xl shadow-lg border border-slate-700/50 divide-y divide-slate-700/50 group member-card cursor-move hover:border-emerald-500/50 hover:shadow-emerald-500/10 transition-all';
        card.dataset.teamId = member.id;
        card.draggable = true;
        card.dataset.memberId = member.id;
        card.title = 'Drag to assign to a project';

        card.innerHTML = `
            <div class="w-full flex items-center justify-between p-5 space-x-6">
                <div class="flex-1 truncate">
                    <div class="flex items-center space-x-3">
                        <h3 class="text-slate-100 text-sm font-bold truncate editable-field" contenteditable="true" data-member-id="${member.id}" data-field="name">${member.name}</h3>
                        <span class="flex-shrink-0 inline-block px-2.5 py-1 text-xs font-semibold bg-slate-700/50 text-slate-300 rounded-full editable-field border border-slate-600/50" contenteditable="true" data-member-id="${member.id}" data-field="role">
                            ${member.role}
                        </span>
                    </div>
                    <p class="mt-1 text-slate-400 text-sm truncate">Core Platform</p>
                </div>
                <div class="flex items-center gap-2">
                    <img class="w-12 h-12 rounded-full flex-shrink-0 ring-2 ring-slate-700" src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" alt="${member.name}">
                    <button class="delete-member-btn opacity-0 group-hover:opacity-100 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg p-1.5 transition-all" onclick="removeMemberFromTeam('${member.id}')">
                        <i data-lucide="trash-2" class="h-4 w-4"></i>
                    </button>
                </div>
            </div>
            <div class="p-5 bg-slate-800/30 overflow-y-auto" style="max-height: 500px; min-height: 180px;">
                ${assignedTask ?
                renderTaskOnCard(assignedTask) :
                `<div class="flex items-center justify-center h-full">
                        <p class="text-sm text-slate-400 italic">No task assigned for this project.</p>
                     </div>`
            }
            </div>
        `;
        container.appendChild(card);

        // Add event listeners for editable fields
        card.querySelectorAll('.editable-field[contenteditable="true"]').forEach(field => {
            field.addEventListener('blur', async () => {
                const memberId = field.dataset.memberId;
                const fieldName = field.dataset.field;
                const newValue = field.textContent.trim();

                const memberToUpdate = state.teamMembers.find(m => m.id === memberId);
                if (memberToUpdate) {
                    memberToUpdate[fieldName] = newValue;
                    await saveMember(memberToUpdate);
                }
            });
        });

        // Ensure assigned task is draggable
        const assignedTaskCard = card.querySelector('.task-card-assigned');
        if (assignedTaskCard) {
            assignedTaskCard.draggable = true;
            assignedTaskCard.addEventListener('dragstart', handleDragStart);
            assignedTaskCard.addEventListener('dragend', handleDragEnd);
        }
    });
}

function renderTaskOnCard(task) {
    const priorityClass = getPriorityClasses(task.priority);
    const hasTechStack = task.techStack && task.techStack.techStack && task.techStack.techStack.length > 0;

    // Add badge indicator on task header
    const techStackBadge = hasTechStack
        ? '<span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" title="Tech stack suggestions available">✨ AI</span>'
        : '';

    let techStackHtml = '';
    if (hasTechStack) {
        const topTech = task.techStack.techStack.slice(0, 3);
        techStackHtml = `
            <div class="mt-3 pt-3 border-t border-slate-600/30 ml-6">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center">
                        <i data-lucide="code" class="mr-1.5 h-3.5 w-3.5 text-emerald-500"></i>
                        Suggested Tech Stack
                    </h4>
                    <button class="text-xs text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1" onclick="generateTechStack(event, '${task.id}')" title="Regenerate tech stack suggestions">
                        <i data-lucide="refresh-cw" class="h-3 w-3"></i>
                        Regenerate
                    </button>
                </div>
                <div class="flex flex-wrap gap-1.5">
                    ${topTech.map(tech => `
                        <span class="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-md" title="${tech.purpose}">
                            ${tech.name}
                        </span>
                    `).join('')}
                    ${task.techStack.techStack.length > 3 ? `<span class="text-xs text-slate-400">+${task.techStack.techStack.length - 3} more</span>` : ''}
                </div>
                <button class="mt-2 text-xs text-emerald-400 hover:text-emerald-300 transition-colors" onclick="showTechStackModal(event, '${task.id}')">
                    View Details →
                </button>
            </div>
        `;
    } else {
        techStackHtml = `
            <div class="mt-3 pt-3 border-t border-slate-600/30 ml-6">
                <div class="flex items-center justify-center">
                    <div class="spinner mr-2" style="border-color: rgba(16, 185, 129, 0.3); border-top-color: rgb(16, 185, 129); width: 1rem; height: 1rem;"></div>
                    <p class="text-xs text-emerald-400 italic">Generating tech stack suggestions...</p>
                </div>
            </div>
        `;
    }

    return `
        <div class="task-card-assigned relative group p-4 bg-slate-700/30 rounded-lg border border-slate-600/30 hover:border-emerald-500/30 transition-all cursor-move" draggable="true" data-task-id="${task.id}" data-project-id="${task.projectId}" title="Drag to move task back to backlog or to another team member">
            <div class="absolute top-2 left-2 opacity-0 group-hover:opacity-100 text-slate-500 transition-all pointer-events-none">
                <i data-lucide="grip-vertical" class="h-4 w-4"></i>
            </div>
            <button class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg p-1.5 transition-all" onclick="deleteTaskConfirm(event, '${task.id}')">
                <i data-lucide="trash-2" class="h-4 w-4"></i>
            </button>
            <div class="flex items-center ml-6">
                <h4 class="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Current Task</h4>
                ${techStackBadge}
            </div>
            <p class="mt-2 text-sm text-slate-100 font-semibold editable-field ml-6" contenteditable="true" data-task-id="${task.id}" data-field="title">${task.title}</p>
            
            <div class="mt-4 flex justify-between items-start gap-4 ml-6">
                <div class="flex-1">
                    <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Priority</h4>
                    <select class="text-xs font-semibold px-3 py-1.5 rounded-full border-0 ${priorityClass} cursor-pointer hover:opacity-80 transition-opacity" data-task-id="${task.id}" data-field="priority">
                        <option value="low" ${task.priority === 'low' ? 'selected' : ''}>Low</option>
                        <option value="medium" ${task.priority === 'medium' ? 'selected' : ''}>Medium</option>
                        <option value="high" ${task.priority === 'high' ? 'selected' : ''}>High</option>
                    </select>
                </div>
                <div class="flex-1 text-right">
                    <h4 class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-end mb-2">
                        <i data-lucide="calendar" class="mr-1.5 h-3.5 w-3.5 text-slate-500"></i>
                        Deadline
                    </h4>
                    <p class="text-sm text-slate-100 font-semibold editable-field" contenteditable="true" data-task-id="${task.id}" data-field="deadline">${task.deadline}</p>
                </div>
            </div>
            ${techStackHtml}
        </div>
    `;
}

async function renderProjectBacklog() {
    const project = state.projects[state.currentProjectId];

    if (!project) {
        document.getElementById('project-backlog-title').textContent = 'Select a project';
        document.getElementById('project-backlog-list').innerHTML = '';
        return;
    }

    const backlogTasks = project.tasks.filter(task => task.assignedTo === null);

    const titleEl = document.getElementById('project-backlog-title');
    titleEl.textContent = `${project.name} Tasks`;
    titleEl.dataset.projectId = project.id;

    const list = document.getElementById('project-backlog-list');
    list.innerHTML = '';

    if (backlogTasks.length === 0) {
        list.innerHTML = `<li class="text-sm text-slate-400 italic text-center mt-4">No unassigned tasks!</li>`;
        return;
    }

    backlogTasks.forEach(task => {
        const priorityClass = getPriorityClasses(task.priority);
        const taskCard = document.createElement('li');
        taskCard.className = 'p-4 bg-gradient-to-r from-slate-800/60 to-slate-800/40 backdrop-blur-sm rounded-xl border border-slate-700/50 shadow-lg hover:border-emerald-500/50 hover:shadow-emerald-500/10 cursor-grab active:cursor-grabbing relative group transition-all';
        taskCard.draggable = true;
        taskCard.dataset.taskId = task.id;
        taskCard.dataset.projectId = project.id;

        taskCard.innerHTML = `
            <button class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-lg p-1.5 transition-all" onclick="deleteTaskConfirm(event, '${task.id}')">
                <i data-lucide="trash-2" class="h-4 w-4"></i>
            </button>
            <p class="text-sm font-semibold text-slate-100 pr-10">${task.title}</p>
            <div class="mt-3 flex justify-between items-center">
                <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${priorityClass}">
                    ${task.priority}
                </span>
                <span class="text-xs font-medium text-slate-400 flex items-center">
                    <i data-lucide="calendar" class="mr-1.5 h-3.5 w-3.5 text-slate-500"></i>
                    ${task.deadline}
                </span>
            </div>
            <div class="mt-3 pt-3 border-t border-slate-700/30">
                <p class="text-xs text-slate-400 italic flex items-center justify-center">
                    <i data-lucide="sparkles" class="mr-1.5 h-3 w-3 text-emerald-500"></i>
                    Tech stack will be auto-generated when assigned
                </p>
            </div>
        `;
        list.appendChild(taskCard);
    });
}

function updateMainHeader() {
    const project = state.projects[state.currentProjectId];
    const title = project ? `Core Platform Team - ${project.name}` : 'Core Platform Team';
    document.getElementById('main-dashboard-title').textContent = title;
}

// Drag and Drop Functions
function addDragAndDropListeners() {
    // Task drag and drop
    const draggableItems = document.querySelectorAll('[draggable="true"]:not(.member-card)');
    draggableItems.forEach(item => {
        item.removeEventListener('dragstart', handleDragStart);
        item.removeEventListener('dragend', handleDragEnd);
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });

    // Member card drag and drop
    const memberCards = document.querySelectorAll('.member-card[draggable="true"]');
    memberCards.forEach(card => {
        card.removeEventListener('dragstart', handleMemberDragStart);
        card.removeEventListener('dragend', handleMemberDragEnd);
        card.addEventListener('dragstart', handleMemberDragStart);
        card.addEventListener('dragend', handleMemberDragEnd);
    });

    const teamCards = document.querySelectorAll('#team-cards-container > li');
    teamCards.forEach(card => {
        card.removeEventListener('dragover', handleDragOver);
        card.removeEventListener('dragleave', handleDragLeave);
        card.removeEventListener('drop', handleDropOnTeamCard);
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('dragleave', handleDragLeave);
        card.addEventListener('drop', handleDropOnTeamCard);
    });

    // Project cards as drop zones for members
    const projectLinks = document.querySelectorAll('.project-link');
    projectLinks.forEach(link => {
        link.removeEventListener('dragover', handleProjectDragOver);
        link.removeEventListener('dragleave', handleProjectDragLeave);
        link.removeEventListener('drop', handleMemberDropOnProject);
        link.addEventListener('dragover', handleProjectDragOver);
        link.addEventListener('dragleave', handleProjectDragLeave);
        link.addEventListener('drop', handleMemberDropOnProject);
    });

    const backlogDropzone = document.getElementById('project-backlog-dropzone');
    if (backlogDropzone) {
        backlogDropzone.removeEventListener('dragover', handleDragOverBacklog);
        backlogDropzone.removeEventListener('dragleave', handleDragLeaveBacklog);
        backlogDropzone.removeEventListener('drop', handleDropOnBacklog);
        backlogDropzone.addEventListener('dragover', handleDragOverBacklog);
        backlogDropzone.addEventListener('dragleave', handleDragLeaveBacklog);
        backlogDropzone.addEventListener('drop', handleDropOnBacklog);
    }

    // Add event listeners for task edits
    document.querySelectorAll('.editable-field[data-task-id]').forEach(field => {
        field.addEventListener('blur', async () => {
            const taskId = field.dataset.taskId;
            const fieldName = field.dataset.field;
            const newValue = field.textContent.trim();

            const project = state.projects[state.currentProjectId];
            const task = project.tasks.find(t => t.id === taskId);
            if (task) {
                task[fieldName] = newValue;
                await saveTask(task);
            }
        });
    });

    document.querySelectorAll('select[data-task-id]').forEach(select => {
        select.addEventListener('change', async (e) => {
            const taskId = select.dataset.taskId;
            const fieldName = select.dataset.field;
            const newValue = e.target.value;

            const project = state.projects[state.currentProjectId];
            const task = project.tasks.find(t => t.id === taskId);
            if (task) {
                task[fieldName] = newValue;
                await saveTask(task);
                await renderAll();
            }
        });
    });
}

function handleDragStart(e) {
    // Prevent drag if clicking on interactive elements
    if (e.target.tagName === 'BUTTON' ||
        e.target.tagName === 'SELECT' ||
        e.target.tagName === 'INPUT' ||
        e.target.classList.contains('editable-field') ||
        e.target.closest('button') ||
        e.target.closest('select')) {
        e.preventDefault();
        return;
    }

    // Get the task card element (could be e.target or a parent)
    const taskCard = e.target.closest('[data-task-id]') || e.target;

    taskCard.classList.add('task-card-dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', JSON.stringify({
        taskId: taskCard.dataset.taskId,
        projectId: taskCard.dataset.projectId
    }));
}

function handleDragEnd(e) {
    // Get the task card element
    const taskCard = e.target.closest('[data-task-id]') || e.target;
    taskCard.classList.remove('task-card-dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const dropTarget = e.target.closest('#team-cards-container > li');
    if (dropTarget) {
        dropTarget.classList.add('drop-zone-active');
    }
}

function handleDragLeave(e) {
    const dropTarget = e.target.closest('#team-cards-container > li');
    if (dropTarget) {
        dropTarget.classList.remove('drop-zone-active');
    }
}

async function handleDropOnTeamCard(e) {
    e.preventDefault();
    e.stopPropagation();

    const dropTarget = e.target.closest('#team-cards-container > li');
    dropTarget.classList.remove('drop-zone-active');

    const data = e.dataTransfer.getData('text/plain');
    if (!data) return;

    const { taskId, projectId } = JSON.parse(data);
    const teamId = dropTarget.dataset.teamId;

    const project = state.projects[projectId];
    const task = project.tasks.find(t => t.id === taskId);

    if (task) {
        const existingTask = project.tasks.find(t => t.assignedTo === teamId);
        if (existingTask) {
            await assignTask(existingTask.id, null);
            existingTask.assignedTo = null;
        }

        await assignTask(task.id, teamId);
        task.assignedTo = teamId;

        await renderAll();

        // Automatically generate tech stack if task doesn't have one
        if (!task.techStack || !task.techStack.techStack || task.techStack.techStack.length === 0) {
            notifications.info('🤖 AI is generating tech stack suggestions...', 3000);

            // Trigger tech stack generation immediately
            try {
                const response = await fetch(`${API_BASE}/tasks/${task.id}/suggest-tech-stack`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (response.ok) {
                    const result = await response.json();
                    notifications.success(`✨ Tech stack suggested by ${result.generatedBy}`, 4000);

                    // Reload and re-render to show the updated tech stack
                    await loadProjects();
                    await renderAll();
                } else {
                    throw new Error('Failed to generate tech stack');
                }
            } catch (error) {
                console.error('Failed to auto-generate tech stack:', error);
                notifications.warning('Tech stack generation failed. Click regenerate to try again.', 5000);
            }
        }

        // Sync with mindmap
        await syncMindmap();
    }
}

function handleDragOverBacklog(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const dropTarget = e.target.closest('#project-backlog-dropzone');
    if (dropTarget) {
        dropTarget.classList.add('backlog-drop-zone-active');
    }
}

function handleDragLeaveBacklog(e) {
    const dropTarget = e.target.closest('#project-backlog-dropzone');
    if (dropTarget) {
        dropTarget.classList.remove('backlog-drop-zone-active');
    }
}

async function handleDropOnBacklog(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropTarget = e.target.closest('#project-backlog-dropzone');
    dropTarget.classList.remove('backlog-drop-zone-active');

    const { taskId, projectId } = JSON.parse(e.dataTransfer.getData('text/plain'));

    const project = state.projects[projectId];
    const task = project.tasks.find(t => t.id === taskId);

    if (task && task.assignedTo) {
        await assignTask(task.id, null);
        task.assignedTo = null;
        await renderAll();

        // Sync with mindmap
        await syncMindmap();
    }
}

// Member drag and drop handlers
function handleMemberDragStart(e) {
    e.target.classList.add('opacity-50');
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('text/plain', JSON.stringify({
        memberId: e.target.dataset.memberId,
        type: 'member'
    }));
}

function handleMemberDragEnd(e) {
    e.target.classList.remove('opacity-50');
}

function handleProjectDragOver(e) {
    const data = e.dataTransfer.types.includes('text/plain');
    if (data) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        const dropTarget = e.target.closest('.project-link');
        if (dropTarget) {
            dropTarget.classList.add('bg-blue-100', 'ring-2', 'ring-blue-500');
        }
    }
}

function handleProjectDragLeave(e) {
    const dropTarget = e.target.closest('.project-link');
    if (dropTarget) {
        dropTarget.classList.remove('bg-blue-100', 'ring-2', 'ring-blue-500');
    }
}

async function handleMemberDropOnProject(e) {
    e.preventDefault();
    e.stopPropagation();

    const dropTarget = e.target.closest('.project-link');
    if (dropTarget) {
        dropTarget.classList.remove('bg-blue-100', 'ring-2', 'ring-blue-500');
    }

    try {
        const data = JSON.parse(e.dataTransfer.getData('text/plain'));

        // Only handle member drops
        if (data.type === 'member') {
            const projectId = dropTarget.dataset.projectId;
            const memberId = data.memberId;
            const member = state.members[memberId];
            const project = state.projects[projectId];

            if (!project) {
                notifications.error('Project not found');
                return;
            }

            // Check if member is already assigned
            if (project.teamMembers && project.teamMembers.includes(memberId)) {
                notifications.warning(`${member.name} is already assigned to ${project.name} `);
                return;
            }

            // Assign member to project
            await assignMemberToProject(projectId, memberId);

            if (!project.teamMembers) {
                project.teamMembers = [];
            }
            project.teamMembers.push(memberId);

            notifications.success(`${member.name} added to ${project.name} `);

            // Update UI if we're viewing this project
            if (state.currentProjectId === projectId) {
                await renderAll();
            } else {
                await renderSidebar();
            }

            // Sync with mindmap
            await syncMindmap();
        }
    } catch (error) {
        console.error('Drop failed:', error);
        notifications.error('Failed to add member to project');
    }
}

// Modal Functions
function openProjectModal() {
    document.getElementById('project-modal').classList.remove('hidden');
}

function openMemberModal() {
    document.getElementById('member-modal').classList.remove('hidden');
}

async function deleteProjectConfirm(event, projectId) {
    event.preventDefault();
    event.stopPropagation();

    if (confirm('Are you sure you want to delete this project? All associated tasks will be deleted.')) {
        await deleteProject(projectId);
        delete state.projects[projectId];

        // Select another project
        const remainingProjects = Object.keys(state.projects);
        state.currentProjectId = remainingProjects.length > 0 ? remainingProjects[0] : null;

        await renderAll();
    }
}

async function deleteMemberConfirm(event, memberId) {
    event.preventDefault();
    event.stopPropagation();

    const member = state.teamMembers.find(m => m.id === memberId);
    const confirmed = await confirmation.show({
        title: 'Remove Team Member',
        message: `Are you sure you want to remove ${member?.name || 'this member'} from the team ? This action cannot be undone.`,
        confirmText: 'Remove Member',
        type: 'danger',
        onConfirm: async () => {
            await deleteMember(memberId);
            state.teamMembers = state.teamMembers.filter(m => m.id !== memberId);
            delete state.members[memberId]; // Remove from members lookup
            notifications.success(`${member?.name || 'Member'} has been removed successfully`);
            await renderAll();
        }
    });
}

async function deleteTaskConfirm(event, taskId) {
    event.preventDefault();
    event.stopPropagation();

    const project = state.projects[state.currentProjectId];
    const task = project?.tasks.find(t => t.id === taskId);

    const confirmed = await confirmation.show({
        title: 'Delete Task',
        message: `Are you sure you want to delete "${task?.title || 'this task'}" ? This action cannot be undone.`,
        confirmText: 'Delete Task',
        type: 'danger',
        onConfirm: async () => {
            await deleteTask(taskId);
            project.tasks = project.tasks.filter(t => t.id !== taskId);
            notifications.success('Task deleted successfully');
            await renderAll();

            // Sync with mindmap
            await syncMindmap();
        }
    });
}

async function deleteProjectConfirm(event, projectId) {
    event.preventDefault();
    event.stopPropagation();

    const project = state.projects[projectId];

    const confirmed = await confirmation.show({
        title: 'Delete Project',
        message: `Are you sure you want to delete "${project?.name || 'this project'}" ? All associated tasks will be permanently deleted.This action cannot be undone.`,
        confirmText: 'Delete Project',
        type: 'danger',
        onConfirm: async () => {
            await deleteProject(projectId);
            delete state.projects[projectId];

            // Select another project if current one was deleted
            const remainingProjects = Object.keys(state.projects);
            if (remainingProjects.length > 0) {
                state.currentProjectId = remainingProjects[0];
            } else {
                state.currentProjectId = null;
            }

            notifications.success(`Project "${project?.name}" deleted successfully`);
            await renderAll();

            // Sync with mindmap
            await syncMindmap();
        }
    });
}

// Auto-generate tech stack for assigned tasks without one
async function autoGenerateMissingTechStacks() {
    const tasksNeedingTechStack = [];

    // Find all assigned tasks without tech stack
    for (const projectId in state.projects) {
        const project = state.projects[projectId];
        if (project.tasks) {
            project.tasks.forEach(task => {
                if (task.assignedTo && (!task.techStack || !task.techStack.techStack || task.techStack.techStack.length === 0)) {
                    tasksNeedingTechStack.push({ task, projectId });
                }
            });
        }
    }

    if (tasksNeedingTechStack.length === 0) {
        return;
    }

    console.log(`Auto-generating tech stack for ${tasksNeedingTechStack.length} assigned tasks...`);

    // Generate tech stack for each task (with a small delay between requests)
    for (let i = 0; i < tasksNeedingTechStack.length; i++) {
        const { task, projectId } = tasksNeedingTechStack[i];

        try {
            const response = await fetch(`${API_BASE}/tasks/${task.id}/suggest-tech-stack`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const result = await response.json();
                console.log(`✓ Tech stack generated for task ${task.id} by ${result.generatedBy}`);
            }

            // Small delay to avoid overwhelming the API
            if (i < tasksNeedingTechStack.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        } catch (error) {
            console.error(`Failed to generate tech stack for task ${task.id}:`, error);
        }
    }

    // Reload projects to show the new tech stacks
    if (tasksNeedingTechStack.length > 0) {
        await loadProjects();
        await renderAll();
        notifications.success(`✨ Tech stacks generated for ${tasksNeedingTechStack.length} task${tasksNeedingTechStack.length > 1 ? 's' : ''}`, 4000);
    }
}

// Initialize Application
async function initializeApp() {
    try {
        await initializeDatabase();

        const members = await loadTeamMembers();
        state.teamMembers = members;

        // Create a member lookup object for quick access by ID
        state.members = {};
        members.forEach(member => {
            state.members[member.id] = member;
        });

        const projects = await loadProjects();
        console.log('Loaded projects:', projects);
        projects.forEach(project => {
            // Log tech stack info for debugging
            if (project.tasks) {
                project.tasks.forEach(task => {
                    if (task.techStack) {
                        console.log(`Task ${task.id} has tech stack:`, task.techStack);
                    }
                });
            }
            state.projects[project.id] = project;
        });

        if (projects.length > 0 && !state.currentProjectId) {
            state.currentProjectId = projects[0].id;
        }

        await renderAll();

        // Auto-generate tech stack for assigned tasks that don't have one
        await autoGenerateMissingTechStacks();

        notifications.success('Dashboard loaded successfully', 2000);
    } catch (error) {
        console.error('Failed to initialize app:', error);
        notifications.error('Failed to load data. Please refresh the page.');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const dateEl = document.getElementById('today-date');
    if (dateEl) {
        const today = new Date();
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.textContent = today.toLocaleDateString('en-US', options);
    }

    // Search and filter
    const projectSearchEl = document.getElementById('project-search');
    if (projectSearchEl) {
        projectSearchEl.addEventListener('input', (e) => {
            state.searchQuery = e.target.value;
            renderSidebar();
        });
    }

    const statusFilterEl = document.getElementById('status-filter');
    if (statusFilterEl) {
        statusFilterEl.addEventListener('change', (e) => {
            state.statusFilter = e.target.value;
            renderSidebar();
        });
    }

    // Mobile sidebar toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileSidebar = document.getElementById('mobile-sidebar');
    const mobileMenuClose = document.getElementById('mobile-menu-close');
    const mobileSidebarOverlay = document.getElementById('mobile-sidebar-overlay');

    if (mobileMenuButton && mobileSidebar) {
        mobileMenuButton.addEventListener('click', () => {
            mobileSidebar.classList.remove('hidden');
        });
    }
    if (mobileMenuClose && mobileSidebar) {
        mobileMenuClose.addEventListener('click', () => {
            mobileSidebar.classList.add('hidden');
        });
    }
    if (mobileSidebarOverlay && mobileSidebar) {
        mobileSidebarOverlay.addEventListener('click', () => {
            mobileSidebar.classList.add('hidden');
        });
    }

    // Task Modal handling
    const addTaskButton = document.getElementById('add-task-button');
    const taskModal = document.getElementById('task-modal');
    const cancelTaskButton = document.getElementById('cancel-task-button');
    const createTaskButton = document.getElementById('create-task-button');

    if (addTaskButton && taskModal) {
        addTaskButton.addEventListener('click', () => {
            if (!state.currentProjectId) {
                notifications.warning('Please select a project first');
                return;
            }
            taskModal.classList.remove('hidden');
            const defaultDeadline = new Date();
            defaultDeadline.setDate(defaultDeadline.getDate() + 7);
            const taskDeadlineEl = document.getElementById('task-deadline');
            if (taskDeadlineEl) {
                taskDeadlineEl.valueAsDate = defaultDeadline;
            }
        });
    }

    if (cancelTaskButton && taskModal) {
        cancelTaskButton.addEventListener('click', () => {
            taskModal.classList.add('hidden');
            const taskTitleEl = document.getElementById('task-title');
            const taskPriorityEl = document.getElementById('task-priority');
            if (taskTitleEl) taskTitleEl.value = '';
            if (taskPriorityEl) taskPriorityEl.value = 'medium';
        });
    }

    if (taskModal) {
        taskModal.addEventListener('click', (e) => {
            if (e.target === taskModal) {
                taskModal.classList.add('hidden');
            }
        });
    }

    if (createTaskButton && taskModal) {
        createTaskButton.addEventListener('click', async () => {
            const titleEl = document.getElementById('task-title');
            const priorityEl = document.getElementById('task-priority');
            const deadlineEl = document.getElementById('task-deadline');

            if (!titleEl || !priorityEl || !deadlineEl) return;

            const title = titleEl.value.trim();
            const priority = priorityEl.value;
            const deadlineInput = deadlineEl.value;

            if (!title || !deadlineInput) {
                notifications.warning('Please fill in all required fields');
                return;
            }

            const deadlineDate = new Date(deadlineInput);
            const deadline = deadlineDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

            const project = state.projects[state.currentProjectId];
            const projectPrefix = state.currentProjectId.substring(0, 1);
            const taskCount = project.tasks.length;
            const newTaskId = `${projectPrefix} -t${taskCount + 1} `;

            const newTask = {
                id: newTaskId,
                title: title,
                priority: priority,
                deadline: deadline,
                projectId: state.currentProjectId,
                assignedTo: null
            };

            try {
                await saveTask(newTask);
                project.tasks.push(newTask);

                taskModal.classList.add('hidden');
                titleEl.value = '';
                priorityEl.value = 'medium';

                notifications.success(`Task "${title}" created successfully`);
                await renderAll();

                // Sync with mindmap
                await syncMindmap();
            } catch (error) {
                console.error('Failed to create task:', error);
                notifications.error('Failed to create task. Please try again.');
            }
        });
    }

    // Member Modal handling
    const addMemberButton = document.getElementById('add-member-button');
    const memberModal = document.getElementById('member-modal');
    const cancelMemberButton = document.getElementById('cancel-member-button');
    const createMemberButton = document.getElementById('create-member-button');

    if (addMemberButton && memberModal) {
        addMemberButton.addEventListener('click', () => {
            memberModal.classList.remove('hidden');
        });
    }

    if (cancelMemberButton && memberModal) {
        cancelMemberButton.addEventListener('click', () => {
            memberModal.classList.add('hidden');
            const memberNameEl = document.getElementById('member-name');
            const memberRoleEl = document.getElementById('member-role');
            if (memberNameEl) memberNameEl.value = '';
            if (memberRoleEl) memberRoleEl.value = '';
        });
    }

    if (memberModal) {
        memberModal.addEventListener('click', (e) => {
            if (e.target === memberModal) {
                memberModal.classList.add('hidden');
            }
        });
    }

    if (createMemberButton && memberModal) {
        createMemberButton.addEventListener('click', async () => {
            const memberNameEl = document.getElementById('member-name');
            const memberRoleEl = document.getElementById('member-role');

            if (!memberNameEl || !memberRoleEl) return;

            const name = memberNameEl.value.trim();
            const role = memberRoleEl.value.trim();

            if (!name || !role) {
                notifications.warning('Please fill in all fields');
                return;
            }

            const memberId = `tm${state.teamMembers.length + 1} `;
            const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
            const colors = ['60a5fa', 'ec4899', 'f59e0b', '8b5cf6', '10b981', 'ef4444', '3b82f6'];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];

            const newMember = {
                id: memberId,
                name: name,
                role: role,
                avatar: initials,
                avatarColor: randomColor
            };

            try {
                await saveMember(newMember);
                state.teamMembers.push(newMember);
                state.members[newMember.id] = newMember; // Add to members lookup

                memberModal.classList.add('hidden');
                memberNameEl.value = '';
                memberRoleEl.value = '';

                notifications.success(`Team member "${name}" added successfully`);
                await renderAll();
            } catch (error) {
                console.error('Failed to create member:', error);
                notifications.error('Failed to create member. Please try again.');
            }
        });
    }

    // Add Member to Project Modal handling
    const addMemberToProjectBtn = document.getElementById('add-member-to-project-btn');
    const addMemberToProjectModal = document.getElementById('add-member-to-project-modal');
    const closeAddMemberModal = document.getElementById('close-add-member-modal');
    const addMemberSearch = document.getElementById('add-member-search');
    const availableMembersList = document.getElementById('available-members-list');

    if (addMemberToProjectBtn && addMemberToProjectModal) {
        addMemberToProjectBtn.addEventListener('click', () => {
            const project = state.projects[state.currentProjectId];
            if (!project) {
                notifications.warning('Please select a project first');
                return;
            }
            renderAvailableMembers();
            addMemberToProjectModal.classList.remove('hidden');
        });
    }

    if (closeAddMemberModal && addMemberToProjectModal) {
        closeAddMemberModal.addEventListener('click', () => {
            addMemberToProjectModal.classList.add('hidden');
        });
    }

    if (addMemberToProjectModal) {
        addMemberToProjectModal.addEventListener('click', (e) => {
            if (e.target === addMemberToProjectModal) {
                addMemberToProjectModal.classList.add('hidden');
            }
        });
    }

    if (addMemberSearch) {
        addMemberSearch.addEventListener('input', (e) => {
            renderAvailableMembers(e.target.value.toLowerCase());
        });
    }

    function renderAvailableMembers(searchQuery = '') {
        if (!availableMembersList) return;

        const project = state.projects[state.currentProjectId];
        if (!project) return;

        const projectMemberIds = project.teamMembers || [];
        const availableMembers = state.teamMembers.filter(member => {
            const notInProject = !projectMemberIds.includes(member.id);
            const matchesSearch = searchQuery === '' ||
                member.name.toLowerCase().includes(searchQuery) ||
                member.role.toLowerCase().includes(searchQuery);
            return notInProject && matchesSearch;
        });

        if (availableMembers.length === 0) {
            availableMembersList.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i data-lucide="users" class="h-12 w-12 mx-auto mb-2 text-gray-400"></i>
                    <p class="text-sm">${searchQuery ? 'No members found' : 'All members are already in this project'}</p>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        availableMembersList.innerHTML = '';
        availableMembers.forEach(member => {
            const memberCard = document.createElement('div');
            memberCard.className = 'flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-green-400 hover:bg-green-50 transition-all cursor-pointer';

            memberCard.innerHTML = `
                <div class="flex items-center space-x-3">
                    <img class="w-10 h-10 rounded-full" 
                         src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" 
                         alt="${member.name}">
                    <div>
                        <h4 class="text-sm font-semibold text-gray-900">${member.name}</h4>
                        <p class="text-xs text-gray-500">${member.role}</p>
                    </div>
                </div>
                <button class="add-member-btn inline-flex items-center px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded-md hover:bg-green-700 transition-colors">
                    <i data-lucide="plus" class="h-3.5 w-3.5 mr-1"></i>
                    Add
                </button>
            `;

            const addBtn = memberCard.querySelector('.add-member-btn');
            addBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                await addMemberToCurrentProject(member.id);
            });

            memberCard.addEventListener('click', async () => {
                await addMemberToCurrentProject(member.id);
            });

            availableMembersList.appendChild(memberCard);
        });

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    async function addMemberToCurrentProject(memberId) {
        const project = state.projects[state.currentProjectId];
        if (!project) return;

        const member = state.teamMembers.find(m => m.id === memberId);
        if (!member) return;

        try {
            await assignMemberToProject(project.id, memberId);

            if (!project.teamMembers) {
                project.teamMembers = [];
            }
            project.teamMembers.push(memberId);

            notifications.success(`${member.name} added to ${project.name}`);
            renderAvailableMembers();
            await renderAll();
        } catch (error) {
            console.error('Failed to add member:', error);
            notifications.error('Failed to add member. Please try again.');
        }
    }

    // Create Project Modal handling
    const createProjectButton = document.getElementById('create-project-button');
    const projectModal = document.getElementById('project-modal');
    const cancelProjectButton = document.getElementById('cancel-project-button');
    const submitProjectButton = document.getElementById('submit-project-button');
    const projectForm = document.getElementById('project-form');
    const aiToggle = document.getElementById('use-ai-toggle');
    const aiUploadSection = document.getElementById('ai-upload-section');
    const manualDescSection = document.getElementById('manual-description-section');
    const manualColorSection = document.getElementById('manual-color-section');

    // Toggle AI-assisted mode
    if (aiToggle && aiUploadSection && manualDescSection && manualColorSection) {
        aiToggle.addEventListener('change', () => {
            if (aiToggle.checked) {
                aiUploadSection.classList.remove('hidden');
                manualDescSection.classList.add('hidden');
                manualColorSection.classList.add('hidden');
            } else {
                aiUploadSection.classList.add('hidden');
                manualDescSection.classList.remove('hidden');
                manualColorSection.classList.remove('hidden');
            }
        });
    }

    if (createProjectButton && projectModal) {
        createProjectButton.addEventListener('click', () => {
            projectModal.classList.remove('hidden');
        });
    }

    if (cancelProjectButton && projectModal && projectForm) {
        cancelProjectButton.addEventListener('click', () => {
            projectModal.classList.add('hidden');
            projectForm.reset();
        });
    }

    if (projectModal && projectForm) {
        projectModal.addEventListener('click', (e) => {
            if (e.target === projectModal) {
                projectModal.classList.add('hidden');
                projectForm.reset();
            }
        });
    }

    if (submitProjectButton && projectModal && projectForm) {
        submitProjectButton.addEventListener('click', async () => {
            const projectNameEl = document.getElementById('project-name');
            const projectDescEl = document.getElementById('project-description');
            const aiToggle = document.getElementById('use-ai-toggle');
            const aiPdfUpload = document.getElementById('ai-pdf-upload');

            if (!projectNameEl || !projectDescEl) return;

            const name = projectNameEl.value.trim();
            const description = projectDescEl.value.trim();
            const useAI = aiToggle && aiToggle.checked;
            const pdfFile = aiPdfUpload && aiPdfUpload.files[0];

            const colorRadios = document.querySelectorAll('input[name="project-color"]');
            let color = 'blue';
            colorRadios.forEach(radio => {
                if (radio.checked) color = radio.value;
            });

            if (!name) {
                notifications.warning('Please enter a project name');
                return;
            }

            // AI-Assisted project creation
            if (useAI && pdfFile) {
                try {
                    submitProjectButton.disabled = true;
                    submitProjectButton.innerHTML = '<i data-lucide="loader" class="h-4 w-4 mr-2 animate-spin"></i> Processing with AI...';
                    lucide.createIcons();

                    // Step 1: Upload PDF and create MCP project
                    const formData = new FormData();
                    formData.append('project_name', name);
                    formData.append('pdf_file', pdfFile);

                    const createResponse = await fetch('/api/mcp-projects/create', {
                        method: 'POST',
                        body: formData
                    });

                    if (!createResponse.ok) throw new Error('Failed to upload PDF');
                    const createResult = await createResponse.json();
                    const mcpProjectId = createResult.project.id;

                    // Step 2: Analyze with Gemini AI
                    submitProjectButton.innerHTML = '<i data-lucide="sparkles" class="h-4 w-4 mr-2 animate-pulse"></i> Analyzing with AI...';
                    lucide.createIcons();

                    const analyzeResponse = await fetch(`/api/mcp-projects/${mcpProjectId}/analyze`, {
                        method: 'POST'
                    });

                    if (!analyzeResponse.ok) throw new Error('Failed to analyze document');

                    // Step 3: Create dashboard project from analysis
                    submitProjectButton.innerHTML = '<i data-lucide="layout-dashboard" class="h-4 w-4 mr-2"></i> Creating project...';
                    lucide.createIcons();

                    const dashboardResponse = await fetch(`/api/mcp-projects/${mcpProjectId}/create-dashboard-project`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });

                    if (!dashboardResponse.ok) {
                        const error = await dashboardResponse.json();
                        throw new Error(error.error || 'Failed to create project');
                    }

                    const dashboardResult = await dashboardResponse.json();
                    notifications.success(`🎉 Project created with ${dashboardResult.tasks_created} AI-generated tasks!`);

                    projectModal.classList.add('hidden');
                    projectForm.reset();

                    // Reload page to show new project
                    window.location.reload();

                } catch (error) {
                    console.error('AI project creation error:', error);
                    notifications.error(`Failed to create AI project: ${error.message}`);
                } finally {
                    submitProjectButton.disabled = false;
                    submitProjectButton.innerHTML = '<i data-lucide="check" class="h-4 w-4 mr-2"></i> Create Project';
                    lucide.createIcons();
                }
                return;
            }

            // Manual project creation (existing code)
            const projectId = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

            const newProject = {
                id: projectId,
                name: name,
                description: description,
                tagColor: color,
                tasks: [],
                teamMembers: []
            };

            try {
                await saveProject(newProject);
                state.projects[projectId] = newProject;
                state.currentProjectId = projectId;

                projectModal.classList.add('hidden');
                projectForm.reset();

                notifications.success(`Project "${name}" created successfully`);
                await renderAll();

                // Sync with mindmap
                await syncMindmap();
            } catch (error) {
                console.error('Failed to create project:', error);
                notifications.error('Failed to create project. Please try again.');
            }
        });
    }

    // Member Directory Search
    const memberSearchInput = document.getElementById('member-search-input');
    if (memberSearchInput) {
        memberSearchInput.addEventListener('input', (e) => {
            state.memberSearchQuery = e.target.value;
            renderMemberDirectory();
            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                lucide.createIcons();
            }
        });
    }

    // Manage Team Modal handling
    const manageTeamButton = document.getElementById('manage-team-button');
    const manageTeamModal = document.getElementById('manage-team-modal');
    const closeManageTeamButton = document.getElementById('close-manage-team-button');
    const doneManageTeamButton = document.getElementById('done-manage-team-button');
    const teamMemberSearchInput = document.getElementById('team-member-search-input');

    if (manageTeamButton) {
        manageTeamButton.addEventListener('click', () => {
            if (!state.currentProjectId) {
                notifications.warning('Please select a project first');
                return;
            }
            openManageTeamModal();
        });
    }

    if (closeManageTeamButton && manageTeamModal) {
        closeManageTeamButton.addEventListener('click', async () => {
            manageTeamModal.classList.add('hidden');
            await renderAll();
        });
    }

    if (doneManageTeamButton && manageTeamModal) {
        doneManageTeamButton.addEventListener('click', async () => {
            manageTeamModal.classList.add('hidden');
            await renderAll();
        });
    }

    if (manageTeamModal) {
        manageTeamModal.addEventListener('click', (e) => {
            if (e.target === manageTeamModal) {
                manageTeamModal.classList.add('hidden');
                renderAll();
            }
        });
    }

    if (teamMemberSearchInput) {
        teamMemberSearchInput.addEventListener('input', (e) => {
            state.teamMemberSearchQuery = e.target.value;
            renderTeamManagementModal();
        });
    }

    initializeApp();
});

// Cleanup polling on page unload
window.addEventListener('beforeunload', () => {
    techStackPolling.stopAll();
});

// Team Management Modal Functions
function openManageTeamModal() {
    const project = state.projects[state.currentProjectId];
    if (!project) return;

    const modal = document.getElementById('manage-team-modal');
    const projectNameEl = document.getElementById('manage-team-project-name');

    projectNameEl.textContent = project.name;
    modal.classList.remove('hidden');

    renderTeamManagementModal();
}

function renderTeamManagementModal() {
    const project = state.projects[state.currentProjectId];
    if (!project) return;

    const currentTeamList = document.getElementById('current-team-list');
    const availableMembersList = document.getElementById('available-members-list');
    const noTeamMembers = document.getElementById('no-team-members');

    // Get current team members
    const currentTeamMembers = state.teamMembers.filter(m =>
        project.teamMembers && project.teamMembers.includes(m.id)
    );

    // Get available members (not in current team)
    const availableMembers = state.teamMembers.filter(m =>
        !project.teamMembers || !project.teamMembers.includes(m.id)
    ).filter(m => {
        const query = state.teamMemberSearchQuery.toLowerCase();
        return m.name.toLowerCase().includes(query) || m.role.toLowerCase().includes(query);
    });

    // Render current team
    if (currentTeamMembers.length === 0) {
        noTeamMembers.classList.remove('hidden');
        currentTeamList.innerHTML = '';
    } else {
        noTeamMembers.classList.add('hidden');
        currentTeamList.innerHTML = currentTeamMembers.map(member => `
            <div class="flex items-center justify-between p-3 bg-blue-50 rounded-md border border-blue-200">
                <div class="flex items-center space-x-3">
                    <img class="w-8 h-8 rounded-full" 
                         src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" 
                         alt="${member.name}">
                    <div>
                        <h5 class="text-sm font-semibold text-gray-900">${member.name}</h5>
                        <p class="text-xs text-gray-600">${member.role}</p>
                    </div>
                </div>
                <button onclick="removeMemberFromTeam('${member.id}')" 
                        class="text-red-500 hover:text-red-700 p-1">
                    <i data-lucide="x" class="h-4 w-4"></i>
                </button>
            </div>
        `).join('');
    }

    // Render available members
    if (availableMembers.length === 0) {
        availableMembersList.innerHTML = '<p class="text-sm text-gray-400 italic text-center py-4">No available members</p>';
    } else {
        availableMembersList.innerHTML = availableMembers.map(member => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors">
                <div class="flex items-center space-x-3">
                    <img class="w-8 h-8 rounded-full" 
                         src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" 
                         alt="${member.name}">
                    <div>
                        <h5 class="text-sm font-semibold text-gray-900">${member.name}</h5>
                        <p class="text-xs text-gray-600">${member.role}</p>
                    </div>
                </div>
                <button onclick="addMemberToTeam('${member.id}')" 
                        class="px-3 py-1 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md">
                    Add
                </button>
            </div>
    `).join('');
    }

    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }
}

async function addMemberToTeam(memberId) {
    const project = state.projects[state.currentProjectId];
    if (!project) return;

    try {
        await assignMemberToProject(project.id, memberId);

        if (!project.teamMembers) {
            project.teamMembers = [];
        }
        project.teamMembers.push(memberId);

        const member = state.members[memberId];
        notifications.success(`${member.name} added to team`);

        renderTeamManagementModal();
        renderMemberDirectory();
    } catch (error) {
        console.error('Failed to add member to team:', error);
        notifications.error('Failed to add member. Please try again.');
    }
}

async function removeMemberFromTeam(memberId) {
    const project = state.projects[state.currentProjectId];
    if (!project) return;

    const member = state.members[memberId];

    try {
        const confirmed = await confirmation.show({
            title: 'Remove Team Member',
            message: `Are you sure you want to remove ${member.name} from this project ? `,
            danger: true,
            confirmText: 'Remove',
            async onConfirm() {
                try {
                    await removeMemberFromProject(project.id, memberId);

                    if (project.teamMembers) {
                        project.teamMembers = project.teamMembers.filter(id => id !== memberId);
                    }

                    // Unassign any tasks assigned to this member in this project
                    if (project.tasks) {
                        project.tasks.forEach(task => {
                            if (task.assignedTo === memberId) {
                                task.assignedTo = null;
                            }
                        });
                    }

                    // Re-render all relevant sections
                    await renderAll();
                    notifications.success(`${member.name} removed from team`);
                } catch (error) {
                    console.error('Failed to remove member from project:', error);
                    notifications.error('Failed to remove member. Please try again.');
                    throw error; // Re-throw to prevent modal from closing
                }
            }
        });
    } catch (error) {
        console.error('Error in removeMemberFromTeam:', error);
    }
}

// Global function for opening project modal (called from sidebar)
function openProjectModal() {
    const modal = document.getElementById('project-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

// Tech Stack Suggestions
async function generateTechStack(event, taskId) {
    event.stopPropagation();
    event.preventDefault();

    const button = event.currentTarget;
    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i data-lucide="loader" class="h-3.5 w-3.5 animate-spin"></i> Generating...';
    lucide.createIcons();

    try {
        console.log('Generating tech stack for task:', taskId);
        const response = await fetch(`${API_BASE}/tasks/${taskId}/suggest-tech-stack`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error('Failed to generate tech stack');

        const result = await response.json();
        console.log('Tech stack generated:', result);

        notifications.success(`Tech stack suggested by ${result.generatedBy}`);

        // Reload data to show the updated tech stack
        await loadProjects();
        renderAll();

    } catch (error) {
        console.error('Failed to generate tech stack:', error);
        notifications.error('Failed to generate tech stack. Please try again.');
        button.disabled = false;
        button.innerHTML = originalHtml;
        lucide.createIcons();
    }
}

function showTechStackModal(event, taskId) {
    event.stopPropagation();
    event.preventDefault();

    // Find the task
    let task = null;
    for (const projectId in state.projects) {
        const project = state.projects[projectId];
        task = project.tasks.find(t => t.id === taskId);
        if (task) break;
    }

    if (!task || !task.techStack) {
        notifications.error('Tech stack not found');
        return;
    }

    const techStack = task.techStack;

    let modalHtml = `
        <div id="tech-stack-modal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onclick="this.remove()">
            <div class="bg-slate-800 rounded-xl border border-slate-700 shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto" onclick="event.stopPropagation()">
                <div class="sticky top-0 bg-slate-800 border-b border-slate-700 p-6 flex justify-between items-start">
                    <div>
                        <h2 class="text-xl font-bold text-emerald-400">Tech Stack Suggestions</h2>
                        <p class="text-sm text-slate-400 mt-1">${task.title}</p>
                    </div>
                    <button onclick="document.getElementById('tech-stack-modal').remove()" class="text-slate-400 hover:text-slate-100 transition-colors">
                        <i data-lucide="x" class="h-6 w-6"></i>
                    </button>
                </div>
                
                <div class="p-6 space-y-6">
                    <!-- Tech Stack -->
                    ${techStack.techStack && techStack.techStack.length > 0 ? `
                        <div>
                            <h3 class="text-lg font-semibold text-slate-100 mb-3 flex items-center">
                                <i data-lucide="layers" class="h-5 w-5 mr-2 text-emerald-400"></i>
                                Technologies & Frameworks
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                ${techStack.techStack.map(tech => `
                                    <div class="p-4 bg-slate-700/50 rounded-lg border border-slate-600/30">
                                        <div class="flex items-start justify-between mb-2">
                                            <h4 class="font-semibold text-slate-100">${tech.name}</h4>
                                            <span class="text-xs px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">${tech.category}</span>
                                        </div>
                                        <p class="text-sm text-slate-400">${tech.purpose}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Tools -->
                    ${techStack.tools && techStack.tools.length > 0 ? `
                        <div>
                            <h3 class="text-lg font-semibold text-slate-100 mb-3 flex items-center">
                                <i data-lucide="wrench" class="h-5 w-5 mr-2 text-emerald-400"></i>
                                Development Tools
                            </h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                ${techStack.tools.map(tool => `
                                    <div class="p-4 bg-slate-700/50 rounded-lg border border-slate-600/30">
                                        <h4 class="font-semibold text-slate-100 mb-1">${tool.name}</h4>
                                        <p class="text-sm text-slate-400">${tool.purpose}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Best Practices -->
                    ${techStack.bestPractices && techStack.bestPractices.length > 0 ? `
                        <div>
                            <h3 class="text-lg font-semibold text-slate-100 mb-3 flex items-center">
                                <i data-lucide="check-circle" class="h-5 w-5 mr-2 text-emerald-400"></i>
                                Best Practices
                            </h3>
                            <ul class="space-y-2">
                                ${techStack.bestPractices.map(practice => `
                                    <li class="flex items-start text-slate-300">
                                        <span class="text-emerald-400 mr-2">•</span>
                                        <span class="text-sm">${practice}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    
                    <!-- Resources -->
                    ${techStack.resources && techStack.resources.length > 0 ? `
                        <div>
                            <h3 class="text-lg font-semibold text-slate-100 mb-3 flex items-center">
                                <i data-lucide="book-open" class="h-5 w-5 mr-2 text-emerald-400"></i>
                                Learning Resources
                            </h3>
                            <div class="space-y-2">
                                ${techStack.resources.map(resource => `
                                    <a href="${resource.url}" target="_blank" class="block p-4 bg-slate-700/50 rounded-lg border border-slate-600/30 hover:border-emerald-500/50 transition-all group">
                                        <h4 class="font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors">${resource.title}</h4>
                                        <p class="text-sm text-slate-400 mt-1">${resource.description}</p>
                                        <div class="text-xs text-emerald-400 mt-2 flex items-center">
                                            <span class="truncate">${resource.url}</span>
                                            <i data-lucide="external-link" class="h-3 w-3 ml-1 flex-shrink-0"></i>
                                        </div>
                                    </a>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
                
                <div class="sticky bottom-0 bg-slate-800 border-t border-slate-700 p-6 flex justify-end gap-3">
                    <button onclick="generateTechStack(event, '${taskId}')" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-all flex items-center gap-2">
                        <i data-lucide="refresh-cw" class="h-4 w-4"></i>
                        Regenerate
                    </button>
                    <button onclick="document.getElementById('tech-stack-modal').remove()" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg transition-all">
                        Close
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    lucide.createIcons();
}