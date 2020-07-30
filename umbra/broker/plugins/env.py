import logging
from umbra.common.scheduler import Handler

logger = logging.getLogger(__name__)

# TODO: think how build_calls should be implemented

class EnvironmentEvent():
    def __init__(self):
        self.handler = Handler()

    def schedule(self, events):
        logger.info("HELLO EnvironmentEvent, events=%s", events)


     # refer agent/tools.py
    async def handle(self, instruction):
        pass
        # actions = instruction.get("actions")
        # calls = self.build_calls(actions)
        # results = await self.handler.run(calls)
        # evals = self.build_outputs(results)
        # logger.info(f"Finished handling instruction actions")
        # snap = {
        #     "id": instruction.get('id'),
        #     "evaluations": evals,
        # }
        # logger.debug(f"{snap}")
        # return snap
