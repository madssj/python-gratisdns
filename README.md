python-gratisdns
================

A project which aims to combine the ease of python, with the power of GratisDNS.

Depends uppon [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) for html parsing.

Some other guys created the same in [php](https://github.com/kasperhartwich/php-gratisdns), and a ruby version is in the works.

Installation
============
Just copy ```gratisdns.py``` somewhere - that could be into ```site-packages```.

_Someone should create a ```setup.py``` file._

Examples
========
Relocate all secondary domains to a new ip:

```python
my_new_ip = '231.231.231.231'
from gratisdns import GratisDNS
g = GratisDNS('username', 'password')
for domain in g.get_secondary_domains():
	g.delete_secondary_domain(domain)
	g.create_secondary_domain(domain, my_new_ip)
```

All functions
-------------

```python
>>> from gratisdns import GratisDNS
>>> g = GratisDNS('username', 'password')
>>> g.get_primary_domains()
[]
>>> g.get_secondary_domains()
[]
>>> g.create_secondary_domain('mytest.dk', '123.123.123.123')
True
>>> g.delete_secondary_domain('mytest.dk')
True
>>> g.create_primary_domain('mytest.dk')
True
>>> g.get_primary_domains()
[u'mytest.dk']
>>> g.get_primary_domain_details('mytest.dk')
[{'domainid': 123, 'recordid': 123, 'type': u'A', 'host': u'localhost.mytest.dk', 'ttl': 43200, 'data': u'127.0.0.1'}]
>>> g.create_record('mytest.dk', 'test', 'CNAME', 'www.gratisdns.dk')
True
>>> g.update_record('mytest.dk', 159068, 'test2', 'CNAME', 'ssl.gratisdns.dk', 900)
True
>>> g.delete_record('mytest.dk', 'test2', 'CNAME')
True
>>> g.delete_primary_domain('mytest.dk')
True
```
