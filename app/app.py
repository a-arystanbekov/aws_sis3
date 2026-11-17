import json, os, signal, socket, sys, uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
import boto3

TOPIC_ARN = os.environ["TOPIC_ARN"]
sns = boto3.client("sns")


class H(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        self._send(200, {"service": "orders-api", "container": socket.gethostname()})

    def do_POST(self):
        if self.path != "/orders":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._send(400, {"error": "invalid json"})
        order_id = str(data.get("orderId") or uuid.uuid4())
        event = {"orderId": order_id, "total": data.get("total", 0)}
        try:
            sns.publish(TopicArn=TOPIC_ARN, Message=json.dumps(event))
        except Exception as e:
            print("publish failed", e, flush=True)
            return self._send(500, {"error": "publish failed"})
        print("published", order_id, flush=True)
        self._send(202, {"accepted": order_id})

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)


def stop(signum, frame):
    print("SIGTERM received", flush=True)
    sys.exit(0)


signal.signal(signal.SIGTERM, stop)
HTTPServer(("0.0.0.0", 8080), H).serve_forever()
