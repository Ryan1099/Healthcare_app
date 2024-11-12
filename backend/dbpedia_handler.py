from SPARQLWrapper import SPARQLWrapper, JSON


def get_all_symptoms():
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery("""
        SELECT DISTINCT ?symptom ?label
        WHERE {
            ?disease dbo:symptom ?symptom.
            ?symptom rdfs:label ?label.
            filter langMatches(lang(?label), "en")
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    label_resource_dict = {x["label"]["value"]: x["symptom"]["value"].replace("http://dbpedia.org/resource/", "dbr:")
                           for x in results}
    label_resource_dict = {k: v for k, v in sorted(label_resource_dict.items(), key=lambda x: x[1])}
    return label_resource_dict


def get_diseases_by_symptoms(symptom_list):
    symptom_triples = "\n".join([f"?disease dbo:symptom+ {x}." for x in symptom_list])

    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery(f"""
            SELECT DISTINCT ?disease ?label
            WHERE {{
                {symptom_triples}
                ?disease rdfs:label ?label.
                filter langMatches(lang(?label), "en")
            }}
        """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    label_resource_dict = {x["label"]["value"]: x["disease"]["value"] for x in results}
    label_resource_dict = {k: v for k, v in sorted(label_resource_dict.items(), key=lambda x: x[1])}
    return label_resource_dict


def get_symptoms_of_disease(disease_id, symptom_label_list, no_symptom_label_list):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery(f"""
            SELECT DISTINCT ?symptom ?label
            WHERE {{
                {disease_id.replace("http://dbpedia.org/resource/", "dbr:")} dbo:symptom+ ?symptom.
                ?symptom rdfs:label ?label.
                filter langMatches(lang(?label), "en")
            }}
        """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    label_resource_dict = {x["label"]["value"]: x["symptom"]["value"].replace("http://dbpedia.org/resource/", "dbr:")
                           for x in results}
    label_resource_dict = {k: v for k, v in sorted(label_resource_dict.items(), key=lambda x: x[1]) if k not in symptom_label_list + no_symptom_label_list}
    return label_resource_dict

def get_medline_id_of_disease(disease_id):
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery(f"""
                SELECT ?medlineId
                WHERE {{
                    {disease_id.replace("http://dbpedia.org/resource/", "dbr:")} dbo:medlinePlus ?medlineId.
                }}
            """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    if len(results) > 0:
        return results[0]["medlineId"]["value"]
    else:
        return None

if __name__ == "__main__":
    symptom_dict = get_all_symptoms()
    symptom_list = [symptom_dict["Fever"], symptom_dict["Fatigue"]]
    disease_dict = get_diseases_by_symptoms(symptom_list)
    print("Done")
