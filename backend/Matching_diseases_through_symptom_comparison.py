from SPARQLWrapper import SPARQLWrapper, JSON

def get_all_diseases_and_symptoms():
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")
    sparql.setQuery("""
        SELECT DISTINCT ?disease ?symptom
        WHERE {
            ?disease a dbo:Disease;
                    dbo:symptom+ ?symptom.
        }
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    disease_symptom_map = {}
    for result in results["results"]["bindings"]:
        disease_uri = result["disease"]["value"]
        symptom_uri = result["symptom"]["value"]

        disease_name = disease_uri.split("/")[-1]  # Extracts the name after the last "/"
        symptom_name = symptom_uri.split("/")[-1]

        if disease_name not in disease_symptom_map:
            disease_symptom_map[disease_name] = set()

        disease_symptom_map[disease_name].add(symptom_name)

    # Retain only diseases with at least 2 symptoms
    disease_symptom_map = {disease: symptoms for disease, symptoms in disease_symptom_map.items() if len(symptoms) >= 2}

    return disease_symptom_map

def find_matching_diseases(disease_symptom_map):
    matches = []
    disease_list = list(disease_symptom_map.items())

    for i, (disease1, symptoms1) in enumerate(disease_list):
        for j, (disease2, symptoms2) in enumerate(disease_list):
            if i < j and symptoms1 == symptoms2:
                matches.append((disease1, disease2, symptoms1))

    return matches

def find_subset_relations(disease_symptom_map):
    subset_matches = []
    disease_list = list(disease_symptom_map.items())

    for i, (disease1, symptoms1) in enumerate(disease_list):
        for j, (disease2, symptoms2) in enumerate(disease_list):
            if i < j:
                # Checks if symptoms1 is a proper subset of symptoms2
                if symptoms1.issubset(symptoms2) and symptoms1 != symptoms2:
                    subset_matches.append((disease1, disease2, symptoms1, symptoms2))

    return subset_matches

# Example usage
all_diseases_symptoms = get_all_diseases_and_symptoms()
matching_diseases = find_matching_diseases(all_diseases_symptoms)

subset_relations = find_subset_relations(all_diseases_symptoms)

print("Diseases with identical symptoms:")
for disease1, disease2, symptoms in matching_diseases:
    # Display symptoms as a list
    symptom_list = ", ".join(symptoms)
    print(f"{disease1} and {disease2} have the symptoms: {symptom_list}")

print(f"Number of matches found: {len(matching_diseases)}")
print(f"Total number of diseases: {len(all_diseases_symptoms)}")

#print("\nDiseases where the symptoms are a proper subset of another disease:")
#for disease1, disease2, symptoms1, symptoms2 in subset_relations:
#    print(f"{disease1} has the symptoms {', '.join(symptoms1)} as a subset of {disease2} (with additional symptoms: {', '.join(symptoms2 - symptoms1)})")

print(f"\nNumber of subset relations: {len(subset_relations)}")
