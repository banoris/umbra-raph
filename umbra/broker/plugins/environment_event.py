from umbra.common.scheduler import Handler

# TODO: think how build_calls should be implemented

class EnvironmentEvent():
    def __init__(self, arg):
        self.handler = Handler()

     # refer agent/tools.py
     async def handle(self, instruction):
         actions = instruction.get("actions")
         calls = self.build_calls(actions)
         results = await self.handler.run(calls)
         evals = self.build_outputs(results)
         logger.info(f"Finished handling instruction actions")
         snap = {
             "id": instruction.get('id'),
             "evaluations": evals,
         }
         logger.debug(f"{snap}")
         return snap
