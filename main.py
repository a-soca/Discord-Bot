import settings
import discord 
from discord.ext import commands
import random
import time

logger = settings.logging.getLogger("bot")

# Each member of the server is represented as a "User"
class User():
    def __init__ (self, id: int, name: str, balance: int):
        self.name = name # User Name
        self.wallet = balance # User balance
        self.id = id # User id (used to match Users to members)

        # Storing user's last bet parameters to allow multiple user's bets to occur simultaneously
        self.lastBet = 0 # Stores the last bet made by the user
        self.lastOdds = 0 # Stores the odds of the last bet made by the user

    def deposit(self, amount: int): # Function to deposit money to wallet
        self.wallet += amount

    def spend(self, amount: int): # Function to spend money from wallet
        self.wallet -= amount

    # Utilities
    def set_balance(self, amount: int): # Function to set wallet balance
        self.wallet = amount

    def win(self): # Function to payout bet wins
        self.deposit(self.lastBet*self.lastOdds)

    def invalid(self): # Function to return money after an invalid bet or error
        self.deposit(self.lastBet)
    
# Create dictionary to store users
users = dict() # TODO This should be made persistent by storing in another file

def run(): # Main bot code
    intents = discord.Intents.default() # Set initial intents
    intents.message_content = True # Add intent to read messages
    intents.members = True # Add intent to view server members

    bot = commands.Bot(command_prefix = "!", intents = intents)

    @bot.event
    async def on_ready(): # Runs when bot connects
        logger.info(f"User: {bot.user} (ID: {bot.user.id})") # Add bot connection info to logger
        for guild in bot.guilds: # For all servers the bot is in,
            for member in guild.members: # For every member in the server,
                # TODO check if user account already exists before creating
                users[member.id] = User(member.id, member.name, 100) # Initialise their User class
                print("Account created for " + member.name + ", Balance : " + str(users[member.id].wallet)) # TODO remove in final
                logger.info("Account created for " + member.name + ", Balance : " + str(users[member.id].wallet)) # Add User class creation info to logger

    @bot.group()
    async def bet(ctx, amount : int): # Action Group for betting
        if ctx.invoked_subcommand is None: # If an invalid betting game is entered, send error
            await ctx.send(f"Invalid bet : {ctx.subcommand_passed}")
            users[ctx.author.id].invalid()
        else: # Otherwise
            users[ctx.author.id].spend(amount) # Withdraw the amount of the bet from the user's wallet immediately
            users[ctx.author.id].lastBet = amount # Set the last bet variable to the amount bet

    @bot.group()
    async def wallet(ctx): # Action Group for wallet
        if ctx.invoked_subcommand is None: # If an invalid wallet command is entered, send error
            await ctx.send(f"Invalid command : {ctx.subcommand_passed}")

    @bot.command(
            help = "Tests if bot is live",
            description = "Replies with \"Pong\"",
            brief = "Replies with \"Pong\""
    )
    async def ping(ctx): # Ping command for bot
        await ctx.send("Pong")

    @bot.command(
            help = "Repeats what you say",
            description = "Replies to you with your message",
            brief = "Repeats what you say"
    )
    async def say(ctx, *message): # Message repitition command for bot
        if(len(message) == 0):
            await ctx.send("Say what?")
        else:
            await ctx.send(" ".join(message))

    @wallet.command(
            help = "Wipes debt",
            description = "Sets the balance of the specified user to 100",
            brief = "Utility function for resetting balance"
    )
    async def wipe_debt(ctx, member : discord.Member): # Sets the balance of the specified user to 100 
        users[member.id].set_balance(100)
        await ctx.send("Wiped " + member.name + "'s debt!")

    @wallet.command(
            help = "Displays someone's balance",
            description = "Displays the balance of the specified user",
            brief = "Display another user's balance"
    )
    async def pocket_watch(ctx, member : discord.Member): # Displays the balance of the specified user
        await ctx.send(member.name + "'s balance is : " + str(users[member.id].wallet))

    @wallet.command(
            help = "Displays your balance",
            description = "Displays the balance of the user who requests the command",
            brief = "Display user's balance"
    )
    async def open(ctx): # Displays the balance of the user requesting the command
        await ctx.send("Your balance is : " + str(users[ctx.author.id].wallet))

    @wallet.command(
            help = "Utility balance decrease",
            description = "Decreases the balance of specified user",
            brief = "Balance Decrease"
    )
    async def spend(ctx, member : discord.Member, amount : int): # Utility function to decrease wallet balance of specified user
        users[member.id].spend(amount)
        await ctx.send("Spent : " + str(amount))

    @wallet.command(
            help = "Utility balance increase",
            description = "Increases the balance of specified user",
            brief = "Balance Increase"
    )
    async def deposit(ctx, member : discord.Member, amount : int): # Utility function to increase wallet balance of specified user
        users[member.id].deposit(amount)
        await ctx.send("Deposited : " + str(amount))

    @bet.command(
            help = "Dice Roll",
            description = "Picks a number from 1-6 and tells you if your guess was correct",
            brief = "1-6 guesser"
    )
    async def roll(ctx, message = None): # Bet on a 6 sided dice roll
        if message == None:
            await ctx.send("You forgot to enter your number!")
            users[ctx.author.id].invalid()
            await ctx.send("(Your money was returned)")
            return
        odds = 6 # Sets the odds of the game (by default 6, can change to higher or lower returns)
        await ctx.send("Your number is " + message + "!")
        try :
            number = int(message)
            if(number > 6 or number < 1):
                await ctx.send("Pick a number between 1 and 6 next time...")
                users[ctx.author.id].invalid()
                await ctx.send("(Your money was returned)")
                return
            else:
                users[ctx.author.id].lastOdds = odds
                await ctx.send("Rolling...")
                rand = random.randint(1,6)
                time.sleep(1)
                await ctx.send("...")
                time.sleep(1)
                await ctx.send("You rolled : " + str(rand))
                if(number == rand):
                    await ctx.send("You won!")
                    users[ctx.author.id].win()
                else:
                    await ctx.send("You lost...")
        except:
            await ctx.send("That's not a number!")
            users[ctx.author.id].invalid()

    @bot.command(
            help = "Choices",
            description = "Picks a choice from a list of options",
            brief = "Picks a choice"
    )
    async def choose_between(ctx, *options):
        optList = options[0]
        if(len(options) > 1):
            for i in range(len(options)-2): # Creating sensible string from choices
                optList = optList + ", " + options[i+1]
            optList = optList + " and " + options[-1]
            await ctx.send("If I had to pick between " + optList)
            time.sleep(1)
            await ctx.send("...")
            time.sleep(1)
            await ctx.send("I suppose I would choose " + random.choice(options) + "!")
        else:
            await ctx.send("I don't have a choice!")
        

    bot.run(settings.DISCORD_API_SECRET, root_logger = True)

if __name__ == "__main__":
    run()