function jsonToCypher(jsonData) {
    jsonData = JSON.parse(jsonData);
    console.log(jsonData);
    nodeArray = jsonData.nodeDataArray;
    linkArray = jsonData.linkDataArray;
    if (nodeArray.length === 0 && linkArray.length === 0)
        return null;
    cypherQuery = "CREATE \n";
    try {
        for (const node of nodeArray) {
            cypherQuery += `(Node${node.key}:${node.primary_label}`
            if (node.secondary_label)
                cypherQuery += `:${node.secondary_label}`
            cypherQuery += ` {name:"${node.name}", component_id:"${node.key}", type:"${node.type}"}),\n`;
        }
        for (const link of linkArray) {
            if (!link.type || link.type === 'No Type'){
                throw new Error(`Link from Node ${nodeArray[link.from-1].name} to Node ${nodeArray[link.to-1].name} has no type defined.`);
            }
            cypherQuery += `(Node${link.from})-[:${link.type}]->(Node${link.to}),\n`;
        }
        // remove the last comma and add a semicolon
        cypherQuery = cypherQuery.slice(0, -2);
    }
    catch (error) {
        alert(error);
        return null;
    }
    return cypherQuery;
}

function cypherToJson(cypherQuery) {
    const nodeDataArray = [];
    const linkDataArray = [];
    const nodeMap = new Map(); // Map to store node variable names to keys
    
    try {
        // Remove CREATE keyword and trim
        let query = cypherQuery.trim().replace(/^CREATE\s*/i, '').trim();
        
        // Split by lines and filter out empty lines
        const lines = query.split('\n').filter(line => line.trim());
        
        let nodeKey = 1;
        
        for (let line of lines) {
            line = line.trim();
            if (!line) continue;
            
            // Remove trailing commas
            line = line.replace(/,\s*$/, '');
            
            // Match node pattern: (VarName:Label1:Label2 {properties})
            // Improved regex to handle nested JSON in properties
            const nodePattern = /\((\w+):([^{]+)\{((?:[^{}]|\{[^}]*\})*)\}\)/g;
            let nodeMatch;
            
            while ((nodeMatch = nodePattern.exec(line)) !== null) {
                const varName = nodeMatch[1]; // e.g., "User"
                const labels = nodeMatch[2].trim().split(':').map(l => l.trim()); // e.g., ["Party", "Human"]
                const propertiesStr = nodeMatch[3]; // e.g., "component_id:'1', name:'User', type:'Party.Human'"
                
                // Parse properties - improved to handle JSON strings with double quotes
                const properties = {};
                // Split by comma, but respect nested JSON structures
                let currentProp = '';
                let inString = false;
                let braceCount = 0;
                
                for (let i = 0; i < propertiesStr.length; i++) {
                    const char = propertiesStr[i];
                    
                    if (char === "'" && propertiesStr[i-1] !== '\\') {
                        inString = !inString;
                        currentProp += char;
                    } else if (inString) {
                        currentProp += char;
                        if (char === '{') braceCount++;
                        if (char === '}') braceCount--;
                    } else if (char === ',' && braceCount === 0) {
                        // End of property
                        const propMatch = currentProp.trim().match(/(\w+)\s*:\s*'(.*)'/);
                        if (propMatch) {
                            properties[propMatch[1]] = propMatch[2];
                        }
                        currentProp = '';
                    } else {
                        currentProp += char;
                    }
                }
                
                // Don't forget the last property
                if (currentProp.trim()) {
                    const propMatch = currentProp.trim().match(/(\w+)\s*:\s*'(.*)'/);
                    if (propMatch) {
                        properties[propMatch[1]] = propMatch[2];
                    }
                }
                
                // Parse parameters if present
                let parsedParameters = null;
                if (properties.parameters) {
                    try {
                        // The parameters might be a JSON string with escaped quotes
                        parsedParameters = JSON.parse(properties.parameters.replace(/\\"/g, '"'));
                    } catch (e) {
                        console.warn('Failed to parse parameters:', properties.parameters);
                    }
                }
                
                // Create node object
                const nodeData = {
                    name: properties.name || varName,
                    type: properties.type || labels.join('.'),
                    primary_label: labels[0] || null,
                    secondary_label: labels[1] || null,
                    background_color: asset_types_colors[properties.type] || "#0C7C59", // Default color, could be mapped from asset types
                    color:  getTextColor(asset_types_colors[properties.type] || "rgba(255, 255, 255, 1)"),
                    key: parseInt(properties.component_id) || nodeKey
                };
                
                // Add parameters if they exist
                if (parsedParameters) {
                    nodeData.parameters = parsedParameters;
                }
                
                nodeDataArray.push(nodeData);
                nodeMap.set(varName, nodeData.key);
                
                if (!properties.component_id) {
                    nodeKey++;
                }
            }
            
            // Match relationship pattern: (VarFrom)-[:TYPE {properties}]->(VarTo)
            const relPattern = /\((\w+)\)-\[:(\w+)(?:\s*\{([^}]*)\})?\]->\((\w+)\)/g;
            let relMatch;
            
            while ((relMatch = relPattern.exec(line)) !== null) {
                const fromVar = relMatch[1];
                const relType = relMatch[2];
                const propertiesStr = relMatch[3] || '';
                const toVar = relMatch[4];
                
                // Parse relationship properties if they exist
                const relProperties = {};
                if (propertiesStr && propertiesStr.trim()) {
                    const propPattern = /(\w+)\s*:\s*'([^']*)'/g;
                    let propMatch;
                    
                    while ((propMatch = propPattern.exec(propertiesStr)) !== null) {
                        relProperties[propMatch[1]] = propMatch[2];
                    }
                }
                
                // Create link object
                const linkData = {
                    from: nodeMap.get(fromVar),
                    to: nodeMap.get(toVar),
                    type: relType
                };
                
                // Add all properties to the link, not just application_protocol
                for (const [key, value] of Object.entries(relProperties)) {
                    linkData[key] = value;
                }
                
                linkDataArray.push(linkData);
            }
        }
        
        // Create final JSON structure
        const result = {
            class: "GraphLinksModel",
            nodeDataArray: nodeDataArray,
            linkDataArray: linkDataArray
        };
        console.log(result);
        return JSON.stringify(result, null, 2);
        
    } catch (error) {
        console.error('Error parsing Cypher query:', error);
        alert('Error parsing Cypher query: ' + error.message);
        return null;
    }
}

