import axios from 'axios';

export interface JobStatus {
  status: 'started' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
}

export const pollJobStatus = async (
  jobId: string,
  statusUrl: string,
  onProgress?: (progress: number) => void
): Promise<any> => {
  console.log(`🔍 Polling status for job ${jobId}`);
  
  const maxPolls = 1440; // 2 hours max (every 5 seconds) - contact enrichment can take very long for comprehensive intelligence
  let pollCount = 0;
  
  while (pollCount < maxPolls) {
    try {
      await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
      
      const response = await axios.get(statusUrl);
      const jobStatus: JobStatus = response.data;
      
      console.log(`📊 Job ${jobId} status:`, jobStatus.status, `(${jobStatus.progress}%)`);
      
      // Update progress if callback provided
      if (onProgress && typeof jobStatus.progress === 'number') {
        onProgress(jobStatus.progress);
      }
      
      if (jobStatus.status === 'completed') {
        console.log(`✅ Job ${jobId} completed successfully`);
        return jobStatus.result || { success: true, message: jobStatus.message };
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