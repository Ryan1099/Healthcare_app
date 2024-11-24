import pandas as pd  # Bibliothek zur Datenanalyse (z. B. für das Arbeiten mit DataFrames)
import streamlit as st  # Streamlit für die Erstellung von Webanwendungen.

# Import von benutzerdefinierten Funktionen
from backend.dbpedia_handler import *  # Funktionen für DBpedia-Abfragen (z. B. Symptome/Krankheiten)
from backend.medline_handler import get_article  # Funktion zum Abrufen eines Medline-Artikels.
from backend.Entropy import *  # Funktionen zur Berechnung der Entropie von Symptomen
from backend.wikipedia_handler import get_symptom_text


# Zugriff auf den Session-Status, um Daten während der Interaktion zu speichern.
s_state = st.session_state

# Setzt den Titel der Streamlit-Anwendung.
st.title("Healthcare")

if st.button("New Query"):
    for key in st.session_state.keys():
        del st.session_state[key]
    s_state.status = "User Input"
    st.rerun()



# Initialisierung des Status, falls dieser noch nicht existiert.
if "status" not in s_state:
    s_state.status = "User Input"  # Startzustand: Benutzer gibt Symptome ein.

# Zustand "User Input" (Symptomeingabe durch den Nutzer).
if s_state.status == "User Input":
    # Initialisierung der Liste für Symptome, falls diese noch nicht existiert.
    if "symptom_list" not in s_state:
        s_state.symptom_list = []

    # Initialisierung des Wörterbuchs mit Symptomen, falls noch nicht vorhanden.
    if "symptom_dict" not in s_state:
        s_state.symptom_dict = get_all_symptoms()


    # Abrufen aller möglichen Symptome, die noch nicht hinzugefügt wurden.
    s_state.symptom_dict_pos = get_all_possible_symptoms(
        [s_state.symptom_dict[symptom] for symptom in s_state.symptom_list])


    # Trennlinie in der Benutzeroberfläche
    st.divider()
    st.subheader("Symptom Input")  # Unterüberschrift für die Symptomeingabe.

    # Anzeige der Symptome mit Möglichkeit, sie zu löschen.
    for i, symptom in enumerate(s_state.symptom_list):
        with st.container(border=True):  # Umrahmt jedes Symptom.
            col1, col2 = st.columns(2)  # Zwei Spalten für das Symptom und den Löschbutton.
            col1.write(symptom)  # Zeigt das Symptom an.
            if col2.button("Delete Symptom", key=i):  # Löscht das Symptom aus der Liste.
                del s_state.symptom_list[i]
                st.rerun()  # Aktualisiert die App, um die Änderung anzuzeigen.

    # Dropdown-Menü zur Auswahl eines neuen Symptoms aus der verfügbaren Liste.
    selected_symptom = st.selectbox(
        "Symptom",
        sorted(set(s_state.symptom_dict_pos.keys()).difference(set(s_state.symptom_list)))
    )

    # Hinzufügen des ausgewählten Symptoms zur Liste.
    if st.button("Add Symptom"):
        s_state.symptom_list.append(selected_symptom)
        st.rerun()

    # Wenn Symptome vorhanden sind, abrufen möglicher Krankheiten basierend auf den Symptomen.
    if len(s_state.symptom_list) > 0:
        s_state.possible_diseases = get_diseases_by_symptoms(
            [s_state.symptom_dict[x] for x in s_state.symptom_list]
        )
        print(f"Diseases found: {len(s_state.possible_diseases)}")
        if st.button("Finish Input"):  # Wechselt zum nächsten Schritt nach der Symptomeingabe.
            s_state.status = "Symptom Questions"  # Übergang zum Zustand der Symptomfragen.
            st.rerun()

