from worker.jobs.framework import HordeJobFramework
from worker.logger import logger
from worker.stats import bridge_stats

class MultiModalHordeJob(HordeJobFramework):
    def __init__(self, mm, bd, pop):
        super().__init__(mm, bd, pop)
        self.current_model = self.bridge_data.model
        self.current_id = self.pop["id"]
        self.current_payload = self.pop["payload"]
        self.current_payload["quiet"] = True
        self.max_new_tokens = self.current_payload.get("max_new_tokens", self.bridge_data.max_new_tokens)
        self.task = self.current_payload.get("task", "chat")

    @logger.catch(reraise=True)
    def start_job(self):
        logger.debug(f"Starting multi-modal job for model: {self.current_model}")
        super().start_job()
        if self.status == JobStatus.FAULTED:
            self.start_submit_thread()
            return

        try:
            from lmdeploy import pipeline, GenerationConfig

            pipe = pipeline(self.current_model)
            
            gen_config = GenerationConfig(
                top_k=50,
                top_p=0.8,
                temperature=1.0,
                max_new_tokens=self.max_new_tokens
            )

            query = self.current_payload.get("prompt", "")
            media = self.current_payload.get("media", [])

            if self.task == "chat":
                response = pipe.chat((query, media), gen_config=gen_config)
                self.text = response.response.text
            else:
                response = pipe((query, media), gen_config=gen_config)
                self.text = response.response.text if hasattr(response, 'response') else response

            logger.info(f"Generation for id {self.current_id} finished successfully")
        except Exception as err:
            logger.error(f"Error processing multi-modal job: {err}")
            self.status = JobStatus.FAULTED

        self.start_submit_thread()

    def submit_job(self, endpoint="/api/v2/generate/multimodal/submit"):
        super().submit_job(endpoint=endpoint)

    def prepare_submit_payload(self):
        self.submit_dict = {
            "id": self.current_id,
            "generation": self.text,
        }

    def post_submit_tasks(self, submit_req):
        bridge_stats.update_inference_stats(self.current_model, submit_req.json()["reward"])
