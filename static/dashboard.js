// User Authentication Functions
async function loadUserInfo() {
    try {
        const response = await fetch('/api/auth/status');
        const result = await response.json();
        
        if (result.authenticated && result.user) {
            document.getElementById('user-email').textContent = result.user.email || 'Unknown User';
        } else {
            // User not authenticated, redirect to login
            window.location.href = '/logout';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
        document.getElementById('user-email').textContent = 'Error loading user';
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
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
});

// CEO Strategic Intelligence Functions
async function generateCEOIntelligenceBrief() {
    try {
        updateStatus('ceo-brief-status', 'loading', 'Generating CEO intelligence brief...');
        
        const focusArea = document.getElementById('focus-area').value.trim();
        const requestData = {};
        
        if (focusArea) {
            requestData.focus_area = focusArea;
        }
        
        const response = await fetch('/api/intelligence/ceo-intelligence-brief', {
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
        updateStatus('ceo-brief-status', 'error', 'Error generating CEO brief: ' + error.message);
    }
}

async function analyzeCompetitiveLandscape() {
    try {
        updateStatus('competitive-analysis-status', 'loading', 'Analyzing competitive landscape...');
        
        const response = await fetch('/api/intelligence/competitive-landscape-analysis', {
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
        updateStatus('competitive-analysis-status', 'error', 'Error analyzing competitive landscape: ' + error.message);
    }
}

async function mapNetworkToObjectives() {
    try {
        updateStatus('network-mapping-status', 'loading', 'Mapping network to objectives...');
        
        const response = await fetch('/api/intelligence/network-to-objectives-mapping', {
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
        
        const response = await fetch('/api/intelligence/decision-support', {
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