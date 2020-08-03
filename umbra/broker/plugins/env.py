import logging

from datetime import datetime

from grpclib.client import Channel
from umbra.common.protobuf.umbra_grpc import ScenarioStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow

from umbra.common.scheduler import Handler

logger = logging.getLogger(__name__)

# TODO: think how build_calls should be implemented

class EnvironmentEvent():
    def __init__(self):
        self.handler = Handler()
        # TODO: url:port for umbra-scenario
        self.address = None
        # TODO: what's the best way to get this id required by
        # Workflow message for umbra-scenario server?
        self.test_id = None

    def config(self, address, test_id):
        self.address = address
        self.test_id = test_id

    def parse_bytes(self, msg):
        msg_dict = {}

        if type(msg) is bytes:
            msg_str = msg.decode('utf32')
            msg_dict = json.loads(msg_str)

        return msg_dict

    def serialize_bytes(self, msg):
        msg_bytes = b''

        if type(msg) is dict:
            msg_str = json.dumps(msg)
            msg_bytes = msg_str.encode('utf32')

        return msg_bytes

    # TODO: connect to umbra-scenario Establish, pass some stuff
    # Handler will take this and run
    async def call_scenario(self, command, scenario):
        logger.info(f"Deploying Scenario - {command}")

        # TODO: 'scenario' in Workflow message is just a json input to be
        # parsed by the receiving umbra-scenario server
        # Maybe can change to more generic name
        scenario = self.serialize_bytes(scenario)
        deploy = Workflow(id=self.test_id, workflow=command, scenario=scenario)
        deploy.timestamp.FromDatetime(datetime.now())

        host, port = self.address.split(":")
        channel = Channel(host, port)
        stub = ScenarioStub(channel)
        status = await stub.Establish(deploy)

        if status.error:
            ack = False
            logger.info(f'Scenario not deployed error: {status.error}')
        else:
            ack = True
            logger.info(f'Scenario deployed: {status.ok}')

            info = self.parse_bytes(status.info)
            logger.debug(f'info = {info}')

        channel.close()

        return ack, info

    def build_calls(self, events):
        calls = {}

        for event_id, event_args in events.items():
            params = event_args.get('params', {})
            # TODO: function or coroutine? Recall the fix 'repeat' bug
            # Without '()', it will be function
            action_call = self.call_scenario(params['command'], params['args'])
            # action_sched = event_args.get('params', {}).get('schedule', {})
            action_sched = params.get('schedule', {})
            logger.debug(f'ASD: action_sched={action_sched}')

            calls[event_id] = (action_call, action_sched)

        return calls

    def schedule(self, events):
        # {'3': {'category': 'environment', 'ev': 3, 'params': {'args': {'action': 'kill_container', 'action_args': {}, 'node_name': 'peer0.org1.example.com'}, 'command': 'environment_event', 'schedule': {'duration': 0, 'from': 3, 'interval': 0, 'repeat': 0, 'until': 0}}, 'when': '3'}}
        # TODO: restructure above dict
        logger.info("HELLO EnvironmentEvent, events=%s", events)
        calls = self.build_calls(events)
        # results = await self.handler.run(calls)


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
