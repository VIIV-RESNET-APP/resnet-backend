from py2neo import Graph


graph = Graph("bolt://localhost:7687", auth=("neo4j", "narias"))


def getAuthorsByQuery(name, page, size):

    query = """
    match (au:Author) 
    where  toLower(au.first_name) contains '"""+ name +"""' or 
    toLower(au.last_name) contains '"""+ name +"""' or 
    toLower(au.first_name) + " " + toLower(au.last_name) contains '"""+ name +"""' or
    toLower(au.last_name) + " " + toLower(au.first_name) contains '"""+ name +"""' or  
    toLower(au.auth_name) contains '"""+ name +"""' or 
    toLower(au.initials) CONTAINS '"""+ name +"""' or 
    au.scopus_id contains '"""+ name +"""'
    return count(au) as total
    """

    res = graph.run(query)

    total = res.data()[0]['total']

    query = """
    match (au:Author) 
    where  toLower(au.first_name) contains '"""+ name +"""' or 
    toLower(au.last_name) contains '"""+ name +"""' or 
    toLower(au.first_name) + " " + toLower(au.last_name) contains '"""+ name +"""' or
    toLower(au.last_name) + " " + toLower(au.first_name) contains '"""+ name +"""' or  
    toLower(au.auth_name) contains '"""+ name +"""' or 
    toLower(au.initials) CONTAINS '"""+ name +"""' or 
    au.scopus_id contains '"""+ name +"""'
    optional match (aff:Affiliation)-[:AFFILIATED_WITH]-(au)
    optional match (au)-[:WROTE]-(ar:Article)
    optional match (ar:Article)-[:USES]-(to:Topic)
    with au, ar, aff, to
    order by au.first_name asc, au.last_name asc
    return au.scopus_id as scopus_id, 
    [au.first_name + " " + au.last_name, au.auth_name, au.initials] as names, 
    collect(distinct(aff.name)) as affiliations, 
    count(ar) as articles, 
    collect(distinct(to.name)) as topics
    SKIP """+str((page-1)*size)+""" LIMIT """+str(size)+"""
    """

    res = graph.run(query)

    authors = []
    for item in res:
        author = {}
        author['scopusId'] = item.data()['scopus_id']
        author['names'] = item.data()['names']
        author['affiliations'] = item.data()['affiliations']
        author['articles'] = item.data()['articles']
        author['topics'] = item.data()['topics']
        authors.append(author)
    
    return {'total': total, 'data': authors}

    