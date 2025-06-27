import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';
import PipelineStep from './PipelineStep';
import AuthButton from './AuthButton';
import ProgressDisplay from './ProgressDisplay';
import Modal from './Modal';
import { pollJobStatus, cancelJob, JobStatus } from '../utils/api';

const DashboardContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: ${props => props.theme.spacing.lg};
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: ${props => props.theme.spacing.xxl};
  position: relative;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: 300;
  letter-spacing: -0.5px;
  margin-bottom: ${props => props.theme.spacing.md};
  background: linear-gradient(135deg, ${props => props.theme.colors.text} 0%, ${props => props.theme.colors.textSecondary} 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Subtitle = styled.p`
  color: ${props => props.theme.colors.textMuted};
  font-size: 1.1rem;
  margin-bottom: ${props => props.theme.spacing.xl};
`;

const StepsContainer = styled.div`
  display: grid;
  gap: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xxl};
`;

const ControlsContainer = styled.div`
  display: flex;
  justify-content: center;
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.xxl};
`;

const ActionButton = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'variant'
})<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  background: ${props => {
    switch (props.variant) {
      case 'primary': return props.theme.colors.primary;
      case 'danger': return '#dc3545';
      default: return props.theme.colors.surface;
    }
  }};
  color: ${props => 
    props.variant === 'primary' || props.variant === 'danger' 
      ? 'white' 
      : props.theme.colors.text
  };
  border: 1px solid ${props => {
    switch (props.variant) {
      case 'primary': return props.theme.colors.primary;
      case 'danger': return '#dc3545';
      default: return props.theme.colors.border;
    }
  }};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    background: ${props => {
      switch (props.variant) {
        case 'primary': return props.theme.colors.primaryHover || '#0056b3';
        case 'danger': return '#c82333';
        default: return props.theme.colors.surfaceHover || '#f8f9fa';
      }
    }};
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const LogoutButton = styled.button`
  position: absolute;
  top: 0;
  right: 0;
  background: #dc3545;
  color: white;
  border: none;
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  border-radius: ${props => props.theme.borderRadius};
  cursor: pointer;
  font-size: 0.9rem;
  
  &:hover {
    background: #c82333;
  }
`;

const StatusIcon = styled.span.withConfig({
  shouldForwardProp: (prop) => prop !== 'status'
})<{ status: string }>`
  margin-left: ${props => props.theme.spacing.xs};
  
  &:before {
    content: '${props => {
      switch (props.status) {
        case 'running': return '⏳';
        case 'completed': return '✅';
        case 'error': return '❌';
        default: return '⚪';
      }
    }}';
  }
`;

const ConfigModal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const ConfigContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.xl};
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
`;

const ConfigTitle = styled.h3`
  color: ${props => props.theme.colors.text};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const ConfigField = styled.div`
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const ConfigLabel = styled.label`
  display: block;
  color: ${props => props.theme.colors.text};
  font-weight: 500;
  margin-bottom: ${props => props.theme.spacing.sm};
`;

const ConfigInput = styled.input`
  width: 100%;
  padding: ${props => props.theme.spacing.sm};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  background: ${props => props.theme.colors.background};
  color: ${props => props.theme.colors.text};
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const ConfigActions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  justify-content: flex-end;
  margin-top: ${props => props.theme.spacing.lg};
`;

const ConfigButton = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'variant'
})<{ variant?: 'primary' }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.lg};
  background: ${props => 
    props.variant === 'primary' 
      ? props.theme.colors.primary 
      : props.theme.colors.surface
  };
  color: ${props => 
    props.variant === 'primary' 
      ? 'white' 
      : props.theme.colors.text
  };
  border: 1px solid ${props => 
    props.variant === 'primary' 
      ? props.theme.colors.primary 
      : props.theme.colors.border
  };
  border-radius: ${props => props.theme.borderRadius};
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: ${props => 
      props.variant === 'primary' 
        ? props.theme.colors.primaryHover || '#0056b3'
        : props.theme.colors.surfaceHover || '#f8f9fa'
    };
  }
`;

const DangerZone = styled.div`
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.lg};
  text-align: center;
`;

const DangerTitle = styled.h3`
  color: #856404;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const DangerButton = styled(ActionButton)`
  background: #dc3545;
  border-color: #dc3545;
  color: white;
  
  &:hover:not(:disabled) {
    background: #c82333;
    border-color: #bd2130;
  }
