Order of the Overflow Proxy Service (OOPS):
===

# Public information
On our corporate network, the only overflow is the Order of the Overflow.
Score: 350 or 400 points
Category: Web
Author: fasano
[public_files/info.pac](public_files/info.pac)


# Private information
## Challenge Overview
The premise of this challenge is to leverage a bug in a proxy server to get a universal cross-site scripting bug which can then be used to access and exploit a target that would otherwise be unreachable.

## Steps
1. Deobfscuate provided .pac file
2. Connect to proxy with credentials described in (de)obfscuated info.pac comments
3. Identify that any website containing `overflow` in the URL is blocked through info.pac comment
4. Explore proxy "blocked" pages. Identify they are served on all domains. Identify universal XSS
5. Request unblocking of a website. View referrer link from internal server
6. Try to connect to internal website, see "local connections only" error
7. Request unblocking of internal website with XSS, exfiltrate page contents. Observe obvious SQL query
8. Request unblocking of internal website with XSS, with malformed URL. Observe SQL error and investigate (trivial) SQL injection
9. Request unblocking of internal website with XSS and SQLi, identify flag table and structure
10. Using UXSS and SQLi, leak flag from internal website database


## Remaining TODOs
- [ ] Move everything into docker container
- [ ] Finalize infrastructure design for load-balanced URL / IP addresses
- [ ] Add captcha/proof of work to unblock requests
- [ ] (Optional) add HTTPS support to proxy
