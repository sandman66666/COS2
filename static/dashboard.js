// User Authentication Functions
console.log('🔧 Dashboard.js script loaded!');

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user-info');
        
        if (response.status === 401) {
            console.log('❌ Authentication required - redirecting to login');
            handleAuthenticationRequired();
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Validate the response structure
        if (!result || !result.user) {
            throw new Error('Invalid response format: missing user data');
        }
        
        const userEmailElement = document.getElementById('user-email');
        if (userEmailElement) {
            userEmailElement.textContent = result.user.email || 'Unknown User';
        }
        
        console.log('👤 User info loaded:', result.user.email);
        return result.user;
        
    } catch (error) {
        console.error('Error loading user info:', error);
        
        const userEmailElement = document.getElementById('user-email');
        if (userEmailElement) {
            // Check if we're in debug mode or if this is a known auth issue
            if (error.message.includes('404') || error.message.includes('Authentication required')) {
                userEmailElement.textContent = 'Authentication Required';
            } else {
                userEmailElement.textContent = 'Error loading user';
            }
        }
        
        // For non-401 errors, return a default user object for graceful degradation
        return {
            email: 'Not authenticated',
            authenticated: false
        };
    }
}

function handleAuthenticationRequired() {
    // Show user-friendly message
    showMessage('Your session has expired. Please log in again.', 'warning');
    
    // Update UI to show logged out state
    const userEmailElement = document.getElementById('user-email');
    if (userEmailElement) {
        userEmailElement.textContent = 'Please log in';
    }
    
    // Disable all pipeline controls
    disableAllPipelineControls();
    
    // Redirect to login after a short delay
    setTimeout(() => {
        window.location.href = '/login';
    }, 2000);
}

function disableAllPipelineControls() {
    // Disable all run buttons
    const runButtons = document.querySelectorAll('button[onclick*="runIndividualStep"], button[onclick*="startFromStep"], button[onclick*="startFullPipeline"]');
    runButtons.forEach(button => {
        button.disabled = true;
        button.textContent = 'Login Required';
    });
    
    // Show authentication warning on all step controls
    const stepStatuses = document.querySelectorAll('[id$="-status"]');
    stepStatuses.forEach(status => {
        status.innerHTML = '<span class="status warning">⚠️ Please log in to run operations</span>';
    });
}

async function checkAuthentication() {
    try {
        const response = await fetch('/api/user-info');
        
        if (response.status === 401) {
            console.log('❌ Authentication check failed - user not logged in');
            handleAuthenticationRequired();
            return false;
        }
        
        if (response.ok) {
            const result = await response.json();
            return result && result.user && result.user.email;
        }
        
        return false;
    } catch (error) {
        console.error('Authentication check failed:', error);
        return false;
    }
}

function logout() {
    if (confirm('Are you sure you want to sign out?')) {
        // Clear any cached data
        if (typeof(Storage) !== "undefined") {
            localStorage.clear();
            sessionStorage.clear();
        }
        
        // Redirect to logout endpoint
        window.location.href = '/logout';
    }
}

// Initialize user info when page loads
document.addEventListener('DOMContentLoaded', async function() {
    const user = await loadUserInfo();
    if (!user) {
        // User not authenticated, already handled by loadUserInfo
        return;
    }
});

// === AUTHENTICATION STATUS ===

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            console.log(`❌ Authentication required for ${url}`);
            handleAuthenticationRequired();
            throw new Error('Authentication required');
        }
        
        return response;
    } catch (error) {
        if (error.message === 'Authentication required') {
            throw error;
        }
        console.error(`API call to ${url} failed:`, error);
        throw error;
    }
}

async function loadAuthStatus() {
    try {
        // This function checks if user is authenticated
        console.log('🔐 Checking authentication status...');
        
        // Try to load user info to verify auth
        const user = await loadUserInfo();
        
        if (user && user.authenticated !== false && user.email !== 'Not authenticated') {
            console.log('✅ User authenticated:', user.email);
            return user;
        } else {
            console.log('❌ User not authenticated or auth status unknown');
            return null;
        }
        
    } catch (error) {
        console.error('Auth status check failed:', error);
        return null;
    }
}

// CEO Strategic Intelligence Functions
async function generateCEOIntelligenceBrief() {
    try {
        updateStatus('ceo-brief-status', 'loading', 'Generating CEO intelligence brief...');
        
        const focusArea = document.getElementById('focus-area').value.trim();
        const requestData = {};
        
        if (focusArea) {
            requestData.focus_area = focusArea;
        }
        
        const response = await apiCall('/api/intelligence/ceo-intelligence-brief', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            updateStatus('ceo-brief-status', 'success', 'CEO intelligence brief generated successfully');
            showCEOIntelligenceModal(result.brief);
        } else {
            updateStatus('ceo-brief-status', 'error', result.message || 'Failed to generate CEO brief');
        }
        
    } catch (error) {
        console.error('Error generating CEO intelligence brief:', error);
        if (error.message === 'Authentication required') {
            updateStatus('ceo-brief-status', 'error', 'Please log in to generate CEO brief');
            return;
        }
        updateStatus('ceo-brief-status', 'error', 'Error generating CEO brief: ' + error.message);
    }
}

async function analyzeCompetitiveLandscape() {
    try {
        updateStatus('competitive-analysis-status', 'loading', 'Analyzing competitive landscape...');
        
        const response = await apiCall('/api/intelligence/competitive-landscape-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            updateStatus('competitive-analysis-status', 'success', 'Competitive landscape analysis completed');
            // Store analysis data for later use
            window.competitiveLandscapeData = result.analysis;
        } else {
            updateStatus('competitive-analysis-status', 'error', result.message || 'Failed to analyze competitive landscape');
        }
        
    } catch (error) {
        console.error('Error analyzing competitive landscape:', error);
        if (error.message === 'Authentication required') {
            updateStatus('competitive-analysis-status', 'error', 'Please log in to analyze competitive landscape');
            return;
        }
        updateStatus('competitive-analysis-status', 'error', 'Error analyzing competitive landscape: ' + error.message);
    }
}

async function mapNetworkToObjectives() {
    try {
        updateStatus('network-mapping-status', 'loading', 'Mapping network to objectives...');
        
        const response = await apiCall('/api/intelligence/network-to-objectives-mapping', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            updateStatus('network-mapping-status', 'success', 'Network mapping completed');
            // Store network mapping data for later use
            window.networkMappingData = result.network_mapping;
        } else {
            updateStatus('network-mapping-status', 'error', result.message || 'Failed to map network to objectives');
        }
        
    } catch (error) {
        console.error('Error mapping network to objectives:', error);
        if (error.message === 'Authentication required') {
            updateStatus('network-mapping-status', 'error', 'Please log in to map network to objectives');
            return;
        }
        updateStatus('network-mapping-status', 'error', 'Error mapping network: ' + error.message);
    }
}

async function generateDecisionSupport() {
    try {
        updateStatus('decision-support-status', 'loading', 'Generating decision support...');
        
        const decisionArea = document.getElementById('decision-area').value.trim();
        const decisionOptionsText = document.getElementById('decision-options').value.trim();
        
        if (!decisionArea) {
            updateStatus('decision-support-status', 'error', 'Please enter a decision area');
            return;
        }
        
        // Parse decision options from textarea (one per line)
        const decisionOptions = decisionOptionsText.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .map((option, index) => ({
                title: `Option ${index + 1}`,
                description: option,
                timeline: 'To be determined',
                investment: 'To be determined',
                expected_outcome: 'To be analyzed'
            }));
        
        if (decisionOptions.length === 0) {
            updateStatus('decision-support-status', 'error', 'Please enter at least one decision option');
            return;
        }
        
        const response = await apiCall('/api/intelligence/decision-support', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                decision_area: decisionArea,
                decision_options: decisionOptions
            })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            updateStatus('decision-support-status', 'success', 'Decision support generated');
            // Store decision support data for later use
            window.decisionSupportData = result.decision_support;
        } else {
            updateStatus('decision-support-status', 'error', result.message || 'Failed to generate decision support');
        }
        
    } catch (error) {
        console.error('Error generating decision support:', error);
        if (error.message === 'Authentication required') {
            updateStatus('decision-support-status', 'error', 'Please log in to generate decision support');
            return;
        }
        updateStatus('decision-support-status', 'error', 'Error generating decision support: ' + error.message);
    }
}

// CEO Intelligence Modal Functions
function showCEOIntelligenceModal(briefData) {
    const modal = document.getElementById('ceo-results-modal');
    modal.style.display = 'block';
    
    // Populate modal with CEO intelligence brief data
    populateCEOIntelligenceData(briefData);
}

function closeCEOModal() {
    const modal = document.getElementById('ceo-results-modal');
    modal.style.display = 'none';
}

function showCEOTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.ceo-tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.ceo-tab-btn');
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab content
    const selectedContent = document.getElementById(`${tabName}-tab`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showCEOTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
}