`;

const ConfirmDialog = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  padding: ${props => props.theme.spacing.lg};
`;

const ConfirmContainer = styled.div`
  background: ${props => props.theme.colors.background};
  border: 2px solid #dc3545;
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.shadowHover};
  width: 100%;
  max-width: 500px;
  padding: ${props => props.theme.spacing.xl};
  text-align: center;
`;

const ConfirmTitle = styled.h3`
  color: #dc3545;
  margin-bottom: ${props => props.theme.spacing.lg};
  font-size: 1.3rem;
`;

const ConfirmText = styled.p`
  color: ${props => props.theme.colors.text};
  margin-bottom: ${props => props.theme.spacing.lg};
  line-height: 1.6;
`;

const ConfirmActions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.md};
  justify-content: center;
`;

interface PipelineState {
  isRunning: boolean;
  currentStep: number;
  stepResults: Record<string, any>;
}

interface StepData {
  id: string;
  name: string;
  description: string;
  endpoint?: string;
  method?: string;
}

interface DashboardProps {
  onAuthChange: (authenticated: boolean) => void;
}

const PIPELINE_STEPS: StepData[] = [
  {
    id: 'extract',
    name: 'Extract Contacts',
    description: 'Analyze sent emails to extract trusted contacts and build network',
    endpoint: '/api/gmail/analyze-sent',
    method: 'POST'
  },
  {
    id: 'emails',
    name: 'Sync Emails',
    description: 'Connect to Gmail and extract email data',
    endpoint: '/api/emails/sync',
    method: 'POST'
  },
  {
    id: 'augment',
    name: 'Augment Contacts',
    description: 'Enrich contacts with intelligence and web data',
    endpoint: '/api/intelligence/enrich-contacts',
    method: 'POST'
  },
  {
    id: 'tree',
    name: 'Build Knowledge Tree',
    description: 'Analyze relationships and create knowledge structure',
    endpoint: '/api/intelligence/build-knowledge-tree',
    method: 'POST'
  },
  {
    id: 'insights',
    name: 'Generate Insights',
    description: 'Create strategic intelligence and recommendations',
    endpoint: '/api/intelligence/strategic-analysis',
    method: 'POST'
  }
];

const Dashboard: React.FC<DashboardProps> = ({ onAuthChange }) => {
  const [pipelineState, setPipelineState] = useState<PipelineState>({
    isRunning: false,
    currentStep: 0,
    stepResults: {}
  });
  
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [selectedModal, setSelectedModal] = useState<string | null>(null);
  const [stepStatuses, setStepStatuses] = useState<Record<string, string>>({});
  const [stepProgress, setStepProgress] = useState<Record<string, number>>({});
  const [stepJobIds, setStepJobIds] = useState<Record<string, string>>({});
  const [stepJobStatuses, setStepJobStatuses] = useState<Record<string, JobStatus>>({});
  const [showConfigModal, setShowConfigModal] = useState<string | null>(null);
  const [stepConfigs, setStepConfigs] = useState<Record<string, any>>({
    emails: { days: 365 }, // Default to 1 year for comprehensive contact extraction
    extract: { days: 365 }
  });
  const [showFlushConfirm, setShowFlushConfirm] = useState(false);

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      const response = await axios.get('/api/auth/status');
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    }
  };

  const stopStep = async (stepId: string) => {
    const jobId = stepJobIds[stepId];
    if (!jobId) {
      console.warn(`No job ID found for step ${stepId}`);
      return;
    }

    console.log(`🛑 Stopping step ${stepId} (job ${jobId})`);
    
    // Immediately update UI to show stopping state
    setStepStatuses(prev => ({ ...prev, [stepId]: 'stopping' }));
    
    try {
      const success = await cancelJob(jobId);
      if (success) {
        console.log(`✅ Stop request sent for step ${stepId}`);
        // The polling will pick up the stopped status
      } else {
        console.error(`❌ Failed to stop step ${stepId}`);
        // Revert status if stop failed
        setStepStatuses(prev => ({ ...prev, [stepId]: 'running' }));
      }
    } catch (error) {
      console.error(`❌ Error stopping step ${stepId}:`, error);
      // Revert status if stop failed
      setStepStatuses(prev => ({ ...prev, [stepId]: 'running' }));
    }
  };

  const executeStep = async (stepId: string) => {
    const step = PIPELINE_STEPS.find(s => s.id === stepId);
    if (!step || !step.endpoint) return;

    try {
      setStepStatuses(prev => ({ ...prev, [stepId]: 'running' }));
      setStepProgress(prev => ({ ...prev, [stepId]: 0 }));

      // Get configuration for this step
      const config = stepConfigs[stepId] || {};
      
      // Prepare request data based on step type
      let requestData = {};
      if (stepId === 'emails') {
        requestData = { days: config.days || 365 };
      } else if (stepId === 'extract') {
        requestData = { lookback_days: config.days || 365 };
      } else if (stepId === 'augment') {
        requestData = {
          sources: ['email_signatures', 'email_content', 'domain_intelligence'],
          limit: 100
        };
      }

      const response = await axios({
        method: step.method || 'POST',
        url: step.endpoint,
        data: requestData
      });

      // Check if this is a background job
      if (response.data.job_id && response.data.status_url) {
        console.log(`Background job started: ${response.data.job_id}`);
        
        // Store job ID for stop functionality
        setStepJobIds(prev => ({ ...prev, [stepId]: response.data.job_id }));
        
        // Poll for job completion with enhanced progress tracking
        try {
          const result = await pollJobStatus(
            response.data.job_id,
            response.data.status_url,
            (progress, jobStatus) => {
              setStepProgress(prev => ({ ...prev, [stepId]: progress }));
              if (jobStatus) {
                setStepJobStatuses(prev => ({ ...prev, [stepId]: jobStatus }));
                // Update status based on job status
                if (jobStatus.status === 'stopping') {
                  setStepStatuses(prev => ({ ...prev, [stepId]: 'stopping' }));
                } else if (jobStatus.status === 'stopped') {
                  setStepStatuses(prev => ({ ...prev, [stepId]: 'stopped' }));
                }
              }
            }
          );
          
          if (result.stopped) {
            // Job was stopped by user
            setStepStatuses(prev => ({ ...prev, [stepId]: 'stopped' }));
            setPipelineState(prev => ({
              ...prev,
              stepResults: { ...prev.stepResults, [stepId]: result }
            }));
          } else {
            // Job completed normally
            setPipelineState(prev => ({
              ...prev,
              stepResults: { ...prev.stepResults, [stepId]: result }
            }));
            setStepStatuses(prev => ({ ...prev, [stepId]: 'completed' }));
          }
        } catch (error) {
          console.error(`Step ${stepId} failed:`, error);
          setStepStatuses(prev => ({ ...prev, [stepId]: 'error' }));
          setStepProgress(prev => ({ ...prev, [stepId]: 0 }));
        } finally {
          // Clean up job tracking
          setStepJobIds(prev => {
            const newJobIds = { ...prev };
            delete newJobIds[stepId];
            return newJobIds;
          });
        }
      } else {
        // Synchronous response
        setPipelineState(prev => ({
          ...prev,
          stepResults: { ...prev.stepResults, [stepId]: response.data }
        }));
        setStepStatuses(prev => ({ ...prev, [stepId]: 'completed' }));
        setStepProgress(prev => ({ ...prev, [stepId]: 100 }));
      }
    } catch (error) {
      console.error(`Step ${stepId} failed:`, error);
      setStepStatuses(prev => ({ ...prev, [stepId]: 'error' }));
      setStepProgress(prev => ({ ...prev, [stepId]: 0 }));
    }
  };

  const stopAllJobs = async () => {
    console.log('🛑 Stopping all running jobs...');
    const runningSteps = Object.entries(stepStatuses)
      .filter(([_, status]) => status === 'running')
      .map(([stepId, _]) => stepId);
    
    for (const stepId of runningSteps) {
      await stopStep(stepId);
    }
  };

  const openStepConfig = (stepId: string) => {
    setShowConfigModal(stepId);
  };

  const closeStepConfig = () => {
    setShowConfigModal(null);
  };

  const saveStepConfig = (stepId: string, config: any) => {
    setStepConfigs(prev => ({
      ...prev,
      [stepId]: { ...prev[stepId], ...config }
    }));
    setShowConfigModal(null);
  };

  const flushDatabase = async () => {
    try {
      console.log('🗑️ Flushing database...');
      const response = await axios.post('/api/system/flush');
      
      if (response.data.success) {
        alert('Database flushed successfully! Please refresh the page and re-authenticate.');
        // Clear local state
        setPipelineState({
          isRunning: false,
          currentStep: 0,
          stepResults: {}
        });
        setStepStatuses({});
        setStepProgress({});
        setStepJobIds({});
        setStepJobStatuses({});
        // Force logout to re-authenticate
        onAuthChange(false);
      } else {
        alert('Database flush failed: ' + response.data.error);
      }
    } catch (error) {
      console.error('Database flush failed:', error);
      alert('Database flush failed. Check console for details.');
    } finally {
      setShowFlushConfirm(false);
    }
  };

  const runFullPipeline = async () => {
    if (!isAuthenticated) {
      alert('Please authenticate first');
      return;
    }

    setPipelineState(prev => ({ ...prev, isRunning: true }));
    
    for (let i = 0; i < PIPELINE_STEPS.length; i++) {
      const step = PIPELINE_STEPS[i];
      setPipelineState(prev => ({ ...prev, currentStep: i }));
      
      // Check if should stop pipeline
      if (Object.values(stepStatuses).some(status => status === 'stopped')) {
        console.log('Pipeline stopped by user');
        break;
      }
      
      await executeStep(step.id);
    }
    
    setPipelineState(prev => ({ ...prev, isRunning: false, currentStep: 0 }));
  };

  const resetPipeline = () => {
    setPipelineState({
      isRunning: false,
      currentStep: 0,
      stepResults: {}
    });
    setStepStatuses({});
    setStepProgress({});
    setStepJobIds({});
    setStepJobStatuses({});
  };

  const handleLogout = async () => {
    try {
      console.log('Logging out...');
      
      // Stop any running jobs first
      await stopAllJobs();
      
      // Immediately update local state to show login page
      onAuthChange(false);
      
      // Clear backend session (fire and forget - don't wait for response)
      fetch('/logout', { method: 'GET' }).catch(console.error);
      
    } catch (error) {
      console.error('Logout failed:', error);
      // Still force logout by clearing local state
      onAuthChange(false);
    }
  };

  const hasRunningJobs = Object.values(stepStatuses).some(status => 
    status === 'running' || status === 'stopping'
  );

  return (
    <DashboardContainer>
      <Header>
        <LogoutButton onClick={handleLogout}>
          🔓 Logout
        </LogoutButton>
        <Title>Strategic Intelligence System</Title>
        <Subtitle>CEO-Grade Personal AI Intelligence Platform</Subtitle>
        <AuthButton 
          isAuthenticated={isAuthenticated} 
          onAuthChange={setIsAuthenticated} 
        />
      </Header>

      <ProgressDisplay 
        currentStep={pipelineState.currentStep}
        isRunning={pipelineState.isRunning}
        steps={PIPELINE_STEPS}
      />

      <StepsContainer>
        {PIPELINE_STEPS.map((step, index) => (
          <PipelineStep
            key={step.id}
            step={step}
            index={index}
            status={stepStatuses[step.id] || 'ready'}
            progress={stepProgress[step.id] || 0}
            result={pipelineState.stepResults[step.id]}
            jobStatus={stepJobStatuses[step.id]}
            onExecute={() => executeStep(step.id)}
            onStop={() => stopStep(step.id)}
            onInspect={() => setSelectedModal(step.id)}
            onConfigure={['emails', 'extract'].includes(step.id) ? () => openStepConfig(step.id) : undefined}
            disabled={!isAuthenticated || (pipelineState.isRunning && step.id !== PIPELINE_STEPS[pipelineState.currentStep]?.id)}
            config={stepConfigs[step.id]}
          />
        ))}
      </StepsContainer>

      <ControlsContainer>
        <ActionButton
          variant="primary"
          onClick={runFullPipeline}
          disabled={!isAuthenticated || pipelineState.isRunning || hasRunningJobs}
        >
          {pipelineState.isRunning ? 'Running Pipeline...' : 'Run Full Pipeline'}
        </ActionButton>
        
        {hasRunningJobs && (
          <ActionButton
            variant="danger"
            onClick={stopAllJobs}
            title="Stop all running processes"
          >
            ⏹️ Stop All
          </ActionButton>
        )}
        
        <ActionButton
          onClick={resetPipeline}
          disabled={pipelineState.isRunning || hasRunningJobs}
        >
          Reset Pipeline
        </ActionButton>
      </ControlsContainer>

      <DangerZone>
        <DangerTitle>⚠️ Danger Zone</DangerTitle>
        <p style={{ color: '#666', marginBottom: '16px', fontSize: '0.9rem' }}>
          Clear all data to start fresh. This will delete all contacts, emails, and analysis results.
        </p>
        <DangerButton
          onClick={() => setShowFlushConfirm(true)}
          disabled={pipelineState.isRunning || hasRunningJobs}
        >
          🗑️ Flush Database
        </DangerButton>
      </DangerZone>

      {selectedModal && (
        <Modal
          stepId={selectedModal}
          stepName={PIPELINE_STEPS.find(s => s.id === selectedModal)?.name || ''}
          data={pipelineState.stepResults[selectedModal]}
          onClose={() => setSelectedModal(null)}
        />
      )}

      {showFlushConfirm && (
        <ConfigModal onClick={(e) => e.target === e.currentTarget && setShowFlushConfirm(false)}>
          <ConfigContainer>
            <ConfigTitle>⚠️ Confirm Database Flush</ConfigTitle>
            <p style={{ marginBottom: '20px', color: '#666' }}>
              This will permanently delete all your data including:
              <br />• All contacts and enrichment data
              <br />• All synced emails
              <br />• Knowledge trees and analysis results
              <br /><br />
              <strong>This action cannot be undone!</strong>
            </p>
            <ConfigActions>
              <ConfigButton onClick={() => setShowFlushConfirm(false)}>
                Cancel
              </ConfigButton>
              <ConfigButton variant="primary" onClick={flushDatabase}>
                🗑️ Flush Database
              </ConfigButton>
            </ConfigActions>
          </ConfigContainer>
        </ConfigModal>
      )}

      {showConfigModal && (
        <ConfigModal onClick={(e) => e.target === e.currentTarget && closeStepConfig()}>
          <ConfigContainer>
            <ConfigTitle>
              Configure {PIPELINE_STEPS.find(s => s.id === showConfigModal)?.name}
            </ConfigTitle>
            
            {showConfigModal === 'emails' && (
              <>
                <ConfigField>
                  <ConfigLabel>Days Back to Sync</ConfigLabel>
                  <ConfigInput
                    type="number"
                    min="1"
                    max="3650"
                    value={stepConfigs.emails?.days || 365}
                    onChange={(e) => {
                      const days = parseInt(e.target.value) || 365;
                      setStepConfigs(prev => ({
                        ...prev,
                        emails: { ...prev.emails, days }
                      }));
                    }}
                    placeholder="365"
                  />
                  <small style={{ color: '#666', fontSize: '0.8rem' }}>
                    Number of days back to fetch emails (1-3650). Default: 365 days (1 year)
                  </small>
                </ConfigField>
              </>
            )}

            {showConfigModal === 'extract' && (
              <>
                <ConfigField>
                  <ConfigLabel>Days Back to Extract Contacts</ConfigLabel>
                  <ConfigInput
                    type="number"
                    min="1"
                    max="3650"
                    value={stepConfigs.extract?.days || 365}
                    onChange={(e) => {
                      const days = parseInt(e.target.value) || 365;
                      setStepConfigs(prev => ({
                        ...prev,
                        extract: { ...prev.extract, days }
                      }));
                    }}
                    placeholder="365"
                  />
                  <small style={{ color: '#666', fontSize: '0.8rem' }}>
                    Number of days back to analyze for contact extraction. Default: 365 days (1 year)
                  </small>
                </ConfigField>
              </>
            )}

            <ConfigActions>
              <ConfigButton onClick={closeStepConfig}>
                Cancel
              </ConfigButton>
              <ConfigButton 
                variant="primary" 
                onClick={() => saveStepConfig(showConfigModal, stepConfigs[showConfigModal])}
              >
                Save Configuration
              </ConfigButton>
            </ConfigActions>
          </ConfigContainer>
        </ConfigModal>
      )}
    </DashboardContainer>
  );
};

export default Dashboard; 