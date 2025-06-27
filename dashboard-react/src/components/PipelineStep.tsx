import React from 'react';
import styled from 'styled-components';

const StepContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'status'
})<{ status: string }>`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => {
    switch (props.status) {
      case 'running': return props.theme.colors.warning;
      case 'stopping': return '#ff9800';
      case 'stopped': return '#9e9e9e';
      case 'completed': return props.theme.colors.success;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.border;
    }
  }};
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.lg};
  box-shadow: ${props => props.theme.shadow};
  transition: all 0.3s ease;

  &:hover {
    box-shadow: ${props => props.theme.shadowHover};
    transform: translateY(-2px);
  }
`;

const StepHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const StepInfo = styled.div`
  flex: 1;
`;

const StepNumber = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'status'
})<{ status: string }>`
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'running': return props.theme.colors.warning;
      case 'stopping': return '#ff9800';
      case 'stopped': return '#9e9e9e';
      case 'completed': return props.theme.colors.success;
      case 'error': return props.theme.colors.error;
      default: return props.theme.colors.accent;
    }
  }};
  color: ${props => props.theme.colors.text};
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-right: ${props => props.theme.spacing.md};
`;

const StepTitle = styled.h3`
  color: ${props => props.theme.colors.text};
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const StepDescription = styled.p`
  color: ${props => props.theme.colors.textSecondary};
  font-size: 0.9rem;
`;

const StepActions = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  align-items: center;
`;

const ActionButton = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'variant'
})<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
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
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  font-size: 0.9rem;
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
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const StatusIcon = styled.span.withConfig({
  shouldForwardProp: (prop) => prop !== 'status'
})<{ status: string }>`
  margin-left: ${props => props.theme.spacing.sm};
  font-size: 1rem;
  
  &:after {
    content: '${props => {
      switch (props.status) {
        case 'running': return '⏳';
        case 'stopping': return '⏸️';
        case 'stopped': return '⏹️';
        case 'completed': return '✅';
        case 'error': return '❌';
        default: return '⚪';
      }
    }}';
  }
`;

const ProgressContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'visible'
})<{ visible: boolean }>`
  margin-top: ${props => props.theme.spacing.md};
  opacity: ${props => props.visible ? 1 : 0};
  max-height: ${props => props.visible ? '120px' : '0'};
  overflow: hidden;
  transition: all 0.3s ease;
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: ${props => props.theme.colors.border};
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const ProgressFill = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'progress'
})<{ progress: number }>`
  height: 100%;
  width: ${props => props.progress}%;
  background: ${props => props.theme.colors.primary};
  transition: width 0.3s ease;
`;

const ProgressInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.xs};
`;

const ProgressText = styled.div`
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.8rem;
`;

const ProgressDetails = styled.div`
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.75rem;
  margin-top: ${props => props.theme.spacing.xs};
  padding: ${props => props.theme.spacing.xs};
  background: ${props => props.theme.colors.background || '#f8f9fa'};
  border-radius: 4px;
  border-left: 3px solid ${props => props.theme.colors.primary};
`;

const ResumeInfo = styled.div`
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 4px;
  padding: ${props => props.theme.spacing.sm};
  margin-top: ${props => props.theme.spacing.sm};
  font-size: 0.8rem;
  color: #856404;
`;

interface StepData {
  id: string;
  name: string;
  description: string;
  endpoint?: string;
  method?: string;
}

interface JobStatus {
  status: 'started' | 'running' | 'stopping' | 'stopped' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
  // Enhanced progress tracking
  enrichment_phase?: string;
  sync_phase?: string;
  current_contact?: string;
  emails_found?: number;
  contacts_completed?: number;
  contacts_total?: number;
  enriched_contacts_count?: number;
  stored_count?: number;
  // Resume information
  resume_info?: {
    can_resume: boolean;
    next_step?: string;
    reason?: string;
    contacts_remaining?: number;
    progress_checkpoint?: number;
  };
  partial_result?: any;
}

interface PipelineStepProps {
  step: StepData;
  index: number;
  status: string;
  progress: number;
  result?: any;
  jobStatus?: JobStatus; // Enhanced job status with detailed info
  onExecute: () => void;
  onStop?: () => void; // New stop function
  onInspect: () => void;
  onConfigure?: () => void;
  disabled: boolean;
  config?: any;
}

