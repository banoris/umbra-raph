import logging
import json
import asyncio
import functools
from datetime import datetime

from grpclib.client import Channel
from grpclib.exceptions import GRPCError

from google.protobuf import json_format

from umbra.common.protobuf.umbra_grpc import ScenarioStub
from umbra.common.protobuf.umbra_pb2 import Report, Workflow

from umbra.design.configs import Topology, Scenario
from umbra.broker.plugins.fabric import FabricEvents
from umbra.broker.plugins.env import EnvEventHandler

logger = logging.getLogger(__name__)


class Operator:
    def __init__(self, info):
        self.info = info
        self.scenario = None
        self.topology = None
        # TODO: add events_env
        self.events_fabric = FabricEvents()
        self.events_env = EnvEventHandler()
        # TODO: add new plugin called "environment"
        self.plugins = {}

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

    async def call_scenario(self, test, command, topology, address):
        logger.info(f"Deploying Scenario - {command}")

        # TODO: refactor this method to support both Scenario.Establish and Scenario.Modify
        scenario = self.serialize_bytes(topology)
        deploy = Workflow(id=test, workflow=command, scenario=scenario)
        deploy.timestamp.FromDatetime(datetime.now())
        
        host, port = address.split(":")
        channel = Channel(host, port)
        stub = ScenarioStub(channel)
        # TODO: connect to Modify method which takes Environment
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

        return ack,info  

    def config_plugins(self):
        logger.info("Configuring Umbra plugins")
        umbra_cfgs = self.topology.umbra
        plugin = umbra_cfgs.get("plugin")
        
        if plugin == "fabric":
            logger.info("Configuring Fabric plugin")
            topology = umbra_cfgs.get("topology")
            configtx = umbra_cfgs.get("configtx")
            configsdk = umbra_cfgs.get("configsdk")
            chaincode = umbra_cfgs.get("chaincode")
            ack_fabric = self.events_fabric.config(topology, configsdk, chaincode, configtx)
            if ack_fabric:
                self.plugins["fabric"] = self.events_fabric

        # TODO: plugin == "environment"

    def schedule_plugins(self, events):
        for name,plugin in self.plugins.items():
            logger.info("Scheduling plugin %s events", name)
            # TODO: Environment plugin MUST implement schedule method (abstract)
            # Basically 'schedule' will schedule a call to call_scenario to be executed later
            plugin.schedule(events)

    async def call_events(self, scenario, info_deploy):
        logger.info("Scheduling events")
                
        self.scenario = Scenario(None, None, None)
        self.scenario.parse(scenario)
        
        info_topology = info_deploy.get("topology")
        info_hosts = info_deploy.get("hosts")

        # TODO: to modify the topology based on EnvironmentEvent?
        #   If delete (terminate container), should it be reflected on the graph?
        #   Also, think about restarting terminated container. E.g., should you
        #   store the information of terminated container somewhere s.t. we can
        #   refer it again later?
        # TODO: if above is too complicated, focus on basic feature first
        topo = self.scenario.get_topology()
        topo.fill_config(info_topology)
        topo.fill_hosts_config(info_hosts)
        self.topology = topo
        logger.info("self.topology.show()")
        self.topology.show()
        logger.info(f"number_of_edges={self.topology.graph.number_of_edges()}")
        self.config_plugins()

        events = scenario.get("events")
        self.schedule_plugins(events)

    def config_env_event(self, wflow_id):
        logger.info("Configuring EnvironmentEvent")
        self.events_env.config(self.scenario.entrypoint, wflow_id)
        self.plugins["environment"] = self.events_env

    # TODO: maybe no need? call EnvironmentEvent.handler()
    async def schedule_env_event(self):
        pass

    async def call_env_event(self, wflow_id, scenario):
        self.config_env_event(wflow_id)
        events = scenario.get("events")
        # filter out non "environment" type events
        env_events = {key: value for key, value in events.items()
                            if value['category'] == "environment"}
        await self.events_env.handle(env_events)

    async def run(self, request):
        logger.info("Running config request")
        report = Report(id=request.id)

        
        request_scenario = request.scenario
        # logger.debug(f"Received scenario: {request_scenario}")       
        scenario = self.parse_bytes(request_scenario)

        if scenario:
            topology = scenario.get("topology")
            address = scenario.get("entrypoint")
            # NOTE: takes about 1.5mins to deploy topology
            ack,topo_info = await self.call_scenario(request.id, "start", topology, address)
            logger.info(f"topo_info={topo_info}")
            logger.info(f"scenario={scenario}")

            if ack:
                events_info = await self.call_events(scenario, topo_info)

                status_info = {
                    'topology': topo_info,
                    'events': events_info,
                }
                status_bytes = self.serialize_bytes(status_info)
                report.status = status_bytes

            else:
                ack,topo_info = await self.call_scenario(request.id, "stop", {}, address)

            await self.call_env_event(request.id, scenario)

            """
            # sleep until all scheduled FabricEvent completes
            await asyncio.sleep(42)
            args_killcontainer = {'action': "kill_container",
                                'node_name': "peer0.org1.example.com",
                                'params': None,}

            args_cpulimit = {'action': "update_cpu_limit",
                            'node_name': "peer0.org1.example.com",
                            'params': {'cpu_quota':   10000,
                                        'cpu_period': 50000,
                                        'cpu_shares': -1,
                                        'cores':      None,}}

            args_memlimit = {'action': "update_memory_limit",
                            'node_name': "peer0.org1.example.com",
                            # memory in term of bytes
                            'params': {'mem_limit':   256000000,
                                        'memswap_limit': -1,}}

            logger.debug("About to kill_container")
            # TODO: replace with call_event, which will schedule a call to call_scenario
            ack, topo_info = await self.call_scenario(request.id, "environment_event",
                args_memlimit, address)
            logger.debug("Done kill_container")
            """

        return report
    
