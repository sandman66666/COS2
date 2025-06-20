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

// Enhanced status update function for CEO intelligence
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
    if (event.target === ceoModal) {
        closeCEOModal();
    }
} 