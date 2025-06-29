import React, { useState } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const SanityTestContainer = styled.div`
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin: 20px 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-left: 4px solid #6366f1;
`;

const SanityTestHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
`;

const SanityTestTitle = styled.h3`
  margin: 0;
  color: #1f2937;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const SanityTestButton = styled.button<{ running?: boolean; disabled?: boolean }>`
  background: ${props => props.running ? '#f59e0b' : props.disabled ? '#9ca3af' : '#6366f1'};
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 6px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: ${props => props.running ? '#d97706' : '#4f46e5'};
  }
`;

const ProgressContainer = styled.div`
  margin: 20px 0;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
`;

const ProgressHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 12px;
`;

const ProgressTitle = styled.div`
  font-weight: 600;
  color: #374151;
`;

const ProgressStatus = styled.div<{ status?: string }>`
  font-size: 0.9rem;
  color: ${props => {
    switch(props.status) {
      case 'excellent': return '#059669';
      case 'good': return '#0891b2';
      case 'fair': return '#d97706';
      case 'poor': return '#dc2626';
      default: return '#6b7280';
    }
  }};
  font-weight: 500;
`;

const StepList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const StepItem = styled.div<{ completed?: boolean; running?: boolean }>`
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: ${props => props.completed ? '#f0f9ff' : props.running ? '#fef3c7' : 'white'};
  border: 1px solid ${props => props.completed ? '#0ea5e9' : props.running ? '#f59e0b' : '#e5e7eb'};
  border-radius: 4px;
  transition: all 0.2s;
`;

const StepIcon = styled.div`
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  margin-right: 12px;
  flex-shrink: 0;
`;

const StepContent = styled.div`
  flex: 1;
`;

const StepName = styled.div`
  font-weight: 500;
  color: #374151;
  font-size: 0.9rem;
`;

const StepDescription = styled.div`
  color: #6b7280;
  font-size: 0.8rem;
  margin-top: 2px;
`;

const StepDuration = styled.div`
  color: #6b7280;
  font-size: 0.8rem;
  margin-left: auto;
  font-family: monospace;
`;

const ResultsContainer = styled.div`
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
`;

const ResultsTitle = styled.h4`
  margin: 0 0 12px 0;
  color: #374151;
  font-size: 1rem;
`;

const ResultItem = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 0.9rem;
`;

const ResultLabel = styled.span`
  color: #6b7280;
`;

const ResultValue = styled.span`
  color: #374151;
  font-weight: 500;
`;

const RecommendationBox = styled.div<{ status?: string }>`
  margin-top: 16px;
  padding: 12px;
  background: ${props => {
    switch(props.status) {
      case 'excellent': return '#f0fdf4';
      case 'good': return '#f0f9ff';
      case 'fair': return '#fffbeb';
      case 'poor': return '#fef2f2';
      default: return '#f8fafc';
    }
  }};
  border: 1px solid ${props => {
    switch(props.status) {
      case 'excellent': return '#bbf7d0';
      case 'good': return '#bae6fd';
      case 'fair': return '#fed7aa';
      case 'poor': return '#fecaca';
      default: return '#e2e8f0';
    }
  }};
  border-radius: 6px;
  font-size: 0.9rem;
  color: #374151;
