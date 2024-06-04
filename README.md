# LangaraCourseWatcher

This is a project to collect, collate, and serve information about courses at Langara through one service.
- Hosts an API with the courses database at coursesapi.langaracs.ca
- Updates data from the latest Langara semester every hour.
- Updates transfer and older Langara data every day.


### Hosting:
This service will work best with docker-compose.

Make sure that you provide a volume (`course_watcher_db:/database`) for the image.