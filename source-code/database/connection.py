
import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_database():

    mongo_uri = st.secrets["mongodb"]["uri"]
    database_name = st.secrets["mongodb"]["database"]

    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client[database_name]

    return db


def test_connection():

    try:
        db = get_database()

        return True, f"Kết nối thành công! Database: {db.name}"

    except Exception as e:

        return False, str(e)
