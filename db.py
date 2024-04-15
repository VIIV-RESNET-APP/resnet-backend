from neo4j import GraphDatabase
from tfidf import Model
import config
from unidecode import unidecode


class Neo4jService:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            f"bolt://{config.DATABASE_HOST}:7687",
            auth=(config.DATABASE_USER, config.DATABASE_PASSWORD),
        )

    @staticmethod
    def _execute_query(tx, query):
        result = tx.run(query)
        return result.data()

    def getAuthorsByQuery(self, name: str, page, size):

        name = unidecode(name).strip().lower()

        query = f"""
            MATCH (au:Author) 
            WHERE  toLower(au.first_name) CONTAINS '{name}' or 
                toLower(au.last_name) CONTAINS '{name}' or 
                toLower(au.first_name) + " " + toLower(au.last_name) CONTAINS '{name}' or
                toLower(au.last_name) + " " + toLower(au.first_name) CONTAINS '{name}' or  
                toLower(au.auth_name) CONTAINS '{name}' or 
                toLower(au.initials) CONTAINS '{name}' or 
                toLower(au.email) CONTAINS '{name}'or 
                au.scopus_id CONTAINS '{name}'
            RETURN count(au) as total
            """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        total = result[0]['total']

        query = f"""
            MATCH (au:Author) 
            WHERE  toLower(au.first_name) CONTAINS '{name}' or 
                toLower(au.last_name) CONTAINS '{name}' or 
                toLower(au.first_name) + " " + toLower(au.last_name) CONTAINS '{name}' or
                toLower(au.last_name) + " " + toLower(au.first_name) CONTAINS '{name}' or  
                toLower(au.auth_name) CONTAINS '{name}' or 
                toLower(au.initials) CONTAINS '{name}' or 
                toLower(au.email) CONTAINS '{name}'or 
                au.scopus_id CONTAINS '{name}'
            OPTIONAL MATCH (aff:Affiliation)-[:AFFILIATED_WITH]-(au)
            OPTIONAL MATCH (au)-[:WROTE]-(ar:Article)
            OPTIONAL MATCH (ar:Article)-[:USES]-(to:Topic)
            
            
            WITH au, ar, aff, to
            ORDER BY au.first_name ASC, au.last_name ASC
            
            RETURN au.scopus_id as scopusId, 
                [au.first_name + " " + au.last_name, au.auth_name, au.initials] as names, 
                collect(DISTINCT aff.name) as affiliations, 
                au.num_articles as articles, 
                collect(DISTINCT to.name) as topics,
                au.role as role
            SKIP {(page - 1) * size} LIMIT {size}
            """
        # count(DISTINCT ar) as articles,
        with self._driver.session() as session:
            authors = session.read_transaction(self._execute_query, query)
        if authors:
            query = f"""
                MATCH (au:Author) 
                WHERE  toLower(au.first_name) CONTAINS '{name}' or 
                    toLower(au.last_name) CONTAINS '{name}' or 
                    toLower(au.first_name) + " " + toLower(au.last_name) CONTAINS '{name}' or
                    toLower(au.last_name) + " " + toLower(au.first_name) CONTAINS '{name}' or  
                    toLower(au.auth_name) CONTAINS '{name}' or 
                    toLower(au.initials) CONTAINS '{name}' or 
                    toLower(au.email) CONTAINS '{name}'or 
                    au.scopus_id CONTAINS '{name}'
                OPTIONAL MATCH (au)-[:WROTE]-(ar:Article)-[:USES]-(to:Topic)
                WITH au, to, count(to.name) as frequency, collect(DISTINCT to.name) as cTopics 
                ORDER BY au.first_name ASC, au.last_name ASC, frequency DESC
                UNWIND cTopics as uTopics 
                RETURN au.scopus_id as scopusId, collect(DISTINCT uTopics) as topics
                SKIP {(page - 1) * size} LIMIT {size}
                """

            with self._driver.session() as session:
                additional_topics = session.read_transaction(self._execute_query, query)

            for item in additional_topics:
                authorIndex = next((index for (index, d) in enumerate(authors) if d["scopusId"] == item['scopusId']),
                                   None)
                if authorIndex is not None:
                    authors[authorIndex]['topics'] = item['topics']

        return {'total': total, 'data': authors}

    def getAuthorById(self, id):
        # Consulta para obtener la información del autor
        query_author_info = f"""
        MATCH (au:Author {{scopus_id: '{id}'}})
        OPTIONAL MATCH (au)-[:AFFILIATED_WITH]-(af:Affiliation)
        OPTIONAL MATCH (au)-[:WROTE]-(ar:Article)
        RETURN au.scopus_id as scopusId, au.first_name as firstName, 
            au.last_name as lastName, au.auth_name as authName, au.initials as initials, au.email as email, au.rol as rol, 
            collect(DISTINCT af.name) as affiliations, 
            collect(DISTINCT {{scopusId: ar.scopus_id, title: ar.title}}) as articles
        """

        with self._driver.session() as session:
            result_author_info = session.read_transaction(self._execute_query, query_author_info)

        if not result_author_info:
            return None

        author = result_author_info[0]

        # Consulta para obtener los temas relacionados al autor
        query_author_topics = f"""
        MATCH (au:Author {{scopus_id: '{id}'}})-[:WROTE]-(ar:Article)-[:USES]-(to:Topic)
        WITH to, COUNT(to.name) as frequency
        RETURN to.name as name ORDER BY frequency DESC
        """

        with self._driver.session() as session:
            result_author_topics = session.read_transaction(self._execute_query, query_author_topics)

        topics = [item['name'] for item in result_author_topics]

        author['topics'] = topics

        return author

    def getArticleById(self, id):
        query = f"""
        MATCH (ar:Article {{scopus_id: '{id}'}})
        OPTIONAL MATCH (ar)-[:WROTE]-(au:Author)
        OPTIONAL MATCH (ar)-[:BELONGS_TO]-(af:Affiliation)
        OPTIONAL MATCH (ar)-[:USES]-(to:Topic)
        RETURN ar.doi as doi, ar.title as title, ar.abstract as abstract, 
            ar.publication_date as publicationDate,
            collect(DISTINCT {{scopusId: au.scopus_id, name: au.auth_name}}) as authors, 
            collect(DISTINCT af.name) as affiliations, 
            collect(DISTINCT to.name) as topics
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        if result:
            return result[0]
        else:
            return None

    def getCoauthorsById(self, id):
        query = f"""
        MATCH (au:Author {{scopus_id: '{id}'}})-[r1:CO_AUTHORED]-(coAu:Author)
        RETURN collect(DISTINCT {{scopusId: coAu.scopus_id, initials: coAu.initials, 
            firstName: coAu.first_name, lastName: coAu.last_name}}) as nodes
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        nodes = result[0]['nodes']

        if nodes:
            query = f"""
            MATCH (au:Author {{scopus_id: '{id}'}})-[r1:CO_AUTHORED]-(coAu:Author)
            RETURN (collect(DISTINCT {{source: au.scopus_id, target: coAu.scopus_id,
                collabStrength: toFloat(r1.collab_strength)}})) as links
            """

            with self._driver.session() as session:
                result = session.read_transaction(self._execute_query, query)

            links = result[0]['links']

            query = f"""
            MATCH (au:Author {{scopus_id: '{id}'}})-[r1:CO_AUTHORED]-(coAu:Author)-[r2:CO_AUTHORED]-(coCoAu:Author)
            MATCH (au:Author {{scopus_id: '{id}'}})-[:CO_AUTHORED]-(coCoAu:Author)
            WHERE coAu.scopus_id > coCoAu.scopus_id
            RETURN collect(DISTINCT {{source: coAu.scopus_id, target: coCoAu.scopus_id, 
                collabStrength: toFloat(r2.collab_strength)}}) as links
            """

            with self._driver.session() as session:
                result = session.read_transaction(self._execute_query, query)

            links = links + result[0]['links']

            return {"nodes": nodes, "links": links}
        else:
            links = []

        return {"nodes": nodes, "links": links}

    def getCommunity(self, authList):
        auth_list_str = ', '.join([f'"{w}"' for w in authList])

        # Consulta para obtener nodos
        query_nodes = f"""
        WITH [{auth_list_str}] as authList
        MATCH (au:Author)
        WHERE au.scopus_id IN authList
        RETURN collect({{scopusId: au.scopus_id, initials: au.initials, rol: au.rol, 
            firstName: au.first_name, lastName: au.last_name}}) as nodes
        """

        with self._driver.session() as session:
            result_nodes = session.read_transaction(self._execute_query, query_nodes)

        nodes = result_nodes[0]['nodes']

        # Consulta para obtener enlaces
        query_links = f"""
        WITH [{auth_list_str}] as authList
        MATCH (au1:Author)-[r:CO_AUTHORED]-(au2:Author)
        WHERE au1.scopus_id IN authList AND au2.scopus_id IN authList AND au1 > au2
        RETURN collect({{source: au1.scopus_id, target: au2.scopus_id, 
            collabStrength: toFloat(r.collab_strength)}}) as links
        """

        with self._driver.session() as session:
            result_links = session.read_transaction(self._execute_query, query_links)

        links = result_links[0]['links']

        return {"nodes": nodes, "links": links, "sizeNodes": len(nodes), "sizeLinks": len(links)}

    def getAffiliationsByAuthors(self, authList):
        auth_list_str = ', '.join([f'"{w}"' for w in authList])

        # Consulta para obtener afiliaciones
        query = f"""
        WITH [{auth_list_str}] as authList
        MATCH (au:Author)-[:AFFILIATED_WITH]-(aff:Affiliation)
        WHERE au.scopus_id IN authList
        RETURN collect(DISTINCT {{scopusId: aff.scopus_id, name: aff.name}}) as affiliations
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        return result[0]['affiliations']

    def getAuthorsByAffiliationFilters(self, filterType, affiliations, authors):
        filterType = '' if filterType == 'include' else 'not'

        auth_list_str = ', '.join([f'"{w}"' for w in authors])
        aff_list_str = ', '.join([f'"{w}"' for w in affiliations])

        # Consulta para obtener autores
        query = f"""
        WITH [{auth_list_str}] as authList,
            [{aff_list_str}] as affList
        MATCH (au:Author)-[:AFFILIATED_WITH]-(aff:Affiliation)
        WHERE au.scopus_id IN authList AND {filterType} aff.scopus_id IN affList
        RETURN collect(DISTINCT au.scopus_id) as authors
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        return result[0]['authors']

    def getArticlesByIds(self, articlesList, page, size):
        articles_list_str = ', '.join([f'"{w}"' for w in articlesList])

        # Consulta para obtener artículos
        query = f"""
        WITH [{articles_list_str}] as articles
        MATCH (ar:Article)
        WHERE ar.scopus_id IN articles
        OPTIONAL MATCH (ar)-[:WROTE]-(au:Author)
        WITH ar, collect(DISTINCT au.auth_name) as authors
        RETURN ar.scopus_id as scopusId, ar.title as title,
            authors, ar.publication_date as publicationDate
        SKIP {str((page - 1) * size)} LIMIT {str(size)}
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        articles = []
        for item in result:
            article = {
                'scopusId': item['scopusId'],
                'title': item['title'],
                'authors': item['authors'],
                'publicationDate': item['publicationDate']
            }
            articles.append(article)

        return {'total': len(articlesList), 'data': articles}

    def getYearsByArticles(self, articlesList):
        articles_list_str = ', '.join([f'"{w}"' for w in articlesList])

        # Consulta para obtener años
        query = f"""
        WITH [{articles_list_str}] as articles
        MATCH (ar:Article) WHERE ar.scopus_id IN articles
        WITH DISTINCT date(ar.publication_date).year as years
        RETURN COLLECT(years) as years ORDER BY years DESC
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        years = result[0]['years']

        return years

    def getArticlesByFilterYears(self, filterType, years, articles):
        filterType = '' if filterType == 'include' else 'not'

        articles_list_str = ', '.join([f'"{w}"' for w in articles])
        years_list_str = ', '.join([str(w) for w in years])

        # Consulta para obtener artículos
        query = f"""
        WITH [{articles_list_str}] as articlesList,
            [{years_list_str}] as yearsList
        MATCH (ar:Article) 
        WHERE ar.scopus_id IN articlesList AND {filterType} date(ar.publication_date).year IN yearsList
        RETURN collect(ar.scopus_id) as articles
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        return result[0]['articles']

    def getMostRelevantAuthorByTopic(self, topic, size):
        m = Model("author")
        return m.getMostRelevantDocsByTopic(topic, size)

    def getMostRelevantArticlesByTopic(self, topic):
        m = Model('article')
        return m.getMostRelevantDocsByTopic(topic, None)

    def getRandomAuthors(self):
        # Consulta para obtener autores aleatorios
        query = """
        MATCH (au:Author)-[r:CO_AUTHORED]-(coAu:Author) 
        WITH au, COUNT(r) as size
        WHERE size >= 90
        WITH au, size, rand() as random
        ORDER BY random
        RETURN au.auth_name as value, size
        SKIP 0 LIMIT 10
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        return result

    def getRandomTopics(self):
        # Consulta para obtener temas aleatorios
        query = """
        MATCH (topics)-[r:USES]-(ar:Article)
        WITH topics, COUNT(r) as size 
        WHERE size >= 60
        WITH topics, size, rand() as random
        ORDER BY random
        RETURN topics.name as value, size
        LIMIT 10
        """

        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)

        items = result

        return items

    def updateAuthorField(self, id, field_name, new_value):
        query_update_author_field = f"""
        MATCH (au:Author {{scopus_id: '{id}'}})
        SET au.{field_name} = '{new_value}'
        RETURN au
        """

        with self._driver.session() as session:
            result = session.write_transaction(self._execute_query, query_update_author_field)

        return result

    def get_all_scopus_ids(self):
        query = """
        MATCH (au:Author)
        RETURN au.scopus_id as scopusId
        """
        with self._driver.session() as session:
            result = session.read_transaction(self._execute_query, query)
        return result
