"""
Step Log Analyzer
================
Analysis tool for step-by-step system logs with visualization and reporting capabilities.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import statistics

from utils.step_logger import step_logger

class StepAnalyzer:
    """
    Comprehensive analyzer for step execution logs
    """
    
    def __init__(self, logs_dir: Path = None):
        self.logs_dir = logs_dir or Path(__file__).parent.parent / "logs" / "steps"
        
    def load_logs(self, days_back: int = 7) -> Tuple[List[Dict], List[Dict]]:
        """Load step and pipeline logs from the last N days"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        steps = []
        pipelines = []
        
        for log_file in self.logs_dir.glob("*.jsonl"):
            try:
                # Extract date from filename
                file_date_str = log_file.stem.split('_')[1]
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    continue
                
                # Load logs
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if 'step_id' in data:
                                steps.append(data)
                            elif 'pipeline_id' in data:
                                pipelines.append(data)
                        except json.JSONDecodeError:
                            continue
                            
            except (ValueError, IndexError):
                continue
        
        return steps, pipelines
    
    def generate_performance_report(self, days_back: int = 7) -> Dict:
        """Generate comprehensive performance report"""
        
        steps, pipelines = self.load_logs(days_back)
        
        # Step-level analysis
        step_stats = defaultdict(list)
        step_errors = defaultdict(list)
        
        for step in steps:
            step_name = step.get('step_name', 'unknown')
            
            if step.get('status') == 'completed':
                step_stats[step_name].append({
                    'duration_ms': step.get('duration_ms', 0),
                    'input_size': step.get('input_size', 0),
                    'output_size': step.get('output_size', 0),
                    'timestamp': step.get('end_time')
                })
            elif step.get('status') == 'failed':
                step_errors[step_name].append({
                    'error': step.get('error_message'),
                    'timestamp': step.get('end_time'),
                    'duration_ms': step.get('duration_ms', 0)
                })
        
        # Calculate statistics for each step
        step_analysis = {}
        for step_name, stats in step_stats.items():
            if not stats:
                continue
                
            durations = [s['duration_ms'] for s in stats]
            input_sizes = [s['input_size'] for s in stats]
            output_sizes = [s['output_size'] for s in stats]
            
            step_analysis[step_name] = {
                'execution_count': len(stats),
                'success_rate': len(stats) / (len(stats) + len(step_errors.get(step_name, []))),
                'duration': {
                    'avg_ms': statistics.mean(durations) if durations else 0,
                    'median_ms': statistics.median(durations) if durations else 0,
                    'min_ms': min(durations) if durations else 0,
                    'max_ms': max(durations) if durations else 0,
                    'stddev_ms': statistics.stdev(durations) if len(durations) > 1 else 0
                },
                'data_size': {
                    'avg_input': statistics.mean(input_sizes) if input_sizes else 0,
                    'avg_output': statistics.mean(output_sizes) if output_sizes else 0,
                    'total_input': sum(input_sizes),
                    'total_output': sum(output_sizes)
                },
                'error_count': len(step_errors.get(step_name, [])),
                'common_errors': Counter([e['error'] for e in step_errors.get(step_name, [])]).most_common(3)
            }
        
        # Pipeline-level analysis
        pipeline_stats = defaultdict(list)
        for pipeline in pipelines:
            pipeline_type = pipeline.get('pipeline_type', 'unknown')
            pipeline_stats[pipeline_type].append({
                'duration_ms': pipeline.get('total_duration_ms', 0),
                'step_count': pipeline.get('global_metrics', {}).get('total_steps', 0),
                'success_rate': pipeline.get('global_metrics', {}).get('success_rate', 0),
                'timestamp': pipeline.get('end_time')
            })
        
        pipeline_analysis = {}
        for pipeline_type, stats in pipeline_stats.items():
            if not stats:
                continue
                
            durations = [s['duration_ms'] for s in stats]
            step_counts = [s['step_count'] for s in stats]
            success_rates = [s['success_rate'] for s in stats]
            
            pipeline_analysis[pipeline_type] = {
                'execution_count': len(stats),
                'avg_duration_ms': statistics.mean(durations) if durations else 0,
                'avg_step_count': statistics.mean(step_counts) if step_counts else 0,
                'avg_success_rate': statistics.mean(success_rates) if success_rates else 0,
                'total_executions': len(stats)
            }
        
        return {
            'analysis_period': f"{days_back} days",
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_steps_executed': len(steps),
                'total_pipelines_executed': len(pipelines),
                'unique_step_types': len(step_analysis),
                'unique_pipeline_types': len(pipeline_analysis),
                'overall_success_rate': len([s for s in steps if s.get('status') == 'completed']) / len(steps) if steps else 0
            },
            'step_analysis': step_analysis,
            'pipeline_analysis': pipeline_analysis
        }
    
    def get_bottleneck_analysis(self, days_back: int = 7) -> Dict:
        """Identify performance bottlenecks"""
        
        steps, pipelines = self.load_logs(days_back)
        
        # Analyze step durations
        step_durations = defaultdict(list)
        for step in steps:
            if step.get('status') == 'completed' and step.get('duration_ms'):
                step_durations[step.get('step_name', 'unknown')].append(step['duration_ms'])
        
        # Find slowest steps
        slowest_steps = []
        for step_name, durations in step_durations.items():
            if durations:
                avg_duration = statistics.mean(durations)
                slowest_steps.append({
                    'step_name': step_name,
                    'avg_duration_ms': avg_duration,
                    'execution_count': len(durations),
                    'max_duration_ms': max(durations),
                    'slowness_score': avg_duration * len(durations)  # Impact score
                })
        
        slowest_steps.sort(key=lambda x: x['slowness_score'], reverse=True)
        
        # Analyze failure patterns
        failure_patterns = defaultdict(list)
        for step in steps:
            if step.get('status') == 'failed':
                step_name = step.get('step_name', 'unknown')
                failure_patterns[step_name].append({
                    'error': step.get('error_message', 'Unknown error'),
                    'timestamp': step.get('end_time'),
                    'duration_before_failure': step.get('duration_ms', 0)
                })
        
        failure_analysis = {}
        for step_name, failures in failure_patterns.items():
            error_types = Counter([f['error'] for f in failures])
            failure_analysis[step_name] = {
                'total_failures': len(failures),
                'common_errors': error_types.most_common(3),
                'avg_duration_before_failure': statistics.mean([f['duration_before_failure'] for f in failures]) if failures else 0
            }
        
        return {
            'bottleneck_analysis': {
                'slowest_steps': slowest_steps[:10],  # Top 10 slowest
                'high_impact_steps': [s for s in slowest_steps if s['slowness_score'] > 10000][:5],
                'failure_prone_steps': dict(sorted(failure_analysis.items(), 
                                                 key=lambda x: x[1]['total_failures'], 
                                                 reverse=True)[:5])
            },
            'recommendations': self._generate_recommendations(slowest_steps, failure_analysis)
        }
    
    def get_data_flow_analysis(self, days_back: int = 7) -> Dict:
        """Analyze data flow patterns through the system"""
        
        steps, pipelines = self.load_logs(days_back)
        
        # Analyze data sizes and transformations
        data_flow = defaultdict(lambda: {'input_sizes': [], 'output_sizes': [], 'transformations': []})
        
        for step in steps:
            if step.get('status') == 'completed':
                step_name = step.get('step_name', 'unknown')
                input_size = step.get('input_size', 0)
                output_size = step.get('output_size', 0)
                
                data_flow[step_name]['input_sizes'].append(input_size)
                data_flow[step_name]['output_sizes'].append(output_size)
                
                if input_size > 0:
                    transformation_ratio = output_size / input_size
                    data_flow[step_name]['transformations'].append(transformation_ratio)
        
        # Calculate data flow metrics
        flow_analysis = {}
        for step_name, flow_data in data_flow.items():
            input_sizes = flow_data['input_sizes']
            output_sizes = flow_data['output_sizes']
            transformations = flow_data['transformations']
            
            if input_sizes and output_sizes:
                flow_analysis[step_name] = {
                    'avg_input_size': statistics.mean(input_sizes),
                    'avg_output_size': statistics.mean(output_sizes),
                    'avg_transformation_ratio': statistics.mean(transformations) if transformations else 0,
                    'data_reduction_steps': len([t for t in transformations if t < 1]),
                    'data_expansion_steps': len([t for t in transformations if t > 1]),
                    'total_data_processed': sum(input_sizes)
                }
        
        return {
            'data_flow_analysis': flow_analysis,
            'system_wide_metrics': {
                'total_data_processed': sum(sum(flow['input_sizes']) for flow in data_flow.values()),
                'total_data_produced': sum(sum(flow['output_sizes']) for flow in data_flow.values()),
                'most_data_intensive_steps': sorted(
                    [(name, analysis['total_data_processed']) for name, analysis in flow_analysis.items()],
                    key=lambda x: x[1], reverse=True
                )[:5]
            }
        }
    
    def get_user_activity_analysis(self, days_back: int = 7) -> Dict:
        """Analyze user activity patterns"""
        
        steps, pipelines = self.load_logs(days_back)
        
        # User activity analysis
        user_activity = defaultdict(lambda: {
            'pipeline_executions': 0,
            'step_executions': 0,
            'total_duration_ms': 0,
            'pipeline_types': Counter(),
            'step_types': Counter(),
            'success_rate': []
        })
        
        for pipeline in pipelines:
            user_id = pipeline.get('user_id', 'unknown')
            user_activity[user_id]['pipeline_executions'] += 1
            user_activity[user_id]['total_duration_ms'] += pipeline.get('total_duration_ms', 0)
            user_activity[user_id]['pipeline_types'][pipeline.get('pipeline_type', 'unknown')] += 1
            
            success_rate = pipeline.get('global_metrics', {}).get('success_rate', 0)
            user_activity[user_id]['success_rate'].append(success_rate)
        
        for step in steps:
            user_id = step.get('user_id', 'unknown')
            user_activity[user_id]['step_executions'] += 1
            user_activity[user_id]['step_types'][step.get('step_name', 'unknown')] += 1
        
        # Calculate user metrics
        user_analysis = {}
        for user_id, activity in user_activity.items():
            success_rates = activity['success_rate']
            user_analysis[user_id] = {
                'pipeline_executions': activity['pipeline_executions'],
                'step_executions': activity['step_executions'],
                'total_duration_ms': activity['total_duration_ms'],
                'avg_success_rate': statistics.mean(success_rates) if success_rates else 0,
                'most_used_pipeline_types': activity['pipeline_types'].most_common(3),
                'most_used_step_types': activity['step_types'].most_common(5),
                'activity_score': activity['pipeline_executions'] * 10 + activity['step_executions']
            }
        
        return {
            'user_activity_analysis': user_analysis,
            'system_usage': {
                'active_users': len(user_analysis),
                'most_active_users': sorted(
                    [(user_id, analysis['activity_score']) for user_id, analysis in user_analysis.items()],
                    key=lambda x: x[1], reverse=True
                )[:5],
                'total_system_usage_ms': sum(analysis['total_duration_ms'] for analysis in user_analysis.values())
            }
        }
    
    def _generate_recommendations(self, slowest_steps: List[Dict], failure_analysis: Dict) -> List[str]:
        """Generate optimization recommendations"""
        
        recommendations = []
        
        # Performance recommendations
        if slowest_steps:
            slowest = slowest_steps[0]
            recommendations.append(
                f"🚀 Optimize '{slowest['step_name']}' step - avg duration: {slowest['avg_duration_ms']:.1f}ms, "
                f"executed {slowest['execution_count']} times"
            )
        
        high_impact = [s for s in slowest_steps if s['slowness_score'] > 50000]
        if high_impact:
            recommendations.append(
                f"⚡ High-impact optimization needed for: {', '.join([s['step_name'] for s in high_impact[:3]])}"
            )
        
        # Reliability recommendations
        high_failure_steps = sorted(failure_analysis.items(), key=lambda x: x[1]['total_failures'], reverse=True)[:3]
        for step_name, failure_data in high_failure_steps:
            if failure_data['total_failures'] > 5:
                recommendations.append(
                    f"🔧 Improve reliability of '{step_name}' - {failure_data['total_failures']} failures detected"
                )
        
        # General recommendations
        if len(slowest_steps) > 10:
            recommendations.append("📊 Consider adding more granular step tracking for better analysis")
        
        if not recommendations:
            recommendations.append("✅ System performance looks good! No critical issues detected.")
        
        return recommendations

