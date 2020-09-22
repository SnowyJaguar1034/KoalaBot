#!/usr/bin/env python

"""
Koala Bot Text Filter Code
"""

# Libs
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Own modules
import KoalaBot
from utils import KoalaDBManager
from utils.KoalaColours import *

# Constants
load_dotenv()

# Variables
DBManager = KoalaDBManager.KoalaDBManager(KoalaBot.DATABASE_PATH)

class TextFilterCog(commands.Cog):
    """
    A discord.py cog with commands pertaining to the a Text Filter for admins to monitor their server
    """

    def __init__(self, bot):
        self.bot = bot
        self.tf_database_manager = TextFilterDBManager(KoalaBot.database_manager, bot)
        self.tf_database_manager.create_tables()

    @commands.command(name="filter", aliases=["filter_word"])
    #@commands.check(KoalaBot.is_admin)
    async def filter_new_word(self, ctx, word, filter_type="banned", too_many_arguments=None):
        """
        Adds new word to the filtered text list
        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :param filter_type: The filter type (banned or risky)
        :return:
        """
        error = "Something has gone wrong, your word may already be filtered or you have entered the command incorrectly. You try again with: `k!filter [filtered_text] [[risky] or [banned]]`"
        if too_many_arguments == None and typeExists(filter_type):
            await filterWord(self, ctx, word, filter_type)
            await ctx.channel.send("*" + word + "* has been filtered.")
            return
        raise Exception(error)

    @commands.command(name="unfilter", aliases=["unfilter_word"])
    #@commands.check(KoalaBot.is_admin)
    async def unfilter_word(self, ctx, word, too_many_arguments=None):
        """
        Removes existing words from filter list
        :param ctx: The discord context
        :param word: The first argument and word to be filtered
        :return:
        """
        error = "Too many arguments, please try again using the following arguments: `k!unfilter [filtered_word]`"
        if too_many_arguments == None:
            await unfilterWord(self, ctx, word)
            await ctx.channel.send("*"+word+"* has been unfiltered.")
            return
        raise Exception(error)

    @commands.command(name="checkFilteredWords", aliases=["check_filtered_words"])
    #@commands.check(KoalaBot.is_admin)
    async def checkFilteredWords(self, ctx):
        """
        Get a list of filtered words on the current guild.
        :param ctx: The discord context
        :return:
        """
        embed = discord.Embed()
        embed.colour = KOALA_GREEN
        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        embed.title = "Koala Moderation - Filtered Words"
        all_words, all_types = "", ""
        for word, filter_type in self.tf_database_manager.get_filtered_text_for_guild(ctx.guild.id):
            all_words+=word+"\n"
            all_types+=filter_type+"\n"
        embed.add_field(name="Banned Words", value=all_words)
        embed.add_field(name="Filter Types", value=all_types)

        await ctx.channel.send(embed=embed)

    @commands.command(name="setupModChannel", aliases=["setup_mod_channel"])
    #@commands.check(KoalaBot.is_admin)
    async def setupModChannel(self, ctx, channelId, too_many_arguments=None):
        """
        Get a list of filtered words on the current guild.
        :param ctx: The discord context
        :param channelId: The designated channel id for message details
        :return:
        """
        error="Channel not found or too many arguments, please try again: `k!setupModChannel [channelId]`"
        channel = self.bot.get_channel(int(channelId))
        if (channel != None and too_many_arguments == None):
            self.tf_database_manager.new_mod_channel(ctx.guild.id, channelId)
            await ctx.channel.send(embed=createModerationChannelEmbed(ctx,channel,"Added"))
            return
        raise(Exception(error))

    @commands.command(name="removeModChannel", aliases=["remove_mod_channel"])
    #@commands.check(KoalaBot.is_admin)
    async def removeModChannel(self, ctx, channelId, too_many_arguments=None):
        """
        Get a list of filtered words on the current guild.
        :param ctx: The discord context
        :param channelId: The designated channel id to be removed
        :return:
        """
        error = "Missing Channel ID or too many arguments remove a mod channel. If you don't know your Channel ID, use `k!listModChannels` to get information on your mod channels."
        channel = self.bot.get_channel(int(channelId))
        if (channel != None and too_many_arguments == None):
            self.tf_database_manager.remove_mod_channel(ctx.guild.id, channelId)
            await ctx.channel.send(embed=createModerationChannelEmbed(ctx,channel,"Removed"))
            return
        raise Exception(error)

    @commands.command(name="listModChannels", aliases=["list_mod_channels"])
    #@commands.check(KoalaBot.is_admin)
    async def listModChannels(self, ctx):
        """
        Get a list of filtered words on the current guild.
        :param ctx: The discord context
        :return:
        """

        channels = self.tf_database_manager.get_mod_channel(ctx.guild.id)
        embed = discord.Embed()
        embed.colour = KOALA_GREEN
        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        embed.title = "Koala Moderation - Mod Channels"
        for channel in channels:
            details = self.bot.get_channel(int(channel[0]))
            if (details is not None):
                embed.add_field(name="Name & Channel ID", value=details.mention + " " + str(details.id), inline=False)
            else:
                embed.add_field(name="Channel ID", value=channel[0], inline=False)
        await ctx.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self,message):
        """
        Upon receiving a message, it is checked for filtered text and is deleted.
        :param message: The newly received message
        :return:
        """
        if (message.guild is not None): # and not KoalaBot.is_admin and not KoalaBot.is_owner):
            censor_list = self.tf_database_manager.get_filtered_text_for_guild(message.guild.id)
            for word,filter_type in censor_list:
                if (word in message.content):
                    if (filter_type == "risky"):
                        await message.author.send("Watch your language! Your message: '*"+message.content+"*' in "+message.channel.mention+" contains a 'risky' word. This is a warning.")
                        break
                    elif (filter_type == "banned"):
                        await message.author.send("Watch your language! Your message: '*"+message.content+"*' in "+message.channel.mention+" has been deleted by KoalaBot.")
                        await sendToModerationChannels(message, self)
                        await message.delete()
                        break

