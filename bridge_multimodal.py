"""This is the multi-modal bridge. It connects the horde with the LMDeploy processing"""
import os

# isort: off
# We need to import the argparser first, as it sets the necessary Switches
from worker.argparser.multimodal import args
from worker.utils.set_envs import set_worker_env_vars_from_config

set_worker_env_vars_from_config()  # Get `cache_home` from `bridgeconfig.yaml` into the environment variable

# isort: on
from worker.bridge_data.multimodal import MultiModalBridgeData
from worker.logger import logger, quiesce_logger, set_logger_verbosity
from worker.workers.multimodal import MultiModalWorker

def main():
    set_logger_verbosity(args.verbosity)
    quiesce_logger(args.quiet)

    bridge_data = MultiModalBridgeData()
    try:
        bridge_data.reload_data()

        worker = MultiModalWorker(bridge_data)

        worker.start()

    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt Received. Ending Process")
    logger.init(f"{bridge_data.worker_name} Instance", status="Stopped")

if __name__ == "__main__":
    main()