# testmsg
Generate RFC822 compliant e-mail messages for tests and send it over SMTP.

While it's easy to send test messages like `echo asdf | mail you@gmail.com` or via `telnet mx.example.com 25` I need a tool which:
- Generates valid messages
- Messages does not looks spammy or very suspicious
- Easy to use and repeat test
- Ability to customize messages
- Work well with msmtp or other full-featured SMTP client (e.g. which can send over secure SMTP connection with authentication)
- Support DKIM signatures

## Installation
~~~
pip3 install testmsg
~~~
or
~~~
pipx install testmsg
~~~

## Usage example
Just generate minimal valid message, print to stdout (not sending). 

~~~
$ testmsg --to you@gmail.com  --lorem 
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0
Subject: Sent with github.com/yaroslaff/testmsg
From: from@example.com
To: you@gmail.com

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempo=
r incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut al=
iquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore =
eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia des=
erunt mollit anim id est laborum.
~~~

## Options

### Sending  message
To actually send message via SMTP server add `--send localhost` and optionally add `-v` for verbosity.
~~~
testmsg -v --lorem --from you@example.net --to you@gmail.com --send localhost
~~~ 

See below about how to use authentication and  SSL/TLS and how to use with `msmtp` (or other smtp clients).

### Customize message
Use `--from`, `--to` and `--subject` to override basic properties of message, use `--add HEADER VALUE` to add custom header(s).

Default message text is empty, use `--text "blah blah blah"` or `--lorem` or `--msg PATH` or `--msg -` .(to read from stdin). Add `--time` to add current time as an prefix to text.

### Add attachments
Use `--attachment` (or `--att`) to add attachments: `--att FILE1 FILE2 ...`

### Sign with DKIM

Generate DKIM RSA keys:
~~~shell
# generate private RSA key for DKIM
openssl genrsa -out example.com.pem 1024
# generate public key for DKIM
openssl rsa -in example.com.pem -out example.com.pub -pubout
~~~

Make DKIM DNS record with as `SELECTOR`._domainkey.example.com and verify it (here I decide to use selector `mail`):
~~~shell
$ host -t txt mail._domainkey.example.com
mail._domainkey.example.com.net descriptive text "v=DKIM1; h=sha256; k=rsa; p=MII...."
~~~

send DKIM signed message to gmail or mail-tester.com! Use `--selector` and `--privkey` arguments.
~~~shell
testmsg -f test@example.com -t mailbox@gmail.com --lorem --selector mail --privkey example.com.pem -v --send localhost
~~~

## Use with authentication and SSL/STARTTLS SMTP servers

To use authentication, use `--user` and `--password` (or `--pass`) parameters. Use `--ssl` to use SSL-capable SMTP server (port 465), or use `--starttls` to use `STARTTLS` SMTP command. If neither `--ssl` nor `--starttls` is given, message and authentication credentials are sent over plain unencrypted connection, which is highly insecure.

If `--user` is not given (but `--password` given), testmsg will use username same as from (`--from` / `-f`) address. 

Example:

~~~
testmsg -v -f test1@example.com -t somebody@example.net --lorem --pass "MyTestPass" --send mx.example.com --starttls
~~~

## Use together with msmtp

Here we send with TLS and authentication (using [msmtp](https://github.com/marlam/msmtp)). Username for authentication (`--user`) is same as FROM address. Testmsg generates valid message and msmtp sends it.

~~~
FROM=sender@example.com
TO=recipient@gmail.com

testmsg -f $FROM -t $TO --lorem | msmtp -v --host smtp.office365.com --port 587 --user $FROM --passwordeval='echo MyTestPass' -f $FROM --tls=on --auth=on $TO
~~~