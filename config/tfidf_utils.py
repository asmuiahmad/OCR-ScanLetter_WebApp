import os
from sklearn.feature_extraction.text import TfidfVectorizer
from config.models import SuratMasuk, SuratKeluar
from config.extensions import db

# Ambil semua isi surat masuk dari database
def get_all_isi_surat_masuk():
    return [s.isi_suratMasuk for s in SuratMasuk.query.all() if s.isi_suratMasuk]

# Ambil semua isi surat keluar dari database
def get_all_isi_surat_keluar():
    return [s.isi_suratKeluar for s in SuratKeluar.query.all() if s.isi_suratKeluar]

# Hitung TF-IDF untuk surat masuk
def get_tfidf_for_surat_masuk():
    documents = get_all_isi_surat_masuk()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    return tfidf_matrix, feature_names, documents

# Hitung TF-IDF untuk surat keluar
def get_tfidf_for_surat_keluar():
    documents = get_all_isi_surat_keluar()
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    return tfidf_matrix, feature_names, documents

# Ambil top N kata dengan skor tertinggi untuk setiap dokumen
def get_top_terms_per_doc(tfidf_matrix, feature_names, top_n=5):
    top_terms = []
    for doc_idx in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix.getrow(doc_idx).toarray().flatten()
        top_indices = row.argsort()[-top_n:][::-1]
        terms = [(feature_names[i], row[i]) for i in top_indices if row[i] > 0]
        top_terms.append(terms)
    return top_terms 