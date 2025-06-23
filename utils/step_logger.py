"""
Strategic Intelligence Step Logger
=================================
Efficient logging system for analyzing system operations step-by-step
with sampling, performance tracking, and analysis capabilities.
"""

import json
import time
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import hashlib

from utils.logging import structured_logger as base_logger

@dataclass
class StepMetrics:
    """Metrics for a single step execution"""
    step_id: str
    step_name: str
    user_id: str
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "running"  # running, completed, failed, skipped
    input_size: int = 0
    output_size: int = 0
    error_message: Optional[str] = None
    sample_data: Optional[Dict] = None
    performance_metrics: Optional[Dict] = None
    dependencies: List[str] = None
    tags: List[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        if self.start_time:
            result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        return result

@dataclass
class PipelineExecution:
    """Complete pipeline execution tracking"""
    pipeline_id: str
    user_id: str
    session_id: str
    pipeline_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    status: str = "running"
    steps: List[StepMetrics] = None
    global_metrics: Optional[Dict] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []

class StepLogger:
    """
    Efficient step-by-step logging system with sampling and analysis
    """
    
    def __init__(self, 
                 logs_dir: Union[str, Path] = None,
                 sampling_rate: float = 0.1,  # Sample 10% of data by default
                 max_sample_size: int = 1000,  # Max items in sample data
                 retention_days: int = 30):
        
        self.logs_dir = Path(logs_dir) if logs_dir else Path(__file__).parent.parent / "logs" / "steps"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.sampling_rate = sampling_rate
        self.max_sample_size = max_sample_size
        self.retention_days = retention_days
        
        # In-memory tracking
        self.active_pipelines: Dict[str, PipelineExecution] = {}
        self.active_steps: Dict[str, StepMetrics] = {}
        self.recent_completions: deque = deque(maxlen=100)  # Keep last 100 completions
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance tracking
        self.step_performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        
        base_logger.info("Step logger initialized", 
                        logs_dir=str(self.logs_dir),
                        sampling_rate=sampling_rate,
                        max_sample_size=max_sample_size)

    def start_pipeline(self, 
                      user_id: str, 
                      pipeline_type: str,
                      session_id: Optional[str] = None) -> str:
        """Start tracking a new pipeline execution"""
        
        pipeline_id = str(uuid.uuid4())
        session_id = session_id or f"session_{int(time.time())}"
        
        pipeline = PipelineExecution(
            pipeline_id=pipeline_id,
            user_id=user_id,
            session_id=session_id,
            pipeline_type=pipeline_type,
            start_time=datetime.utcnow()
        )
        
        with self._lock:
            self.active_pipelines[pipeline_id] = pipeline
        
        base_logger.info("Pipeline started", 
                        pipeline_id=pipeline_id,
                        user_id=user_id,
                        pipeline_type=pipeline_type)
        
        return pipeline_id

    def start_step(self, 
                   pipeline_id: str,
                   step_name: str,
                   input_data: Any = None,
                   dependencies: List[str] = None,
                   tags: List[str] = None) -> str:
        """Start tracking a step execution"""
        
        step_id = str(uuid.uuid4())
        
        # Get pipeline info
        pipeline = self.active_pipelines.get(pipeline_id)
        if not pipeline:
            base_logger.warning("Step started without active pipeline", 
                              step_id=step_id, pipeline_id=pipeline_id)
            user_id = "unknown"
            session_id = "unknown"
        else:
            user_id = pipeline.user_id
            session_id = pipeline.session_id
        
        # Sample input data
        sample_data = self._sample_data(input_data, f"input_{step_name}")
        input_size = self._calculate_size(input_data)
        
        step = StepMetrics(
            step_id=step_id,
            step_name=step_name,
            user_id=user_id,
            session_id=session_id,
            start_time=datetime.utcnow(),
            input_size=input_size,
            sample_data=sample_data,
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        with self._lock:
            self.active_steps[step_id] = step
            if pipeline:
                pipeline.steps.append(step)
        
        base_logger.info("Step started", 
                        step_id=step_id,
                        step_name=step_name,
                        pipeline_id=pipeline_id,
                        input_size=input_size)
        
        return step_id

    def complete_step(self, 
                     step_id: str,
                     output_data: Any = None,
                     performance_metrics: Dict = None,
                     status: str = "completed") -> bool:
        """Complete a step execution"""
        
        with self._lock:
            step = self.active_steps.get(step_id)
            if not step:
                base_logger.warning("Attempted to complete unknown step", step_id=step_id)
                return False
            
            # Update step
            step.end_time = datetime.utcnow()
            step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
            step.status = status
            step.output_size = self._calculate_size(output_data)
            step.performance_metrics = performance_metrics or {}
            
            # Sample output data
            if output_data is not None:
                output_sample = self._sample_data(output_data, f"output_{step.step_name}")
                if step.sample_data:
                    step.sample_data['output'] = output_sample
                else:
                    step.sample_data = {'output': output_sample}
            
            # Track performance history
            self.step_performance_history[step.step_name].append({
                'duration_ms': step.duration_ms,
                'input_size': step.input_size,
                'output_size': step.output_size,
                'timestamp': step.end_time.isoformat()
            })
            
            # Move to completed
            completed_step = self.active_steps.pop(step_id)
            self.recent_completions.append(completed_step)
            
            # Log completion
            self._log_step_completion(completed_step)
        
        base_logger.info("Step completed", 
                        step_id=step_id,
                        step_name=step.step_name,
                        duration_ms=step.duration_ms,
                        status=status)
        
        return True

    def fail_step(self, step_id: str, error_message: str, error_details: Dict = None):
        """Mark a step as failed"""
        
        with self._lock:
            step = self.active_steps.get(step_id)
            if not step:
                base_logger.warning("Attempted to fail unknown step", step_id=step_id)
                return False
            
            step.end_time = datetime.utcnow()
            step.duration_ms = (step.end_time - step.start_time).total_seconds() * 1000
            step.status = "failed"
            step.error_message = error_message
            
            if error_details:
                if step.sample_data:
                    step.sample_data['error_details'] = error_details
                else:
                    step.sample_data = {'error_details': error_details}
            
            # Move to completed
            failed_step = self.active_steps.pop(step_id)
            self.recent_completions.append(failed_step)
            
            # Log failure
            self._log_step_completion(failed_step)
        
        base_logger.error("Step failed", 
                         step_id=step_id,
                         step_name=step.step_name,
                         error=error_message)
        
        return True

    def complete_pipeline(self, pipeline_id: str, status: str = "completed", global_metrics: Dict = None) -> bool:
        """Complete a pipeline execution"""
        
        with self._lock:
            pipeline = self.active_pipelines.get(pipeline_id)
            if not pipeline:
                base_logger.warning("Attempted to complete unknown pipeline", pipeline_id=pipeline_id)
                return False
            
            pipeline.end_time = datetime.utcnow()
            pipeline.total_duration_ms = (pipeline.end_time - pipeline.start_time).total_seconds() * 1000
            pipeline.status = status
            pipeline.global_metrics = global_metrics or {}
            
            # Calculate pipeline-level metrics
            completed_steps = [s for s in pipeline.steps if s.status == "completed"]
            failed_steps = [s for s in pipeline.steps if s.status == "failed"]
            
            pipeline.global_metrics.update({
                'total_steps': len(pipeline.steps),
                'completed_steps': len(completed_steps),
                'failed_steps': len(failed_steps),
                'success_rate': len(completed_steps) / len(pipeline.steps) if pipeline.steps else 0,
                'total_input_size': sum(s.input_size for s in pipeline.steps),
                'total_output_size': sum(s.output_size for s in pipeline.steps if s.output_size),
                'average_step_duration_ms': sum(s.duration_ms for s in completed_steps) / len(completed_steps) if completed_steps else 0
            })
            
            # Remove from active and log
            completed_pipeline = self.active_pipelines.pop(pipeline_id)
            self._log_pipeline_completion(completed_pipeline)
        
        base_logger.info("Pipeline completed", 
                        pipeline_id=pipeline_id,
                        status=status,
                        total_duration_ms=pipeline.total_duration_ms,
                        total_steps=len(pipeline.steps))
        
        return True

    def get_step_analysis(self, step_name: str = None, hours_back: int = 24) -> Dict:
        """Get analysis of step performance"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        if step_name:
            # Analysis for specific step
            history = list(self.step_performance_history.get(step_name, []))
            recent_history = [h for h in history 
                            if datetime.fromisoformat(h['timestamp']) > cutoff_time]
            
            if not recent_history:
                return {'step_name': step_name, 'no_data': True}
            
            durations = [h['duration_ms'] for h in recent_history]
            input_sizes = [h['input_size'] for h in recent_history]
            
            return {
                'step_name': step_name,
                'execution_count': len(recent_history),
                'avg_duration_ms': sum(durations) / len(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'avg_input_size': sum(input_sizes) / len(input_sizes),
                'recent_executions': recent_history[-10:]  # Last 10 executions
            }
        else:
            # Analysis for all steps
            analysis = {}
            for step_name in self.step_performance_history.keys():
                analysis[step_name] = self.get_step_analysis(step_name, hours_back)
            return analysis

    def get_pipeline_status(self) -> Dict:
        """Get current pipeline status"""
        
        with self._lock:
            return {
                'active_pipelines': len(self.active_pipelines),
                'active_steps': len(self.active_steps),
                'recent_completions': len(self.recent_completions),
                'pipeline_details': [
                    {
                        'pipeline_id': p.pipeline_id,
                        'user_id': p.user_id,
                        'pipeline_type': p.pipeline_type,
                        'running_duration_ms': (datetime.utcnow() - p.start_time).total_seconds() * 1000,
                        'steps_count': len(p.steps),
                        'active_step_names': [s.step_name for s in p.steps if s.status == "running"]
                    }
                    for p in self.active_pipelines.values()
                ]
            }

    def _sample_data(self, data: Any, data_type: str) -> Optional[Dict]:
        """Sample data for logging based on sampling rate"""
        
        if random.random() > self.sampling_rate:
            return None
        
        if data is None:
            return None
        
        sample = {
            'data_type': data_type,
            'sampled_at': datetime.utcnow().isoformat(),
            'original_size': self._calculate_size(data)
        }
        
        try:
            if isinstance(data, (dict, list)):
                if isinstance(data, list) and len(data) > self.max_sample_size:
                    # Sample from list
                    sample_indices = random.sample(range(len(data)), min(self.max_sample_size, len(data)))
                    sample['data'] = [data[i] for i in sorted(sample_indices)]
                    sample['sampling_method'] = 'random_indices'
                    sample['sample_size'] = len(sample['data'])
                elif isinstance(data, dict):
                    # Limit dict size
                    if len(data) > self.max_sample_size:
                        sample_keys = random.sample(list(data.keys()), self.max_sample_size)
                        sample['data'] = {k: data[k] for k in sample_keys}
                        sample['sampling_method'] = 'random_keys'
                    else:
                        sample['data'] = data
                    sample['sample_size'] = len(sample['data'])
                else:
                    sample['data'] = data
                    sample['sample_size'] = len(data)
            elif isinstance(data, str):
                if len(data) > 1000:
                    sample['data'] = data[:500] + "..." + data[-500:]
                    sample['sampling_method'] = 'truncated'
                else:
                    sample['data'] = data
                sample['sample_size'] = len(data)
            else:
                sample['data'] = str(data)[:1000]  # Convert to string and limit
                sample['sample_size'] = len(str(data))
                
        except Exception as e:
            sample['data'] = f"<sampling_error: {str(e)}>"
            sample['sampling_method'] = 'error'
        
        return sample

    def _calculate_size(self, data: Any) -> int:
        """Calculate approximate size of data"""
        try:
            if data is None:
                return 0
            elif isinstance(data, (str, bytes)):
                return len(data)
            elif isinstance(data, (list, tuple, dict)):
                return len(str(data))  # Rough approximation
            else:
                return len(str(data))
        except:
            return 0

    def _log_step_completion(self, step: StepMetrics):
        """Log step completion to file"""
        log_file = self.logs_dir / f"steps_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(step.to_dict()) + '\n')
        except Exception as e:
            base_logger.error("Failed to log step completion", error=str(e))

    def _log_pipeline_completion(self, pipeline: PipelineExecution):
        """Log pipeline completion to file"""
        log_file = self.logs_dir / f"pipelines_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        
        try:
            pipeline_dict = {
                'pipeline_id': pipeline.pipeline_id,
                'user_id': pipeline.user_id,
                'session_id': pipeline.session_id,
                'pipeline_type': pipeline.pipeline_type,
                'start_time': pipeline.start_time.isoformat(),
                'end_time': pipeline.end_time.isoformat() if pipeline.end_time else None,
                'total_duration_ms': pipeline.total_duration_ms,
                'status': pipeline.status,
                'global_metrics': pipeline.global_metrics,
                'steps': [s.to_dict() for s in pipeline.steps]
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(pipeline_dict) + '\n')
        except Exception as e:
            base_logger.error("Failed to log pipeline completion", error=str(e))

    def cleanup_old_logs(self):
        """Clean up old log files"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        for log_file in self.logs_dir.glob("*.jsonl"):
            try:
                file_date_str = log_file.stem.split('_')[1]  # Extract date from filename
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    base_logger.info("Deleted old log file", file=str(log_file))
            except Exception as e:
                base_logger.warning("Failed to process log file for cleanup", 
                                  file=str(log_file), error=str(e))

# Global step logger instance
step_logger = StepLogger()

# Context manager for easy step tracking
class StepTracker:
    """Context manager for automatic step tracking"""
    
    def __init__(self, 
                 pipeline_id: str, 
                 step_name: str,
                 input_data: Any = None,
                 dependencies: List[str] = None,
                 tags: List[str] = None):
        self.pipeline_id = pipeline_id
        self.step_name = step_name
        self.input_data = input_data
        self.dependencies = dependencies
        self.tags = tags
        self.step_id = None
        self.output_data = None
        self.performance_metrics = {}
        
    def __enter__(self):
        self.step_id = step_logger.start_step(
            self.pipeline_id,
            self.step_name,
            self.input_data,
            self.dependencies,
            self.tags
        )
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.performance_metrics['duration_ms'] = duration_ms
        
        if exc_type is not None:
            # Step failed
            step_logger.fail_step(
                self.step_id,
                f"{exc_type.__name__}: {str(exc_val)}",
                {'traceback': str(exc_tb)}
            )
        else:
            # Step completed successfully
            step_logger.complete_step(
                self.step_id,
                self.output_data,
                self.performance_metrics
            )
    
    def set_output(self, output_data: Any):
        """Set output data for the step"""
        self.output_data = output_data
    
    def add_metric(self, key: str, value: Any):
        """Add a performance metric"""
        self.performance_metrics[key] = value 