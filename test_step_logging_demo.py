#!/usr/bin/env python3
"""
Step Logging System Demonstration
=================================
Comprehensive test and demonstration of the step logging capabilities
"""

import time
import random
from datetime import datetime
from utils.step_logger import step_logger, StepTracker
from utils.step_analyzer import step_analyzer, generate_quick_report
from utils.logging import structured_logger as logger

def demo_basic_step_logging():
    """Demonstrate basic step logging functionality"""
    print("\n" + "="*60)
    print("🔄 DEMO 1: Basic Step Logging")
    print("="*60)
    
    # Start a demo pipeline
    pipeline_id = step_logger.start_pipeline(
        user_id="demo_user@session-42.com",
        pipeline_type="basic_demo_pipeline"
    )
    
    print(f"✅ Started pipeline: {pipeline_id}")
    
    # Demo steps with context manager
    steps_data = [
        {
            'name': 'data_extraction',
            'input': {'sources': 3, 'records_to_process': 1000},
            'processing_time': 1.2,
            'output': {'records_extracted': 987, 'quality_score': 0.94}
        },
        {
            'name': 'data_transformation',
            'input': {'records': 987, 'transformations': ['normalize', 'enrich']},
            'processing_time': 0.8,
            'output': {'records_transformed': 976, 'transformation_success_rate': 0.98}
        },
        {
            'name': 'data_analysis',
            'input': {'records': 976, 'analysis_type': 'comprehensive'},
            'processing_time': 2.1,
            'output': {'insights_generated': 45, 'confidence_score': 0.87}
        }
    ]
    
    pipeline_results = {}
    
    for step_data in steps_data:
        print(f"\n🔄 Running step: {step_data['name']}")
        
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name=step_data['name'],
            input_data=step_data['input'],
            tags=['demo', 'basic']
        ) as tracker:
            
            # Simulate processing
            time.sleep(step_data['processing_time'])
            
            # Add custom metrics
            tracker.add_metric('processing_complexity', random.uniform(0.3, 1.0))
            tracker.add_metric('resource_usage_mb', random.randint(50, 200))
            
            # Set output
            tracker.set_output(step_data['output'])
            
            pipeline_results[step_data['name']] = step_data['output']
            
        print(f"✅ Completed: {step_data['name']} ({step_data['processing_time']:.1f}s)")
    
    # Complete pipeline
    step_logger.complete_pipeline(
        pipeline_id=pipeline_id,
        status="completed",
        global_metrics={
            'total_records_processed': 1000,
            'final_insights': 45,
            'overall_quality': 0.91
        }
    )
    
    print(f"\n🎉 Pipeline completed: {pipeline_id}")
    return pipeline_id

def demo_error_handling():
    """Demonstrate error handling and failure logging"""
    print("\n" + "="*60)
    print("❌ DEMO 2: Error Handling & Failure Logging")
    print("="*60)
    
    # Start a pipeline that will have failures
    pipeline_id = step_logger.start_pipeline(
        user_id="demo_user@session-42.com",
        pipeline_type="error_demo_pipeline"
    )
    
    print(f"✅ Started error demo pipeline: {pipeline_id}")
    
    # Step 1: Success
    print("\n🔄 Step 1: Successful step")
    with StepTracker(
        pipeline_id=pipeline_id,
        step_name="successful_step",
        input_data={'data': 'sample'},
        tags=['demo', 'success']
    ) as tracker:
        time.sleep(0.5)
        tracker.set_output({'result': 'success'})
    
    print("✅ Step 1 completed successfully")
    
    # Step 2: Controlled failure
    print("\n💥 Step 2: Simulated failure")
    try:
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name="failing_step",
            input_data={'data': 'will_fail'},
            tags=['demo', 'failure']
        ) as tracker:
            time.sleep(0.3)
            # Simulate a failure
            raise ValueError("Simulated processing error for demo")
    except ValueError as e:
        print(f"❌ Step failed as expected: {str(e)}")
    
    # Step 3: Recovery step
    print("\n🔄 Step 3: Recovery step")
    with StepTracker(
        pipeline_id=pipeline_id,
        step_name="recovery_step",
        input_data={'previous_error': True},
        tags=['demo', 'recovery']
    ) as tracker:
        time.sleep(0.7)
        tracker.set_output({'recovered': True, 'fallback_used': True})
    
    print("✅ Step 3 completed (recovery successful)")
    
    # Complete pipeline with mixed results
    step_logger.complete_pipeline(
        pipeline_id=pipeline_id,
        status="completed_with_errors",
        global_metrics={
            'total_steps': 3,
            'successful_steps': 2,
            'failed_steps': 1,
            'recovery_successful': True
        }
    )
    
    print(f"\n🎯 Error demo pipeline completed: {pipeline_id}")
    return pipeline_id

