# bot.py
import os
import json
import math

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

with open('Recipes.json', 'r') as recipeFile:
    data = recipeFile.read()

recipes = json.loads(data)

client = discord.Client()


def find_assembler_level(content):
    for x in range(2, len(content)):
        if content[x] == "-a" and content[x+1].isnumeric():
            level = int(content[x+1])
            if 0 < level < 4:
                return level
    return 3


def find_furnace_level(content):
    for x in range(2, len(content)):
        if content[x] == "-f" and content[x+1].isnumeric():
            level = int(content[x+1])
            if 0 < level < 4:
                return level
    return 3


def find_miner_level(content):
    for x in range(2, len(content)):
        if content[x] == "-m" and content[x+1].isnumeric():
            level = int(content[x+1])
            if 0 < level < 3:
                return level
    return 2


def find_belt_level(content):
    for x in range(2, len(content)):
        if content[x] == "-b" and content[x+1].isnumeric():
            level = int(content[x+1])
            if 0 < level < 4:
                return level
    return 3


# todo: add modules
def get_crafting_speed(builder, assembler_level, furnace_level, miner_level):
    if builder == "Assembler":
        if assembler_level == 1:
            return 0.5
        if assembler_level == 2:
            return 0.75
        if assembler_level == 3:
            return 1.25
        return 1.25
    elif builder == "Chemical":
        return 1
    elif builder == "Furnace":
        if furnace_level == 1:
            return 1
        if furnace_level == 2:
            return 2
        if furnace_level == 3:
            return 2
        return 2
    elif builder == "Miner":
        if miner_level == 1:
            return 0.25
        if miner_level == 2:
            return 0.5
        return 0.5
    elif builder == "Centrifuge":
        return 1
    elif builder == "Refinery":
        return 1


def get_builder_level(builder, assembler_level, furnace_level, miner_level):
    if builder == "Assembler":
        return assembler_level
    elif builder == "Chemical":
        return 1
    elif builder == "Furnace":
        return furnace_level
    elif builder == "Miner":
        return miner_level
    elif builder == "Centrifuge":
        return 1
    elif builder == "Refinery":
        return 1


def input_ratio(assembler_count, item, assembler_level, furnace_level, miner_level):
    # calculate time it takes for one craft for given recipe using given crafting speed modifier
    craft_time = item['recipe']['time'] / get_crafting_speed(item['built_in'], assembler_level,
                                                             furnace_level, miner_level)
    input_requirements = []

    # for each ingredient required in the given recipe
    for ingredient in item['recipe']['ingredients']:
        # calculate the required total ingredient amount needed per second
        required_per_second = ingredient['amount'] * assembler_count / craft_time
        ingredient_obj = recipes[ingredient['id']]
        if ingredient_obj['type'] != 'Liquid' and ingredient_obj['built_in'] != "N/A" \
                and ingredient_obj['built_in'] != "Refinery":
            ingredient_recipe = ingredient_obj['recipe']
            # calculate time it takes for ingredient to craft
            sub_craft_time = ingredient_recipe['time'] / get_crafting_speed(ingredient_obj['built_in'], assembler_level,
                                                                            furnace_level, miner_level)
            # calculate number of ingredients created per second
            sub_produced_per_second = ingredient_recipe['yield'] / sub_craft_time
            input_requirement = {
                "id": ingredient['id'],
                # set amount needed to required per second / produced per second rounded up for padding
                "amount": math.ceil(required_per_second / sub_produced_per_second)
            }
            input_requirements.append(input_requirement)

    return input_requirements


def saturation(item, crafting_speed, belt_level):
    throughput_per_second = belt_level * 15
    craft_time = item['recipe']['time'] / crafting_speed
    output_per_second = item['recipe']['yield'] / craft_time
    return math.ceil(throughput_per_second / output_per_second)


@client.event
async def on_ready():
    print(
        f'{client.user} is connected to the following guilds:'
    )

    for guild in client.guilds:
        print(
            f'{guild.name}(id: {guild.id})'
        )


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.split(" ")

    if len(content) < 2:
        return

    assembler_level = find_assembler_level(content)
    furnace_level = find_furnace_level(content)
    miner_level = find_miner_level(content)
    belt_level = find_belt_level(content)

    if content[0] == "!saturation":
        if content[1] in recipes:
            crafting_speed = get_crafting_speed(recipes[content[1]]['built_in'], assembler_level, furnace_level, miner_level)
            result = saturation(recipes[content[1]], crafting_speed, belt_level)
            response = "--- Saturation for " + content[1] + " on belt r" + str(belt_level) + " ---\n"
            response += str(result) + " x " + recipes[content[1]]['built_in'] + " r"
            response += str(get_builder_level(recipes[content[1]]['built_in'], assembler_level, furnace_level, miner_level))
            await message.channel.send(response)

    if len(content) < 3:
        return

    if content[0] == "!ratio":
        if content[1].isnumeric() and 0 < int(content[1]) < 10000:
            if content[2] in recipes:
                results = input_ratio(int(content[1]), recipes[content[2]], assembler_level, furnace_level, miner_level)
                response = "--- Input for " + content[1] + " " + content[2] + " ---"
                for result in results:
                    response += "\n" + str(result['id']) + ": " + str(result['amount']) + " x "
                    response += recipes[result['id']]['built_in'] + " r"
                    response += str(get_builder_level(recipes[result['id']]['built_in'], assembler_level, furnace_level, miner_level))
                await message.channel.send(response)


client.run(TOKEN)
