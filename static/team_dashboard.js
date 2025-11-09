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
        case 'high': return 'bg-red-100 text-red-800';
        case 'medium': return 'bg-yellow-100 text-yellow-800';
        case 'low': return 'bg-green-100 text-green-800';
        default: return 'bg-gray-100 text-gray-800';
    }
};

const getProjectTagColor = (color) => {
    switch (color) {
        case 'yellow': return 'bg-yellow-100 text-yellow-800';
        case 'green': return 'bg-green-100 text-green-800';
        case 'blue': return 'bg-blue-100 text-blue-800';
        case 'red': return 'bg-red-100 text-red-800';
        case 'purple': return 'bg-purple-100 text-purple-800';
        default: return 'bg-gray-100 text-gray-800';
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
        addDragAndDropListeners();

        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
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
        container.innerHTML = '<p class="col-span-4 text-center text-gray-500">Select a project to view stats</p>';
        return;
    }

    const tasks = project.tasks || [];
    const tasksInProgress = tasks.filter(t => t.assignedTo).length;
    const tasksInBacklog = tasks.filter(t => !t.assignedTo).length;
    const teamMembersOnProject = project.teamMembers ? project.teamMembers.length : 0;

    container.innerHTML = `
        <div class="bg-white overflow-hidden shadow-sm rounded-lg border border-slate-200 cursor-pointer hover:shadow-md transition-shadow">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center"><i data-lucide="users" class="h-6 w-6 text-blue-600"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dt class="text-sm font-medium text-gray-500 truncate">Team Members on Project</dt>
                        <dd class="text-3xl font-semibold text-gray-900">${teamMembersOnProject}</dd>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-white overflow-hidden shadow-sm rounded-lg border border-slate-200 cursor-pointer hover:shadow-md transition-shadow">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center"><i data-lucide="folder-kanban" class="h-6 w-6 text-green-600"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dt class="text-sm font-medium text-gray-500 truncate">Total Project Tasks</dt>
                        <dd class="text-3xl font-semibold text-gray-900">${tasks.length}</dd>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-white overflow-hidden shadow-sm rounded-lg border border-slate-200 cursor-pointer hover:shadow-md transition-shadow">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center"><i data-lucide="check-circle" class="h-6 w-6 text-yellow-600"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dt class="text-sm font-medium text-gray-500 truncate">Tasks In-Progress</dt>
                        <dd class="text-3xl font-semibold text-gray-900">${tasksInProgress}</dd>
                    </div>
                </div>
            </div>
        </div>
        <div class="bg-white overflow-hidden shadow-sm rounded-lg border border-slate-200 cursor-pointer hover:shadow-md transition-shadow">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0"><div class="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center"><i data-lucide="list" class="h-6 w-6 text-red-600"></i></div></div>
                    <div class="ml-4 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 truncate">Tasks in Backlog</dt>
                            <dd class="text-3xl font-semibold text-gray-900">${tasksInBacklog}</dd>
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

    countBadge.textContent = `${filteredMembers.length} member${filteredMembers.length !== 1 ? 's' : ''}`;

    if (filteredMembers.length === 0) {
        container.innerHTML = '<p class="text-sm text-gray-400 italic text-center py-4">No members found</p>';
        return;
    }

    container.innerHTML = '';

    filteredMembers.forEach(member => {
        const project = state.projects[state.currentProjectId];
        const isAssigned = project && project.teamMembers && project.teamMembers.includes(member.id);

        const card = document.createElement('div');
        card.className = 'flex items-center justify-between p-3 bg-slate-50 rounded-md hover:bg-slate-100 transition-colors member-card cursor-move';
        card.draggable = true;
        card.dataset.memberId = member.id;
        card.title = 'Drag to assign to a project';

        card.innerHTML = `
            <div class="flex items-center space-x-3">
                <img class="w-10 h-10 rounded-full" 
                     src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" 
                     alt="${member.name}">
                <div>
                    <h4 class="text-sm font-semibold text-gray-900 editable-field" contenteditable="true" data-member-id="${member.id}" data-field="name">${member.name}</h4>
                    <p class="text-xs text-gray-500 editable-field" contenteditable="true" data-member-id="${member.id}" data-field="role">${member.role}</p>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                ${isAssigned ?
                `<span class="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">Assigned</span>` :
                `<span class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">Available</span>`
            }
                <button class="delete-member-btn text-red-400 hover:text-red-600" onclick="deleteMemberConfirm(event, '${member.id}')">
                    <i data-lucide="trash-2" class="h-4 w-4"></i>
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
        card.className = 'col-span-1 bg-white rounded-lg shadow-sm border border-slate-200 divide-y divide-slate-200 group member-card cursor-move';
        card.dataset.teamId = member.id;
        card.draggable = true;
        card.dataset.memberId = member.id;
        card.title = 'Drag to assign to a project';

        card.innerHTML = `
    < div class="w-full flex items-center justify-between p-5 space-x-6" >
                <div class="flex-1 truncate">
                    <div class="flex items-center space-x-3">
                        <h3 class="text-gray-900 text-sm font-semibold truncate editable-field" contenteditable="true" data-member-id="${member.id}" data-field="name">${member.name}</h3>
                        <span class="flex-shrink-0 inline-block px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full editable-field" contenteditable="true" data-member-id="${member.id}" data-field="role">
                            ${member.role}
                        </span>
                    </div>
                    <p class="mt-1 text-gray-500 text-sm truncate">Core Platform</p>
                </div>
                <div class="flex items-center gap-2">
                    <img class="w-10 h-10 bg-gray-300 rounded-full flex-shrink-0" src="https://placehold.co/100x100/${member.avatarColor}/ffffff?text=${member.avatar}" alt="${member.name}">
                    <button class="delete-member-btn opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600" onclick="deleteMemberConfirm(event, '${member.id}')">
                        <i data-lucide="trash-2" class="h-4 w-4"></i>
                    </button>
                </div>
            </div >
    <div class="p-5 min-h-[160px]">
        ${assignedTask ?
            renderTaskOnCard(assignedTask) :
            `<div class="flex items-center justify-center h-full">
                        <p class="text-sm text-gray-400 italic">No task assigned for this project.</p>
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
    });
}

