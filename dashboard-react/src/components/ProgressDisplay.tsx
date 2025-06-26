import React from 'react';
import styled from 'styled-components';

const ProgressContainer = styled.div`
  background: ${props => props.theme.colors.surface};
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  padding: ${props => props.theme.spacing.lg};
  margin-bottom: ${props => props.theme.spacing.xxl};
  box-shadow: ${props => props.theme.shadow};
`;

const ProgressHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: ${props => props.theme.spacing.md};
`;

const ProgressTitle = styled.h3`
  color: ${props => props.theme.colors.text};
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
`;

const ProgressStatus = styled.span.withConfig({
  shouldForwardProp: (prop) => prop !== 'isRunning'
})<{ isRunning: boolean }>`
  color: ${props => 
    props.isRunning 
      ? props.theme.colors.warning 
      : props.theme.colors.textMuted
  };
  font-size: 0.9rem;
  font-weight: 500;
  margin-left: auto;
  
  &:before {
    content: '${props => props.isRunning ? '⏳' : '⚪'}';
    margin-right: ${props => props.theme.spacing.xs};
  }
`;

const StepsOverview = styled.div`
  display: flex;
  gap: ${props => props.theme.spacing.sm};
  margin-bottom: ${props => props.theme.spacing.md};
`;

const StepDot = styled.div.withConfig({
  shouldForwardProp: (prop) => !['isActive', 'isCompleted', 'isCurrent'].includes(prop)
})<{ 
  isActive: boolean; 
  isCompleted: boolean; 
  isCurrent: boolean;
}>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${props => {
    if (props.isCompleted) return props.theme.colors.success;
    if (props.isCurrent) return props.theme.colors.warning;
    if (props.isActive) return props.theme.colors.primary;
    return props.theme.colors.border;
  }};
  transition: all 0.3s ease;
  position: relative;

  &:after {
    content: '';
    position: absolute;
    top: 50%;
    left: calc(100% + 4px);
    width: ${props => props.theme.spacing.sm};
    height: 2px;
    background: ${props => props.theme.colors.border};
    transform: translateY(-50%);
  }

  &:last-child:after {
    display: none;
  }
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
  background: linear-gradient(90deg, 
    ${props => props.theme.colors.primary} 0%, 
    ${props => props.theme.colors.success} 100%
  );
  transition: width 0.5s ease;
`;

const ProgressText = styled.div`
  text-align: center;
  color: ${props => props.theme.colors.textMuted};
  font-size: 0.8rem;
  margin-top: ${props => props.theme.spacing.xs};
`;

interface StepData {
  id: string;
  name: string;
  description: string;
}

interface ProgressDisplayProps {
  currentStep: number;
  isRunning: boolean;
  steps: StepData[];
}

const ProgressDisplay: React.FC<ProgressDisplayProps> = ({
  currentStep,
  isRunning,
  steps
}) => {
  const progress = isRunning 
    ? ((currentStep + 1) / steps.length) * 100 
    : 0;

  return (
    <ProgressContainer>
      <ProgressHeader>
        <ProgressTitle>Pipeline Progress</ProgressTitle>
        <ProgressStatus isRunning={isRunning}>
          {isRunning 
            ? `Running Step ${currentStep + 1}/${steps.length}` 
            : 'Pipeline Ready'
          }
        </ProgressStatus>
      </ProgressHeader>

      <StepsOverview>
        {steps.map((step, index) => (
          <StepDot
            key={step.id}
            isActive={index <= currentStep}
            isCompleted={!isRunning && index < currentStep}
            isCurrent={isRunning && index === currentStep}
          />
        ))}
      </StepsOverview>

      <ProgressBar>
        <ProgressFill progress={progress} />
      </ProgressBar>
      
      <ProgressText>
        {isRunning 
          ? `${Math.round(progress)}% - ${steps[currentStep]?.name || 'Processing...'}`
          : 'Ready to start pipeline'
        }
      </ProgressText>
    </ProgressContainer>
  );
};

export default ProgressDisplay; 