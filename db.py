from py2neo import Graph
from tfidf import Model

def getDB():
    return Graph("bolt://18.224.32.50:7687", auth=("neo4j", "narias98"))

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
    RETURN ar.title as title, ar.abstract as abstract, ar.publication_date as publicationDate,
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


def getCoauthoList():
    return ["56586156800", "56100321400", "57220861039", "57197859208", "27169241100", "56565073100", "57409561300", "16643844400", "57164304900", "24074299200", "57201298392", "57221675857", "57530325700", "57199325314", "57207833319", "57219088349", "57129931400", "53986216300", "57191279128", "36176985200", "55151526400", "57203341772", "37072764100", "57207767724", "55601621800", "57218121593", "57219326252", "36843394100", "57203482833", "7006323466", "57226630860", "56313035200", "24573438500", "55251352200", "6506037991", "54391675100", "57044064900", "57218580675", "56868597700", "25228069800", "57210194751", "57393389200", "7005323427", "56942230300", "55620245800", "57204392587", "6507825232", "57197858331", "26027643100", "6603937596", "36242059300", "57216628384", "56966750300", "57218414270", "15741703700", "16304577200", "57192198105", "55326145300", "55100465200", "6505482977", "57200228538", "8411951300", "57216927571", "57282297600", "6603708617", "57190295493", "7004890176", "57226652602", "6506845058", "57204904539", "57214314212", "36155389400", "6603839864", "36982889800", "35072751100", "57191525873", "57209213643", "57200124960", "57200741801", "7402319036", "7202132648", "15135088100", "57212733625", "57429919700", "12785309600", "54409578400", "57194944802", "57193324487", "56574275200", "57198502862", "57253475700", "57215434676", "57204410267", "36992446600", "56521513800", "57205221247", "56672934400", "36933891300", "57226660903", "35215080300", "57193847621", "57195724493", "57219141395", "57219143527", "57609617500", "57193097232", "57219804473", "35998528900", "6507051570", "57218369337", "57759370700", "56755417400", "56109253800", "57203582439", "55241803600", "57376185200", "56805263600", "26647168500", "57438634600", "57223283201", "56058857700", "57226634855", "57211663311", "57189660380", "57427072500", "57217661678", "57211354935", "8509701900", "57196326678", "57111846500", "57193029630", "57211992800", "57221923040", "57207686788", "56243004700", "55884900500", "55973684200", "57198128905", "57202277592", "24587024000", "57214116301", "6602943383", "55241787700", "57219747121", "16407030800", "37009670400", "6603850178", "57193321309", "57200800572", "6505692279", "57329353900", "35502919500", "11241724100", "25925337100", "57164579400", "57194547528", "56069580100", "57355912300", "57538394400", "57195607314", "57193028430", "28567495300", "57211646991", "6507197871", "57193322181", "55325149700", "14019356600", "55241705000", "57193497695", "57217632449", "57201727198", "57195128044", "57226088374", "57197165974", "55889841600", "27568125300", "6506931095", "57221678763", "56335294600", "57191344655", "57221679352", "56989953200", "57192974770", "57191526119", "56000584100", "57220104472", "56340568400", "36983083000", "25623972200", "6603885391", "57197723171", "57204429245", "56281965400", "57205219088", "6507359524", "57226632355", "57211320390", "57044868100", "55249622500", "55305484700", "57207692821", "55646259800", "57214480217", "7003861861", "57209686809", "57221676051", "36705961100", "18040542200", "57408357100", "57217985242", "57203485303", "53984207200", "57194137124", "54879365900", "15754951300", "57221792694", "57226643927", "28567636800", "7006690970", "57201069599", "57191824485", "57204908517", "57192198705", "57203881629", "57193669183", "57197799939", "57219776386", "56089474000", "14035636600", "57221671680", "57193845161", "56921726400", "57219804159", "57207766167", "57218369546", "57192250871", "57191968061", "55613972200", "13006316400", "55175583400", "57440063600", "57203589114", "56394604900", "57219238644", "56369203800", "8574680100", "57195603925", "27267729600", "40761299900", "43160971100", "57207597201", "55305709200", "57195604726", "56717497000", "55541000100", "57219164869", "57212348128", "57195127196", "6503878914", "55960919800", "57193915411", "57204022882", "57044582000", "57217735242", "57221670824", "57195469442", "8581993600", "22333478300", "57219241595", "55242119400", "57193846214", "57213103723", "7101843237", "57201717835", "57200582283", "51963759900", "56018847700", "14038038900", "6504789088", "57202190671", "6602118668", "57200230204", "57192186254", "56345819600", "57219052646", "57188581743", "57191926377", "57222362492", "28367582700", "6506915029", "56575131300", "36983294200", "57205664444", "37031088600", "55206188000", "6505991046", "56134917000", "57211567110", "36454763800", "57299026200", "57205219617", "56481668900", "57210757331", "36561793100", "55786570900", "57210191951", "36344605800", "55360745200", "57391736200", "57564598400", "57192213434", "26533780200", "55363634900", "55530699700", "57764491800", "57224545422", "57204236282", "57218119458", "55981383500", "57189510053", "57211566730", "57223288094", "57191342337", "57203081696", "57211030699", "55848966500", "36897189200", "36899691400", "57199373824", "55808536900", "57384168400", "57223105913", "36019842500", "6504567347", "57195133965", "57657344400", "57739168400", "57222431340", "57191756685", "55507886700", "57209886499", "57205395330", "57217927265", "57409043200", "56084401300", "57217633286", "15830542300", "57208817821", "8892520800", "57534646000", "35617220000", "57208507170", "57369986400", "57220033824", "57225240631", "56693978700", "34868240000", "57194458733", "57221093124", "57220750051", "14035477300", "57208028409", "57204433753", "15832372700", "57219778521", "57195761190", "56584657000", "57226424506", "57201953494", "57223281864", "8875724800", "57225431746", "57205362923", "57445104100", "8263547400", "55956682700", "8580309500", "7401505218", "56313050800", "6602832639", "57208102955", "6602629287", "57218367835", "57646119700", "35367370400", "7102016921", "23009641700", "25623528100", "57202442085", "57442593800", "57219098961", "57191480779", "57208112459", "36996946900", "22833954600", "12645534600", "57209748169", "57222979678", "57193003974", "36970586200", "9640137200", "57216892219", "57482438200", "57221673585", "57223291387", "54917356300", "57212305908", "43160925400", "57222015783", "57205221564", "57195148411", "57214235334", "25959574700", "57195153837", "57195557532", "57195718017", "57222984321", "57223606431", "57204465253", "57413543100", "57193311501", "57195132383", "57204014981", "57216893637", "6508053748", "57381195300", "56462342200", "24768290700", "57212810470", "57223682746", "57190987335", "57204922674", "49661227500", "56521745300", "57211339418", "57223309073", "56845813600", "57194080051", "57214856086", "57194589424", "57191429458", "56676321800", "57188970527", "57193196927", "57215528510", "26029946900", "57220613397", "24464802600", "57363299400", "57056430400", "7202626586", "57441716600", "56208905400", "55856706700", "7801529331", "12791687700", "57223986997", "57226472683", "57193948570", "57219800679", "56721348000", "56866280200", "56177258800", "57195721974", "15750057900", "55799217600", "56575169100", "57191490204", "57352361300", "57382870400", "55241803900", "57215316518", "57195609721", "6507641960", "57240324800", "57610431200", "57223310073", "57222621367", "57195458378", "6603199979", "57206902062", "57751576900", "43160907600", "57749876300", "57205221256", "57226065919", "57226312799", "56087730600", "57211969301", "57210189241", "57201442698", "57561779800", "35338804600", "35742842700", "57384172200", "57207253725", "57189690950", "6603035688", "7006339730", "57723056500"]

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