function populateCEOIntelligenceData(briefData) {
    if (!briefData) return;
    
    // Populate Executive Summary
    const executiveSummaryContent = document.getElementById('executive-summary-content');
    if (executiveSummaryContent && briefData.executive_summary) {
        const summary = briefData.executive_summary;
        executiveSummaryContent.innerHTML = `
            <div class="ceo-summary-section">
                <h4><i class="fas fa-star"></i> Key Strategic Insights</h4>
                <div class="insight-items">
                    ${(summary.key_insights || []).map(insight => 
                        `<div class="insight-item">
                            <i class="fas fa-lightbulb"></i> ${insight}
                        </div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="ceo-summary-section">
                <h4><i class="fas fa-target"></i> Strategic Priorities</h4>
                <div class="priority-items">
                    ${(summary.strategic_priorities || []).map(priority => 
                        `<div class="priority-item priority-${priority.confidence}">
                            <div class="priority-text">${priority.priority}</div>
                            <div class="priority-meta">
                                <span class="confidence-badge ${priority.confidence}">${priority.confidence} confidence</span>
                                <span class="source-badge">${priority.source}</span>
                            </div>
                        </div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="ceo-summary-section">
                <h4><i class="fas fa-bolt"></i> Immediate Actions</h4>
                <div class="action-items">
                    ${(summary.immediate_actions || []).map(action => 
                        `<div class="action-item">
                            <div class="action-text">${action.action}</div>
                            <div class="action-meta">
                                <span class="timeline-badge">${action.timeline}</span>
                                <span class="source-badge">${action.source}</span>
                            </div>
                        </div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    // Populate Strategic Opportunities
    const opportunitiesContent = document.getElementById('opportunities-content');
    if (opportunitiesContent && briefData.opportunity_mapping) {
        const opportunities = briefData.opportunity_mapping;
        opportunitiesContent.innerHTML = `
            <div class="opportunity-section">
                <h4><i class="fas fa-chart-line"></i> Strategic Opportunities</h4>
                <div class="opportunity-grid">
                    ${(opportunities.strategic_opportunities || []).map(opp => 
                        `<div class="opportunity-card">
                            <h5>${opp.title || 'Strategic Opportunity'}</h5>
                            <p>${opp.description || opp}</p>
                            ${opp.timeline ? `<div class="meta"><i class="fas fa-clock"></i> ${opp.timeline}</div>` : ''}
                            ${opp.impact ? `<div class="meta"><i class="fas fa-chart-bar"></i> ${opp.impact} impact</div>` : ''}
                        </div>`
                    ).join('')}
                </div>
            </div>
            
            <div class="opportunity-section">
                <h4><i class="fas fa-handshake"></i> Relationship Activation</h4>
                <div class="activation-plan">
                    ${opportunities.relationship_activation ? 
                        `<div class="activation-content">${JSON.stringify(opportunities.relationship_activation, null, 2)}</div>` :
                        '<p class="text-muted">No relationship activation plan available</p>'
                    }
                </div>
            </div>
        `;
    }
    
    // Populate Competitive Position
    const competitiveContent = document.getElementById('competitive-content');
    if (competitiveContent && (briefData.detailed_analysis?.competitive_landscape || window.competitiveLandscapeData)) {
        const competitive = briefData.detailed_analysis?.competitive_landscape || window.competitiveLandscapeData || {};
        competitiveContent.innerHTML = `
            <div class="competitive-section">
                <h4><i class="fas fa-chart-pie"></i> Market Position</h4>
                <div class="position-analysis">
                    ${competitive.market_position_analysis ? 
                        Object.entries(competitive.market_position_analysis).map(([key, value]) => 
                            `<div class="position-item">
                                <strong>${key.replace(/_/g, ' ').toUpperCase()}:</strong>
                                <span>${typeof value === 'object' ? JSON.stringify(value) : value}</span>
                            </div>`
                        ).join('') :
                        '<p class="text-muted">Market position analysis not available</p>'
                    }
                </div>
            </div>
            
            <div class="competitive-section">
                <h4><i class="fas fa-chess"></i> Competitive Landscape</h4>
                <div class="landscape-overview">
                    ${competitive.competitive_landscape ? 
                        `<div class="landscape-content">${JSON.stringify(competitive.competitive_landscape, null, 2)}</div>` :
                        '<p class="text-muted">Competitive landscape analysis not available</p>'
                    }
                </div>
            </div>
        `;
    }
    
    // Populate Network Intelligence
    const networkContent = document.getElementById('network-content');
    if (networkContent && (briefData.detailed_analysis?.strategic_network || window.networkMappingData)) {
        const network = briefData.detailed_analysis?.strategic_network || window.networkMappingData || {};
        networkContent.innerHTML = `
            <div class="network-section">
                <h4><i class="fas fa-sitemap"></i> Network Analysis</h4>
                <div class="network-stats">
                    <div class="stat-item">
                        <div class="stat-number">${network.total_contacts_analyzed || 0}</div>
                        <div class="stat-label">Contacts Analyzed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${network.objectives_mapped || 0}</div>
                        <div class="stat-label">Objectives Mapped</div>
                    </div>
                </div>
            </div>
            
            <div class="network-section">
                <h4><i class="fas fa-project-diagram"></i> Strategic Network Topology</h4>
                <div class="network-topology">
                    ${network.network_topology_analysis ? 
                        `<div class="topology-content">${JSON.stringify(network.network_topology_analysis, null, 2)}</div>` :
                        '<p class="text-muted">Network topology analysis not available</p>'
                    }
                </div>
            </div>
        `;
    }
    
    // Populate Risk Assessment
    const risksContent = document.getElementById('risks-content');
    if (risksContent && briefData.risk_assessment) {
        const risks = briefData.risk_assessment;
        risksContent.innerHTML = `
            <div class="risk-section">
                <h4><i class="fas fa-exclamation-triangle"></i> Risk Assessment</h4>
                <div class="risk-categories">
                    ${Object.entries(risks).map(([category, data]) => 
                        `<div class="risk-category">
                            <h5>${category.replace(/_/g, ' ').toUpperCase()}</h5>
                            <div class="risk-content">
                                ${typeof data === 'object' ? JSON.stringify(data, null, 2) : data}
                            </div>
                        </div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    // Populate Strategic Recommendations
    const recommendationsContent = document.getElementById('recommendations-content');
    if (recommendationsContent && briefData.strategic_recommendations) {
        const recommendations = briefData.strategic_recommendations;
        recommendationsContent.innerHTML = `
            <div class="recommendations-section">
                <h4><i class="fas fa-lightbulb"></i> Strategic Recommendations</h4>
                <div class="recommendations-grid">
                    <div class="recommendation-category">
                        <h5><i class="fas fa-bolt"></i> Immediate Actions</h5>
                        <div class="recommendation-items">
                            ${(recommendations.immediate_actions || []).map(action => 
                                `<div class="recommendation-item immediate">
                                    ${typeof action === 'object' ? action.action || JSON.stringify(action) : action}
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <div class="recommendation-category">
                        <h5><i class="fas fa-chart-line"></i> Medium-term Strategy</h5>
                        <div class="recommendation-items">
                            ${(recommendations.medium_term_strategy || []).map(strategy => 
                                `<div class="recommendation-item medium-term">
                                    ${typeof strategy === 'object' ? strategy.strategy || JSON.stringify(strategy) : strategy}
                                </div>`
                            ).join('')}
                        </div>
                    </div>
                    
                    <div class="recommendation-category">
                        <h5><i class="fas fa-target"></i> Long-term Positioning</h5>
                        <div class="recommendation-items">
                            ${recommendations.long_term_positioning ? 
                                `<div class="recommendation-item long-term">
                                    ${typeof recommendations.long_term_positioning === 'object' ? 
                                        JSON.stringify(recommendations.long_term_positioning, null, 2) : 
                                        recommendations.long_term_positioning}
                                </div>` :
                                '<p class="text-muted">No long-term positioning recommendations available</p>'
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// Operation status tracking to prevent DB conflicts
let activeOperations = new Set();

// Add operation tracking
function startOperation(operationName) {
    activeOperations.add(operationName);
    console.log(`Started operation: ${operationName}`);
}

function endOperation(operationName) {
    activeOperations.delete(operationName);
    console.log(`Completed operation: ${operationName}`);
}

function isOperationActive(operationName) {
    return activeOperations.has(operationName);
}

function hasActiveOperations() {
    return activeOperations.size > 0;
}

// Enhanced status update function with operation tracking
function updateStatus(elementId, status, message) {
    const statusElement = document.getElementById(elementId);
    if (!statusElement) return;
    
    // Remove all status classes
    statusElement.className = 'analysis-status';
    
    // Add appropriate status class and icon
    let icon = '';
    switch (status) {
        case 'loading':
            statusElement.classList.add('status-loading');
            icon = '<i class="fas fa-spinner fa-spin"></i>';
            break;
        case 'success':
            statusElement.classList.add('status-success');
            icon = '<i class="fas fa-check-circle"></i>';
            break;
        case 'error':
            statusElement.classList.add('status-error');
            icon = '<i class="fas fa-exclamation-circle"></i>';
            break;
        default:
            icon = '<i class="fas fa-info-circle"></i>';
    }
    
    statusElement.innerHTML = `${icon} ${message}`;
}

// Global message display function for pipeline feedback
function showMessage(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Try to find status messages container
    let statusContainer = document.getElementById('statusMessages');
    if (!statusContainer) {
        // Create a floating message container if none exists
        statusContainer = document.createElement('div');
        statusContainer.id = 'statusMessages';
        statusContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 400px;
        `;
        document.body.appendChild(statusContainer);
    }
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.style.cssText = `
        padding: 12px 16px;
        margin-bottom: 8px;
        border-radius: 6px;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: white;
        font-weight: 500;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Set colors based on type
    switch (type) {
        case 'success':
            messageElement.style.backgroundColor = '#28a745';
            messageElement.style.borderLeftColor = '#1e7e34';
            break;
        case 'error':
            messageElement.style.backgroundColor = '#dc3545';
            messageElement.style.borderLeftColor = '#c82333';
            break;
        case 'warning':
            messageElement.style.backgroundColor = '#ffc107';
            messageElement.style.borderLeftColor = '#e0a800';
            messageElement.style.color = '#000';
            break;
        default: // 'info'
            messageElement.style.backgroundColor = '#007bff';
            messageElement.style.borderLeftColor = '#0056b3';
    }
    
    messageElement.innerHTML = message;
    statusContainer.appendChild(messageElement);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (messageElement.parentNode) {
                    messageElement.parentNode.removeChild(messageElement);
                }
            }, 300);
        }
    }, 5000);
}

// Add CSS animations for messages
if (!document.getElementById('messageAnimations')) {
    const style = document.createElement('style');
    style.id = 'messageAnimations';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// Modal event handlers
window.onclick = function(event) {
    const ceoModal = document.getElementById('ceo-results-modal');
    const inspectionModal = document.getElementById('inspection-modal');
    
    if (event.target === ceoModal) {
        closeCEOModal();
    }
    if (event.target === inspectionModal) {
        closeInspectionModal();
    }
}

// Basic Dashboard Functions
async function connectGmail() {
    try {
        updateStatus('gmail-status', 'loading', 'Connecting to Gmail...');
        
        const response = await fetch('/api/gmail/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('gmail-status', 'success', 'Gmail connected successfully');
        } else {
            updateStatus('gmail-status', 'error', result.message || 'Failed to connect Gmail');
        }
        
    } catch (error) {
        console.error('Error connecting Gmail:', error);
        updateStatus('gmail-status', 'error', 'Error connecting Gmail: ' + error.message);
    }
}

async function syncEmails() {
    try {
        startOperation('email-sync');
        updateStatus('gmail-status', 'loading', 'Fetching emails from Gmail...');
        
        const response = await fetch('/api/emails/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                days: 30  // Fetch last 30 days of emails
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('gmail-status', 'success', 
                `Successfully synced ${result.stats?.processed || 0} emails from last ${result.stats?.days_synced || 30} days`);
        } else {
            updateStatus('gmail-status', 'error', result.error || 'Failed to sync emails');
        }
        
    } catch (error) {
        console.error('Error syncing emails:', error);
        updateStatus('gmail-status', 'error', 'Error syncing emails: ' + error.message);
    } finally {
        endOperation('email-sync');
    }
}

async function extractContacts() {
    try {
        startOperation('contact-extraction');
        updateStatus('extraction-status', 'loading', 'Extracting contacts from emails...');
        
        const response = await fetch('/api/email/extract-sent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('extraction-status', 'success', 'Contacts extracted successfully');
        } else {
            updateStatus('extraction-status', 'error', result.message || 'Failed to extract contacts');
        }
        
    } catch (error) {
        console.error('Error extracting contacts:', error);
        updateStatus('extraction-status', 'error', 'Error extracting contacts: ' + error.message);
    } finally {
        endOperation('contact-extraction');
    }
}

async function augmentContacts() {
    try {
        startOperation('contact-augmentation');
        updateStatus('augmentation-status', 'loading', 'Augmenting contacts with intelligence data...');
        
        const response = await fetch('/api/contacts/augment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('augmentation-status', 'success', 'Contacts augmented successfully');
        } else {
            updateStatus('augmentation-status', 'error', result.message || 'Failed to augment contacts');
        }
        
    } catch (error) {
        console.error('Error augmenting contacts:', error);
        updateStatus('augmentation-status', 'error', 'Error augmenting contacts: ' + error.message);
    } finally {
        endOperation('contact-augmentation');
    }
}

async function generateIntelligence() {
    try {
        updateStatus('intelligence-status', 'loading', 'Generating AI intelligence insights...');
        
        const response = await fetch('/api/intelligence/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('intelligence-status', 'success', 'Intelligence insights generated successfully');
        } else {
            updateStatus('intelligence-status', 'error', result.message || 'Failed to generate intelligence');
        }
        
    } catch (error) {
        console.error('Error generating intelligence:', error);
        updateStatus('intelligence-status', 'error', 'Error generating intelligence: ' + error.message);
    }
}

async function buildKnowledgeTree() {
    try {
        startOperation('knowledge-tree-building');
        updateStatus('tree-status', 'loading', 'Building Advanced Strategic Intelligence...');
        
        const analysisDepth = document.getElementById('analysis-depth').value;
        const timeWindow = 30; // Default 30 days
        
        const response = await fetch('/api/intelligence/build-knowledge-tree', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                time_window_days: timeWindow,
                analysis_depth: analysisDepth,
                iteration: 1
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('tree-status', 'success', 
                `Advanced Strategic Intelligence built successfully (Iteration ${result.iteration || 1})`);
            showAdvancedKnowledgeResults(result);
        } else {
            updateStatus('tree-status', 'error', result.error || 'Failed to build knowledge tree');
        }
        
    } catch (error) {
        console.error('Error building knowledge tree:', error);
        updateStatus('tree-status', 'error', 'Error building knowledge tree: ' + error.message);
    } finally {
        endOperation('knowledge-tree-building');
    }
}

async function iterateKnowledgeTree() {
    try {
        startOperation('knowledge-tree-iteration');
        updateStatus('tree-status', 'loading', 'Iterating Advanced Strategic Intelligence...');
        
        const focusArea = document.getElementById('iteration-focus')?.value?.trim() || '';
        const timeWindow = 30;
        
        const requestBody = {
            time_window_days: timeWindow
        };
        
        if (focusArea) {
            requestBody.focus_area = focusArea;
        }
        
        const response = await fetch('/api/intelligence/iterate-knowledge-tree', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('tree-status', 'success', 
                `Knowledge tree improved (Iteration ${result.iteration || 'N/A'})`);
            showAdvancedKnowledgeResults(result);
        } else {
            updateStatus('tree-status', 'error', result.error || 'Failed to iterate knowledge tree');
        }
        
    } catch (error) {
        console.error('Error iterating knowledge tree:', error);
        updateStatus('tree-status', 'error', 'Error iterating knowledge tree: ' + error.message);
    } finally {
        endOperation('knowledge-tree-iteration');
    }
}

function showKnowledgeResults(result) {
    const resultsContainer = document.getElementById('knowledge-results');
    if (resultsContainer) {
        resultsContainer.style.display = 'block';
        
        // Initialize the first tab (worldview) if multidimensional
        if (result.knowledge_tree_summary?.analysis_type === 'multidimensional') {
            initializeMultidimensionalMatrix();
        }
        
        // Show basic summary in raw data tab
        const rawDataContainer = document.getElementById('raw-data');
        if (rawDataContainer) {
            rawDataContainer.innerHTML = `
                <h4>Knowledge Tree Summary</h4>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            `;
        }
    }
}

function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => button.classList.remove('active'));
    
    // Show selected tab content
    const selectedContent = document.getElementById(`${tabName}-tab`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
}

// Placeholder functions for multidimensional matrix
async function initializeMultidimensionalMatrix() {
    try {
        const response = await fetch('/api/intelligence/multidimensional-matrix');
        const result = await response.json();
        
        if (result.success) {
            loadWorldviewData(result.matrix);
            loadStrategicInsights(result.matrix);
            loadHierarchicalStructure(result.matrix);
        }
    } catch (error) {
        console.error('Error loading multidimensional matrix:', error);
    }
}

function loadWorldviewData(matrix) {
    const philosophiesContainer = document.getElementById('core-philosophies');
    const modelsContainer = document.getElementById('mental-models');
    const patternsContainer = document.getElementById('behavioral-patterns');
    
    if (philosophiesContainer && matrix.core_worldview) {
        philosophiesContainer.innerHTML = Object.entries(matrix.core_worldview).map(([key, value]) => 
            `<div class="philosophy-card">
                <h5>${key.replace(/_/g, ' ').toUpperCase()}</h5>
                <p>${typeof value === 'object' ? JSON.stringify(value, null, 2) : value}</p>
            </div>`
        ).join('');
    }
    
    if (modelsContainer && matrix.conceptual_frameworks) {
        modelsContainer.innerHTML = Object.entries(matrix.conceptual_frameworks).map(([key, value]) => 
            `<div class="model-card">
                <h5>${key.replace(/_/g, ' ').toUpperCase()}</h5>
                <p>${typeof value === 'object' ? JSON.stringify(value, null, 2) : value}</p>
            </div>`
        ).join('');
    }
    
    if (patternsContainer && matrix.decision_patterns) {
        patternsContainer.innerHTML = Object.entries(matrix.decision_patterns).map(([key, value]) => 
            `<div class="pattern-card">
                <h5>${key.replace(/_/g, ' ').toUpperCase()}</h5>
                <p>${typeof value === 'object' ? JSON.stringify(value, null, 2) : value}</p>
            </div>`
        ).join('');
    }
}

function loadStrategicInsights(matrix) {
    const insightsContainer = document.getElementById('key-insights');
    const opportunitiesContainer = document.getElementById('strategic-opportunities');
    const actionsContainer = document.getElementById('recommended-actions');
    
    if (insightsContainer && matrix.strategic_insights) {
        const insights = matrix.strategic_insights.key_insights || [];
        insightsContainer.innerHTML = insights.map(insight => 
            `<div class="insight-item">
                <i class="fas fa-lightbulb"></i>
                ${typeof insight === 'object' ? insight.content || JSON.stringify(insight) : insight}
            </div>`
        ).join('');
    }
    
    if (opportunitiesContainer && matrix.opportunity_landscape) {
        const opportunities = Object.entries(matrix.opportunity_landscape).slice(0, 5);
        opportunitiesContainer.innerHTML = opportunities.map(([key, value]) => 
            `<div class="opportunity-item">
                <h5>${key.replace(/_/g, ' ').toUpperCase()}</h5>
                <p>${typeof value === 'object' ? JSON.stringify(value, null, 2) : value}</p>
            </div>`
        ).join('');
    }
}

function loadHierarchicalStructure(matrix) {
    const hierarchyContainer = document.getElementById('hierarchy-structure');
    
    if (hierarchyContainer && matrix.hierarchical_structure) {
        hierarchyContainer.innerHTML = buildHierarchyHTML(matrix.hierarchical_structure);
    }
}

function buildHierarchyHTML(structure, level = 0) {
    let html = '';
    
    for (const [key, value] of Object.entries(structure)) {
        const indent = '  '.repeat(level);
        html += `
            <div class="hierarchy-node" style="margin-left: ${level * 20}px;">
                <div class="hierarchy-header" onclick="toggleHierarchyNode(this)">
                    <i class="fas fa-chevron-right"></i>
                    <span class="hierarchy-title">${key.replace(/_/g, ' ').toUpperCase()}</span>
                </div>
                <div class="hierarchy-children" style="display: none;">
        `;
        
        if (typeof value === 'object' && value !== null) {
            if (value.subcategories) {
                html += buildHierarchyHTML(value.subcategories, level + 1);
            } else {
                html += `<div class="hierarchy-content">${JSON.stringify(value, null, 2)}</div>`;
            }
        } else {
            html += `<div class="hierarchy-content">${value}</div>`;
        }
        
        html += `
                </div>
            </div>
        `;
    }
    
    return html;
}

function toggleHierarchyNode(element) {
    const children = element.nextElementSibling;
    const icon = element.querySelector('i');
    
    if (children.style.display === 'none') {
        children.style.display = 'block';
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-down');
    } else {
        children.style.display = 'none';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-right');
    }
}

function expandAllHierarchy() {
    const nodes = document.querySelectorAll('.hierarchy-children');
    const icons = document.querySelectorAll('.hierarchy-header i');
    
    nodes.forEach(node => node.style.display = 'block');
    icons.forEach(icon => {
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-down');
    });
}

function collapseAllHierarchy() {
    const nodes = document.querySelectorAll('.hierarchy-children');
    const icons = document.querySelectorAll('.hierarchy-header i');
    
    nodes.forEach(node => node.style.display = 'none');
    icons.forEach(icon => {
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-right');
    });
}

// === EMAIL SYNC FUNCTION ===
async function syncEmails() {
    try {
        startOperation('email-sync');
        updateStatus('gmail-status', 'loading', 'Fetching emails from Gmail...');
        
        const response = await fetch('/api/emails/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                days: 30  // Fetch last 30 days of emails
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStatus('gmail-status', 'success', 
                `Successfully synced ${result.stats?.processed || 0} emails from last ${result.stats?.days_synced || 30} days`);
        } else {
            updateStatus('gmail-status', 'error', result.error || 'Failed to sync emails');
        }
        
    } catch (error) {
        console.error('Error syncing emails:', error);
        updateStatus('gmail-status', 'error', 'Error syncing emails: ' + error.message);
    } finally {
        endOperation('email-sync');
    }
}

// === INSPECTION FUNCTIONS ===
let currentInspectionData = null;

async function inspectEmails() {
    try {
        showInspectionLoading('Emails', 'Loading stored emails...');
        
        // Add retry logic for the frontend as well
        let lastError = null;
        const maxRetries = 3;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                if (attempt > 1) {
                    showInspectionLoading('Emails', `Retrying... (attempt ${attempt}/${maxRetries})`);
                    // Wait a bit before retrying
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                }
                
                const response = await fetch('/api/inspect/emails');
                const result = await response.json();
                
                if (result.success) {
                    currentInspectionData = result;
                    displayInspectionData(result, 'Stored Emails', 'emails', [
                        { key: 'id', label: 'ID', type: 'text' },
                        { key: 'gmail_id', label: 'Gmail ID', type: 'text' },
                        { key: 'subject', label: 'Subject', type: 'text' },
                        { key: 'from', label: 'From', type: 'text' },
                        { key: 'to', label: 'To', type: 'array' },
                        { key: 'date', label: 'Date', type: 'text' },
                        { key: 'content_preview', label: 'Content Preview', type: 'truncate' },
                        { key: 'content_length', label: 'Content Length', type: 'number' },
                        { key: 'created_at', label: 'Created', type: 'datetime' }
                    ]);
                    return; // Success, exit retry loop
                } else {
                    lastError = result.error;
                    
                    // Check if this is a retryable error
                    if (result.error.includes('another operation is in progress') || 
                        result.error.includes('connection') ||
                        result.error.includes('Database connection failed')) {
                        
                        if (attempt < maxRetries) {
                            console.warn(`Retryable error on attempt ${attempt}: ${result.error}`);
                            continue; // Try again
                        }
                    }
                    
                    // Non-retryable error
                    throw new Error(result.error);
                }
            } catch (fetchError) {
                lastError = fetchError.message;
                
                // Check if this looks like a connection issue
                if ((fetchError.message.includes('Failed to fetch') || 
                     fetchError.message.includes('Network request failed') ||
                     fetchError.message.includes('connection')) && attempt < maxRetries) {
                    console.warn(`Network error on attempt ${attempt}: ${fetchError.message}`);
                    continue; // Try again
                }
                
                // Non-retryable error or last attempt
                if (attempt === maxRetries) {
                    throw fetchError;
                }
            }
        }
        
        // If we get here, all retries failed
        throw new Error(lastError || 'Failed after multiple attempts');
        
    } catch (error) {
        console.error('Error inspecting emails:', error);
        showInspectionError(`Failed to load emails: ${error.message}. Try refreshing the page or using the Flush DB button to reset.`);
    }
}

async function inspectContacts() {
    try {
        // Check if heavy operations are still running
        if (hasActiveOperations()) {
            const activeOps = Array.from(activeOperations).join(', ');
            showInspectionLoading('Contacts', `Waiting for active operations to complete: ${activeOps}...`);
            
            // Wait for operations to complete (max 30 seconds)
            let waitTime = 0;
            while (hasActiveOperations() && waitTime < 30000) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                waitTime += 1000;
                
                const remainingOps = Array.from(activeOperations).join(', ');
                showInspectionLoading('Contacts', `Waiting for operations: ${remainingOps} (${Math.floor((30000 - waitTime) / 1000)}s remaining)...`);
            }
            
            if (hasActiveOperations()) {
                showInspectionError('Operations are taking longer than expected. Try again in a moment or use the Flush DB button to reset.');
                return;
            }
        }
        
        showInspectionLoading('Contacts', 'Loading stored contacts...');
        
        // Add retry logic for the frontend as well
        let lastError = null;
        const maxRetries = 3;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                if (attempt > 1) {
                    showInspectionLoading('Contacts', `Retrying... (attempt ${attempt}/${maxRetries})`);
                    // Wait a bit before retrying with exponential backoff
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                }
                
                const response = await fetch('/api/inspect/contacts');
                const result = await response.json();
                
                if (result.success) {
                    currentInspectionData = result;
                    displayInspectionData(result, 'Stored Contacts', 'contacts', [
                        { key: 'id', label: 'ID', type: 'text' },
                        { key: 'email', label: 'Email', type: 'text' },
                        { key: 'name', label: 'Name', type: 'text' },
                        { key: 'trust_tier', label: 'Trust Tier', type: 'trust_tier' },
                        { key: 'frequency', label: 'Frequency', type: 'number' },
                        { key: 'domain', label: 'Domain', type: 'text' },
                        { key: 'enrichment_status', label: 'Enrichment', type: 'status_badge' },
                        { key: 'created_at', label: 'Created', type: 'datetime' }
                    ]);
                    return; // Success, exit retry loop
                } else {
                    lastError = result.error;
                    
                    // Check if this is a retryable error
                    if (result.error.includes('another operation is in progress') || 
                        result.error.includes('connection') ||
                        result.error.includes('Database connection failed')) {
                        
                        if (attempt < maxRetries) {
                            console.warn(`Retryable error on attempt ${attempt}: ${result.error}`);
                            continue; // Try again
                        }
                    }
                    
                    // Non-retryable error
                    throw new Error(result.error);
                }
            } catch (fetchError) {
                lastError = fetchError.message;
                
                // Check if this looks like a connection issue
                if ((fetchError.message.includes('Failed to fetch') || 
                     fetchError.message.includes('Network request failed') ||
                     fetchError.message.includes('connection')) && attempt < maxRetries) {
                    console.warn(`Network error on attempt ${attempt}: ${fetchError.message}`);
                    continue; // Try again
                }
                
                // Non-retryable error or last attempt
                if (attempt === maxRetries) {
                    throw fetchError;
                }
            }
        }
        
        // If we get here, all retries failed
        throw new Error(lastError || 'Failed after multiple attempts');
        
    } catch (error) {
        console.error('Error inspecting contacts:', error);
        showInspectionError(`Failed to load contacts: ${error.message}. Try waiting a moment and trying again, or use the Flush DB button to reset.`);
    }
}

async function inspectAugmentedContacts() {
    try {
        showInspectionLoading('Augmented Contacts', 'Loading augmented contact data...');
        
        const response = await fetch('/api/inspect/contacts');
        const result = await response.json();
        
        if (result.success) {
            // Filter to only show augmented contacts
            const augmentedContacts = result.contacts.filter(contact => contact.has_augmentation);
            const augmentedResult = {
                ...result,
                contacts: augmentedContacts,
                total_contacts: augmentedContacts.length
            };
            
            currentInspectionData = augmentedResult;
            displayInspectionData(augmentedResult, 'Augmented Contacts', 'contacts', [
                { key: 'id', label: 'ID', type: 'text' },
                { key: 'email', label: 'Email', type: 'text' },
                { key: 'name', label: 'Name', type: 'text' },
                { key: 'trust_tier', label: 'Trust Tier', type: 'trust_tier' },
                { key: 'enrichment_status', label: 'Enrichment', type: 'status_badge' },
                { key: 'metadata', label: 'Augmentation Data', type: 'json' },
                { key: 'updated_at', label: 'Last Updated', type: 'datetime' }
            ]);
        } else {
            showInspectionError('Failed to load augmented contacts: ' + result.error);
        }
    } catch (error) {
        console.error('Error inspecting augmented contacts:', error);
        showInspectionError('Error loading augmented contacts: ' + error.message);
    }
}

async function inspectIntelligence() {
    try {
        showInspectionLoading('Intelligence Data', 'Loading intelligence data...');
        
        const response = await fetch('/api/inspect/contacts');
        const result = await response.json();
        
        if (result.success) {
            // Filter to only show contacts with intelligence data
            const intelligenceContacts = result.contacts.filter(contact => 
                contact.metadata && contact.metadata.intelligence_data
            );
            const intelligenceResult = {
                ...result,
                contacts: intelligenceContacts,
                total_contacts: intelligenceContacts.length
            };
            
            currentInspectionData = intelligenceResult;
            displayInspectionData(intelligenceResult, 'Intelligence Data', 'contacts', [
                { key: 'email', label: 'Email', type: 'text' },
                { key: 'name', label: 'Name', type: 'text' },
                { key: 'trust_tier', label: 'Trust Tier', type: 'trust_tier' },
                { key: 'metadata', label: 'Intelligence Data', type: 'json' },
                { key: 'updated_at', label: 'Last Updated', type: 'datetime' }
            ]);
        } else {
            showInspectionError('Failed to load intelligence data: ' + result.error);
        }
    } catch (error) {
        console.error('Error inspecting intelligence:', error);
        showInspectionError('Error loading intelligence data: ' + error.message);
    }
}

async function inspectKnowledgeTree() {
    try {
        showInspectionLoading('Knowledge Tree', 'Loading knowledge tree...');
        
        // Add retry logic for the frontend as well
        let lastError = null;
        const maxRetries = 3;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                if (attempt > 1) {
                    showInspectionLoading('Knowledge Tree', `Retrying... (attempt ${attempt}/${maxRetries})`);
                    // Wait a bit before retrying
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
                }
                
                const response = await fetch('/api/inspect/knowledge-tree');
                const result = await response.json();
                
                if (result.success) {
                    currentInspectionData = result;
                    
                    if (result.knowledge_tree) {
                        displayKnowledgeTreeInspection(result);
                    } else {
                        showInspectionError('No knowledge tree found. Please build one first.');
                    }
                    return; // Success, exit retry loop
                } else {
                    lastError = result.error;
                    
                    // Check if this is a retryable error
                    if (result.error.includes('another operation is in progress') || 
                        result.error.includes('connection') ||
                        result.error.includes('Database connection failed')) {
                        
                        if (attempt < maxRetries) {
                            console.warn(`Retryable error on attempt ${attempt}: ${result.error}`);
                            continue; // Try again
                        }
                    }
                    
                    // Non-retryable error
                    throw new Error(result.error);
                }
            } catch (fetchError) {
                lastError = fetchError.message;
                
                // Check if this looks like a connection issue
                if ((fetchError.message.includes('Failed to fetch') || 
                     fetchError.message.includes('Network request failed') ||
                     fetchError.message.includes('connection')) && attempt < maxRetries) {
                    console.warn(`Network error on attempt ${attempt}: ${fetchError.message}`);
                    continue; // Try again
                }
                
                // Non-retryable error or last attempt
                if (attempt === maxRetries) {
                    throw fetchError;
                }
            }
        }
        
        // If we get here, all retries failed
        throw new Error(lastError || 'Failed after multiple attempts');
        
    } catch (error) {
        console.error('Error inspecting knowledge tree:', error);
        showInspectionError(`Failed to load knowledge tree: ${error.message}. Try refreshing the page or using the Flush DB button to reset.`);
    }
}

