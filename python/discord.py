from LangaraCourseInfo import Course
import os

from discord_webhook import DiscordWebhook, DiscordEmbed


import os
from dotenv import load_dotenv
load_dotenv()

def send_webhooks(url:str, changes:list[tuple[Course | None, Course]]):
    
    if os.getenv("DEBUG_MODE") == 1:
        return
    
    embeds = []
    
    for c in changes:
        e = generate_embed(url, c[0], c[1])
        
        if e != None:
            embeds.append(e)
    
    if len(embeds) == 0:
        return
        
    webhook = DiscordWebhook(
            url = url,
            username = "LangaraCourseWatcher",
            rate_limit_retry=True
        )
    course_updates_role = 1169017540790468734
    webhook.content = f"<@&{course_updates_role}> Course updates found!"
    webhook.execute()

    for e in embeds:
        webhook = DiscordWebhook(
            url = url,
            username = "LangaraCourseWatcher",
            rate_limit_retry=True
        )
        
        webhook.add_embed(e)
        webhook.execute()


def generate_embed(url:str, c1: Course, c2: Course) -> DiscordEmbed | None:
    
    # Too many course changes
    if c2.subject not in ["MATH", "CPSC"]:
        return
    
    embed = DiscordEmbed()
    embed.set_footer("This feature is in beta. Suggestions / pull requests welcome.")
    
    if c1 == None:
        embed.set_title(f"NEW SECTION ADDED: {c2.subject} {c2.course_code} {c2.crn}!")
        embed.set_color("FF0000")
        desc = f"{c2.subject} {c2.course_code} {c2.title} {c2.section} {c2.crn}\n"
        if c2.notes != None:
            desc += f"{c2.notes}\n"
        
        for s in c2.schedule:
            desc += f"\n{s.type.value} {s.days} {s.time} {s.room} {s.instructor}"
        
        embed.set_description(desc)
        embed.set_color("008000")
    
    elif c1.schedule[0].instructor != c2.schedule[0].instructor:
        embed.set_title(f"Instructor changed for {c2.subject} {c2.course_code} {c2.crn}.")
        desc = f"{c2.subject} {c2.course_code} {c2.title} {c2.section} {c2.crn}\n"
        if c2.notes != None:
            desc += f"{c2.notes}\n"
        
        embed.set_description(desc)
        
        t1 = ""
        for s in c1.schedule:
            t1 += f"\n{s.type.value}  {s.days}  {s.time}  {s.room}  {s.instructor}"
        embed.add_embed_field(name="Schedule Before:", value=t1)
        
        t2 = ""
        for s in c2.schedule:
            t2 += f"\n{s.type.value}  {s.days}  {s.time}  {s.room}  {s.instructor}"
        embed.add_embed_field(name="Schedule After:", value=t2)
        
        embed.set_color("FF0000")
    
    else:
        return None
    
    return embed
    
    
    