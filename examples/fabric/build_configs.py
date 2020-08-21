import os
import sys
import logging
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import write_dot
from umbra.design.configs import Profile, Topology, Scenario
from umbra.design.configs import FabricTopology

from base_configtx.fabric import org1_policy, org2_policy, org3_policy, org4_policy, orderer_policy, configtx


def build_simple_fabric_cfg():

    temp_dir = "./fabric_configs"
    configs_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), temp_dir))

    temp_dir = "./chaincode"
    chaincode_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), temp_dir))

    # Defines Fabric Topology - main class to have orgs/peers/cas/orderers added
    fab_topo = FabricTopology('fabric_simple', configs_dir, chaincode_dir)  

    # Defines scenario containing topology, so events can be added   
    # NOTE: these addr are also hardcoded at run.sh
    entrypoint = {
        "umbra-scenario": "172.17.0.1:8988",
        "umbra-monitor" : "172.17.0.1:8990"
    }
    scenario = Scenario(id="Fabric-Simple-01", entrypoint=entrypoint, folder=configs_dir)
    scenario.set_topology(fab_topo)

    domain = "example.com"
    image_tag = "1.4.0.1"

    fab_topo.add_org("org1", domain, policies=org1_policy)
    fab_topo.add_peer("peer0", "org1", anchor=True, image_tag=image_tag)
    fab_topo.add_peer("peer1", "org1", image_tag=image_tag)

    fab_topo.add_org("org2", domain, policies=org2_policy)
    fab_topo.add_peer("peer0", "org2", anchor=True, image_tag=image_tag)
    fab_topo.add_peer("peer1", "org2", image_tag=image_tag)

    fab_topo.add_org("org3", domain, policies=org3_policy)
    fab_topo.add_peer("peer0", "org3", anchor=True, image_tag=image_tag)
    
    fab_topo.add_org("org4", domain, policies=org4_policy)
    fab_topo.add_peer("peer0", "org4", anchor=True, image_tag=image_tag)  
    # fab_topo.add_peer("peer1", "org4", anchor=True, image_tag=image_tag)

    agent_image = "umbra-agent"
    agent_name = "umbraagent" # umbraagent.example.com
    fab_topo.add_agent(agent_name, domain, image=agent_image)

    ord_specs = [
        {"Hostname": "orderer"},
        {"Hostname": "orderer2"},
        {"Hostname": "orderer3"},
        {"Hostname": "orderer4"},
        {"Hostname": "orderer5"},
    ] 

    fab_topo.add_orderer("orderer", domain, mode="solo", specs=ord_specs, policies=orderer_policy, image_tag=image_tag)

    fab_topo.add_ca("ca", "org1", domain, "admin", "admin_pw", image_tag=image_tag)
    fab_topo.add_ca("ca", "org2", domain, "admin", "admin_pw", image_tag=image_tag)
    fab_topo.add_ca("ca", "org3", domain, "admin", "admin_pw", image_tag=image_tag)
    fab_topo.add_ca("ca", "org4", domain, "admin", "admin_pw", image_tag=image_tag)

    # Configtx quick fixes - checks which paths from configtx needs to have full org desc
    fab_topo.configtx(configtx)
    p1 = "TwoOrgsOrdererGenesis.Consortiums.SampleConsortium.Organizations"
    p2 = "TwoOrgsOrdererGenesis.Orderer.Organizations"
    p3 = "TwoOrgsChannel.Application.Organizations"
    fab_topo.set_configtx_profile(p1, ["org1", "org2", "org3", "org4"])
    fab_topo.set_configtx_profile(p2, ["orderer"])
    fab_topo.set_configtx_profile(p3, ["org1", "org2", "org3", "org4"])

    # Creates all config files - i.e., crypto-config configtx config-sdk
    fab_topo.build_configs()

    # Creates the network topology - orgs/nodes and links
    fab_topo.add_network("s0")
    fab_topo.add_org_network_link("org1", "s0", "E-Line")
    fab_topo.add_org_network_link("org2", "s0", "E-Line")
    fab_topo.add_org_network_link("org3", "s0", "E-Line")
    fab_topo.add_org_network_link("org4", "s0", "E-Line")
    fab_topo.add_org_network_link("orderer", "s0", "E-Line")
    fab_topo.add_org_network_link("umbraagent", "s0", "E-Line")

    # Defines resources for nodes and links
    node_resources = fab_topo.create_node_profile(cpus=1, memory=512, disk=None)
    link_resources = fab_topo.create_link_profile(bw=1, delay='2ms', loss=None)
    
    fab_topo.add_node_profile(node_resources, node_type="container")
    fab_topo.add_link_profile(link_resources, link_type="E-Line")
    
    # topo_built = fab_topo.build()
    # print("topo_built =", topo_built)
    # print("fab_topo.show()")
    # fab_topo.show()
  
    ev_create_channel = {
        "action": "create_channel",
        "org": "org1",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "profile": "TwoOrgsChannel",
    }

    ev_join_channel_org1 = {
        "action": "join_channel",
        "org": "org1",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0", "peer1"],
    }

    ev_join_channel_org2 = {
        "action": "join_channel",
        "org": "org2",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0", "peer1"],
    }

    ev_join_channel_org3 = {
        "action": "join_channel",
        "org": "org3",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_join_channel_org4 = {
        "action": "join_channel",
        "org": "org4",
        "user": "Admin",
        "orderer": "orderer",
        "channel": "testchannel",
        "peers": ["peer0"],
    }


    ev_info_channel = {
        "action": "info_channel",
        "org": "org1",
        "user": "Admin",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_info_channel_config = {
        "action": "info_channel_config",
        "org": "org1",
        "user": "Admin",
        "channel": "testchannel",
        "peers": ["peer0"],
    }

    ev_info_channels = {
        "action": "info_channels",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer0"],
    }

    ev_info_network = {
        "action": "info_network",
        "orderer": "orderer",
    }

    ev_chaincode_install_org1 = {
        "action": "chaincode_install",
        "org": "org1",
        "user": "Admin",
        "chaincode_name": "example_cc",
        "chaincode_path": "github.com/example_cc",
        "chaincode_version": "v1.0",
        "peers": ["peer0", "peer1"],
    }

    ev_chaincode_install_org2 = {
        "action": "chaincode_install",
        "org": "org2",
        "user": "Admin",
        "chaincode_name": "example_cc",
        "chaincode_path": "github.com/example_cc",
        "chaincode_version": "v1.0",
        "peers": ["peer0", "peer1"],
    }

    ev_chaincode_instantiate_org1 = {
        "action": "chaincode_instantiate",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['a', '200', 'b', '50'],
        "chaincode_version": "v1.0",        
    }

    ev_chaincode_instantiate_org2 = {
        "action": "chaincode_instantiate",
        "org": "org2",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['a', '200', 'b', '50'],
        "chaincode_version": "v1.0",        
    }

    ev_chaincode_invoke_org1 = {
        "action": "chaincode_invoke",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['a', 'b', '100'],
    }

    ev_chaincode_query_org1 = {
        "action": "chaincode_query",
        "org": "org1",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['b'],
    }

    ev_chaincode_query_org2 = {
        "action": "chaincode_query",
        "org": "org2",
        "user": "Admin",
        "peers": ["peer1"],
        "channel": "testchannel",
        "chaincode_name": "example_cc",
        "chaincode_args": ['b'],
    }

    # TODO: add_event to kill_container
    ev_kill_container_peer0_org1 = {
        "command": "environment_event",
        "args": {
            "node_name": "peer0.org1.example.com", # TODO: not hardcode?
            "action": "kill_container",
            "action_args": {},
        },
        "schedule": {
            "from": 4, # run on the 4th second, after ev_create_channel
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    ev_kill_container_peer0_org2 = {
        "command": "environment_event",
        "args": {
            "node_name": "peer0.org2.example.com", # TODO: not hardcode?
            "action": "kill_container",
            "action_args": {},
        },
        "schedule": {
            "from": 4, # run on the 4th second, after ev_create_channel
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    ev_mem_limit_peer1_org1 = {
        "command": "environment_event",
        "args": {
            "action": "update_memory_limit",
            "action_args": {
                "mem_limit": 256000000,
                "memswap_limit": -1
            },
            "node_name": "peer1.org1.example.com"
        },
        "schedule": {
            "from": 4, # run on the 4th second, after ev_create_channel
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    ev_cpu_limit_peer1_org2 = {
        "command": "environment_event",
        "args": {
            "action": "update_cpu_limit",
            "action_args": {
                "cpu_quota": 10000,
                "cpu_period": 50000,
                "cpu_shares": -1,
                "cores": {}
            },
            "node_name": "peer1.org2.example.com"
        },
        "schedule": {
            "from": 4, # run on the 4th second, after ev_create_channel
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    """
    $ tc qdisc show dev s0-eth2
    qdisc htb 5: root refcnt 2 r2q 10 default 1 direct_packets_stat 0 direct_qlen 1000
    qdisc netem 10: parent 5:1 limit 1000 delay 4.0ms loss 10%

    $ tc qdisc show dev s0-eth5
    qdisc htb 5: root refcnt 2 r2q 10 default 1 direct_packets_stat 0 direct_qlen 1000
    qdisc netem 10: parent 5:1 limit 1000 delay 4.0ms loss 10%
    """
    ev_update_link = {
        "command": "environment_event",
        "args": {
            "action": "update_link",
            "action_args": {
                "events": [
                    {
                        "group": "links",
                        "specs": {
                            "action": "update",
                            "online": True,
                            "resources": {
                                "bw": 3,
                                "delay": "4ms",
                                "loss": 10,
                            }
                        },
                        "targets": ("s0", "peer1.org1.example.com")
                    },
                    {
                        "group": "links",
                        "specs": {
                            "action": "update",
                            "online": True,
                            "resources": {
                                "bw": 3,
                                "delay": "4ms",
                                "loss": 10,
                            }
                        },
                        "targets": ("s0", "peer0.org3.example.com")
                    },
                ]
            },
        },
        "schedule": {
            "from": 6,
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    # $ ip link show s0-eth2 # ensure state DOWN
    # ... state DOWN mode DEFAULT
    ev_update_link_peer1_org1_downlink = {
        "command": "environment_event",
        "args": {
            "action": "update_link",
            "action_args": {
                "events": [
                    {
                        "group": "links",
                        "specs": {
                            "action": "update",
                            "online": False,
                            "resources": None
                        },
                        "targets": ("s0", "peer1.org1.example.com")
                    },
                ]
            },
        },
        "schedule": {
            "from": 1,
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    ev_update_link_peer1_org1_uplink = {
        "command": "environment_event",
        "args": {
            "action": "update_link",
            "action_args": {
                "events": [
                    {
                        "group": "links",
                        "specs": {
                            "action": "update",
                            "online": True,
                            "resources": {
                                "bw": 1,
                                "delay": "2ms",
                                # "loss": None,
                            }
                        },
                        "targets": ("s0", "peer1.org1.example.com")
                    },
                ]
            },
        },
        "schedule": {
            "from": 3,
            "until": 0,
            "duration": 0,
            "interval": 0,
            "repeat": 0
        },
    }

    ev_agent_v2 = {
        "agent_name": agent_name,
        "id": "100",
        "actions": [
            {
                'id': "1",
                "tool": "ping",
                "output": {
                    "live": False,
                    "address": None,
                },
                'parameters': {
                    "target": "peer0.org1.example.com",
                    "interval": "1",
                    "duration": "4",
                },
                'schedule': {
                    "from": 1,
                    "until": 0,
                    "duration": 0,
                    "interval": 0,
                    "repeat": 0
                },
            },
        ],
    }

    ev_monitor_v2 = {
        "id": "101",
        "actions": [
            {
                'id': "2",
                "tool": "container",
                "output": {
                    "live": False,
                    "address": None,
                },
                'parameters': {
                    "target": "peer0.org1.example.com",
                    "interval": "1",
                    "duration": "1",
                },
                'schedule': {
                    "from": 2,
                    "until": 0,
                    "duration": 0,
                    "interval": 0,
                    "repeat": 0
                },
            },
        ],

    }

    scenario.add_event("0", "fabric", ev_info_channels)
    scenario.add_event("1", "fabric", ev_create_channel)
    scenario.add_event_v2(1, "agent", ev_agent_v2)
    scenario.add_event_v2(3, "monitor", ev_monitor_v2)
    # TODO: kill_container event, note that the first arg for add_event
    # is not used since we will be using Handler scheduler.py
    # scenario.add_event("3", "environment", ev_kill_container_peer0_org1)
    # scenario.add_event("4", "environment", ev_kill_container_peer0_org2)
    # scenario.add_event("6", "environment", ev_update_link)
    # scenario.add_event("0", "environment", ev_update_link_peer1_org1_downlink)
    # scenario.add_event("0", "environment", ev_update_link_peer1_org1_uplink)
    scenario.add_event("2", "environment", ev_mem_limit_peer1_org1)
    scenario.add_event("2", "environment", ev_cpu_limit_peer1_org2)

    scenario.add_event("3", "fabric", ev_join_channel_org1)
    scenario.add_event("3", "fabric", ev_join_channel_org2)
    scenario.add_event("3", "fabric", ev_join_channel_org3)
    scenario.add_event("3", "fabric", ev_join_channel_org4)
    scenario.add_event("5", "fabric", ev_info_channel)
    # scenario.add_event("5", "fabric", ev_info_channel_config)

    # scenario.add_event("9", "fabric", ev_info_channels)
    # scenario.add_event("10", "fabric", ev_info_network)
    # scenario.add_event("11", "fabric", ev_chaincode_install_org1)
    # scenario.add_event("11", "fabric", ev_chaincode_install_org2)
    # scenario.add_event("13", "fabric", ev_chaincode_instantiate_org1)
    # scenario.add_event("13", "fabric", ev_chaincode_instantiate_org2)
    # scenario.add_event("23", "fabric", ev_chaincode_invoke_org1)
    # scenario.add_event("40", "fabric", ev_chaincode_query_org1)
    # scenario.add_event("43", "fabric", ev_chaincode_query_org2)

    # Save config file
    scenario.save()
    print("fab_topo.show()")
    
    for (n1, n2, d) in fab_topo.graph.edges(data=True):
        d.clear()

    for (n, d) in fab_topo.graph.nodes(data=True):
        d.clear()
    # pos = nx.nx_agraph.graphviz_layout(fab_topo.graph.graph)
    # nx.draw(fab_topo.graph)
    write_dot(fab_topo.graph, "umbra_topo.dot")
    # fab_topo.show()
    # nx.draw(fab_topo.graph)
    # plt.savefig("test1.png")

def builds():
    build_simple_fabric_cfg()

def setup_logging(log_level=logging.DEBUG):
    """Set up the logging."""
    logging.basicConfig(level=log_level)
    fmt = ("%(asctime)s %(levelname)s (%(threadName)s) "
           "[%(name)s] %(message)s")
    colorfmt = "%(log_color)s{}%(reset)s".format(fmt)
    datefmt = '%Y-%m-%d %H:%M:%S'

    try:
        from colorlog import ColoredFormatter
        logging.getLogger().handlers[0].setFormatter(ColoredFormatter(
            colorfmt,
            datefmt=datefmt,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red',
            }
        ))
    except ImportError:
        pass

    logger = logging.getLogger('')
    logger.setLevel(log_level) 

if __name__ == "__main__":
    setup_logging()
    builds()
