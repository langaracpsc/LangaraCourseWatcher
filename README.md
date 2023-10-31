# LangaraCourseWatcher


Reincarnation of https://github.com/Highfire1/langara-course-api

Implements LangaraCourseInfo into a service.
- Hosts an API with the courses database.
- Re-fetches new data every 30 minutes.
- Sends notifications to a discord channel when changes are found.


### Hosting:
This service will work best with docker-compose.

Make sure that you provide a volume (`course_watcher_db:/database`) for the image. If you don't, the image will have to redownload the 250mb courseDB file if you recreate the image. As well, the discord notification feature is not very smart and will send duplicate messages if you recreate the image without the old volume.
