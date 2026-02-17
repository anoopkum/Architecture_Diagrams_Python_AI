"""Generate diagram by parsing the natural-language instructions file.
This script expects `../instructions.md` (the file you wrote) and creates
`diagrams/from_instructions.png/.dot` and attempts drawio conversion.
"""
import re
import subprocess
from pathlib import Path
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.azure.network import ApplicationGateway, FrontDoors, NetworkSecurityGroupsClassic, Firewall, RouteTables
from diagrams.azure.compute import AppServices, FunctionApps
from diagrams.azure.integration import ServiceBus
from diagrams.azure.database import SQLServers, SQLDatabases
from diagrams.azure.storage import StorageAccounts
from diagrams.azure.security import KeyVaults
from diagrams.azure.analytics import LogAnalyticsWorkspaces
from diagrams.azure.devops import ApplicationInsights

ROOT = Path(__file__).resolve().parent
INS = ROOT.parent / "instructions.md"
OUT_BASE = ROOT / "diagrams" / "from_instructions"
OUT_BASE.parent.mkdir(parents=True, exist_ok=True)

def read_instructions(path):
    text = path.read_text()
    return text

def extract_section(text, heading):
    pattern = rf"{re.escape(heading)}\n(.*?)(?:\n\n|$)"
    m = re.search(pattern, text, re.S | re.I)
    return m.group(1).strip() if m else ""

def parse_resources(text):
    resources = {}
    # Networking
    net = extract_section(text, "1. **Networking**")
    if net:
        # VNet name and CIDR
        vnet_m = re.search(r"VNet:\s*\"?([\w\-]+)\"?\s*\(([^)]+)\)", net)
        if vnet_m:
            resources['vnet'] = {'name': vnet_m.group(1), 'cidr': vnet_m.group(2)}
        # subnets
        subs = re.findall(r"- \"([\w\-]+)\" \(([^)]+)\)", net)
        if subs:
            resources['subnets'] = [{'name': s[0], 'cidr': s[1]} for s in subs]
        # firewall
        fw = re.search(r"Azure Firewall:\s*\"?([\w\-]+)\"?", net)
        if fw:
            resources['firewall'] = fw.group(1)
    # Web Tier
    web = extract_section(text, "2. **Web Tier**")
    if web:
        afd = re.search(r"Azure Front Door:\s*\"?([\w\-]+)\"?", web)
        agw = re.search(r"Application Gateway.*?:\s*\"?([\w\-]+)\"?", web)
        webapp = re.search(r"Web App:\s*\"?([\w\-]+)\"?", web)
        resources['afd'] = afd.group(1) if afd else 'afd'
        resources['agw'] = agw.group(1) if agw else 'agw'
        resources['webapp'] = webapp.group(1) if webapp else 'webapp'
    # App Tier
    app = extract_section(text, "3. **Application Tier**")
    if app:
        backend = re.search(r"Backend App Service:\s*\"?([\w\-]+)\"?", app)
        func = re.search(r"Azure Function App:\s*\"?([\w\-]+)\"?", app)
        sb = re.search(r"Azure Service Bus:\s*\"?([\w\-]+)\"?", app)
        resources['backend'] = backend.group(1) if backend else 'app-api'
        resources['function'] = func.group(1) if func else 'function'
        resources['servicebus'] = sb.group(1) if sb else 'servicebus'
    # Data Tier
    data = extract_section(text, "4. **Data Tier**")
    if data:
        sqlsrv = re.search(r"SQL Server:\s*\"?([\w\-]+)\"?", data)
        sqldb = re.search(r"SQL Database:\s*\"?([\w\-]+)\"?", data)
        storage = re.search(r"Storage Account:\s*\"?([\w\-]+)\"?", data)
        kv = re.search(r"Azure Key Vault:\s*\"?([\w\-]+)\"?", data)
        resources['sqlsrv'] = sqlsrv.group(1) if sqlsrv else 'sqlsrv'
        resources['sqldb'] = sqldb.group(1) if sqldb else 'sqldb'
        resources['storage'] = storage.group(1) if storage else 'storage'
        resources['keyvault'] = kv.group(1) if kv else 'keyvault'
    # Monitoring
    mon = extract_section(text, "5. **Monitoring**")
    if mon:
        law = re.search(r"Log Analytics Workspace:\s*\"?([\w\-]+)\"?", mon)
        appi = re.search(r"Application Insights:\s*\"?([\w\-]+)\"?", mon)
        resources['law'] = law.group(1) if law else 'law'
        resources['appi'] = appi.group(1) if appi else 'appi'

    return resources

