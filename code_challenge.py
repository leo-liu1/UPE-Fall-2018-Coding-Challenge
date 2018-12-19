import requests
import json
import sys

url = "http://ec2-34-216-8-43.us-west-2.compute.amazonaws.com"
uid = { "uid": 000000000 }
header = { "Content-Type": "application/x-www-form-urlencoded" }
token = ""
currentLoc = [0, 0]
currentLevel = 0
totalLevels = 0
width = 0
height = 0
maze = []
history = []
moves = [ "LEFT", "RIGHT", "UP", "DOWN" ]
totalMoves = 0

def checkStatusCode(status):
	if status != requests.codes.ok:
		print("Response code for POST returned error")
		sys.exit(1)

# returns the opposite direction. Ex: LEFT returns RIGHT
# returns INVALID if opp is not a valid direction
def reverse(opp):
	if opp == "LEFT":
		return "RIGHT"
	elif opp == "RIGHT":
		return "LEFT"
	elif opp == "UP":
		return "DOWN"
	elif opp == "DOWN":
		return "UP"
	else:
		return "INVALID"

# loc is an array containing the x and y coords of the position being checked
# direction is the direction being moved to
# returns [loc, valid] where loc is the new location
# and valid is true if it is within the bounds of the maze, false if not
def checkOutOfBounds(loc, direction):
	xVal = loc[0]
	yVal = loc[1]

	if direction == "LEFT":
		xVal = xVal - 1
	elif direction == "RIGHT":
		xVal = xVal + 1
	elif direction == "UP":
		yVal = yVal - 1
	elif direction == "DOWN":
		yVal = yVal + 1

	# check if out of bounds so no post call needs to be made
	valid = not (xVal < 0 or xVal >= width or yVal < 0 or yVal >= height)

	return [ [xVal, yVal], valid]

# prints string representation of known details of maze
def printMaze():
	global width
	global height
	global maze

	for i in range(height):
		for j in range(width):
			print(maze[i][j], end = " ")
		print()

# gets relevant maze info from HTTPS GET request
# also returns relevant status codes depending on game state
def getMazeInfo():
	global token
	global currentLoc
	global currentLevel
	global totalLevels
	global width
	global height
	global maze
	
	res = requests.get(url + "/game?token=" + token)
	info = json.loads(res.content)

	# process status codes
	if info["status"] == "NONE":
		print("Session has expired or does not exist")
		sys.exit(1)
	elif info["status"] == "GAME_OVER":
		print("Error with game. Status returns GAME_OVER")
		sys.exit(1)
	elif info["status"] == "FINISHED":
		print("All levels were successfully completed!")
		sys.exit(0)

	# fill global variables with data from JSON obj
	print(info)
	width = info["maze_size"][0]
	height = info["maze_size"][1]
	currentLoc = info["current_location"]
	currentLevel = info["levels_completed"]
	totalLevels = info["total_levels"]

	# initialize an empty maze and print out maze
	maze = [[0 for x in range(width)] for y in range(height)]
	maze[currentLoc[1]][currentLoc[0]] = 1;
	print("LEVEL", currentLevel, "INITAL STATE:")
	printMaze()

	return info

# direction is a string, that is either LEFT, UP, RIGHT, or DOWN
# moveIfExplored is a boolean that specifies whether or not a move will go back over explored territory
# if true, allows for moves to go back over explored territory, false if not
def move(direction, moveIfExplored = False, iteration = 0):
	global token
	global currentLoc
	global width
	global height
	global maze
	global history
	global totalMoves

	bounds = checkOutOfBounds(currentLoc, direction)
	newLoc = bounds[0]
	valid = bounds[1]

	# check if out of bounds
	if bounds[1] == False:
		return "OUT_OF_BOUNDS"

	# check if wall
	if maze[newLoc[1]][newLoc[0]] == 2:
		return "WALL"

	# if square was already explored
	if moveIfExplored == False and maze[newLoc[1]][newLoc[0]] == 1:
		return "EXPLORED"

	action = { "action": direction }
	res = requests.post(url + "/game?token=" + token, action, header)

	checkStatusCode(res.status_code)

	move = json.loads(res.content)["result"]

	if move == "WALL":
		maze[newLoc[1]][newLoc[0]] = 2
	elif move == "SUCCESS":
		maze[newLoc[1]][newLoc[0]] = 1;
		currentLoc = newLoc
		totalMoves = totalMoves + 1
		if iteration > 0 and totalMoves % iteration == 0:
			print("MOVE:", totalMoves, "CURRENT LOCATION:", currentLoc)
			printMaze()
		if moveIfExplored == False:
			history.append(direction)

	return move

# iteration is how often the maze should be printed based on the number of moves that it makes, < 0 means that the maze will not be printed
def generatePath(iteration = 0):
	global history
	global moves
	global currentLoc
	global currentLevel
	global totalMoves

	solved = False
	code = ""
	validMove = False
	totalMoves = 0

	while solved == False:
		validMove = False

		for direction in moves:
			code = move(direction = direction, iteration = iteration)
			if code == "SUCCESS":
				validMove = True
				break
			elif code == "END":
				print("Successfully reached the end of level", currentLevel, "with", totalMoves, "moves.")
				return True

		# check if move was valid
		if validMove == True:
			continue

		# if history is length 0, then that means there are no more moves to be made, and error is thrown
		if len(history) == 0:
			print("Error: No more moves can be made.")
			sys.exit(1)
		else:
			moveBackwards = reverse(history.pop())
			move(direction = moveBackwards, moveIfExplored = True, iteration = iteration)

def main():
	global uid
	global header
	global token
	global totalLevels
	global currentLevel

	res = requests.post(url + "/session", uid, header)
	checkStatusCode(res.status_code)
	token = json.loads(res.content)["token"]
	getMazeInfo()

	for x in range(totalLevels - currentLevel):
		getMazeInfo()
		generatePath(iteration = 10)

	getMazeInfo()

	print("ERROR: Program did not return a status")
	exit(1)

if __name__ == "__main__":
	main()
