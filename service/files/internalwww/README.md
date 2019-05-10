Internal WWW
===
"Internal" webserver to view proxy unblock requests. Can only be accessed by local connections (and attackers pivoting through UXSS on admin).

Vulnerable to trivial SQL Injection.

URLs are visited using PhantomJS driven by Selenium by [../admin/](admin/) scripts.
