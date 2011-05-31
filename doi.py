#!/usr/bin/env python
# -*- encoding:utf-8 -*-

# kzfm <kerolinq@gmail.com>

from pyquery import PyQuery as pq
import re

r = re.compile('10.(\d+)/')

def get_contents(doi):
    DX_DOI = "http://dx.doi.org/"
    doi_url = DX_DOI + doi
    d = None
    try:
        d = pq(doi_url)
    except:
        pass

    return _extract(d,doi)

def _extract(d,doi):
    registrant_prefix = r.search(doi).group(1)    
    if registrant_prefix == '1021':
        return _extractACS(d,doi)
    else:
        return "no extractor"

#
#    title            = Column(String(256), unique=True)
#    pubmed_id        = Column(Integer, unique=True)
#    doi              = Column(String(128), unique=True)
#    abstract         = Column(Text())

def _extractACS(d,doi):
    title = d("h1.articleTitle").text()
    abstract = d("p.articleBody_abstractText").text()
    return {'doi': doi, 'title': title, 'abstract': abstract}
