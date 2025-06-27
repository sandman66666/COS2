import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';

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
  max-width: 1400px;
  max-height: 95vh;
  display: flex;
  flex-direction: column;
`;

const ModalHeader = styled.div`
  padding: ${props => props.theme.spacing.lg};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
`;

const ModalTitle = styled.h2`
  color: ${props => props.theme.colors.text};
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: ${props => props.theme.colors.textMuted};
  padding: ${props => props.theme.spacing.xs};
  
  &:hover {
    color: ${props => props.theme.colors.text};
  }
`;

const ModalBody = styled.div`
  padding: ${props => props.theme.spacing.lg};
  overflow-y: auto;
  flex: 1;
  min-height: 0;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 1.2rem;
  color: ${props => props.theme.colors.textMuted};
`;

const ErrorMessage = styled.div`
  background: rgba(220, 53, 69, 0.1);
  border: 1px solid #dc3545;
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.lg};
  color: #dc3545;
  text-align: center;
`;

const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const SummaryCard = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.lg};
  text-align: center;
`;

const SummaryNumber = styled.div`
  font-size: 2rem;
  font-weight: 600;
  color: ${props => props.theme.colors.primary};
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const SummaryLabel = styled.div`
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.9rem;
`;

const TableContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  overflow: hidden;
`;

const TableHeader = styled.div`
  background: ${props => props.theme.colors.background};
  padding: ${props => props.theme.spacing.md};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  font-weight: 600;
  color: ${props => props.theme.colors.text};
  position: sticky;
  top: 0;
  z-index: 10;
`;

const TableScrollContainer = styled.div`
  max-height: 60vh;
  overflow-y: auto;
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const TableHeaderCell = styled.th<{ width?: string }>`
  padding: ${props => props.theme.spacing.md};
  text-align: left;
  color: ${props => props.theme.colors.text};
  font-weight: 600;
  font-size: 0.9rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  white-space: nowrap;
  background: ${props => props.theme.colors.background};
  position: sticky;
  top: 0;
  z-index: 5;
  ${props => props.width && `width: ${props.width};`}
`;

const TableCell = styled.td`
  padding: ${props => props.theme.spacing.md};
  border-bottom: 1px solid ${props => props.theme.colors.border};
  color: ${props => props.theme.colors.text};
  font-size: 0.9rem;
  vertical-align: top;
`;

const TrustBadge = styled.span<{ tier: string | number }>`
  padding: ${props => props.theme.spacing.xs} ${props => props.theme.spacing.sm};
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  
  background: ${props => {
    const tierStr = String(props.tier);
    switch (tierStr) {
      case 'tier_1': 
      case '1': 
      case 'High': return '#d4edda';
      case 'tier_2': 
      case '2': 
      case 'Medium': return '#fff3cd';
      default: return '#f8d7da';
    }
  }};
  
  color: ${props => {
    const tierStr = String(props.tier);
    switch (tierStr) {
      case 'tier_1': 
      case '1': 
      case 'High': return '#155724';
      case 'tier_2': 
      case '2': 
      case 'Medium': return '#856404';
      default: return '#721c24';
    }
  }};
`;

const ExpandableRow = styled.tr<{ clickable?: boolean }>`
  cursor: ${props => props.clickable ? 'pointer' : 'default'};
  
  &:hover {
    background: ${props => props.clickable ? props.theme.colors.surfaceHover : 'transparent'};
  }
`;

const ExpandedContent = styled.td`
  padding: ${props => props.theme.spacing.lg};
  background: ${props => props.theme.colors.background};
  border-bottom: 2px solid ${props => props.theme.colors.border};
`;

const DetailGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: ${props => props.theme.spacing.lg};
`;

const DetailSection = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.md};
`;

const DetailTitle = styled.h4`
  color: ${props => props.theme.colors.text};
  margin-bottom: ${props => props.theme.spacing.sm};
  font-size: 1rem;
`;

const DetailItem = styled.div`
  margin-bottom: ${props => props.theme.spacing.xs};
  font-size: 0.9rem;
  line-height: 1.4;
`;

const DetailLabel = styled.span`
  font-weight: 500;
  color: ${props => props.theme.colors.textMuted};
  margin-right: ${props => props.theme.spacing.xs};
`;

const DetailValue = styled.span`
  color: ${props => props.theme.colors.text};
`;

const PaginationContainer = styled.div`
  padding: ${props => props.theme.spacing.md};
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: ${props => props.theme.colors.background};
  border-top: 1px solid ${props => props.theme.colors.border};
