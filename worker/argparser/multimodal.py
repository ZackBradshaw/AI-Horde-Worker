import argparse

parser = argparse.ArgumentParser(description="AI Horde Multi-Modal Worker")
parser.add_argument("--lmdeploy_url", type=str, help="URL for the LMDeploy server")
parser.add_argument("--sfw", action="store_true", help="Set the worker to SFW mode")
parser.add_argument("--blacklist", nargs="+", help="Blacklisted words or phrases")

args = parser.parse_args()
