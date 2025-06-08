import sys
import os
import numpy as np
import time

from .utils import *

class ItemToItem():
    '''
    This method initializes the ItemToItem class with the necessary data and parameters,
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
        self.matrix = self.generate_items_matrix()
    
    '''
    This method calculates the mean ratings of each items
    '''
    def calculateRatingsMean(self):
        matrix = self.matrix
        ratingsMean = {}
        for k, v in matrix.items():
            ratingsMean[k] = sum(v.values())/len(v)
        return ratingsMean
    
    '''
    This method computes Pearson similariy between two items
    '''
    def pearsonSimilarity(self, itemA, itemB, meanItemA, meanItemB):
        ratingsA = {userId: rating-meanItemA for userId, rating in itemA}
        ratingsB = {userId: rating-meanItemB for userId, rating in itemB}
        
        # Find common users and their ratings
        common_users = set(ratingsA.keys()) & set(ratingsB.keys())
        if not common_users:
            return 0  # No common users, similarity is 0
        
        # Calculate person similarity
        # sumAB, sumA, sumB = 0, 0, 0
        # for userId in common_users:
        #     ratingA = ratingsA[userId]
        #     ratingB = ratingsB[userId]
        #     sumAB += ratingA * ratingB
        #     sumA += ratingA ** 2
        #     sumB += ratingB ** 2

        # Calculate person similarity
        sumAB = sum([ratingsA[userId] * ratingsB[userId] for userId in common_users])
        sumA = sum([ratingsA[userId] ** 2 for userId in common_users])
        sumB = sum([ratingsB[userId] ** 2 for userId in common_users])
        
        # Check for division by zero
        if sumA == 0 or sumB == 0: return 0

        similarity = sumAB / (np.sqrt(sumA) * np.sqrt(sumB))
        return similarity

    '''
    This function generates the matrix between users and items with their ratings, where M[item][user] = rating
    '''
    def generate_items_matrix(self):
        # Complete the datastructure for rating matrix 
        movies_idx = self.movies['movieId']
        m = {}
        data = []
        ratings = self.ratings_train

        for i in movies_idx:
            ratingsMovie = ratings.loc[(ratings['movieId'] == i)]
            # Find all users that rated the movie
            data = ratingsMovie[['userId', 'rating']].values.tolist()
            rate = {}
            for j in data:
                rate[j[0]] = j[1]
            if len(rate) != 0:  m[i] = rate    
        return m 

    '''
    This function find the movies seen and unseen by the specified user
    '''
    def findItemsSeenAndNoSeenByUser(self, userId):
        seenMovies = {}
        unseenMovies = {}
        matrix = self.matrix
        for item, users in matrix.items():
            if userId in users.keys(): seenMovies[item] = users
            else: unseenMovies[item] = users
        # print(len(seenMovies))
        return (seenMovies, unseenMovies)

    '''
    Computation function of item-to-item collaborative filtering algorithm
    '''
    def item_based_recommender(self, target_user_idx):
        matrix = self.matrix
        recommendations = []
        
        # Compute the mean rating of each movie and find seen and unseen movies by the target user
        moviesRatingMean = self.calculateRatingsMean()
        seenMovies, unseenMovies = self.findItemsSeenAndNoSeenByUser(target_user_idx)
        predictRateUnseenMovies = {}
        
        # For each seen movie, find the ratings of the target user
        userRate = {}
        for k, v in seenMovies.items():
            userRate[k] = matrix[k][target_user_idx]
        
        for kUnseenMovies, vUnseenMovies in unseenMovies.items():
            usersListA = list(vUnseenMovies.items())
            similarity = {}
            simMax = 0
            simMin = 0
            # Find seen movie and unseen movie similarity
            for kSeenMovies, vSeenMovies in seenMovies.items():
                usersListB = list(vSeenMovies.items())
                # Compute the similarity between the two movies
                sim = self.pearsonSimilarity(usersListA, usersListB, moviesRatingMean[kUnseenMovies], moviesRatingMean[kSeenMovies])
                if simMax < sim: simMax = sim
                if simMin > sim: simMin = sim
                similarity[kSeenMovies] = sim
            
            # Normalize similarities between 0 and 1
            # sum all similarity respecte an unseen movie
            sumRateSim = 0
            similitude = 0
            for kSimilarity, vSimilarity in similarity.items():
                if vSimilarity != 0: 
                    similarity[kSimilarity] = (vSimilarity - simMin) / (simMax-simMin)
                    sumRateSim += similarity[kSimilarity]*userRate[kSimilarity]
                    similitude += similarity[kSimilarity]
            
            # Predict the rating of the unseen movie
            if sumRateSim == 0: predictRateUnseenMovies[kUnseenMovies] = 0
            else: predictRateUnseenMovies[kUnseenMovies] = sumRateSim/similitude
            recommendations.append((kUnseenMovies, predictRateUnseenMovies[kUnseenMovies]))
        
        # Sort the recommendations by the predicted rating
        recommendations = sorted(recommendations, key=lambda x:x[1], reverse=True)

        # Normalize the predictions
        max = recommendations[0][1]
        min = recommendations[len(recommendations)-1][1]
        for i in range(len(recommendations)):
            predictRate = (recommendations[i][1] - min) / (max - min)
            recommendations[i] = (recommendations[i][0], predictRate)

        self.recommendations = recommendations
        return recommendations

    '''
    Method to print the top K recommendations
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
        # print(' Similarity with item-to-item recommender for user: '+ str(target_user_idx) + ' is ' + str(sim))
        return sim