`;

const PaginationInfo = styled.span`
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.9rem;
`;

const PaginationButtons = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
`;

const PaginationButton = styled.button`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  color: ${props => props.theme.colors.text};
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover:not(:disabled) {
    background: ${props => props.theme.colors.surfaceHover};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const DownloadButton = styled.button`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.text};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  cursor: pointer;
  font-size: 0.9rem;
  margin-bottom: ${props => props.theme.spacing.md};
  
  &:hover {
    background: ${props => props.theme.colors.primaryHover};
  }
`;

const PreviewText = styled.div`
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.85rem;
  color: ${props => props.theme.colors.textMuted};
`;

const EmailSubject = styled.div`
  font-weight: 500;
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const TreeNode = styled.div<{ level: number; clickable?: boolean }>`
  padding: ${props => props.theme.spacing.sm};
  margin-left: ${props => props.level * 20}px;
  border-left: ${props => props.level > 0 ? `2px solid ${props.theme.colors.border}` : 'none'};
  cursor: ${props => props.clickable ? 'pointer' : 'default'};
  
  &:hover {
    background: ${props => props.clickable ? props.theme.colors.surfaceHover : 'transparent'};
  }
`;

const TreeNodeTitle = styled.div`
  font-weight: 500;
  color: ${props => props.theme.colors.text};
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const TreeNodeDetails = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.colors.textMuted};
`;

interface ModalProps {
  stepId: string;
  stepName: string;
  data?: any;
  onClose: () => void;
}

interface FreshData {
  contacts?: any[];
  emails?: any[];
  knowledge_tree?: any;
  total_contacts?: number;
  total_emails?: number;
  [key: string]: any;
}