# Zustand "Symptom Questions" (Weitere Fragen zu den Symptomen).
if s_state.status == "Symptom Questions":
    st.divider()
    st.subheader("Symptom Questions")

    # Initialisierung der Variablen für den Krankheits- und Frageindex.
    if "no_symptom_list" not in s_state:
        s_state.no_symptom_list = []

    # Anzeige der bekannten und ausgeschlossenen Symptome.
    st.write(f"Already known symptoms: {', '.join(s_state.symptom_list)}")
    st.write(f"Already excluded symptoms: {', '.join(s_state.no_symptom_list)}")

    # Berechnung der Entropie für alle Symptome der gefundenen Krankheiten.
    disease_list = get_diseases_for_symptoms([s_state.symptom_dict[x] for x in s_state.symptom_list])
    disease_symptom_pairs = get_disease_symptom_pairs(disease_list)
    entropy_values = calculate_entropy_for_all_symptoms(disease_symptom_pairs)

    # Entfernt Symptome, die bereits in den Listen vorhanden sind.
    filtered_entropy_values = {
        key: value
        for key, value in entropy_values.items()
        if key not in [s_state.symptom_dict[symptom] for symptom in s_state.no_symptom_list]
    }

    # Sortiert die verbleibenden Einträge nach Entropiewerten in absteigender Reihenfolge.
    sorted_filtered_entropy_values = sorted(filtered_entropy_values.items(), key=lambda x: x[1], reverse=True)

    print(sorted_filtered_entropy_values)

    # Entfernen und Überprüfen der Symptome für die Krankheiten.
    count_distinct_diseases = remove_and_check_symptoms(disease_symptom_pairs,
                                                        [s_state.symptom_dict[symptom] for symptom in
                                                         s_state.no_symptom_list])

    # Überprüfung, ob es noch Symptome gibt, die abgefragt werden müssen.
    if count_distinct_diseases > 1:
        symptom_with_highest_entropy = sorted_filtered_entropy_values[0]
        symptom = next(key for key, value in s_state.symptom_dict.items() if value == symptom_with_highest_entropy[0])

        with st.container(border=True):
            st.write(f"Do you have: {symptom}?")  # Fragt den Nutzer nach dem Symptom.

            # Wenn "Ja", fügt das Symptom der Liste hinzu.
            if st.button("Yes"):
                s_state.symptom_list.append(symptom)
                st.rerun()

            # Wenn "Nein", schließt das Symptom aus.
            if st.button("No"):
                s_state.no_symptom_list.append(symptom)
                st.rerun()
    else:  # Wenn keine weiteren Fragen übrig sind, wechselt zum Plausibilitäts-Check.
        s_state.possible_diseases = get_diseases_by_symptoms(
            [s_state.symptom_dict[x] for x in s_state.symptom_list]
        )
        print("Starting Plausibility Check for diseases:", s_state.possible_diseases)
        s_state.status = "Plausibility Check"
        st.rerun()

# Zustand "Plausibility Check" (Abschlussprüfung der Ergebnisse).
if s_state.status == "Plausibility Check":
    st.divider()
    st.subheader("Plausibility Check")

    if "disease_decision" not in s_state:
        s_state.disease_list = get_diseases_for_symptoms([s_state.symptom_dict[x] for x in s_state.symptom_list])
        print('Checking for ', s_state.disease_list)
        s_state.disease_decision = dict()

    if "current_index" not in s_state:
        s_state.current_index = 0

    # Abrufen der möglichen Krankheiten basierend auf den eingegebenen Symptomen.


    # Abrufen des Wikipedia Signs and Symptoms Kapitels.
    current_disease = list(s_state.possible_diseases.values())[s_state.current_index]

    with st.container(border=True):
        st.write("Does the following list of symptoms match your condition?")
        if st.button("Yes"):
            s_state.disease_decision[list(s_state.possible_diseases.keys())[s_state.current_index]] = True
            if s_state.current_index == len(s_state.disease_list) - 1:
                s_state.status = "Display Results"
            else:
                s_state.current_index += 1
            st.rerun()
        if st.button("No"):
            s_state.disease_decision[list(s_state.possible_diseases.keys())[s_state.current_index]] = False
            if s_state.current_index == len(s_state.disease_list) - 1:
                s_state.status = "Display Results"
            else:
                s_state.current_index += 1
            st.rerun()

    wikiPageID = get_wikiPageID_of_disease(current_disease)
    print(f"wikiPageID: {wikiPageID}")
    symptom_text = get_symptom_text(wikiPageID)

    print(symptom_text)

    if "An error occurred" not in symptom_text:  # Wenn eine Medline-ID gefunden wurde, Artikel und Symptome anzeigen.
        st.write(f"Possible Disease: {list(s_state.possible_diseases.keys())[s_state.current_index]}")
        st.markdown(symptom_text)  # Anzeige der Symptome im Artikel.
    else:
        # Wenn keine Medline-ID gefunden wird, wird die Krankheit ohne Medline-ID angezeigt.
        st.write(f"Possible Disease: {list(s_state.possible_diseases.keys())[s_state.current_index]}")
        st.write("Unfortunately no symptoms were found in Wikipedia")

if s_state.status == "Display Results":
    st.divider()
    st.subheader("Results")

    # Anzeige der ausgewählten Symptome.
    st.write(f"Selected Symptoms: {', '.join(s_state.symptom_list)}")

    # Anzeige der möglichen Krankheiten.
    st.write("Disease Symptom Answers:")
    st.write(s_state.disease_decision)