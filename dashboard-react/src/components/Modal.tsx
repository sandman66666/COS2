import React, { useState } from 'react';
import styled from 'styled-components';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: ${props => props.theme.spacing.lg};
`;

const ModalContainer = styled.div`
  background: ${props => props.theme.colors.background};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.shadowHover};
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const ModalHeader = styled.div`
  padding: ${props => props.theme.spacing.lg};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: ${props => props.theme.colors.surface};
  flex-shrink: 0;
`;

const ModalTitle = styled.h2`
  color: ${props => props.theme.colors.text};
  font-size: 1.3rem;
  font-weight: 500;
  margin: 0;
`;

const HeaderActions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  align-items: center;
`;

const DownloadButton = styled.button`
  background: ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.text};
  border: none;
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.xs};

  &:hover {
    background: ${props => props.theme.colors.primaryHover};
    transform: scale(1.05);
  }
`;

const CloseButton = styled.button`
  background: ${props => props.theme.colors.error};
  color: ${props => props.theme.colors.text};
  border: none;
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: #6d5555;
    transform: scale(1.05);
  }
`;

const ModalContent = styled.div`
  padding: ${props => props.theme.spacing.lg};
  overflow-y: auto;
  flex: 1;
  min-height: 0;
`;

const ScrollableTableContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  overflow: hidden;
  margin-bottom: ${props => props.theme.spacing.lg};
  max-height: 60vh;
`;

const ScrollableTable = styled.div`
  overflow-y: auto;
  max-height: 100%;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
`;

const TableHeader = styled.thead`
  background: ${props => props.theme.colors.accent};
  position: sticky;
  top: 0;
  z-index: 1;
`;

const TableHeaderCell = styled.th<{ width?: string }>`
  padding: ${props => props.theme.spacing.md};
  text-align: left;
  color: ${props => props.theme.colors.text};
  font-weight: 600;
  font-size: 0.9rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  white-space: nowrap;
  ${props => props.width && `width: ${props.width};`}
`;

const TableBody = styled.tbody``;

const TableRow = styled.tr<{ clickable?: boolean }>`
  &:nth-child(even) {
    background: ${props => props.theme.colors.background};
  }
  
  &:hover {
    background: ${props => props.theme.colors.surfaceHover};
    ${props => props.clickable && 'cursor: pointer;'}
  }
`;

const TableCell = styled.td<{ width?: string }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  color: ${props => props.theme.colors.text};
  font-size: 0.85rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  ${props => props.width && `width: ${props.width};`}
  word-wrap: break-word;
  vertical-align: top;
`;

const ExpandableCell = styled(TableCell)`
  cursor: pointer;
  
  &:hover {
    background: ${props => props.theme.colors.primary};
    color: ${props => props.theme.colors.background};
  }
`;

const ExpandedDetails = styled.div`
  background: ${props => props.theme.colors.background};
  padding: ${props => props.theme.spacing.md};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  margin: ${props => props.theme.spacing.sm} 0;
  max-height: 300px;
  overflow-y: auto;
`;

const DetailSection = styled.div`
  margin-bottom: ${props => props.theme.spacing.md};
`;

const DetailTitle = styled.h4`
  color: ${props => props.theme.colors.primary};
  margin: 0 0 ${props => props.theme.spacing.xs} 0;
  font-size: 0.9rem;
`;

const DetailContent = styled.pre`
  color: ${props => props.theme.colors.text};
  font-size: 0.8rem;
  line-height: 1.4;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: ${props => props.theme.colors.surface};
  padding: ${props => props.theme.spacing.sm};
  border-radius: calc(${props => props.theme.borderRadius} / 3);
  border: 1px solid ${props => props.theme.colors.border};
`;

const SummaryCards = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const SummaryCard = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  padding: ${props => props.theme.spacing.md};
  text-align: center;
`;

const SummaryLabel = styled.div`
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: ${props => props.theme.spacing.xs};
  text-transform: uppercase;
`;

