from flask import current_app as app
from apps.databases.models import Macm
from apps.my_modules.converter import Converter
import nmap as nm

from apps.my_modules.utils import MacmUtils

class NmapParser:
        
    def __init__(self):
        self.converter = Converter()
        
    def nmap_classic(self, macmID, content):
        app.logger.info(f"Running nmap classic parser on MACM {macmID}")
        scanner = nm.PortScanner()
        output = scanner.analyse_nmap_xml_scan(content)
        hosts = output['scan'].keys()
        check = self.check_hosts(macmID, hosts)
        output = self.converter.list_to_string(hosts)
        return output
    
    def check_hosts(self, macmID, hosts):
        app.logger.info(f"Checking if hosts are already in MACM {macmID}")
        macmAssets = Macm.query.filter_by(App_ID=macmID, Type='Service.VM').all()
        for asset in macmAssets:
            if asset.Parameters is not None:
                ip = asset.Parameters.get('ip')
                if ip in hosts:
                    hosts.remove(ip)
        return True
    
    def add_hosts(self, macmID, hosts):
        app.logger.info(f"Adding hosts to MACM {macmID}")
        for host in hosts:
            MacmUtils().add_asset(macmID, 'Service.VM', {'ip': host})
        return True