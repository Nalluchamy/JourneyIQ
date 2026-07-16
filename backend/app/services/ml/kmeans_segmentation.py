import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class KMeansSegmenter:
    """
    Unsupervised ML Algorithm for dynamically clustering customers based on RFM behaviors.
    """

    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)

    def cluster_users(self, user_rfm_data: list[dict]) -> dict[int, str]:
        """
        Takes a list of dicts with keys: user_id, recency, frequency, monetary
        Returns a mapping of {user_id: "Segment Name"}
        """
        if len(user_rfm_data) < self.n_clusters:
            raise ValueError(f"Requires at least {self.n_clusters} users to run K-Means.")

        user_ids = [d["user_id"] for d in user_rfm_data]
        
        # We invert Recency so that Higher = Better (more recent), matching F and M logic.
        # This makes centroid analysis easier (High R, High F, High M -> VIP).
        max_recency = max([d["recency"] for d in user_rfm_data])
        
        features = np.array([
            [
                max_recency - d["recency"], 
                d["frequency"], 
                d["monetary"]
            ]
            for d in user_rfm_data
        ])

        # Standardize the features so variables with larger scales (like monetary) don't dominate
        features_scaled = self.scaler.fit_transform(features)

        # Fit K-Means
        cluster_labels = self.kmeans.fit_predict(features_scaled)
        centroids = self.kmeans.cluster_centers_

        # Analyze centroids to dynamically assign business labels
        # Calculate a "value score" for each cluster centroid (sum of standardized scaled R, F, M)
        centroid_scores = [(idx, np.sum(centroid)) for idx, centroid in enumerate(centroids)]
        
        # Sort clusters by their value score (descending)
        centroid_scores.sort(key=lambda x: x[1], reverse=True)
        
        cluster_mapping = {}
        if self.n_clusters == 4:
            # High R, High F, High M
            cluster_mapping[centroid_scores[0][0]] = "VIP Champions"
            # Moderate
            cluster_mapping[centroid_scores[1][0]] = "Loyal Customers"
            # Lower, mostly new
            cluster_mapping[centroid_scores[2][0]] = "Recent Shoppers"
            # Low R (High days since last order), Low F, Low M
            cluster_mapping[centroid_scores[3][0]] = "At-Risk Customers"
        else:
            for i, (cluster_idx, _) in enumerate(centroid_scores):
                cluster_mapping[cluster_idx] = f"Cluster Rank {i+1}"

        # Map back to users
        user_segments = {}
        for uid, label_idx in zip(user_ids, cluster_labels):
            user_segments[uid] = cluster_mapping[label_idx]

        return user_segments
