from py2neo import Graph
from tfidf import Model

def getDB():
    return Graph("bolt://52.146.3.93:7687", auth=("neo4j", "narias98"))

def getAuthorsByQuery(name, page, size):

    query = """
    match (au:Author) 
    where  toLower(au.first_name) contains '""" + name + """' or 
    toLower(au.last_name) contains '""" + name + """' or 
    toLower(au.first_name) + " " + toLower(au.last_name) contains '""" + name + """' or
    toLower(au.last_name) + " " + toLower(au.first_name) contains '""" + name + """' or  
    toLower(au.auth_name) contains '""" + name + """' or 
    toLower(au.initials) CONTAINS '""" + name + """' or 
    au.scopus_id contains '""" + name + """'
    return count(au) as total
    """

    res = getDB().run(query)

    total = res.data()[0]['total']

    query = """
    match (au:Author) 
    where  toLower(au.first_name) contains '""" + name + """' or 
    toLower(au.last_name) contains '""" + name + """' or 
    toLower(au.first_name) + " " + toLower(au.last_name) contains '""" + name + """' or
    toLower(au.last_name) + " " + toLower(au.first_name) contains '""" + name + """' or  
    toLower(au.auth_name) contains '""" + name + """' or 
    toLower(au.initials) CONTAINS '""" + name + """' or 
    au.scopus_id contains '""" + name + """'
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

    res = getDB().run(query).data()

    authors = []
    for item in res:
        author = {}
        author['scopusId'] = item['scopus_id']
        author['names'] = item['names']
        author['affiliations'] = item['affiliations']
        author['articles'] = item['articles']
        author['topics'] = item['topics']
        authors.append(author)


    if len(res) > 0:
        
        query = """
        match (au:Author) 
        where  toLower(au.first_name) contains '""" + name + """' or 
        toLower(au.last_name) contains '""" + name + """' or 
        toLower(au.first_name) + " " + toLower(au.last_name) contains '""" + name + """' or
        toLower(au.last_name) + " " + toLower(au.first_name) contains '""" + name + """' or  
        toLower(au.auth_name) contains '""" + name + """' or 
        toLower(au.initials) CONTAINS '""" + name + """' or 
        au.scopus_id contains '""" + name + """'
        optional match (au)-[:WROTE]-(ar:Article)-[:USES]-(to:Topic)
        with au, to, count(to.name) as frequency, collect(distinct to.name) as cTopics 
        order by au.first_name asc, au.last_name asc, frequency desc
        unwind cTopics as uTopics 
        return au.scopus_id as scopus_id, collect(distinct uTopics) as topics
        SKIP """+str((page-1)*size)+""" LIMIT """+str(size)+"""
        """

        res = getDB().run(query).data()

        for item in res:
            authorIndex = next((index for (index, d) in enumerate(authors) if d["scopusId"] == item['scopus_id']), None)
            if authorIndex != None:
                authors[authorIndex]['topics']  =  item['topics']
        
    return {'total': total, 'data': authors}


def getAuthorById(id):

    query = """
    match (au:Author {scopus_id:'""" + id + """'})
    optional match (au)-[:AFFILIATED_WITH]-(af:Affiliation)
    optional match (au)-[:WROTE]-(ar:Article)
    return au.scopus_id as scopusId, au.first_name as firstName, 
    au.last_name as lastName, au.auth_name as authName, au.initials as initials, 
    collect(distinct(af.name)) as affiliations, 
    collect(distinct({scopusId: ar.scopus_id, title: ar.title})) as articles
    """
    res = getDB().run(query).data()

    if len(res) > 0:

        author = res[0]

        query = """
        match (au:Author {scopus_id:'""" + id + """'})-[:WROTE]-(ar:Article)-[:USES]-(to:Topic)
        with to, count(to.name) as frequency
        return to.name as name order by frequency desc
        """

        res = getDB().run(query)

        return {**author, 'topics': [item.data()['name'] for item in res]}


def getArticleById(id):

    query = """
    match (ar:Article {scopus_id: '""" + id + """'})
    optional match (ar)-[:WROTE]-(au:Author)
    optional match (ar)-[:BELONGS_TO]-(af:Affiliation)
    optional match (ar)-[:USES]-(to:Topic)
    RETURN ar.doi as doi, ar.title as title, ar.abstract as abstract, 
    ar.publication_date as publicationDate,
    collect(distinct({scopusId: au.scopus_id, name: au.auth_name})) as authors, 
    collect(distinct(af.name)) as affiliations, 
    collect(distinct(to.name)) as topics
    """
    res = getDB().run(query).data()

    if len(res) > 0:
        return res[0]


def getCoauthorsById(id):

    query = """
    match (au:Author {scopus_id:'""" + id + """'})-[r1:CO_AUTHORED]-(coAu:Author)
    return collect(distinct({scopusId: coAu.scopus_id, initials: coAu.initials, 
    firstName: coAu.first_name, lastName: coAu.last_name})) as nodes
    """

    res = getDB().run(query).data()

    nodes = res[0]['nodes']

    if len(nodes) > 0:
        query = """
        match (au:Author {scopus_id:'""" + id + """'})-[r1:CO_AUTHORED]-(coAu:Author)
        return (collect(distinct({source: au.scopus_id, target: coAu.scopus_id,
        collabStrength: toFloat(r1.collab_strength)}))) as links
        """

        res = getDB().run(query).data()

        links = res[0]['links']

        query = """
        match (au:Author {scopus_id:'""" + id + """'})-[r1:CO_AUTHORED]-(coAu:Author)-[r2:CO_AUTHORED]-(coCoAu:Author)
        match (au:Author {scopus_id:'""" + id + """'})-[:CO_AUTHORED]-(coCoAu:Author)
        where coAu.scopus_id > coCoAu.scopus_id
        return collect(distinct({source: coAu.scopus_id,target: coCoAu.scopus_id, 
        collabStrength: toFloat(r2.collab_strength)})) as links
        """

        res = getDB().run(query).data()

        links = links + res[0]['links']

        return {"nodes": nodes, "links": links}

    else:
        links = []

    return {"nodes": nodes, "links": links}


def getCommunity(authList):

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authList) + """] as authList
    match (au:Author)
    where au.scopus_id in authList
    return collect({scopusId: au.scopus_id, initials: au.initials, 
    firstName: au.first_name, lastName: au.last_name})  as nodes
    """

    res = getDB().run(query).data()

    nodes = res[0]['nodes']

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authList) + """] as authList
    match (au1:Author)-[r:CO_AUTHORED]-(au2:Author)
    where au1.scopus_id in authList AND au2.scopus_id in authList AND au1>au2
    return collect({source: au1.scopus_id, target: au2.scopus_id, 
    collabStrength: r.collab_strength}) as links
    """

    res = getDB().run(query).data()

    links = res[0]['links']

    return {"nodes": nodes, "links": links, "sizeNodes": len(nodes), "sizeLinks": len(links)}


def getAffiliationsByAuthors(authList):

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authList) + """] as authList
    match (au:Author)-[:AFFILIATED_WITH]-(aff:Affiliation)
    where au.scopus_id in authList
    return collect(distinct({scopusId: aff.scopus_id, name: aff.name})) as affiliations
    """

    res = getDB().run(query).data()

    return res[0]['affiliations']


def getAuthorsByAffiliationFilters(filterType, affiliations, authors):

    filterType = '' if filterType == 'include' else 'not'

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authors) + """] as authList,
    [""" + ', '.join(f'"{w}"' for w in affiliations) + """] as affList
    match (au:Author)-[:AFFILIATED_WITH]-(aff:Affiliation)
    where au.scopus_id in authList and """ + filterType + """ aff.scopus_id in affList
    return collect(distinct(au.scopus_id)) as authors
    """

    res = getDB().run(query).data()

    return res[0]['authors']


def getArticlesByIds(articlesList, page, size):

    query = """
    with [""" + ', '.join(f'"{w}"' for w in articlesList) + """] as articles
    match (ar:Article)
    where ar.scopus_id in articles
    optional match (ar)-[:WROTE]-(au:Author)
    with ar, collect(DISTINCT(au.auth_name)) as authors
    return ar.scopus_id as scopusId, ar.title as title,
    authors, ar.publication_date as publicationDate
    SKIP """+str((page-1)*size)+""" LIMIT """+str(size)+"""
    """

    res = getDB().run(query)

    articles = []
    for item in res:
        article = {}
        article['scopusId'] = item.data()['scopusId']
        article['title'] = item.data()['title']
        article['authors'] = item.data()['authors']
        article['publicationDate'] = item.data()['publicationDate']
        articles.append(article)

    return {'total': len(articlesList), 'data': articles}


def getYearsByArticles(articlesList):
    query = """
    with [""" + ', '.join(f'"{w}"' for w in articlesList) + """] as articles
    match (ar:Article) where ar.scopus_id in articles
    with distinct(date(ar.publication_date).year) as years
    return years order by years desc
    """

    res = getDB().run(query)

    years = []
    for item in res:
        years.append(item.data()['years'])

    return years


def getArticlesByFilterYears(filterType, years, articles):
    filterType = '' if filterType == 'include' else 'not'

    query = """
    with [""" + ', '.join(f'"{w}"' for w in articles) + """] as articlesList,
    [""" + ', '.join(f'{w}' for w in years) + """] as yearsList
    match (ar:Article) 
    where ar.scopus_id in articlesList and """ + filterType + """ date(ar.publication_date).year in yearsList
    return collect(ar.scopus_id) as articles
    """
    res = getDB().run(query).data()

    return res[0]['articles']


def getMostRelevantAuthorByTopic(topic, size):
    m = Model("author")
    return m.getMostRelevantDocsByTopic(topic, size)


def getMostRelevantArticlesByTopic(topic):
    m = Model('article')
    return m.getMostRelevantDocsByTopic(topic, None)


def getCommunity(authList):

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authList) + """] as authList
    match (au:Author)
    where au.scopus_id in authList
    return collect({scopusId: au.scopus_id, initials: au.initials, 
    firstName: au.first_name, lastName: au.last_name})  as nodes
    """

    res = getDB().run(query).data()

    nodes = res[0]['nodes']

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authList) + """] as authList
    match (au1:Author)-[r:CO_AUTHORED]-(au2:Author)
    where au1.scopus_id in authList AND au2.scopus_id in authList AND au1>au2
    return collect({source: au1.scopus_id, target: au2.scopus_id, 
    collabStrength: r.collab_strength}) as links
    """

    res = getDB().run(query).data()

    links = res[0]['links']

    return {"nodes": nodes, "links": links, "sizeNodes": len(nodes), "sizeLinks": len(links)}


def getAffiliationsByAuthors(authList):

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authList) + """] as authList
    match (au:Author)-[:AFFILIATED_WITH]-(aff:Affiliation)
    where au.scopus_id in authList
    return collect(distinct({scopusId: aff.scopus_id, name: aff.name})) as affiliations
    """

    res = getDB().run(query).data()

    return res[0]['affiliations']


def getAuthorsByAffiliationFilters(filterType, affiliations, authors):

    filterType = '' if filterType == 'include' else 'not'

    query = """
    with [""" + ', '.join(f'"{w}"' for w in authors) + """] as authList,
    [""" + ', '.join(f'"{w}"' for w in affiliations) + """] as affList
    match (au:Author)-[:AFFILIATED_WITH]-(aff:Affiliation)
    where au.scopus_id in authList and """ + filterType + """ aff.scopus_id in affList
    return collect(distinct(au.scopus_id)) as authors
    """

    res = getDB().run(query).data()

    return res[0]['authors']


def getArticlesByIds(articlesList, page, size):

    query = """
    with [""" + ', '.join(f'"{w}"' for w in articlesList) + """] as articles
    match (ar:Article)
    where ar.scopus_id in articles
    optional match (ar)-[:WROTE]-(au:Author)
    with ar, collect(DISTINCT(au.auth_name)) as authors
    return ar.scopus_id as scopusId, ar.title as title,
    authors, ar.publication_date as publicationDate
    SKIP """+str((page-1)*size)+""" LIMIT """+str(size)+"""
    """

    res = getDB().run(query)

    articles = []
    for item in res:
        article = {}
        article['scopusId'] = item.data()['scopusId']
        article['title'] = item.data()['title']
        article['authors'] = item.data()['authors']
        article['publicationDate'] = item.data()['publicationDate']
        articles.append(article)

    return {'total': len(articlesList), 'data': articles}


def getYearsByArticles(articlesList):
    query = """
    with [""" + ', '.join(f'"{w}"' for w in articlesList) + """] as articles
    match (ar:Article) where ar.scopus_id in articles
    with distinct(date(ar.publication_date).year) as years
    return years order by years desc
    """

    res = getDB().run(query)

    years = []
    for item in res:
        years.append(item.data()['years'])

    return years


def getArticlesByFilterYears(filterType, years, articles):
    filterType = '' if filterType == 'include' else 'not'

    print(', '.join(f'{w}' for w in years))
    print(', '.join(f'"{w}"' for w in articles))
    query = """
    with [""" + ', '.join(f'"{w}"' for w in articles) + """] as articlesList,
    [""" + ', '.join(f'{w}' for w in years) + """] as yearsList
    match (ar:Article) 
    where ar.scopus_id in articlesList and """ + filterType + """ date(ar.publication_date).year in yearsList
    return collect(ar.scopus_id) as articles
    """
    res = getDB().run(query).data()

    print(res[0]['articles'])
    return res[0]['articles']


def getMostRelevantAuthorByTopic(topic, size):
    m = Model("author")
    return m.getMostRelevantDocsByTopic(topic, size)


def getMostRelevantArticlesByTopic(topic):
    m = Model('article')
    return m.getMostRelevantDocsByTopic(topic, None)


def getRandomAuthors():

    query = """
    MATCH (au:Author)-[r:CO_AUTHORED]-(coAu:Author) 
    WITH au, COUNT(r) as size
    ORDER BY RAND()
    WHERE size >= 90
    RETURN au.auth_name as value, size 
    SKIP 0 LIMIT 7
    """

    res = getDB().run(query).data()

    items = []
    for item in res:
        items.append(item)
        
    return items

def getRandomTopics():

    query = """
    MATCH (topics)-[r:USES]-(ar:Article)
    WITH topics, count(r) as size 
    ORDER BY RAND()
    WHERE size >= 60
    return topics.name as value, size
    LIMIT 10
    """

    res = getDB().run(query).data()

    items = []
    for item in res:
        items.append(item)
        
    return items

