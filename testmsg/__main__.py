#!/usr/bin/env python3
import smtplib
import argparse
import datetime
import sys
import mimetypes
import dkim
from email.message import EmailMessage
import email.utils

lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " \
    "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n" \
    "Ut enim ad minim veniam," \
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.\n" \
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.\n" \
    "Excepteur sint occaecat cupidatat non proident, " \
    "sunt in culpa qui officia deserunt mollit anim id est laborum.\n"

__version__='0.0.9'


def attach(msg: EmailMessage, path: str):

    ctype, _ = mimetypes.guess_type(path)
    maintype, subtype = ctype.split('/', 1)

    with open(path, 'rb') as fp:
        msg.add_attachment(fp.read(),
                            maintype=maintype,
                            subtype=subtype,
                            filename=path)


def get_args():
    parser = argparse.ArgumentParser(description=f'Generate/Send valid RFC822 email messages for testing {__version__}')
    parser.add_argument('-f', '--from', dest='_from', default='from@example.com', metavar='EMAIL')
    parser.add_argument('-t', '--to', default='to@example.net', metavar='EMAIL')
    parser.add_argument('-s', '--subject', metavar='Subject', default='Sent with github.com/yaroslaff/testmsg')
    parser.add_argument('-a', '--add', nargs=2, action='append', dest='headers', metavar=('HEADER', 'VALUE'), help='add header')


    g = parser.add_argument_group('Message body')
    g.add_argument('--text')
    g.add_argument('--lorem', default=False, action='store_true', help='Use lorem ipsum...')
    g.add_argument('--msg', metavar='FILE', help='read message body from file (or "-" to read from stdin)')
    g.add_argument('--time', default=False, action='store_true', help='add timestamp to text')

    g.add_argument('--attach', nargs='+', metavar='FILE', help='add attachment')

    g = parser.add_argument_group('DKIM signature (optional)')
    g.add_argument('--selector', help='DKIM selector, e.g. "mail"')
    g.add_argument('--privkey', help='Path to private key')


    g = parser.add_argument_group('Sending (optional)')
    g.add_argument('--send', metavar='HOST')
    g.add_argument('-v', '--verbose', default=False, action='store_true', help='Verbose SMTP')


    return parser.parse_args()

def main():

    args = get_args()

    text = ''

    # generate text
    if args.text:
        text = args.text
    elif args.lorem:
        text = lorem
    elif args.msg:
        if args.msg == '-':
            for line in sys.stdin:
                text += line;
        else:
            with open(args.msg) as fh:
                text = fh.read()

    if args.time:
        text = datetime.datetime.now().strftime('%D %H:%M:%S') + '\n' + text

    msg = EmailMessage()
    msg.set_content(text)

    if args.headers:
        for h in args.headers:
            msg.add_header(h[0], h[1])

    if args.attach:
        for att_file in args.attach:
            attach(msg, att_file)

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = args.subject
    msg['From'] = f'"{args._from}" <{args._from}>'
    msg['To'] = f'"{args.to}" <{args.to}>'
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Message-Id'] = email.utils.make_msgid()

    if args.selector:
        domainname = args._from.split('@')[1]
        with open(args.privkey) as fh:
            dkim_private_key = fh.read()
        headers = [b"To", b"From", b"Subject"]
        sig = dkim.sign(
            message=msg.as_bytes(),
            selector=str(args.selector).encode(),
            domain=domainname.encode(),
            privkey=dkim_private_key.encode(),
            include_headers=headers,
            linesep=b''
        )
        # add the dkim signature to the email message headers.
        # decode the signature back to string_type because later on
        # the call to msg.as_string() performs it's own bytes encoding...
        
        # un-wrap sig
        # sig = sig.decode()

        msg["DKIM-Signature"] = sig.decode()[len("DKIM-Signature: ") :]


    # Send the message via our own SMTP server.
    if args.send:
        smtp = smtplib.SMTP(args.send)
        if args.verbose:
            smtp.set_debuglevel(True)
        try:
            r = smtp.send_message(msg)
        except smtplib.SMTPResponseException as e:
            print(e.smtp_code, e.smtp_error.decode(), file=sys.stderr)
        except smtplib.SMTPException as e:
            print(e, file=sys.stderr)
        smtp.quit()
    else:
        print(msg)

if __name__ == '__main__':
    main()