def demo_performance_tracking():
    """Demonstrate performance tracking and metrics"""
    print("\n" + "="*60)
    print("📊 DEMO 3: Performance Tracking & Metrics")
    print("="*60)
    
    # Run multiple pipelines to generate performance data
    pipeline_ids = []
    
    for i in range(5):
        pipeline_id = step_logger.start_pipeline(
            user_id="demo_user@session-42.com",
            pipeline_type="performance_demo_pipeline"
        )
        pipeline_ids.append(pipeline_id)
        
        print(f"\n🔄 Performance test {i+1}/5 (Pipeline: {pipeline_id[:8]}...)")
        
        # Variable performance characteristics
        performance_steps = [
            {
                'name': 'fast_step',
                'base_time': 0.2,
                'variance': 0.1,
                'complexity': random.uniform(0.1, 0.3)
            },
            {
                'name': 'medium_step', 
                'base_time': 1.0,
                'variance': 0.3,
                'complexity': random.uniform(0.4, 0.7)
            },
            {
                'name': 'slow_step',
                'base_time': 2.5,
                'variance': 0.5,
                'complexity': random.uniform(0.7, 1.0)
            }
        ]
        
        for step_data in performance_steps:
            actual_time = step_data['base_time'] + random.uniform(-step_data['variance'], step_data['variance'])
            
            with StepTracker(
                pipeline_id=pipeline_id,
                step_name=step_data['name'],
                input_data={'iteration': i, 'expected_time': step_data['base_time']},
                tags=['demo', 'performance', f'iteration_{i}']
            ) as tracker:
                
                # Simulate processing with variable time
                time.sleep(actual_time)
                
                # Add performance metrics
                tracker.add_metric('processing_complexity', step_data['complexity'])
                tracker.add_metric('memory_usage_mb', random.randint(10, 100))
                tracker.add_metric('cpu_usage_percent', random.randint(20, 80))
                tracker.add_metric('expected_duration_s', step_data['base_time'])
                
                tracker.set_output({
                    'actual_duration': actual_time,
                    'performance_ratio': actual_time / step_data['base_time']
                })
        
        # Complete pipeline
        step_logger.complete_pipeline(
            pipeline_id=pipeline_id,
            status="completed",
            global_metrics={'iteration': i, 'performance_test': True}
        )
        
        print(f"✅ Performance test {i+1} completed")
    
    print(f"\n🎯 Performance tracking demo completed ({len(pipeline_ids)} pipelines)")
    return pipeline_ids

def demo_data_sampling():
    """Demonstrate data sampling capabilities"""
    print("\n" + "="*60)
    print("🔬 DEMO 4: Data Sampling & Analysis")
    print("="*60)
    
    pipeline_id = step_logger.start_pipeline(
        user_id="demo_user@session-42.com",
        pipeline_type="sampling_demo_pipeline"
    )
    
    print(f"✅ Started sampling demo pipeline: {pipeline_id}")
    
    # Generate large datasets to test sampling
    large_datasets = [
        {
            'name': 'process_large_list',
            'input': list(range(5000)),  # Large list
            'output': {'processed_items': 4987, 'success_rate': 0.997}
        },
        {
            'name': 'process_large_dict',
            'input': {f'key_{i}': f'value_{i}' for i in range(2000)},  # Large dict
            'output': {'dict_processed': True, 'unique_keys': 2000}
        },
        {
            'name': 'process_text_content',
            'input': 'This is a very long text that represents email content or document text that would be processed by the intelligence system. ' * 100,
            'output': {'text_length': 12000, 'analysis_complete': True}
        }
    ]
    
    for dataset in large_datasets:
        print(f"\n🔄 Processing: {dataset['name']}")
        
        with StepTracker(
            pipeline_id=pipeline_id,
            step_name=dataset['name'],
            input_data=dataset['input'],
            tags=['demo', 'sampling', 'large_data']
        ) as tracker:
            
            # Simulate processing time based on data size
            processing_time = 0.5 + len(str(dataset['input'])) / 10000
            time.sleep(processing_time)
            
            tracker.add_metric('input_data_size', len(str(dataset['input'])))
            tracker.add_metric('sampling_applied', True)
            
            tracker.set_output(dataset['output'])
        
        print(f"✅ Completed: {dataset['name']}")
    
    # Complete pipeline
    step_logger.complete_pipeline(
        pipeline_id=pipeline_id,
        status="completed",
        global_metrics={'data_sampling_demo': True, 'large_datasets_processed': len(large_datasets)}
    )
    
    print(f"\n🎯 Data sampling demo completed: {pipeline_id}")
    return pipeline_id

