"""Optional exploratory TF-IDF + KMeans clustering. Not a trained engagement model."""

# Any is module we can use to have a value of any type. 
from typing import Any


# function defination says ads is an array of dictionaries. 
# Each dictionary is an ad. The arrow represents the returning mechanism. the type of value function would return 
def cluster_creatives(ads: list[dict[str, Any]]) -> dict[str, Any]:

    # we are using shorthands here. documents would have ads with headings and body together in each index.
    documents = [
        " ".join(str(ad.get(key) or "") for key in ("headline", "ad_text")).strip()
        for ad in ads
    ]

    # filtering ads with empty strings
    valid_indices = [i for i, doc in enumerate(documents) if doc]

    # filtering process with ads less than 4 
    if len(valid_indices) < 4:
        return {
            "status": "insufficient_data",
            "message": "At least four ads with text are needed for exploratory clustering.",
            "clusters": [],
        }

    # try and except
    try:

        # Kmeans helps in clustering the numerical features
        from sklearn.cluster import KMeans

        # TfidVectorizer is a famous module used for converting ads into numerical features
        from sklearn.feature_extraction.text import TfidfVectorizer

        # term frequency inverse document frequency (TF-IDF)
        valid_docs = [documents[i] for i in valid_indices]

        # stop_words = english means it will not consider common english words like the, is, and
        # ngram_range => it means it will consider one or two words(adjacent words).
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500, ngram_range=(1, 2))

        # it will perform two things, fit and transform
        # fit will learn the vocabalury and numerical weights and 
        # transform will convert each document into vectors using learned features
        matrix = vectorizer.fit_transform(valid_docs)

        # it checks whether no of features generated aren't zero. 
        if matrix.shape[1] == 0:
            raise ValueError("No meaningful terms found in the ad text.")


        # the no of clusters to be created must be between 2 and 3 
        n_clusters = min(3, max(2, len(valid_docs) // 3))

        # it ensures that no of clusters must not exceed the size of valid_docs
        n_clusters = min(n_clusters, len(valid_docs))

        # Imagine a three dimensional space and vectors in it. those vectors will be used by k means to
        # do clustering for nearby vectors.
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        
        # it will contain numbering like 0, 1, 2 which represents the cluster 0, cluster 1. 
        labels = model.fit_predict(matrix)

        # it reveals the name of the features
        terms = vectorizer.get_feature_names_out()
        clusters = []

        
        for cluster_id in range(n_clusters):
            member_local = [j for j, label in enumerate(labels) if int(label) == cluster_id]
            center = model.cluster_centers_[cluster_id]
            top_indices = center.argsort()[::-1][:5]
            clusters.append({
                "cluster_id": cluster_id,
                "label_terms": [str(terms[i]) for i in top_indices if center[i] > 0],
                "ad_indices": [valid_indices[j] for j in member_local],
                "size": len(member_local),
            })
        return {
            "status": "exploratory",
            "method": "TF-IDF + KMeans",
            "sample_size": len(valid_docs),
            "warning": "Clusters are exploratory and may be unstable on small samples; review example ads before drawing conclusions.",
            "clusters": clusters,
        }
    except Exception as exc:
        return {"status": "unavailable", "message": str(exc), "clusters": []}
