from LangaraCourseInfo import Course

from discord_webhook import DiscordWebhook, DiscordEmbed

import os
from dotenv import load_dotenv
load_dotenv()

def send_webhook(self, c1: Course, c2: Course):
    
    if c2.subject not in ["MATH", "CPSC"]:
        return
    
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if url == None:
        return
    
    webhook = DiscordWebhook(
        url = url,
        username = "Peregrine",
        rate_limit_retry=True)
    
    embed = DiscordEmbed()
    embed.set_footer("This feature is in beta. Suggestions / pull requests welcome.")
    
    if c1 == None:
        embed.set_title(f"NEW SECTION ADDED: {c2.subject} {c2.course_code} {c2.crn}!")
        embed.set_color("FF0000")
        desc = f"{c2.subject} {c2.course_code} {c2.title} {c2.section} {c2.crn}\n"
        desc += f"{c2.notes}\n"
        
        for s in c2.schedule:
            desc += f"\n{s.type} {s.days} {s.time} {s.room} {s.instructor}"
        
        embed.set_description(desc)
    
    elif c1.schedule[0].instructor != c2.schedule[0].instructor:
        embed.set_title(f"Instructor changed for {c2.subject} {c2.course_code} {c2.crn}.")
        desc = f"{c2.subject} {c2.course_code} {c2.title} {c2.section} {c2.crn}\n"
        desc += f"{c2.notes}\n"
        
        embed.set_description(desc)
        
        t1 = ""
        for s in c1.schedule:
            t1 += f"\n{s.type} {s.days} {s.time} {s.room} {s.instructor}"
        embed.add_embed_field(name="Schedule Before:", value=t1)
        
        t2 = ""
        for s in c2.schedule:
            t2 += f"\n{s.type} {s.days} {s.time} {s.room} {s.instructor}"
        embed.add_embed_field(name="Schedule After:", value=t2)
    
    else:
        return
    
    response = webhook.execute()
    
    