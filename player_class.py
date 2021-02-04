class Player:
    def __init__(self, name):
        self.name = name
        self.role = ''
        self.points = 0
        self.hasVote = True

    def playerVoted(self):
        self.hasVote = False

    def addPoints(self, points):
        self.points += points

    def setRole(self, role):
        self.role = role
