"""This is the multi-modal bridge. It connects the horde with the LMDeploy processing"""
import os
import random
import sys
import threading
import requests
import yaml
from worker.consts import BRIDGE_CONFIG_FILE, BRIDGE_VERSION
from worker.logger import logger
from worker.argparser.multimodal import args
from worker.utils.set_envs import set_worker_env_vars_from_config
from lmdeploy import pipeline, GenerationConfig
from lmdeploy.vl import load_image
from lmdeploy.vl.constants import IMAGE_TOKEN

set_worker_env_vars_from_config()

class MultiModalBridgeData:
    """Configuration object for multi-modal jobs"""
    mutex = threading.Lock()

    def __init__(self):
        random.seed()
        self.args = args
        self.load_config()
        
        self.horde_url = os.environ.get("HORDE_URL", "https://stablehorde.net")
        self.worker_name = os.environ.get("HORDE_WORKER_NAME", f"MultiModal_Worker_{random.randint(-100000000, 100000000)}")
        self.api_key = os.environ.get("HORDE_API_KEY", "0000000000")
        self.priority_usernames = list(filter(lambda a: a, os.environ.get("HORDE_PRIORITY_USERNAMES", "").split(",")))
        self.max_power = int(os.environ.get("HORDE_MAX_POWER", 8))
        self.max_threads = int(os.environ.get("HORDE_MAX_THREADS", 1))
        self.queue_size = int(os.environ.get("HORDE_QUEUE_SIZE", 0))
        self.allow_unsafe_ip = os.environ.get("HORDE_ALLOW_UNSAFE_IP", "true") == "true"
        self.require_upfront_kudos = os.environ.get("REQUIRE_UPFRONT_KUDOS", "false") == "true"
        self.stats_output_frequency = int(os.environ.get("STATS_OUTPUT_FREQUENCY", 30))
        self.disable_terminal_ui = os.environ.get("DISABLE_TERMINAL_UI", "false") == "true"

        self.model = os.environ.get("model_name", "internlm/internlm-xcomposer2d5-7b")
        self.max_new_tokens = int(os.environ.get("max_new_tokens", 2048))
        self.max_input_length = int(os.environ.get("max_input_length", 4096))
        self.max_media_size = int(os.environ.get("max_media_size", 20480000))
        self.num_gpus = int(os.environ.get("num_gpus", 1))
        
        self.initialized = False
        self.username = None
        self.models_reloading = False
        self.supported_tasks = []
        self.pipe = None

    def load_config(self):
        if os.path.exists(BRIDGE_CONFIG_FILE):
            with open(BRIDGE_CONFIG_FILE, "rt", encoding="utf-8", errors="ignore") as configfile:
                config = yaml.safe_load(configfile)
                for key, value in config.items():
                    setattr(self, key, value)
            return True
        return None

    @logger.catch(reraise=True)
    def reload_data(self):
        previous_api_key = self.api_key
        self.load_config()
        
        # Update attributes from command-line arguments
        for attr in ['api_key', 'worker_name', 'horde_url', 'priority_usernames', 'max_threads', 'queue_size', 'allow_unsafe_ip', 'max_power']:
            if hasattr(self.args, attr):
                setattr(self, attr, getattr(self.args, attr))
        
        self.max_power = max(self.max_power, 2)
        
        if not self.initialized or previous_api_key != self.api_key:
            try:
                user_req = requests.get(
                    f"{self.horde_url}/api/v2/find_user",
                    headers={"apikey": self.api_key},
                    timeout=10,
                )
                user_req = user_req.json()
                self.username = user_req["username"]
            except Exception:
                logger.warning(f"Server {self.horde_url} error during find_user. Setting username 'N/A'")
                self.username = "N/A"
        
        self.initialize_pipeline()

    def initialize_pipeline(self):
        logger.debug("Initializing LMDeploy pipeline...")
        try:
            self.pipe = pipeline(self.model)
            self.supported_tasks = ["chat", "image_understanding", "video_understanding"]
            if "web" in self.model.lower():
                self.supported_tasks.append("webpage_creation")
            if "write" in self.model.lower():
                self.supported_tasks.append("article_writing")
            logger.info(f"LMDeploy pipeline initialized for model: {self.model}")
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize LMDeploy pipeline: {str(e)}")
            self.initialized = False

    def process_job(self, job_data):
        if not self.initialized:
            logger.error("LMDeploy pipeline not initialized. Cannot process job.")
            return None

        try:
            query = job_data.get("prompt", "")
            media = job_data.get("media", [])
            
            processed_media = []
            for item in media:
                if item['type'] == 'image':
                    image = load_image(item['url'])
                    processed_media.append(image)
                # Add support for video if needed
            
            if processed_media:
                media_tokens = [f"Image{i+1} {IMAGE_TOKEN}; " for i in range(len(processed_media))]
                query = "".join(media_tokens) + query

            gen_config = GenerationConfig(
                top_k=50,
                top_p=0.8,
                temperature=1.0,
                max_new_tokens=self.max_new_tokens
            )

            response = self.pipe((query, processed_media), gen_config=gen_config)
            return response.response.text if hasattr(response, 'response') else response
        except Exception as e:
            logger.error(f"Error processing job: {str(e)}")
            return None

def main():
    bridge_data = MultiModalBridgeData()
    try:
        bridge_data.reload_data()
        
        if not bridge_data.initialized:
            logger.error("LMDeploy pipeline is not initialized. Exiting.")
            sys.exit(1)
        
        from worker.workers.multimodal import MultiModalWorker
        worker = MultiModalWorker(bridge_data)
        worker.start()

    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt Received. Ending Process")
    logger.init(f"{bridge_data.worker_name} Instance", status="Stopped")

if __name__ == "__main__":
    main()