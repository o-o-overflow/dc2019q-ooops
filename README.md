Order of the Overflow Proxy Service (OOOPS):
===

# Public information
Description: On our corporate network, the only overflow is the Order of the Overflow.

Category: Web

Difficulty: Hard

Author: [@AndrewFasano](https://twitter.com/andrewfasano)

Download: [service/info.pac](public_files/info.pac). Note competitors should only start with this file, not the IP address of the webserver.

## Running the Challenge Locally
You can build and launch the docker container with the following command. Instead of using info.pac, use [service/local.pac](local.pac) and replace the `url` variable with the IP address of your docker container.
```
docker build -t dc2019q:ooops ./service && docker run -it --rm -p 8080:8080 -p5000:5000 dc2019q:ooops
```
<br/><br/><br/>
# Solution Information
Spoilers below
<br/><br/><br/><br/><br/><br/>

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
8. Request unblocking of internal website with XSS, with malformed URL. Observe SQL error and investigate SQL injection
9. Request unblocking of internal website with XSS and SQLi, identify flag table and structure
10. Using UXSS and SQLi, leak flag from internal website database


# Known Issues
- The proxy doesn't actually support HTTPs

