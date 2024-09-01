import time

from worker.jobs.poppers import MultiModalPopper
from worker.jobs.multimodal import MultiModalHordeJob
from worker.workers.framework import WorkerFramework


class MultiModalWorker(WorkerFramework):
    def __init__(self, this_bridge_data):
        super().__init__(None, this_bridge_data)
        self.PopperClass = MultiModalPopper
        self.JobClass = MultiModalHordeJob

    def can_process_jobs(self):
        lmdeploy_avail = self.bridge_data.lmdeploy_available
        if not lmdeploy_avail:
            # We do this to allow the worker to try and reload the config every 5 seconds until the LMDeploy server is up
            self.last_config_reload = time.time() - 55
        return lmdeploy_avail

    def add_job_to_queue(self):
        super().add_job_to_queue()

    def pop_job(self):
        return super().pop_job()

    def get_running_models(self):
        running_job_models = [job.current_model for job_thread, start_time, job in self.running_jobs]
        queued_jobs_models = [job.current_model for job in self.waiting_jobs]
        return list(set(running_job_models + queued_jobs_models))

    def get_supported_tasks(self):
        return self.bridge_data.supported_tasks
