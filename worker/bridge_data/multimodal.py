"""The configuration of the bridge for multi-modal jobs"""

import os
import random
import sys
import threading
import requests
import yaml
from loguru import logger
from worker.consts import BRIDGE_CONFIG_FILE, BRIDGE_VERSION
from worker.bridge_data.framework import BridgeDataTemplate
from worker.argparser.multimodal import args

class MultiModalBridgeData(BridgeDataTemplate):
    """Configuration object for multi-modal jobs"""

    def __init__(self):
        super().__init__(args)
        self.lmdeploy_available = False
        self.model = None
        self.lmdeploy_url = os.environ.get("LMDEPLOY_URL", "http://localhost:23333")
        self.max_new_tokens = int(os.environ.get("HORDE_MAX_NEW_TOKENS", "2048"))
        self.max_input_length = int(os.environ.get("HORDE_MAX_INPUT_LENGTH", "4096"))
        self.branded_model = os.environ.get("HORDE_BRANDED_MODEL", "false") == "true"
        self.supported_tasks = []
        self.nsfw = os.environ.get("HORDE_NSFW", "true") == "true"
        self.blacklist = list(filter(lambda a: a, os.environ.get("HORDE_BLACKLIST", "").split(",")))
        self.max_media_size = int(os.environ.get("HORDE_MAX_MEDIA_SIZE", "20480000"))  # 20MB default

    @logger.catch(reraise=True)
    def reload_data(self):
        """Reloads configuration data"""
        previous_url = self.horde_url
        super().reload_data()
        if hasattr(self, "multimodal_name") and not self.args.worker_name:
            self.worker_name = self.multimodal_name
        if args.lmdeploy_url:
            self.lmdeploy_url = args.lmdeploy_url
        if args.sfw:
            self.nsfw = False
        if args.blacklist:
            self.blacklist = args.blacklist
        self.validate_lmdeploy()
        if self.lmdeploy_available and not self.initialized and previous_url != self.horde_url:
            logger.init(
                (
                    f"Username '{self.username}'. Server Name '{self.worker_name}'. "
                    f"Horde URL '{self.horde_url}'. LMDeploy URL '{self.lmdeploy_url}'"
                    "Worker Type: MultiModal"
                ),
                status="Joining Horde",
            )

    @logger.catch(reraise=True)
    def validate_lmdeploy(self):
        logger.debug("Retrieving settings from LMDeploy...")
        try:
            req = requests.get(f"{self.lmdeploy_url}/v1/models")
            models = req.json()
            self.model = models[0]["id"] if models else None
            self.supported_tasks = ["chat", "image_understanding", "video_understanding"]
            if "web" in self.model.lower():
                self.supported_tasks.append("webpage_creation")
            if "write" in self.model.lower():
                self.supported_tasks.append("article_writing")
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Server {self.lmdeploy_url} is up but does not appear to be an LMDeploy server.")
            self.lmdeploy_available = False
            return
        except requests.exceptions.ConnectionError:
            logger.error(f"Server {self.lmdeploy_url} is not reachable. Are you sure it's running?")
            self.lmdeploy_available = False
            return
        self.lmdeploy_available = True

    @logger.catch(reraise=True)
    def check_models(self, model_manager):
        """Check to see if we have the models needed"""
        if self.models_reloading:
            return
        if not self.initialized:
            logger.init("Models", status="Checking")
        
        if not self.model:
            logger.error("No model available from LMDeploy. Please check your configuration.")
            return

        # For multi-modal, we might not need to download models as they're handled by LMDeploy
        # But we can check if the model is available and supported
        model_info = model_manager.models.get(self.model, None)
        if not model_info:
            logger.warning(f"Model {self.model} is unknown. Please check your configuration.")
            return

        if int(model_info.get("min_bridge_version", 0)) > BRIDGE_VERSION:
            logger.warning(
                f"Model {self.model} is not supported in bridge version {BRIDGE_VERSION}. "
                "Please upgrade your bridge."
            )
            return

        if not self.initialized:
            logger.init_ok("Models", status="OK")

    def reload_models(self, model_manager):
        """Reloads models - Note this is IN A THREAD"""
        # For multi-modal, model reloading might be handled differently
        # This is a placeholder and might need to be adjusted based on LMDeploy's capabilities
        pass

    def load_config(self):
        # YAML config
        if os.path.exists(BRIDGE_CONFIG_FILE):
            with open(BRIDGE_CONFIG_FILE, "rt", encoding="utf-8", errors="ignore") as configfile:
                config = yaml.safe_load(configfile)
                # Map the config's values directly into this instance's properties
                for key, value in config.items():
                    setattr(self, key, value)
            return True  # loaded
        return None