def getCoauthoList():
    return ["56586156800", "56100321400", "57220861039", "57197859208", "27169241100", "56565073100", "57409561300", "16643844400", "57164304900", "24074299200", "57201298392", "57221675857", "57530325700", "57199325314", "57207833319", "57219088349", "57129931400", "53986216300", "57191279128", "36176985200", "55151526400", "57203341772", "37072764100", "57207767724", "55601621800", "57218121593", "57219326252", "36843394100", "57203482833", "7006323466", "57226630860", "56313035200", "24573438500", "55251352200", "6506037991", "54391675100", "57044064900", "57218580675", "56868597700", "25228069800", "57210194751", "57393389200", "7005323427", "56942230300", "55620245800", "57204392587", "6507825232", "57197858331", "26027643100", "6603937596", "36242059300", "57216628384", "56966750300", "57218414270", "15741703700", "16304577200", "57192198105", "55326145300", "55100465200", "6505482977", "57200228538", "8411951300", "57216927571", "57282297600", "6603708617", "57190295493", "7004890176", "57226652602", "6506845058", "57204904539", "57214314212", "36155389400", "6603839864", "36982889800", "35072751100", "57191525873", "57209213643", "57200124960", "57200741801", "7402319036", "7202132648", "15135088100", "57212733625", "57429919700", "12785309600", "54409578400", "57194944802", "57193324487", "56574275200", "57198502862", "57253475700", "57215434676", "57204410267", "36992446600", "56521513800", "57205221247", "56672934400", "36933891300", "57226660903", "35215080300", "57193847621", "57195724493", "57219141395", "57219143527", "57609617500", "57193097232", "57219804473", "35998528900", "6507051570", "57218369337", "57759370700", "56755417400", "56109253800", "57203582439", "55241803600", "57376185200", "56805263600", "26647168500", "57438634600", "57223283201", "56058857700", "57226634855", "57211663311", "57189660380", "57427072500", "57217661678", "57211354935", "8509701900", "57196326678", "57111846500", "57193029630", "57211992800", "57221923040", "57207686788", "56243004700", "55884900500", "55973684200", "57198128905", "57202277592", "24587024000", "57214116301", "6602943383", "55241787700", "57219747121", "16407030800", "37009670400", "6603850178", "57193321309", "57200800572", "6505692279", "57329353900", "35502919500", "11241724100", "25925337100", "57164579400", "57194547528", "56069580100", "57355912300", "57538394400", "57195607314", "57193028430", "28567495300", "57211646991", "6507197871", "57193322181", "55325149700", "14019356600", "55241705000", "57193497695", "57217632449", "57201727198", "57195128044", "57226088374", "57197165974", "55889841600", "27568125300", "6506931095", "57221678763", "56335294600", "57191344655", "57221679352", "56989953200", "57192974770", "57191526119", "56000584100", "57220104472", "56340568400", "36983083000", "25623972200", "6603885391", "57197723171", "57204429245", "56281965400", "57205219088", "6507359524", "57226632355", "57211320390", "57044868100", "55249622500", "55305484700", "57207692821", "55646259800", "57214480217", "7003861861", "57209686809", "57221676051", "36705961100", "18040542200", "57408357100", "57217985242", "57203485303", "53984207200", "57194137124", "54879365900", "15754951300", "57221792694", "57226643927", "28567636800", "7006690970", "57201069599", "57191824485", "57204908517", "57192198705", "57203881629", "57193669183", "57197799939", "57219776386", "56089474000", "14035636600", "57221671680", "57193845161", "56921726400", "57219804159", "57207766167", "57218369546", "57192250871", "57191968061", "55613972200", "13006316400", "55175583400", "57440063600", "57203589114", "56394604900", "57219238644", "56369203800", "8574680100", "57195603925", "27267729600", "40761299900", "43160971100", "57207597201", "55305709200", "57195604726", "56717497000", "55541000100", "57219164869", "57212348128", "57195127196", "6503878914", "55960919800", "57193915411", "57204022882", "57044582000", "57217735242", "57221670824", "57195469442", "8581993600", "22333478300", "57219241595", "55242119400", "57193846214", "57213103723", "7101843237", "57201717835", "57200582283", "51963759900", "56018847700", "14038038900", "6504789088", "57202190671", "6602118668", "57200230204", "57192186254", "56345819600", "57219052646", "57188581743", "57191926377", "57222362492", "28367582700", "6506915029", "56575131300", "36983294200", "57205664444", "37031088600", "55206188000", "6505991046", "56134917000", "57211567110", "36454763800", "57299026200", "57205219617", "56481668900", "57210757331", "36561793100", "55786570900", "57210191951", "36344605800", "55360745200", "57391736200", "57564598400", "57192213434", "26533780200", "55363634900", "55530699700", "57764491800", "57224545422", "57204236282", "57218119458", "55981383500", "57189510053", "57211566730", "57223288094", "57191342337", "57203081696", "57211030699", "55848966500", "36897189200", "36899691400", "57199373824", "55808536900", "57384168400", "57223105913", "36019842500", "6504567347", "57195133965", "57657344400", "57739168400", "57222431340", "57191756685", "55507886700", "57209886499", "57205395330", "57217927265", "57409043200", "56084401300", "57217633286", "15830542300", "57208817821", "8892520800", "57534646000", "35617220000", "57208507170", "57369986400", "57220033824", "57225240631", "56693978700", "34868240000", "57194458733", "57221093124", "57220750051", "14035477300", "57208028409", "57204433753", "15832372700", "57219778521", "57195761190", "56584657000", "57226424506", "57201953494", "57223281864", "8875724800", "57225431746", "57205362923", "57445104100", "8263547400", "55956682700", "8580309500", "7401505218", "56313050800", "6602832639", "57208102955", "6602629287", "57218367835", "57646119700", "35367370400", "7102016921", "23009641700", "25623528100", "57202442085", "57442593800", "57219098961", "57191480779", "57208112459", "36996946900", "22833954600", "12645534600", "57209748169", "57222979678", "57193003974", "36970586200", "9640137200", "57216892219", "57482438200", "57221673585", "57223291387", "54917356300", "57212305908", "43160925400", "57222015783", "57205221564", "57195148411", "57214235334", "25959574700", "57195153837", "57195557532", "57195718017", "57222984321", "57223606431", "57204465253", "57413543100", "57193311501", "57195132383", "57204014981", "57216893637", "6508053748", "57381195300", "56462342200", "24768290700", "57212810470", "57223682746", "57190987335", "57204922674", "49661227500", "56521745300", "57211339418", "57223309073", "56845813600", "57194080051", "57214856086", "57194589424", "57191429458", "56676321800", "57188970527", "57193196927", "57215528510", "26029946900", "57220613397", "24464802600", "57363299400", "57056430400", "7202626586", "57441716600", "56208905400", "55856706700", "7801529331", "12791687700", "57223986997", "57226472683", "57193948570", "57219800679", "56721348000", "56866280200", "56177258800", "57195721974", "15750057900", "55799217600", "56575169100", "57191490204", "57352361300", "57382870400", "55241803900", "57215316518", "57195609721", "6507641960", "57240324800", "57610431200", "57223310073", "57222621367", "57195458378", "6603199979", "57206902062", "57751576900", "43160907600", "57749876300", "57205221256", "57226065919", "57226312799", "56087730600", "57211969301", "57210189241", "57201442698", "57561779800", "35338804600", "35742842700", "57384172200", "57207253725", "57189690950", "6603035688", "7006339730", "57723056500"]
