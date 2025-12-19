import re
import pandas as pd
from html2text import html2text as h2t
import bleach
import yaml

class Converter:

    def _sanitize_cypher_identifier(self, value: str) -> str:
        sanitized = re.sub(r'[^A-Za-z0-9_]', '_', value)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"_{sanitized}"
        return sanitized

    def tuple_list_to_dict(self, tuple_list: list):
        if tuple_list is None:
            return None
        else:
            return {k: v for k, v in tuple_list}
    
    def tuple_list_to_list_of_tuples(self, tuple_list: list):
        if tuple_list is None:
            return None
        else:
            return [list(t) for t in tuple_list]

    def string_to_list(self, string: str, sepator=r'[ ,]+'):
        if string is None:
            return None
        else:
            return re.split(sepator, string)

    def string_to_int_list(self, string: str, sepator=r'[ ,]+'):
        string = f"{string}"
        if string in [None, '', 'None', 'nan']:
            return None
        else:
            return [int(x) for x in re.split(sepator, string)]
        
    def sub_string(self, string):
        if string is None:
            return None
        elif type(string) is list:
            for i, s in enumerate(string):
                string[i] = self.sub_string(s)
            return string
        else:
            subs = {'*': '', '#': ''}
            string = h2t(str(string))   # convert html in certain columns to text
            string = string.translate(str.maketrans(subs))
            string = re.sub(r'(\S)\n(\S)', r'\1 \2', string)
            string = string.replace('\n', '')
            return string

    def list_to_string(self, list: list, sepator=', '):
        if list is None:
            return None
        else:
            return sepator.join(list)
    
    def dict_to_string(self, dict: dict):
        if dict is None:
            return None
        else:
            if type(list(dict.values())[0]) is list:
                return '\n\n'.join([f"{k}: {', '.join(v)}" for k, v in dict.items()])
            return '\n\n'.join([f"{k}: {v}" for k, v in dict.items()])
    
    def string_to_dict(self, string: str):
        if string is None:
            return None
        else:
            string = string.replace('{', '').replace('}', '')
            out_dict = {k.strip(): v.strip() for k, v in [x.split(':') for x in string.split(',')]}
            out_dict = {k.removeprefix("'").removesuffix("'"): v.removeprefix("'").removesuffix("'") for k, v in out_dict.items()}
            return out_dict

    def convert_column_to_text(self, df: pd.DataFrame):
        # for column in ['Can Follow Refs', 'Domains', 'Object Marking Refs', 'Prerequisites', 'Alternate Terms', 'Can Precede Refs', 'Resources Required', 'Example Instances']:
        for column in ['Can_Follow_Refs', 'Domains', 'Object_Marking_Refs', 'Prerequisites', 'Alternate_Terms', 'Can_Precede_Refs', 'Resources_Required', 'Example_Instances']:
            df[column] = df[column].apply(lambda x: self.list_to_string(x))

        # for column in ['Description', 'Extended Description', 'Example Instances', 'Resources Required']:
        for column in ['Description', 'Extended_Description', 'Example_Instances', 'Resources_Required']:
            df[column] = df[column].apply(lambda x: self.sub_string(x))

        for column in ['Consequences', 'Skills_Required']:
            df[column] = df[column].apply(lambda x: self.dict_to_string(x))

        return df

    def convert_ids_to_capec_ids(self, df: pd.DataFrame):
        df['capec_id'] = df['external_references'].apply(lambda x: int(x[0]['external_id'].split('-')[1]) if x[0]['source_name'] == 'capec' else None)
        df['capec_children_id'] = df['x_capec_parent_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        df['capec_parents_id'] = df['x_capec_child_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        df['x_capec_peer_of_refs'] = df['x_capec_peer_of_refs'].apply(lambda ids: [int(df.loc[id]['capec_id']) for id in ids] if ids is not None or [] else None)
        return df
    
    def convert_column_names(self, df: pd.DataFrame):
        # position the index column to the first column
        new_columns = []
        for column in df.columns:
            column = column.replace('x_capec_', '')
            column = column.title()
            column = column.replace('Id', 'ID')
            new_columns.append(column)
        df.columns = new_columns
        return df
    
    def escape_script(self, html: str):
        html = bleach.clean(html, tags=['table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'b', 'i', 'u', 'br', 'a'], attributes=['style', 'class', 'id', 'href'], strip=True)
        return html

    def docker_compose_2_MACM(self, dockerComposeContent):
        dockerComposeContent = yaml.safe_load(dockerComposeContent)
        if 'services' not in dockerComposeContent:
            raise ValueError("The docker-compose file does not contain the 'services' section.")
        
        services = list(dockerComposeContent['services'].keys())
        service_identifiers = {service: self._sanitize_cypher_identifier(service) for service in services}

        networks_connects_services = {}
        port_service_map = {}
        for service, config in dockerComposeContent['services'].items():
            print(f"Processing service: {service} with config: {config}")
            if 'networks' in config: # Se il servizio specifica reti
                for network in config['networks']:
                    if network not in networks_connects_services:
                        networks_connects_services[network] = []
                    networks_connects_services[network].append(service)
            else: # Se il servizio non specifica reti, connettilo alla rete di default
                if 'default' not in networks_connects_services:
                    networks_connects_services['default'] = []
                networks_connects_services['default'].append(service)
            port_service_map[service] = []
            if 'ports' in config: # Mappa le porte ai servizi
                for port in config['ports']:
                    if isinstance(port, dict):
                        # Docker long syntax exposes host port under the published key
                        published = port.get('published')
                        host_port = str(published) if published is not None else str(port.get('target', ''))
                    else:
                        port_entry = str(port).split("/")[0]
                        segments = port_entry.split(":")
                        if len(segments) == 3:
                            # ip:host:container -> reuse host segment
                            host_port = segments[1]
                        elif len(segments) >= 2:
                            host_port = segments[0]
                        else:
                            host_port = segments[0]
                    if host_port:
                        port_service_map[service].append(host_port)

        service_uses_services = {}
        for service, config in dockerComposeContent['services'].items():
            if 'depends_on' in config:
                depends_on = config['depends_on']
                if isinstance(depends_on, dict):
                    depends_on = list(depends_on.keys())
                service_uses_services[service] = depends_on

        network_identifiers = {network: self._sanitize_cypher_identifier(network) for network in networks_connects_services.keys()}

        component_id = 1
        macm = []
        hosts = []
        connects = []
        macm.append("CREATE\n")
        macm.append(f"\t(CSP:CSP {{name:'CSP', type:'CSP', component_id:'{component_id}'}}),\n")
        component_id += 1
        hosts.append(f"\t(CSP) -[:provides]->(VM),\n")
        macm.append(f"\t(VM:Virtual:VM {{name:'VM', type:'Virtual.VM', component_id:'{component_id}'}}),\n")
        component_id += 1
        macm.append(f"\t(VM_OS:SystemLayer:OS {{name:'VM_OS', type:'SystemLayer.OS', component_id:'{component_id}'}}),\n")
        component_id += 1
        hosts.append("\t(VM)-[:hosts]->(VM_OS),\n")
        macm.append(f"\t(Docker:SystemLayer:ContainerRuntime {{name:'Docker', type:'SystemLayer.ContainerRuntime', component_id:'{component_id}'}}),\n")
        component_id += 1
        hosts.append("\t(VM_OS)-[:hosts]->(Docker),\n")
        for service in services:
            service_id = service_identifiers[service]
            macm.append(f"\t({service_id}_container:Virtual:Container {{name:'{service}_container', type:'Virtual.Container', component_id:'{component_id}'}}),\n")
            component_id += 1
            hosts.append(f"\t(Docker)-[:hosts]->({service_id}_container),\n")
            macm.append(f"\t({service_id}_OS:SystemLayer:OS {{name:'{service}_OS', type:'SystemLayer.OS', component_id:'{component_id}'}}),\n")
            component_id += 1
            hosts.append(f"\t({service_id}_container)-[:hosts]->({service_id}_OS),\n")
            macm.append(f"\t({service_id}:Service {{name:'{service}', type:'Service', component_id:'{component_id}', parameters:'{{\"ports\": \"{', '.join(port_service_map.get(service, []))}\"}}'}}),\n")
            component_id += 1
            hosts.append(f"\t({service_id}_OS)-[:hosts]->({service_id}),\n")
        
        for network, connected_services in networks_connects_services.items():
            network_id = network_identifiers[network]
            macm.append(f"\t({network_id}:Network:LAN {{name:'{network}', type:'Network.LAN', component_id:'{component_id}'}}),\n")
            component_id += 1
            hosts.append(f"\t(VM_OS)-[:hosts]->({network_id}),\n")
            for service in connected_services:
                service_id = service_identifiers[service]
                connects.append(f"\t({network_id})-[:connects]->({service_id}_container),\n")

        macm.append("\n")

        for host in hosts:
            macm.append(host)
        for connect in connects:
            macm.append(connect)
        for service, used_services in service_uses_services.items():
            service_id = service_identifiers.get(service)
            if service_id is None:
                continue
            for used_service in used_services:
                used_service_id = service_identifiers.get(used_service)
                if used_service_id is None:
                    continue
                macm.append(f"\t({service_id})-[:uses]->({used_service_id}),\n")

        macm[-1] = macm[-1].rstrip(",\n") # Rimuovi l'ultima virgola

        return "".join(macm), services, port_service_map