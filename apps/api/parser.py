from flask import current_app as app
from apps.databases.models import Macm
from apps.my_modules.converter import Converter
import nmap as nm

from apps.my_modules.utils import MacmUtils

class NmapParser:
        
    def __init__(self):
        self.converter = Converter()
        self.macmUtils = MacmUtils()
        
    def nmap_classic(self, macmID, content):
        app.logger.info(f"Running nmap classic parser on MACM {macmID}")
        scanner = nm.PortScanner()
        output = scanner.analyse_nmap_xml_scan(content)
        hosts = output['scan'].keys()
        query = self.add_hosts(macmID, hosts)
        return query
    
    def check_hosts(self, macmID, hosts):
        app.logger.info(f"Checking if hosts are already in MACM {macmID}")
        macmAssets = Macm.query.filter_by(App_ID=macmID, Type='Service.VM').all()
        for asset in macmAssets:
            if asset.Parameters is not None:
                ip = asset.Parameters.get('ip')
                if ip in hosts:
                    hosts.remove(ip)
        return hosts
    
    def add_hosts(self, macmID, hosts):
        hosts = self.check_hosts(macmID, hosts)
        appID, applicationName, maxID = self.macmUtils.get_macm_info(macmID)
        maxID = int(maxID) + 1
        query = ''
        for host in hosts:
            app.logger.info(f"Adding host {host} to MACM {macmID}")
            app.logger.info(type(host))
            query += f"""CREATE (VM{maxID}:service {{component_id:'{maxID}', name:'VM{maxID}', type:'Service.VM', app_id:'{appID}',application:'{applicationName}', parameters: '{{"ip":"{host}"}}'}})
                WITH VM{maxID}
                MATCH (net {{name:'CSPnet1'}})
                MERGE (VM{maxID})<-[:connects]-(net)\n"""
            maxID += 1
        return query