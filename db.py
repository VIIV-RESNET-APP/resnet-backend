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
    count(distinct(ar)) as articles, 
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



def getAuthorById(id):

    query="""
    match (au:Author {scopus_id:'"""+ id +"""'})
    optional match (au)-[:AFFILIATED_WITH]-(af:Affiliation)
    optional match (au)-[:WROTE]-(ar:Article)
    return au.scopus_id as scopusId, au.first_name as firstName, 
    au.last_name as lastName, au.auth_name as authName, au.initials as initials, 
    collect(distinct(af.name)) as affiliations, 
    collect({scopusId: ar.scopus_id, title: ar.title}) as articles
    """
    res = graph.run(query).data()

    if len(res) > 0:
        return res[0]


def getArticleById(id):

    query="""
    match (ar:Article {scopus_id: '"""+ id +"""'})
    optional match (ar)-[:WROTE]-(au:Author)
    optional match (ar)-[:BELONGS_TO]-(af:Affiliation)
    optional match (ar)-[:USES]-(to:Topic)
    RETURN ar.title as title, ar.abstract as abstract, 
    collect(distinct({scopusId: au.scopus_id, name: au.auth_name})) as authors, 
    collect(distinct(af.name)) as affiliations, 
    collect(distinct(to.name)) as topics
    """
    res = graph.run(query).data()

    if len(res) > 0:
        return res[0]


def getCoauthorsById(id):

    query="""
    match (au:Author {scopus_id:'"""+ id +"""'})-[r1:CO_AUTHORED]-(coAu:Author)
    return collect(distinct({scopusId: coAu.scopus_id, initials: coAu.initials, 
    firstName: coAu.first_name, lastName: coAu.last_name})) as nodes
    """

    res = graph.run(query).data()

    nodes = res[0]['nodes']

    if len(nodes) > 0:
        query="""
        match (au:Author {scopus_id:'"""+ id +"""'})-[r1:CO_AUTHORED]-(coAu:Author)
        return (collect(distinct({source: au.scopus_id, target: coAu.scopus_id,
        collabStrength: toFloat(r1.collab_strength)}))) as links
        """

        res = graph.run(query).data()

        links = res[0]['links']

        query="""
        match (au:Author {scopus_id:'"""+ id +"""'})-[r1:CO_AUTHORED]-(coAu:Author)-[r2:CO_AUTHORED]-(coCoAu:Author)
        match (au:Author {scopus_id:'"""+ id +"""'})-[:CO_AUTHORED]-(coCoAu:Author)
        where coAu.scopus_id > coCoAu.scopus_id
        return collect(distinct({source: coAu.scopus_id,target: coCoAu.scopus_id, 
        collabStrength: toFloat(r2.collab_strength)})) as links
        """

        res = graph.run(query).data()

        links = links + res[0]['links']

        return {"nodes": nodes, "links": links}

    else:
        links = []

    return {"nodes": nodes, "links": links}


    