import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import quote


class SmtpMailer:
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        origin: str,
        starttls: bool = False,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.host, self.port, self.sender, self.origin = host, port, sender, origin
        self.starttls, self.username, self.password = starttls, username, password

    def send(self, email: str, purpose: str, token: str) -> None:
        route, title = {
            "customer-claim": ("vincular-cadastro", "Vincule seu cadastro PetLand"),
            "verify": ("verificar-email", "Confirme seu e-mail"),
            "reset": ("redefinir-senha", "Redefina sua senha"),
            "invite": ("aceitar-convite", "Seu convite para a equipe PetLand"),
            "bootstrap": ("aceitar-convite", "Primeiro acesso administrativo PetLand"),
        }[purpose]
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = email
        message["Subject"] = f"PetLand — {title}"
        # Fragment is removed by the UI and never sent in HTTP URLs or Referer.
        message.set_content(
            f"{title}\n\nAbra o link para continuar:\n{self.origin}/{route}#token={quote(token)}\n\nEste link é pessoal, tem prazo limitado e só pode ser usado uma vez.\nSe você não solicitou esta ação, ignore a mensagem."
        )
        try:
            with smtplib.SMTP(self.host, self.port, timeout=5) as smtp:
                if self.starttls:
                    smtp.starttls(context=ssl.create_default_context())
                if self.username and self.password:
                    smtp.login(self.username, self.password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            # A generic public response avoids enumeration; resend is explicit, not an in-memory job.
            logging.getLogger("petland").error("identity_mail_delivery_failed")
