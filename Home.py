import pandas as pd
import streamlit as st

from backend.dbpedia_handler import *
from backend.medline_handler import get_article

st.title("Healthcare")

s_state = st.session_state
if "status" not in s_state:
    s_state.status = "User Input"

if s_state.status == "User Input":
    if "symptom_list" not in s_state:
        s_state.symptom_list = []

    if "symptom_dict" not in s_state:
        s_state.symptom_dict = get_all_symptoms()

    st.divider()
    st.subheader("Symptom Input")

    for i, symptom in enumerate(s_state.symptom_list):
        with st.container(border=True):
            col1, col2 = st.columns(2)
            col1.write(symptom)
            if col2.button("Delete Symptom", key=i):
                del s_state.symptom_list[i]
                st.rerun()

    selected_symptom = st.selectbox("Symptom",
                                    sorted(set(s_state.symptom_dict.keys()).difference(set(s_state.symptom_list))))
    if st.button("Add Symptom"):
        s_state.symptom_list.append(selected_symptom)
        st.rerun()

    if len(s_state.symptom_list) > 0:
        s_state.possible_diseases = get_diseases_by_symptoms([s_state.symptom_dict[x] for x in s_state.symptom_list])
        print(
            f"Diseases found: {len(s_state.possible_diseases)}")
        if st.button("Finish Input"):
            s_state.status = "Symptom Questions"
            st.rerun()

if s_state.status == "Symptom Questions":
    st.divider()
    st.subheader("Symptom Questions")
    if "disease_index" not in s_state:
        s_state.disease_index = 0
    if "question_index" not in s_state:
        s_state.question_index = 0
    if "no_symptom_list" not in s_state:
        s_state.no_symptom_list = []
    st.write(f"Already known symptoms: {', '.join(s_state.symptom_list)}")
    st.write(f"Already excluded symptoms: {', '.join(s_state.no_symptom_list)}")
    print(f"Testing for: {list(s_state.possible_diseases.keys())[s_state.disease_index]}")
    possible_symptoms = get_symptoms_of_disease(list(s_state.possible_diseases.values())[s_state.disease_index],
                                                s_state.symptom_list, s_state.no_symptom_list)
    if len(possible_symptoms) > s_state.question_index:
        with st.container(border=True):
            st.write(f"Do you have: {list(possible_symptoms.keys())[s_state.question_index]}")
            if st.button("Yes"):
                s_state.symptom_list.append(list(possible_symptoms.keys())[s_state.question_index])
                s_state.question_index += 1
                st.rerun()
            if st.button("No"):
                s_state.no_symptom_list.append(list(possible_symptoms.keys())[s_state.question_index])
                s_state.question_index += 1
                st.rerun()
    elif s_state.disease_index + 1 < len(s_state.possible_diseases):
        s_state.question_index = 0
        s_state.disease_index += 1
        st.rerun()
    else:
        s_state.possible_diseases = get_diseases_by_symptoms([s_state.symptom_dict[x] for x in s_state.symptom_list])
        s_state.disease_index = 0
        s_state.status = "Plausibility Check"
        st.rerun()

if s_state.status == "Plausibility Check":
    st.divider()
    st.subheader("Plausibilty Check")
    medlineId = get_medline_id_of_disease(list(s_state.possible_diseases.values())[s_state.disease_index])
    if medlineId:
        st.write(f"Possible Disease: {list(s_state.possible_diseases.keys())[s_state.disease_index]}")
        article_text, symptoms_text = get_article(medlineId)
        st.text(symptoms_text)