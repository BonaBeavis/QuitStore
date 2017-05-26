#!/usr/bin/env python3

import functools as ft

from rdflib import BNode
from quit.namespace import FOAF, PROV, QUIT

class Blame(object):
    """
    Reusable Blame object for web client
    """
    def __init__(self, quit):
        self.quit = quit

    def _generate_values(self, quads):
        result = list()

        for quad in quads:  
            (s, p, o, c) = quad
            
            # Todo: BNodes in VALUES are not supported by specification? Using UNDEF for now
            _s = 'UNDEF' if isinstance(s, BNode) else s.n3()
            _p = 'UNDEF' if isinstance(p, BNode) else p.n3()
            _o = 'UNDEF' if isinstance(o, BNode) else o.n3()
            _c = 'UNDEF' if isinstance(c, BNode) else c.n3()

            result.append((_s, _p, _o, _c))
        return result

    def run(self, quads=None, branch_or_ref='master'):
        """
        Annotated every quad with the respective author

        Args:
                querystring: A string containing a SPARQL ask or select query.
        Returns:
                The SPARQL result set
        """


        commit = self.quit.repository.revision(branch_or_ref)
        g = self.quit.instance(branch_or_ref)    

        #if not quads:
        quads = [x for x in g.store.quads((None, None, None, None))]

        print(quads)

        values = self._generate_values(quads)
        values_string = ft.reduce(lambda acc, quad: acc + '( %s %s %s %s )\n' % quad, values, '') 
                          
        print(values_string)
        
        q = """
            SELECT ?s ?p ?o ?context ?y ?name ?date WHERE {                
                ?commit quit:preceedingCommit* ?y .
                ?y      prov:endedAtTime ?date ;
                        prov:qualifiedAssociation ?qa ;
                        quit:updates ?update .
                ?qa     prov:agent ?user ;
                        prov:role quit:author .
                ?user foaf:mbox ?email ;
                        rdfs:label ?name .                    
                ?update quit:graph ?context ;
                        quit:additions ?additions . 
                GRAPH ?additions {
                    ?s ?p ?o 
                } 
                FILTER NOT EXISTS {
                    ?y quit:preceedingCommit+ ?z . 
                    ?z quit:updates ?update2 .
                    ?update2 quit:graph ?context ;
                        quit:removals ?removals . 
                    GRAPH ?removals {
                        ?s ?p ?o 
                    } 
                }
                VALUES (?s ?p ?o ?context) {
                    %s
                }                                 
            }                
            """ % values_string

        return self.quit.store.store.query(q, initNs = { 'foaf': FOAF, 'prov': PROV, 'quit': QUIT }, initBindings = { 'commit': QUIT['commit-' + commit.id] })