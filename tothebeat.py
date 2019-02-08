#This program syncs video with music



#Iterate through audio every .25 sec
#See if that .25 sec has a hit/beat/etc
#find the exact location of that hit/beat/etc

#options for arss
#min freq           = 27.500
#bands per octave   = 24
#max freq           = 20000
#pixels per sec     = 150



'''from scipy.spatial import distance

def euc(a, b):
    return distance.euclidean(a, b)

class ScrappyKNN():
    def fit(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train
    
    def predict(self, X_test):
        predictions = []

        for row in X_test:
            label = self.closest(row)
            predictions.append(label)

        return predictions

    def closest(self, row):
        best_dist = euc(row, self.X_train[0])
        best_index = 0
        for i in range(1, len(self.X_train)):
            dist = euc(row, self.X_train[i])
            if dist < best_dist:
                best_dist = dist
                best_index = i
                
        return self.y_train[best_index]

from sklearn import datasets
iris = datasets.load_iris()

X = iris.data
y = iris.target

from sklearn.cross_validation import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.5)

#from sklearn.neighbors import KNeighborsClassifier
clf = ScrappyKNN()
clf.fit(X_train, y_train)

predictions = clf.predict(X_test)

from sklearn.metrics import accuracy_score
print(accuracy_score(y_test, predictions))
'''