function renderTaskOnCard(task) {
    const priorityClass = getPriorityClasses(task.priority);
    return `
    < div class="task-card-assigned relative group" draggable = "true" data - task - id="${task.id}" data - project - id="${task.projectId}" >
            <button class="absolute top-0 right-0 opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600" onclick="deleteTaskConfirm(event, '${task.id}')">
                <i data-lucide="trash-2" class="h-4 w-4"></i>
            </button>
            <h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider">Current Task</h4>
            <p class="mt-1 text-sm text-gray-800 font-medium editable-field" contenteditable="true" data-task-id="${task.id}" data-field="title">${task.title}</p>
            
            <div class="mt-4 flex justify-between items-start">
                <div>
                    <h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</h4>
                    <select class="mt-1 text-xs font-medium px-2.5 py-0.5 rounded-full border-0 ${priorityClass}" data-task-id="${task.id}" data-field="priority">
                        <option value="low" ${task.priority === 'low' ? 'selected' : ''}>Low</option>
                        <option value="medium" ${task.priority === 'medium' ? 'selected' : ''}>Medium</option>
                        <option value="high" ${task.priority === 'high' ? 'selected' : ''}>High</option>
                    </select>
                </div>
                <div class="text-right">
                    <h4 class="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center justify-end">
                        <i data-lucide="calendar" class="mr-1.5 h-3.5 w-3.5 text-gray-400"></i>
                        Deadline
                    </h4>
                    <p class="mt-1 text-sm text-gray-800 font-medium editable-field" contenteditable="true" data-task-id="${task.id}" data-field="deadline">${task.deadline}</p>
                </div>
            </div>
        </div >
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
    titleEl.textContent = `${ project.name } Backlog`;
    titleEl.dataset.projectId = project.id;

    const list = document.getElementById('project-backlog-list');
    list.innerHTML = '';

    if (backlogTasks.length === 0) {
        list.innerHTML = `< li class="text-sm text-gray-400 italic text-center mt-4" > Backlog is empty!</li > `;
        return;
    }

    backlogTasks.forEach(task => {
        const priorityClass = getPriorityClasses(task.priority);
        const taskCard = document.createElement('li');
        taskCard.className = 'p-3 bg-slate-50 rounded-md border border-slate-200 shadow-sm cursor-grab active:cursor-grabbing relative group';
        taskCard.draggable = true;
        taskCard.dataset.taskId = task.id;
        taskCard.dataset.projectId = project.id;

        taskCard.innerHTML = `
    < button class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600" onclick = "deleteTaskConfirm(event, '${task.id}')" >
        <i data-lucide="trash-2" class="h-4 w-4"></i>
            </button >
            <p class="text-sm font-medium text-gray-800 pr-8">${task.title}</p>
            <div class="mt-2 flex justify-between items-center">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${priorityClass}">
                    ${task.priority}
                </span>
                <span class="text-xs font-medium text-gray-500 flex items-center">
                    <i data-lucide="calendar" class="mr-1 h-3.5 w-3.5 text-gray-400"></i>
                    ${task.deadline}
                </span>
            </div>
`;
        list.appendChild(taskCard);
    });
}

function updateMainHeader() {
    const project = state.projects[state.currentProjectId];
    const title = project ? `Core Platform Team - ${ project.name } ` : 'Core Platform Team';
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
    e.target.classList.add('task-card-dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', JSON.stringify({
        taskId: e.target.dataset.taskId,
        projectId: e.target.dataset.projectId
    }));
}

function handleDragEnd(e) {
    e.target.classList.remove('task-card-dragging');
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
                notifications.warning(`${ member.name } is already assigned to ${ project.name } `);
                return;
            }

            // Assign member to project
            await assignMemberToProject(projectId, memberId);

            if (!project.teamMembers) {
                project.teamMembers = [];
            }
            project.teamMembers.push(memberId);

            notifications.success(`${ member.name } added to ${ project.name } `);

            // Update UI if we're viewing this project
            if (state.currentProjectId === projectId) {
                await renderAll();
            } else {
                await renderSidebar();
            }
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
        message: `Are you sure you want to remove ${ member?.name || 'this member' } from the team ? This action cannot be undone.`,
        confirmText: 'Remove Member',
        type: 'danger',
        onConfirm: async () => {
            await deleteMember(memberId);
            state.teamMembers = state.teamMembers.filter(m => m.id !== memberId);
            delete state.members[memberId]; // Remove from members lookup
            notifications.success(`${ member?.name || 'Member' } has been removed successfully`);
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
        }
    });
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
        projects.forEach(project => {
            state.projects[project.id] = project;
        });

        if (projects.length > 0 && !state.currentProjectId) {
            state.currentProjectId = projects[0].id;
        }

        await renderAll();
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
            const newTaskId = `${ projectPrefix } -t${ taskCount + 1 } `;

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

            const memberId = `tm${ state.teamMembers.length + 1 } `;
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

    // Create Project Modal handling
    const createProjectButton = document.getElementById('create-project-button');
    const projectModal = document.getElementById('project-modal');
    const cancelProjectButton = document.getElementById('cancel-project-button');
    const submitProjectButton = document.getElementById('submit-project-button');
    const projectForm = document.getElementById('project-form');

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

            if (!projectNameEl || !projectDescEl) return;

            const name = projectNameEl.value.trim();
            const description = projectDescEl.value.trim();
            const colorRadios = document.querySelectorAll('input[name="project-color"]');
            let color = 'blue';
            colorRadios.forEach(radio => {
                if (radio.checked) color = radio.value;
            });

            if (!name) {
                notifications.warning('Please enter a project name');
                return;
            }

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
    < div class="flex items-center justify-between p-3 bg-blue-50 rounded-md border border-blue-200" >
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
            </div >
    `).join('');
    }

    // Render available members
    if (availableMembers.length === 0) {
        availableMembersList.innerHTML = '<p class="text-sm text-gray-400 italic text-center py-4">No available members</p>';
    } else {
        availableMembersList.innerHTML = availableMembers.map(member => `
    < div class="flex items-center justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors" >
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
            </div >
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
        notifications.success(`${ member.name } added to team`);

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
            message: `Are you sure you want to remove ${ member.name } from this project ? `,
            danger: true,
            confirmText: 'Remove',
            async onConfirm() {
                try {
                    await removeMemberFromProject(project.id, memberId);

                    if (project.teamMembers) {
                        project.teamMembers = project.teamMembers.filter(id => id !== memberId);
                    }

                    renderTeamManagementModal();
                    renderMemberDirectory();
                    notifications.success(`${ member.name } removed from team`);
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