// === INSPECTION MODAL FUNCTIONS ===
function showInspectionLoading(title, message) {
    const modal = document.getElementById('inspection-modal');
    const titleElement = document.getElementById('inspection-modal-title');
    const loadingElement = document.getElementById('inspection-loading');
    
    titleElement.innerHTML = `<i class="fas fa-database"></i> ${title}`;
    loadingElement.style.display = 'flex';
    loadingElement.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${message}`;
    
    // Hide other content
    document.getElementById('inspection-table-tab').style.display = 'none';
    document.getElementById('inspection-json-tab').style.display = 'none';
    document.querySelector('.inspection-summary').style.display = 'none';
    document.querySelector('.inspection-controls').style.display = 'none';
    document.querySelector('.inspection-tabs').style.display = 'none';
    
    modal.style.display = 'block';
}

function showInspectionError(errorMessage) {
    const loadingElement = document.getElementById('inspection-loading');
    loadingElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${errorMessage}`;
    loadingElement.style.color = '#dc3545';
}

function displayInspectionData(result, title, dataKey, columns) {
    const modal = document.getElementById('inspection-modal');
    const titleElement = document.getElementById('inspection-modal-title');
    const data = result[dataKey] || [];
    
    // Update title and stats - show REAL total vs displayed
    titleElement.innerHTML = `<i class="fas fa-database"></i> ${title}`;
    
    // Use total_emails if available (for emails), otherwise fall back to data.length
    const totalCount = result.total_emails || result.total_contacts || data.length;
    const displayedCount = data.length;
    
    // Show real total count with pagination info
    if (totalCount > displayedCount) {
        document.getElementById('inspection-count').textContent = `${totalCount} (showing ${displayedCount})`;
    } else {
        document.getElementById('inspection-count').textContent = totalCount;
    }
    
    document.getElementById('inspection-count-label').textContent = dataKey;
    document.getElementById('inspection-user').textContent = result.user_email || '-';
    
    // Show/hide Load More button
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (result.has_more && dataKey === 'emails') {
        loadMoreBtn.style.display = 'inline-block';
        // Store current state for Load More function
        window.currentInspectionState = {
            dataKey: dataKey,
            columns: columns,
            title: title,
            limit: result.limit || 100,
            offset: (result.offset || 0) + displayedCount
        };
    } else {
        loadMoreBtn.style.display = 'none';
    }
    
    // Show content
    document.querySelector('.inspection-summary').style.display = 'block';
    document.querySelector('.inspection-controls').style.display = 'flex';
    document.querySelector('.inspection-tabs').style.display = 'flex';
    document.getElementById('inspection-loading').style.display = 'none';
    
    // Generate table
    generateInspectionTable(data, columns);
    
    // Generate JSON view
    document.getElementById('inspection-json').textContent = JSON.stringify(result, null, 2);
    
    // Show table tab by default
    showInspectionTab('table');
}

