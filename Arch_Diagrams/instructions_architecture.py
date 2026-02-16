"""Generate architecture diagram based on instructions.md scenario.
Outputs: diagrams/instructions_architecture.png, .dot and (if graphviz2drawio installed) .drawio
"""
import subprocess
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.azure.network import (
    VirtualNetworks, Subnets, ApplicationGateway, FrontDoors,
    NetworkSecurityGroupsClassic, Firewall, RouteTables
)
from diagrams.azure.compute import AppServices, FunctionApps
from diagrams.azure.integration import ServiceBus
from diagrams.azure.database import SQLServers, SQLDatabases
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.security import KeyVaults
from diagrams.azure.analytics import LogAnalyticsWorkspaces
from diagrams.azure.devops import ApplicationInsights

# Graph attributes (tuned for clearer layout)
graph_attr = {
    "splines": "ortho",
    "nodesep": "1.2",
    "ranksep": "1.5",
    "fontsize": "13",
    "bgcolor": "white",
    "pad": "0.5",
    "compound": "true",
    "rankdir": "TB"
}

vnet_attr = {"fontsize": "14", "bgcolor": "#E8F4F8", "style": "dashed", "margin": "25", "labelloc": "t"}
subnet_front_attr = {"fontsize": "13", "bgcolor": "#E3F2FD", "style": "rounded", "margin": "15"}
subnet_back_attr = {"fontsize": "13", "bgcolor": "#F3E5F5", "style": "rounded", "margin": "15"}
subnet_data_attr = {"fontsize": "13", "bgcolor": "#FFF3E0", "style": "rounded", "margin": "15"}
fw_attr = {"fontsize": "13", "bgcolor": "#FFEBEE", "style": "rounded", "margin": "15"}
mon_attr = {"fontsize": "13", "bgcolor": "#E8F5E9", "style": "rounded", "margin": "15"}

filename = "diagrams/instructions_architecture"

with Diagram("Contoso Instructions Architecture", filename=filename, outformat=["png","dot"], show=False, direction="TB", graph_attr=graph_attr):
    users = Users("Users")
    afd = FrontDoors("afd-contoso")

    with Cluster("vnet-contoso-auea-001\n(10.10.0.0/16)", graph_attr=vnet_attr):
        with Cluster("snet-frontend\n(10.10.1.0/24)", graph_attr=subnet_front_attr):
            nsg_front = NetworkSecurityGroupsClassic("NSG-Frontend")
            agw = ApplicationGateway("agw-contoso\n(WAF)")
            webapp = AppServices("app-frontend-portal")

        with Cluster("snet-backend\n(10.10.2.0/24)", graph_attr=subnet_back_attr):
            nsg_back = NetworkSecurityGroupsClassic("NSG-Backend")
            backend_api = AppServices("app-order-api")
            func = FunctionApps("func-order-processor")
            sb = ServiceBus("sb-contoso-orders")

        with Cluster("snet-data\n(10.10.3.0/24)", graph_attr=subnet_data_attr):
            nsg_data = NetworkSecurityGroupsClassic("NSG-Data")
            sqlsrv = SQLServers("sqlsrv-contoso")
            sqldb = SQLDatabases("sqldb-orders")
            storage = StorageAccounts("stcontosodata001")
            kv = KeyVaults("kv-contoso-prod")

        with Cluster("Firewall & Routing", graph_attr=fw_attr):
            azfw = Firewall("azfw-contoso")
            rt = RouteTables("rt-default-to-fw")

    with Cluster("Monitoring", graph_attr=mon_attr):
        law = LogAnalyticsWorkspaces("law-contoso-prod")
        appi = ApplicationInsights("appi-contoso")

    # Connections (explicit labels and ordering to match instructions.md layout)
    users >> Edge(label="HTTPS") >> afd
    afd >> Edge(label="HTTPS") >> agw
    agw >> Edge(label="HTTPS") >> webapp

    webapp >> Edge(label="API") >> backend_api
    backend_api >> Edge(label="SQL (Private)") >> sqldb
    backend_api >> Edge(label="Storage (Private)") >> storage

    func >> Edge(label="Message") >> sb
    sb >> Edge(label="Consume") >> func
    func >> Edge(label="SQL (Private)") >> sqldb

    webapp >> Edge(label="Secrets", style="dotted") >> kv
    backend_api >> Edge(label="Secrets", style="dotted") >> kv
    func >> Edge(label="Secrets", style="dotted") >> kv

    webapp >> Edge(label="Outbound", style="dashed") >> azfw
    backend_api >> Edge(label="Outbound", style="dashed") >> azfw
    func >> Edge(label="Outbound", style="dashed") >> azfw

    # Monitoring
    for r in (webapp, backend_api, func, sqldb, storage):
        r >> Edge(label="Logs", style="dotted", color="green") >> law
    webapp >> Edge(label="Telemetry", style="dotted", color="green") >> appi
    backend_api >> Edge(label="Telemetry", style="dotted", color="green") >> appi
    func >> Edge(label="Telemetry", style="dotted", color="green") >> appi

print("Generated PNG and DOT:", filename + ".png", filename + ".dot")

try:
    subprocess.run(["graphviz2drawio", f"{filename}.dot", "-o", f"{filename}.drawio"], check=True)
    print("Generated drawio:", filename + ".drawio")
except FileNotFoundError:
    print("graphviz2drawio not found; skip drawio conversion")
except subprocess.CalledProcessError as e:
    print("graphviz2drawio failed:", e)