def build_diagram(resources):
    with Diagram("From Instructions", filename=str(OUT_BASE), outformat=["png","dot"], show=False, direction="TB"):
        users = Users("Users")
        afd = FrontDoors(resources.get('afd','afd'))

        with Cluster(f"{resources.get('vnet',{}).get('name','vnet')}\n({resources.get('vnet',{}).get('cidr','')})"):
            # subnets
            subs = resources.get('subnets', [])
            # map names to created nodes
            nodes = {}
            # Frontend
            if subs:
                frontend = subs[0]['name']
            else:
                frontend = 'snet-frontend'
            with Cluster(frontend):
                nsg_f = NetworkSecurityGroupsClassic('NSG-Frontend')
                agw = ApplicationGateway(resources.get('agw','agw'))
                webapp = AppServices(resources.get('webapp','webapp'))
            # Backend
            if len(subs) > 1:
                backend = subs[1]['name']
            else:
                backend = 'snet-backend'
            with Cluster(backend):
                nsg_b = NetworkSecurityGroupsClassic('NSG-Backend')
                backend_api = AppServices(resources.get('backend','backend'))
                func = FunctionApps(resources.get('function','func'))
                sb = ServiceBus(resources.get('servicebus','sb'))
            # Data
            if len(subs) > 2:
                data = subs[2]['name']
            else:
                data = 'snet-data'
            with Cluster(data):
                nsg_d = NetworkSecurityGroupsClassic('NSG-Data')
                sqlsrv = SQLServers(resources.get('sqlsrv','sqlsrv'))
                sqldb = SQLDatabases(resources.get('sqldb','sqldb'))
                storage = StorageAccounts(resources.get('storage','storage'))
                kv = KeyVaults(resources.get('keyvault','kv'))
            # Firewall
            azfw = Firewall(resources.get('firewall','azfw'))

        # Monitoring
        law = LogAnalyticsWorkspaces(resources.get('law','law'))
        appi = ApplicationInsights(resources.get('appi','appi'))

        # Connections
        users >> Edge(label='HTTPS') >> afd
        afd >> Edge(label='HTTPS') >> agw
        agw >> Edge(label='HTTPS') >> webapp
        webapp >> Edge(label='API') >> backend_api
        backend_api >> Edge(label='SQL (Private)') >> sqldb
        backend_api >> Edge(label='Storage (Private)') >> storage
        func >> Edge(label='Message') >> sb
        sb >> Edge(label='Consume') >> func
        func >> Edge(label='SQL (Private)') >> sqldb
        webapp >> Edge(label='Secrets', style='dotted') >> kv
        backend_api >> Edge(label='Secrets', style='dotted') >> kv
        func >> Edge(label='Secrets', style='dotted') >> kv
        webapp >> Edge(label='Outbound', style='dashed') >> azfw
        backend_api >> Edge(label='Outbound', style='dashed') >> azfw
        func >> Edge(label='Outbound', style='dashed') >> azfw
        for r in (webapp, backend_api, func, sqldb, storage):
            r >> Edge(label='Logs', style='dotted', color='green') >> law
        webapp >> Edge(label='Telemetry', style='dotted', color='green') >> appi

def main():
    text = read_instructions(INS)
    resources = parse_resources(text)
    build_diagram(resources)
    # attempt drawio conversion
    dot = OUT_BASE.with_suffix('.dot')
    drawio = OUT_BASE.with_suffix('.drawio')
    try:
        subprocess.run(['graphviz2drawio', str(dot), '-o', str(drawio)], check=True)
        print('Created drawio:', drawio)
    except Exception:
        print('graphviz2drawio not available or conversion failed; dot saved at', dot)

if __name__ == '__main__':
    main()