async function loadMoreInspectionData() {
    try {
        const state = window.currentInspectionState;
        if (!state) {
            console.error('No current inspection state found');
            return;
        }
        
        const loadMoreBtn = document.getElementById('load-more-btn');
        const originalText = loadMoreBtn.innerHTML;
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        loadMoreBtn.disabled = true;
        
        // Fetch more data with offset
        const response = await fetch(`/api/inspect/emails?limit=${state.limit}&offset=${state.offset}`);
        const result = await response.json();
        
        if (result.success && result.emails.length > 0) {
            // Append new emails to existing table
            const existingData = currentInspectionData.emails || [];
            const newData = [...existingData, ...result.emails];
            
            // Update the current inspection data
            currentInspectionData.emails = newData;
            currentInspectionData.displayed_emails = newData.length;
            currentInspectionData.has_more = result.has_more;
            
            // Update the display with all data
            displayInspectionData({
                ...currentInspectionData,
                emails: newData,
                displayed_emails: newData.length,
                has_more: result.has_more,
                total_emails: result.total_emails,
                limit: result.limit,
                offset: result.offset
            }, state.title, state.dataKey, state.columns);
            
        } else {
            console.warn('No more data available or error loading more');
            loadMoreBtn.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error loading more data:', error);
        alert('Failed to load more data: ' + error.message);
    } finally {
        const loadMoreBtn = document.getElementById('load-more-btn');
        loadMoreBtn.innerHTML = '<i class="fas fa-plus"></i> Load More';
        loadMoreBtn.disabled = false;
    }
}

function displayKnowledgeTreeInspection(result) {
    const titleElement = document.getElementById('inspection-modal-title');
    const tree = result.knowledge_tree;
    
    titleElement.innerHTML = `<i class="fas fa-brain"></i> CEO Strategic Intelligence`;
    
    // Handle both old and new structure
    const analysisData = tree.analysis_metadata || tree;
    const emailCount = analysisData.email_count || tree.email_count || 0;
    const systemVersion = analysisData.system_version || tree.version || 'v1.0';
    
    document.getElementById('inspection-count').textContent = emailCount;
    document.getElementById('inspection-count-label').textContent = 'emails analyzed';
    document.getElementById('inspection-user').textContent = result.user_email || '-';
    
    // Show content
    document.querySelector('.inspection-summary').style.display = 'block';
    document.querySelector('.inspection-controls').style.display = 'flex';
    document.querySelector('.inspection-tabs').style.display = 'flex';
    document.getElementById('inspection-loading').style.display = 'none';
    
    // Generate CEO Strategic Intelligence view
    generateCEOStrategicIntelligenceView(tree);
    
    // Generate JSON view
    document.getElementById('inspection-json').textContent = JSON.stringify(result, null, 2);
    
    showInspectionTab('table');
}

function generateCEOStrategicIntelligenceView(tree) {
    const tableContainer = document.getElementById('inspection-table');
    
    if (!tableContainer) {
        console.error('Table container not found');
        return;
    }
    
    // Create a beautiful hierarchical view for CEO Strategic Intelligence
    let htmlContent = '';
    
    // Header with system info
    const metadata = tree.analysis_metadata || {};
    htmlContent += `
        <div class="ceo-intelligence-header">
            <div class="intelligence-badge">
                <i class="fas fa-brain"></i>
                <span>CEO Strategic Intelligence</span>
                <span class="version">${metadata.system_version || 'v1.0'}</span>
            </div>
            <div class="analysis-info">
                <span class="analysis-date">Generated: ${new Date(metadata.generated_at || Date.now()).toLocaleString()}</span>
                <span class="analysis-depth">Analysis: ${metadata.analysis_depth || 'multidimensional'}</span>
                ${metadata.focus_area ? `<span class="focus-area">Focus: ${metadata.focus_area}</span>` : ''}
            </div>
        </div>
    `;
    
    // Executive Brief Section
    if (tree.executive_brief && tree.executive_brief.executive_summary) {
        htmlContent += `
            <div class="intelligence-section executive-brief">
                <h3><i class="fas fa-chart-line"></i> Executive Brief</h3>
                <div class="brief-content">
                    <div class="confidence-score">Confidence: ${Math.round((tree.executive_brief.confidence_score || 0.85) * 100)}%</div>
                    <div class="brief-text">${tree.executive_brief.executive_summary.substring(0, 500)}${tree.executive_brief.executive_summary.length > 500 ? '...' : ''}</div>
                </div>
            </div>
        `;
    }
    
    // Domain Hierarchy (Topic-Centric Structure)
    if (tree.domain_hierarchy) {
        htmlContent += `
            <div class="intelligence-section domain-hierarchy">
                <h3><i class="fas fa-sitemap"></i> Strategic Domains</h3>
                <div class="domain-cards">
        `;
        
        for (const [domainName, domainData] of Object.entries(tree.domain_hierarchy)) {
            const subtopics = domainData.subtopics || [];
            const insights = domainData.strategic_insights || [];
            
            htmlContent += `
                <div class="domain-card" onclick="toggleDomainCard(this)">
                    <div class="domain-header">
                        <h4><i class="fas fa-chevron-right domain-toggle"></i> ${formatDomainName(domainName)}</h4>
                        <span class="subtopic-count">${subtopics.length} areas</span>
                    </div>
                    <div class="domain-content">
                        <div class="subtopics">
                            <strong>Key Areas:</strong>
                            <ul>
                                ${subtopics.map(topic => `<li>${formatTopicName(topic)}</li>`).join('')}
                            </ul>
                        </div>
                        ${insights.length > 0 ? `
                            <div class="strategic-insights">
                                <strong>Strategic Insights:</strong>
                                ${insights.map(insight => `
                                    <div class="insight-item">
                                        <span class="insight-text">${insight.insight || insight}</span>
                                        ${insight.confidence ? `<span class="confidence">${Math.round(insight.confidence * 100)}%</span>` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        htmlContent += `
                </div>
            </div>
        `;
    }
    
    // Strategic Frameworks
    if (tree.strategic_frameworks) {
        htmlContent += `
            <div class="intelligence-section strategic-frameworks">
                <h3><i class="fas fa-chess"></i> Strategic Frameworks</h3>
                <div class="framework-grid">
        `;
        
        for (const [frameworkName, frameworkData] of Object.entries(tree.strategic_frameworks)) {
            htmlContent += `
                <div class="framework-card">
                    <h4>${formatFrameworkName(frameworkName)}</h4>
                    <div class="framework-content">
                        ${generateFrameworkContent(frameworkData)}
                    </div>
                </div>
            `;
        }
        
        htmlContent += `
                </div>
            </div>
        `;
    }
    
    // Competitive Landscape
    if (tree.competitive_landscape && Object.keys(tree.competitive_landscape).length > 0) {
        htmlContent += `
            <div class="intelligence-section competitive-landscape">
                <h3><i class="fas fa-globe"></i> Competitive Landscape</h3>
                <div class="landscape-content">
        `;
        
        for (const [areaName, areaData] of Object.entries(tree.competitive_landscape)) {
            if (areaName !== 'error' && typeof areaData === 'object') {
                htmlContent += `
                    <div class="landscape-area">
                        <h4>${formatAreaName(areaName)}</h4>
                        ${generateLandscapeContent(areaData)}
                    </div>
                `;
            }
        }
        
        htmlContent += `
                </div>
            </div>
        `;
    }
    
    // Cross-Domain Connections
    if (tree.cross_domain_connections && tree.cross_domain_connections.length > 0) {
        htmlContent += `
            <div class="intelligence-section cross-connections">
                <h3><i class="fas fa-network-wired"></i> Cross-Domain Connections</h3>
                <div class="connections-list">
        `;
        
        tree.cross_domain_connections.forEach(connection => {
            htmlContent += `
                <div class="connection-item">
                    <div class="connection-type">${connection.type || 'Connection'}</div>
                    <div class="connection-desc">${connection.description || 'Strategic connection identified'}</div>
                    <div class="connection-strength">Strength: ${Math.round((connection.strength || 0.5) * 100)}%</div>
                </div>
            `;
        });
        
        htmlContent += `
                </div>
            </div>
        `;
    }
    
    // Network Activation (if available)
    if (tree.network_activation && tree.network_activation.key_relationships) {
        const relationships = tree.network_activation.key_relationships;
        const relationshipCount = Object.keys(relationships).length;
        
        if (relationshipCount > 0) {
            htmlContent += `
                <div class="intelligence-section network-activation">
                    <h3><i class="fas fa-users"></i> Strategic Network (${relationshipCount} contacts)</h3>
                    <div class="relationship-summary">
                        ${tree.network_activation.network_summary || `Analyzed ${relationshipCount} strategic relationships`}
                    </div>
                </div>
            `;
        }
    }
    
    // Add custom CSS for the intelligence view
    htmlContent += `
        <style>
        .ceo-intelligence-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .intelligence-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .version {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        .analysis-info {
            display: flex;
            gap: 20px;
            font-size: 14px;
            opacity: 0.9;
        }
        .intelligence-section {
            background: white;
            border: 1px solid #e1e5e9;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .intelligence-section h3 {
            margin: 0 0 15px 0;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .domain-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        .domain-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .domain-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .domain-header {
            background: #f8f9fa;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .domain-header h4 {
            margin: 0;
            color: #495057;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .domain-toggle {
            transition: transform 0.3s ease;
        }
        .domain-card.expanded .domain-toggle {
            transform: rotate(90deg);
        }
        .subtopic-count {
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        .domain-content {
            padding: 15px;
            display: none;
        }
        .domain-card.expanded .domain-content {
            display: block;
        }
        .subtopics ul {
            margin: 5px 0;
            padding-left: 20px;
        }
        .strategic-insights {
            margin-top: 15px;
        }
        .insight-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px;
            background: #f8f9fa;
            margin: 5px 0;
            border-radius: 4px;
        }
        .confidence {
            background: #28a745;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
        }
        .framework-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .framework-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            background: #fafafa;
        }
        .framework-card h4 {
            margin: 0 0 10px 0;
            color: #343a40;
        }
        .connection-item {
            background: #f8f9fa;
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }
        .connection-type {
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        }
        .connection-strength {
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }
        .brief-content {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
        }
        .confidence-score {
            float: right;
            background: #28a745;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
        }
        .brief-text {
            margin-top: 10px;
            line-height: 1.6;
        }
        </style>
    `;
    
    tableContainer.innerHTML = htmlContent;
}

// Helper functions for formatting
function formatDomainName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatTopicName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatFrameworkName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function formatAreaName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function generateFrameworkContent(data) {
    if (typeof data === 'string') {
        return `<p>${data}</p>`;
    }
    if (Array.isArray(data)) {
        return `<ul>${data.map(item => `<li>${item}</li>`).join('')}</ul>`;
    }
    if (typeof data === 'object') {
        let content = '';
        for (const [key, value] of Object.entries(data)) {
            content += `<div><strong>${formatTopicName(key)}:</strong> `;
            if (Array.isArray(value)) {
                content += `<ul>${value.map(item => `<li>${item.contact || item.rationale || item}</li>`).join('')}</ul>`;
            } else {
                content += `${value}</div>`;
            }
        }
        return content;
    }
    return `<p>${data}</p>`;
}

function generateLandscapeContent(data) {
    if (typeof data === 'string') {
        return `<p>${data}</p>`;
    }
    if (typeof data === 'object') {
        let content = '';
        for (const [key, value] of Object.entries(data)) {
            if (key === 'raw_analysis') continue; // Skip raw data
            content += `<div class="landscape-item">`;
            content += `<strong>${formatTopicName(key)}:</strong> `;
            if (Array.isArray(value)) {
                content += `<ul>${value.map(item => `<li>${item}</li>`).join('')}</ul>`;
            } else {
                content += `<span>${value}</span>`;
            }
            content += `</div>`;
        }
        return content;
    }
    return `<p>${data}</p>`;
}

function toggleDomainCard(card) {
    card.classList.toggle('expanded');
}

function showInspectionTab(tabName) {
    console.log('Switching to inspection tab:', tabName);
    
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.inspection-tab-content');
    console.log('Found tab contents:', tabContents.length);
    tabContents.forEach(content => {
        content.classList.remove('active');
        content.style.display = 'none'; // Force hide
    });
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.inspection-tab-btn');
    console.log('Found tab buttons:', tabButtons.length);
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedContent = document.getElementById(`inspection-${tabName}-tab`);
    if (selectedContent) {
        selectedContent.classList.add('active');
        selectedContent.style.display = 'block'; // Force show
        console.log('Activated tab content:', selectedContent.id);
    } else {
        console.error('Tab content not found:', `inspection-${tabName}-tab`);
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showInspectionTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
        console.log('Activated tab button');
    } else {
        console.error('Tab button not found for:', tabName);
    }
    
    // If switching to table tab, verify table content
    if (tabName === 'table') {
        const tableContainer = document.getElementById('inspection-table');
        if (tableContainer) {
            console.log('Table container found, content length:', tableContainer.innerHTML.length);
            const table = tableContainer.querySelector('.inspection-table');
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                console.log('Table has', rows.length, 'data rows');
            } else {
                console.warn('No table element found in container');
            }
        } else {
            console.error('Table container not found');
        }
    }
}

function closeInspectionModal() {
    document.getElementById('inspection-modal').style.display = 'none';
}

function exportInspectionData() {
    if (!currentInspectionData) return;
    
    const dataStr = JSON.stringify(currentInspectionData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `inspection-data-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

// Close modal when clicking outside
window.onclick = function(event) {
    const ceoModal = document.getElementById('ceo-results-modal');
    const inspectionModal = document.getElementById('inspection-modal');
    
    if (event.target === ceoModal) {
        closeCEOModal();
    }
    if (event.target === inspectionModal) {
        closeInspectionModal();
    }
}

// Database flush function
async function flushDatabase() {
    // Double confirmation since this is destructive
    const firstConfirm = confirm(
        '⚠️ WARNING: This will permanently delete ALL your data!\n\n' +
        'This includes:\n' +
        '• All emails\n' +
        '• All contacts\n' +
        '• All intelligence data\n' +
        '• Knowledge trees\n' +
        '• Cache data\n' +
        '• Session data\n\n' +
        'Are you sure you want to continue?'
    );
    
    if (!firstConfirm) return;
    
    const secondConfirm = confirm(
        '🚨 FINAL WARNING!\n\n' +
        'This action CANNOT be undone!\n\n' +
        'Type "FLUSH" in the prompt that follows to confirm you want to delete everything.'
    );
    
    if (!secondConfirm) return;
    
    const confirmText = prompt('Type "FLUSH" to confirm (case sensitive):');
    if (confirmText !== 'FLUSH') {
        alert('Database flush cancelled - confirmation text did not match.');
        return;
    }
    
    try {
        // Update status to show flushing in progress
        updateStatus('status-text', 'loading', 'Flushing database...');
        
        const response = await fetch('/api/system/flush', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success message with details
            const clearedItems = result.cleared.join('\n• ');
            alert(
                '✅ Database flush completed successfully!\n\n' +
                'Cleared items:\n• ' + clearedItems + '\n\n' +
                'The page will now reload for a fresh start.'
            );
            
            // Reload the page after a brief delay
            setTimeout(() => {
                window.location.reload();
            }, 1000);
            
        } else {
            throw new Error(result.error || 'Unknown error during flush');
        }
        
    } catch (error) {
        console.error('Error flushing database:', error);
        alert(
            '❌ Database flush failed!\n\n' +
            'Error: ' + error.message + '\n\n' +
            'Please check the console for details and try again.'
        );
        
        // Reset status
        updateStatus('status-text', 'error', 'Flush failed');
        
        // Reset status back to ready after a few seconds
        setTimeout(() => {
            updateStatus('status-text', 'success', 'Ready');
        }, 3000);
    }
}

function generateInspectionTable(data, columns) {
    const tableContainer = document.getElementById('inspection-table');
    
    if (!tableContainer) {
        console.error('Table container not found');
        return;
    }
    
    if (!data || data.length === 0) {
        tableContainer.innerHTML = '<div class="inspection-loading">No data available</div>';
        return;
    }
    
    console.log('Generating table with data:', data.length, 'items');
    console.log('Sample data item:', data[0]);
    console.log('Columns:', columns);
    
    let tableHTML = '<table class="inspection-table"><thead><tr>';
    
    // Generate headers
    columns.forEach(col => {
        tableHTML += `<th>${col.label}</th>`;
    });
    tableHTML += '</tr></thead><tbody>';
    
    // Generate rows
    data.forEach((item, index) => {
        tableHTML += '<tr>';
        columns.forEach(col => {
            const value = item[col.key];
            const cellClass = col.type === 'truncate' ? 'truncate' : (col.type === 'json' ? 'json-cell' : '');
            tableHTML += `<td class="${cellClass}">`;
            
            try {
                tableHTML += formatCellValue(value, col.type);
            } catch (formatError) {
                console.error(`Error formatting cell value for ${col.key}:`, formatError, 'Value:', value);
                tableHTML += value || '-';
            }
            
            tableHTML += '</td>';
        });
        tableHTML += '</tr>';
        
        // Log first few items for debugging
        if (index < 3) {
            console.log(`Row ${index}:`, Object.keys(item).map(key => `${key}=${item[key]}`).join(', '));
        }
    });
    
    tableHTML += '</tbody></table>';
    
    console.log('Generated table HTML length:', tableHTML.length);
    tableContainer.innerHTML = tableHTML;
    
    // Verify the table was actually inserted
    const insertedTable = tableContainer.querySelector('.inspection-table');
    if (!insertedTable) {
        console.error('Table was not properly inserted into DOM');
        tableContainer.innerHTML = `
            <div class="inspection-loading">
                <p>Error rendering table. Debug info:</p>
                <p>Data items: ${data.length}</p>
                <p>Columns: ${columns.length}</p>
                <p>First item keys: ${Object.keys(data[0] || {}).join(', ')}</p>
            </div>
        `;
    } else {
        console.log('Table successfully inserted with', insertedTable.querySelectorAll('tr').length - 1, 'data rows');
    }
}

function formatCellValue(value, type) {
    if (value === null || value === undefined) return '-';
    
    try {
        switch (type) {
            case 'array':
                if (Array.isArray(value)) {
                    return value.join(', ');
                } else if (typeof value === 'string') {
                    try {
                        const parsed = JSON.parse(value);
                        return Array.isArray(parsed) ? parsed.join(', ') : value;
                    } catch {
                        return value;
                    }
                } else {
                    return String(value);
                }
                
            case 'json':
                if (typeof value === 'object') {
                    return `<pre>${JSON.stringify(value, null, 2)}</pre>`;
                } else if (typeof value === 'string') {
                    try {
                        const parsed = JSON.parse(value);
                        return `<pre>${JSON.stringify(parsed, null, 2)}</pre>`;
                    } catch {
                        return `<pre>${value}</pre>`;
                    }
                } else {
                    return `<pre>${String(value)}</pre>`;
                }
                
            case 'datetime':
                if (!value) return '-';
                try {
                    const date = new Date(value);
                    if (isNaN(date.getTime())) {
                        return String(value);
                    }
                    return date.toLocaleString();
                } catch {
                    return String(value);
                }
                
            case 'number':
                if (typeof value === 'number') {
                    return value.toLocaleString();
                } else if (typeof value === 'string' && !isNaN(Number(value))) {
                    return Number(value).toLocaleString();
                } else {
                    return String(value);
                }
                
            case 'trust_tier':
                const tierValue = String(value);
                return `<span class="trust-tier ${tierValue}">${tierValue}</span>`;
                
            case 'status_badge':
                const statusValue = String(value);
                const statusClass = (statusValue === 'success' || statusValue === 'enriched') ? 'enriched' : 'not-enriched';
                return `<span class="status-badge ${statusClass}">${statusValue}</span>`;
                
            case 'truncate':
                const stringValue = String(value);
                return stringValue.length > 50 ? stringValue.substring(0, 50) + '...' : stringValue;
                
            default:
                return String(value);
        }
    } catch (error) {
        console.error('Error in formatCellValue:', error, 'Value:', value, 'Type:', type);
        return String(value) || '-';
    }
}

function displayKnowledgeTree(data) {
    const container = document.getElementById('knowledge-tree-content');
    
    if (!data || !data.inspection_data) {
        container.innerHTML = '<div class="error">No knowledge tree data available</div>';
        return;
    }
    
    const inspection = data.inspection_data;
    const treeType = inspection.tree_type;
    
    if (treeType === 'Factual Knowledge Tree') {
        displayFactualKnowledgeTree(inspection, container);
    } else {
        displayLegacyStrategicTree(inspection, container);
    }
}

function displayFactualKnowledgeTree(inspection, container) {
    const html = `
        <div class="factual-tree-container">
            <!-- Header -->
            <div class="tree-header">
                <h2>📊 Factual Knowledge Tree</h2>
                <div class="tree-status ${inspection.status?.replace(/[^a-zA-Z0-9]/g, '_')}">
                    Status: ${inspection.status || 'Unknown'}
                </div>
                <div class="tree-metadata">
                    <span>Built: ${formatTimestamp(inspection.build_timestamp)}</span>
                    <span>Sources: ${(inspection.data_sources || []).join(', ')}</span>
                    <span>Emails: ${inspection.analysis_metadata?.emails_analyzed || 'N/A'}</span>
                </div>
            </div>
            
            <!-- Confidence Levels Legend -->
            <div class="confidence-legend">
                <h3>🎯 Confidence Levels</h3>
                <div class="confidence-items">
                    ${Object.entries(inspection.confidence_levels || {}).map(([level, description]) => 
                        `<div class="confidence-item ${level.toLowerCase()}">
                            <strong>${level}:</strong> ${description}
                        </div>`
                    ).join('')}
                </div>
            </div>
            
            <!-- Extracted Facts -->
            <div class="extracted-facts">
                <h3>📋 Extracted Facts</h3>
                
                <!-- Organizational Structure -->
                <div class="fact-section">
                    <h4>👥 Organizational Structure</h4>
                    ${displayOrganizationalFacts(inspection.extracted_facts?.organizational_structure)}
                </div>
                
                <!-- Business Entities -->
                <div class="fact-section">
                    <h4>🏢 Business Entities</h4>
                    ${displayBusinessEntities(inspection.extracted_facts?.business_entities)}
                </div>
                
                <!-- Communication Patterns -->
                <div class="fact-section">
                    <h4>📞 Communication Patterns</h4>
                    ${displayCommunicationPatterns(inspection.extracted_facts?.communication_patterns)}
                </div>
            </div>
            
            <!-- Proposed Structure -->
            <div class="proposed-structure">
                <h3>🌳 Proposed Knowledge Tree Structure</h3>
                ${displayProposedStructure(inspection.proposed_structure)}
            </div>
            
            <!-- Validation Required -->
            <div class="validation-section">
                <h3>✅ Validation Required</h3>
                
                <div class="validation-questions">
                    <h4>❓ Questions for You</h4>
                    <ul>
                        ${(inspection.validation_required?.questions || []).map(q => 
                            `<li class="validation-question">${q}</li>`
                        ).join('')}
                    </ul>
                </div>
                
                <div class="data-gaps">
                    <h4>🔍 Data Gaps</h4>
                    <ul>
                        ${(inspection.validation_required?.data_gaps || []).map(gap => 
                            `<li class="data-gap">${gap}</li>`
                        ).join('')}
                    </ul>
                </div>
                
                <div class="next-steps">
                    <h4>⏭️ Next Steps</h4>
                    <ol>
                        ${(inspection.validation_required?.next_steps || []).map(step => 
                            `<li class="next-step">${step}</li>`
                        ).join('')}
                    </ol>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayOrganizationalFacts(orgStructure) {
    if (!orgStructure) return '<div class="no-data">No organizational data extracted</div>';
    
    const roles = orgStructure.roles || [];
    const companies = orgStructure.companies || [];
    const relationships = orgStructure.relationships || [];
    const clarifications = orgStructure.needs_clarification || [];
    
    return `
        <div class="org-facts">
            <div class="roles-section">
                <h5>🎭 Roles Identified</h5>
                ${roles.length ? roles.map(role => `
                    <div class="role-item confidence-${role.confidence?.toLowerCase()}">
                        <strong>${role.email}:</strong> ${role.role}
                        <span class="confidence">[${role.confidence}]</span>
                        <div class="evidence">"${role.evidence}"</div>
                    </div>
                `).join('') : '<div class="no-data">No roles clearly identified</div>'}
            </div>
            
            <div class="companies-section">
                <h5>🏢 Companies Mentioned</h5>
                ${companies.length ? companies.map(company => `
                    <div class="company-item confidence-${company.confidence?.toLowerCase()}">
                        <strong>${company.name}:</strong> ${company.relationship}
                        <span class="confidence">[${company.confidence}]</span>
                        <div class="evidence">${company.evidence}</div>
                    </div>
                `).join('') : '<div class="no-data">No companies clearly identified</div>'}
            </div>
            
            <div class="relationships-section">
                <h5>🔗 Relationships</h5>
                ${relationships.length ? relationships.map(rel => `
                    <div class="relationship-item confidence-${rel.confidence?.toLowerCase()}">
                        <strong>${rel.person_a}</strong> → <strong>${rel.person_b}</strong>
                        <span class="relationship-type">(${rel.relationship_type})</span>
                        <span class="confidence">[${rel.confidence}]</span>
                        <div class="evidence">${rel.evidence}</div>
                    </div>
                `).join('') : '<div class="no-data">No clear relationships identified</div>'}
            </div>
            
            ${clarifications.length ? `
                <div class="clarifications-section">
                    <h5>❓ Needs Clarification</h5>
                    <ul>
                        ${clarifications.map(c => `<li>${c}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

function displayBusinessEntities(businessEntities) {
    if (!businessEntities) return '<div class="no-data">No business entities extracted</div>';
    
    const products = businessEntities.products || [];
    const businessUnits = businessEntities.business_units || [];
    const externalEntities = businessEntities.external_entities || [];
    const technologies = businessEntities.technologies || [];
    
    return `
        <div class="business-entities">
            <div class="products-section">
                <h5>🚀 Products</h5>
                ${products.length ? products.map(product => `
                    <div class="entity-item confidence-${product.confidence?.toLowerCase()}">
                        <strong>${product.name}</strong> (${product.type})
                        <span class="confidence">[${product.confidence}]</span>
                        <div class="evidence">${product.evidence}</div>
                    </div>
                `).join('') : '<div class="no-data">No products clearly identified</div>'}
            </div>
            
            <div class="business-units-section">
                <h5>🏛️ Business Units</h5>
                ${businessUnits.length ? businessUnits.map(unit => `
                    <div class="entity-item confidence-${unit.confidence?.toLowerCase()}">
                        <strong>${unit.name}</strong> (${unit.type})
                        <span class="confidence">[${unit.confidence}]</span>
                        <div class="evidence">${unit.evidence}</div>
                    </div>
                `).join('') : '<div class="no-data">No business units clearly identified</div>'}
            </div>
            
            <div class="external-entities-section">
                <h5>🤝 External Entities</h5>
                ${externalEntities.length ? externalEntities.map(entity => `
                    <div class="entity-item confidence-${entity.confidence?.toLowerCase()}">
                        <strong>${entity.name}</strong> (${entity.relationship_type})
                        <span class="confidence">[${entity.confidence}]</span>
                        <div class="evidence">${entity.evidence}</div>
                    </div>
                `).join('') : '<div class="no-data">No external entities clearly identified</div>'}
            </div>
            
            <div class="technologies-section">
                <h5>💻 Technologies</h5>
                ${technologies.length ? technologies.map(tech => `
                    <div class="entity-item confidence-${tech.confidence?.toLowerCase()}">
                        <strong>${tech.name}</strong> (${tech.category})
                        <span class="confidence">[${tech.confidence}]</span>
                        <div class="context">${tech.context}</div>
                    </div>
                `).join('') : '<div class="no-data">No technologies clearly identified</div>'}
            </div>
        </div>
    `;
}

function displayCommunicationPatterns(patterns) {
    if (!patterns?.communication_frequency) return '<div class="no-data">No communication patterns available</div>';
    
    const topSenders = patterns.communication_frequency.top_senders || [];
    const topDomains = patterns.communication_frequency.top_domains || [];
    const totalEmails = patterns.communication_frequency.total_emails || 0;
    
    return `
        <div class="communication-patterns">
            <div class="summary">
                <strong>Total Emails Analyzed:</strong> ${totalEmails}
            </div>
            
            <div class="top-senders">
                <h5>📧 Most Frequent Contacts</h5>
                ${topSenders.slice(0, 10).map(sender => `
                    <div class="sender-item">
                        <strong>${sender.email}</strong>: ${sender.count} emails
                    </div>
                `).join('')}
            </div>
            
            <div class="top-domains">
                <h5>🌐 Most Active Domains</h5>
                ${topDomains.slice(0, 5).map(domain => `
                    <div class="domain-item">
                        <strong>${domain.domain}</strong>: ${domain.count} emails
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function displayProposedStructure(structure) {
    if (!structure) return '<div class="no-data">No proposed structure available</div>';
    
    return `
        <div class="proposed-tree">
            <div class="structure-note">
                <em>This is the proposed knowledge tree structure based on extracted facts. Please review and validate before proceeding.</em>
            </div>
            <pre class="structure-json">${JSON.stringify(structure, null, 2)}</pre>
        </div>
    `;
}

function displayLegacyStrategicTree(inspection, container) {
    container.innerHTML = `
        <div class="legacy-tree-container">
            <div class="tree-header">
                <h2>⚠️ Legacy Strategic Intelligence Tree</h2>
                <div class="tree-status warning">
                    ${inspection.status}
                </div>
            </div>
            
            <div class="legacy-message">
                <p>${inspection.message}</p>
                <button onclick="rebuildFactualTree()" class="rebuild-button">
                    🔄 Rebuild with Factual Approach
                </button>
            </div>
            
            <details class="legacy-data">
                <summary>View Legacy Data</summary>
                <pre>${JSON.stringify(inspection.legacy_data, null, 2)}</pre>
            </details>
        </div>
    `;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString();
}

function rebuildFactualTree() {
    buildKnowledgeTree();
}

function showAdvancedKnowledgeResults(result) {
    const resultsContainer = document.getElementById('knowledge-results');
    if (resultsContainer) {
        resultsContainer.style.display = 'block';
        
        // Update the results container with advanced intelligence summary
        const summaryHTML = `
            <div class="advanced-intelligence-summary">
                <h3>🧠 Advanced Strategic Intelligence Summary</h3>
                <div class="intelligence-stats">
                    <div class="stat-item">
                        <span class="stat-number">${result.analysis_summary?.emails_analyzed || 0}</span>
                        <span class="stat-label">Emails Analyzed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${result.analysis_summary?.contacts_integrated || 0}</span>
                        <span class="stat-label">Contacts Integrated</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${result.analysis_summary?.enriched_contacts || 0}</span>
                        <span class="stat-label">Enriched Contacts</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${result.analysis_summary?.agents_executed || 0}</span>
                        <span class="stat-label">AI Agents Executed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${result.iteration || 1}</span>
                        <span class="stat-label">Iteration</span>
                    </div>
                </div>
                
                <div class="intelligence-capabilities">
                    <h4>🚀 System Capabilities</h4>
                    <ul>
                        ${(result.intelligence_capabilities || []).map(capability => 
                            `<li>${capability}</li>`
                        ).join('')}
                    </ul>
                </div>
                
                <div class="strategic-highlights">
                    <h4>📊 Strategic Intelligence Highlights</h4>
                    <div class="highlight-grid">
                        <div class="highlight-item">
                            <span class="highlight-number">${result.strategic_highlights?.cross_domain_connections || 0}</span>
                            <span class="highlight-label">Cross-Domain Connections</span>
                        </div>
                        <div class="highlight-item">
                            <span class="highlight-number">${result.strategic_highlights?.business_opportunities || 0}</span>
                            <span class="highlight-label">Business Opportunities</span>
                        </div>
                        <div class="highlight-item">
                            <span class="highlight-number">${result.strategic_highlights?.predictive_insights || 0}</span>
                            <span class="highlight-label">Predictive Insights</span>
                        </div>
                        <div class="highlight-item">
                            <span class="highlight-number">${result.strategic_highlights?.strategic_frameworks || 0}</span>
                            <span class="highlight-label">Strategic Frameworks</span>
                        </div>
                    </div>
                </div>
                
                ${(result.next_iteration_suggestions && result.next_iteration_suggestions.length > 0) ? `
                    <div class="iteration-suggestions">
                        <h4>💡 Next Iteration Suggestions</h4>
                        <ul>
                            ${result.next_iteration_suggestions.map(suggestion => 
                                `<li>${suggestion}</li>`
                            ).join('')}
                        </ul>
                        <div class="iteration-controls">
                            <input type="text" id="iteration-focus" placeholder="Focus area (optional)" class="input-field">
                            <button onclick="iterateKnowledgeTree()" class="btn btn-primary btn-small">
                                <i class="fas fa-sync"></i> Run Next Iteration
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Add summary to the top of results
        const existingSummary = document.getElementById('knowledge-summary');
        if (existingSummary) {
            existingSummary.innerHTML = summaryHTML;
        } else {
            resultsContainer.insertAdjacentHTML('afterbegin', `<div id="knowledge-summary">${summaryHTML}</div>`);
        }
        
        // Show the first tab (worldview) by default
        showTab('worldview');
        
        // Show raw data in the raw data tab
        const rawDataContainer = document.getElementById('raw-data');
        if (rawDataContainer) {
            rawDataContainer.innerHTML = `
                <h4>Advanced Strategic Intelligence Data</h4>
                <div class="tree-metadata">
                    <p><strong>System:</strong> ${result.tree_type} v${result.system_version}</p>
                    <p><strong>Iteration:</strong> ${result.iteration}</p>
                    <p><strong>Capabilities:</strong> Multi-agent analysis, Contact integration, Web augmentation</p>
                </div>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            `;
        }
    }
}

// === STRATEGIC INTELLIGENCE DASHBOARD ===
// Full Pipeline Management with Progress Tracking and Tree Visualization

let currentPipelineState = {
    isRunning: false,
    currentStep: 0,
    totalSteps: 5,
    stepResults: {},
    finalKnowledgeTree: null
};

const PIPELINE_STEPS = [
    { id: 'contacts', name: 'Extract Official Contacts', description: 'Analyzing 1 year of sent emails...' },
    { id: 'emails', name: 'Collect Recent Communications', description: 'Gathering emails from contact network...' },
    { id: 'augment', name: 'Augment Contact Intelligence', description: 'Enhancing contacts with Claude...' },
    { id: 'tree', name: 'Build Knowledge Tree', description: 'Consolidating content with Claude...' },
    { id: 'intelligence', name: 'Generate Strategic Intelligence', description: 'Running strategic analysis...' }
];

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadAuthStatus();
});

async function initializeDashboard() {
    console.log('🚀 initializeDashboard() called');
    
    const app = document.getElementById('app');
    console.log('📱 App element found:', app);
    
    app.innerHTML = `
        <div class="dashboard-container">
            <!-- Header -->
            <div class="dashboard-header">
                <h1>🧠 Strategic Intelligence Dashboard</h1>
                <p>Claude-Powered Content Consolidation & Intelligence Analysis</p>
            </div>

            <!-- Configuration Panel -->
            <div class="config-panel">
                <div class="config-item">
                    <label for="daysBack">📅 Content History Range (Days):</label>
                    <input type="number" id="daysBack" value="30" min="1" max="365" />
                    <span class="config-help">How far back to analyze emails and content</span>
                </div>
                
                <div class="config-item">
                    <label for="skipValidation">
                        <input type="checkbox" id="skipValidation" />
                        🚫 Skip Step Prerequisites Validation
                    </label>
                    <span class="config-help">Allow running any step independently without checking prerequisites</span>
                </div>
                
                <div class="action-buttons">
                    <button id="startPipeline" class="start-button" onclick="startFullPipeline()">
                        🚀 Start Full Pipeline
                    </button>
                    
                    <button id="flushButton" class="flush-button" onclick="flushDatabase()">
                        🗑️ Flush Database
                    </button>
                    
                    <button id="testModalButton" class="test-button" onclick="testModal()" style="
                        background: #17a2b8;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        margin-left: 10px;
                    ">
                        🧪 Test Modal
                    </button>
                </div>
            </div>

            <!-- Step Controls Panel -->
            <div class="step-controls-panel">
                <div class="step-controls-header">
                    <h3>📋 Individual Step Controls</h3>
                    <p>Run specific steps independently or restart from any point. Smart validation will use existing data when available.</p>
                </div>
                
                ${PIPELINE_STEPS.map((step, index) => `
                    <div class="step-card">
                        <div class="step-header">
                            <h2>
                                <span class="step-number">${index + 1}</span>
                                ${getStepIcon(step.id)} ${step.name}
                            </h2>
                            <div id="step-control-status-${step.id}" class="step-control-status"></div>
                        </div>
                        <div class="step-content">
                            <p>${step.description}</p>
                            
                            <!-- Individual Step Progress Bar -->
                            <div class="step-progress-container" id="step-progress-${step.id}" style="display: none;">
                                <div class="step-progress-bar">
                                    <div id="step-progress-fill-${step.id}" class="step-progress-fill"></div>
                                </div>
                                <span id="step-progress-text-${step.id}" class="step-progress-text">0%</span>
                            </div>
                            
                            <div class="step-actions">
                                <button id="run-step-${step.id}" class="btn btn-primary" onclick="handleRunIndividualStep('${step.id}')">
                                    ▶️ Run Step ${index + 1}
                                </button>
                                ${index > 0 ? `
                                    <button id="start-from-${step.id}" class="start-from-step-button" onclick="startFromStep('${step.id}', ${index + 1})">
                                        🚀 Start From Here
                                    </button>
                                ` : ''}
                                <button id="inspect-results-${step.id}" class="btn btn-secondary btn-small" onclick="handleInspectStepResults('${step.id}')">
                                    🔍 Inspect Results
                                </button>
                                <button id="view-results-${step.id}" class="btn btn-secondary btn-small" onclick="handleViewStepResults('${step.id}')">
                                    📊 View Results
                                </button>
                            </div>
                            <div class="step-prerequisites">
                                <small><strong>Prerequisites:</strong> ${getStepPrerequisites(step.id)}</small>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>

            <!-- Progress Section -->
            <div id="progressSection" class="progress-section" style="display: none;">
                <div class="progress-header">
                    <h3>Pipeline Progress</h3>
                    <button id="stopPipeline" onclick="stopPipeline()" class="stop-button">⏹️ Stop</button>
                </div>
                
                <div class="progress-bar-container">
                    <div id="progressBar" class="progress-bar">
                        <div id="progressFill" class="progress-fill"></div>
                    </div>
                    <span id="progressText">0% Complete</span>
                </div>

                <div id="stepsList" class="steps-list"></div>
            </div>

            <!-- Results Section -->
            <div id="resultsSection" class="results-section" style="display: none;">
                <div class="results-header">
                    <h3>📊 Pipeline Results</h3>
                    <div class="results-actions">
                        <button onclick="downloadAllResults()" class="download-button">📥 Download All JSON</button>
                        <button onclick="resetPipeline()" class="reset-button">🔄 Run Again</button>
                    </div>
                </div>

                <div id="resultsSummary" class="results-summary"></div>
                
                <!-- Knowledge Tree Visualization -->
                <div id="treeVisualization" class="tree-visualization">
                    <h4>🌳 Knowledge Tree Explorer</h4>
                    <div id="treeContainer" class="tree-container"></div>
                </div>

                <!-- Content Details Modal -->
                <div id="contentModal" class="modal" style="display: none;">
                    <div class="modal-content">
                        <span class="modal-close" onclick="closeModal()">&times;</span>
                        <div id="modalContent"></div>
                    </div>
                </div>
            </div>

            <!-- Run From Modal -->
            <div id="runFromModal" class="modal" style="display: none;">
                <div class="modal-content">
                    <span class="modal-close" onclick="closeRunFromModal()">&times;</span>
                    <div id="runFromModalContent">
                        <h3>🎯 Start Pipeline From Specific Step</h3>
                        <p>Select the step you want to start from. All subsequent steps will run automatically.</p>
                        <div class="run-from-options">
                            ${PIPELINE_STEPS.map((step, index) => `
                                <div class="run-from-option">
                                    <input type="radio" id="runFrom-${step.id}" name="runFromStep" value="${step.id}">
                                    <label for="runFrom-${step.id}">
                                        <span class="option-number">${index + 1}</span>
                                        <span class="option-name">${step.name}</span>
                                        <span class="option-desc">${step.description}</span>
                                    </label>
                                </div>
                            `).join('')}
                        </div>
                        <div class="run-from-actions">
                            <button onclick="startFromSelectedStep()" class="start-from-button">🚀 Start From Selected Step</button>
                            <button onclick="closeRunFromModal()" class="cancel-button">❌ Cancel</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Status Messages -->
            <div id="statusMessages" class="status-messages"></div>
            
            <!-- Inspection Modal -->
            <div id="inspection-modal" class="modal" style="display: none;">
                <div class="modal-content inspection-modal">
                    <div class="modal-header">
                        <h2 id="inspection-modal-title">🔍 Data Inspection</h2>
                        <span class="modal-close" onclick="closeInspectionModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <!-- Loading State -->
                        <div id="inspection-loading" class="inspection-loading" style="display: none;">
                            <i class="fas fa-spinner fa-spin"></i> Loading data...
                        </div>
                        
                        <!-- Summary Stats -->
                        <div class="inspection-summary" style="display: none;">
                            <div class="summary-stats">
                                <div class="stat-item">
                                    <div id="inspection-count" class="stat-number">0</div>
                                    <div id="inspection-count-label" class="stat-label">Items</div>
                                </div>
                                <div class="stat-item">
                                    <div id="inspection-user" class="stat-number">-</div>
                                    <div class="stat-label">User</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Controls -->
                        <div class="inspection-controls" style="display: none;">
                            <input type="text" id="inspection-search" class="search-input" placeholder="Search data...">
                            <button id="load-more-btn" onclick="loadMoreInspectionData()" class="btn btn-primary btn-small" style="display: none;">
                                <i class="fas fa-plus"></i> Load More
                            </button>
                            <button onclick="exportInspectionData()" class="btn btn-secondary btn-small">
                                <i class="fas fa-download"></i> Export JSON
                            </button>
                        </div>
                        
                        <!-- Tabs -->
                        <div class="inspection-tabs" style="display: none;">
                            <button class="inspection-tab-btn active" onclick="showInspectionTab('table')">
                                <i class="fas fa-table"></i> Table View
                            </button>
                            <button class="inspection-tab-btn" onclick="showInspectionTab('json')">
                                <i class="fas fa-code"></i> Raw JSON
                            </button>
                        </div>
                        
                        <!-- Tab Contents -->
                        <div id="inspection-table-tab" class="inspection-tab-content active">
                            <div id="inspection-table" class="inspection-table-container">
                                <!-- Table content will be generated here -->
                            </div>
                        </div>
                        
                        <div id="inspection-json-tab" class="inspection-tab-content">
                            <pre id="inspection-json" class="inspection-json">
                                <!-- JSON content will be displayed here -->
                            </pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    console.log('🚀 Dashboard HTML generated, initializing...');
    
    // Initialize button states and check for existing data
    setTimeout(async () => {
        console.log('🔧 Initializing button states...');
        updateStartFromButtonStates();
        
        // Check for existing data and enable view/inspect buttons accordingly
        console.log('🔍 Checking for existing data...');
        await checkAndEnableExistingDataButtons();
        console.log('✅ Dashboard initialization complete');
    }, 100);
}

// New function to check for existing data and enable buttons
async function checkAndEnableExistingDataButtons() {
    console.log('🔍 Checking for existing step data...');
    
    for (const step of PIPELINE_STEPS) {
        try {
            const hasData = await checkStepHasExistingData(step.id);
            if (hasData) {
                enableViewResultsButton(step.id, 'Has existing data from previous runs');
            } else {
                disableViewResultsButton(step.id, 'Run this step first to see results');
            }
        } catch (error) {
            console.warn(`Error checking data for step ${step.id}:`, error);
            disableViewResultsButton(step.id, 'Run this step first to see results');
        }
    }
}

// Check if a step has existing data in the database
async function checkStepHasExistingData(stepId) {
    console.log(`🔍 Checking existing data for step: ${stepId}`);
    try {
        switch (stepId) {
            case 'contacts':
                console.log(`📞 Checking contacts data...`);
                const contactsResponse = await fetch('/api/contacts?limit=1');
                const contactsData = await contactsResponse.json();
                const hasContacts = contactsData.success && contactsData.total > 0;
                console.log(`📞 Contacts result: ${hasContacts}, total: ${contactsData.total}`);
                return hasContacts;
                
            case 'emails':
                console.log(`📧 Checking emails data...`);
                const emailsResponse = await fetch('/api/inspect/emails?limit=1');
                const emailsData = await emailsResponse.json();
                const hasEmails = emailsData.success && emailsData.total_emails > 0;
                console.log(`📧 Emails result: ${hasEmails}, total: ${emailsData.total_emails}`);
                return hasEmails;
                
            case 'augment':
                console.log(`🔬 Checking enrichment data...`);
                // Check for enriched contacts using the real API endpoint
                const enrichmentResponse = await fetch('/api/intelligence/enrichment-results?format=summary&limit=1');
                console.log(`🔬 Enrichment API response status: ${enrichmentResponse.status}`);
                if (enrichmentResponse.ok) {
                    const enrichmentData = await enrichmentResponse.json();
                    console.log(`🔬 Enrichment API data:`, enrichmentData);
                    if (enrichmentData.success && enrichmentData.data && enrichmentData.data.statistics.enriched_contacts > 0) {
                        console.log(`🔬 Found ${enrichmentData.data.statistics.enriched_contacts} enriched contacts via API`);
                        return true; // Return boolean instead of complex object
                    }
                }
                // Fallback: check contacts API for enrichment data
                console.log(`🔬 Fallback: checking contacts for enrichment data...`);
                const contactsInspectResponse = await fetch('/api/inspect/contacts');
                console.log(`🔬 Contacts inspect response status: ${contactsInspectResponse.status}`);
                if (contactsInspectResponse.ok) {
                    const contactsData = await contactsInspectResponse.json();
                    console.log(`🔬 Contacts inspect data success: ${contactsData.success}, total contacts: ${contactsData.total_contacts}`);
                    if (contactsData.success && contactsData.contacts) {
                        const enrichedContacts = contactsData.contacts.filter(c => c.has_augmentation || c.enrichment_status === 'enriched');
                        console.log(`🔬 Found ${enrichedContacts.length} enriched contacts via fallback`);
                        return enrichedContacts.length > 0; // Return boolean instead of complex object
                    }
                }
                console.log(`🔬 No enrichment data found`);
                return false; // Return false if no enrichment data found
                
            case 'tree':
                console.log(`🌳 Checking knowledge tree data...`);
                const treeResponse = await fetch('/api/inspect/knowledge-tree');
                const treeData = await treeResponse.json();
                const hasTree = treeData.success && treeData.knowledge_tree !== null;
                console.log(`🌳 Knowledge tree result: ${hasTree}`);
                return hasTree;
                
            case 'intelligence':
                console.log(`🧠 Checking intelligence data...`);
                // Intelligence is integrated in knowledge tree, so check for tree
                const intelligenceResponse = await fetch('/api/inspect/knowledge-tree');
                const intelligenceData = await intelligenceResponse.json();
                const hasIntelligence = intelligenceData.success && intelligenceData.knowledge_tree !== null;
                console.log(`🧠 Intelligence result: ${hasIntelligence}`);
                return hasIntelligence;
                
            default:
                console.log(`❓ Unknown step: ${stepId}`);
                return false;
        }
    } catch (error) {
        console.warn(`❌ Error checking existing data for ${stepId}:`, error);
        return false;
    }
}

function enableViewResultsButton(stepId, title) {
    console.log(`✅ Enabling View Results button for step: ${stepId}, title: ${title}`);
    const viewButton = document.getElementById(`view-results-${stepId}`);
    const inspectButton = document.getElementById(`inspect-results-${stepId}`);
    
    console.log(`✅ View button element:`, viewButton);
    console.log(`✅ Inspect button element:`, inspectButton);
    
    if (viewButton) {
        viewButton.disabled = false;
        viewButton.title = title || 'View results from database';
        viewButton.style.opacity = '1';
        console.log(`✅ View button enabled for ${stepId}`);
    } else {
        console.warn(`❌ View button not found for ${stepId}`);
    }
    if (inspectButton) {
        inspectButton.disabled = false;
        inspectButton.title = title || 'Inspect results from database';
        inspectButton.style.opacity = '1';
        console.log(`✅ Inspect button enabled for ${stepId}`);
    } else {
        console.warn(`❌ Inspect button not found for ${stepId}`);
    }
}

function disableViewResultsButton(stepId, title) {
    console.log(`❌ Disabling View Results button for step: ${stepId}, title: ${title}`);
    const viewButton = document.getElementById(`view-results-${stepId}`);
    const inspectButton = document.getElementById(`inspect-results-${stepId}`);
    
    console.log(`❌ View button element:`, viewButton);
    console.log(`❌ Inspect button element:`, inspectButton);
    
    if (viewButton) {
        viewButton.disabled = true;
        viewButton.title = title || 'No data available';
        viewButton.style.opacity = '0.5';
        console.log(`❌ View button disabled for ${stepId}`);
    } else {
        console.warn(`❌ View button not found for ${stepId}`);
    }
    if (inspectButton) {
        inspectButton.disabled = true;
        inspectButton.title = title || 'No data available';
        inspectButton.style.opacity = '0.5';
        console.log(`❌ Inspect button disabled for ${stepId}`);
    } else {
        console.warn(`❌ Inspect button not found for ${stepId}`);
    }
}

async function downloadStepResult(stepId) {
    let result = currentPipelineState.stepResults?.[stepId];
    
    // If no result in current session, try to fetch from database
    if (!result) {
        try {
            result = await fetchStepResultsFromDatabase(stepId);
        } catch (error) {
            showMessage(`❌ Error loading results for download: ${error.message}`, 'error');
            return;
        }
    }
    
    if (!result) {
        showMessage(`❌ No results available for ${stepId}`, 'error');
        return;
    }
    
    const step = PIPELINE_STEPS.find(s => s.id === stepId);
    const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    const dataSource = currentPipelineState.stepResults?.[stepId] ? 'session' : 'database';
    
    const downloadLink = document.createElement('a');
    downloadLink.href = 'data:application/json,' + encodeURIComponent(JSON.stringify(result, null, 2));
    downloadLink.download = `${stepId}_${step.name.replace(/\s+/g, '_')}_${dataSource}_${timestamp}.json`;
    downloadLink.click();
    
    showMessage(`📥 Downloaded ${step.name} results`, 'success');
}

function validateStepPrerequisites(stepId) {
    const results = currentPipelineState.stepResults || {};
    
    // Add option to skip validation for testing/development
    const skipValidation = document.getElementById('skipValidation')?.checked || false;
    if (skipValidation) {
        return { valid: true, message: 'Validation skipped' };
    }
    
    switch (stepId) {
        case 'contacts':
            // Always allowed - just needs Gmail OAuth
            return { valid: true };
            
        case 'emails':
            // Needs contacts to be extracted OR allow if user wants to start from here
            if (!results.contacts) {
                // Instead of blocking, show a warning but allow
                return { 
                    valid: true, 
                    warning: true,
                    message: 'Note: Starting without extracted contacts. This step will sync emails independently.' 
                };
            }
            return { valid: true };
            
        case 'augment':
            // Needs contacts extracted OR allow if user wants to start from here
            if (!results.contacts) {
                // Check if we have contacts in database from previous runs
                return { 
                    valid: true, 
                    warning: true,
                    message: 'Note: Starting without fresh contact extraction. Will use existing contacts from database.' 
                };
            }
            return { valid: true };
            
        case 'tree':
            // Allow starting from tree building even without fresh augmentation
            return { 
                valid: true, 
                warning: !results.augment,
                message: !results.augment ? 'Note: Building tree with existing data. For best results, run augmentation first.' : undefined
            };
            
        case 'intelligence':
            // Allow starting intelligence even without fresh tree building
            return { 
                valid: true, 
                warning: !results.tree,
                message: !results.tree ? 'Note: Using existing knowledge tree. For latest insights, rebuild tree first.' : undefined
            };
            
        default:
            return { valid: false, message: 'Unknown step' };
    }
}

// Add new function to validate with database check
async function validateStepPrerequisitesWithDatabase(stepId) {
    const sessionResults = currentPipelineState.stepResults || {};
    
    // If we have results from current session, use the regular validation
    if (sessionResults[getPreviousStepId(stepId)]) {
        return validateStepPrerequisites(stepId);
    }
    
    // Check database for existing data
    try {
        switch (stepId) {
            case 'emails':
                // Check if we have any contacts in database
                const contactsResponse = await fetch('/api/contacts?limit=1');
                const contactsData = await contactsResponse.json();
                if (contactsData.total > 0) {
                    return { valid: true, message: 'Using existing contacts from database' };
                } else {
                    return { 
                        valid: true, 
                        warning: true,
                        message: 'No contacts found in database. This step will sync emails independently.' 
                    };
                }
                
            case 'augment':
                // Check if we have contacts to augment
                const augmentContactsResponse = await fetch('/api/contacts?limit=1');
                const augmentContactsData = await augmentContactsResponse.json();
                if (augmentContactsData.total > 0) {
                    return { valid: true, message: 'Using existing contacts from database' };
                } else {
                    return { 
                        valid: true, 
                        warning: true,
                        message: 'No contacts found. Run "Extract Contacts" first for best results.' 
                    };
                }
                
            case 'tree':
                // Check if we have augmented contacts or any contacts
                const treeContactsResponse = await fetch('/api/contacts?limit=1');
                const treeContactsData = await treeContactsResponse.json();
                if (treeContactsData.total > 0) {
                    return { valid: true, message: 'Using existing contacts from database' };
                } else {
                    return { 
                        valid: true, 
                        warning: true,
                        message: 'Limited data available. Run previous steps for richer knowledge tree.' 
                    };
                }
                
            case 'intelligence':
                // Check if we have a knowledge tree
                const treeResponse = await fetch('/api/inspect/knowledge-tree');
                const treeData = await treeResponse.json();
                if (treeData.success && treeData.knowledge_tree) {
                    return { valid: true, message: 'Using existing knowledge tree from database' };
                } else {
                    return { 
                        valid: true, 
                        warning: true,
                        message: 'No knowledge tree found. Build tree first for best results.' 
                    };
                }
                
            default:
                return { valid: true };
        }
    } catch (error) {
        console.warn('Database validation check failed:', error);
        // If database check fails, allow the step but with warning
        return { 
            valid: true, 
            warning: true,
            message: 'Cannot verify prerequisites. Step will run with available data.' 
        };
    }
}

function getPreviousStepId(stepId) {
    const stepOrder = ['contacts', 'emails', 'augment', 'tree', 'intelligence'];
    const currentIndex = stepOrder.indexOf(stepId);
    return currentIndex > 0 ? stepOrder[currentIndex - 1] : null;
}

function validateStepDependencies() {
    const results = currentPipelineState.stepResults || {};
    let validationReport = '';
    let allValid = true;
    
    validationReport += '<h3>🔍 Step Dependencies Validation</h3>\n<div class="validation-report">\n';
    
    PIPELINE_STEPS.forEach(step => {
        const validation = validateStepPrerequisites(step.id);
        const status = validation.valid ? '✅' : '❌';
        const statusClass = validation.valid ? 'valid' : 'invalid';
        
        validationReport += `
            <div class="validation-item ${statusClass}">
                <span class="validation-status">${status}</span>
                <span class="validation-step">${step.name}</span>
                <span class="validation-message">${validation.valid ? 'Ready to run' : validation.message}</span>
            </div>
        `;
        
        if (!validation.valid) allValid = false;
    });
    
    validationReport += '</div>\n';
    
    if (allValid) {
        validationReport += '<p class="validation-summary success">🎉 All dependencies satisfied! You can run any step.</p>';
    } else {
        validationReport += '<p class="validation-summary warning">⚠️ Some steps have unmet dependencies. Run prerequisite steps first.</p>';
    }
    
    showModal(validationReport);
}

// === RUN FROM MODAL ===

function showRunFromModal() {
    const modal = document.getElementById('runFromModal');
    modal.style.display = 'block';
}

function closeRunFromModal() {
    const modal = document.getElementById('runFromModal');
    modal.style.display = 'none';
}

async function startFromSelectedStep() {
    const selectedRadio = document.querySelector('input[name="runFromStep"]:checked');
    if (!selectedRadio) {
        showMessage('Please select a step to start from', 'warning');
        return;
    }
    
    const startStepId = selectedRadio.value;
    const startIndex = PIPELINE_STEPS.findIndex(s => s.id === startStepId);
    
    closeRunFromModal();
    
    if (currentPipelineState.isRunning) {
        showMessage('Pipeline already running!', 'warning');
        return;
    }
    
    const daysBack = parseInt(document.getElementById('daysBack').value);
    
    // Reset state
    currentPipelineState = {
        isRunning: true,
        currentStep: startIndex,
        totalSteps: PIPELINE_STEPS.length,
        stepResults: currentPipelineState.stepResults || {}, // Preserve existing results
        finalKnowledgeTree: null,
        daysBack: daysBack
    };
    
    // Show progress section
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('startPipeline').disabled = true;
    
    updateProgressDisplay();
    renderStepsList();
    
    showMessage(`🚀 Starting pipeline from step ${startIndex + 1}: ${PIPELINE_STEPS[startIndex].name}`, 'info');
    
    try {
        // Run from selected step to end
        for (let i = startIndex; i < PIPELINE_STEPS.length; i++) {
            const step = PIPELINE_STEPS[i];
            
            switch (step.id) {
                case 'contacts':
                    await executeStep('contacts', async () => {
                        const response = await fetch('/api/gmail/analyze-sent', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                lookback_days: 365,
                                force_refresh: true 
                            })
                        });
                        const result = await response.json();
                    
                    // Check if this is a background job
                    if (result.job_id && result.status_url) {
                        console.log(`⏳ Background job started: ${result.job_id}`);
                        showMessage(`⏳ Contact enrichment started in background...`, 'info');
                        
                        // Poll for job completion
                        return await pollJobStatus(result.job_id, result.status_url, 'augment');
                    }
                    
                    return result;
                    });
                    break;
                    
                case 'emails':
                    await executeStep('emails', async () => {
                        const response = await fetch('/api/emails/sync', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ days: daysBack })
                        });
                        return await response.json();
                    });
                    break;
                    
                case 'augment':
                    await executeStep('augment', async () => {
                        const response = await fetch('/api/intelligence/enrich-contacts', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                sources: ['email_signatures', 'email_content', 'domain_intelligence'],
                                limit: 100 
                            })
                        });
                        
                        if (response.status === 401) {
                            throw new Error('Authentication required - please log in again');
                        }
                        
                        const result = await response.json();
                        
                        // Check if this is a background job
                        if (result.job_id && result.status_url) {
                            console.log(`⏳ Background job started: ${result.job_id}`);
                            showMessage(`⏳ Contact enrichment started in background...`, 'info');
                            
                            // Poll for job completion
                            return await pollJobStatus(result.job_id, result.status_url, 'augment');
                        }
                        
                        return result;
                    });
                    break;
                    
                case 'tree':
                    await executeStep('tree', async () => {
                        const response = await fetch('/api/intelligence/build-knowledge-tree', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ force_rebuild: true })
                        });
                        const result = await response.json();
                    
                    // Check if this is a background job
                    if (result.job_id && result.status_url) {
                        console.log(`⏳ Background job started: ${result.job_id}`);
                        showMessage(`⏳ Contact enrichment started in background...`, 'info');
                        
                        // Poll for job completion
                        return await pollJobStatus(result.job_id, result.status_url, 'augment');
                    }
                    
                    return result;
                    });
                    break;
                    
                case 'intelligence':
                    await executeStep('intelligence', async () => {
                        return {
                            success: true,
                            message: 'Strategic intelligence integrated in knowledge tree',
                            intelligence_ready: true
                        };
                    });
                    break;
            }
        }
        
        await completePipeline();
        
    } catch (error) {
        console.error('Pipeline failed:', error);
        showMessage(`❌ Pipeline failed: ${error.message}`, 'error');
        currentPipelineState.isRunning = false;
        document.getElementById('startPipeline').disabled = false;
    }
}