# Global analyzer instance
step_analyzer = StepAnalyzer()

def generate_quick_report(days_back: int = 1) -> str:
    """Generate a quick text report for recent activity"""
    
    # Get current status from step logger
    status = step_logger.get_pipeline_status()
    
    # Get performance analysis
    performance = step_analyzer.generate_performance_report(days_back)
    
    report = f"""
📊 STRATEGIC INTELLIGENCE SYSTEM - PERFORMANCE REPORT
{'='*60}
Report Period: Last {days_back} day(s)
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

🔄 CURRENT STATUS:
- Active Pipelines: {status['active_pipelines']}
- Active Steps: {status['active_steps']}
- Recent Completions: {status['recent_completions']}

📈 EXECUTION SUMMARY:
- Total Steps Executed: {performance['summary']['total_steps_executed']}
- Total Pipelines Executed: {performance['summary']['total_pipelines_executed']}
- Overall Success Rate: {performance['summary']['overall_success_rate']:.1%}
- Unique Step Types: {performance['summary']['unique_step_types']}

⚡ TOP PERFORMING STEPS:
"""
    
    # Add top performing steps
    step_analysis = performance.get('step_analysis', {})
    if step_analysis:
        sorted_steps = sorted(step_analysis.items(), 
                            key=lambda x: x[1]['execution_count'], 
                            reverse=True)[:5]
        
        for step_name, stats in sorted_steps:
            report += f"  • {step_name}: {stats['execution_count']} executions, "
            report += f"{stats['duration']['avg_ms']:.1f}ms avg, "
            report += f"{stats['success_rate']:.1%} success rate\n"
    
    # Add recommendations
    bottlenecks = step_analyzer.get_bottleneck_analysis(days_back)
    recommendations = bottlenecks.get('recommendations', [])
    
    if recommendations:
        report += f"\n💡 RECOMMENDATIONS:\n"
        for rec in recommendations[:5]:
            report += f"  • {rec}\n"
    
    return report 