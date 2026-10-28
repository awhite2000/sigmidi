#!/usr/bin/env python3
"""Call the user's local Fusion MCP, with JSON arguments from a file."""
import json,sys,urllib.request,os
from pathlib import Path
URL='http://127.0.0.1:27182/mcp'
headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
def rpc(payload):
    request=urllib.request.Request(URL,json.dumps(payload).encode(),headers)
    with urllib.request.urlopen(request,timeout=int(os.environ.get("FUSION_MCP_TIMEOUT", "900"))) as response:
        session=response.headers.get('Mcp-Session-Id')
        if session: headers['Mcp-Session-Id']=session
        data=response.read().decode()
        if not data:return None
        if data.lstrip().startswith('{'):return json.loads(data)
        for line in data.splitlines():
            if line.startswith('data:'):
                result=json.loads(line[5:])
                if 'result' in result or 'error' in result:return result
init=rpc({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex chassis authoring','version':'1.0'}}})
if not init or 'error' in init:raise RuntimeError(init)
headers['MCP-Protocol-Version']=init['result']['protocolVersion']
rpc({'jsonrpc':'2.0','method':'notifications/initialized'})
args=json.loads(Path(sys.argv[2]).read_text())
result=rpc({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':sys.argv[1],'arguments':args}})
if len(sys.argv)>3:Path(sys.argv[3]).write_text(json.dumps(result,indent=2))
else: print(json.dumps(result,indent=2))