const SummaryValue = styled.div`
  color: ${props => props.theme.colors.text};
  font-size: 1.2rem;
  font-weight: 600;
`;

const StatusBadge = styled.span<{ success?: boolean }>`
  display: inline-block;
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  background: ${props => 
    props.success 
      ? props.theme.colors.success 
      : props.theme.colors.error
  };
  color: ${props => props.theme.colors.text};
  border-radius: calc(${props => props.theme.borderRadius} / 3);
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const TreeContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  padding: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.lg};
  max-height: 60vh;
  overflow-y: auto;
`;

const TreeNode = styled.div<{ level: number; expanded?: boolean }>`
  margin-left: ${props => props.level * 20}px;
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const TreeNodeHeader = styled.div<{ clickable?: boolean }>`
  display: flex;
  align-items: center;
  padding: ${props => props.theme.spacing.sm};
  border-radius: ${props => props.theme.borderRadius};
  cursor: ${props => props.clickable ? 'pointer' : 'default'};
  transition: all 0.3s ease;
  
  &:hover {
    background: ${props => props.clickable ? props.theme.colors.surfaceHover : 'transparent'};
  }
`;

const TreeNodeIcon = styled.span`
  margin-right: ${props => props.theme.spacing.sm};
  font-size: 0.9rem;
`;

const TreeNodeTitle = styled.span`
  color: ${props => props.theme.colors.text};
  font-weight: 500;
  font-size: 0.9rem;
`;

const TreeNodeDetails = styled.div`
  background: ${props => props.theme.colors.background};
  padding: ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  margin-top: ${props => props.theme.spacing.sm};
  border-left: 3px solid ${props => props.theme.colors.primary};
`;

const EmptyState = styled.div`
  text-align: center;
  color: ${props => props.theme.colors.textMuted};
  font-style: italic;
  padding: ${props => props.theme.spacing.xl};
