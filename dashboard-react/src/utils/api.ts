import axios from 'axios';

export interface JobStatus {
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
  job_id?: string;
}

export const pollJobStatus = async (
  jobId: string,
  statusUrl: string,
  onProgress?: (progress: number, jobStatus?: JobStatus) => void
): Promise<any> => {
  console.log(`🔍 Polling status for job ${jobId}`);
  
  const maxPolls = 1440; // 2 hours max (every 5 seconds) - contact enrichment can take very long for comprehensive intelligence
  let pollCount = 0;
  
  while (pollCount < maxPolls) {
    try {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
      
      const response = await axios.get(statusUrl);
      const jobStatus: JobStatus = response.data;
      
      console.log(`📊 Job ${jobId} status:`, jobStatus.status, `(${jobStatus.progress}%)`, jobStatus.message);
      
      // Update progress if callback provided
      if (onProgress && typeof jobStatus.progress === 'number') {
        onProgress(jobStatus.progress, jobStatus);
      }
      
      if (jobStatus.status === 'completed') {
        console.log(`✅ Job ${jobId} completed successfully`);
        return jobStatus.result || { success: true, message: jobStatus.message };
      }
      
      if (jobStatus.status === 'stopped') {
        console.log(`⏹️ Job ${jobId} stopped by user`);
        return { 
          success: false, 
          stopped: true, 
          message: jobStatus.message || 'Process stopped by user',
          partial_result: jobStatus.partial_result,
          resume_info: jobStatus.resume_info
        };
      }
      
      if (jobStatus.status === 'failed') {
        console.error(`❌ Job ${jobId} failed:`, jobStatus.error);
        throw new Error(jobStatus.error || 'Job failed');
      }
      
      pollCount++;
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.error(`❌ Job ${jobId} not found`);
        throw new Error('Job not found');
      }
      
      console.error(`⚠️ Polling error for job ${jobId}:`, error.message);
      pollCount++;
      
      if (pollCount >= maxPolls) {
        throw new Error('Contact enrichment timeout - comprehensive intelligence gathering can take up to 2 hours. Job will continue running in background.');
      }
    }
  }
  
  throw new Error('Contact enrichment timeout - comprehensive intelligence gathering can take up to 2 hours. Job will continue running in background.');
};

export const cancelJob = async (jobId: string): Promise<boolean> => {
  try {
    console.log(`🛑 Cancelling job ${jobId}`);
    
    const response = await axios.post(`/api/cancel-job/${jobId}`);
    
    if (response.data.status === 'success') {
      console.log(`✅ Job ${jobId} cancellation requested successfully`);
      return true;
    } else {
      console.error(`❌ Failed to cancel job ${jobId}:`, response.data.message);
      return false;
    }
  } catch (error: any) {
    console.error(`❌ Error cancelling job ${jobId}:`, error.message);
    return false;
  }
};

export const getJobStatus = async (jobId: string): Promise<JobStatus | null> => {
  try {
    const response = await axios.get(`/api/job-status/${jobId}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      return null; // Job not found
    }
    console.error(`Error getting status for job ${jobId}:`, error.message);
    throw error;
  }
};

export const getUserJobs = async (): Promise<JobStatus[]> => {
  try {
    const response = await axios.get('/api/jobs');
    return response.data.jobs || [];
  } catch (error: any) {
    console.error('Error getting user jobs:', error.message);
    return [];
  }
}; 