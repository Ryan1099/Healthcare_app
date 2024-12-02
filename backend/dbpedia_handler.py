from SPARQLWrapper import SPARQLWrapper, JSON
import time


def query_dbpedia(sparql, query, query_type="generic"):
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    for attempt in range(3):
        try:
            results = sparql.query().convert()["results"]["bindings"]
            return results
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {query_type} query: {e}")
            time.sleep(1)  # Add a small delay between retry attempts

    raise Exception(f"Failed to execute {query_type} query after 3 attempts")


def get_all_symptoms():
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = """
        SELECT DISTINCT ?symptom ?label
        WHERE {
            ?disease dbo:symptom ?symptom.
            ?symptom rdfs:label ?label.
            filter langMatches(lang(?label), "en")
        }
    """

    try:
        results = query_dbpedia(sparql, query, "all symptoms")
        label_resource_dict = {
            x["label"]["value"]: x["symptom"]["value"]
            for x in results}
        return {k: v for k, v in sorted(label_resource_dict.items(), key=lambda x: x[1])}
    except Exception as e:
        print(f"Error retrieving symptoms: {e}")
        return {}


def get_all_possible_symptoms(input_symptoms):
    """
    This function takes a list of symptoms as input.
    If the input list is empty, it returns all symptoms.
    Otherwise, it searches for diseases containing all the input symptoms
    and returns all symptoms of the remaining diseases, excluding the input symptoms.
    """
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")

    if not input_symptoms:  # Check if the input list is empty
        query = """
            SELECT DISTINCT ?symptom ?label
            WHERE {
                ?disease dbo:symptom ?symptom.
                ?symptom rdfs:label ?label.
                FILTER (langMatches(lang(?label), "en"))
            }
        """
    else:
        # SPARQL query to find diseases that contain all input symptoms
        query = f"""
            SELECT DISTINCT ?symptom ?label
            WHERE {{
                # Identify diseases that have all the provided symptoms
                {{
                    SELECT DISTINCT ?disease
                    WHERE {{
                        ?disease dbo:symptom ?inputSymptom.
                        VALUES ?inputSymptom {{
                            {" ".join(f"<{symptom}>" for symptom in input_symptoms)}
                        }}
                    }}
                    GROUP BY ?disease
                    HAVING (COUNT(?inputSymptom) = {len(input_symptoms)})
                }}

                # Retrieve all symptoms of the filtered diseases
                ?disease dbo:symptom ?symptom.
                ?symptom rdfs:label ?label.
                FILTER (langMatches(lang(?label), "en"))
            }}
        """

    try:
        results = query_dbpedia(sparql, query, "possible symptoms")

        # Create a dictionary of symptoms excluding the input symptoms
        symptom_dict = {x["label"]["value"]: x["symptom"]["value"]
                        for x in results}

        # Exclude input symptoms from the result
        if input_symptoms:
            symptom_dict = {k: v for k, v in symptom_dict.items() if k not in input_symptoms}

        return symptom_dict
    except Exception as e:
        print(f"Error retrieving possible symptoms: {e}")
        return {}


def get_diseases_by_symptoms(symptom_list):
    symptom_triples = "\n".join([f"?disease dbo:symptom+ <{x}>." for x in symptom_list])

    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = f"""
        SELECT DISTINCT ?disease ?label
        WHERE {{
            {symptom_triples}
            ?disease rdfs:label ?label.
            filter langMatches(lang(?label), "en")
        }}
    """

    try:
        results = query_dbpedia(sparql, query, "diseases by symptoms")
        label_resource_dict = {x["label"]["value"]: x["disease"]["value"] for x in results}
        return {k: v for k, v in sorted(label_resource_dict.items(), key=lambda x: x[1])}
    except Exception as e:
        print(f"Error retrieving diseases by symptoms: {e}")
        return {}


def get_symptoms_of_disease(disease_uri, symptom_label_list, no_symptom_label_list):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = f"""
        SELECT DISTINCT ?symptom ?label
        WHERE {{
            <{disease_uri}> dbo:symptom+ ?symptom.
            ?symptom rdfs:label ?label.
            filter langMatches(lang(?label), "en")
        }}
    """

    try:
        results = query_dbpedia(sparql, query, "symptoms of disease")
        label_resource_dict = {
            x["label"]["value"]: x["symptom"]["value"]
            for x in results}
        return {k: v for k, v in sorted(label_resource_dict.items(), key=lambda x: x[1]) if
                k not in symptom_label_list + no_symptom_label_list}
    except Exception as e:
        print(f"Error retrieving symptoms of disease: {e}")
        return {}


def get_medline_id_of_disease(disease_uri):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = f"""
        SELECT ?medlineId
        WHERE {{
            <{disease_uri}> dbo:medlinePlus ?medlineId.
        }}
    """

    try:
        results = query_dbpedia(sparql, query, "medline ID")
        return results[0]["medlineId"]["value"] if results else None
    except Exception as e:
        print(f"Error retrieving Medline ID: {e}")
        return None


def get_wikiPageID_of_disease(disease_uri):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    query = f"""
        SELECT ?wikiPageID
        WHERE {{
            <{disease_uri}> dbo:wikiPageID ?wikiPageID.
        }}
    """

    try:
        results = query_dbpedia(sparql, query, "wiki page ID")
        return int(results[0]["wikiPageID"]["value"]) if results else None
    except Exception as e:
        print(f"Error retrieving Wiki Page ID: {e}")
        return None


if __name__ == "__main__":
    symptom_dict = get_all_symptoms()
    symptom_list = [symptom_dict["Fever"], symptom_dict["Fatigue"]]
    disease_dict = get_diseases_by_symptoms(symptom_list)
    print("Done")