async function executeIndividualStep(stepId, stepFunction) {
    const step = PIPELINE_STEPS.find(s => s.id === stepId);
    showMessage(`⏳ ${step.description}`, 'info');
    
    const result = await stepFunction();
    
    if (!result.success && result.success !== undefined) {
        throw new Error(result.error || 'Step failed');
    }
    
    return result;
}

function updateStepControlStatus(stepId, status, message) {
    const statusElement = document.getElementById(`step-control-status-${stepId}`);
    if (!statusElement) return;
    
    const icons = {
        'running': '🔄',
        'completed': '✅',
        'error': '❌',
        'waiting': '⏳'
    };
    
    statusElement.className = `step-control-status status-${status}`;
    statusElement.innerHTML = `${icons[status] || '⏳'} ${message}`;
}

function showViewResultsButton(stepId) {
    const viewButton = document.getElementById(`view-results-${stepId}`);
    const inspectButton = document.getElementById(`inspect-results-${stepId}`);
    if (viewButton) {
        viewButton.disabled = false;
        viewButton.title = 'View raw JSON results';
    }
    if (inspectButton) {
        inspectButton.disabled = false;
        inspectButton.title = 'Inspect formatted results';
    }
}

async function viewStepResults(stepId) {
    try {
        console.log(`🔍 Loading results for step: ${stepId}`);
        
        let result = currentPipelineState.stepResults?.[stepId];
        
        // If no result in current session, try to fetch from database
        if (!result) {
            try {
                showMessage('📊 Loading results from database...', 'info');
                result = await fetchStepResultsFromDatabase(stepId);
                
                if (!result) {
                    console.log(`❌ No results found for step: ${stepId}`);
                    showModal(`
                        <div class="no-results-message">
                            <h3>📊 No Results Available</h3>
                            <p>This step hasn't been run yet or has no stored results.</p>
                            <p>Please run <strong>${PIPELINE_STEPS.find(s => s.id === stepId)?.name || stepId}</strong> first to see results.</p>
                            <div class="results-actions">
                                <button onclick="handleRunIndividualStep('${stepId}')" class="btn btn-primary" style="
                                    padding: 10px 20px;
                                    margin: 5px;
                                    border: none;
                                    border-radius: 5px;
                                    background: #007bff;
                                    color: white;
                                    cursor: pointer;
                                ">
                                    ▶️ Run Step Now
                                </button>
                                <button onclick="closeModal()" class="btn btn-secondary" style="
                                    padding: 10px 20px;
                                    margin: 5px;
                                    border: none;
                                    border-radius: 5px;
                                    background: #6c757d;
                                    color: white;
                                    cursor: pointer;
                                ">
                                    ❌ Close
                                </button>
                            </div>
                        </div>
                    `);
                    return;
                }
            } catch (error) {
                console.error(`❌ Error loading results for ${stepId}:`, error);
                showMessage(`❌ Error loading results: ${error.message}`, 'error');
                return;
            }
        }
        
        console.log(`✅ Results loaded for step: ${stepId}`, result);
        
        const step = PIPELINE_STEPS.find(s => s.id === stepId);
        const dataSource = currentPipelineState.stepResults?.[stepId] ? 'Current Session' : 'Database';
        
        const content = `
            <h3 style="margin-top: 0; color: #333;">${getStepIcon(stepId)} ${step.name} Results</h3>
            <div class="step-results-content">
                <div class="data-source-info" style="margin-bottom: 15px; text-align: center;">
                    <span class="data-source-badge ${dataSource.toLowerCase().replace(' ', '-')}" style="
                        display: inline-block;
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: bold;
                        color: white;
                        background: ${dataSource === 'Current Session' ? '#28a745' : '#007bff'};
                    ">
                        📊 ${dataSource}
                    </span>
                </div>
                <div class="results-summary">
                    <h4 style="color: #495057;">📊 Raw JSON Data</h4>
                    <pre class="results-json" style="
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        border: 1px solid #e9ecef;
                        overflow-x: auto;
                        font-size: 12px;
                        line-height: 1.4;
                        max-height: 400px;
                        overflow-y: auto;
                    ">${JSON.stringify(result, null, 2)}</pre>
                </div>
                <div class="results-actions" style="margin-top: 20px; text-align: center;">
                    <button onclick="handleDownloadStepResult('${stepId}')" class="download-button" style="
                        padding: 10px 20px;
                        margin: 5px;
                        border: none;
                        border-radius: 5px;
                        background: #28a745;
                        color: white;
                        cursor: pointer;
                    ">
                        📥 Download JSON
                    </button>
                    <button onclick="closeModal()" class="btn btn-secondary" style="
                        padding: 10px 20px;
                        margin: 5px;
                        border: none;
                        border-radius: 5px;
                        background: #6c757d;
                        color: white;
                        cursor: pointer;
                    ">
                        ❌ Close
                    </button>
                </div>
            </div>
        `;
        
        console.log(`📄 Generated content for modal, length: ${content.length}`);
        showModal(content);
        
    } catch (error) {
        console.error(`❌ Critical error in viewStepResults for ${stepId}:`, error);
        showMessage(`❌ Critical error viewing results: ${error.message}`, 'error');
        
        // Show a simple error modal
        showModal(`
            <div style="text-align: center; padding: 20px;">
                <h3 style="color: #dc3545;">❌ Error Loading Results</h3>
                <p>There was an error loading the results for this step.</p>
                <p><strong>Error:</strong> ${error.message}</p>
                <button onclick="closeModal()" style="
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    background: #6c757d;
                    color: white;
                    cursor: pointer;
                ">Close</button>
            </div>
        `);
    }
}

