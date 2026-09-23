import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_egoi = os.getenv("api_egoi")
sender_id = os.getenv("sender_id")

URL = "https://slingshot.egoiapp.com/api/v2/email/messages/action/send/single"


def enviar_email_confirmacao(nome: str, email: str, id_public: str):
    payload = {
        "senderId": sender_id,
        "to": email,
        "subject": "Seu Passaporte Exagerado foi criado! 🎉",

        "htmlBody": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>

<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
<tr>
<td align="center">

<table width="600" cellpadding="0" cellspacing="0"
style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.08);">

<tr>
<td align="center"
style="background:#E54E88;padding:30px;">

<h1 style="margin:0;color:white;">
🎉 Passaporte Exagerado
</h1>

</td>
</tr>

<tr>
<td style="padding:40px;">

<h2 style="margin-top:0;color:#333;">
Olá, {nome}!
</h2>

<p style="font-size:16px;color:#555;line-height:1.6;">
Seu cadastro foi realizado com sucesso.
</p>

<p style="font-size:16px;color:#555;">
Seu ID Público é:
</p>

<div
style="
background:#fafafa;
border:2px dashed #E54E88;
padding:18px;
border-radius:10px;
text-align:center;
font-size:28px;
font-weight:bold;
letter-spacing:2px;
color:#E54E88;
margin:30px 0;
">
{id_public}
</div>

<p style="color:#666;">
Guarde esse código. Ele será utilizado para consultar seus pontos durante o evento.
</p>

<b style="font-size: 16px;">Leia os QRCodes espalhados pelo evento e responda aos questionários para acumular pontos e trocar por brindes.</b>

<hr style="border:none;border-top:1px solid #eee;margin:35px 0;">

<p style="font-size:13px;color:#999;text-align:center;">
Este é um email automático. Não responda esta mensagem.
</p>

</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>""",

        "textBody": f"""Olá, {nome}!

Seu cadastro foi realizado com sucesso.

Seu ID Público: {id_public}

Guarde esse código. Ele será utilizado para consultar seus pontos durante o evento.""",

        "openTracking": False,
        "clickTracking": False,
        "group": "default"
    }

    headers = {
        "ApiKey": api_egoi,
        "Content-Type": "application/json"
    }

    response = requests.post(
        URL,
        json=payload,
        headers=headers,
        timeout=30
    )

    print(response.status_code)
    print(response.text)

    response.raise_for_status()