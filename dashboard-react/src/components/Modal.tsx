import React from 'react';
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
  max-width: 1000px;
  max-height: 85vh;
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
`;

const TableContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  overflow: hidden;
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const TableHeader = styled.thead`
  background: ${props => props.theme.colors.accent};
`;

const TableHeaderCell = styled.th`
  padding: ${props => props.theme.spacing.md};
  text-align: left;
  color: ${props => props.theme.colors.text};
  font-weight: 600;
  font-size: 0.9rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
`;

const TableBody = styled.tbody``;

const TableRow = styled.tr`
  &:nth-child(even) {
    background: ${props => props.theme.colors.background};
  }
  
  &:hover {
    background: ${props => props.theme.colors.surfaceHover};
  }
`;

const TableCell = styled.td`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  color: ${props => props.theme.colors.text};
  font-size: 0.85rem;
  border-bottom: 1px solid ${props => props.theme.colors.border};
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const SummaryCards = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

const DataContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  padding: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.md};
`;

const DataLabel = styled.div`
  color: ${props => props.theme.colors.textSecondary};
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: ${props => props.theme.spacing.xs};
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const DataValue = styled.pre`
  color: ${props => props.theme.colors.text};
  font-size: 0.8rem;
  line-height: 1.4;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: ${props => props.theme.colors.background};
  padding: ${props => props.theme.spacing.sm};
  border-radius: calc(${props => props.theme.borderRadius} / 3);
  border: 1px solid ${props => props.theme.colors.border};
  max-height: 300px;
  overflow-y: auto;
`;

const EmptyState = styled.div`
  text-align: center;
  color: ${props => props.theme.colors.textMuted};
  font-style: italic;
  padding: ${props => props.theme.spacing.xl};
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

interface ModalProps {
  stepId: string;
  stepName: string;
  data: any;
  onClose: () => void;
}

const Modal: React.FC<ModalProps> = ({ stepId, stepName, data, onClose }) => {
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

  const formatData = (obj: any): string => {
    if (!obj) return 'No data available';
    
    try {
      return JSON.stringify(obj, null, 2);
    } catch (error) {
      return String(obj);
    }
  };

  const getContactsData = () => {
    if (!data) return null;
    
    // Check for contacts in various possible locations
    const contacts = data.contacts || data.results || data.data || [];
    
    // Debug logging
    console.log('🔍 Modal data structure:', {
      hasData: !!data,
      dataKeys: data ? Object.keys(data) : [],
      contactsLength: Array.isArray(contacts) ? contacts.length : 'not array',
      contactsType: typeof contacts,
      sampleData: data ? JSON.stringify(data).substring(0, 200) + '...' : 'no data'
    });
    
    if (Array.isArray(contacts) && contacts.length > 0) {
      return contacts;
    }
    
    return null;
  };

  const getDebugInfo = () => {
    if (!data) return { hasData: false };
    
    return {
      hasData: true,
      dataKeys: Object.keys(data),
      success: data.success,
      error: data.error,
      contactsLength: Array.isArray(data.contacts) ? data.contacts.length : 'not array',
      totalSentEmails: data.total_sent_emails,
      message: data.message,
      fullDataPreview: JSON.stringify(data, null, 2).substring(0, 500) + '...'
    };
  };

  const renderContactsTable = (contacts: any[]) => {
    if (!contacts || !Array.isArray(contacts) || contacts.length === 0) return null;

    // Get all unique keys from all contacts for table headers
    const allKeys = new Set<string>();
    contacts.forEach(contact => {
      Object.keys(contact).forEach(key => allKeys.add(key));
    });

    const headers = Array.from(allKeys).slice(0, 6); // Limit to 6 columns for readability

    return (
      <TableContainer>
        <Table>
          <TableHeader>
            <TableRow>
              {headers.map(header => (
                <TableHeaderCell key={header}>
                  {header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </TableHeaderCell>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {contacts.slice(0, 50).map((contact, index) => (
              <TableRow key={index}>
                {headers.map(header => (
                  <TableCell key={header} title={String(contact[header] || '')}>
                    {String(contact[header] || '-')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {contacts.length > 50 && (
          <div style={{ padding: '12px', textAlign: 'center', color: '#666', fontSize: '0.8rem' }}>
            Showing first 50 of {contacts.length} contacts. Download JSON for full data.
          </div>
        )}
      </TableContainer>
    );
  };

  const getSummaryStats = () => {
    if (!data) return {};
    
    const stats: Record<string, any> = {};
    
    // Extract common statistics
    if (data.email_count || data.emails_processed) stats['Emails'] = data.email_count || data.emails_processed;
    if (data.contacts_extracted || data.contact_count) stats['Contacts'] = data.contacts_extracted || data.contact_count;
    if (data.enriched_count || data.contacts_enriched) stats['Enriched'] = data.enriched_count || data.contacts_enriched;
    if (data.nodes_created || data.knowledge_nodes) stats['Nodes'] = data.nodes_created || data.knowledge_nodes;
    if (data.processing_time) stats['Time'] = `${data.processing_time}s`;
    
    // Count contacts if available
    const contacts = getContactsData();
    if (contacts) stats['Total Items'] = contacts.length;
    
    return stats;
  };

  const contacts = getContactsData();
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
                <DataContainer>
                  <DataLabel>Summary</DataLabel>
                  <DataValue>{data.message}</DataValue>
                </DataContainer>
              )}

              {data.error && (
                <DataContainer>
                  <DataLabel>Error Details</DataLabel>
                  <DataValue style={{ color: '#dc3545' }}>{data.error}</DataValue>
                </DataContainer>
              )}

              {/* Debug Section - Always show for extract step */}
              {stepId === 'extract' && (
                <DataContainer>
                  <DataLabel>🔍 Contact Detection Debug</DataLabel>
                  <DataValue>
                    {`Data Keys: ${Object.keys(data).join(', ')}
Success: ${data.success}
Contacts Array: ${Array.isArray(data.contacts) ? `Found ${data.contacts.length} contacts` : 'Not an array or missing'}
Total Sent Emails: ${data.total_sent_emails || 'unknown'}
First Contact Sample: ${data.contacts && data.contacts[0] ? JSON.stringify(data.contacts[0], null, 2) : 'No contacts found'}`}
                  </DataValue>
                </DataContainer>
              )}

              {contacts && contacts.length > 0 && (
                <>
                  <DataContainer>
                    <DataLabel>📊 Contacts Found</DataLabel>
                    <DataValue>Found {contacts.length} contacts - showing table below</DataValue>
                  </DataContainer>
                  {renderContactsTable(contacts)}
                </>
              )}

              {(!contacts || contacts.length === 0) && stepId === 'extract' && (
                <DataContainer>
                  <DataLabel>⚠️ No Contacts Table</DataLabel>
                  <DataValue style={{ color: '#dc3545' }}>
                    {`Table not showing because:
• Contacts detected: ${contacts ? 'Yes but empty' : 'No'}
• Contacts length: ${contacts ? contacts.length : 'undefined'}
• Array check: ${Array.isArray(contacts)}

Raw contacts data: ${JSON.stringify(data.contacts || 'undefined', null, 2)}`}
                  </DataValue>
                </DataContainer>
              )}

              <DataContainer>
                <DataLabel>Full Response Data</DataLabel>
                <DataValue>{formatData(data)}</DataValue>
              </DataContainer>
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