const PipelineStep: React.FC<PipelineStepProps> = ({
  step,
  index,
  status,
  progress,
  result,
  jobStatus,
  onExecute,
  onStop,
  onInspect,
  onConfigure,
  disabled,
  config
}) => {
  const isRunning = status === 'running';
  const isStopping = status === 'stopping';
  const isStopped = status === 'stopped';
  const hasResult = result && (result.success !== false);
  const canStop = isRunning && onStop && !isStopping;
  const canResume = isStopped && jobStatus?.resume_info?.can_resume;

  // Get detailed progress information
  const getProgressMessage = () => {
    if (!jobStatus?.message) {
      return isRunning ? `Running... ${progress}%` : 
             status === 'completed' ? 'Completed' :
             status === 'stopped' ? 'Stopped' :
             status === 'error' ? 'Error occurred' : '';
    }
    return jobStatus.message;
  };

  const getProgressDetails = () => {
    if (!jobStatus) return null;

    const details = [];
    
    // Add phase-specific information
    if (jobStatus.enrichment_phase) {
      details.push(`Phase: ${jobStatus.enrichment_phase.replace(/_/g, ' ')}`);
    }
    if (jobStatus.sync_phase) {
      details.push(`Phase: ${jobStatus.sync_phase.replace(/_/g, ' ')}`);
    }
    
    // Add current contact being processed
    if (jobStatus.current_contact) {
      details.push(`Processing: ${jobStatus.current_contact}`);
    }
    
    // Add counts and statistics
    if (jobStatus.contacts_completed && jobStatus.contacts_total) {
      details.push(`Contacts: ${jobStatus.contacts_completed}/${jobStatus.contacts_total}`);
    }
    if (jobStatus.emails_found !== undefined) {
      details.push(`Emails found: ${jobStatus.emails_found}`);
    }
    if (jobStatus.enriched_contacts_count !== undefined) {
      details.push(`Enriched: ${jobStatus.enriched_contacts_count}`);
    }
    if (jobStatus.stored_count !== undefined) {
      details.push(`Stored: ${jobStatus.stored_count}`);
    }
    
    return details.length > 0 ? details.join(' • ') : null;
  };

  return (
    <StepContainer status={status}>
      <StepHeader>
        <StepNumber status={status}>
          {index + 1}
        </StepNumber>
        
        <StepInfo>
          <StepTitle>
            {step.name}
            <StatusIcon status={status} />
          </StepTitle>
          <StepDescription>{step.description}</StepDescription>
        </StepInfo>

        <StepActions>
          {onConfigure && (
            <ActionButton
              onClick={onConfigure}
              disabled={isRunning || isStopping}
              title="Configure step parameters"
            >
              ⚙️ Config
            </ActionButton>
          )}
          
          {canStop && (
            <ActionButton
              variant="danger"
              onClick={onStop}
              disabled={isStopping}
              title="Stop this process safely"
            >
              {isStopping ? 'Stopping...' : '⏹️ Stop'}
            </ActionButton>
          )}
          
          <ActionButton
            variant="primary"
            onClick={onExecute}
            disabled={disabled || isRunning || isStopping}
          >
            {isRunning ? 'Running...' : 
             isStopping ? 'Stopping...' :
             canResume ? '🔄 Resume' : '▶️ Run'}
          </ActionButton>
          
          <ActionButton
            onClick={onInspect}
            disabled={isRunning || isStopping}
            title="Inspect stored data for this step"
          >
            📊 Inspect
          </ActionButton>
        </StepActions>
      </StepHeader>

      {config && (config.days || config.limit) && (
        <div style={{ 
          fontSize: '0.8rem', 
          color: '#666', 
          marginBottom: '8px',
          fontStyle: 'italic'
        }}>
          {config.days && `📅 ${config.days} days back`}
          {config.limit && ` • 📝 ${config.limit} items max`}
        </div>
      )}

      {/* Resume information for stopped jobs */}
      {canResume && jobStatus?.resume_info && (
        <ResumeInfo>
          ⏸️ <strong>Stopped:</strong> {jobStatus.resume_info.reason || 'Process was stopped safely'}
          {jobStatus.resume_info.contacts_remaining && (
            <span> • {jobStatus.resume_info.contacts_remaining} items remaining</span>
          )}
          <br />
          <small>You can resume where you left off or start over.</small>
        </ResumeInfo>
      )}

      <ProgressContainer visible={isRunning || isStopping || status === 'completed' || isStopped}>
        <ProgressInfo>
          <ProgressText>{getProgressMessage()}</ProgressText>
          <ProgressText>{Math.round(progress)}%</ProgressText>
        </ProgressInfo>
        
        <ProgressBar>
          <ProgressFill progress={progress} />
        </ProgressBar>
        
        {getProgressDetails() && (
          <ProgressDetails>
            {getProgressDetails()}
          </ProgressDetails>
        )}
      </ProgressContainer>
    </StepContainer>
  );
};

export default PipelineStep; 