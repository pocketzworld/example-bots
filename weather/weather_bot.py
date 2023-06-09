import httpx
from highrise import BaseBot, User


"""
Note: 
Make sure you have the httpx module installed. You can install it using 'pip install httpx'.
An API key is also necessary to run this bot, sign up for a free one here: 'https://www.weatherapi.com/signup.aspx'

Usage:
To start interacting with the Weather Bot, use the following command in the chat of the 
room your bot is currently in, replacing <location> with the desired location:

/w <location>

Example:
/w Paris

The Weather Bot will provide you with the current temperature for the specified location.

Please note that the accuracy and availability of weather data may vary depending on the location and the weather API being used.
"""


class WeatherBot(BaseBot):
    """
    A Highrise bot that displays the current temperature based on location (city, country, etc.) input

    This class extends the base Highrise bot and uses a third-party API to retrieve weather information. It 
    offers a command to retrieve the temperature of a specified location in celsius and fahrenheit. 
    """

    identifier: str = "/w "  # Command prefix for the bot
    APIKEY: str = "<YOUR-API-KEY>" # API key for weatherapi.com 

    async def on_chat(self, user: User, message: str) -> None:
        """On a received room-wide chat."""

        # Handle commands
        if message.startswith(self.identifier):
            await self.handle_command(message.removeprefix(self.identifier))

    async def handle_command(self, message: str) -> None:
        """Handler for bot commands"""

        response = await self.get_weather_data(message)

        if response is not None:
            # Convert the response to JSON format
            data = response.json()
            if "current" in data:
                # Extract the current temperature and display it
                await self.highrise.chat(f"The current temperature in {message} is:\n{data['current']['temp_c']} °C\n{data['current']['temp_f']} °F")
            elif "error" in data:
                # Common mistake is to forget to replace <YOUR-API-KEY>
                await self.highrise.chat("Make sure you've configured your bot with a valid weatherapi.com API key")

                # Other error handling would go here...

            else:
                # Handle unrecognized location
                await self.highrise.chat(f"Unrecognized location: {message}")
        else:
            # Handle failed API request
            await self.highrise.chat("Failed to retrieve weather data.")

    async def get_weather_data(self, location: str) -> httpx.Response:
        """Retrieves and returns the weather data based on provided location"""
        async with httpx.AsyncClient() as client:
            # Send a GET request to the API endpoint
            response = await client.get(f"http://api.weatherapi.com/v1/current.json?key={self.APIKEY}&q={location}")

            return response
