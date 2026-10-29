#!/usr/bin/env python3
"""Serve the production Wi-Fi editor with simulated state on localhost:8766."""
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import argparse, json, os, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]

def demo_config():
    cache=Path(os.environ.get('PLATFORMIO_CORE_DIR','/tmp/midi-foot-toolchain'))/'packages/framework-espidf'
    source=Path(os.environ.get('IDF_PATH',cache))/'components/json/cJSON'
    with tempfile.TemporaryDirectory(prefix='midi-demo-') as name:
        p=Path(name)
        (p/'demo.cpp').write_text('''#include "config.hpp"
#include <cstdio>
#include <cstring>
int main(){auto c=foot::defaults();strcpy(c.switches[0].name,"Lead");
auto &s=c.switches[0];s.toggle=true;s.press.count=4;s.release.count=1;
s.press.messages[0]={1,2,24,0,5};s.press.messages[1]={0,3,17,127,5};s.release.messages[0]={0,3,17,0,5};
s.press.messages[2]={1,2,0,0,5,foot::Increment,1};s.press.messages[3]={1,3,0,0,5,foot::Decrement,2};c.nextCounterId=3;
auto j=configJson(c);auto text=cJSON_Print(j);puts(text);cJSON_free(text);cJSON_Delete(j);}
''')
        subprocess.run(['cc','-x','c','-c',str(source/'cJSON.c'),'-o',str(p/'json.o')],check=True)
        subprocess.run(['c++','-std=c++17','-Isrc','-I'+str(source),'src/core.cpp','src/config.cpp',str(p/'demo.cpp'),str(p/'json.o'),'-o',str(p/'demo')],cwd=ROOT,check=True)
        return json.loads(subprocess.check_output([str(p/'demo')]))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8766);args=parser.parse_args()
    config=demo_config();revision=1
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,data,kind='application/json'):
            body=data if isinstance(data,bytes) else json.dumps(data).encode()
            self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def state(self):return {'config':config,'revision':revision,'bleReady':True,'usbReady':True,'midiReady':True,'adcCalibrated':True,'mv':[2200,100,200],'key':0}
        def do_GET(self):
            if self.path=='/':
                html=(ROOT/'web/index.html').read_text().replace('<h1>','<p class="muted">Preview · Simulated controller · No hardware connection</p><h1>',1)
                self.send(html.encode(),'text/html; charset=utf-8')
            else:self.send(self.state())
        def do_POST(self):
            nonlocal config,revision
            if self.path=='/session':self.send({'token':'preview'});return
            data=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            config=data.get('config',config);revision+=1;self.send(self.state())
    print(f'Preview only: http://127.0.0.1:{args.port}/',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
if __name__=='__main__':main()