`;

interface ModalProps {
  stepId: string;
  stepName: string;
  data: any;
  onClose: () => void;
}

const Modal: React.FC<ModalProps> = ({ stepId, stepName, data, onClose }) => {
  const [expandedContacts, setExpandedContacts] = useState<Set<string>>(new Set());
  const [expandedTreeNodes, setExpandedTreeNodes] = useState<Set<string>>(new Set());

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const downloadJSON = () => {
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${stepId}-results-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const toggleContactExpansion = (contactEmail: string) => {
    const newExpanded = new Set(expandedContacts);
    if (newExpanded.has(contactEmail)) {
      newExpanded.delete(contactEmail);
    } else {
      newExpanded.add(contactEmail);
    }
    setExpandedContacts(newExpanded);
  };

  const toggleTreeNode = (nodeId: string) => {
    const newExpanded = new Set(expandedTreeNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedTreeNodes(newExpanded);
  };

  const getSummaryStats = () => {
    if (!data) return {};
    
    const stats: Record<string, any> = {};
    
    // Extract statistics based on step type
    switch (stepId) {
      case 'extract':
        if (data.contacts?.length) stats['Contacts Found'] = data.contacts.length;
        if (data.total_sent_emails) stats['Emails Analyzed'] = data.total_sent_emails;
        if (data.trust_tier_counts) {
          const tiers = data.trust_tier_counts;
          if (tiers.high) stats['High Trust'] = tiers.high;
          if (tiers.medium) stats['Medium Trust'] = tiers.medium;
          if (tiers.low) stats['Low Trust'] = tiers.low;
        }
        break;
      
      case 'emails':
        if (data.emails?.length) stats['Emails Synced'] = data.emails.length;
        if (data.contacts_processed) stats['Contacts Processed'] = data.contacts_processed;
        if (data.new_emails) stats['New Emails'] = data.new_emails;
        break;
        
      case 'augment':
        if (data.contacts_enriched) stats['Contacts Enriched'] = data.contacts_enriched;
        if (data.contacts_processed) stats['Contacts Processed'] = data.contacts_processed;
        if (data.success_rate) stats['Success Rate'] = `${Math.round(data.success_rate * 100)}%`;
        if (data.sources_used) stats['Data Sources'] = data.sources_used;
        break;
        
      case 'tree':
        if (data.total_nodes) stats['Knowledge Nodes'] = data.total_nodes;
        if (data.tree_data?.metadata) {
          const meta = data.tree_data.metadata;
          if (meta.total_contacts) stats['Contacts'] = meta.total_contacts;
          if (meta.total_emails) stats['Emails'] = meta.total_emails;
        }
        break;
    }
    
    return stats;
  };

  const renderContactsTable = () => {
    const contacts = data.contacts || data.results || [];
    if (!Array.isArray(contacts) || contacts.length === 0) return null;

    const isAugmented = stepId === 'augment';

    return (
      <ScrollableTableContainer>
        <ScrollableTable>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell width="25%">Email</TableHeaderCell>
                <TableHeaderCell width="15%">Name</TableHeaderCell>
                <TableHeaderCell width="12%">Domain</TableHeaderCell>
                <TableHeaderCell width="10%">Trust Tier</TableHeaderCell>
                <TableHeaderCell width="8%">Frequency</TableHeaderCell>
                <TableHeaderCell width="15%">Last Contact</TableHeaderCell>
                <TableHeaderCell width="15%">Recent Subjects</TableHeaderCell>
                {isAugmented && <TableHeaderCell width="10%">Enrichment</TableHeaderCell>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {contacts.map((contact: any, index: number) => {
                const email = contact.email || contact.contact_email || `contact-${index}`;
                const isExpanded = expandedContacts.has(email);
                const hasEnrichment = contact.metadata?.enrichment_data || contact.enrichment_data;
                
                return (
                  <React.Fragment key={email}>
                    <TableRow clickable={isAugmented && hasEnrichment}>
                      <TableCell width="25%">{email}</TableCell>
                      <TableCell width="15%">
                        {contact.name || contact.first_name 
                          ? `${contact.first_name || ''} ${contact.last_name || ''}`.trim() || contact.name
                          : email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                        }
                      </TableCell>
                      <TableCell width="12%">{contact.domain || email.split('@')[1]}</TableCell>
                      <TableCell width="10%">
                        <span style={{ 
                          color: contact.trust_tier === 'tier_1' ? '#28a745' : 
                                contact.trust_tier === 'tier_2' ? '#ffc107' : '#6c757d' 
                        }}>
                          {contact.trust_tier === 'tier_1' ? 'High' : 
                           contact.trust_tier === 'tier_2' ? 'Medium' : 'Low'}
                        </span>
                      </TableCell>
                      <TableCell width="8%">{contact.frequency || '-'}</TableCell>
                      <TableCell width="15%">
                        {contact.last_contact ? new Date(contact.last_contact).toLocaleDateString() : '-'}
                      </TableCell>
                      <TableCell width="15%">
                        {Array.isArray(contact.recent_subjects) 
                          ? contact.recent_subjects.slice(0, 2).join(', ') 
                          : '-'}
                      </TableCell>
                      {isAugmented && (
                        <ExpandableCell 
                          width="10%" 
                          onClick={() => hasEnrichment && toggleContactExpansion(email)}
                        >
                          {hasEnrichment ? (isExpanded ? '▼ Hide' : '▶ View') : 'No data'}
                        </ExpandableCell>
                      )}
                    </TableRow>
                    {isAugmented && isExpanded && hasEnrichment && (
                      <TableRow>
                        <TableCell colSpan={8}>
                          <ExpandedDetails>
                            {renderContactEnrichmentDetails(contact)}
                          </ExpandedDetails>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </ScrollableTable>
      </ScrollableTableContainer>
    );
  };

  const renderContactEnrichmentDetails = (contact: any) => {
    const enrichmentData = contact.metadata?.enrichment_data || contact.enrichment_data || {};
    
    return (
      <div>
        <DetailSection>
          <DetailTitle>🎯 Enrichment Summary</DetailTitle>
          <DetailContent>
            {`Confidence Score: ${enrichmentData.confidence_score || 'N/A'}
