from json import load, dump
from time import time
from math import sqrt
from typing import Dict, List
from highrise import BaseBot, User, Position, AnchorPosition

"""
Usage:

To start interacting with the statistics bot, use any of the following commands to see 
statistics of users who have entered your room:

/s leaderboard
/s @<username>

"""

class StatisticsBot(BaseBot):
    """
    A Highrise bot that passively tracks user activity in a room

    This class extends the base Highrise bot and uses a local JSON file to record
    user activity. It offers commands to view specific users' activity, along with
    a leaderboard of the most active users in the room. There are simplier and more 
    complicated ways to implement your own bot; the way it is done here is just an 
    example to help get you started. It will mainly depend on your specific bot's needs.   
    """

    identifier: str = "/s " # make this an empty string for testing purposes
    lobby: Dict[str, dict] = {}

    async def on_chat(self, user: User, message: str) -> None:
        """On a received room-wide chat."""

        # calculate the number of characters 
        num_chars = len(message)

        # write the data to JSON
        self.write_data(user, "chat_message_chars", num_chars)

        # handle commands
        if (message.startswith(self.identifier)):
            await self.handle_command(user, message.removeprefix(self.identifier))

    async def on_user_join(self, user: User) -> None:
        """On a user joining the room."""

        if not user.id in self.lobby:
            # add user to lobby
            self.lobby[user.id] = self.create_default()
        

    async def on_user_leave(self, user: User) -> None:
        """On a user leaving the room."""

        if user.id in self.lobby:
            # number of seconds user spent in the room
            time_spent = round(
                time() - self.lobby[user.id]["time_joined"])

            # write the data to JSON
            self.write_data(user, "time_spent", time_spent)

            # remove their entry from lobby
            del self.lobby[user.id]


    async def on_user_move(self, user: User, pos: Position | AnchorPosition) -> None:
        """On a user moving in the room."""

        # we're only tracking distance for Position, not AnchorPosition
        if isinstance(pos, Position):
            if not user.id in self.lobby:
                self.lobby[user.id] = self.create_default()
            
            # calculate distance
            distance = self.calculate_distance(self.lobby[user.id]["last_pos"], pos)

            # write the data to JSON
            self.write_data(user, "distance_travelled", distance)

            # set their new "last pos"
            self.lobby[user.id]["last_pos"] = pos

    def write_data(self, user: User, key: str, value: int) -> None:
        """Writes data to local JSON file"""

        with open("./data.json", "r+") as file:
            data = load(file)

            # Move the file pointer back to the beginning
            file.seek(0)

            # Perform desired operations on the data
            if user.id in data:
                data[user.id][key] = data[user.id][key] + value
            else:
                # new user in the room
                data[user.id] = {
                    "time_spent": 0,
                    "chat_message_chars": 0,
                    "distance_travelled": 0,
                    "username": user.username
                }
                data[user.id][key] = value

            # Print the updated data
            print(f"Updated {user.username} with {value} of {key}")

            # Write the updated data back to the file
            dump(data, file)
            file.truncate()

    async def handle_command(self, user: User, message: str) -> None:
        """Handler for all bot commands"""
            
        match message:
            case "leaderboard" | "Leaderboard":
                with open("./data.json", "r") as file:
                    data = load(file)

                    # Get the top 5 most active users by score
                    top_five = self.get_leaderboard(data)
                    await self.highrise.chat("Leaderboard:\n" + "\n".join(top_five))

            case username if message.startswith("@") and len(message[1:]) > 0:
                with open("./data.json", "r") as file:
                    data = load(file)

                    username = username[1:] # trim @ character

                    for value in data.values():
                        if value["username"] == username:
                            stats = [
                                f"Distance Walked: {value['distance_travelled']}",
                                f"Time Spent: {value['time_spent']}",
                                f"Characters Messaged: {value['chat_message_chars']}"
                            ]
                            return await self.highrise.chat(f"{username}:\n" + "\n".join(stats))
                    
                    # user does not exist in our JSON
                    return await self.highrise.chat(f"{username} does not exist or has not joined this room before")
            case _:
                await self.highrise.send_whisper(user.id, f"Not a valid command. Use {self.identifier}help to see the list of commands")

    def calculate_distance(self, lastpos: Position, nextpos: Position) -> None:
        """Calculate the distance a user has travelled based on their last and next location"""
        return round(sqrt(pow(lastpos.x - nextpos.x, 2) + pow(lastpos.y - nextpos.y, 2) + pow(lastpos.z - nextpos.z, 2)))

    def create_default(self) -> Dict[str, object]:
        """Create dict to track user data"""
        return ({
                "last_pos": Position(0, 0, 0, "FrontRight"),
                "time_joined": time()
            })
    
    def get_leaderboard(self, data: Dict[str, dict]) -> List[str]:
        """Returns top 5 most active users based on their score, where score is the sum of all metrics"""
        
        # Calculate the score for each user
        scores = {metrics["username"]: self.calculate_score(metrics) for metrics in data.values()}

        # Sort the users based on their scores in descending order
        sorted_users = sorted(scores, key=scores.get, reverse=True)

        # Get the top 5 users
        top_five = sorted_users[:5]

        return top_five
    
    def calculate_score(self, data: Dict[str, dict]) -> List[str]:
        """Calculates the score of a user to determine leaderboard rankings"""
        return data["time_spent"] + data["chat_message_chars"] + data["distance_travelled"]