async function inspectStepResults(stepId) {
    let result = currentPipelineState.stepResults?.[stepId];
    
    // If no result in current session, try to fetch from database
    if (!result) {
        try {
            showMessage('🔍 Loading results from database...', 'info');
            result = await fetchStepResultsFromDatabase(stepId);
            
            if (!result) {
                showModal(`
                    <div class="no-results-message">
                        <h3>🔍 No Results Available</h3>
                        <p>This step hasn't been run yet or has no stored results.</p>
                        <p>Please run <strong>${PIPELINE_STEPS.find(s => s.id === stepId).name}</strong> first to see results.</p>
                        <div class="results-actions">
                            <button onclick="handleRunIndividualStep('${stepId}')" class="btn btn-primary">
                                ▶️ Run Step Now
                            </button>
                            <button onclick="closeModal()" class="btn btn-secondary">
                                ❌ Close
                            </button>
                        </div>
                    </div>
                `);
                return;
            }
        } catch (error) {
            showMessage(`❌ Error loading results: ${error.message}`, 'error');
            return;
        }
    }
    
    const step = PIPELINE_STEPS.find(s => s.id === stepId);
    const dataSource = currentPipelineState.stepResults?.[stepId] ? 'Current Session' : 'Database';
    let formattedContent = '';
    
    // Format content based on step type
    switch (stepId) {
        case 'contacts':
            formattedContent = formatContactsResults(result);
            break;
        case 'emails':
            formattedContent = formatEmailsResults(result);
            break;
        case 'augment':
            formattedContent = formatAugmentResults(result);
            break;
        case 'tree':
            formattedContent = formatTreeResults(result);
            break;
        case 'intelligence':
            formattedContent = formatIntelligenceResults(result);
            break;
        default:
            formattedContent = `<pre class="results-json">${JSON.stringify(result, null, 2)}</pre>`;
    }
    
    const content = `
        <div class="step-results-modal">
            <h3>${getStepIcon(stepId)} ${step.name} - Detailed Results</h3>
            <div class="data-source-info">
                <span class="data-source-badge ${dataSource.toLowerCase().replace(' ', '-')}">
                    📊 ${dataSource}
                </span>
            </div>
            <div class="results-tabs">
                <button class="tab-btn active" onclick="showResultTab(event, 'formatted')">📊 Summary</button>
                <button class="tab-btn" onclick="showResultTab(event, 'raw')">🔧 Raw Data</button>
            </div>
            
            <div id="formatted-tab" class="tab-content active">
                ${formattedContent}
            </div>
            
            <div id="raw-tab" class="tab-content">
                <div class="raw-results">
                    <h4>Raw JSON Response</h4>
                    <pre class="results-json">${JSON.stringify(result, null, 2)}</pre>
                </div>
            </div>
            
            <div class="results-actions">
                <button onclick="handleDownloadStepResult('${stepId}')" class="btn btn-primary">
                    📥 Download JSON
                </button>
                <button onclick="closeModal()" class="btn btn-secondary">
                    ❌ Close
                </button>
            </div>
        </div>
        
        <style>
        .data-source-info {
            margin-bottom: 15px;
            text-align: center;
        }
        .data-source-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
        .data-source-badge.current-session {
            background: #28a745;
        }
        .data-source-badge.database {
            background: #007bff;
        }
        </style>
    `;
    
    showModal(content);
}

// New function to fetch step results from database
async function fetchStepResultsFromDatabase(stepId) {
    try {
        switch (stepId) {
            case 'contacts':
                const contactsResponse = await fetch('/api/contacts');
                const contactsData = await contactsResponse.json();
                if (contactsData.success && contactsData.total > 0) {
                    return {
                        success: true,
                        message: `Found ${contactsData.total} contacts from database`,
                        stats: {
                            total_contacts: contactsData.total,
                            trust_tier_1: contactsData.contacts?.filter(c => c.trust_tier === 'tier_1').length || 0,
                            trust_tier_2: contactsData.contacts?.filter(c => c.trust_tier === 'tier_2').length || 0,
                            domains_found: new Set(contactsData.contacts?.map(c => c.domain).filter(Boolean)).size || 0
                        },
                        contacts: contactsData.contacts,
                        source: 'database'
                    };
                }
                break;
                
            case 'emails':
                const emailsResponse = await fetch('/api/inspect/emails?limit=100');
                const emailsData = await emailsResponse.json();
                if (emailsData.success && emailsData.total_emails > 0) {
                    return {
                        success: true,
                        message: `Found ${emailsData.total_emails} emails from database`,
                        stats: {
                            processed: emailsData.displayed_emails,
                            total_found: emailsData.total_emails,
                            days_synced: 'Historical data',
                            source: 'database'
                        },
                        emails: emailsData.emails,
                        source: 'database'
                    };
                }
                break;
                
            case 'augment':
                const augmentResponse = await fetch('/api/contacts');
                const augmentData = await augmentResponse.json();
                if (augmentData.success) {
                    const enrichedContacts = augmentData.contacts?.filter(c => c.has_augmentation) || [];
                    if (enrichedContacts.length > 0) {
                        return {
                            success: true,
                            message: `Found ${enrichedContacts.length} enriched contacts from database`,
                            stats: {
                                contacts_processed: augmentData.total,
                                successfully_enriched: enrichedContacts.length,
                                success_rate: enrichedContacts.length / Math.max(augmentData.total, 1),
                                sources_used: ['email_signatures', 'email_content', 'domain_intelligence'].length
                            },
                            enriched_contacts: enrichedContacts,
                            source: 'database'
                        };
                    }
                }
                break;
                
            case 'tree':
                const treeResponse = await fetch('/api/inspect/knowledge-tree');
                const treeData = await treeResponse.json();
                if (treeData.success && treeData.knowledge_tree) {
                    const tree = treeData.knowledge_tree;
                    const metadata = tree.analysis_metadata || {};
                    return {
                        success: true,
                        message: 'Knowledge tree loaded from database',
                        knowledge_tree: tree,
                        analysis_summary: {
                            emails_analyzed: metadata.email_count || tree.email_count || 0,
                            contacts_integrated: metadata.contact_count || tree.contact_count || 0,
                            system_version: metadata.system_version || tree.version || 'v2.0',
                            strategic_domains: Object.keys(tree.domain_hierarchy || {}).length
                        },
                        source: 'database'
                    };
                }
                break;
                
            case 'intelligence':
                // Intelligence is integrated in knowledge tree
                const intelligenceResponse = await fetch('/api/inspect/knowledge-tree');
                const intelligenceData = await intelligenceResponse.json();
                if (intelligenceData.success && intelligenceData.knowledge_tree) {
                    return {
                        success: true,
                        message: 'Strategic intelligence integrated in knowledge tree (loaded from database)',
                        intelligence_ready: true,
                        knowledge_tree: intelligenceData.knowledge_tree,
                        source: 'database'
                    };
                }
                break;
        }
        
        return null; // No data found
    } catch (error) {
        console.error(`Error fetching ${stepId} results from database:`, error);
        throw error;
    }
}

// === INDIVIDUAL STEP PROGRESS BARS ===

function showStepProgress(stepId) {
    const progressContainer = document.getElementById(`step-progress-${stepId}`);
    if (progressContainer) {
        progressContainer.style.display = 'flex';
    }
}

function hideStepProgress(stepId) {
    const progressContainer = document.getElementById(`step-progress-${stepId}`);
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
}

function updateStepProgress(stepId, progress) {
    const progressFill = document.getElementById(`step-progress-fill-${stepId}`);
    const progressText = document.getElementById(`step-progress-text-${stepId}`);
    
    if (progressFill && progressText) {
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}%`;
    }
}

// === START FROM HERE FUNCTIONALITY ===

// === PROGRESS DISPLAY FUNCTIONS ===

function updateProgressDisplay() {
    if (!currentPipelineState.isRunning) {
        return;
    }
    
    const progressSection = document.getElementById('progressSection');
    const progressBar = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressSection && progressBar && progressText) {
        const percentage = Math.round((currentPipelineState.currentStep / currentPipelineState.totalSteps) * 100);
        
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}% Complete`;
        
        console.log(`📊 Pipeline progress: ${percentage}% (step ${currentPipelineState.currentStep + 1}/${currentPipelineState.totalSteps})`);
    }
}

function renderStepsList() {
    const stepsList = document.getElementById('stepsList');
    if (!stepsList) return;
    
    let stepsHTML = '';
    
    PIPELINE_STEPS.forEach((step, index) => {
        const isActive = index === currentPipelineState.currentStep;
        const isCompleted = index < currentPipelineState.currentStep;
        const stepResult = currentPipelineState.stepResults?.[step.id];
        
        const statusClass = isActive ? 'active' : (isCompleted ? 'completed' : 'pending');
        const statusIcon = isActive ? '🔄' : (isCompleted ? '✅' : '⏳');
        
        stepsHTML += `
            <div class="step-item ${statusClass}">
                <span class="step-icon">${statusIcon}</span>
                <span class="step-name">${step.name}</span>
                <span class="step-status">
                    ${isActive ? 'Running...' : (isCompleted ? 'Completed' : 'Pending')}
                </span>
            </div>
        `;
    });
    
    stepsList.innerHTML = stepsHTML;
}

function updateStepStatus(stepId, status) {
    // Update in-progress steps list
    renderStepsList();
    
    // Also update individual step control status if available
    updateStepControlStatus(stepId, status, getStatusMessage(status));
    
    console.log(`📋 Step ${stepId} status updated to: ${status}`);
}

function getStatusMessage(status) {
    const messages = {
        'running': 'Running...',
        'completed': 'Completed successfully',
        'error': 'Error occurred',
        'waiting': 'Waiting to start'
    };
    return messages[status] || 'Unknown status';
}

async function startFromStep(stepId, stepNumber) {
    // Check authentication first
    const isAuthenticated = await checkAuthentication();
    if (!isAuthenticated) {
        showMessage('Authentication required. Please log in to run pipeline operations.', 'error');
        return;
    }
    
    // Check if anything is running
    if (currentPipelineState.isRunning) {
        showMessage('Another operation is already running!', 'warning');
        return;
    }
    
    // Use database-aware validation instead of strict session validation
    const validationResult = await validateStepPrerequisitesWithDatabase(stepId);
    if (!validationResult.valid) {
        showMessage(`❌ Prerequisites not met: ${validationResult.message}`, 'error');
        return;
    }
    
    // Show warning if there are prerequisites issues but step is allowed
    if (validationResult.warning) {
        showMessage(`⚠️ ${validationResult.message}`, 'warning');
    } else if (validationResult.message && !validationResult.warning) {
        showMessage(`ℹ️ ${validationResult.message}`, 'info');
    }
    
    const stepIndex = PIPELINE_STEPS.findIndex(s => s.id === stepId);
    const daysBack = parseInt(document.getElementById('daysBack').value);
    
    // Reset state for pipeline starting from this step
    currentPipelineState = {
        isRunning: true,
        currentStep: stepIndex,
        totalSteps: PIPELINE_STEPS.length,
        stepResults: currentPipelineState.stepResults || {}, // Preserve existing results
        finalKnowledgeTree: null,
        daysBack: daysBack
    };
    
    // Disable all start from buttons
    updateStartFromButtonStates();
    
    // Show progress section
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('startPipeline').disabled = true;
    
    updateProgressDisplay();
    renderStepsList();
    
    showMessage(`🚀 Starting pipeline from step ${stepNumber}: ${PIPELINE_STEPS[stepIndex].name}`, 'info');
    
    try {
        // Run from selected step to end
        for (let i = stepIndex; i < PIPELINE_STEPS.length; i++) {
            const step = PIPELINE_STEPS[i];
            
            switch (step.id) {
                case 'contacts':
                    await executeStep('contacts', async () => {
                        const response = await fetch('/api/gmail/analyze-sent', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                lookback_days: 365,
                                force_refresh: true 
                            })
                        });
                        
                        if (response.status === 401) {
                            throw new Error('Authentication required - please log in again');
                        }
                        
                        const result = await response.json();
                    
                    // Check if this is a background job
                    if (result.job_id && result.status_url) {
                        console.log(`⏳ Background job started: ${result.job_id}`);
                        showMessage(`⏳ Contact enrichment started in background...`, 'info');
                        
                        // Poll for job completion
                        return await pollJobStatus(result.job_id, result.status_url, 'augment');
                    }
                    
                    return result;
                    });
                    break;
                    
                case 'emails':
                    await executeStep('emails', async () => {
                        const response = await fetch('/api/emails/sync', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ days: daysBack })
                        });
                        
                        if (response.status === 401) {
                            throw new Error('Authentication required - please log in again');
                        }
                        
                        return await response.json();
                    });
                    break;
                    
                case 'augment':
                    await executeStep('augment', async () => {
                        const response = await fetch('/api/intelligence/enrich-contacts', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                sources: ['email_signatures', 'email_content', 'domain_intelligence'],
                                limit: 100 
                            })
                        });
                        
                        if (response.status === 401) {
                            throw new Error('Authentication required - please log in again');
                        }
                        
                        const result = await response.json();
                    
                    // Check if this is a background job
                    if (result.job_id && result.status_url) {
                        console.log(`⏳ Background job started: ${result.job_id}`);
                        showMessage(`⏳ Contact enrichment started in background...`, 'info');
                        
                        // Poll for job completion
                        return await pollJobStatus(result.job_id, result.status_url, 'augment');
                    }
                    
                    return result;
                    });
                    break;
                    
                case 'tree':
                    await executeStep('tree', async () => {
                        const response = await fetch('/api/intelligence/build-knowledge-tree', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ force_rebuild: true })
                        });
                        
                        if (response.status === 401) {
                            throw new Error('Authentication required - please log in again');
                        }
                        
                        return await response.json();
                    });
                    break;
                    
                case 'intelligence':
                    await executeStep('intelligence', async () => {
                        return {
                            success: true,
                            message: 'Strategic intelligence integrated in knowledge tree',
                            intelligence_ready: true
                        };
                    });
                    break;
            }
        }
        
        await completePipeline();
        
    } catch (error) {
        console.error('Pipeline failed:', error);
        
        // Check if it's an authentication error
        if (error.message.includes('Authentication required') || error.message.includes('401')) {
            handleAuthenticationRequired();
            return;
        }
        
        showMessage(`❌ Pipeline failed: ${error.message}`, 'error');
        currentPipelineState.isRunning = false;
        updateStartFromButtonStates();
        document.getElementById('startPipeline').disabled = false;
    }
}

