import pandas as pd
import numpy as np
from .utils import *

class UserToUser:
    '''
    This method initializes the UserToUser class with the necessary data and parameters,
    preparing it for the item-to-item collaborative filtering algorithm.
     - self.ratings_train: Stores the training ratings dataset
     - self.users: Stores a list of users id
     - self.topK: Stores the number of top recommendations to be generated
     - self.movies: Stores a dataframe with the movies information
     - self.matrix: Stores the matrix between users and items with their ratings
    '''
    def __init__(self, ratings_train, movies, users, k=5) -> None:
        self.ratings_train = ratings_train
        self.topK = k
        self.movies = movies
        self.users = users
        self.matrix = self.generate_users_matrix()

    '''
    This method calculates the mean of each user's ratings and returns a dictionary
    with the mean ratings for each user
    '''
    def calculateRatingsMean(self):
        ratingsMean = {}
        matrix = self.matrix
        for k, v in matrix.items():
            ratingsMean[k] = sum(v.values())/len(v)
        return ratingsMean

    '''
    This method generates a matrix with the ratings of each user for each item, where M[user][item] = rating
    '''
    def generate_users_matrix(self):
        # Complete the datastructure for rating matrix 
        m = {}
        data = []
        ratings = self.ratings_train
        users = self.users
        for i in users:
            # Find movies rated by the user
            ratingsUser = ratings.loc[(ratings['userId'] == i)]
            data = ratingsUser[['movieId', 'rating']].values.tolist()
            rate = {}
            for j in data:
                rate[j[0]] = j[1]
            m[i] = rate
        return m 
    
    '''
    This function compute the similarity between two users
    '''
    def pearsonSimilarity(self, userA, userB, meanUserA, meanUserB):
        ## using dict
        ratingsA = {itemId: rating-meanUserA for itemId, rating in userA}
        ratingsB = {itemId: rating-meanUserB for itemId, rating in userB}
        
        # Find common users and their ratings
        common_items = set(ratingsA.keys()) & set(ratingsB.keys())
        if not common_items:
            return 0  # No common users, similarity is 0
        
        # Calculate person similarity
        # sumAB, sumA, sumB = 0, 0, 0
        # for itemId in common_items:
        #     ratingA = ratingsA[itemId]
        #     ratingB = ratingsB[itemId]
        #     sumAB += ratingA * ratingB
        #     sumA += ratingA ** 2
        #     sumB += ratingB ** 2

        # Calculate person similarity
        sumAB    = sum([ratingsA[userId] * ratingsB[userId] for userId in common_items])
        sumA     = sum([ratingsA[userId] ** 2 for userId in common_items])
        sumB     = sum([ratingsB[userId] ** 2 for userId in common_items])
        
        # Check for division by zero
        if sumA == 0 or sumB == 0: return 0

        similarity = sumAB / (np.sqrt(sumA) * np.sqrt(sumB))
        return similarity
        
    '''
    Function to get all unseen movies by a target user
    '''
    def getUnseenmovies(self, seenMovies):
        matrix = self.matrix
        unseenMovies = []
        first = True
        
        # Obtain unseen movies for an user
        for id, auxUser in matrix.items():
            auxUserList = list(auxUser.items())
            auxUserRating = pd.DataFrame(auxUserList, columns=['movieId', 'rating'])
            unseenMovies1 = auxUserRating.loc[~auxUserRating['movieId'].isin(seenMovies)]
            unseenMovies1 = unseenMovies1['movieId'].values.tolist()
            if first: 
                unseenMovies = unseenMovies1
                first = not first
            else: 
                # Obtain not repeated unseen movies
                for i in unseenMovies1:
                    if not i in unseenMovies: unseenMovies.append(i)
        return unseenMovies
    
    '''
     Computation function of user-to-user collaborative filtering algorithm
    '''
    def user_based_recommender(self, target_user_idx):
        matrix = self.matrix
        target_user = matrix[target_user_idx]
        recommendations = []
        # Compute the similarity between  the target user and each other user in the matrix. 
        # We recomend to store the results in a dataframe (userId and Similarity)

        # Calculate the average of ratings for each user
        usersRatingsMean = self.calculateRatingsMean()

        # Compute the similarity between the target user and each other user in the matrix.
        similarity = {}
        simMax, simMin = 0, 0
        targetUserList = list(target_user.items())
        
        for userId, userMovies in matrix.items():
            if userId != target_user_idx:
                userMoviesList = list(userMovies.items())
                # Compute the similarity between two users
                sim = self.pearsonSimilarity(targetUserList, userMoviesList, usersRatingsMean[target_user_idx], usersRatingsMean[userId])
                if simMax < sim: simMax = sim
                if simMin > sim: simMin = sim
                similarity[userId] = sim
        
        # Normalize the similarity between 0 and 1
        for k,v in similarity.items():
            if v != 0: similarity[k] = (v - simMin) / (simMax-simMin)
        
        # Determine the unseen movies by the target user. Those films are identfied since don't have any rating. 
        targetUser= pd.DataFrame(targetUserList, columns=['movieId', 'rating'])
        seenMovies = targetUser[['movieId']]
        seenMovies = seenMovies['movieId'].values.tolist()

        unseenMovies = self.getUnseenmovies(seenMovies)

        # Generate recommendations for unrated movies based on user similarity and ratings.
        meanUser = usersRatingsMean[target_user_idx]
        for i in unseenMovies:
            sum = 0
            for userId, userMovies in matrix.items():
                if userId != target_user_idx:
                    sim = similarity[userId]
                    ratingMean = usersRatingsMean[userId]
                    if not i in userMovies:
                        ratingMovie = 0
                    else:
                        ratingMovie = userMovies[i]
                    sum += sim*(ratingMovie-ratingMean)
            recommendations.append((i, meanUser+sum))
        # Sort recommendations by interest
        recommendations = sorted(recommendations, key=lambda x:x[1], reverse=True)
        
        # Normalize the recommendations beetween 0 and 1
        max = recommendations[0][1]
        min = recommendations[len(recommendations)-1][1]
        
        for i in range(len(recommendations)):
            if (max - min != 0): interest = (recommendations[i][1] - min) / (max - min)
            else: interest = 1.0
            recommendations[i] = (recommendations[i][0], interest)

        self.recommendations = recommendations
        return recommendations 
    
    '''
    This function prints the top K recommendations
    '''
    def printTopRecommendations(self):
        for recomendation in self.recommendations[:self.topK]:
            rec_movie = self.movies[self.movies["movieId"]  == recomendation[0]]
            print (" Recomendation: Movie:{} (Genre: {})".format(rec_movie["title"].values[0], rec_movie["genres"].values[0]))

    '''
    Method to compute the similarity between predictions and the validation dataset,
    which is the same as the similarity between the validation movies genres and the recommended movies genres
    '''
    def validation(self, ratings_val, target_user_idx):
        # Validation
        matrixmpa_genres, validationMoviesGenress = validationMoviesGenres(self.movies, ratings_val, target_user_idx)

        topMoviesUser = list(list(zip(*self.recommendations[:self.topK]))[0])
        recommendsMoviesUser = matrixmpa_genres.loc[topMoviesUser]
        
        # Compute the similarity between the validation movies genres and the recommended movies genres
        sim = cosinuSimilarity(validationMoviesGenress, recommendsMoviesUser)
        print(' Similarity with user-to-user recommender: ' + str(sim))
        return sim


