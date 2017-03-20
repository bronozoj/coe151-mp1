# Machine Problem 1 for CoE 151

This documentation is also available in my [Github repository](https://github.com/bronozoj/coe151-mp1) along with my codes

This explains a lot about my implementation of an IRC-like chat client and server as well as a P2P model of chat.  
Note that these applications were rigorously tested on python3 and may not always work as intended in other earlier versions of python (python2.7 perhaps)

`mp1-irc.py` - Internet Relay Chat Version (Client-Server) full implementation  
`mp1-p2p.py` - Peer-to-Peer Chat Version (Client-Server) full implementation  
`hanaserver.py` - Interner Relay Chat Server-only implementation

## Tuesday Class Protocols

#### Chat commands

##### User changes alias to \<alias\>, server broadcasts name change to everyone.

>User types:          /name \<alias\>  
>Server receives:  NAME \<alias\>

##### Server sends alias (if set), and IP address of person of interest only to user who requested.

>User types:          /whois alias|IP  
>Server receives:  WHOIS \<alias|IP\>

##### Server broadcasts message with the format “\<alias|IP\>: \<message\>” to everyone.

>User types:          \<message\>  
>Server receives:  MSG \<message\>

##### Server closes user connection, server broadcasts “user left chat” message to everyone.

>User types:          /quit  
>Server receives:  QUIT

##### Server sends local time to user who requested.

>User types:          /time  
>Server receives:  TIME

##### Server sends alias and IP address to user who requested.

>User types:          /whoami  
>Server receives:  WHOAMI

#### Server-Client Communication

Clients search for the starting slash character `/` for input and parses possible command.  
>User types: /\<command\> \<parameters\>  
>Client Send Buffer: \<COMMAND\> \<parameters\>

#### Handling commands beyond this protocol

User-defined commands other than ones specified above can be made at the programmer's discretion but in order to comply with this protocol, all commands and communication model must be at least implemented by the client/server

## Program Implementation

### Exception Classes

I defined exception classes for the sole purpose of making the raised exceptions intuitive and easy to remember (UserQuit, PeerQuit, ServerDown)

### Socket Container Class

I designed a socket container class `NamedSocket` that stores and exposes socket functions used by my implementation while storing other custom information about that socket like alias name and address.

#### SelfSocket subclass

As an extension, i defined a subclass `SelfSocket` where I overrode some of the exposed socket function in its parent class and replaced it with terminal handling. For example, instead of referring to a socket file descriptor, it now refers to stdin to accept new characters. It also contains a function to read that new character (or escape sequence) and add it to its buffer. It also can receive sent data and be able to display it properly to the terminal without it affecting user input.

### Broadcasting and Command Parsing

When the application is run as a server, command interpretation is handled by a specific function, to which it can take into account the source and determine who to broadcast it to in the list of connected clients. It can also handle unexpected disconnections from clients that crash and leave the socket half-open and to forcefully disconnect it from the server(and broadcast its unexpected disconnection to everyone else).

### Chat runtime

I chose to make the application run on a single thread and to implement polling instead of using multithreading for the sole reason of synchronization. This is still plausible with a few users and a substantially good processor. My server code (and terminal handling) requires synchronization to ensure that it does not bug out and making it run on a single thread improves its robustness to those kinds of errors. However, this does not scale properly with large networks of connected users, where even high performance processors may experience problems in sending structured data properly.

### Termios and File Control Compatibility

I hoped to make a program with portable code since I used Python3 as my language but failed to do so because of dependencies with `termios` and `fcntl` python libraries which are not available (or would not work as inteded) on certain non-unix compliant operating systems (ahem.. Windows). Perhaps workarounds would be available in some other way that i have not explored in the making of this set of applications.  
The exception to this is the server-only program `hanaserver.py` which does not have this dependency
