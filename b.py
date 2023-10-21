import discord
import json
import asyncio

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

cfg = open("config.json", "r")
tmpconfig = cfg.read()
cfg.close()
config = json.loads(tmpconfig)

token = config["token"]
guild_id = config["server-id"]
logs_channel = config["logs-channel-id"]
invite_code = config["invite-code"]
admin_role_id = config["admin-role-id"]

invites = {}
last = ""
new_joiner = False

try:
    with open("admin_users.json", "r") as file:
        admin_users = json.load(file)
except FileNotFoundError:
    admin_users = []

async def save_admin_users():
    with open("admin_users.json", "w") as file:
        json.dump(admin_users, file)

async def fetch():
    global last
    global invites
    global new_joiner
    await client.wait_until_ready()
    gld = client.get_guild(int(guild_id))
    logs = client.get_channel(int(logs_channel))
    while not client.is_closed():
        invs = await gld.invites()
        tmp = []

        for i in invs:
            for s in invites:
                if s[0] == i.code:
                    if int(i.uses) > s[1]:
                        usr = await gld.fetch_member(int(last))
                        eme = discord.Embed(description="Just joined the server" , color=0x03d692, title=" ")
                        eme.set_author(name=usr.name + "#" + usr.discriminator, icon_url=usr.avatar.url)
                        eme.set_footer(text="ID: " + str(usr.id))
                        eme.timestamp = usr.joined_at
                        eme.add_field(name="Used invite", 
                                      value="Inviter: " + f" (`{i.inviter.name}#{i.inviter.discriminator}` | `{i.inviter.id}`)\nCode: `{i.code}`\nUses: `{i.uses}`", inline=False)

                        if i.code == invite_code:
                            admin_role = gld.get_role(int(admin_role_id))
                            if admin_role:
                                user_id = str(usr.id)
                                if user_id in admin_users:
                                    await logs.send(f" Weekly Trial Already Assigned: {usr.mention} has already received the 'Weekly Trial' role. You are not allowed to receive it again.")
                                else:
                                    await usr.add_roles(admin_role)
                                    eme.add_field(name="Weekly Trial  Assigned " , value= f"{usr.mention}The joiner has been assigned the 'Weekly Trial' role", inline=False)
                                    admin_users.append(user_id)
                                    await logs.send(embed=eme)
                                    await save_admin_users()

            tmp.append(tuple((i.code, i.uses)))
        
        if new_joiner:
            new_joiner = False  
        else:
            await asyncio.sleep(4)  
        
        invites = tmp

@client.event
async def on_ready():
    print("Ready!")
    await client.change_presence(activity=discord.Activity(name="joins", type=2))
    client.loop.create_task(fetch())

@client.event
async def on_member_join(member):
    global last
    global new_joiner
    last = str(member.id)
    new_joiner = True  
    client.loop.create_task(remove_role_after_delay(member.id, admin_role_id, 60))

async def remove_role_after_delay(user_id, role_id, delay):
    await asyncio.sleep(delay)
    gld = client.get_guild(int(guild_id))
    user = await gld.fetch_member(int(user_id))
    role = gld.get_role(int(role_id))
    if user and role:
        await user.remove_roles(role)
        logs = client.get_channel(int(logs_channel))
        await logs.send(f"Weekly Trial Removed for {user.mention} after the countdown")


client.run(token)