Data Sources: ${enrichmentData.data_sources ? enrichmentData.data_sources.join(', ') : 'None'}
Status: ${enrichmentData.enrichment_status || 'Unknown'}`}
          </DetailContent>
        </DetailSection>

        {enrichmentData.person_data && (
          <DetailSection>
            <DetailTitle>👤 Personal Information</DetailTitle>
            <DetailContent>{JSON.stringify(enrichmentData.person_data, null, 2)}</DetailContent>
          </DetailSection>
        )}

        {enrichmentData.company_data && (
          <DetailSection>
            <DetailTitle>🏢 Company Information</DetailTitle>
            <DetailContent>{JSON.stringify(enrichmentData.company_data, null, 2)}</DetailContent>
          </DetailSection>
        )}

        {enrichmentData.intelligence_summary && (
          <DetailSection>
            <DetailTitle>🧠 Intelligence Summary</DetailTitle>
            <DetailContent>{JSON.stringify(enrichmentData.intelligence_summary, null, 2)}</DetailContent>
          </DetailSection>
        )}

        {contact.behavioral_intelligence && (
          <DetailSection>
            <DetailTitle>📊 Behavioral Intelligence</DetailTitle>
            <DetailContent>{JSON.stringify(contact.behavioral_intelligence, null, 2)}</DetailContent>
          </DetailSection>
        )}
      </div>
    );
  };

  const renderEmailsTable = () => {
    const emails = data.emails || [];
    if (!Array.isArray(emails) || emails.length === 0) return null;

    return (
      <ScrollableTableContainer>
        <ScrollableTable>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHeaderCell width="20%">Subject</TableHeaderCell>
                <TableHeaderCell width="15%">From</TableHeaderCell>
                <TableHeaderCell width="15%">To</TableHeaderCell>
                <TableHeaderCell width="12%">Date</TableHeaderCell>
                <TableHeaderCell width="30%">Content Preview</TableHeaderCell>
                <TableHeaderCell width="8%">Length</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {emails.map((email: any, index: number) => (
                <TableRow key={index}>
                  <TableCell width="20%">
                    {email.subject || email.metadata?.subject || 'No Subject'}
                  </TableCell>
                  <TableCell width="15%">
                    {email.from || email.metadata?.from || '-'}
                  </TableCell>
                  <TableCell width="15%">
                    {Array.isArray(email.to) 
                      ? email.to.join(', ')
                      : Array.isArray(email.metadata?.to)
                      ? email.metadata.to.join(', ')
                      : email.to || email.metadata?.to || '-'}
                  </TableCell>
                  <TableCell width="12%">
                    {email.date 
                      ? new Date(email.date).toLocaleDateString()
                      : email.metadata?.date
                      ? new Date(email.metadata.date).toLocaleDateString()
                      : '-'}
                  </TableCell>
                  <TableCell width="30%">
                    {(email.content || email.content_preview || '').substring(0, 150)}
                    {(email.content || email.content_preview || '').length > 150 ? '...' : ''}
                  </TableCell>
                  <TableCell width="8%">
                    {email.content_length || (email.content || '').length || '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollableTable>
      </ScrollableTableContainer>
    );
  };

  const renderKnowledgeTree = () => {
    const treeData = data.tree_data || data.tree || data;
    if (!treeData) return null;

    const renderTreeNode = (node: any, level: number = 0, parentId: string = ''): React.ReactNode => {
      if (!node) return null;
      
      const nodeId = `${parentId}-${node.name || node.title || 'node'}`;
      const hasChildren = node.children && Array.isArray(node.children) && node.children.length > 0;
      const isExpanded = expandedTreeNodes.has(nodeId);

      return (
        <TreeNode key={nodeId} level={level}>
          <TreeNodeHeader 
            clickable={hasChildren || node.details}
            onClick={() => hasChildren && toggleTreeNode(nodeId)}
          >
            <TreeNodeIcon>
              {hasChildren ? (isExpanded ? '📂' : '📁') : '📄'}
            </TreeNodeIcon>
            <TreeNodeTitle>
              {node.name || node.title || 'Unnamed Node'}
              {node.count && ` (${node.count})`}
            </TreeNodeTitle>
          </TreeNodeHeader>
          
          {node.details && (
            <TreeNodeDetails>
              <DetailContent>{JSON.stringify(node.details, null, 2)}</DetailContent>
            </TreeNodeDetails>
          )}
          
          {hasChildren && isExpanded && (
            <div>
              {node.children.map((child: any, index: number) => 
                renderTreeNode(child, level + 1, `${nodeId}-${index}`)
              )}
            </div>
          )}
        </TreeNode>
      );
    };

    // Handle different tree data structures
    if (treeData.root) {
      return (
        <TreeContainer>
          {renderTreeNode(treeData.root, 0)}
        </TreeContainer>
      );
    } else if (Array.isArray(treeData)) {
      return (
        <TreeContainer>
          {treeData.map((node, index) => renderTreeNode(node, 0, `root-${index}`))}
        </TreeContainer>
      );
    } else {
      return (
        <TreeContainer>
          {renderTreeNode(treeData, 0)}
        </TreeContainer>
      );
    }
  };

  const renderStepContent = () => {
    switch (stepId) {
      case 'extract':
        return renderContactsTable();
      case 'emails':
        return renderEmailsTable();
      case 'augment':
        return renderContactsTable();
      case 'tree':
        return renderKnowledgeTree();
      default:
        return (
          <EmptyState>
            No specialized view available for this step.
            <br />
            Check the raw data below.
          </EmptyState>
        );
    }
  };

  const summaryStats = getSummaryStats();
  const isSuccess = data?.success !== false;

  return (
    <ModalOverlay onClick={handleOverlayClick}>
      <ModalContainer>
        <ModalHeader>
          <ModalTitle>📊 {stepName} - Results</ModalTitle>
          <HeaderActions>
            <DownloadButton onClick={downloadJSON}>
              💾 Download JSON
            </DownloadButton>
            <CloseButton onClick={onClose}>✕ Close</CloseButton>
          </HeaderActions>
        </ModalHeader>
        
        <ModalContent>
          {data ? (
            <>
              <StatusBadge success={isSuccess}>
                {isSuccess ? '✅ Success' : '❌ Error'}
              </StatusBadge>

              {Object.keys(summaryStats).length > 0 && (
                <SummaryCards>
                  {Object.entries(summaryStats).map(([label, value]) => (
                    <SummaryCard key={label}>
                      <SummaryLabel>{label}</SummaryLabel>
                      <SummaryValue>{value}</SummaryValue>
                    </SummaryCard>
                  ))}
                </SummaryCards>
              )}

              {data.message && (
                <div style={{ 
                  background: '#f8f9fa', 
                  padding: '12px', 
                  borderRadius: '6px', 
                  marginBottom: '16px',
                  border: '1px solid #e9ecef'
                }}>
                  <strong>Summary:</strong> {data.message}
                </div>
              )}

              {renderStepContent()}

              {stepId === 'extract' && (!data.contacts || data.contacts.length === 0) && (
                <div style={{ 
                  background: '#fff3cd', 
                  padding: '12px', 
                  borderRadius: '6px', 
                  marginBottom: '16px',
                  border: '1px solid #ffeaa7',
                  color: '#856404'
                }}>
                  <strong>No contacts found.</strong> This might be because:
                  <ul>
                    <li>No sent emails in the specified timeframe</li>
                    <li>Emails don't contain valid recipient addresses</li>
                    <li>Email addresses were filtered out (common domains, etc.)</li>
                  </ul>
                </div>
              )}
            </>
          ) : (
            <EmptyState>
              No data available for this step yet.
              <br />
              Run the step to see results.
            </EmptyState>
          )}
        </ModalContent>
      </ModalContainer>
    </ModalOverlay>
  );
};

export default Modal; 