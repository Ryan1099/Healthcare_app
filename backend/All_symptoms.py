from SPARQLWrapper import SPARQLWrapper, JSON

count = 0  # Globale Zählvariable

def get_all_symptoms():
    global count  # Deklariere, dass die globale count-Variable verwendet wird

    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery("""
        SELECT DISTINCT ?symptom
        WHERE {
            ?disease dbo:symptom ?symptom.
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    symptoms = []
    for result in results["results"]["bindings"]:
        symptom_uri = result["symptom"]["value"]
        symptom_name = symptom_uri.split("/")[-1]  # Extrahiert den Namen nach dem letzten "/"
        symptoms.append(symptom_name)
        count += 1  # Erhöht den globalen Zähler
    return symptoms

# Beispielnutzung
all_symptoms = get_all_symptoms()
print(f"Liste der verfügbaren Symptome:")
for symptom in all_symptoms:
    print(symptom)

# Ausgabe der Anzahl der Symptome
print(f"Wir haben folgende Anzahl an Symptomen gefunden: {count}")