const Modal: React.FC<ModalProps> = ({ stepId, stepName, data, onClose }) => {
  const [freshData, setFreshData] = useState<FreshData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedContact, setExpandedContact] = useState<string | null>(null);
  const [expandedNode, setExpandedNode] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(50);

  useEffect(() => {
    fetchFreshData();
  }, [stepId]);

  const fetchFreshData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let endpoint = '';
      
      switch (stepId) {
        case 'extract':
          endpoint = '/api/inspect/contacts';
          break;
        case 'emails':
          endpoint = '/api/inspect/emails';
          break;
        case 'augment':
          endpoint = '/api/inspect/contacts';
          break;
        case 'tree':
          endpoint = '/api/inspect/knowledge-tree';
          break;
        case 'insights':
          endpoint = '/api/inspect/contacts'; // Fallback for now
          break;
        default:
          endpoint = '/api/inspect/contacts';
      }

      console.log(`🔍 Fetching fresh data from ${endpoint} for step ${stepId}`);
      
      const response = await axios.get(endpoint);
      
      if (response.data.success) {
        setFreshData(response.data);
        console.log(`✅ Fresh data loaded for ${stepId}:`, response.data);
      } else {
        setError(response.data.error || 'Failed to load data');
      }
    } catch (err: any) {
      console.error(`❌ Error fetching data for ${stepId}:`, err);
      setError(err.response?.data?.error || err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const downloadData = () => {
    if (!freshData) return;
    
    const dataToDownload = {
      step: stepId,
      stepName,
      timestamp: new Date().toISOString(),
      data: freshData
    };
    
    const blob = new Blob([JSON.stringify(dataToDownload, null, 2)], { 
      type: 'application/json' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${stepId}-${stepName.replace(/\s+/g, '-')}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const renderContactsView = () => {
    if (!freshData?.contacts) {
      return <div>No contacts found.</div>;
    }

    const contacts = freshData.contacts;
    const startIndex = currentPage * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedContacts = contacts.slice(startIndex, endIndex);
    const totalPages = Math.ceil(contacts.length / pageSize);

    return (
      <>
        <SummaryGrid>
          <SummaryCard>
            <SummaryNumber>{contacts.length}</SummaryNumber>
            <SummaryLabel>Total Contacts</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{contacts.filter(c => String(c.trust_tier) === 'tier_1' || String(c.trust_tier) === '1').length}</SummaryNumber>
            <SummaryLabel>High Trust</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{contacts.filter(c => String(c.trust_tier) === 'tier_2' || String(c.trust_tier) === '2').length}</SummaryNumber>
            <SummaryLabel>Medium Trust</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{contacts.filter(c => c.has_augmentation).length}</SummaryNumber>
            <SummaryLabel>Enriched</SummaryLabel>
          </SummaryCard>
        </SummaryGrid>

        <DownloadButton onClick={downloadData}>
          📥 Download Contact Data (JSON)
        </DownloadButton>

        <TableContainer>
          <TableScrollContainer>
            <Table>
              <thead>
                <tr>
                  <TableHeaderCell width="30%">Contact</TableHeaderCell>
                  <TableHeaderCell width="25%">Email</TableHeaderCell>
                  <TableHeaderCell width="15%">Domain</TableHeaderCell>
                  <TableHeaderCell width="10%">Trust</TableHeaderCell>
                  <TableHeaderCell width="10%">Frequency</TableHeaderCell>
                  <TableHeaderCell width="10%">Status</TableHeaderCell>
                </tr>
              </thead>
              <tbody>
                {paginatedContacts.map((contact: any, index: number) => {
                  const email = contact.email || '';
                  const name = contact.name || 
                    email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase());
                  const isExpandable = stepId === 'augment' && contact.has_augmentation;
                  const isExpanded = expandedContact === contact.email;

                  return (
                    <React.Fragment key={contact.email || index}>
                      <ExpandableRow 
                        clickable={isExpandable}
                        onClick={() => isExpandable && setExpandedContact(isExpanded ? null : contact.email)}
                      >
                        <TableCell>
                          <div style={{ fontWeight: 500 }}>{name}</div>
                          {isExpandable && (
                            <div style={{ fontSize: '0.8rem', color: '#666' }}>
                              {isExpanded ? '▼ Click to collapse' : '▶ Click to expand enrichment'}
                            </div>
                          )}
                        </TableCell>
                        <TableCell>{email}</TableCell>
                        <TableCell>{contact.domain || email.split('@')[1] || 'Unknown'}</TableCell>
                        <TableCell>
                          <TrustBadge tier={contact.trust_tier}>
                            {String(contact.trust_tier) === 'tier_1' || String(contact.trust_tier) === '1' ? 'High' :
                             String(contact.trust_tier) === 'tier_2' || String(contact.trust_tier) === '2' ? 'Medium' : 'Low'}
                          </TrustBadge>
                        </TableCell>
                        <TableCell>{contact.frequency || 0}</TableCell>
                        <TableCell>
                          {contact.has_augmentation ? '✅ Enriched' : '⚪ Basic'}
                        </TableCell>
                      </ExpandableRow>
                      
                      {isExpanded && contact.metadata?.enrichment_data && (
                        <tr>
                          <ExpandedContent colSpan={6}>
                            <DetailGrid>
                              <DetailSection>
                                <DetailTitle>📋 Enrichment Summary</DetailTitle>
                                <DetailItem>
                                  <DetailLabel>Confidence:</DetailLabel>
                                  <DetailValue>{Math.round((contact.metadata.enrichment_data.confidence_score || 0) * 100)}%</DetailValue>
                                </DetailItem>
                                <DetailItem>
                                  <DetailLabel>Sources:</DetailLabel>
                                  <DetailValue>{(contact.metadata.enrichment_data.data_sources || []).join(', ')}</DetailValue>
                                </DetailItem>
                                <DetailItem>
                                  <DetailLabel>Last Updated:</DetailLabel>
                                  <DetailValue>{contact.metadata.enrichment_data.enrichment_timestamp || 'Unknown'}</DetailValue>
                                </DetailItem>
                              </DetailSection>
                              
                              {contact.metadata.enrichment_data.person_data && (
                                <DetailSection>
                                  <DetailTitle>👤 Personal Info</DetailTitle>
                                  <DetailItem>
                                    <DetailLabel>Name:</DetailLabel>
                                    <DetailValue>{contact.metadata.enrichment_data.person_data.name || 'Unknown'}</DetailValue>
                                  </DetailItem>
                                  <DetailItem>
                                    <DetailLabel>Title:</DetailLabel>
                                    <DetailValue>{contact.metadata.enrichment_data.person_data.current_title || 'Unknown'}</DetailValue>
                                  </DetailItem>
                                  <DetailItem>
                                    <DetailLabel>Career Stage:</DetailLabel>
                                    <DetailValue>{contact.metadata.enrichment_data.person_data.career_stage || 'Unknown'}</DetailValue>
                                  </DetailItem>
                                </DetailSection>
                              )}
                              
                              {contact.metadata.enrichment_data.company_data && (
                                <DetailSection>
                                  <DetailTitle>🏢 Company Info</DetailTitle>
                                  <DetailItem>
                                    <DetailLabel>Company:</DetailLabel>
                                    <DetailValue>{contact.metadata.enrichment_data.company_data.name || 'Unknown'}</DetailValue>
                                  </DetailItem>
                                  <DetailItem>
                                    <DetailLabel>Industry:</DetailLabel>
                                    <DetailValue>{contact.metadata.enrichment_data.company_data.industry || 'Unknown'}</DetailValue>
                                  </DetailItem>
                                  <DetailItem>
                                    <DetailLabel>Stage:</DetailLabel>
                                    <DetailValue>{contact.metadata.enrichment_data.company_data.company_profile?.company_stage || 'Unknown'}</DetailValue>
                                  </DetailItem>
                                </DetailSection>
                              )}
                              
                              {contact.metadata.enrichment_data.intelligence_summary && (
                                <DetailSection>
                                  <DetailTitle>🧠 Intelligence Summary</DetailTitle>
                                  <DetailItem>
                                    <DetailValue>{JSON.stringify(contact.metadata.enrichment_data.intelligence_summary, null, 2)}</DetailValue>
                                  </DetailItem>
                                </DetailSection>
                              )}
                            </DetailGrid>
                          </ExpandedContent>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </Table>
          </TableScrollContainer>
          
          {totalPages > 1 && (
            <PaginationContainer>
              <PaginationInfo>
                Showing {startIndex + 1}-{Math.min(endIndex, contacts.length)} of {contacts.length} contacts
              </PaginationInfo>
              <PaginationButtons>
                <PaginationButton
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 0}
                >
                  ‹ Previous
                </PaginationButton>
                <PaginationButton
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage >= totalPages - 1}
                >
                  Next ›
                </PaginationButton>
              </PaginationButtons>
            </PaginationContainer>
          )}
        </TableContainer>
      </>
    );
  };

  const renderEmailsView = () => {
    if (!freshData?.emails) {
      return <div>No emails found. Try running the Email Sync step first.</div>;
    }

    const emails = freshData.emails;
    const startIndex = currentPage * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedEmails = emails.slice(startIndex, endIndex);
    const totalPages = Math.ceil(emails.length / pageSize);

    return (
      <>
        <SummaryGrid>
          <SummaryCard>
            <SummaryNumber>{emails.length}</SummaryNumber>
            <SummaryLabel>Total Emails</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{emails.filter(e => e.from?.includes('@')).length}</SummaryNumber>
            <SummaryLabel>Received</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{emails.filter(e => e.to?.includes('@')).length}</SummaryNumber>
            <SummaryLabel>Sent</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{Math.round(emails.reduce((sum, e) => sum + (e.content_length || 0), 0) / emails.length)}</SummaryNumber>
            <SummaryLabel>Avg Length</SummaryLabel>
          </SummaryCard>
        </SummaryGrid>

        <DownloadButton onClick={downloadData}>
          📥 Download Email Data (JSON)
        </DownloadButton>

        <TableContainer>
          <TableScrollContainer>
            <Table>
              <thead>
                <tr>
                  <TableHeaderCell width="25%">Subject</TableHeaderCell>
                  <TableHeaderCell width="20%">From</TableHeaderCell>
                  <TableHeaderCell width="20%">To</TableHeaderCell>
                  <TableHeaderCell width="15%">Date</TableHeaderCell>
                  <TableHeaderCell width="20%">Content Preview</TableHeaderCell>
                </tr>
              </thead>
              <tbody>
                {paginatedEmails.map((email: any, index: number) => (
                  <tr key={email.id || index}>
                    <TableCell>
                      <EmailSubject>{email.subject || '(No Subject)'}</EmailSubject>
                      <div style={{ fontSize: '0.8rem', color: '#666' }}>
                        Length: {email.content_length || 0} chars
                      </div>
                    </TableCell>
                    <TableCell>
                      <div style={{ fontSize: '0.9rem' }}>{email.from || 'Unknown'}</div>
                    </TableCell>
                    <TableCell>
                      <div style={{ fontSize: '0.9rem' }}>
                        {Array.isArray(email.to) ? email.to.join(', ') : (email.to || 'Unknown')}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div style={{ fontSize: '0.9rem' }}>
                        {email.date ? new Date(email.date).toLocaleDateString() : 
                         email.created_at ? new Date(email.created_at).toLocaleDateString() : 'Unknown'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <PreviewText>
                        {email.content_preview || email.content || 'No content preview available'}
                      </PreviewText>
                    </TableCell>
                  </tr>
                ))}
              </tbody>
            </Table>
          </TableScrollContainer>
          
          {totalPages > 1 && (
            <PaginationContainer>
              <PaginationInfo>
                Showing {startIndex + 1}-{Math.min(endIndex, emails.length)} of {emails.length} emails
              </PaginationInfo>
              <PaginationButtons>
                <PaginationButton
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 0}
                >
                  ‹ Previous
                </PaginationButton>
                <PaginationButton
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage >= totalPages - 1}
                >
                  Next ›
                </PaginationButton>
              </PaginationButtons>
            </PaginationContainer>
          )}
        </TableContainer>
      </>
    );
  };

  const renderKnowledgeTreeView = () => {
    if (!freshData?.knowledge_tree) {
      return <div>No knowledge tree found. Try running the Build Knowledge Tree step first.</div>;
    }

    const tree = freshData.knowledge_tree;

    const toggleNode = (nodeId: string) => {
      const newExpanded = new Set(expandedNode);
      if (newExpanded.has(nodeId)) {
        newExpanded.delete(nodeId);
      } else {
        newExpanded.add(nodeId);
      }
      setExpandedNode(newExpanded);
    };

    const renderNode = (node: any, level: number = 0, parentPath: string = ''): React.ReactNode => {
      if (!node) return null;
      
      const nodeId = `${parentPath}/${node.name || node.type || 'unknown'}`;
      const hasChildren = node.children && node.children.length > 0;
      const isExpanded = expandedNode.has(nodeId);

      return (
        <div key={nodeId}>
          <TreeNode 
            level={level} 
            clickable={hasChildren}
            onClick={() => hasChildren && toggleNode(nodeId)}
          >
            <TreeNodeTitle>
              {hasChildren && (isExpanded ? '📂' : '📁')} 
              {node.name || node.type || 'Unknown Node'}
              {node.email && ` (${node.email})`}
            </TreeNodeTitle>
            {node.type && (
              <TreeNodeDetails>
                Type: {node.type}
                {node.domain && ` • Domain: ${node.domain}`}
                {node.trust_tier && ` • Trust: ${node.trust_tier}`}
              </TreeNodeDetails>
            )}
          </TreeNode>
          
          {hasChildren && isExpanded && (
            <div>
              {node.children.map((child: any, index: number) => 
                renderNode(child, level + 1, nodeId)
              )}
            </div>
          )}
        </div>
      );
    };

    return (
      <>
        <SummaryGrid>
          <SummaryCard>
            <SummaryNumber>{tree.metadata?.total_contacts || 0}</SummaryNumber>
            <SummaryLabel>Total Contacts</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{tree.metadata?.total_emails || 0}</SummaryNumber>
            <SummaryLabel>Total Emails</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{tree.root?.children?.length || 0}</SummaryNumber>
            <SummaryLabel>Main Categories</SummaryLabel>
          </SummaryCard>
          <SummaryCard>
            <SummaryNumber>{tree.metadata?.analysis_type || 'N/A'}</SummaryNumber>
            <SummaryLabel>Analysis Type</SummaryLabel>
          </SummaryCard>
        </SummaryGrid>

        <DownloadButton onClick={downloadData}>
          📥 Download Knowledge Tree (JSON)
        </DownloadButton>

        <TableContainer>
          <TableHeader>Knowledge Tree Structure (Click folders to expand)</TableHeader>
          <TableScrollContainer>
            {tree.root && renderNode(tree.root, 0)}
          </TableScrollContainer>
        </TableContainer>
      </>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <LoadingSpinner>
          🔄 Loading {stepName.toLowerCase()} data...
        </LoadingSpinner>
      );
    }

    if (error) {
      return (
        <ErrorMessage>
          ❌ Error loading data: {error}
          <br />
          <button 
            onClick={fetchFreshData} 
            style={{ 
              marginTop: '12px', 
              padding: '8px 16px', 
              background: '#dc3545', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px', 
              cursor: 'pointer' 
            }}
          >
            🔄 Retry
          </button>
        </ErrorMessage>
      );
    }

    switch (stepId) {
      case 'extract':
        return renderContactsView();
      case 'emails':
        return renderEmailsView();
      case 'augment':
        return renderContactsView();
      case 'tree':
        return renderKnowledgeTreeView();
      case 'insights':
        return <div>Strategic insights view coming soon...</div>;
      default:
        return <div>No specific view available for this step.</div>;
    }
  };

  return (
    <ModalOverlay onClick={(e) => e.target === e.currentTarget && onClose()}>
      <ModalContainer>
        <ModalHeader>
          <ModalTitle>
            📊 Inspect: {stepName}
          </ModalTitle>
          <CloseButton onClick={onClose}>
            ✕
          </CloseButton>
        </ModalHeader>
        <ModalBody>
          {renderContent()}
        </ModalBody>
      </ModalContainer>
    </ModalOverlay>
  );
};

export default Modal; 