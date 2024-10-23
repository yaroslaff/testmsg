#!/usr/bin/env python3
import smtplib
import argparse
import datetime
import sys
import mimetypes
import dkim
from email.message import EmailMessage
import email.utils
from dotenv import load_dotenv
import os


lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, " \
    "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n" \
    "Ut enim ad minim veniam," \
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.\n" \
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.\n" \
    "Excepteur sint occaecat cupidatat non proident, " \
    "sunt in culpa qui officia deserunt mollit anim id est laborum.\n"

__version__='0.0.15'

verbose = False

def attach(msg: EmailMessage, path: str):

    ctype, _ = mimetypes.guess_type(path)
    maintype, subtype = ctype.split('/', 1)

    with open(path, 'rb') as fp:
        msg.add_attachment(fp.read(),
                            maintype=maintype,
                            subtype=subtype,
                            filename=path)


def vprint(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def get_args():
    
    if load_dotenv():
        vprint("loaded .env file")

    def_from = os.getenv('FROM', 'from@example.com')
    def_to = os.getenv('TO', 'to@example.net')
    def_subj = os.getenv('SUBJECT', 'Sent with github.com/yaroslaff/testmsg')

    def_text = os.getenv('TEXT')
    def_lorem = bool(os.getenv('LOREM', '0') == '1')
    def_msg = os.getenv('MSG')
    def_timestamp = os.getenv('TIMESTAMP', '0') == '1'

    def_send = os.getenv('SEND')
    def_ssl = os.getenv('SSL', '0') == '1'
    def_port = os.getenv('PORT')
    def_starttls = os.getenv('STARTTLS', '0') == '1'
    def_username = os.getenv('SMTPUSER')
    def_password = os.getenv('SMTPPASS')
    
    
    def_verbose = os.getenv('VERBOSE', '0') == '1'

    def_selector = os.getenv("DKIM_SELECTOR")
    def_privkey = os.getenv("DKIM_PRIVKEY")

    parser = argparse.ArgumentParser(description=f'Generate/Send valid RFC822 email messages for testing {__version__}')
    parser.add_argument('-f', '--from', dest='_from', default=def_from, metavar='EMAIL')
    parser.add_argument('-t', '--to', default=def_to, metavar='EMAIL')
    parser.add_argument('-s', '--subject', metavar='Subject', default=def_subj)
    parser.add_argument('-a', '--add', nargs=2, action='append', dest='headers', metavar=('HEADER', 'VALUE'), help='add header')


    g = parser.add_argument_group('Message body')
    g.add_argument('--text', default=def_text)
    g.add_argument('--lorem', default=def_lorem, action='store_true', help='Use lorem ipsum...')
    g.add_argument('--msg', metavar='FILE', default=def_msg, help='read message body from file (or "-" to read from stdin)')
    g.add_argument('--time', default=def_timestamp, action='store_true', help='add timestamp to text')

    g.add_argument('--attach', nargs='+', metavar='FILE', help='add attachment')

    g = parser.add_argument_group('DKIM signature (optional)')
    g.add_argument('--selector', default=def_selector, help='DKIM selector, e.g. "mail"')
    g.add_argument('--privkey', default=def_privkey, help='Path to private key')


    g = parser.add_argument_group('Sending (optional)')
    g.add_argument('--send', default=def_send, metavar='HOST')
    g.add_argument('--ssl', default=def_ssl, action='store_true', help='Use SSL (will use default port 465)')
    g.add_argument('--port', '-p', default=def_port, type=int, metavar='PORT')
    g.add_argument('--starttls', default=def_starttls, action='store_true', help='Use STARTTLS command')
    g.add_argument('--user', default=def_username, metavar='USERNAME')
    g.add_argument('--password', default=def_password, metavar='PASSWORD')
    g.add_argument('-r','--return', default=None, dest='_return', metavar='RETURN-PATH', help='Return-Path address (used in MAIL FROM). Default is same as --from')
    g.add_argument('-v', '--verbose', default=def_verbose, action='store_true', help='Verbose SMTP')


    return parser.parse_args()

def main():
    global verbose

    args = get_args()

    if args.verbose:
        verbose = True
        print("verbose mode")

    vprint(args)

    text = ''

    if args.password and not args.user:
        args.user = args._from

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

    return_path = args._return or args._from

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
        if args.ssl:
            smtp = smtplib.SMTP_SSL(args.send, port=args.port)
        else:
            smtp = smtplib.SMTP(args.send, port=args.port)
        if args.verbose:
            smtp.set_debuglevel(True)
        
        if args.starttls:
            smtp.starttls()

        if args.user:
            smtp.login(args.user, args.password)
        
        try:
            r = smtp.send_message(msg, from_addr=return_path)
        except smtplib.SMTPResponseException as e:
            print(e.smtp_code, e.smtp_error.decode(), file=sys.stderr)
        except smtplib.SMTPException as e:
            print(e, file=sys.stderr)
        smtp.quit()
    else:
        print(msg)

if __name__ == '__main__':
    main()