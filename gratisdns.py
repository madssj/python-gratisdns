# -*- encoding: utf-8 -*-
"""
Copyright (c) 2007 Mads Sülau Jørgensen <mads@sulau.dk>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import re
from urllib import urlopen, urlencode
from BeautifulSoup import BeautifulSoup

__version__ = '$Id$'
__license__ = 'MIT'
__copyright__ = 'Mads Sülau Jørgensen <mads@sulau.dk>'

class GratisDNS(object): # {{{
    BACKEND_URL = 'https://ssl.gratisdns.dk/editdomains4.phtml'
    SUPPORTED_RECORDS = ('A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV')
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
    # }}}
    def _get_domains(self, soup): # {{{
        domains = set()
        for domain in soup.findAll('input', {'name': 'user_domain', 'type': 'hidden'}):
            domains.add(domain['value'])
        
        return list(domains)
    # }}}
    def _get_records(self, soup): # {{{
        records = []
        siblings = soup.findAll('tr', {'class': re.compile('BODY[1-2]BG')})
        
        for sibling in siblings:
            type = sibling.parent.find('td').next.string
            
            if type in self.SUPPORTED_RECORDS and sibling.find('input'):
                record = {}
                tds = sibling.findAll('td')
                form = sibling.find('form')
                
                record['type'] = type
                record['recordid'] = int(sibling.find('input', {'name': 'recordid'})['value'])
                record['domainid'] = int(sibling.find('input', {'name': 'domainid'})['value'])
                record['host'] = tds[0].string
                record['data'] = tds[1].string
                
                if type == 'MX':
                    record['preference'] = int(tds[2].string)
                    record['ttl'] = int(tds[3].string)
                elif type != 'TXT':
                    record['ttl'] = int(tds[2].string)
                
                records.append(record)
        
        return records
    # }}}
    def create_record(self, domain, host, type, data, preference=None, weight=None, port=None): # {{{
        if type in self.SUPPORTED_RECORDS:
            if host.find(domain) == -1:
                if host == '':
                    host = domain
                else:
                    host = "%s.%s" % (host, domain)
            
            args = {
                'action': 'add%srecord' % type.lower(),
                'user_domain': domain,
            }
            
            if type in ('A', 'AAAA'):
                args['host'] = host
                args['ip'] = data
            elif type == 'CNAME':
                args['host'] = host
                args['kname'] = data
            elif type == 'MX':
                args['host'] = host
                args['preference'] = preference or 10
                args['exchanger'] = data
            elif type == 'TXT':
                args['leftRR'] = host
                args['rightRR'] = data
            elif type == 'SRV':
                args['host'] = host
                args['exchanger'] = data
                args['preference'] = preference or 10
                args['weight'] = weight or 0
                args['port'] = port or 0
            
            soup = self._request(**args)
            for record in self._get_records(soup):
                if record['host'] == host:
                    return True
            return False
        else:
            raise ValueError, 'Unsupported record type.'
    # }}}
    def update_record(self, domain, recordid, host, type, data, ttl): # {{{
        if type in self.SUPPORTED_RECORDS:
            if host.find(domain) == -1:
                if host == '':
                    host = domain
                else:
                    host = "%s.%s" % (host, domain)
            
            soup = self._request(
                action='makechangesnow',
                recordid=recordid,
                type=type,
                user_domain=domain,
                host=host,
                new_data=data,
                new_ttl=ttl,
            )
            
            for record in self._get_records(soup):
                if record['host'] == host:
                    return True
            return False
        else:
            raise ValueError, 'Unsupported record type.'
    # }}}
    def delete_record(self, domain, host, type=None, preference=None): # {{{
        records = self.get_primary_domain_details(domain)
        
        if host.find(domain) == -1:
            if host == '':
                host = domain
            else:
                host = "%s.%s" % (host, domain)
        
        record = None
        for record in records:
            if record['host'] == host:
                if not type or record['type'] == type:
                    if not preference or record['preference'] == preference:
                        break
        
        if record:
            soup = self._request(
                action='delete%s' % record['type'].lower(),
                recordid=record['recordid'],
                domainid=record['domainid'],
                type=record['type'],
            )
            
            for record in self._get_records(soup):
                if record['host'] == host:
                    return False
            return True
        else:
            raise ValueError, 'Host not found.'
    # }}}
    def get_primary_domains(self): # {{{
        return self._get_domains(self._request(action='primarydns'))
    # }}}
    def get_secondary_domains(self): # {{{
        return self._get_domains(self._request(action='secondarydns'))
    # }}}
    def get_primary_domain_details(self, domain): # {{{
        soup = self._request(action='changeDNSsetup', user_domain=domain)
        
        return self._get_records(soup)
    # }}}
    def create_primary_domain(self, domain): # {{{
        soup = self._request(action='createprimaryandsecondarydnsforthisdomain', user_domain=domain)
        return domain in self._get_domains(soup)
    # }}}
    def create_secondary_domain(self, domain, master, slave='xxx.xxx.xxx.xxx'): # {{{
        soup = self._request(
            action='createsecondarydnsforthisdomain', 
            user_domain=domain, 
            user_domain_ip=master,
            user_domain_ip2=slave
        )
        
        return domain in self._get_domains(soup)
    # }}}
    def delete_primary_domain(self, domain): # {{{
        soup = self._request(action="deleteprimarydnsnow", user_domain=domain)
        return domain not in self._get_domains(soup)
    # }}}
    def delete_secondary_domain(self, domain): # {{{
        soup = self._request(action="deletesecondarydns", user_domain=domain)
        return domain not in self._get_domains(soup)
    # }}}
    def test_axfr(self, domain, master, slave=None): # {{{
        raise NotImplementedError()
    # }}}
    def _request(self, **kwargs): # {{{
        kwargs['user'] = self.username
        kwargs['password'] = self.password
        
        req = urlopen(self.BACKEND_URL, urlencode(kwargs))
        
        return BeautifulSoup(req.read())
# }}}
if __name__ == '__main__':
    # TODO: Add tests here.
    pass
