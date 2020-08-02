import logging
from umbra.common.scheduler import Handler

logger = logging.getLogger(__name__)

# TODO: think how build_calls should be implemented

class EnvironmentEvent():
    def __init__(self):
        self.handler = Handler()
        # TODO: url:port for umbra-scenario
        self.address = None

    def config(self, address):
        self.address = address

    def serialize_bytes(self, msg):
        msg_bytes = b''

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode('utf32')

        return msg_bytes

    # TODO: connect to umbra-scenario Establish, pass some stuff
    # Handler will take this and run
    async def call_scenario(self, test, command, params, address):
        logger.info(f"Deploying Scenario - {command}")

        scenario = self.serialize_bytes(topology)
        # deploy = Workflow(id=test, workflow=command, scenario=scenario)
        # deploy.timestamp.FromDatetime(datetime.now())

        # host, port = address.split(":")
        # channel = Channel(host, port)
        # stub = ScenarioStub(channel)
        # # TODO: connect to Modify method which takes Environment
        # status = await stub.Establish(deploy)

        # if status.error:
        #     ack = False
        #     logger.info(f'Scenario not deployed error: {status.error}')
        # else:
        #     ack = True
        #     logger.info(f'Scenario deployed: {status.ok}')

        #     info = self.parse_bytes(status.info)
        #     logger.debug(f'info = {info}')

        # channel.close()

        return ack,info

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
