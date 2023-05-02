# testmsg
Generate RFC822 compliant e-mail messages for tests and send it over SMTP.

While it's easy to send test messages like `echo asdf | mail you@gmail.com` or via `telnet mx.example.com 25` I need a tool which:
- Generates valid messages
- Messages does not looks spammy or very suspicious
- Easy to use and repeat test
- Ability to customize messages
- Work well with msmtp or other full-featured SMTP client (e.g. which can send over secure SMTP connection with authentication)

## Installation
~~~
pip3 install testmsg
~~~

## Usage examples
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
To actually send message via SMTP server add `--send localhost` or (if you need really powerful SMTP client features) pipe to msmtp:
~~~
testmsg --lorem --to you@gmail.com --from you@example.net | msmtp --host mail.example.net -v --tls=on --tls-starttls=on --auth=on --user=you@example.com --passwordeval "echo YourPass" -f you@example.net you@gmail.com
~~~ 

Use `--from`, `--to` and `--subject` to override basic properties of message, use `--add HEADER VALUE` to add custom header(s).

Default message text is empty, use `--text "blah blah blah"` or `--lorem` or `--file PATH` or `--file -` .(to read from stdin). Add `--time` to add current time as an prefix to text.



