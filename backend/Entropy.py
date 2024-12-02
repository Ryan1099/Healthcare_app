import math
import time

from SPARQLWrapper import SPARQLWrapper, JSON

def get_diseases_for_symptoms(symptoms_list):
    """
    Finds diseases associated with the given symptoms via the DBpedia SPARQL endpoint.

    Args:
    - symptoms_list (list): A list of symptoms (e.g., ["Headache", "Fever"]).

    Returns:
    - list: A list of diseases in the "dbr:" format.
    """
    # Set up the SPARQL endpoint
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")

    # Create conditions for the symptoms in the SPARQL query
    symptom_conditions = "\n".join([f"?disease dbo:symptom+ <{symptom}> ." for symptom in symptoms_list])

    # SPARQL query to find diseases based on the symptoms
    query = f"""
    SELECT DISTINCT ?disease
    WHERE {{
        {symptom_conditions}
    }}
    """

    # Configure and execute the query
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = None
    for attempt in range(3):
        try:
            results = sparql.query().convert()["results"]["bindings"]
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise

    if not results:
        print("No results found for the given symptoms")
        return []

    # Extract diseases from the results and convert them into "dbr:" format
    diseases = []
    for result in results:
        if "disease" in result:
            disease_value = result["disease"]["value"]
            diseases.append(disease_value)
        else:
            print("No 'disease' key found in result:", result)

    return diseases



def get_disease_symptom_pairs(disease_list):
    """
    Finds symptoms associated with the given diseases.

    Args:
    - disease_list (list): A list of diseases in the "dbr:" format.

    Returns:
    - dict: A dictionary that associates each disease (as a label) with its list of symptoms.
    """
    # Set up the SPARQL endpoint
    sparql = SPARQLWrapper("https://dbpedia.org/sparql")

    # Create conditions for the diseases in the SPARQL query
    disease_conditions = " ".join([f"<{disease}>" for disease in disease_list])

    # SPARQL query to find diseases and their symptoms
    query = f"""
    SELECT DISTINCT ?disease ?label ?symptom
    WHERE {{
        VALUES ?disease {{ {disease_conditions} }}
        ?disease dbo:symptom+ ?symptom.
        ?disease rdfs:label ?label.
        FILTER langMatches(lang(?label), "en")
    }}
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    results = None

    for attempt in range(3):
        try:
            results = sparql.query().convert()["results"]["bindings"]
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for entropy query: {e}")
            time.sleep(1)  # Add a small delay between retry attempts

    if results is None:
        raise Exception("Failed to execute query after 3 attempts")

    # Extract diseases and symptoms into a dictionary
    disease_symptom_pairs = {}
    for result in results:
        disease_label = result["label"]["value"]  # Disease as a readable label
        symptom = result["symptom"]["value"]  # Symptom in "dbr:" format

        if disease_label not in disease_symptom_pairs:
            disease_symptom_pairs[disease_label] = []
        disease_symptom_pairs[disease_label].append(symptom)

    # Print the number of found diseases
    print(f"Number of diseases found: {len(disease_symptom_pairs)}")

    return disease_symptom_pairs


def calculate_entropy_for_all_symptoms(disease_symptom_pairs):
    """
    Calculates the entropy for each symptom across all diseases.

    Args:
    - disease_symptom_pairs (dict): A dictionary associating diseases with their symptoms.

    Returns:
    - dict: A dictionary that associates each symptom with its calculated entropy.
    """
    # Count the occurrences of each symptom
    symptom_counts = {}
    total_diseases = len(disease_symptom_pairs)  # Total number of diseases

    for symptoms in disease_symptom_pairs.values():
        for symptom in symptoms:
            symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1

    # Calculate the entropy for each symptom
    entropies = {}
    for symptom, count in symptom_counts.items():
        p_positive = count / total_diseases  # Probability that a disease has this symptom
        p_negative = 1 - p_positive  # Probability that a disease does not have this symptom

        if p_positive == 0 or p_negative == 0:
            entropies[symptom] = 0  # No uncertainty if a symptom always/never occurs
        else:
            entropies[symptom] = - (
                p_positive * math.log2(p_positive) +
                p_negative * math.log2(p_negative)
            )

    # Sort the entropy values alphabetically by symptom
    return {k: v for k, v in sorted(entropies.items())}

from collections import defaultdict

def remove_and_check_symptoms(disease_symptom_pairs, no_symptom_list):
    # Neue Dictionary-Liste, um die gefilterten Ergebnisse zu speichern
    filtered_diseases = {}
    
    # Gehe jedes Krankheit-Symptom-Paar durch und filtere Symptome
    for disease, symptoms in disease_symptom_pairs.items():
        filtered_symptoms = [symptom for symptom in symptoms if symptom not in no_symptom_list]
        filtered_diseases[disease] = filtered_symptoms


    # Überprüfen auf doppelte Krankheiten basierend auf den Symptomen
    symptom_sets = defaultdict(list)
    
    for disease, symptoms in filtered_diseases.items():
        # Symptomliste in Set umwandeln, um die Reihenfolge zu ignorieren
        symptom_sets[tuple(sorted(symptoms))].append(disease)
    
    # Zähle die Anzahl der verschiedenen (distinct) Krankheiten
    distinct_count = len(symptom_sets)  # Anzahl der verschiedenen (distinct) Krankheiten
    
    return distinct_count

# Example usage
if __name__ == "__main__":
    # List of symptoms of interest
    symptoms = ["Headache", "Fever"]

    # Get diseases for the given symptoms
    disease_list = get_diseases_for_symptoms(symptoms)

    # Get symptoms for the found diseases
    disease_symptom_pairs = get_disease_symptom_pairs(disease_list)
    print(disease_symptom_pairs)

    # Calculate entropy for all symptoms
    entropy_values = calculate_entropy_for_all_symptoms(disease_symptom_pairs)

    # Print the entropy values for the symptoms
    print("Entropy values for symptoms:", entropy_values)
