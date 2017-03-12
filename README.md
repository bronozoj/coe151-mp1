# CoE 151 MP 1

This is a TCP Client-Server Application tailored to work with chat protocol standards from the Tuesday class (CoE 151 T 2:30-5:30)

[hanaserver](hanaserver.py) - Server-only application to be used for always-on configuration

[client-server](mp1-irc.py) - MP1 combined client-server application (up for submission)

[termios example](test modules/termiostest.py) - an example of how to control the terminal using the termios library

[exceptions example](test modules/exceptiontest.py) - an example of how to do custom exception handling

## Tuesday Class Protocol Specifications

>User types:          /name <alias>
>
>Server receives:  NAME <alias>
>
>User changes alias to <alias>, server broadcasts name change to everyone.


>User types:          /whois alias|IP
>
>Server receives:  WHOIS <alias|IP>
>
>Server sends alias (if set), and IP address of person of interest only to user who requested.


>User types:          <message>
>
>Server receives:  MSG <message> 
>
>Server broadcasts message with the format “<alias|IP>: <message>” to everyone.


>User types:          /quit
>
>Server receives:  QUIT
>
>Server closes user connection, server broadcasts “user left chat” message to everyone.


>User types:          /time
>
>Server receives:  TIME
>
>Server sends local time to user who requested.


>User types:          /whoami
>
>Server receives:  WHOAMI
>
>Server sends alias and IP address to user who requested.

Server broadcasts new connections with “user joins chat” message to everyone, and when user opts to change alias, user keeps alias until the end of his/her session (i.e., when user 10.158.22.99 changes own alias to “AriesBestGrill” and disconnects, when user reconnects, user is back to 10.158.22.99).

# Additional Notes

PS: the name 'Hana' which can be seen multiple times in the code is a reference to 'Hana Song' from 'Overwatch'

add me bronozoj#1884
