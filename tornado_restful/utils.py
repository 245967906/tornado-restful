from __future__ import annotations

import base64
import smtplib
import uuid
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import TracebackType
from typing import Optional, Type, Union

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key: str) -> None:
        self.key = key

    def encrypt(self, plaintext: str) -> str:
        plaintext = self._pad(plaintext)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        b64ciphertext = base64.b64encode(iv + cipher.encrypt(plaintext))
        ciphertext = b64ciphertext.decode("utf-8")
        return ciphertext

    def decrypt(self, ciphertext: str) -> str:
        ciphertext = base64.b64decode(ciphertext.encode("utf-8"))
        iv = ciphertext[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        b64plaintext = self._unpad(cipher.decrypt(ciphertext[AES.block_size:]))
        return b64plaintext.decode("utf-8")

    def _pad(self, text: str) -> str:
        pad_num = AES.block_size - (len(text) % AES.block_size)
        pad_char = chr(pad_num)
        return text + pad_char * pad_num

    def _unpad(self, text: bytes) -> bytes:
        pad_char = text[-1:]
        pad_num = ord(pad_char)
        return text[:-pad_num]


class SMTP:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        tls: bool = True,
        timeout: Union[int, float] = None,
    ) -> None:
        server = smtplib.SMTP(host, port, timeout=timeout)
        if tls:
            server.starttls()
        server.login(user, password)
        self.server = server
        self.multipart = MIMEMultipart()
        self.content_subtype = "plain"
        self.encoding = "utf-8"

    def __enter__(self) -> SMTP:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        self.server.quit()
        return False

    def sendmail(
        self,
        subject: str,
        content: str,
        from_email: str,
        to: Union[str, list],
    ) -> None:
        self.multipart["From"] = from_email
        self.multipart["To"] = ";".join(to) if isinstance(to, list) else to
        self.multipart["Subject"] = subject
        message = MIMEText(content, self.content_subtype, self.encoding)
        self.multipart.attach(message)
        self.server.sendmail(from_email, to, self.multipart.as_string())

    def add_attachment(
        self, content: Union[str, bytes], filename: str
    ) -> None:
        attachment = MIMEText(content, "plain", self.encoding)
        attachment.add_header("Content-Type", "application/octet-stream")
        attachment.add_header(
            "Content-Disposition", "attachment", filename=filename
        )
        self.multipart.attach(attachment)

    def add_image(self, content: bytes) -> str:
        image_id = str(uuid.uuid1())
        image = MIMEImage(content)
        image.add_header("Content-ID", f"<{image_id}>")
        self.multipart.attach(image)
        return image_id

    def close(self):
        self.server.quit()