`;

interface SanityTestPanelProps {
  isAuthenticated: boolean;
  disabled?: boolean;
}

interface SanityTestStep {
  step: number;
  name: string;
  description: string;
  status: string;
  duration: string;
  result: string;
  completed: boolean;
}

interface SanityTestResults {
  success: boolean;
  summary: string;
  recommendation: string;
  health_status: string;
  step_logs: SanityTestStep[];
  total_duration: number;
  performance_metrics: Record<string, number>;
  errors: string[];
}

const SanityTestPanel: React.FC<SanityTestPanelProps> = ({ isAuthenticated, disabled }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [results, setResults] = useState<SanityTestResults | null>(null);

  const runSanityTest = async () => {
    if (!isAuthenticated) {
      alert('Please authenticate first');
      return;
    }

    setIsRunning(true);
    setCurrentStep(0);
    setResults(null);
    
    try {
      console.log('🧪 Starting Sanity Fast Test...');
      
      // Simulate step progress for better UX
      const progressSteps = [
        'Fetching sample contacts...',
        'Getting related emails...',
        'Running contact enrichment...',
        'Building knowledge tree...',
        'Generating strategic insights...'
      ];

      const progressInterval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev < progressSteps.length - 1) {
            return prev + 1;
          }
          return prev;
        });
      }, 4000); // Update every 4 seconds

      const response = await axios.post('/api/system/sanity-fast-test');
      
      clearInterval(progressInterval);
      setCurrentStep(5); // Complete

      if (response.data) {
        setResults(response.data);
        console.log('🧪 Sanity Test Results:', response.data);
        
        // Show success/failure notification
        if (response.data.success !== false) {
          console.log(`🎉 Sanity Test: ${response.data.summary}`);
        } else {
          console.warn(`⚠️ Sanity Test Issues: ${response.data.summary}`);
        }
      }
    } catch (error) {
      console.error('❌ Sanity Test failed:', error);
      setResults({
        success: false,
        summary: 'Test failed with network error',
        recommendation: 'Check network connection and try again',
        health_status: 'poor',
        step_logs: [],
        total_duration: 0,
        performance_metrics: {},
        errors: ['Network error during test execution']
      });
    } finally {
      setIsRunning(false);
      setCurrentStep(0);
    }
  };

  const getStepStatus = (stepIndex: number) => {
    if (!isRunning) return 'ready';
    if (stepIndex < currentStep) return 'completed';
    if (stepIndex === currentStep) return 'running';
    return 'pending';
  };

  const stepTemplates = [
    { name: 'Get Sample Contacts', description: 'Fetch 2 contacts from database with highest frequency' },
    { name: 'Get Related Emails', description: 'Fetch emails from/to the sample contacts' },
    { name: 'Contact Enrichment', description: 'Run enterprise-grade contact augmentation with Claude 4 Opus' },
    { name: 'Knowledge Tree Building', description: 'Build comprehensive knowledge tree from email content' },
    { name: 'Strategic Intelligence', description: 'Generate strategic insights and business opportunities' }
  ];

  return (
    <SanityTestContainer>
      <SanityTestHeader>
        <SanityTestTitle>
          🧪 Sanity Fast Test
          <span style={{ fontSize: '0.8rem', color: '#6b7280', fontWeight: 'normal' }}>
            End-to-end pipeline validation
          </span>
        </SanityTestTitle>
        <SanityTestButton
          onClick={runSanityTest}
          disabled={!isAuthenticated || disabled || isRunning}
          running={isRunning}
        >
          {isRunning ? (
            <>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                border: '2px solid #ffffff40',
                borderTop: '2px solid #ffffff',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              Testing...
            </>
          ) : (
            '🧪 Run Test'
          )}
        </SanityTestButton>
      </SanityTestHeader>

      <ProgressContainer>
        <ProgressHeader>
          <ProgressTitle>Test Progress</ProgressTitle>
          {results && (
            <ProgressStatus status={results.health_status}>
              {results.health_status === 'excellent' && '🎉 Excellent'}
              {results.health_status === 'good' && '✅ Good'}
              {results.health_status === 'fair' && '⚠️ Fair'}
              {results.health_status === 'poor' && '❌ Poor'}
            </ProgressStatus>
          )}
        </ProgressHeader>

        <StepList>
          {(results?.step_logs || stepTemplates).map((step, index) => {
            const isResultStep = results && results.step_logs;
            const stepStatus = isResultStep ? (step as SanityTestStep).status : getStepStatus(index);
            const isCompleted = stepStatus.includes('✅');
            const isRunning = !results && getStepStatus(index) === 'running';
            
            return (
              <StepItem key={index} completed={isCompleted} running={isRunning}>
                <StepIcon
                  style={{
                    background: isCompleted ? '#059669' : isRunning ? '#f59e0b' : '#e5e7eb',
                    color: isCompleted || isRunning ? 'white' : '#6b7280'
                  }}
                >
                  {isCompleted ? '✓' : isRunning ? '●' : index + 1}
                </StepIcon>
                <StepContent>
                  <StepName>
                    {isResultStep ? (step as SanityTestStep).name : (step as any).name}
                  </StepName>
                  <StepDescription>
                    {isResultStep ? (step as SanityTestStep).description : (step as any).description}
                  </StepDescription>
                  {isResultStep && (step as SanityTestStep).result && (
                    <div style={{ fontSize: '0.8rem', color: '#059669', marginTop: '4px' }}>
                      {(step as SanityTestStep).result}
                    </div>
                  )}
                </StepContent>
                {isResultStep && (
                  <StepDuration>{(step as SanityTestStep).duration}</StepDuration>
                )}
              </StepItem>
            );
          })}
        </StepList>
      </ProgressContainer>

      {results && (
        <ResultsContainer>
          <ResultsTitle>Test Results</ResultsTitle>
          <ResultItem>
            <ResultLabel>Total Duration:</ResultLabel>
            <ResultValue>{results.total_duration?.toFixed(1)}s</ResultValue>
          </ResultItem>
          <ResultItem>
            <ResultLabel>Steps Completed:</ResultLabel>
            <ResultValue>{results.step_logs?.filter(s => s.completed).length || 0}/5</ResultValue>
          </ResultItem>
          <ResultItem>
            <ResultLabel>Success Rate:</ResultLabel>
            <ResultValue>{((results.step_logs?.filter(s => s.completed).length || 0) / 5 * 100).toFixed(0)}%</ResultValue>
          </ResultItem>
          {results.errors && results.errors.length > 0 && (
            <ResultItem>
              <ResultLabel>Errors:</ResultLabel>
              <ResultValue style={{ color: '#dc2626' }}>{results.errors.length}</ResultValue>
            </ResultItem>
          )}
          
          <RecommendationBox status={results.health_status}>
            <strong>Recommendation:</strong> {results.recommendation}
          </RecommendationBox>
        </ResultsContainer>
      )}

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </SanityTestContainer>
  );
};

export default SanityTestPanel; 