def setup(bot: KoalaBot) -> None:
    """
    Loads this cog into the selected bot
    :param  bot: The client of the KoalaBot
    """
    bot.add_cog(TextFilterCog(bot))

def createModerationChannelEmbed(ctx, channel, action):
    embed = discord.Embed()
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
    embed.title = "Koala Moderation - Mod Channel " + action
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel ID", value=channel.id)
    return embed

async def filterWord(self, ctx, word, filter_type):
    self.tf_database_manager.new_filtered_text(ctx.guild.id, word, filter_type)

async def unfilterWord(self, ctx, word):
    self.tf_database_manager.unfilter_text(ctx.guild.id, word)

def typeExists(filter_type):
    return filter_type == "risky" or filter_type == "banned"

def isModerationChannelAvailable(guild_id, self):
    channels = self.tf_database_manager.get_mod_channel(guild_id)
    return len(channels) > 0

async def sendToModerationChannels(message, self):
    if (isModerationChannelAvailable(message.guild.id, self)):
        channels = self.tf_database_manager.get_mod_channel(message.guild.id)
        for each_chan in channels:
            channel = self.bot.get_channel(id=int(each_chan[0]))
            await channel.send(embed=buildModerationEmbed(message))

def buildModerationEmbed(message):
    embed = discord.Embed()
    embed.colour = KOALA_GREEN
    embed.title = "Koala Moderation - Message Deleted"
    embed.add_field(name="Reason",value="Contained banned word")
    embed.add_field(name="User",value=message.author.mention)
    embed.add_field(name="Channel",value=message.channel.mention)
    embed.add_field(name="Message",value=message.content)
    embed.add_field(name="Message",value=message.created_at)
    return embed

def doesWordExist(self, ft_id):
    return len(self.database_manager.db_execute_select(f"SELECT * FROM TextFilter WHERE filtered_text_id = (\"{ft_id}\");")) > 0

class TextFilterDBManager:
    """
    A class for interacting with the Koala text filter database
    """

    def __init__(self, database_manager: KoalaDBManager, bot_client: discord.client):
        """
        Initialises local variables
        :param database_manager:
        :param bot_client:
        """
        self.database_manager = database_manager
        self.bot = bot_client

    def create_tables(self):
        """
        Creates all the tables associated with TextFilter
        :return:
        """
        sql_create_text_filter_table = """
        CREATE TABLE IF NOT EXISTS TextFilter (
        filtered_text_id text NOT NULL,
        guild_id integer NOT NULL,
        filtered_text text NOT NULL,
        filter_type text NOT NULL,
        PRIMARY KEY (filtered_text_id)
        );"""

        sql_create_mod_table = """
        CREATE TABLE IF NOT EXISTS TextFilterModeration (
        channel_id text NOT NULL,
        guild_id integer NOT NULL,
        PRIMARY KEY (channel_id)
        );"""

        self.database_manager.db_execute_commit(sql_create_text_filter_table)
        self.database_manager.db_execute_commit(sql_create_mod_table)

    def new_mod_channel(self, guild_id, channel_id):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from
        :param channel_id: The new channel for moderation
        :return:
        """
        self.database_manager.db_execute_commit(
            f"INSERT INTO TextFilterModeration (channel_id, guild_id) VALUES (\"{channel_id}\", {guild_id});")

    def new_filtered_text(self, guild_id, filtered_text, filter_type):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from
        :param filtered_text: The new word to be filtered
        :param filtered_type: The filter type (banned or risky)
        :return:
        """
        ft_id = str(guild_id) + filtered_text
        if not doesWordExist(self, ft_id):
            self.database_manager.db_execute_commit(
                f"INSERT INTO TextFilter (filtered_text_id, guild_id, filtered_text, filter_type) VALUES (\"{ft_id}\", {guild_id}, \"{filtered_text}\", \"{filter_type}\");")
            return 
        raise Exception("Filtered word already exists")
            
    def unfilter_text(self, guild_id, filtered_text):
        """
        Adds new filtered word for a guild
        :param guild_id: Guild ID to retrieve filtered words from
        :param filtered_text: The new word to be filtered
        :return:
        """
        ft_id = str(guild_id) + filtered_text
        if doesWordExist(self, ft_id):
            self.database_manager.db_execute_commit(
                f"DELETE FROM TextFilter WHERE filtered_text_id = (\"{ft_id}\");")
            return
        raise Exception("Filtered word does not exist")

    def get_filtered_text_for_guild(self, guild_id):
        """
        Retrieves all filtered words for a specific guild and formats into a nice list of words
        :param guild_id: Guild ID to retrieve filtered words from:
        :return: list of filtered words
        """
        rows = self.database_manager.db_execute_select(f"SELECT * FROM TextFilter WHERE guild_id = {guild_id};")
        censor_list = []
        for row in rows:
            censor_list.append((row[2], row[3]))
        return censor_list

    def get_mod_channel(self, guild_id):
        return self.database_manager.db_execute_select(f"SELECT channel_id FROM TextFilterModeration WHERE guild_id = {guild_id};")

    def remove_mod_channel(self, guild_id, channel_id):
        self.database_manager.db_execute_commit(
            f"DELETE FROM TextFilterModeration WHERE guild_id = ({guild_id}) AND channel_id = (\"{channel_id}\");")