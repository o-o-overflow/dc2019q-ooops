Order of the Overflow Proxy Service (OOOPS):
===

# Public information
On our corporate network, the only overflow is the Order of the Overflow.

Score: 400 points

Category: Web

Author: fasano

Download: [public_files/info.pac](public_files/info.pac)


# Private information
## Running the container
The tester script breaks with multiple ports. This service needs to expose 5000 and 8080
```
docker build -t dc2019q:ooops ./service && docker run -it --rm -p 8080:8080 -p5000:5000 dc2019q:ooops
```

## Challenge Overview
The premise of this challenge is to leverage a bug in a proxy server to get a universal cross-site scripting bug which can then be used to access and exploit a target that would otherwise be unreachable.

## Steps
1. Deobfscuate provided info.pac file
2. Connect to proxy with credentials described in (de)obfscuated info.pac comments
3. Identify that any website containing `overflow` in the URL is blocked through info.pac comment
4. Explore proxy "blocked" pages. Identify they are served on all domains. Identify universal XSS
5. Request unblocking of a website. View referrer link to identify requests are coming from [internal www/](internal website)
6. Try to connect to the internal website, see "local connections only" error
7. Request unblocking of internal website with XSS, exfiltrate page contents. Observe obvious SQL query
8. Request unblocking of internal website with XSS, with malformed URL. Observe SQL error and investigate (trivial) SQL injection
9. Request unblocking of internal website with XSS and SQLi, identify flag table and structure
10. Using UXSS and SQLi, leak flag from internal website database


## Remaining TODOs
- [x] Write and validate end-to-end exploit
- [x] Move everything into docker container
- [x] Reduce permissions so exploitable SQLi can't be used to drop pending requests (split into 2 databases or use real SQL?)
- [x] Update info.pac with load-balanced url 
- [x] Add captcha to unblock requests
- [d] Write automated end-to-end exploit for testing
- [x] Consider switching back to phantomJS for faster xss testing
- [ ] Stress test and update info.yaml with number of allowed connections
- [x] Debug issues building container with `./tester` (though manual building works)
- [x]  (Optional) Add more CSS to make everything look better
- [x]  (Optional) Switch internal server to gunicorn or something more reliable for admin
- [ ]  (Optional) finish adding HTTPS support to proxy