# def main():
#     exploit_path = '../../../../Data Management/Exploitation Zone/ml-20m/'

#     spark = get_spark_session()
#     # Load ratings and filter
#     ratings = spark.read.format('delta').load(exploit_path + "ml-20m_rating")
#     ratings = ratings.filter(col('userId') <= 100)
#     ratings = ratings.limit(10000).toPandas()

#     # Get unique movieIds from ratings
#     movieIds = list(set(ratings['movieId']))

#     # Load movies and filter
#     movies = spark.read.format('delta').load( exploit_path + 'ml-20m_movie')
#     movies = movies.filter(col('movieId').isin(movieIds))
#     movies = movies.limit(len(movieIds)).toPandas()
#     dataset = {}
#     # Ratings data
#     val_movies = 5
#     ratings_train, ratings_val = split_users(ratings, val_movies)
    
#     # Create matrix between user and movies 
#     movies_idx = movies["movieId"]
#     users_idy = list(set(ratings_train["userId"].values))
#     start = time.time()

#     # 387, 109
#     target_user_idx = "80"
#     print('The prediction for user ' + str(target_user_idx) + ':')

#     userToUser = UserToUser(ratings_train, movies, users_idy)
#     recommendations = userToUser.user_based_recommender(target_user_idx)
#     userToUser.printTopRecommendations()
#     userToUser.validation(ratings_val, target_user_idx)

#     end = time.time()
#     print("The execution time: " + str(end-start) + " seconds")

# if __name__ == "__main__":
#     main()
