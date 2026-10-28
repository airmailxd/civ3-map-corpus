"""A view-only live view of the map-making VMs: each VM's screen as a
motion-JPEG stream, several frames a second, all on one page, with each
VM's map count and last log line. Nothing on the page can reach the VMs.

    python tools/civ3_maps/vm/watch_live.py [--port=8770] [--fps=4]

then open http://127.0.0.1:8770 (this PC only).
"""
import glob
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PIL import Image

VBOX = r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
CORPUS = r'C:\Dev\civ3_map_corpus'
WIDTH = 800  # frames are shrunk to this width

frames = {}       # VM name -> latest JPEG bytes
lock = threading.Condition()


def running_vms():
    out = subprocess.run([VBOX, 'list', 'runningvms'], capture_output=True, text=True).stdout
    return sorted(re.findall(r'^"(civ3gen-[^"]+)"', out, re.M), key=lambda n: (len(n), n))


def grab(name, fps):
    path = os.path.join(tempfile.gettempdir(), f'watch_{name}.png')
    while True:
        t = time.time()
        r = subprocess.run([VBOX, 'controlvm', name, 'screenshotpng', path], capture_output=True)
        if r.returncode == 0:
            try:
                img = Image.open(path).convert('RGB')
                img = img.resize((WIDTH, int(img.height * WIDTH / img.width)))
                buf = io.BytesIO()
                img.save(buf, 'JPEG', quality=70)
                with lock:
                    frames[name] = buf.getvalue()
                    lock.notify_all()
            except OSError:
                pass
        time.sleep(max(0, 1 / fps - (time.time() - t)))


def status():
    result = []
    for name in sorted(frames, key=lambda n: (len(n), n)):
        folder = os.path.join(CORPUS, f'vm_{name}')
        maps = len(glob.glob(os.path.join(folder, '*.SAV')))
        log = ''
        try:
            with open(os.path.join(folder, 'run.log'), errors='replace') as f:
                lines = [line.strip() for line in f if line.strip()]
                log = lines[-1] if lines else ''
        except OSError:
            pass
        result.append({'name': name, 'maps': maps, 'log': log})
    return result


# Three across and two down, all on one screen: each cell takes a sixth of
# the window, and its stream shrinks to fit under its caption.
PAGE = """<!doctype html><meta charset="utf-8"><title>Civ3 VMs</title>
<style>html,body{height:100%;margin:0}
body{background:#111;color:#ddd;font:12px sans-serif;overflow:hidden}
#g{display:grid;grid-template-columns:repeat(3,1fr);grid-template-rows:repeat(2,1fr);gap:6px;
  height:100vh;padding:6px;box-sizing:border-box}
#g>div{display:flex;flex-direction:column;min-height:0;min-width:0}
.cap{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
small{color:#9a9}
img{flex:1;min-height:0;width:100%;object-fit:contain;background:#000;display:block}</style>
<div id="g"></div>
<script>
async function tick(){
  let s=await (await fetch('/status')).json();
  let g=document.getElementById('g');
  for (let v of s) {
    let d=document.getElementById(v.name);
    if (!d) {
      d=document.createElement('div'); d.id=v.name;
      d.innerHTML='<div class="cap"><b></b> <span></span> <small></small></div><img src="/stream/'+v.name+'">';
      g.appendChild(d);
    }
    d.querySelector('b').textContent=v.name;
    d.querySelector('span').textContent=v.maps+' maps';
    d.querySelector('small').textContent=v.log;
  }
}
tick(); setInterval(tick, 3000);
</script>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            body = PAGE.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/status':
            body = json.dumps(status()).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith('/stream/'):
            name = self.path[len('/stream/'):]
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            last = None
            try:
                while True:
                    with lock:
                        lock.wait_for(lambda: frames.get(name) is not last, timeout=5)
                        frame = frames.get(name)
                    if frame is None or frame is last:
                        continue
                    last = frame
                    self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: '
                                     + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
        else:
            self.send_error(404)


def main(argv):
    opts = dict(a[2:].split('=', 1) for a in argv if a.startswith('--') and '=' in a)
    port, fps = int(opts.get('port', 8770)), float(opts.get('fps', 4))
    started = set()

    def watch_for_vms():
        while True:
            for name in running_vms():
                if name not in started:
                    started.add(name)
                    threading.Thread(target=grab, args=(name, fps), daemon=True).start()
            time.sleep(10)

    threading.Thread(target=watch_for_vms, daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    main(sys.argv[1:])
