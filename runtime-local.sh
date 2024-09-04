#!/bin/bash
if [ ! -f "conda/envs/linux/bin/python" ]; then
./update-runtime-local.sh
fi
bin/micromamba run -r conda -n linux "$@"