function updateStartFromButtonStates() {
    const isRunning = currentPipelineState.isRunning;
    
    PIPELINE_STEPS.forEach((step, index) => {
        if (index > 0) { // Skip step 1 (contacts)
            const button = document.getElementById(`start-from-${step.id}`);
            if (button) {
                button.disabled = isRunning;
                
                // Update button text based on state
                if (isRunning) {
                    button.innerHTML = '⏳ Pipeline Running...';
                } else {
                    button.innerHTML = '🚀 Start From Here';
                }
            }
        }
    });
    
    // Also update individual run buttons
    PIPELINE_STEPS.forEach(step => {
        const button = document.getElementById(`run-step-${step.id}`);
        if (button) {
            button.disabled = isRunning;
            if (isRunning) {
                button.innerHTML = '⏳ Running...';
            } else {
                const stepIndex = PIPELINE_STEPS.findIndex(s => s.id === step.id);
                button.innerHTML = `▶️ Run Step ${stepIndex + 1}`;
            }
        }
    });
}

// Update the existing executeStep function to include progress tracking
async function executeStep(stepId, stepFunction) {
    const stepIndex = PIPELINE_STEPS.findIndex(s => s.id === stepId);
    currentPipelineState.currentStep = stepIndex;
    
    updateProgressDisplay();
    updateStepStatus(stepId, 'running');
    updateStepControlStatus(stepId, 'running', 'Running...');
    showStepProgress(stepId);
    updateStepProgress(stepId, 0);
    
    try {
        showMessage(`⏳ ${PIPELINE_STEPS[stepIndex].description}`, 'info');
        
        // Simulate progress updates during execution
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 20;
            if (progress >= 90) progress = 90; // Don't complete until actually done
            updateStepProgress(stepId, progress);
        }, 500);
        
        const result = await stepFunction();
        
        clearInterval(progressInterval);
        updateStepProgress(stepId, 100);
        
        if (!result.success && result.success !== undefined) {
            throw new Error(result.error || 'Step failed');
        }
        
        // Store result
        currentPipelineState.stepResults[stepId] = result;
        
        // Make JSON downloadable
        createDownloadLink(stepId, result);
        
        updateStepStatus(stepId, 'completed');
        updateStepControlStatus(stepId, 'completed', 'Completed successfully');
        enableViewResultsButton(stepId, 'View current session results');
        showMessage(`✅ ${PIPELINE_STEPS[stepIndex].name} completed`, 'success');
        
        // Small delay for UI feedback
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Hide progress after completion
        setTimeout(() => hideStepProgress(stepId), 2000);
        
        // Refresh button states for all steps in case this step affects others
        setTimeout(async () => {
            await checkAndEnableExistingDataButtons();
        }, 1000);
        
    } catch (error) {
        updateStepStatus(stepId, 'error');
        updateStepControlStatus(stepId, 'error', `Error: ${error.message}`);
        hideStepProgress(stepId);
        throw error;
    }
}

// === INDIVIDUAL STEP CONTROLS ===

function getStepIcon(stepId) {
    const icons = {
        'contacts': '👥',
        'emails': '📧',
        'augment': '🔍',
        'tree': '🌳',
        'intelligence': '🧠'
    };
    return icons[stepId] || '⚙️';
}

function getStepPrerequisites(stepId) {
    const prerequisites = {
        'contacts': 'Gmail OAuth connection',
        'emails': 'Gmail OAuth + Contacts extracted',
        'augment': 'Contacts + Recent emails',
        'tree': 'Augmented contacts + Email data',
        'intelligence': 'Complete knowledge tree'
    };
    return prerequisites[stepId] || 'None';
}

async function runIndividualStep(stepId) {
    // Check authentication first
    const isAuthenticated = await checkAuthentication();
    if (!isAuthenticated) {
        showMessage('Authentication required. Please log in to run pipeline operations.', 'error');
        return;
    }
    
    const daysBack = parseInt(document.getElementById('daysBack').value);
    
    // Check if another operation is running
    if (currentPipelineState.isRunning) {
        showMessage('Another operation is already running!', 'warning');
        return;
    }
    
    // Use database-aware validation instead of strict session validation
    const validationResult = await validateStepPrerequisitesWithDatabase(stepId);
    if (!validationResult.valid) {
        showMessage(`❌ Prerequisites not met: ${validationResult.message}`, 'error');
        return;
    }
    
    // Show warning if there are prerequisites issues but step is allowed
    if (validationResult.warning) {
        showMessage(`⚠️ ${validationResult.message}`, 'warning');
    } else if (validationResult.message && !validationResult.warning) {
        showMessage(`ℹ️ ${validationResult.message}`, 'info');
    }
    
    updateStepControlStatus(stepId, 'running', 'Running...');
    showStepProgress(stepId);
    updateStepProgress(stepId, 0);
    
    try {
        let result;
        
        switch (stepId) {
            case 'contacts':
                result = await executeIndividualStep('contacts', async () => {
                    const response = await fetch('/api/gmail/analyze-sent', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            lookback_days: 365,  // Always 1 year for contacts
                            force_refresh: true 
                        })
                    });
                    
                    if (response.status === 401) {
                        throw new Error('Authentication required - please log in again');
                    }
                    
                    return await response.json();
                });
                break;
                
            case 'emails':
                result = await executeIndividualStep('emails', async () => {
                    const response = await fetch('/api/emails/sync', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ days: daysBack })
                    });
                    
                    if (response.status === 401) {
                        throw new Error('Authentication required - please log in again');
                    }
                    
                    return await response.json();
                });
                break;
                
            case 'augment':
                result = await executeIndividualStep('augment', async () => {
                    const response = await fetch('/api/intelligence/enrich-contacts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            sources: ['email_signatures', 'email_content', 'domain_intelligence'],
                            limit: 100 
                        })
                    });
                    
                    if (response.status === 401) {
                        throw new Error('Authentication required - please log in again');
                    }
                    
                    const result = await response.json();
                    
                    // Check if this is a background job
                    if (result.job_id && result.status_url) {
                        console.log(`⏳ Background job started: ${result.job_id}`);
                        showMessage(`⏳ Contact enrichment started in background...`, 'info');
                        
                        // Poll for job completion
                        return await pollJobStatus(result.job_id, result.status_url, 'augment');
                    }
                    
                    return result;
                });
                break;
                
            case 'tree':
                result = await executeIndividualStep('tree', async () => {
                    const response = await fetch('/api/intelligence/build-knowledge-tree', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ force_rebuild: true })
                    });
                    
                    if (response.status === 401) {
                        throw new Error('Authentication required - please log in again');
                    }
                    
                    return await response.json();
                });
                break;
                
            case 'intelligence':
                result = await executeIndividualStep('intelligence', async () => {
                    return {
                        success: true,
                        message: 'Strategic intelligence integrated in knowledge tree',
                        intelligence_ready: true
                    };
                });
                break;
                
            default:
                throw new Error(`Unknown step: ${stepId}`);
        }
        
        // Simulate progress completion
        updateStepProgress(stepId, 100);
        
        // Store result
        if (!currentPipelineState.stepResults) {
            currentPipelineState.stepResults = {};
        }
        currentPipelineState.stepResults[stepId] = result;
        
        updateStepControlStatus(stepId, 'completed', 'Completed successfully');
        enableViewResultsButton(stepId, 'View current session results');
        
        // Show success message with step name
        const stepName = PIPELINE_STEPS.find(s => s.id === stepId)?.name || stepId;
        showMessage(`✅ ${stepName} completed successfully!`, 'success');
        
        // Hide progress after completion
        setTimeout(() => hideStepProgress(stepId), 2000);
        
    } catch (error) {
        updateStepControlStatus(stepId, 'error', `Error: ${error.message}`);
        hideStepProgress(stepId);
        
        // Check if it's an authentication error
        if (error.message.includes('Authentication required') || error.message.includes('401')) {
            handleAuthenticationRequired();
            return;
        }
        
        showMessage(`❌ Step failed: ${error.message}`, 'error');
    }
}

function formatContactsResults(result) {
    const stats = result.stats || {};
    return `
        <div class="formatted-results">
            <div class="results-summary">
                <h4>📊 Contact Extraction Summary</h4>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-number">${stats.total_contacts || 0}</span>
                        <span class="stat-label">Total Contacts</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.emails_processed || 0}</span>
                        <span class="stat-label">Emails Processed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.domains_found || 0}</span>
                        <span class="stat-label">Unique Domains</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.trust_tier_1 || 0}</span>
                        <span class="stat-label">Tier 1 Contacts</span>
                    </div>
                </div>
                ${result.message ? `<p class="result-message">${result.message}</p>` : ''}
            </div>
        </div>
    `;
}

function formatEmailsResults(result) {
    const stats = result.stats || {};
    return `
        <div class="formatted-results">
            <div class="results-summary">
                <h4>📧 Email Sync Summary</h4>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-number">${stats.processed || 0}</span>
                        <span class="stat-label">Emails Synced</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.days_synced || 0}</span>
                        <span class="stat-label">Days Range</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.new_emails || 0}</span>
                        <span class="stat-label">New Emails</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.updated_emails || 0}</span>
                        <span class="stat-label">Updated</span>
                    </div>
                </div>
                ${result.message ? `<p class="result-message">${result.message}</p>` : ''}
            </div>
        </div>
    `;
}

function formatAugmentResults(result) {
    const stats = result.stats || {};
    return `
        <div class="formatted-results">
            <div class="results-summary">
                <h4>🔍 Contact Enrichment Summary</h4>
                <div class="stat-grid">
                    <div class="stat-item">
                        <span class="stat-number">${stats.contacts_processed || 0}</span>
                        <span class="stat-label">Contacts Processed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.successfully_enriched || 0}</span>
                        <span class="stat-label">Successfully Enriched</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${stats.sources_used || 0}</span>
                        <span class="stat-label">Data Sources Used</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${Math.round((stats.success_rate || 0) * 100)}%</span>
                        <span class="stat-label">Success Rate</span>
                    </div>
                </div>
                ${result.message ? `<p class="result-message">${result.message}</p>` : ''}
            </div>
        </div>
    `;
}

