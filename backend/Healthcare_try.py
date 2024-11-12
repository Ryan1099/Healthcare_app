from SPARQLWrapper import SPARQLWrapper, JSON

def get_disease_by_symptom(symptom):
    # Verbindung zu DBpedia SPARQL-Endpunkt
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    
    # SPARQL-Abfrage für Krankheiten basierend auf Symptomen
    query = f"""
    SELECT ?disease ?diseaseLabel
    WHERE {{
        ?disease dbo:symptom dbr:{symptom} .
        ?disease rdfs:label ?diseaseLabel .
        FILTER (lang(?diseaseLabel) = 'en')
    }}
    LIMIT 10
    """
    
    # Abfrage setzen und Format definieren
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    # Abfrage ausführen und Ergebnisse verarbeiten
    results = sparql.query().convert()
    diseases = []
    
    for result in results["results"]["bindings"]:
        diseases.append(result["diseaseLabel"]["value"])
    
    return diseases

# Beispielnutzung
symptom_input = "Fever"  # Beispiel-Symptom
predicted_diseases = get_disease_by_symptom(symptom_input)
if predicted_diseases:
    print("Basierend auf dem Symptom könnten folgende Krankheiten vorliegen:")
    for disease in predicted_diseases:
        print(f"- {disease}")
else:
    print("Keine passenden Krankheiten gefunden.")
