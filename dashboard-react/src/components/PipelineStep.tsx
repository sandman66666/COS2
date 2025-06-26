import React from 'react';
import styled from 'styled-components';

const StepContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'status'
})<{ status: string }>`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => {
    switch (props.status) {
      case 'running': return props.theme.colors.warning;
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
`;

const ActionButton = styled.button.withConfig({
  shouldForwardProp: (prop) => prop !== 'variant'
})<{ variant?: 'primary' | 'secondary' }>`
  padding: ${props => props.theme.spacing.sm} ${props => props.theme.spacing.md};
  background: ${props => 
    props.variant === 'primary' 
      ? props.theme.colors.primary 
      : props.theme.colors.surface
  };
  color: ${props => props.theme.colors.text};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: calc(${props => props.theme.borderRadius} / 2);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover:not(:disabled) {
    background: ${props => 
      props.variant === 'primary' 
        ? props.theme.colors.primaryHover 
        : props.theme.colors.surfaceHover
    };
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ProgressContainer = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'visible'
})<{ visible: boolean }>`
  margin-top: ${props => props.theme.spacing.md};
  opacity: ${props => props.visible ? 1 : 0};
  max-height: ${props => props.visible ? '60px' : '0'};
  overflow: hidden;
  transition: all 0.3s ease;
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background: ${props => props.theme.colors.border};
  border-radius: 4px;
  overflow: hidden;
`;

const ProgressFill = styled.div.withConfig({
  shouldForwardProp: (prop) => prop !== 'progress'
})<{ progress: number }>`
  height: 100%;
  width: ${props => props.progress}%;
  background: ${props => props.theme.colors.primary};
  transition: width 0.3s ease;
`;

const ProgressText = styled.div`
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.8rem;
  margin-top: ${props => props.theme.spacing.xs};
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

interface StepData {
  id: string;
  name: string;
  description: string;
}

interface PipelineStepProps {
  step: StepData;
  index: number;
  status: string;
  progress: number;
  result?: any;
  onExecute: () => void;
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
  onExecute,
  onInspect,
  onConfigure,
  disabled,
  config
}) => {
  const isRunning = status === 'running';
  const hasResult = result && (result.success !== false);

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
              disabled={isRunning}
              title="Configure step parameters"
            >
              ⚙️ Config
            </ActionButton>
          )}
          
          <ActionButton
            variant="primary"
            onClick={onExecute}
            disabled={disabled || isRunning}
          >
            {isRunning ? 'Running...' : '▶️ Run'}
          </ActionButton>
          
          {hasResult && (
            <ActionButton
              onClick={onInspect}
              disabled={isRunning}
            >
              📊 Inspect
            </ActionButton>
          )}
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

      <ProgressContainer visible={isRunning || status === 'completed'}>
        <ProgressBar>
          <ProgressFill progress={progress} />
        </ProgressBar>
        <ProgressText>
          {isRunning ? `Running... ${progress}%` : status === 'completed' ? 'Completed' : ''}
        </ProgressText>
      </ProgressContainer>
    </StepContainer>
  );
};

export default PipelineStep; 