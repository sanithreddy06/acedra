"""A local SMTP server on 127.0.0.1:2525 that saves each message as a file (needs `pip install aiosmtpd`).
For verification only: point SMTP_HOST/SMTP_PORT at it with SMTP_STARTTLS=false."""
import asyncio
import itertools
import os
import pathlib

from aiosmtpd.controller import Controller
out = pathlib.Path(os.environ.get("ACEDRA_MAIL_DIR", "/tmp/acedra-mail")); counter = itertools.count(1)
out.mkdir(parents=True, exist_ok=True)
class Sink:
    async def handle_DATA(self, server, session, envelope):
        (out / f"{next(counter):03d}.eml").write_bytes(envelope.content)
        return "250 OK"
c = Controller(Sink(), hostname="127.0.0.1", port=2525); c.start()
asyncio.new_event_loop().run_forever()