def show_analysis_reports():
    """Display comprehensive analysis reports"""
    print("\n" + "="*60)
    print("📈 ANALYSIS REPORTS")
    print("="*60)
    
    # Show current system status
    print("\n🔄 Current System Status:")
    status = step_logger.get_pipeline_status()
    print(f"  Active Pipelines: {status['active_pipelines']}")
    print(f"  Active Steps: {status['active_steps']}")
    print(f"  Recent Completions: {status['recent_completions']}")
    
    # Show quick performance report
    print("\n📊 Quick Performance Report:")
    quick_report = generate_quick_report(days_back=1)
    print(quick_report)
    
    # Show step analysis for specific steps
    print("\n⚡ Step Performance Analysis:")
    for step_name in ['fast_step', 'medium_step', 'slow_step']:
        analysis = step_logger.get_step_analysis(step_name, hours_back=1)
        if not analysis.get('no_data'):
            print(f"\n  {step_name}:")
            print(f"    Executions: {analysis['execution_count']}")
            print(f"    Avg Duration: {analysis['avg_duration_ms']:.1f}ms")
            print(f"    Min/Max: {analysis['min_duration_ms']:.1f}ms / {analysis['max_duration_ms']:.1f}ms")
    
    # Show bottleneck analysis
    print("\n🐌 Bottleneck Analysis:")
    bottlenecks = step_analyzer.get_bottleneck_analysis(days_back=1)
    recommendations = bottlenecks.get('recommendations', [])
    if recommendations:
        for rec in recommendations[:3]:
            print(f"  • {rec}")
    else:
        print("  ✅ No critical bottlenecks detected")
    
    # Show data flow analysis
    print("\n📊 Data Flow Summary:")
    data_flow = step_analyzer.get_data_flow_analysis(days_back=1)
    system_metrics = data_flow.get('system_wide_metrics', {})
    if system_metrics:
        print(f"  Total Data Processed: {system_metrics.get('total_data_processed', 0):,} bytes")
        print(f"  Total Data Produced: {system_metrics.get('total_data_produced', 0):,} bytes")

def run_comprehensive_demo():
    """Run all demo functions"""
    print("🚀 STRATEGIC INTELLIGENCE STEP LOGGING SYSTEM DEMO")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Sampling Rate: {step_logger.sampling_rate*100:.1f}%")
    print(f"Max Sample Size: {step_logger.max_sample_size:,}")
    
    # Run all demos
    demo_basic_step_logging()
    demo_error_handling()
    demo_performance_tracking()
    demo_data_sampling()
    
    # Show comprehensive analysis
    show_analysis_reports()
    
    print("\n" + "="*70)
    print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("✅ Step-by-step execution tracking")
    print("✅ Performance monitoring and metrics")
    print("✅ Error handling and failure logging")
    print("✅ Data sampling for efficiency")
    print("✅ Comprehensive analysis and reporting")
    print("✅ Pipeline management and status tracking")
    print("\nAPI Endpoints Available:")
    print("📊 GET /api/logging/status - System status")
    print("📈 GET /api/logging/performance-report - Detailed performance analysis")
    print("⚡ GET /api/logging/bottlenecks - Bottleneck identification")
    print("🔄 GET /api/logging/recent-completions - Recent step completions")
    print("🧪 POST /api/logging/start-demo-pipeline - Generate sample data")
    print("🎯 POST /api/intelligence-logged/full-pipeline - Full logged pipeline")

if __name__ == "__main__":
    try:
        run_comprehensive_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc() 