"""Read-only loopback case preview with HTTP ranges for video chapter seeking."""

import argparse
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "docs/case"


class CaseHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def log_message(self, *args):
        # No raw URLs/queries or request bodies in preview logs.
        pass

    def send_head(self):
        path = Path(self.translate_path(self.path)).resolve()
        if not path.is_relative_to(PUBLIC.resolve()):
            self.send_error(403)
            return None
        if path.is_dir():
            path /= "index.html"
        try:
            file = path.open("rb")
        except OSError:
            self.send_error(404)
            return None
        length = path.stat().st_size
        start, end = 0, length - 1
        ranged = self.headers.get("Range")
        if ranged:
            match = re.fullmatch(r"bytes=(\d+)-(\d*)", ranged)
            if not match:
                file.close()
                self.send_error(416)
                return None
            start = int(match[1])
            end = min(int(match[2]) if match[2] else end, end)
            if start > end:
                file.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{length}")
                self.end_headers()
                return None
        self.send_response(206 if ranged else 200)
        self.send_header(
            "Content-Type",
            "text/vtt; charset=utf-8" if path.suffix == ".vtt" else self.guess_type(str(path)),
        )
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if ranged:
            self.send_header("Content-Range", f"bytes {start}-{end}/{length}")
        self.end_headers()
        file.seek(start)
        self.remaining = end - start + 1
        return file

    def copyfile(self, source, outputfile):
        while self.remaining > 0:
            block = source.read(min(64 * 1024, self.remaining))
            if not block:
                break
            try:
                outputfile.write(block)
            except (BrokenPipeError, ConnectionResetError):
                break
            self.remaining -= len(block)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8780)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), CaseHandler) as server:
        print(f"Portfolio preview: http://127.0.0.1:{server.server_port}/", flush=True)
        server.serve_forever()