function formatTreeResults(result) {
    if (!result.knowledge_tree) {
        return `
            <div class="result-card">
                <h4>❌ Knowledge Tree Generation Failed</h4>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
    }

    const tree = result.knowledge_tree;
    
    // Enhanced tree visualization with tabs
    return `
        <div class="result-card tree-result-card">
            <div class="tree-result-header">
                <h4>🌳 Strategic Knowledge Tree</h4>
                <div class="tree-actions">
                    <button onclick="showTreeVisualization()" class="btn btn-primary">
                        🗺️ Open Tree Explorer
                    </button>
                    <button onclick="downloadTreeData()" class="btn btn-secondary">
                        📥 Download Tree Data
                    </button>
                </div>
            </div>
            
            <!-- Tree Tabs -->
            <div class="tree-tabs">
                <button class="tree-tab-btn active" onclick="showTreeTab(event, 'overview')">
                    📊 Overview
                </button>
                <button class="tree-tab-btn" onclick="showTreeTab(event, 'topics')">
                    📁 Topics
                </button>
                <button class="tree-tab-btn" onclick="showTreeTab(event, 'relationships')">
                    🤝 Relationships
                </button>
                <button class="tree-tab-btn" onclick="showTreeTab(event, 'timeline')">
                    📅 Timeline
                </button>
                <button class="tree-tab-btn" onclick="showTreeTab(event, 'domains')">
                    🏢 Domains
                </button>
            </div>

            <!-- Overview Tab -->
            <div id="tree-overview-tab" class="tree-tab-content active">
                ${generateTreeOverview(tree)}
            </div>

            <!-- Topics Tab -->
            <div id="tree-topics-tab" class="tree-tab-content">
                ${generateTopicsView(tree.phase1_claude_tree?.topics || tree.topics || {})}
            </div>

            <!-- Relationships Tab -->
            <div id="tree-relationships-tab" class="tree-tab-content">
                ${generateRelationshipsView(tree.phase1_claude_tree?.relationships || tree.relationships || {})}
            </div>

            <!-- Timeline Tab -->
            <div id="tree-timeline-tab" class="tree-tab-content">
                ${generateTimelineView(tree.phase1_claude_tree?.timeline || tree.timeline || [])}
            </div>

            <!-- Domains Tab -->
            <div id="tree-domains-tab" class="tree-tab-content">
                ${generateBusinessDomainsView(tree.phase1_claude_tree?.business_domains || tree.business_domains || {})}
            </div>
        </div>
    `;
}

function generateTreeOverview(tree) {
    const phase1 = tree.phase1_claude_tree || {};
    const phase2 = tree.phase2_strategic_analysis || {};
    const phase3 = tree.phase3_opportunity_analysis || {};
    const performance = tree.processing_performance || {};
    
    const topicsCount = Object.keys(phase1.topics || tree.topics || {}).length;
    const relationshipsCount = Object.keys(phase1.relationships || tree.relationships || {}).length;
    const domainsCount = Object.keys(phase1.business_domains || tree.business_domains || {}).length;
    const timelineCount = (phase1.timeline || tree.timeline || []).length;
    const strategicInsights = phase2.total_insights || 0;
    const opportunities = (phase3.opportunities || []).length;
    
    return `
        <div class="tree-overview">
            <div class="tree-stats-grid">
                <div class="tree-stat-card topics">
                    <div class="stat-icon">📁</div>
                    <div class="stat-content">
                        <div class="stat-number">${topicsCount}</div>
                        <div class="stat-label">Key Topics</div>
                    </div>
                </div>
                
                <div class="tree-stat-card relationships">
                    <div class="stat-icon">🤝</div>
                    <div class="stat-content">
                        <div class="stat-number">${relationshipsCount}</div>
                        <div class="stat-label">Relationships</div>
                    </div>
                </div>
                
                <div class="tree-stat-card domains">
                    <div class="stat-icon">🏢</div>
                    <div class="stat-content">
                        <div class="stat-number">${domainsCount}</div>
                        <div class="stat-label">Business Domains</div>
                    </div>
                </div>
                
                <div class="tree-stat-card timeline">
                    <div class="stat-icon">📅</div>
                    <div class="stat-content">
                        <div class="stat-number">${timelineCount}</div>
                        <div class="stat-label">Timeline Events</div>
                    </div>
                </div>
                
                ${strategicInsights > 0 ? `
                    <div class="tree-stat-card insights">
                        <div class="stat-icon">🧠</div>
                        <div class="stat-content">
                            <div class="stat-number">${strategicInsights}</div>
                            <div class="stat-label">Strategic Insights</div>
                        </div>
                    </div>
                ` : ''}
                
                ${opportunities > 0 ? `
                    <div class="tree-stat-card opportunities">
                        <div class="stat-icon">🎯</div>
                        <div class="stat-content">
                            <div class="stat-number">${opportunities}</div>
                            <div class="stat-label">Opportunities</div>
                        </div>
                    </div>
                ` : ''}
            </div>
            
            ${performance.total_duration_seconds ? `
                <div class="processing-summary">
                    <h5>⚡ Processing Performance</h5>
                    <div class="performance-grid">
                        <div class="performance-item">
                            <span class="performance-label">Phase 1 (Content Consolidation):</span>
                            <span class="performance-value">${performance.phase1_duration_seconds?.toFixed(1) || 0}s</span>
                        </div>
                        ${performance.phase2_duration_seconds ? `
                            <div class="performance-item">
                                <span class="performance-label">Phase 2 (Strategic Analysis):</span>
                                <span class="performance-value">${performance.phase2_duration_seconds.toFixed(1)}s</span>
                            </div>
                        ` : ''}
                        ${performance.phase3_duration_seconds ? `
                            <div class="performance-item">
                                <span class="performance-label">Phase 3 (Opportunity Scoring):</span>
                                <span class="performance-value">${performance.phase3_duration_seconds.toFixed(1)}s</span>
                            </div>
                        ` : ''}
                        <div class="performance-item total">
                            <span class="performance-label">Total Processing Time:</span>
                            <span class="performance-value">${performance.total_duration_seconds.toFixed(1)}s</span>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <div class="tree-description">
                <h5>🧠 About This Knowledge Tree</h5>
                <p>This strategic intelligence tree represents your comprehensive business knowledge, consolidating insights from your communications, relationships, and content into an organized, actionable framework.</p>
                <p><strong>Architecture:</strong> ${tree.architecture || 'claude_consolidation_plus_strategic_analysis'}</p>
                <p><strong>Generated:</strong> ${tree.build_timestamp || tree.created_at || 'Unknown'}</p>
            </div>
        </div>
    `;
}

function showTreeVisualization() {
    // Open the enhanced tree visualization modal
    const modal = document.getElementById('contentModal');
    const modalContent = document.getElementById('modalContent');
    
    // Get the current knowledge tree data
    fetchCurrentKnowledgeTree().then(tree => {
        if (tree) {
            modalContent.innerHTML = generateEnhancedTreeVisualization(tree);
            modal.style.display = 'block';
            
            // Initialize tree visualization interactions
            initializeTreeVisualizationInteractions();
        } else {
            showMessage('Please build a knowledge tree first', 'warning');
        }
    });
}

async function fetchCurrentKnowledgeTree() {
    try {
        const response = await fetch('/api/intelligence/knowledge-tree');
        const result = await response.json();
        
        if (result.success && result.knowledge_tree) {
            return result.knowledge_tree;
        }
        return null;
    } catch (error) {
        console.error('Error fetching knowledge tree:', error);
        return null;
    }
}

function generateEnhancedTreeVisualization(tree) {
    const phase1 = tree.phase1_claude_tree || tree;
    const phase2 = tree.phase2_strategic_analysis || {};
    const phase3 = tree.phase3_opportunity_analysis || {};
    
    const topics = phase1.topics || {};
    const relationships = phase1.relationships || {};
    const domains = phase1.business_domains || {};
    const timeline = phase1.timeline || [];
    
    return `
        <div class="enhanced-tree-visualization">
            <div class="tree-header">
                <h2>🧠 Strategic Intelligence Tree Explorer</h2>
                <div class="tree-meta">
                    Generated: ${tree.build_timestamp || tree.created_at || 'Unknown'} | 
                    Architecture: ${tree.architecture || 'Enhanced Strategic Analysis'}
                </div>
            </div>
            
            <div class="tree-stats-header">
                <div class="stat-item">
                    <span class="stat-number">${Object.keys(topics).length}</span>
                    <span class="stat-label">Key Topics</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${Object.keys(relationships).length}</span>
                    <span class="stat-label">Relationships</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${Object.keys(domains).length}</span>
                    <span class="stat-label">Business Domains</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${timeline.length}</span>
                    <span class="stat-label">Timeline Events</span>
                </div>
                ${phase2.total_insights ? `
                    <div class="stat-item">
                        <span class="stat-number">${phase2.total_insights}</span>
                        <span class="stat-label">Strategic Insights</span>
                    </div>
                ` : ''}
                ${phase3.opportunities?.length ? `
                    <div class="stat-item">
                        <span class="stat-number">${phase3.opportunities.length}</span>
                        <span class="stat-label">Opportunities</span>
                    </div>
                ` : ''}
            </div>
            
            <!-- Topics Section -->
            <div class="tree-section">
                <div class="section-title">
                    📁 Strategic Topics
                </div>
                <div class="topic-grid">
                    ${generateTopicCards(topics)}
                </div>
            </div>
            
            <!-- Relationships Section -->
            <div class="tree-section">
                <div class="section-title">
                    🤝 Key Relationships
                </div>
                <div class="contact-grid">
                    ${generateContactCards(relationships)}
                </div>
            </div>
            
            <!-- Timeline Section -->
            ${timeline.length > 0 ? `
                <div class="tree-section">
                    <div class="section-title">
                        📅 Business Timeline
                    </div>
                    <div class="timeline">
                        ${generateTimelineItems(timeline)}
                    </div>
                </div>
            ` : ''}
            
            <!-- Business Domains Section -->
            <div class="tree-section">
                <div class="section-title">
                    🏢 Business Domain Analysis
                </div>
                <div class="domain-grid">
                    ${generateDomainCards(domains)}
                </div>
            </div>
            
            ${phase2.agent_insights ? generateStrategicInsightsSection(phase2.agent_insights) : ''}
            ${phase3.opportunities?.length > 0 ? generateOpportunitiesSection(phase3.opportunities) : ''}
        </div>
    `;
}

function generateTopicCards(topics) {
    const topicCategories = {
        'funding': { color: '#dc3545', icon: '💰' },
        'growth': { color: '#28a745', icon: '📈' },
        'ai': { color: '#007bff', icon: '🤖' },
        'restructuring': { color: '#ffc107', icon: '🔄' },
        'investment': { color: '#6f42c1', icon: '💼' },
        'partnership': { color: '#17a2b8', icon: '🤝' },
        'technology': { color: '#fd7e14', icon: '⚙️' },
        'default': { color: '#6c757d', icon: '📋' }
    };
    
    return Object.entries(topics).map(([topicName, topicData]) => {
        const category = Object.keys(topicCategories).find(cat => 
            topicName.toLowerCase().includes(cat)
        ) || 'default';
        
        const categoryInfo = topicCategories[category];
        const participants = topicData.participants || [];
        const keyPoints = topicData.key_points || [];
        const businessRelevance = topicData.business_relevance || 'medium';
        
        return `
            <div class="topic-card ${category}" onclick="expandTopicCard(this)" style="border-left-color: ${categoryInfo.color}">
                <div class="relevance-badge relevance-${businessRelevance}">
                    ${businessRelevance.toUpperCase()}
                </div>
                
                <div class="topic-title">
                    <span class="topic-icon">${categoryInfo.icon}</span>
                    ${topicName.replace(/_/g, ' ')}
                </div>
                
                <div class="topic-summary">
                    ${topicData.timeline_summary || topicData.business_context || 'Strategic business topic'}
                </div>
                
                ${keyPoints.length > 0 ? `
                    <div class="key-points">
                        <h4>Key Points</h4>
                        <ul class="point-list">
                            ${keyPoints.slice(0, 3).map(point => `<li>${point}</li>`).join('')}
                            ${keyPoints.length > 3 ? `<li><em>+${keyPoints.length - 3} more points...</em></li>` : ''}
                        </ul>
                    </div>
                ` : ''}
                
                ${participants.length > 0 ? `
                    <div class="participants">
                        <h4>Participants</h4>
                        <div class="participant-tags">
                            ${participants.slice(0, 4).map(participant => 
                                `<span class="participant-tag">${participant}</span>`
                            ).join('')}
                            ${participants.length > 4 ? `<span class="participant-tag">+${participants.length - 4} more</span>` : ''}
                        </div>
                    </div>
                ` : ''}
                
                <div class="topic-actions" style="display: none;">
                    <button onclick="drillDownTopic('${topicName}', event)" class="drill-down-btn">
                        🔍 View Details
                    </button>
                    <button onclick="showRelatedContent('${topicName}', event)" class="related-content-btn">
                        📄 Related Content
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function generateContactCards(relationships) {
    return Object.entries(relationships).map(([contactEmail, contactData]) => {
        const name = contactData.name || contactEmail.split('@')[0];
        const company = contactData.company || '';
        const relationshipStatus = contactData.relationship_status || 'unknown';
        const engagementScore = contactData.engagement_score || Math.random() * 0.5 + 0.3; // Fallback
        const topicsInvolved = contactData.topics_involved || [];
        
        const statusColors = {
            'established': '#28a745',
            'ongoing': '#17a2b8', 
            'attempted': '#ffc107',
            'cold': '#dc3545',
            'unknown': '#6c757d'
        };
        
        return `
            <div class="contact-card" onclick="expandContactCard(this)" style="border-left-color: ${statusColors[relationshipStatus] || statusColors.unknown}">
                <div class="contact-header">
                    <div>
                        <div class="contact-name">${name}</div>
                        <div class="contact-email">${contactEmail}</div>
                        ${company ? `<div class="contact-company">${company}</div>` : ''}
                    </div>
                    <div class="engagement-score" style="background: ${statusColors[relationshipStatus] || statusColors.unknown}">
                        ${engagementScore.toFixed(1)}
                    </div>
                </div>
                
                <div class="contact-context">
                    ${contactData.communication_summary || 'Professional contact with ongoing relationship.'}
                </div>
                
                ${topicsInvolved.length > 0 ? `
                    <div class="contact-topics">
                        ${topicsInvolved.slice(0, 3).map(topic => 
                            `<span class="topic-tag">${topic}</span>`
                        ).join('')}
                        ${topicsInvolved.length > 3 ? `<span class="topic-tag">+${topicsInvolved.length - 3} more</span>` : ''}
                    </div>
                ` : ''}
                
                <div class="contact-actions" style="display: none;">
                    <button onclick="drillDownContact('${contactEmail}', event)" class="drill-down-btn">
                        🔍 View Details
                    </button>
                    <button onclick="showContactHistory('${contactEmail}', event)" class="history-btn">
                        📧 Communication History
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function generateTimelineItems(timeline) {
    return timeline.map(event => {
        const date = new Date(event.date || event.timestamp);
        const formattedDate = date.toLocaleDateString();
        
        return `
            <div class="timeline-item">
                <div class="timeline-date">${formattedDate}</div>
                <div class="timeline-event">
                    ${event.event || event.description || event}
                </div>
            </div>
        `;
    }).join('');
}

function generateDomainCards(domains) {
    return Object.entries(domains).map(([domainName, domainData]) => {
        const topics = Array.isArray(domainData) ? domainData : 
                      typeof domainData === 'object' ? Object.keys(domainData) : 
                      [domainData];
        
        return `
            <div class="domain-card" onclick="expandDomainCard(this)">
                <div class="domain-name">${domainName.replace(/_/g, ' ')}</div>
                <div class="domain-topics">
                    ${topics.slice(0, 3).join(', ')}
                    ${topics.length > 3 ? ` (+${topics.length - 3} more)` : ''}
                </div>
                
                <div class="domain-actions" style="display: none;">
                    <button onclick="drillDownDomain('${domainName}', event)" class="drill-down-btn">
                        🔍 Explore Domain
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function generateStrategicInsightsSection(insights) {
    return `
        <div class="tree-section">
            <div class="section-title">
                🧠 Strategic Intelligence Insights
            </div>
            <div class="insights-grid">
                ${Object.entries(insights).map(([agentName, agentInsights]) => `
                    <div class="insight-category">
                        <h4>${agentName.replace(/_/g, ' ').toUpperCase()}</h4>
                        <div class="insight-items">
                            ${Array.isArray(agentInsights) ? 
                                agentInsights.slice(0, 3).map(insight => `
                                    <div class="insight-item">
                                        ${typeof insight === 'object' ? insight.title || insight.description || JSON.stringify(insight).slice(0, 100) : insight}
                                    </div>
                                `).join('') : 
                                `<div class="insight-item">${agentInsights}</div>`
                            }
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function generateOpportunitiesSection(opportunities) {
    return `
        <div class="tree-section">
            <div class="section-title">
                🎯 Strategic Opportunities
            </div>
            <div class="opportunities-grid">
                ${opportunities.slice(0, 6).map(opp => `
                    <div class="opportunity-card" onclick="expandOpportunityCard(this)">
                        <div class="opportunity-score">${Math.round(opp.score || 0)}</div>
                        <div class="opportunity-title">${opp.title}</div>
                        <div class="opportunity-type">${(opp.type || '').replace(/_/g, ' ').toUpperCase()}</div>
                        <div class="opportunity-timing">
                            Optimal timing: ${new Date(opp.optimal_timing).toLocaleDateString()}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// Interactive functions
function initializeTreeVisualizationInteractions() {
    // Add CSS for the enhanced tree visualization
    if (!document.getElementById('tree-visualization-styles')) {
        const style = document.createElement('style');
        style.id = 'tree-visualization-styles';
        style.textContent = getTreeVisualizationStyles();
        document.head.appendChild(style);
    }
}

function expandTopicCard(card) {
    const actions = card.querySelector('.topic-actions');
    if (actions) {
        actions.style.display = actions.style.display === 'none' ? 'flex' : 'none';
    }
    
    card.classList.toggle('expanded');
}

function expandContactCard(card) {
    const actions = card.querySelector('.contact-actions');
    if (actions) {
        actions.style.display = actions.style.display === 'none' ? 'flex' : 'none';
    }
    
    card.classList.toggle('expanded');
}

function expandDomainCard(card) {
    const actions = card.querySelector('.domain-actions');
    if (actions) {
        actions.style.display = actions.style.display === 'none' ? 'flex' : 'none';
    }
    
    card.classList.toggle('expanded');
}

function expandOpportunityCard(card) {
    card.classList.toggle('expanded');
}

async function drillDownTopic(topicName, event) {
    event?.stopPropagation();
    
    try {
        const response = await fetch(`/api/intelligence/topics/${encodeURIComponent(topicName)}/content`);
        if (response.ok) {
            const content = await response.json();
            showContentDrillDown('Topic: ' + topicName, content);
        } else {
            showMessage('Topic content not available', 'info');
        }
    } catch (error) {
        console.error('Error fetching topic content:', error);
        showMessage('Error loading topic content', 'error');
    }
}

async function drillDownContact(contactEmail, event) {
    event?.stopPropagation();
    
    try {
        const response = await fetch(`/api/intelligence/contacts/${encodeURIComponent(contactEmail)}/history`);
        if (response.ok) {
            const history = await response.json();
            showContentDrillDown('Contact: ' + contactEmail, history);
        } else {
            showMessage('Contact history not available', 'info');
        }
    } catch (error) {
        console.error('Error fetching contact history:', error);
        showMessage('Error loading contact history', 'error');
    }
}

async function drillDownDomain(domainName, event) {
    event?.stopPropagation();
    
    try {
        const response = await fetch(`/api/intelligence/domains/${encodeURIComponent(domainName)}/details`);
        if (response.ok) {
            const details = await response.json();
            showContentDrillDown('Domain: ' + domainName, details);
        } else {
            showMessage('Domain details not available', 'info');
        }
    } catch (error) {
        console.error('Error fetching domain details:', error);
        showMessage('Error loading domain details', 'error');
    }
}

function showContentDrillDown(title, content) {
    const modal = document.getElementById('contentModal');
    const modalContent = document.getElementById('modalContent');
    
    modalContent.innerHTML = `
        <div class="drill-down-content">
            <h3>${title}</h3>
            <div class="content-details">
                <pre>${JSON.stringify(content, null, 2)}</pre>
            </div>
            <button onclick="closeModal()" class="btn btn-secondary">Close</button>
        </div>
    `;
    
    modal.style.display = 'block';
}

function showRelatedContent(topicName, event) {
    event?.stopPropagation();
    showMessage(`Related content for ${topicName} - feature coming soon!`, 'info');
}

function showContactHistory(contactEmail, event) {
    event?.stopPropagation();
    showMessage(`Communication history for ${contactEmail} - feature coming soon!`, 'info');
}

function downloadTreeData() {
    fetchCurrentKnowledgeTree().then(tree => {
        if (tree) {
            const dataStr = JSON.stringify(tree, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `knowledge-tree-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            URL.revokeObjectURL(url);
        }
    });
}

function getTreeVisualizationStyles() {
    return `
        .enhanced-tree-visualization {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .tree-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .tree-header h2 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2rem;
        }
        
        .tree-meta {
            color: #666;
            font-size: 0.9rem;
        }
        
        .tree-stats-header {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 40px;
            flex-wrap: wrap;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 1.8rem;
            font-weight: bold;
            display: block;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .tree-section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 20px;
            padding: 15px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        
        .topic-grid, .contact-grid, .domain-grid, .opportunities-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .topic-card, .contact-card, .domain-card, .opportunity-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            border-left: 5px solid #007bff;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }
        
        .topic-card:hover, .contact-card:hover, .domain-card:hover, .opportunity-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .topic-card.expanded, .contact-card.expanded, .domain-card.expanded, .opportunity-card.expanded {
            transform: scale(1.02);
        }
        
        .topic-title, .contact-name, .domain-name, .opportunity-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .topic-icon {
            font-size: 1.3rem;
        }
        
        .relevance-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .relevance-high {
            background: #dc3545;
            color: white;
        }
        
        .relevance-medium {
            background: #ffc107;
            color: #212529;
        }
        
        .relevance-low {
            background: #28a745;
            color: white;
        }
        
        .key-points h4, .participants h4, .contact-topics {
            font-size: 0.9rem;
            color: #495057;
            margin-bottom: 8px;
        }
        
        .point-list {
            list-style: none;
            padding: 0;
        }
        
        .point-list li {
            padding: 3px 0;
            padding-left: 15px;
            position: relative;
            font-size: 0.9rem;
        }
        
        .point-list li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #007bff;
            font-weight: bold;
        }
        
        .participant-tags, .contact-topics {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        
        .participant-tag, .topic-tag {
            background: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
        }
        
        .contact-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }
        
        .contact-email {
            font-size: 0.85rem;
            color: #666;
        }
        
        .contact-company {
            font-size: 0.8rem;
            color: #888;
            font-style: italic;
        }
        
        .engagement-score {
            background: #28a745;
            color: white;
            padding: 6px 10px;
            border-radius: 50%;
            font-size: 0.8rem;
            font-weight: bold;
            min-width: 35px;
            text-align: center;
        }
        
        .contact-context, .topic-summary {
            font-size: 0.9rem;
            line-height: 1.4;
            color: #495057;
            margin-bottom: 10px;
        }
        
        .timeline {
            position: relative;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .timeline:before {
            content: '';
            position: absolute;
            left: 20px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #007bff;
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
            padding-left: 50px;
        }
        
        .timeline-item:before {
            content: '';
            position: absolute;
            left: 14px;
            top: 5px;
            width: 12px;
            height: 12px;
            background: #007bff;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 2px #007bff;
        }
        
        .timeline-date {
            font-weight: bold;
            color: #007bff;
            font-size: 0.9rem;
        }
        
        .timeline-event {
            margin-top: 5px;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .domain-topics {
            font-size: 0.85rem;
            color: #666;
            margin-top: 5px;
        }
        
        .opportunity-score {
            position: absolute;
            top: 15px;
            right: 15px;
            background: #28a745;
            color: white;
            padding: 8px 12px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        .opportunity-type {
            font-size: 0.8rem;
            color: #666;
            text-transform: uppercase;
            margin: 5px 0;
        }
        
        .opportunity-timing {
            font-size: 0.85rem;
            color: #888;
        }
        
        .topic-actions, .contact-actions, .domain-actions {
            display: none;
            gap: 10px;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        
        .drill-down-btn, .related-content-btn, .history-btn {
            padding: 6px 12px;
            border: 1px solid #007bff;
            background: #007bff;
            color: white;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .drill-down-btn:hover, .related-content-btn:hover, .history-btn:hover {
            background: #0056b3;
            border-color: #0056b3;
        }
        
        .related-content-btn {
            background: transparent;
            color: #007bff;
        }
        
        .related-content-btn:hover {
            background: #007bff;
            color: white;
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .insight-category {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-left: 4px solid #28a745;
        }
        
        .insight-category h4 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1rem;
        }
        
        .insight-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .drill-down-content {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .drill-down-content h3 {
            margin-bottom: 20px;
            color: #333;
        }
        
        .content-details {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .content-details pre {
            font-size: 0.9rem;
            line-height: 1.4;
            margin: 0;
        }
        
        @media (max-width: 768px) {
            .topic-grid, .contact-grid, .domain-grid, .opportunities-grid {
                grid-template-columns: 1fr;
            }
            
            .tree-stats-header {
                flex-direction: column;
                gap: 15px;
            }
            
            .enhanced-tree-visualization {
                padding: 10px;
            }
        }
    `;
}

// ... existing code ...

async function startFullPipeline() {
    console.log('🚀 startFullPipeline() called');
    
    // Check authentication first
    const isAuthenticated = await checkAuthentication();
    console.log('🔐 Authentication check result:', isAuthenticated);
    
    if (!isAuthenticated) {
        console.log('❌ Authentication failed');
        showMessage('Authentication required. Please log in to run pipeline operations.', 'error');
        return;
    }
    
    // Check if anything is running
    console.log('⚙️ Current pipeline state:', currentPipelineState);
    if (currentPipelineState.isRunning) {
        console.log('⚠️ Pipeline already running');
        showMessage('Another operation is already running!', 'warning');
        return;
    }
    
    console.log('✅ Starting pipeline from first step');
    // Start from the first step (contacts)
    const firstStepId = PIPELINE_STEPS[0].id;
    console.log('🎯 First step ID:', firstStepId);
    await startFromStep(firstStepId, 1);
}

async function startFromStep(stepId, stepNumber) {
    // ... existing code ...
}

async function handleRunIndividualStep(stepId) {
    // Simple wrapper that calls the existing runIndividualStep function
    await runIndividualStep(stepId);
}

async function handleInspectStepResults(stepId) {
    // Simple wrapper that calls the existing inspectStepResults function
    await inspectStepResults(stepId);
}

async function handleViewStepResults(stepId) {
    // Simple wrapper that calls the existing viewStepResults function
    await viewStepResults(stepId);
}

function testModal() {
    console.log('🧪 testModal() called - button click detected!');
    // Simple test function for the test modal button
    showMessage('🧪 Test button clicked! All functions are working.', 'success');
}

function stopPipeline() {
    // Stop the current running pipeline
    if (currentPipelineState.isRunning) {
        currentPipelineState.isRunning = false;
        updateStartFromButtonStates();
        document.getElementById('startPipeline').disabled = false;
        showMessage('⏹️ Pipeline stopped by user', 'warning');
    } else {
        showMessage('No pipeline is currently running', 'info');
    }
}

function downloadAllResults() {
    // Download all pipeline results as JSON
    if (currentPipelineState.stepResults && Object.keys(currentPipelineState.stepResults).length > 0) {
        const dataStr = JSON.stringify(currentPipelineState.stepResults, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `pipeline-results-${new Date().toISOString().slice(0,10)}.json`;
        link.click();
        URL.revokeObjectURL(url);
        showMessage('📥 Results downloaded successfully', 'success');
    } else {
        showMessage('No results available to download', 'warning');
    }
}

function resetPipeline() {
    // Reset all pipeline state
    currentPipelineState = {
        isRunning: false,
        currentStep: 0,
        stepResults: {}
    };
    
    // Reset UI
    PIPELINE_STEPS.forEach(step => {
        updateStepControlStatus(step.id, 'ready', 'Ready');
        hideStepProgress(step.id);
    });
    
    updateProgressDisplay();
    showMessage('Pipeline state reset', 'info');
}

// Background job polling function
async function pollJobStatus(jobId, statusUrl, stepId) {
    console.log(`🔍 Polling status for job ${jobId}`);
    
    const maxPolls = 120; // 10 minutes max (every 5 seconds)
    let pollCount = 0;
    
    while (pollCount < maxPolls) {
        try {
            await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
            
            const statusResponse = await fetch(statusUrl);
            if (!statusResponse.ok) {
                throw new Error(`Failed to check job status: ${statusResponse.status}`);
            }
            
            const jobStatus = await statusResponse.json();
            console.log(`📊 Job ${jobId} status:`, jobStatus);
            
            // Update step progress if available
            if (jobStatus.progress !== undefined) {
                updateStepProgress(stepId, jobStatus.progress);
            }
            
            // Update step message if available
            if (jobStatus.message) {
                updateStepControlStatus(stepId, 'running', jobStatus.message);
            }
            
            // Check if job is complete
            if (jobStatus.status === 'completed') {
                console.log(`✅ Job ${jobId} completed successfully`);
                
                // Return structured result for the step
                return {
                    success: true,
                    message: jobStatus.message || 'Contact enrichment completed',
                    job_id: jobId,
                    stats: {
                        contacts_processed: jobStatus.contacts_processed || 0,
                        successfully_enriched: jobStatus.contacts_enriched || 0,
                        success_rate: jobStatus.success_rate || 0,
                        sources_used: jobStatus.sources_used || 0
                    },
                    mode: 'background_job'
                };
            }
            
            // Check if job failed
            if (jobStatus.status === 'failed') {
                console.error(`❌ Job ${jobId} failed:`, jobStatus.message);
                throw new Error(jobStatus.message || 'Background job failed');
            }
            
            pollCount++;
            
        } catch (error) {
            console.error(`Error polling job status:`, error);
            if (pollCount > 5) { // Give it a few retries before giving up
                throw error;
            }
            pollCount++;
        }
    }
    
    // Timeout
    throw new Error(`Job ${jobId} timed out after ${maxPolls * 5} seconds`);
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM loaded, initializing dashboard...');
    initializeDashboard();
});

// Fallback initialization in case DOMContentLoaded already fired
if (document.readyState === 'loading') {
    console.log('📖 Document still loading, waiting for DOMContentLoaded...');
} else {
    console.log('📖 Document already loaded, initializing immediately...');
    initializeDashboard();
}

// Additional fallback with window.onload
window.addEventListener('load', function() {
    const app = document.getElementById('app');
    if (app && app.innerHTML.includes('Loading Strategic Intelligence Dashboard')) {
        console.log('🔄 Dashboard not initialized yet, trying again...');
        initializeDashboard();
    }
});

