#!/usr/bin/env python
"""
Testing KoalaBot TextFilter

Commented using reStructuredText (reST)
"""

import asyncio

# Libs
import discord
import discord.ext.test as dpytest
import mock
import pytest
from discord.ext import commands

# Own modules
import KoalaBot
from cogs import BaseCog
from cogs import TextFilter
from tests.utils import TestUtilsCog
from tests.utils.TestUtils import assert_activity
from utils import KoalaDBManager
from utils.KoalaColours import *

# Constants

# Variables
base_cog = None
tf_cog = None
utils_cog =  None

# to-do: Research verify_embed - missing checks on embed content, currently just checks embed structure is correct
# to-do: test edge cases (empty filtered word, multiple words, etc)


def setup_function():
    """ setup any state specific to the execution of the given module."""
    global base_cog, tf_cog, utils_cog
    bot = commands.Bot(command_prefix=KoalaBot.COMMAND_PREFIX)
    base_cog = BaseCog.BaseCog(bot)
    tf_cog = TextFilter.TextFilterCog(bot)
    tf_cog.tf_database_manager.create_tables()
    utils_cog = TestUtilsCog.TestUtilsCog(bot)
    bot.add_cog(base_cog)
    bot.add_cog(tf_cog)
    bot.add_cog(utils_cog)
    dpytest.configure(bot)
    print("Tests starting")

def assertDeleteWarning(word):
    dpytest.verify_message("*"+word+"* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_word " + word + "*' in " + dpytest.get_config().guilds[0].channels[0].mention + " has been deleted by KoalaBot.")

def assertRiskyWarning(word):
    dpytest.verify_message("*"+word+"* has been filtered.")
    dpytest.verify_message("Watch your language! Your message: '*k!filter_word " + word + " risky*' in " + dpytest.get_config().guilds[0].channels[0].mention + " contains a 'risky' word. This is a warning.")

def createNewModChannelEmbed(channel):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channel Added"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Channel Name", value=channel.mention)
    embed.add_field(name="Channel IDs", value=str(channel.id))
    return embed

def listModChannelEmbed(channels):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channels"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    for channel in channels:
        embed.add_field(name="Name & Channel ID", value=channel.mention + " " + str(channel.id))
    return embed

def removeModChannelEmbed(channel):
    embed = discord.Embed()
    embed.title = "Koala Moderation - Mod Channel Removed"
    embed.colour = KOALA_GREEN
    embed.add_field(name="Name", value=channel.mention)
    embed.add_field(name="ID", value=str(channel.id))
    return embed

def createFilteredString(text):
    createTextString = ""
    for current in text:
        createTextString+=current+"\n"
    return createTextString

def filteredWordsEmbed(words,filter):
    wordString = createFilteredString(words)
    filterString = createFilteredString(filter)
    embed = discord.Embed()
    embed.title = "Koala Moderation - Filtered Words"
    embed.colour = KOALA_GREEN
    embed.set_footer(text=f"Guild ID: {dpytest.get_config().guilds[0].id}")
    embed.add_field(name="Banned Words", value=wordString)
    embed.add_field(name="Banned Words", value=filterString)
    return embed

@pytest.mark.asyncio()
async def test_filter_new_word_correct_database():
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no';"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word no")
    assertDeleteWarning("no")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'no';")) == old + 1 

@pytest.mark.asyncio()
async def test_unfilter_word_correct_database():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word unfilterboi")
    assertDeleteWarning("unfilterboi")
    
    old = len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi';"))
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word unfilterboi")
    assert len(tf_cog.tf_database_manager.database_manager.db_execute_select(f"SELECT filtered_text FROM TextFilter WHERE filtered_text = 'unfilterboi';")) == old - 1  
    dpytest.verify_message("*unfilterboi* has been unfiltered.")

@pytest.mark.asyncio()
async def test_filter_empty_word():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word")

@pytest.mark.asyncio()
async def test_filter_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word a b c d e f g")

@pytest.mark.asyncio()
async def test_unfilter_empty():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word")

@pytest.mark.asyncio()
async def test_unfilter_too_many_arguments():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "unfilter_word a b c d e")

@pytest.mark.asyncio()
async def test_unrecognised_filter_type():
    with pytest.raises(Exception):
        await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word testy unknown")

@pytest.mark.asyncio()
async def test_list_filtered_words():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word listing1")
    assertDeleteWarning("listing1")
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "filter_word listing2 risky")
    assertRiskyWarning("listing2")

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "check_filtered_words")
    assert_embed = filteredWordsEmbed(['listing1','listing2'],['banned','risky'])
    dpytest.verify_embed(embed=assert_embed)

@pytest.mark.asyncio()
async def test_list_filtered_words_empty():
    await dpytest.message(KoalaBot.COMMAND_PREFIX + "check_filtered_words")
    assert_embed = filteredWordsEmbed([],[])
    dpytest.verify_embed(embed=assert_embed)

@pytest.mark.asyncio()
async def test_add_mod_channel():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel.id))
    assert_embed = createNewModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)

@pytest.mark.asyncio()
async def test_list_channels():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel.id))
    assert_embed = createNewModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "listModChannels")
    assert_embed = listModChannelEmbed([channel])
    dpytest.verify_embed(embed=assert_embed)

@pytest.mark.asyncio()
async def test_list_multiple_channels():
    channel1 = dpytest.backend.make_text_channel(name="TestChannel1", guild=dpytest.get_config().guilds[0])
    channel2 = dpytest.backend.make_text_channel(name="TestChannel2", guild=dpytest.get_config().guilds[0])
    dpytest.get_config().channels.append(channel1)
    dpytest.get_config().channels.append(channel2)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel1.id))
    assert_embed = createNewModChannelEmbed(channel1)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+str(channel2.id))
    assert_embed = createNewModChannelEmbed(channel2)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "listModChannels")
    assert_embed = listModChannelEmbed([channel1,channel2])
    dpytest.verify_embed(embed=assert_embed)

@pytest.mark.asyncio()
async def test_remove_mod_channel():
    channel = dpytest.backend.make_text_channel(name="TestChannel", guild=dpytest.get_config().guilds[0])
    channelId = str(channel.id)
    dpytest.get_config().channels.append(channel)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "setupModChannel "+channelId)
    assert_embed = createNewModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)

    await dpytest.message(KoalaBot.COMMAND_PREFIX + "removeModChannel "+channelId)
    assert_embed = removeModChannelEmbed(channel)
    dpytest.verify_embed(embed=assert_embed)

@pytest.mark.asyncio()
@pytest.mark.last()
async def cleanup():
    tf_cog.tf_database_manager.database_manager.db_execute_commit(f"DELETE * FROM TextFilter")
    tf_cog.tf_database_manager.database_manager.db_execute_commit(f"DELETE * FROM TextFilterModeration")
